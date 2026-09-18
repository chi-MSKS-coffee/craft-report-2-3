# -*- coding: utf-8 -*-
"""2-3 操作できるデータアプリ（配布スケルトン）。

このファイルに、受講データのダッシュボードを自分で作っていく。
課題（配布の「課題.pdf」）の Q1 から順に埋める。
使うデータは Craft College を題材にした学習用の想定データ（架空。実在の受講実績ではない）。

データの置き場所:
    このデータは 2-1「Pythonによるデータ分析」とまったく同じもの。同じデータを何度も配らないよう、
    2-1 の単元フォルダにだけ置いてある。2-1 の dataset フォルダを、この単元のフォルダにコピーしてから始めること
    （中身は データ一式.zip と データ定義書.pdf）。zip は下の ensure_dataset() が初回に自動で解凍する。

起動:
    cd 2-3_演習用Code && streamlit run app/app.py

設計の型：
    「分析ロジック（pandas の関数）」と「画面（Streamlit）」を混ぜない。
    分析は下の純粋関数に書く。画面は main() に書き、関数を呼ぶだけにする。
"""
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st
import altair as alt

DATA_DIR = "dataset"   # 2-1 からコピーしてきた dataset フォルダ
PASS = ["優秀合格", "合格"]


def ensure_dataset(data_dir: str = DATA_DIR) -> None:
    """dataset/データ一式.zip を、最初の1回だけ自動で解凍する（2-1 のノートブックと同じ方式）。"""
    base = Path(data_dir)
    zip_path = base / "データ一式.zip"
    if not zip_path.exists():
        return
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            if not (base / name).exists():
                z.extract(name, base)


# ---- 分析ロジック（Streamlit に依存しない純粋な関数・Q1 で作る） ----------

def load_data(data_dir: str = DATA_DIR) -> pd.DataFrame:
    ensure_dataset(data_dir)   # zip のままなら、ここで自動的に解凍される

    # TODO(Q1): 受講生.csv・課題成績.csv・学習ログ.csv を読み、受講生1人1行の表にまとめて返す。
    受講生df = pd.read_csv(Path(data_dir)/"受講生.csv")
    課題成績df = pd.read_csv(Path(data_dir)/"課題成績.csv")
    学習ログdf = pd.read_csv(Path(data_dir)/"学習ログ.csv")

    # 合格フラグ・平均点・課題提出数・総クリック数の列を作る。
    受講生df["合格"] = 受講生df["最終結果"].isin(PASS)

    平均点 = 課題成績df.groupby("受講生ID")["点数"].mean().rename("平均点")
    受講生df = 受講生df.merge(平均点, on="受講生ID", how="left")

    課題提出数 = 課題成績df.groupby("受講生ID")["課題ID"].size().rename("課題提出数")
    受講生df = 受講生df.merge(課題提出数, on="受講生ID",how="left").fillna({"課題提出数": 0})

    総クリック数 = 学習ログdf.groupby("受講生ID")["クリック数"].sum().rename("総クリック数")
    受講生df = 受講生df.merge(総クリック数, on="受講生ID",how="left")
    総クリックdf = 受講生df["講座名"] =="データサイエンス基礎"
    受講生df.loc[総クリックdf,"総クリック数"] = 受講生df.loc[総クリックdf,"総クリック数"].fillna(0)

    return 受講生df


def filter_students(df, kouza, nendai, gakureki):
    # TODO(Q2): 講座・年代・学歴の選択で絞り込んで返す（'すべて'・空リストは絞らない）。
    filter_df = df.copy()
    if kouza != "すべて":
        filter_df = filter_df[filter_df["講座名"] == kouza] 
    if nendai:
        filter_df = filter_df[filter_df["年代"].isin(nendai)]
    if gakureki:
        filter_df = filter_df[filter_df["学歴"].isin(gakureki)]
    return filter_df

    
def kpis(df) -> dict:
    受講生数 = len(df) 
    if 受講生数 == 0:
        # 人数0のときは0除算になるので、合格率などは計算せず「－」を返す。
        return {"受講生数": 0, "合格率": "－", "平均点": "－", "平均クリック数": "－"}

    結果 = {
        "受講生数": 受講生数,
        "合格率": df["合格"].mean() * 100,
        "平均点": df["平均点"].mean(),
        "平均クリック数": df["総クリック数"].mean(),
    }
    # 講座はデータサイエンス基礎以外、平均クリック数のNaN対応
    # 平均点は課題が０回の人のNaN対応(合格率は真偽だから本当はなくてもよい)
    for key in ["合格率", "平均点", "平均クリック数"]:
        if pd.isna(結果[key]):
            結果[key] = "－"
    return 結果


def pass_rate_by(df, col):
    # TODO(Q1/Q4): col ごとの合格率（%）を返す（講座名・学歴・年代 で使う）。
    return(df.groupby(col)["合格"].mean() * 100)
    


# ---- 画面（Streamlit）----------------------------------------------------
  # TODO(Q7): データ読み込みに @st.cache_data を付けて軽くする
@st.cache_data
def get_data():
    return load_data()

def main():
    st.set_page_config(page_title="受講データ ダッシュボード", layout="wide")
    st.title("受講データ ダッシュボード")
    # TODO(Q2): サイドバーに 講座・年代・学歴 の絞り込みを作る
    講座リスト = ["すべて"] + list(get_data()["講座名"].unique())
    kouza = st.sidebar.selectbox("講座",講座リスト)

    年代リスト = list(get_data()["年代"].unique())
    nendai = st.sidebar.multiselect("年代",年代リスト)

    学歴リスト = list(get_data()["学歴"].unique())
    gakureki = st.sidebar.multiselect("学歴",学歴リスト)

    filter_df = filter_students(get_data(),kouza,nendai,gakureki)
    if filter_df.empty:
        st.warning("該当する受講生がいません。絞り込み条件を変えてください。")
        return # 処理の打ち切り

   # TODO(Q3): 主要指標（受講生数・合格率・平均点…）を st.metric で横に並べる
    結果 = kpis(filter_df)
    表示 = dict(結果)
    
    表示["受講生数"] = f"{表示["受講生数"]:,}"
    for key in ["合格率", "平均点", "平均クリック数"]:
        if isinstance(表示[key], (int, float)):
            表示[key] = f"{表示[key]:.1f}"

    col1,col2,col3,col4 = st.columns(4)
    with col1:
        st.metric("受講生数",表示["受講生数"],border=True)
    with col2:
        st.metric("合格率",表示["合格率"],border=True)
    with col3:
        st.metric("平均点",表示["平均点"],border=True)
    with col4:
        st.metric("平均総クリック数",表示["平均クリック数"],border=True)
           
    # TODO(Q4): 合格率を「講座別・学歴別・年代別」の3つの切り口で見せる（st.tabs で切り替え）
    tab1, tab2, tab3 = st.tabs(["講座別", "学歴別", "年代別"])

    with tab1:
        st.header("講座別合格率")
        結果 = pass_rate_by(filter_df,"講座名").reset_index()
        結果.columns = ["講座名","合格率"]

        if kouza == "すべて":
            top = 結果.sort_values("合格率",ascending=False).iloc[0]
            st.info(f"最も合格率が高いのは「{top['講座名']}」({top['合格率']:.1f}%)")
            chart = alt.Chart(結果).mark_bar(size=30).encode(
                 y=alt.Y("講座名:N",sort="-x",axis=alt.Axis(labelLimit=200)),
                 x=alt.X("合格率:Q"),
                 color=alt.value("#0068c9"))
            st.altair_chart(chart,use_container_width=True,height=300)
        else:
            chart = alt.Chart(結果).mark_bar(size=30).encode(
                 y=alt.Y("講座名:N",sort="-x",axis=alt.Axis(labelLimit=200)),
                 x=alt.X("合格率:Q"),
                 color=alt.value("#0068c9"))
            st.altair_chart(chart,use_container_width=True,height=150)

    with tab2:
        st.header("学歴別合格率")
        結果 = pass_rate_by(filter_df,"学歴").reset_index()
        結果.columns = ["学歴","合格率"]
        chart = alt.Chart(結果).mark_bar(size=30).encode(
             y=alt.Y("学歴:N",sort="-x"),
             x=alt.X("合格率:Q"),
             color=alt.value("#0068c9"))
        st.altair_chart(chart,use_container_width=True,height=300)
    with tab3:
        st.header("年代別合格率")
        結果 = pass_rate_by(filter_df,"年代").reset_index()
        結果.columns = ["年代","合格率"]
        chart = alt.Chart(結果).mark_bar(size=30).encode(
             y=alt.Y("年代:N",sort="-x"),
             x=alt.X("合格率:Q"),
             color=alt.value("#0068c9"))
        st.altair_chart(chart,use_container_width=True,height=200)

    # TODO(Q5): 最終結果の内訳グラフと、学習量と合否（平均クリック）のグラフを描く
    st.header("最終結果")
    結果 = filter_df["最終結果"].value_counts().reset_index()
    結果.columns = ["最終結果","人数"]
    結果["区分"] = 結果["最終結果"].apply(lambda x: "合格" if x in PASS else "不合格")

    chart = alt.Chart(結果).mark_bar(size=30).encode(
        y=alt.Y("最終結果:N", sort="-x"),
        x=alt.X("人数:Q"),
        color=alt.Color("区分:N", scale=alt.Scale(domain=["合格","不合格"], range=["#0068c9","red"]), legend=None))
    st.altair_chart(chart, use_container_width=True,height=250)

    st.header("平均総クリック数と合否")
    結果 = filter_df.groupby("合格")["総クリック数"].mean().reset_index()
    結果["合格"] = 結果["合格"].map({True: "合格", False: "不合格"})
    結果.columns = ["結果","平均総クリック数"]

    if 結果["平均総クリック数"].isna().all():
        st.info("総クリック数は「データサイエンス基礎」の受講生のみ記録されているため、この講座ではグラフを表示できません。")
    else:
        st.info("総クリック数は「データサイエンス基礎」の受講生のみ記録されています。")
        chart = alt.Chart(結果).mark_bar(size=30).encode(
        y=alt.Y("結果:N"),
        x=alt.X("平均総クリック数:Q"),
        color=alt.Color("結果:N", scale=alt.Scale(domain=["合格","不合格"], range=["#0068c9","red"]), legend=None)
        )
        st.altair_chart(chart, use_container_width=True, height=200)

    # TODO(Q6): 絞り込み結果の一覧と、CSVダウンロードボタン（utf-8-sig）を付ける
    st.header("受講生一覧")
    st.dataframe(filter_df)
 
    csv = filter_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("CSVダウンロード",data=csv,file_name="受講生一覧.csv",mime="text/csv") 
  
if __name__ == "__main__":
    main()
# このファイルが直接実行されたときだけmain()を呼ぶ、importされたときは呼ばない
