# ゆかりねっと用のFaster-Whisper音声認識エンジン
AI認識のFaster-WhisperをゆかりねっとやゆかコネNEOで使うための音声認識エンジンです。

# Features
* google認識に頼らない音声認識が出来ます。
* googleより少し認識速度が速いです(RTX3080Ti基準)
* 1.7GBほどビデオメモリを消費します。  
![yukarisettei.png.](/image/YukariWhisper01.png "settei")  

# Installation
* 実行にはphyonのインストールが必要です。  
* 今の所gitとphyonの知識がないと導入が難しい状態です。  
* 自動インストーラー(install.bat)を作成中  

#settings
* yukariwhisper.iniを書き換えてください。  

* text_type = 0  
* 送信する文字形式を指定します。  
* ゆかりねっとを使う場合=0  
* ゆかコネNEOを使う場合=1  

* local_port = 50000  
* ゆかりねっとの設定にある。「音声認識エンジン」の「認識結果待ち受けポート」と番号を同じにしてください。  
![yukarisettei.png.](/image/YukariWhisper02.png "settei")  

* ゆかコネNEOの場合は、「︙」三点アイコンの動作状況にあるCommunicationPortのWebSocket(NEO-innerAPI):  の値と同じにしてください  
![yukarisettei.png.](/image/YukariWhisper03.png "settei")  

# License
"YukariWhisper" is under [MIT license](https://en.wikipedia.org/wiki/MIT_License).

