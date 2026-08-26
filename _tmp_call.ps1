$body = Get-Content -Path 'd:\test_dev_projects\_tmp_body.json' -Raw
Invoke-RestMethod -Uri 'https://newapi.noontec.net/v1/chat/completions' -Method Post -ContentType 'application/json' -Headers @{'Authorization'='Bearer sk-YGSTYMY09N76P0cKbOXYKb48b8hYQcM92YcFAiDjdaCfccpE'} -Body $body
