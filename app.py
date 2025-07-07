import streamlit as st
import pandas as pd
import plotly.express as px
import io
import numpy as np
import random

# --- ページの基本設定 ---
st.set_page_config(
    page_title="成績分析ツール",
    page_icon="📊",
    layout="wide"
)

# --- カスタムCSSでUIデザインを調整 ---
st.markdown("""
<style>
/* --- 全体のカラー設定 --- */
:root {
    --primary-color: #FF6347; /* Tomato */
    --light-primary-color: #FFF0E6; /* Light Orange Background */
    --text-on-light-bg: #D9534F; /* Darker Orange Text */
    --border-color: #FFA07A; /* LightSalmon */
}

/* --- 情報・成功メッセージのスタイル --- */
div[data-testid="stInfo"], div[data-testid="stSuccess"] {
    background-color: var(--light-primary-color);
    border: none;
    border-radius: 5px;
}
div[data-testid="stSuccess"] {
    color: var(--text-on-light-bg);
}
div[data-testid="stSuccess"] svg {
    fill: var(--text-on-light-bg);
}


/* --- ボタンのスタイル --- */
/* 分析モード選択ボタン (A, B) */
div[data-testid="stButton"] > button:not([kind="primary"]) {
    background-color: var(--light-primary-color);
    color: var(--text-on-light-bg);
    border: 1px solid var(--border-color);
    width: 100%;
}
div[data-testid="stButton"] > button:not([kind="primary"]):hover {
    background-color: #FFE0D1;
    border-color: var(--primary-color);
    color: var(--primary-color);
}

/* グラフ作成ボタン */
div[data-testid="stButton"] > button[kind="primary"] {
    background-color: var(--primary-color);
    color: white;
    border: none;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    background-color: #E5533D; /* Darker Tomato */
    color: white;
}

/* --- テキスト入力エリアのスタイル --- */
.stTextArea textarea {
    border: 1px solid #d3d3d3;
    border-radius: 5px;
}
.stTextArea textarea:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 2px rgba(255, 99, 71, 0.2);
}

/* --- 複数選択ボックスで選択したアイテムのスタイル --- */
div[data-baseweb="tag"], div[data-testid="stTag"] {
    background-color: var(--light-primary-color) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 5px !important;
}
div[data-baseweb="tag"] > div, div[data-testid="stTag"] > div {
    color: var(--text-on-light-bg) !important;
}
div[data-baseweb="tag"] span[role="button"] svg, div[data-testid="stTag"] span[role="button"] svg {
    fill: var(--text-on-light-bg) !important;
}
</style>
""", unsafe_allow_html=True)


# --- アプリのタイトルと説明 ---
st.title("📊 成績分析ツール")
st.info(
    "**使い方**\n"
    "1. 必ず1行目をタイトル行として、Excelなどを範囲指定してコピーして下のボックスに貼り付けます。\n"
    "   ※不要な列が含まれたまま貼り付けても構いません。\n"
    "2. 実行したい分析のボタン（AまたはB）を押して、データを読み込みます。\n"
    "3. 左のサイドバーで項目を設定し、グラフ作成ボタンを押してください。"
)

# --- セッションステートの初期化 ---
if 'df_final' not in st.session_state:
    st.session_state.df_final = None
if 'df_current' not in st.session_state:
    st.session_state.df_current = None
if 'df_past' not in st.session_state:
    st.session_state.df_past = None
if 'analysis_mode' not in st.session_state:
    st.session_state.analysis_mode = None
if 'fig_a' not in st.session_state:
    st.session_state.fig_a = None
if 'figs_b' not in st.session_state:
    st.session_state.figs_b = []
if 'compare_mode' not in st.session_state:
    st.session_state.compare_mode = False
if 'ready_to_merge' not in st.session_state:
    st.session_state.ready_to_merge = False
if 'current_data_text' not in st.session_state:
    st.session_state.current_data_text = ""

# --- デモデータ生成関数 ---
def generate_demo_data():
    surnames = ["佐藤", "鈴木", "高橋", "田中", "渡辺", "伊藤", "山本", "中村", "小林", "加藤", "吉田", "山田", "佐々木", "山口", "松本", "井上", "木村", "林", "斎藤", "清水"]
    given_names = ["太郎", "花子", "一郎", "美咲", "健太", "さくら", "大輔", "愛", "翔太", "陽子", "直樹", "恵美", "拓也", "舞", "誠", "優子", "雄太", "杏奈", "浩二", "彩"]
    
    names = list(set([f"{random.choice(surnames)} {random.choice(given_names)}" for _ in range(100)]))
    random.shuffle(names)
    names = names[:60]

    data = {
        "組": [1]*20 + [2]*20 + [3]*20,
        "氏名": names,
        "部活": np.random.choice(["野球", "サッカー", ""], 60, p=[0.25, 0.25, 0.5]),
        "国語": np.random.randint(30, 101, size=60),
        "数学": np.random.randint(30, 101, size=60),
        "英語": np.random.randint(30, 101, size=60)
    }
    df = pd.DataFrame(data)
    return df.to_csv(sep='\t', index=False)

# --- 【追加】データ前処理関数 ---
def preprocess_dataframe(df):
    """文字列型の列にある空欄や欠損値を '(未所属)' に置き換える"""
    for col in df.columns:
        # オブジェクト型（主に文字列）のカラムを対象
        if pd.api.types.is_object_dtype(df[col]):
            # 空白文字列をNaNに統一してから、まとめて置換
            df[col] = df[col].replace(r'^\s*$', np.nan, regex=True).fillna('（未所属）')
    return df

# --- UI: データ入力エリア ---
col_label, col_demo, col_toggle = st.columns([1.5, 1, 1])
with col_label:
    st.subheader("▼ データ貼り付けエリア")
with col_demo:
    if st.button("デモデータを使用"):
        st.session_state.current_data_text = generate_demo_data()
with col_toggle:
    st.session_state.compare_mode = st.toggle("過去の結果と比較", value=st.session_state.compare_mode, key="compare_toggle")

data_input = st.text_area("現在のデータを貼り付け", value=st.session_state.current_data_text, height=200, placeholder="（ここに現在のデータを貼り付けます）", label_visibility="collapsed", key="current_data_input_area")

if st.session_state.compare_mode:
    past_data_input = st.text_area("過去のデータを貼り付け", height=200, placeholder="（ここに過去のデータを貼り付けます）", label_visibility="collapsed")
else:
    past_data_input = None

# --- データ処理関数 ---
def process_data_inputs(current_data_str, past_data_str, compare_mode_is_on):
    st.session_state.ready_to_merge = False
    if not current_data_str:
        st.warning("現在のデータを入力してください。")
        return

    try:
        df_current = pd.read_csv(io.StringIO(current_data_str), sep='\t')
        df_current = preprocess_dataframe(df_current) # 【追加】前処理を実行
        st.session_state.df_current = df_current
        st.success("✅ 現在のデータを読み込みました。")

        if not compare_mode_is_on:
            st.session_state.df_final = df_current
            st.write("プレビュー:")
            st.dataframe(st.session_state.df_final.head())
        else:
            if not past_data_str:
                st.warning("比較モードがONです。過去のデータを入力してください。")
                st.session_state.df_final = df_current
                return
            try:
                df_past = pd.read_csv(io.StringIO(past_data_str), sep='\t')
                df_past = preprocess_dataframe(df_past) # 【追加】前処理を実行
                st.session_state.df_past = df_past
                st.success("✅ 過去のデータを読み込みました。")
                st.session_state.ready_to_merge = True
            except Exception as e:
                st.error(f"過去データの読み込みに失敗しました: {e}")
    except Exception as e:
        st.error(f"現在のデータの読み込みに失敗しました: {e}")

# --- 分析モード選択ボタン ---
col1, col2 = st.columns(2)
with col1:
    if st.button("A. 散布図で相関を分析"):
        st.session_state.analysis_mode = 'A'
        st.session_state.fig_a = None
        st.session_state.figs_b = []
        process_data_inputs(data_input, past_data_input, st.session_state.compare_mode)
with col2:
    if st.button("B. 科目ごとに集団を比較"):
        st.session_state.analysis_mode = 'B'
        st.session_state.fig_a = None
        st.session_state.figs_b = []
        process_data_inputs(data_input, past_data_input, st.session_state.compare_mode)

# --- データ結合UI ---
if st.session_state.ready_to_merge:
    st.info("過去のデータとの結合設定")
    common_cols = list(set(st.session_state.df_current.columns) & set(st.session_state.df_past.columns))
    if not common_cols:
        st.error("エラー: 現在のデータと過去のデータに共通の列がありません。結合できません。")
    else:
        preferred_keys = ["生徒名", "学籍番号", "氏名", "ID"]
        default_index = 0
        for key in preferred_keys:
            if key in common_cols:
                default_index = common_cols.index(key)
                break
        merge_key = st.selectbox("どの列の値を基準に結合しますか？", common_cols, index=default_index)
        
        if st.button("データを結合する"):
            try:
                df_current = st.session_state.df_current.copy()
                df_past = st.session_state.df_past.copy()
                past_rename_cols = {col: f"{col}_過去" for col in df_past.columns if col != merge_key}
                df_past.rename(columns=past_rename_cols, inplace=True)
                df_merged = pd.merge(df_current, df_past, on=merge_key, how='left')
                st.session_state.df_final = df_merged
                st.session_state.ready_to_merge = False
                st.success("✅ データの結合が完了しました。")
                st.write("結合後のデータのプレビュー:")
                st.dataframe(st.session_state.df_final.head())
            except Exception as e:
                st.error(f"データの結合中にエラーが発生しました: {e}")

# --- サイドバーとグラフ作成ロジック ---
if st.session_state.df_final is not None:
    df = st.session_state.df_final
    column_names = df.columns.tolist()
    
    # モードA: 散布図
    if st.session_state.analysis_mode == 'A':
        st.sidebar.header("A: 散布図の設定")
        x_axis_col = st.sidebar.selectbox("X軸（横軸）", column_names, index=0, key="a_x_axis")
        y_axis_col = st.sidebar.selectbox("Y軸（縦軸）", column_names, index=1 if len(column_names) > 1 else 0, key="a_y_axis")
        color_options = ["色分けしない"] + column_names
        color_col = st.sidebar.selectbox("色分け", color_options, index=0, key="a_color")
        hover_data_cols = st.sidebar.multiselect("ホバー情報", column_names, default=[], key="a_hover")

        if st.sidebar.button("グラフ作成", type="primary"):
            try:
                plot_df = df.copy()
                color_argument = color_col if color_col != "色分けしない" else None
                if color_argument:
                    plot_df[color_argument] = plot_df[color_argument].astype(str)
                fig = px.scatter(plot_df, x=x_axis_col, y=y_axis_col, color=color_argument, color_discrete_sequence=px.colors.qualitative.Vivid, hover_data=hover_data_cols, title=f"「{y_axis_col}」と「{x_axis_col}」の関係")
                fig.update_traces(marker=dict(size=12, line=dict(width=1.5, color='white')), selector=dict(mode='markers'))
                fig.update_layout(template="seaborn", plot_bgcolor='#f0f2f6', xaxis=dict(showgrid=True, gridwidth=1, gridcolor='white'), yaxis=dict(showgrid=True, gridwidth=1, gridcolor='white'), title_x=0, title_font_size=22, font=dict(family="Arial, sans-serif", size=14), legend_title_text=color_col if color_argument else '')
                st.session_state.fig_a = fig
            except Exception as e:
                st.session_state.fig_a = None
                st.error(f"グラフの作成中にエラーが発生しました: {e}")
        
        if st.session_state.fig_a:
            st.header("グラフ描画結果")
            st.plotly_chart(st.session_state.fig_a, use_container_width=True)
            st.success("🎉 グラフが完成しました！")
            if color_col != "色分けしない":
                st.caption("※凡例をクリックすると表示・非表示が切り替えられます")
            img_col, html_col = st.columns(2)
            with img_col:
                st.download_button("画像として保存 (PNG)", st.session_state.fig_a.to_image(format="png"), "scatter_plot.png", "image/png", use_container_width=True)
            with html_col:
                st.download_button("HTMLとして保存", st.session_state.fig_a.to_html(), "scatter_plot.html", "text/html", use_container_width=True)

    # モードB: 集団比較
    elif st.session_state.analysis_mode == 'B':
        st.sidebar.header("B: 集団比較の設定")
        x_axis_col_b = st.sidebar.selectbox("X軸（横軸）※クラスなど", column_names, index=1 if len(column_names) > 1 else 0, key="b_x_axis")
        y_axis_cols_b = st.sidebar.multiselect("Y軸（縦軸）（複数選択可）", [col for col in column_names if col != x_axis_col_b], default=[], key="b_y_axis")
        hover_data_cols_b = st.sidebar.multiselect("ホバー情報", column_names, default=[], key="b_hover")

        btn1_col, btn2_col = st.sidebar.columns(2)
        
        def create_comparison_charts(plot_type):
            if not y_axis_cols_b:
                st.warning("Y軸で使う列を1つ以上選択してください。")
                st.session_state.figs_b = []
                return

            try:
                figs_list = []
                for y_col in y_axis_cols_b:
                    stats_df = None
                    # 数値データの場合のみ統計量を計算
                    if pd.api.types.is_numeric_dtype(df[y_col]):
                        stats_df = df.groupby(x_axis_col_b)[y_col].describe()
                        stats_df = stats_df[['count', 'mean', 'std', 'min', '50%', 'max']].round(2)
                        stats_df.rename(columns={'count': '人数', 'mean': '平均点', 'std': '標準偏差', 'min': '最低点', '50%': '中央値', 'max': '最高点'}, inplace=True)

                    if plot_type == 'box':
                        fig = px.box(df, x=x_axis_col_b, y=y_col, color=x_axis_col_b, hover_data=hover_data_cols_b, color_discrete_sequence=px.colors.qualitative.Vivid, title=f"「{x_axis_col_b}」ごとの「{y_col}」の分布（箱ひげ図）")
                    else:
                        fig = px.strip(df, x=x_axis_col_b, y=y_col, color=x_axis_col_b, hover_data=hover_data_cols_b, color_discrete_sequence=px.colors.qualitative.Vivid, title=f"「{x_axis_col_b}」ごとの「{y_col}」の分布（散布図）")
                    
                    fig.update_layout(template="seaborn", plot_bgcolor='#f0f2f6', xaxis=dict(showgrid=True, gridwidth=1, gridcolor='white'), yaxis=dict(showgrid=True, gridwidth=1, gridcolor='white'), title_x=0, font=dict(family="Arial, sans-serif", size=14), legend_title_text=x_axis_col_b)
                    figs_list.append({'fig': fig, 'y_col': y_col, 'stats_df': stats_df})
                st.session_state.figs_b = figs_list
            except Exception as e:
                st.session_state.figs_b = []
                st.error(f"グラフの作成中にエラーが発生しました: {e}")

        with btn1_col:
            if st.button("①箱ひげ図", type="primary"):
                create_comparison_charts('box')
        with btn2_col:
            if st.button("②全員ﾌﾟﾛｯﾄ", type="primary"):
                create_comparison_charts('strip')

        if st.session_state.figs_b:
            st.header("グラフ描画結果")
            for i, item in enumerate(st.session_state.figs_b):
                fig = item['fig']
                y_col = item['y_col']
                stats_df = item['stats_df']
                
                st.subheader(f"「{y_col}」の集団比較")
                st.plotly_chart(fig, use_container_width=True)
                
                if stats_df is not None:
                    st.write(f"**▼「{y_col}」の基本統計量**")
                    st.dataframe(stats_df, use_container_width=True)

                img_col, html_col = st.columns(2)
                with img_col:
                    st.download_button(f"「{y_col}」を画像として保存 (PNG)", fig.to_image(format="png"), f"plot_{y_col}.png", "image/png", use_container_width=True, key=f"png_dl_{i}")
                with html_col:
                    st.download_button(f"「{y_col}」をHTMLとして保存", fig.to_html(), f"plot_{y_col}.html", "text/html", use_container_width=True, key=f"html_dl_{i}")
                st.markdown("---")
            st.success("🎉 全てのグラフが完成しました！")

# --- 著作権表示 ---
st.markdown(
    """
    <div style="text-align: center; padding: 2rem 1rem; color: #888; font-size: 0.8rem;">
        © YusukeEnomoto
    </div>
    """,
    unsafe_allow_html=True
)
