ECHO Start setup. It will take several minutes. Please wait
set temp=../tmp
python -m pip install --upgrade pip
pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt

ECHO Setup is complete. Please run run.bat
cd ../
PAUSE
deactivate
