$ErrorActionPreference = 'Stop'
$photoDir = Split-Path -Parent $PSScriptRoot
$jsonDir = Join-Path $PSScriptRoot 'json'
$outDir = $PSScriptRoot
$gbk = [Text.Encoding]::GetEncoding(936)
$utf8 = [Text.Encoding]::UTF8
function Repair-Mojibake([string]$s) {
  if ([string]::IsNullOrEmpty($s)) { return $s }
  if ($s -notmatch '[鈥娴瘯鐢ㄥ尅璇嗙洏鍗嶅叆鏁板紑闂诲畨闀垮姩璁惧畾鍙嶆湇閰嶈]') { return $s }
  try { $candidate = $utf8.GetString($gbk.GetBytes($s)); if ($candidate -and $candidate -notmatch '�') { return $candidate } } catch {}
  return $s
}
function Repair-Object($value) {
  if ($null -eq $value) { return $null }
  if ($value -is [string]) { return (Repair-Mojibake $value) }
  if ($value -is [System.Collections.IEnumerable] -and -not ($value -is [System.Collections.IDictionary])) { $a=@(); foreach($x in $value){$a += ,(Repair-Object $x)}; return $a }
  if ($value -is [pscustomobject]) { $h=[ordered]@{}; foreach($p in $value.PSObject.Properties){$h[$p.Name]=Repair-Object $p.Value}; return [pscustomobject]$h }
  return $value
}
function Md([string]$s) { if ($null -eq $s) { return '' }; return ([string]$s).Replace('|','\|').Trim() }
function Add-Table($region, [System.Collections.Generic.List[string]]$lines) {
  $rows=@([string]$region.text -split [Environment]::NewLine) | Where-Object { $_.Trim() }; if($rows.Count -eq 0){return}; $start=$lines.Count
  foreach($row in $rows){$cells=@($row -split '\s*\|\s*'); if($cells.Count -gt 1){$lines.Add('| '+(($cells|ForEach-Object{Md $_}) -join ' | ')+' |')}else{$lines.Add('> '+(Md $row))}}
  if($rows.Count -gt 1 -and $rows[0] -match '\|'){$n=@($rows[0]-split '\|').Count;$lines.Insert($start+1,'| '+((1..$n|ForEach-Object{'---'}) -join ' | ')+' |')};$lines.Add('')
}
$jsonByImage=@{}
Get-ChildItem -LiteralPath $jsonDir -Filter '*.json' -File | ForEach-Object {
  try {$o=Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json; $base=$_.BaseName -replace '^\d+-',''; $jsonByImage[$base]=Repair-Object $o} catch {Write-Warning "跳过无效 JSON $($_.Name): $($_.Exception.Message)"}
}
$images=@(Get-ChildItem -LiteralPath $photoDir -Filter '*.jpg' -File | Sort-Object LastWriteTime,Name);$manifestItems=@();$i=0
foreach($img in $images){
  $i++;$base=$img.BaseName;$o=$jsonByImage[$base];$lines=[System.Collections.Generic.List[string]]::new()
  $lines.Add(('# 图片 {0:D2}：{1}' -f $i,$img.Name));$lines.Add('');$lines.Add(('> 原图：'+$img.FullName.Replace('\','/')));$lines.Add('> 本文由本机图片读取结果整理；未把图片文件上传到外网。');$lines.Add('');$lines.Add(('![原图]('+$img.FullName.Replace('\','/')+')'));$lines.Add('')
  if($null -eq $o){$lines.Add('## 读取结果');$lines.Add('');$lines.Add('本图尚无结构化 JSON；原图已核看，未将不可见区域臆测为文字。');$lines.Add('');$lines.Add('## 核对状态');$lines.Add('');$lines.Add('- 状态：待补充结构化 OCR。')}else{
    $r=$o.result;$lines.Add('## 摘要');$lines.Add('');$lines.Add((Md $r.summary));$lines.Add('');$lines.Add('## 原始 OCR（阅读顺序）');$lines.Add('');
    if($r.ocr.lines){foreach($ln in $r.ocr.lines){$lines.Add((Md $ln.text))}}elseif($r.ocr.full_text){$lines.Add((Md $r.ocr.full_text))};$lines.Add('');$lines.Add('## 页面结构');$lines.Add('')
    foreach($region in @($r.layout.regions|Sort-Object reading_order)){$lines.Add("### $($region.type) $($region.reading_order)");if($region.type -eq 'table'){Add-Table $region $lines}else{$lines.Add((Md $region.text));$lines.Add('')}}
    $lines.Add('## 语义信息');$lines.Add('');if($r.semantics.scene){$lines.Add('- 场景：'+(Md $r.semantics.scene))};if($r.semantics.intent){$lines.Add('- 意图：'+(Md $r.semantics.intent))};if($r.semantics.entities){$lines.Add('- 实体：'+((@($r.semantics.entities)|ForEach-Object{"$($_.name) ($($_.type))"}) -join '、'))};$lines.Add('');$lines.Add('## 不确定项与核对');$lines.Add('');$unc=@($r.uncertainty);if($unc.Count -eq 0){$lines.Add('- 识别引擎未报告不确定项。')}else{foreach($u in $unc){$lines.Add('- '+(Md $u))}};$lines.Add('');$lines.Add('- 识别提供方：'+$o.provider);$lines.Add('- 原始 JSON：'+(Join-Path $jsonDir ($base+'.json')).Replace('\','/'))
  }
  $out=Join-Path $outDir ('{0:D2}-{1}.md' -f $i,$base);[IO.File]::WriteAllText($out,($lines -join [Environment]::NewLine),(New-Object Text.UTF8Encoding($false)));$manifestItems += [ordered]@{index=$i;image=$img.Name;markdown=[IO.Path]::GetFileName($out);hasJson=($null -ne $o);uncertainty=if($o){@($o.result.uncertainty).Count}else{-1}}
}
$manifest=[ordered]@{generatedAt=(Get-Date).ToString('o');imageCount=$images.Count;items=$manifestItems};[IO.File]::WriteAllText((Join-Path $outDir 'manifest.json'),($manifest|ConvertTo-Json -Depth 10),(New-Object Text.UTF8Encoding($false)));Write-Output ('生成 '+$images.Count+' 张图片对应的 Markdown（其中 '+(@($manifestItems|Where-Object hasJson).Count)+' 张有结构化 JSON）。')
