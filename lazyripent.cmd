@echo off
TITLE LazyRipent
set mypath=%cd%
@echo %mypath%
@for %%f in ("%1") do set rulepath=%%~dpnf
@for %%f in ("%1") do set rulename=%%~nf
ECHO.
ECHO LazyRipent by Zode
ECHO Powerful mass ripenting tool for multiple bsps
ECHO Usage- Put in the full path to the maps folder eg. C:\path\to\bsps
ECHO.
:a
ECHO Using rule file "%rulename%"
set /p lrpath=Select path to maps folder:
python lazyripent.py "%lrpath%" %rulepath%
goto :a