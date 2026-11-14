# ゆかりねっと用のFaster-Whisper音声認識エンジン
AI認識のFaster-Whisperをゆかりねっとや、ゆかコネNEOで使うための音声認識エンジンです。

## ※CPU認識でより良い物が出てきましたので[こちら(Parapper)](https://github.com/Parakeet-Inc/Parapper-ASR)の使用をお勧めします。
https://github.com/Parakeet-Inc/Parapper-ASR

# Features
* google認識に頼らない音声認識が出来ます。
* 1.1GBほどビデオメモリを消費します。(kotoba-whisper使用時)
* googleより少し認識速度が速いです(RTX3080Ti基準)
* 日本語特化モデル **Haas-ja-v1.0** も選択できます(ONNX版・CPU推論・自動ダウンロード)。詳しくは下記「Haas-ja-v1.0 を使う」を参照してください。  
* nVIDIA系GPU(1000番以降)で動作します。 Driverは572.83以降(Cuda12.8)必須
![YukariWhisper01.png.](./image/YukariWhisper01.png "YukariWhisper01")  
![YukariWhisper07.png.](./image/YukariWhisper07.png "YukariWhisper07")  

# Installation
* 実行にはpythonのインストールが必要です。  https://www.google.com/search?q=PythonインストールWindows  
  python3.9以上で動作します。推奨は [`3.13.9です`](https://www.python.org/downloads/release/python-3139/)  
  pythonのパスを追加にチェックを入れてインストールしてください。  
  ![YukariWhisper05.png.](./image/YukariWhisper05.png "YukariWhisper05")

### v0.0.5以前からバージョンアップの方
  * [変更点はこちら](https://github.com/tyapa0/YukariWhisper/releases)
  * v0.0.5以前からは互換性が無いので、旧フォルダを削除してください。
  * `初めてのかた`を見て新規インストールをしてください。
  * `yukariwhisper.ini`は古いものを使わないでください！！(互換性なし)
  
### 初めてのかた
  *  Source code (zip) をDownLoadします。 https://github.com/tyapa0/YukariWhisper/archive/refs/tags/v0.1.1.zip
  * `YukariWhisper-0.x.x.zip`を任意のフォルダへ解凍します。  
     ※解凍ツールによってはセキュリティ許可がされていない場合があります。  
   ファイルを右クリック→プロパティで表示し、セキュリティを許可してください。  
     ![kyoka.png.](./image/kyoka.png "kyoka") 
  * フォルダ内にある自動インストーラー`setup.bat`を実行します。
  * 数十分かかります。「続行するには何かキーを押してください . . .」と出れば終了です。
  * `run.bat`を実行します。
  * 初回のみダウンロードが始まります。しばらくするとマイク選択が出ます。
  * マイクの番号を入力してEnterキーを押してください。
### venv等 設定済みの方(分かる人用)  
  * gitで本プロジェクトをcloneしてmain.pyを実行してください。
  * `YukariWhisper`フォルダ内に`requirements.txt`があります。
  * AMD環境の方はLinux環境上で手動で構築できる人なら動かせるかも？[制約が多いです。 ](https://rocm.docs.amd.com/en/latest/reference/gpu-atomics-operation.html)  

# Haas-ja-v1.0 を使う
* `yukariwhisper.ini` の `whisper_model_size` に次のように書くだけで切り替わります。Whisper同様初回起動時に自動でダウンロードされます。
```ini
whisper_model_size = kizuna-intelligence/Haas-ja-v1.0-OneCompression-ONNX
haas_format = int8
haas_threads = 4
```
* **なぜONNX版？**  
  Haas-ja-v1.0 は Whisper ではなく Parakeet-TDT(NeMo)系のモデルで、CTranslate2 では読み込めず。また元のNeMo版は「Linux + NVIDIA GPU + NeMo 2.7 + Triton(flash-linear-attention)」専用で、Windows / CPU は非対応。Windows でそのまま動く ONNX 変換版 [kizuna-intelligence/Haas-ja-v1.0-OneCompression-ONNX](https://huggingface.co/kizuna-intelligence/Haas-ja-v1.0-OneCompression-ONNX) を採用。推論コードは `YukariWhisper/haas_cpu/` 。
* **推論はCPUです。** GPUは使いません、モデルカード実測(Core i7-12700F・4スレッド・30秒音声)では int8 で音声の41.6倍速、int4-onecomp で30.2倍速と、数秒の発話なら十分にリアルタイム。VRAM消費ナシ。
* **形式は `haas_format` で選択可。** `int8`(最速・DL約664MB) / `int4-onecomp`(最小・精度良好・DL約380MB) / `fp32`(無圧縮・DL約2.47GB)。選択した形式のファイルだけをダウンロードします。
* Haas選択時は `beam_size` や `compute_type`、などのGPU設定は使いません。マイク側のVAD(Silero)や無音区切りなどの動作は Whisper の時と同じです。

# Settings
* `yukariwhisper.ini`を書き換えてください。  

* **text_type = 0**  
送信する文字形式を指定します。  
ゆかりねっとを使う場合=0  
ゆかコネNEOを使う場合=1  

* **local_port = 50000**  
ゆかりねっとの設定にある。「音声認識エンジン」の「認識結果待ち受けポート」と番号を同じにしてください。  
![YukariWhisper02.png.](./image/YukariWhisper02.png "YukariWhisper02")  
ゆかコネNEOの場合は、「︙」三点アイコンの動作状況にあるCommunicationPortのWebSocket(NEO-innerAPI):  の値と同じにしてください  
![YukariWhisper03.png.](./image/YukariWhisper03.png "YukariWhisper03")  


* 下記2つのパラメータは使用状況に応じて調整してください。  
* **pause_threshold = 5**  
フレーズの終わりとして認識される無音の最小の長さ (0.1秒単位)を指定します。値が小さいほど認識はより速く完了しますが、発声の途中で切れるなどのぶつ切りになりやすくなります。
* **phrase_threshold = 10**  
発話音声をフレーズとみなすまでの発話音声の最小秒数(0.1秒単位)を指定します。「はい」等の短いフレーズを認識させたい場合は短くしてみてください。短くするとあくびや鼻をすする音などでハルシネーション(誤認識)が出やすくなります。

* その他オプションはyukariwhisper.ini内を見てください。  

# Q&A
* 動かない！  
 エラー画面をキャプチャして[issues](https://github.com/tyapa0/YukariWhisper/issues)へ投稿、もしくは[Xへリプライ](https://twitter.com/TYA_PA_)をしていただければ確認します。  

* マイクが認識しない？  
 音声のリアルタイムプロットの波形が紫になっているか確認してください。  
 マイクの入力や音量がちょうど良くなるように調節してください。  
 ![YukariWhisper06.png.](./image/YukariWhisper08.png "YukariWhisper06")  


* マウスやJoyStickの音を拾ってブブブブブブブブ等の文字が大量に出る。
  1. まずはマイクの音量を認識ギリギリまで絞ってみてください。
  1. [NVIDIA Broadcastアプリ](https://www.nvidia.com/ja-jp/geforce/broadcasting/broadcast-app/)等のノイズキャンセル技術を検討してみてください。  
  1. `yukariwhisper.ini`の vad_threshold=0.5など、少し大きくしてみてください。
  1. `ngwords.txt`に入れたキーワードを含む言葉は無視されます。5～8文字程度入れてみてください。  
  NVIDIA Broadcastアプリをインストールした後、マイク選択はNVIDIA Broadcastを選択してください。  
  ![YukariWhisper06.png.](./image/YukariWhisper06.png "YukariWhisper06")  

* 起動時にDLしたモデルはどこ？  
  **C:\\Users\\ユーザー名\\.cache\\huggingface\\hub** に入っています。完全アンインストールする場合はその中にある models--Systran--faster-whisper-large-v3 や models--kotoba-tech--kotoba-whisper-v1.0-faster などを削除してください。他にもAI系のソフトを使っていると、何かしらファイルがあるので必要なものは残してください。


# Planned Features
* ~~デバイスリストの文字化けを修正する(python-sounddeviceへ変更)~~  
* ~~区切り検出をspeech_recognitionからSilero VADへ完全移行する  
  参考：https://github.com/jianfch/stable-ts~~
* ~~pyqtgraphで音声のリアルタイムプロットを表示する  
  音声認識中かそうで無いかをインジケータ表示で分かりやすくする  
  定常ノイズを可視化しユーザーに認識させる~~  
* ~~Kotoba-Whisperの評価 (distil-whisper)  
  参考：[https://github.com/huggingface/distil-whisper/tree/main/training](https://huggingface.co/kotoba-tech/kotoba-whisper-v1.0)~~　　

# コード構成 (開発者向け)
* `recognizer.py` … 認識本体。モデルの違いはここでは意識しません。
* `plotlib.py` … 波形ウインドウ(matplotlib)。今回 `recognizer.py` から分離しました。波形バッファ・発話色・Ampスライダー・FuncAnimation はすべてこちらです。
* `whisper_utils.py` … faster-whisper(CTranslate2)バックエンド。
* `haas_utils.py` … Haas-ja-v1.0(ONNX)バックエンド。自動ダウンロードと、Whisper側と共通の `transcribe() -> [.text]` 形式への変換を行います。
* `google_utils.py` … Google音声認識(デバッグ用)。音声はFLAC化せず16bit PCM(`audio/l16`)で送ります。
* 認識結果の後処理(タイムアウト判定・NFC正規化・NGワード・送信)は全エンジン共通。
* `settings.py` … ini解析。`haas_format` / `haas_threads` / `haas_repo` は任意項目で、古いiniに無くてもデフォルト値で動きます。Haas / google 選択時はGPU判定(compute_type算出)を行わないため、CUDAが無い環境でもHaasは起動できます。

# License
"YukariWhisper" is under [MIT license](https://en.wikipedia.org/wiki/MIT_License).
