; -- Example1.iss --
; Demonstrates copying 3 files and creating an icon.

; SEE THE DOCUMENTATION FOR DETAILS ON CREATING .ISS SCRIPT FILES!

[Setup]
AppName=Earth Wallpaper
AppVerName=Earth Wallpaper 1.0 (beta)
DefaultDirName={pf}\Earth Wallpaper
DefaultGroupName=Earth Wallpaper
UninstallDisplayIcon={app}\earthwp.ico
Compression=lzma
SolidCompression=yes
;OutputDir=userdocs:Inno Setup Examples Output

[Dirs]
Name: "{app}/cache"

[Files]
Source: "dist/*"; DestDir: "{app}"
Source: "defaults/*"; DestDir: "{app}"
Source: "graphics/*"; DestDir: "{app}/graphics"
Source: "earthwp.ico"; DestDir: "{app}"

[Icons]
Name: "{group}\Earth Wallpaper"; Filename: "{app}\earthwp.exe"; IconFilename: "{app}\earthwp.ico"; WorkingDir: "{app}"
Name: "{group}\Edit Settings"; Filename: "{win}\notepad.exe"; Parameters: """{app}\settings.cfg"""; IconFilename: "{app}\earthwp.ico"; WorkingDir: "{app}"
Name: "{group}\Uninstall Earth Wallpaper"; Filename: "{uninstallexe}"

[UninstallDelete]
Type: files; Name: "{app}\pywallpaper.bmp"
Type: files; Name: "{app}\cache\*"
Type: files; Name: "{app}\graphics\*"
