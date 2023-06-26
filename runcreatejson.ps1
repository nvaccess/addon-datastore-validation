# create json from manifest <dir file.json>
$ErrorActionPreference = "Stop";
cmd.exe /C $PSScriptRoot\venvUtils\venvCmd py "$PSScriptRoot\_validate\createJson.py" $args
