$ErrorActionPreference = 'Stop'
$repo = if ($env:AICOMING_SKILL_REPO) { $env:AICOMING_SKILL_REPO } else { 'https://github.com/aicomingai/skills' }
$target = if ($env:AICOMING_SKILL_DIR) { $env:AICOMING_SKILL_DIR } else { Join-Path $HOME '.claude\skills\aicoming' }
$temp = Join-Path ([System.IO.Path]::GetTempPath()) ("aicoming-skill-" + [guid]::NewGuid())
try {
  git clone --depth 1 $repo $temp | Out-Null
  New-Item -ItemType Directory -Force -Path $target | Out-Null
  Copy-Item -Recurse -Force (Join-Path $temp 'aicoming\*') $target
  Write-Host "AIComing skill 已安装到 $target"
  Write-Host "下一步：python `"$target\scripts\aic.py`" login（隐藏输入，不要把 Key 写进命令行）"
} finally {
  if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}
