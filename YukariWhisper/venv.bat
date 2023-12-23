ECHO Start setup. It will take several minutes. Please wait
set temp=../tmp
python -m pip install --upgrade pip
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt

ECHO Setup is complete. Please run run.bat
cd ../
PAUSE
deactivate
