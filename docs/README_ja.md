<div align="center">
  
[English](../README.md) | 日本語

<h1 id="title">📅 NL Calender 📅</h1>

</div>

自然言語で記述された予定をカレンダーに登録・修正する簡易的なWebツールです。
ローカルのみで動作します。

このツールの主な特徴は以下の通りです。
- 登録した予定のローカル保存機能
- 登録済み予定の自然言語クエリによる編集・削除機能

# 使い方

## 環境設定
> [!NOTE]
> **venvなどの何らかの仮想環境で実行することを強く推奨します。**

requirements.txtに記載されたライブラリとtorchライブラリを以下のコマンドでインストールしてください。
- requirements.txt
```
pip install -r requirements.txt
```
- torch (GPUを使用する場合）

> [!NOTE]
> torchはGPUバージョンによって異なるため、バージョンと互換性のあるものをお使いください。
```
pip install torch
```

## Qwen3のダウンロード
このツールは自然言語の解析に [Qwen3](https://github.com/QwenLM/Qwen3)を使用します。
パラメータ依存性のため、ほかのLLMで代用することはできません。
[HuggingFace](https://huggingface.co/Qwen) などからローカルにダウンロードしてください。

快適・安全な動作のために、お使いのGPUのVRAMメモリよりも少ないパラメータサイズのモデルを使用することを推奨します。

なお、"NLParser.py"のコードを修正することで別のLLMを使用できるようにすることも可能です。

## LLMへのパスを通す
setting.envのLLMのパスを、ダウンロードしたLLMのパス名に変更してください。
```
LLM_MODEL_PATH = path/to/downloaded/LLM
```

## UI起動
ダウンロードしたディレクトリに移動します。
```
cd /path/to/this/app
```
上記設定を終えた環境で、下記コマンドを実行してください。

既定のWebブラウザでアプリが起動します。
```
streamlit run UI.py
```

# ライセンス

このリポジトリのコードは Apache License 2.0 のもとで公開されています。詳細は [LICENSE](../LICENSE) ファイルをご確認ください。

> [!IMPORTANT]
> 本ツールで使用されるQwen3は [Qianwen License Version 2](https://github.com/QwenLM/Qwen/blob/main/LICENSE) に基づいて提供されています。
> 本プロジェクトを商用やプロダクション環境で使用する場合は、必ず公式ライセンスをご確認ください。
