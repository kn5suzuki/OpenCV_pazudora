# OpenCV でパズドラを作ってみた

## 動作確認環境

- macOS 13.3.1(a)
- python 3.10.3

venv に必要なパッケージのインストール

```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## 実行方法

```bash
python3 main.py
```

ウィンドウは自動的には閉じないので Ctrl+C を入力する必要がある。

## 操作方法

- ゲーム画面が表示され、PC 内部カメラが起動する
  <image src="images/image1.png">

- カメラに手を写すと自動的に検出される
  <image src="images/image2.png">

- 人差し指の先がカーソルになっており、人差し指と中指でオブジェクトを挟むようにすることで、中指との距離が一定より短くなったのを検知してオブジェクトを掴む
  <image src="images/image3.png">

- オブジェクトを移動し終わるとお互いに攻撃を行う。体力を削り切った方が勝利
