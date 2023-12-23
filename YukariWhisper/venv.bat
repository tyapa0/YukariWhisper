ECHO セットアップを開始します。数十分かかります。しばらくお待ちください
set temp=../tmp
python -m pip install --upgrade pip
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt

ECHO セットアップが完了しました。run.batを実行してください
cd ../
PAUSE
deactivate
