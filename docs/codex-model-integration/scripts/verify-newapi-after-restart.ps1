param(
    [string]$BaselineDirectory = 'C:\Users\twm\.cc-switch\backups\stable-newapi-pre-restart-20260901_115905',
    [switch]$SkipLiveRequests
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$sqlite = 'D:\self_install\adb\platform-tools\sqlite3.exe'
$ccSwitchDb = 'C:\Users\twm\.cc-switch\cc-switch.db'
$baselineDb = Join-Path $BaselineDirectory 'cc-switch.db'
$configPath = 'C:\Users\twm\.codex\config.toml'
$catalogPath = 'C:\Users\twm\.codex\cc-switch-model-catalog.json'
$stateDb = 'C:\Users\twm\.codex\state_5.sqlite'
$authPath = 'C:\Users\twm\.codex\auth.json'
$providerId = 'universal-codex-950cc769853e4620b148532ead68beb2'
$routerProviderId = 'codex-multirouter'
$visionId = 'newapi-deepseek-v4-flash-vision-exp'
$fallbackId = 'deepseek-v4-flash-noontec-newapi'

$checks = [System.Collections.Generic.List[object]]::new()

function Add-Check {
    param(
        [string]$Name,
        [bool]$Passed,
        [object]$Actual,
        [object]$Expected,
        [string]$Note = ''
    )

    $checks.Add([pscustomobject]@{
        name = $Name
        passed = $Passed
        actual = $Actual
        expected = $Expected
        note = $Note
    })
}

function Get-SqliteText {
    param([string]$Database, [string]$Sql)

    $value = & $sqlite $Database $Sql
    if ($LASTEXITCODE -ne 0) {
        throw "SQLite query failed for $Database"
    }
    return ($value -join [Environment]::NewLine)
}

function Get-ProviderSettings {
    param([string]$Database, [string]$Id)

    $sql = "SELECT settings_config FROM providers WHERE id='$Id' AND app_type='codex';"
    return (Get-SqliteText -Database $Database -Sql $sql) | ConvertFrom-Json -Depth 100
}

function Get-Model {
    param([object[]]$Models, [string]$Id)

    return $Models | Where-Object {
        $_.id -eq $Id -or $_.slug -eq $Id -or $_.model -eq $Id
    } | Select-Object -First 1
}

foreach ($requiredPath in @($sqlite, $ccSwitchDb, $baselineDb, $configPath, $catalogPath, $stateDb)) {
    Add-Check -Name "file:$requiredPath" -Passed (Test-Path -LiteralPath $requiredPath) `
        -Actual (Test-Path -LiteralPath $requiredPath) -Expected $true
}

$config = [IO.File]::ReadAllText($configPath)
$activeProvider = [regex]::Match($config, '(?m)^model_provider\s*=\s*"([^"]+)"').Groups[1].Value
$globalEffort = [regex]::Match($config, '(?m)^model_reasoning_effort\s*=\s*"([^"]+)"').Groups[1].Value
Add-Check 'config.active_provider' ($activeProvider -eq 'codex_model_router_v2') $activeProvider 'codex_model_router_v2'
Add-Check 'config.global_reasoning' ($globalEffort -eq 'max') $globalEffort 'max'
Add-Check 'config.legacy_provider_alias' ($config.Contains('[model_providers.cc-switch-official]')) `
    ($config.Contains('[model_providers.cc-switch-official]')) $true '旧任务需要这个兼容定义'
Add-Check 'config.active_provider_definition' ($config.Contains('[model_providers.codex_model_router_v2]')) `
    ($config.Contains('[model_providers.codex_model_router_v2]')) $true

$catalog = Get-Content -Raw -LiteralPath $catalogPath | ConvertFrom-Json -Depth 100
$vision = Get-Model -Models $catalog.models -Id $visionId
$fallback = Get-Model -Models $catalog.models -Id $fallbackId
Add-Check 'catalog.vision_exists' ($null -ne $vision) ([bool]$vision) $true
Add-Check 'catalog.vision_default' ($vision.isDefault -eq $true) $vision.isDefault $true
Add-Check 'catalog.vision_reasoning' (
    $vision.defaultReasoningEffort -eq 'max' -and
    $vision.default_reasoning_effort -eq 'max' -and
    $vision.default_reasoning_level -eq 'max'
) "$($vision.defaultReasoningEffort)/$($vision.default_reasoning_effort)/$($vision.default_reasoning_level)" 'max/max/max'
Add-Check 'catalog.vision_modalities' (
    @($vision.input_modalities) -contains 'text' -and @($vision.input_modalities) -contains 'image'
) (@($vision.input_modalities) -join ',') 'text,image'
Add-Check 'catalog.fallback_exists' ($null -ne $fallback) ([bool]$fallback) $true
Add-Check 'catalog.fallback_display' ($fallback.display_name -eq 'newapi-deepseek-v4-flash') `
    $fallback.display_name 'newapi-deepseek-v4-flash'
Add-Check 'catalog.fallback_reasoning' (
    $fallback.defaultReasoningEffort -eq 'max' -and
    $fallback.default_reasoning_effort -eq 'max' -and
    $fallback.default_reasoning_level -eq 'max'
) "$($fallback.defaultReasoningEffort)/$($fallback.default_reasoning_effort)/$($fallback.default_reasoning_level)" 'max/max/max'

$commonConfig = Get-SqliteText -Database $ccSwitchDb -Sql "SELECT value FROM settings WHERE key='common_config_codex';"
$defaultModel = [regex]::Match($commonConfig, '(?m)^model\s*=\s*"([^"]+)"').Groups[1].Value
$defaultEffort = [regex]::Match($commonConfig, '(?m)^model_reasoning_effort\s*=\s*"([^"]+)"').Groups[1].Value
Add-Check 'ccswitch.default_model' ($defaultModel -eq $visionId) $defaultModel $visionId
Add-Check 'ccswitch.default_reasoning' ($defaultEffort -eq 'max') $defaultEffort 'max'

$provider = Get-ProviderSettings -Database $ccSwitchDb -Id $providerId
$providerModels = @($provider.modelCatalog.models)
$sourceText = Get-Model -Models $providerModels -Id 'newapi-deepseek-v4-flash'
$sourceVision = Get-Model -Models $providerModels -Id $visionId
Add-Check 'provider.base_url' ($provider.base_url -eq 'http://10.18.2.100/v1') $provider.base_url 'http://10.18.2.100/v1'
Add-Check 'provider.text_reasoning' (
    $sourceText.reasoning.defaultEffort -eq 'max' -and
    @($sourceText.reasoning.supportedEfforts) -contains 'max'
) $sourceText.reasoning.defaultEffort 'max'
Add-Check 'provider.vision_reasoning' (
    $sourceVision.reasoning.defaultEffort -eq 'max' -and
    @($sourceVision.reasoning.supportedEfforts) -contains 'max'
) $sourceVision.reasoning.defaultEffort 'max'
Add-Check 'provider.vision_modalities' (
    @($sourceVision.inputModalities) -contains 'text' -and @($sourceVision.inputModalities) -contains 'image'
) (@($sourceVision.inputModalities) -join ',') 'text,image'

$router = Get-ProviderSettings -Database $ccSwitchDb -Id $routerProviderId
$routerText = Get-Model -Models @($router.modelCatalog.models) -Id 'newapi-deepseek-v4-flash'
$routerVision = Get-Model -Models @($router.modelCatalog.models) -Id $visionId
$newApiRoute = @($router.codexRouting.routes) | Where-Object {
    $_.id -eq 'router-universal-codex-newapi-noontec'
} | Select-Object -First 1
Add-Check 'router.newapi_enabled' ($newApiRoute.enabled -eq $true) $newApiRoute.enabled $true
Add-Check 'router.fallback_alias' (
    $newApiRoute.aliases.$fallbackId -eq 'deepseek-v4-flash'
) $newApiRoute.aliases.$fallbackId 'deepseek-v4-flash'
Add-Check 'router.text_reasoning' ($routerText.reasoning.defaultEffort -eq 'max') `
    $routerText.reasoning.defaultEffort 'max'
Add-Check 'router.vision_reasoning' ($routerVision.reasoning.defaultEffort -eq 'max') `
    $routerVision.reasoning.defaultEffort 'max'

$baselineProvider = Get-ProviderSettings -Database $baselineDb -Id $providerId
$currentAuth = $provider.auth | ConvertTo-Json -Compress -Depth 30
$baselineAuth = $baselineProvider.auth | ConvertTo-Json -Compress -Depth 30
Add-Check 'provider.credential_unchanged' ($currentAuth -ceq $baselineAuth) `
    ($currentAuth -ceq $baselineAuth) $true '只比较，不输出认证内容'

$legacyThreadCount = [int](Get-SqliteText -Database $stateDb -Sql "SELECT COUNT(*) FROM threads WHERE archived=0 AND model_provider='cc-switch-official';")
$currentThreadCount = [int](Get-SqliteText -Database $stateDb -Sql "SELECT COUNT(*) FROM threads WHERE archived=0 AND model_provider='codex_model_router_v2';")
Add-Check 'history.legacy_provider_count' ($legacyThreadCount -eq 0) $legacyThreadCount 0
Add-Check 'history.current_provider_count' ($currentThreadCount -gt 0) $currentThreadCount '>0'

if (-not $SkipLiveRequests) {
    $auth = Get-Content -Raw -LiteralPath $authPath | ConvertFrom-Json -Depth 20
    $headers = @{
        Authorization = "Bearer $($auth.tokens.access_token)"
        'ChatGPT-Account-Id' = $auth.tokens.account_id
        'x-cc-switch-proxy-mode' = 'router'
        'Content-Type' = 'application/json'
    }

    $modelsResponse = Invoke-WebRequest -Uri 'http://127.0.0.1:15721/v1/models' `
        -Headers $headers -Method Get -TimeoutSec 30
    $modelIds = @((($modelsResponse.Content | ConvertFrom-Json).data).id)
    Add-Check 'live.models_status' ([int]$modelsResponse.StatusCode -eq 200) `
        ([int]$modelsResponse.StatusCode) 200
    Add-Check 'live.models_present' (
        $modelIds -contains $visionId -and $modelIds -contains $fallbackId
    ) "$($modelIds -contains $visionId)/$($modelIds -contains $fallbackId)" 'True/True'

    Add-Type -AssemblyName System.Drawing
    $visionBitmap = [Drawing.Bitmap]::new(128, 128)
    $visionGraphics = [Drawing.Graphics]::FromImage($visionBitmap)
    $visionGraphics.Clear([Drawing.Color]::Red)
    $visionStream = [IO.MemoryStream]::new()
    $visionBitmap.Save($visionStream, [Drawing.Imaging.ImageFormat]::Png)
    $visionImageBase64 = [Convert]::ToBase64String($visionStream.ToArray())
    $visionGraphics.Dispose()
    $visionBitmap.Dispose()
    $visionStream.Dispose()

    $visionPayload = @{
        model = $visionId
        reasoning = @{ effort = 'max' }
        stream = $false
        store = $false
        input = @(@{
            role = 'user'
            content = @(
                @{ type = 'input_text'; text = '识别所附图片的主要颜色；如果是红色，只回复 VISION_RED_OK。' },
                @{
                    type = 'input_image'
                    image_url = "data:image/png;base64,$visionImageBase64"
                }
            )
        })
    } | ConvertTo-Json -Depth 8 -Compress
    $visionResponse = Invoke-WebRequest -Uri 'http://127.0.0.1:15721/v1/responses' `
        -Headers $headers -Method Post -Body $visionPayload -TimeoutSec 90
    Add-Check 'live.vision_status' ([int]$visionResponse.StatusCode -eq 200) `
        ([int]$visionResponse.StatusCode) 200
    $visionJson = $visionResponse.Content | ConvertFrom-Json -Depth 30
    $visionText = @($visionJson.output | ForEach-Object { $_.content } | ForEach-Object { $_.text }) -join ''
    $visionSemanticPass = $visionText.Trim() -eq 'VISION_RED_OK'
    Add-Check 'live.vision_semantic' $visionSemanticPass `
        $visionSemanticPass $true '必须真正识别红色图片，不能只检查 HTTP 200'

    $fallbackPayload = @{
        model = $fallbackId
        reasoning = @{ effort = 'max' }
        stream = $false
        store = $false
        input = '只回复 FALLBACK_RESTART_OK。'
    } | ConvertTo-Json -Depth 6 -Compress
    $fallbackResponse = Invoke-WebRequest -Uri 'http://127.0.0.1:15721/v1/responses' `
        -Headers $headers -Method Post -Body $fallbackPayload -TimeoutSec 90
    Add-Check 'live.fallback_status' ([int]$fallbackResponse.StatusCode -eq 200) `
        ([int]$fallbackResponse.StatusCode) 200
    $fallbackJson = $fallbackResponse.Content | ConvertFrom-Json -Depth 30
    $fallbackText = @($fallbackJson.output | ForEach-Object { $_.content } | ForEach-Object { $_.text }) -join ''
    $fallbackSemanticPass = $fallbackText.Trim() -eq 'FALLBACK_RESTART_OK'
    Add-Check 'live.fallback_semantic' $fallbackSemanticPass `
        $fallbackSemanticPass $true '必须精确返回验收文本'
}

$failed = @($checks | Where-Object { -not $_.passed })
$report = [pscustomobject]@{
    checked_at = (Get-Date).ToString('o')
    baseline_directory = $BaselineDirectory
    passed = ($failed.Count -eq 0)
    check_count = $checks.Count
    failed_count = $failed.Count
    checks = $checks
}

$report | ConvertTo-Json -Depth 10
if ($failed.Count -gt 0) {
    exit 1
}
