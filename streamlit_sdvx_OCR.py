import streamlit as st
from PIL import Image
import google.generativeai as genai
import os
import pandas as pd
import json
from datetime import datetime

api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Gemini APIキーが設定されていません。'.streamlit/secrets.toml' または環境変数を確認してください。")
    st.stop()

try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"APIキーの設定中にエラーが発生しました: {e}")
    st.stop()


st.set_page_config(
    page_title="Gemini SDVX Result OCR",
    page_icon="🎵",
    layout="wide",
)

st.title("Gemini SDVX Result OCR")
st.write("SOUND VOLTEXのリザルト画像をアップロードすると、Geminiが情報を読み取り、CSVで保存できます。")

if "results" not in st.session_state:
    st.session_state.results = None

PROMPT_TEXT = """
このSOUND VOLTEXのリザルト画像から以下の情報を抽出し、指定されたキーを持つJSON形式で出力してください。

- "曲名": "title" (先頭に「-」やスペースが含まれている場合は削除し、それ以降の文章を出力してください)
- "アーティスト名": "artist"(先頭に「-」やスペースが含まれている場合は削除し、それ以降の文章を出力してください)
- "難易度表記": "difficulty_name" (例: NOV, ADV, EXH, MXM, INF, GRV, HVN, VVD, XCD のいずれか)
- "レベル値": "level" (1から20の整数)
- "通常スコア": "score" (10,000,000 のようなカンマ区切りの数字は、カンマを削除して数値にしてください)
- "EX SCORE": "ex_score" (MAX 5桁のスコア)
- "RATEの名前": "rate_name" (MAXXIVE RATE, EXCESSIVE RATE, EFFECTIVE RATE, HEXATIVE RATE のいずれか)
- "RATEのパーセンテージ": "rate_percentage" (「%」は含めず小数点以下も含めた数値のみ)
- "クリアタイプ": "clear_type" (例: PERFECT, ULTIMATE CHAIN, COMPLETE, SAVED, CRASH のいずれか)

全ての情報を正確に抽出してください。
もし画像内に情報が存在しない、または読み取れない項目があった場合は、その値に "N/A" を設定してください。
出力はJSONオブジェクトのみとし、前後に説明文や ```json ``` のようなマークダウンは含めないでください。

【抽出してほしいキーのリスト】
- `title`
- `artist`
- `difficulty_name`
- `level`
- `score`
- `ex_score`
- `rate_name`
- `rate_percentage`
- `clear_type`

【出力形式の厳密な例】
```json
{
  "title": "ここに曲名が入ります",
  "artist": "ここにアーティスト名が入ります",
  "difficulty_name": "EXH",
  "level": 18,
  "score": 9987654,
  "ex_score": 5800,
  "rate_name": "EXCESSIVE RATE",
  "rate_percentage": 99.5,
  "clear_type": "COMPLETE"
}
"""

uploaded_files = st.file_uploader(
    "リザルト画像をアップロードしてください（複数選択可）",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if uploaded_files:
    
    if st.button(f"{len(uploaded_files)}枚の画像を処理する", type="primary", use_container_width=True):
        st.session_state.results = None # 結果をリセット
        extracted_data = []
        
        progress_bar = st.progress(0, text="処理を開始します...")
        with st.spinner("Geminiが画像を1枚ずつ処理中..."):
            for i, uploaded_file in enumerate(uploaded_files):
                try:
                    image = Image.open(uploaded_file)

                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content([PROMPT_TEXT, image])
                    
                    # response.text 内の ```json ... ``` などを取り除く
                    clean_response = response.text.strip().replace("```json", "").replace("```", "").strip()
                    st.info(f"Geminiからの生データ for {uploaded_file.name}: {response.text}")
                    data = json.loads(clean_response)
                    
                    data['filename'] = uploaded_file.name
                    extracted_data.append(data)

                except json.JSONDecodeError:
                    st.warning(f"**{uploaded_file.name}**: Geminiからの応答がJSON形式ではありませんでした。スキップします。")
                    st.text(f"応答内容: {response.text[:200]}...") # デバッグ用
                except Exception as e:
                    st.error(f"**{uploaded_file.name}**: 処理中にエラーが発生しました: {e}")

                progress_bar.progress((i + 1) / len(uploaded_files), text=f"処理中: {uploaded_file.name}")

        progress_bar.empty()

        if extracted_data:
            df = pd.DataFrame(extracted_data)
            
            column_order = [
                'filename', 'title', 'artist', 'difficulty_name', 'level', 
                'score', 'ex_score', 'rate_name', 'rate_percentage', 'clear_type'
            ]
            # 存在しない列は無視する
            df = df.reindex(columns=[col for col in column_order if col in df.columns])

            st.session_state.results = df
            st.success(f"✅ {len(extracted_data)} / {len(uploaded_files)} 件の画像の処理が完了しました。")
        else:
            st.warning("有効なデータを抽出できませんでした。")


# 結果の表示
if st.session_state.results is not None:
    st.divider()
    st.subheader("抽出結果")
    
    df_results = st.session_state.results

    st.dataframe(df_results)
    
    st.subheader("ダウンロード")
    
    # CSVダウンロード
    today_string = datetime.now().strftime('%Y-%m-%d')
    dynamic_filename = f"sdvx_scores_{today_string}.csv"

    csv_data = df_results.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="CSV形式でダウンロード",
        data=csv_data,
        file_name=dynamic_filename,
        mime="text/csv",
        use_container_width=True,
    )

# アップロードファイルがない場合
if not uploaded_files:
    st.info("画面上部のボックスに、スコアが記載されたリザルト画像をドラッグ＆ドロップしてください。")
