@echo off
pip show pyglossary > nul 2>&1
if errorlevel 1 (
    echo installing the module...
    pip install pyglossary
)
echo Oppenining the app...
python -c"from pyglossary.ui.main import main; main()"

# Done.