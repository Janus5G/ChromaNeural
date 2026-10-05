# ChromaNeural

[English](../en/ChromaNeural-Installation.md) · [Dansk](../da/ChromaNeural-Installation-DA.md) · [Deutsch](../de/ChromaNeural-Installation.md) · [Français](../fr/ChromaNeural-Installation.md) · [日本語](ChromaNeural-Installation.md) · [简体中文](../zh-CN/ChromaNeural-Installation.md) · [हिन्दी](../hi-IN/ChromaNeural-Installation.md)
## インストール

ChromaNeural 0.2.21-rc.2 ドキュメント | 未公開候補 | 2026年10月3日

**rc.2 ドキュメントの状態：** この候補は一般公開されていません。ローカライズと拡張可能な i18n はローカル検証に合格しましたが、rc.2 のネイティブビルド／パッケージ受け入れは未完了です。以下のインストール、プラットフォーム、LAN/WAN、推論、実稼働サービスの証拠は、明示的に rc.2 と記したもの以外は過去の rc.1 の証拠です。rc.1 のダウンロードには rc.2 のローカライズは含まれません。

## 過去の rc.1 インストール参照

公開 rc.2 パッケージはまだありません。以下の名前とコマンドは意図的に rc.1 のままで、言語選択や登録簿を導入しません。準備済みローカル rc.2 は --language でその起動の言語を指定し、Windows は -Language を受け付けます。GUI 選択は保存されます。rc.1 パッケージの改名や未検証 rc.2 URL への置換をしないでください。

## 導入前

公式リリースから取得します：

../../RELEASE_NOTES.md

プラットフォームとアーキテクチャを正確に選びます。未署名・macOS 未公証のため OS が警告／遮断する場合があります。保護を全体無効にせず、提供元とハッシュを確認してから判断してください。

- Windows x64：ChromaNeural-0.2.21-rc.1-windows-x64.exe
- Linux amd64：chromaneural_0.2.21.rc.1_amd64.deb
- macOS Intel x86_64：ChromaNeural-0.2.21-rc.1-macos-x86_64.zip
- ソース：ChromaNeural-0.2.21-rc.1-source.zip
- チェックサム：SHA256SUMS.txt

GitHub が DEB 名の ~rc.1 を .rc.1 に正規化しました。バイトと SHA-256 は同一で、内部 Debian 版は ~rc.1 のままです。

### SHA-256 確認

ダウンロードしたパッケージのディレクトリで実行します。

Windows PowerShell：
```
Get-FileHash -Algorithm SHA256 -LiteralPath '.\ChromaNeural-0.2.21-rc.1-windows-x64.exe'
```

Linux：
```
sha256sum chromaneural_0.2.21.rc.1_amd64.deb
```

macOS：
```
shasum -a 256 ChromaNeural-0.2.21-rc.1-macos-x86_64.zip
```

SHA256SUMS.txt の正確なファイル名の64文字全体と照合し、違えば停止します。チェックサムはバイト完全性の確認で、独立した発行者認証ではありません。公開5ハッシュは docs/DOWNLOADS.md にもあります。

<!-- page -->
## Windows x64

### 前提条件

Python 3.14 と Tk、py/pyw ランチャー、Node.js 24 を導入します。EXE はユーザー別オフラインインストーラーで、完全に固定同梱した Python/Node ランタイムではありません。一時展開と導入に約 2 GB の空きが必要です。

### 手順

1. 前述の方法で EXE を確認します。
2. OS 警告を確認して開き、導入を承認します。
3. プログラムは版別の次の場所へ入ります：
```
%LOCALAPPDATA%\Programs\ChromaNeural\0.2.21-rc.1
```
4. そこから Start-ChromaNeural.ps1 を起動します：
```
& "$env:LOCALAPPDATA\Programs\ChromaNeural\0.2.21-rc.1\Start-ChromaNeural.ps1"
```
5. 初回はリソース設定を保存します。ログインと接続で任意の公開 API 確認ができます。

導入ログは %TEMP%\ChromaNeural-install.log。既存の導入先は拒否し、自動上書きアップグレードはしません。自動参加や OS 自動起動登録はありません。デスクトップショートカットもこの RC は自動作成しません。

ICP SDK と固定依存物は同梱済みです。導入のために npm ci を実行したり、NODE_PATH を古い開発環境に向けたりする必要はありません。

### 削除と利用者の状態

完全終了してください。版別導入フォルダーだけを消せばプログラムが削除されます。%LOCALAPPDATA%\ChromaNeural\client の状態、作業領域、別の ID ディレクトリは保持するか、明示的判断で別途扱います。自動アンインストーラーはありません。

<!-- page -->
## Linux amd64

ネイティブ検証対象は Ubuntu 24.04 amd64 で、すべての配布版・版番号ではありません。WSL はネイティブ Linux 検証の代替には数えません。

Python 3.11+、Tk、ディストリビューションの cryptography、Node.js 20+、libgomp1 が必要です。依存物は OS パッケージ管理で入れます。取得ディレクトリから：
```
sudo apt install ./chromaneural_0.2.21.rc.1_amd64.deb
```

アプリメニューまたは次で起動：
```
chromaneural
```

プログラムは /opt/chromaneural、ランチャーは /usr/bin/chromaneural、デスクトップ情報は /usr/share/applications/chromaneural.desktop。導入後の npm ネット取得や状態の自動移行はありません。

ネイティブビルド、展開、完全性、SDK、CLI、Xvfb/Tk は検証済み。完全な dpkg 導入／削除は未検証です。公開 desktop 項目に製品固有アイコン参照はありませんが起動できます。

## macOS Intel x86_64

macOS 15+、正常な Tk を持つ Python 3.14、Node.js 24 が必要です。同じ Python に固定暗号依存物を入れます。受け入れ済みソースのルートで：
```
python3 -m pip install --require-hashes -r packaging/requirements-runtime.txt
```

固定版は cryptography 46.0.5、cffi 2.1.1、pycparser 3.0。実行前提条件であり、II 認証情報の要求ではありません。

ZIP を展開し ChromaNeural.app を Applications に移し、提供元と警告を確認して開きます。Intel 専用で、Universal 2、Apple Silicon、Rosetta はこの版の受け入れ対象ではありません。

ネイティブビルド、完全性、SDK、CLI、Tk は検証済み、手動 GUI は未検証です。未署名・未公証で製品固有バンドルアイコンもありません。macOS に Qwen/llama.cpp は同梱しません。明示選択のローカル Ollama は別途モデル導入が必要で、制御付きバックグラウンド貢献は非対応です。

<!-- page -->
## 初回起動とその後

![実際の Windows リソース設定。ウィンドウ装飾は OS により異なります。](../images/chroma-neural-resources.png)

設定を選び保存します。概要は確定値だけを表示し、ダッシュは収益の約束ではありません。一般共有は無効です。**Afslut ChromaNeural** で完全終了します。

起動失敗時はまず前提条件とパッケージ／アーキテクチャを確認し、状態を保全します。ID を初期化したり私的データを報告に添付したりしないでください。利用ガイドとプライバシーガイドを参照してください。

導入は Internet Identity、本番バックエンド、ブラウザーセッションを変えません。公開 API 到達は Windows で検証済みですが、実稼働 II の全工程、参加承認、移行は未検証です。

Android と iOS の公式対応は延期です。

オンライン文書は不変の RC バイナリ／ソース ZIP より新しい場合があります。文書やアイコンのためだけに公開ファイルを置換しません。アイコン状態は docs/BRANDING.md を参照してください。

MCP は rc.2 後に別途判断・承認する機能であり、ここでは未実装です。この文書は本番環境や Internet Identity の新たな変更を意味しません。
