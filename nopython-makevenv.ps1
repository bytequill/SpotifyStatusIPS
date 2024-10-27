if (-not (Test-Path -Path ".\pythonportable")) {
    Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.0/python-3.11.0-embed-amd64.zip' -OutFile "$env:TEMP\python-3.11.0-embed-amd64.zip"
    Expand-Archive -Path "$env:TEMP\python-3.11.0-embed-amd64.zip" -DestinationPath ".\pythonportable"
    Add-Content -Path ".\pythonportable\python311._pth" -Value 'import site'
    Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile ".\pythonportable\get-pip.py"
    &".\pythonportable\python.exe" ".\pythonportable\get-pip.py"
}
Write-Output 'Starting installation of necessary libraries' 
&".\pythonportable\python.exe" "-m" "pip" "install" "-U" "pip" "setuptools" "wheel" "numpy"
&".\pythonportable\python.exe" "-m" "pip" "install" "-r" "requirements.txt"
Write-Output 'Local environment installed. To run the project please open nopython-run.bat'
Pause