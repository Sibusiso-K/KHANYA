param([string]$Deck, [string]$OutDir, [string]$Only = "")
# Render slides with real PowerPoint (the judges' renderer) for visual QA.
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$app = New-Object -ComObject PowerPoint.Application
try {
    $pres = $app.Presentations.Open($Deck, $true, $false, $false)  # read-only, untitled, no window
    $n = $pres.Slides.Count
    $want = @()
    if ($Only) { $want = $Only.Split(",") | ForEach-Object { [int]$_ } } else { $want = 1..$n }
    foreach ($i in $want) {
        $path = Join-Path $OutDir ("slide-{0:D2}.png" -f $i)
        $pres.Slides.Item($i).Export($path, "PNG", 1600, 900)
    }
    $pres.Close()
    "exported $($want.Count) of $n"
} finally {
    $app.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
}
