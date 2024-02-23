ECHO Start setup. It will take several minutes. Please wait
set temp=../tmp
python -m pip install --upgrade pip
pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt

ECHO Setup is complete. Please run run.bat
cd ../
PAUSE
deactivate
