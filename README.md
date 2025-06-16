# streamlit_sdvxocr

## 概要
これは、Streamlitの学習を目的として作成したGemini APIを利用したアプリです。
SOUND VOLTEXのリザルト画像から楽曲情報やスコア、クリアタイプなどを抽出し、CSVファイルで出力します。

## 使用技術
- Python3
- Streamlit
- Google Gemini 1.5 Flash

## 使い方
1. SOUND VOLTEXのリザルト画像を用意してください。NORMAL SCORE表示でもEX SCORE表示でも利用可能です。
2. 正常にアップロードされたことを確認し、「n枚の画像を処理する」ボタンを押下してください。Geminiにより文字認識が行われます。
3. Geminiによる処理が正常に終了すると、認識結果が表形式で出力されます。同じ内容のものをCSVデータとしてダウンロードすることも可能です。
