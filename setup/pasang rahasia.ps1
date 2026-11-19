# Simpan Anthropic API key + data Instagram ke GitHub Secrets repo fishtudio-agent.
$gh = "C:\Program Files\GitHub CLI\gh.exe"; $repo = "cellokerjacerdas/fishtudio-agent"
Write-Host "Tempel Anthropic API key (sk-ant-...), lalu Enter. Tidak tampil di layar:" -ForegroundColor Cyan
$s = Read-Host -AsSecureString
$k = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)).Trim()
if ($k) { $k | & $gh secret set ANTHROPIC_API_KEY --repo $repo; Write-Host "ANTHROPIC_API_KEY tersimpan" }
foreach ($n in 'IG_TOKEN','IG_ID_FISHTUDIO','IG_ID_GOLDFISH') {
  $v = [Environment]::GetEnvironmentVariable($n, 'User')
  if ($v) { $v | & $gh secret set $n --repo $repo; Write-Host "$n tersimpan (dari laptop)" } else { Write-Host "$n kosong di laptop" -ForegroundColor Yellow }
}
& $gh secret list --repo $repo
