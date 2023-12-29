# ゆかりねっと用のFaster-Whisper音声認識エンジン
AI認識のFaster-Whisperをゆかりねっとや、ゆかコネNEOで使うための音声認識エンジンです。

# Features
* google認識に頼らない音声認識が出来ます。
* googleより少し認識速度が速いです(RTX3080Ti基準)
* 1.7GBほどビデオメモリを消費します。
* nVIDIA系GPU(1000番以降)で動作します。  
![yukarisettei01.png.](/image/YukariWhisper01.png "settei01")  

# Installation
* 実行にはpythonのインストールが必要です。  https://www.google.com/search?q=PythonインストールWindows  
  python3.9以上で動作します。推奨は [`3.11.7です`](https://www.python.org/downloads/release/python-3117/)  
  `python3.12では動きません！！`(20023/12/28現在)  
  pythonのパスを追加にチェックを入れてインストールしてください。  
  ![YukariWhisper05.png.](/image/YukariWhisper05.png "settei05")

### 初めてのかた
  *  Source code (zip) をDownLoadします。 https://github.com/tyapa0/YukariWhisper/archive/refs/tags/v0.0.1.zip
  * `YukariWhisper-0.0.1.zip`を任意のフォルダへ解凍します。  
     ※解凍ツールによってはセキュリティ許可がされていない場合があります。  
   ファイルを右クリック→プロパティで表示し、セキュリティを許可してください。  
     ![kyoka.png.](/image/kyoka.png "kyoka") 
  * フォルダ内にある自動インストーラー`setup.bat`を実行します。
  * 数十分かかります。「続行するには何かキーを押してください . . .」と出れば終了です。
  * `run.bat`を実行します。
  * 初回のみダウンロードが始まります。しばらくするとマイク選択が出ます。
  * マイクの番号を入力してEnterキーを押してください。
### venv等 設定済みの方(分かる人用)  
  * gitで本プロジェクトをcloneしてmain.pyを実行してください。
  * `YukariWhisper`フォルダ内に`requirements.txt`があります。
  * AMD環境の方はLinux環境上で手動で構築できる人なら動かせますが、[制約が多いです。 ](https://rocm.docs.amd.com/en/docs-5.7.1/release/gpu_os_support.html)  

# Settings
* `yukariwhisper.ini`を書き換えてください。  

* **text_type = 0**  
送信する文字形式を指定します。  
ゆかりねっとを使う場合=0  
ゆかコネNEOを使う場合=1  

* **local_port = 50000**  
ゆかりねっとの設定にある。「音声認識エンジン」の「認識結果待ち受けポート」と番号を同じにしてください。  
![yukarisettei02.png.](/image/YukariWhisper02.png "settei02")  
ゆかコネNEOの場合は、「︙」三点アイコンの動作状況にあるCommunicationPortのWebSocket(NEO-innerAPI):  の値と同じにしてください  
![yukarisettei03.png.](/image/YukariWhisper03.png "settei03")  

* その他オプションはyukariwhisper.ini内を見てください。  
  音の切れ目を認識にしくいときは、PCのファンノイズを拾っている可能性があります。  
  従来の半分程度の音量でも認識するので、入力を半分に以下にするなど試してみてください。  
  iniファイルはQuest2でのVirtualDesktop基準で設定されています。マイクの推奨値は40%です。  
![yukarisettei04.png.](/image/YukariWhisper04.png "settei04")  


# Q&A
* 動かない！  
 エラー画面をキャプチャして[issues](https://github.com/tyapa0/YukariWhisper/issues)へ投稿、もしくは[Xへリプライ](https://twitter.com/TYA_PA_)をしていただければ確認します。  

* マウスやJoyStickの音を拾ってブブブブブブブブ等の文字が大量に出る。
  1. まずはマイクの音量を認識ギリギリまで絞ってみてください。
  1. [NVIDIA Broadcastアプリ](https://www.nvidia.com/ja-jp/geforce/broadcasting/broadcast-app/)等のノイズキャンセル技術を検討してみてください。  
  1. `yukariwhisper.ini`の vad_threshold=0.5など、少し大きくしてみてください。
  1. `ngwords.txt`に入れたキーワードを含む言葉は無視されます。5～8文字程度入れてみてください。  
  NVIDIA Broadcastアプリをインストールした後、マイク選択はNVIDIA Broadcastを選択してください。  
  ![yukarisettei06.png.](/image/YukariWhisper06.png "settei06")  
  vad_thresholdは=0.1等少なめでも問題なくなります。  
  ダイナミックマイクを使っている方は dynamic_energy_ratio=2.0など、少し少な目がちょうどいい値になります。  

# License
"YukariWhisper" is under [MIT license](https://en.wikipedia.org/wiki/MIT_License).

