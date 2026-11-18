param(
    [string]$Action = "list-devices",
    [string]$Device = "",
    [string]$RemotePath = "",
    [string]$LocalDest = ""
)

$shell = New-Object -ComObject Shell.Application
$thisPC = $shell.Namespace(17) # ssfDRIVES

function Get-PortableDevices {
    $devices = @()
    if ($thisPC) {
        foreach ($item in $thisPC.Items()) {
            $path = $item.Path
            $isDrive = $path -match '^[A-Z]:\\?'
            if (-not $isDrive) {
                $devices += [PSCustomObject]@{
                    Name = $item.Name
                    Path = $path
                    Type = $item.Type
                }
            }
        }
    }
    return $devices
}

function Find-DeviceItem([string]$name) {
    if (-not $thisPC) { return $null }
    foreach ($item in $thisPC.Items()) {
        if ($item.Name -like "*$name*" -or $name -like "*$($item.Name)*") {
            return $item
        }
    }
    return $null
}

switch ($Action) {
    "list-devices" {
        $devs = Get-PortableDevices
        $devs | ConvertTo-Json -Compress
    }
    "list-folders" {
        $target = Find-DeviceItem $Device
        $folders = @()
        if ($target) {
            $folder = $target.GetFolder
            if ($folder) {
                foreach ($sub in $folder.Items()) {
                    if ($sub.IsFolder) {
                        $folders += [PSCustomObject]@{
                            Name = $sub.Name
                            Path = $sub.Path
                        }
                    }
                }
            }
        }
        $folders | ConvertTo-Json -Compress
    }
    default {
        Write-Output "{}"
    }
}
