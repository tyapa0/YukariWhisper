# ゆかりねっと用のFaster-Whisper音声認識エンジン
AI認識のFaster-Whisperをゆかりねっとや、ゆかコネNEOで使うための音声認識エンジンです。

# Features
* google認識に頼らない音声認識が出来ます。
* googleより少し認識速度が速いです(RTX3080Ti基準)
* 1.7GBほどビデオメモリを消費します。  
![yukarisettei.png.](/image/YukariWhisper01.png "settei")  

# Installation
* 実行にはpython のインストールが必要です。  https://www.google.com/search?q=PythonインストールWindows

* 初めてのかた
  *  Source code (zip) をDownLoadします。 https://github.com/tyapa0/YukariWhisper/archive/refs/tags/v0.0.1.zip
  * YukariWhisper-0.0.1.zipを任意のフォルダへ解凍します。
  * フォルダ内にある自動インストーラー(install.bat)を実行します。
  * run.batを実行します。
* venv等 設定済みの方  
  * gitで本プロジェクトをcloneしてmain.pyを実行してください

# Settings
* yukariwhisper.iniを書き換えてください。  

* text_type = 0  
送信する文字形式を指定します。  
ゆかりねっとを使う場合=0  
ゆかコネNEOを使う場合=1  

* local_port = 50000  
ゆかりねっとの設定にある。「音声認識エンジン」の「認識結果待ち受けポート」と番号を同じにしてください。  
![yukarisettei.png.](/image/YukariWhisper02.png "settei")  
ゆかコネNEOの場合は、「︙」三点アイコンの動作状況にあるCommunicationPortのWebSocket(NEO-innerAPI):  の値と同じにしてください  
![yukarisettei.png.](/image/YukariWhisper03.png "settei")  

# License
"YukariWhisper" is under [MIT license](https://en.wikipedia.org/wiki/MIT_License).

