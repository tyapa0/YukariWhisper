# ゆかりねっと用のFaster-Whisper音声認識エンジン
AI認識のFaster-Whisperをゆかりねっとや、ゆかコネNEOで使うための音声認識エンジンです。

# Features
* google認識に頼らない音声認識が出来ます。
* googleより少し認識速度が速いです(RTX3080Ti基準)
* 1.7GBほどビデオメモリを消費します。  
![yukarisettei01.png.](/image/YukariWhisper01.png "settei01")  

# Installation
* 実行にはpython のインストールが必要です。  https://www.google.com/search?q=PythonインストールWindows

* 初めてのかた
  *  Source code (zip) をDownLoadします。 https://github.com/tyapa0/YukariWhisper/archive/refs/tags/v0.0.1.zip
  * YukariWhisper-0.0.1.zipを任意のフォルダへ解凍します。  
     ※解凍ツールによってはセキュリティ許可がされていない場合があります。  
   ファイルを右クリック→プロパティで表示し、セキュリティを許可してください。  
     ![kyoka.png.](/image/kyoka.png "kyoka") 
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
![yukarisettei02.png.](/image/YukariWhisper02.png "settei02")  
ゆかコネNEOの場合は、「︙」三点アイコンの動作状況にあるCommunicationPortのWebSocket(NEO-innerAPI):  の値と同じにしてください  
![yukarisettei03.png.](/image/YukariWhisper03.png "settei03")  

# License
"YukariWhisper" is under [MIT license](https://en.wikipedia.org/wiki/MIT_License).

