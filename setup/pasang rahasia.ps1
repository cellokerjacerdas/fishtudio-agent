# Simpan Anthropic API key ke GitHub Secrets repo fishtudio-agent (data Instagram sudah diisi).
$gh = "C:\Program Files\GitHub CLI\gh.exe"; $repo = "cellokerjacerdas/fishtudio-agent"
Write-Host "Tempel Anthropic API key (sk-ant-...), lalu Enter. Tidak tampil di layar:" -ForegroundColor Cyan
$s = Read-Host -AsSecureString
$k = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)).Trim()
if (-not $k) { Write-Host "Key kosong, batal." -ForegroundColor Red; exit 1 }
for ($i = 0; $i -lt 10; $i++) { $k | & $gh secret set ANTHROPIC_API_KEY --repo $repo 2>$null; if ($LASTEXITCODE -eq 0) { Write-Host "ANTHROPIC_API_KEY tersimpan" -ForegroundColor Green; break }; Start-Sleep 2 }
for ($i = 0; $i -lt 5; $i++) { $o = & $gh secret list --repo $repo 2>$null; if ($LASTEXITCODE -eq 0) { $o; break }; Start-Sleep 2 }
