# flux-pymcprotocol_fxseries

三菱電機 PLC **FX シリーズ（1E フレーム）** 用の Python 通信ライブラリです。
既存の `pymcprotocol`（3E/4E フレーム専用）では対応できない FX シリーズ等との通信を、1E フレーム専用に設計することで実現しています。

## 特徴

* **FX シリーズ専用**: 1E フレーム（A互換1Eフレーム）通信に特化
* **多彩なアクセス**: ビット単位・ワード単位での一括読み書き（Batch Read/Write）に対応
* **バイナリ通信対応**: 高速なバイナリ通信方式を採用（※ASCII方式は未実装）
* **シンプルな API**: `pymcprotocol` に近い操作感で、FXシリーズへの移行もスムーズ
* **デバッグ機能**: 送受信データのバイナリを確認できるデバッグモードを搭載

## インストール

### GitHubから直接

```bash
pip install git+https://github.com/FluxEngine-dev/flux-pymcprotocol_fxseries.git
```

### 開発用（リポジトリをクローンした後）

```bash
pip install -e .
```

## 使い方

```python
from pymcprotocol_fxseries import Type1E

# 1. 接続設定 (IP, ポート番号を指定)
plc = Type1E(ip="192.168.0.10", port=5000)
plc.connect()

# 2. ワード読み込み (例: D1000 から 10 ワード)
values = plc.batchread_wordunits("D1000", 10)
print(f"D1000-D1009: {values}")

# 3. ビット書き込み (例: M0〜M3 を ON にする)
plc.batchwrite_bitunits("M0", [1, 1, 1, 1])

# 4. 切断
plc.close()
```

## 主要API一覧 (Type1E)

| カテゴリ | メソッド | 説明 |
| --- | --- | --- |
| **接続** | `connect(ip, port)` | PLCに接続します。 |
|  | `force_connect()` | 接続失敗時にリトライ（デフォルト3回）を試みます。 |
|  | `close()` / `shutdown()` | 接続を安全に切断します。 |
| **読み込み** | `batchread_wordunits()` | ワード単位で連続したデバイスを読み込みます。 |
|  | `batchread_bitunits()` | ビット単位で連続したデバイスを読み込みます。 |
| **書き込み** | `batchwrite_wordunits()` | 指定したデバイスから値を書き込みます。 |
|  | `batchwrite_bitunits()` | 指定したビットデバイスをON/OFFします。 |
| **設定** | `set_accessopt(pc, ...)` | PC番号や監視タイマーなどのオプションを設定します。 |
|  | `_set_debug(True)` | 通信のバイナリログをターミナルに表示します。 |

## 依存関係

* Python 3.10+
* (通信には標準ライブラリの `socket` を使用します)

## 制限事項

* **1E フレーム専用**: 3E/4E フレーム（Q/L/iQ-Rシリーズ等）とは互換性がありません。
* **バイナリモードのみ**: 現在、ASCII通信モードには対応していません。

## 関連資料

* FXシリーズ 通信マニュアル ([docs/FX_manual.pdf](docs/FX_manual.pdf))

## 更新履歴

* **v0.1.0 (2025/12/18)**:
* Initial Public Release.
* Path構成の整理とパッケージ化の対応。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細については、[LICENSE](LICENSE)ファイルをご覧ください。

Copyright (c) 2025 [FluxEngine-dev]
