import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="予実管理ダッシュボード（デモ）", layout="wide")


@st.cache_data
def load():
    df = pd.read_csv(
        "ec_demo_data.csv",
        parse_dates=["order_date", "order_datetime", "first_order_date"],
    )
    # QuickSightの計算フィールドに相当する派生軸をここで作る
    df["粗利"] = df["sales_amount"] - df["cost_amount"]
    df["新規/既存"] = (
        df["first_order_date"].dt.date == df["order_date"].dt.date
    ).map({True: "新規", False: "既存"})
    df["価格帯"] = pd.cut(
        df["price"],
        bins=[-1, 2999, 9999, 29999, 10**9],
        labels=["～2,999円", "3,000～9,999円", "10,000～29,999円", "30,000円～"],
    )
    wd = ["月", "火", "水", "木", "金", "土", "日"]  # Monday=0
    df["曜日"] = df["order_date"].dt.weekday.map(lambda i: wd[i])
    df["時間帯"] = pd.cut(
        df["order_datetime"].dt.hour,
        bins=[-1, 5, 11, 17, 23],
        labels=["深夜(0-6)", "午前(6-12)", "午後(12-18)", "夜(18-24)"],
    )
    df["月"] = df["order_date"].dt.to_period("M").astype(str)
    return df


df = load()

st.title("予実管理ダッシュボード（デモ）")
st.caption("ダミーデータです。QuickSight移行前の、見た目・分析軸のすり合わせ用プロトタイプ。")

# ---------------- 分析軸（コントロール） ----------------
st.sidebar.header("分析軸")


def msel(label, col):
    opts = sorted(df[col].dropna().astype(str).unique())
    return st.sidebar.multiselect(label, opts, default=opts)


dmin, dmax = df["order_date"].min().date(), df["order_date"].max().date()
dr = st.sidebar.date_input("期間", (dmin, dmax), min_value=dmin, max_value=dmax)
cats = msel("商品カテゴリ", "category")
ranks = msel("会員ランク", "member_rank")
newold = msel("新規/既存", "新規/既存")
devs = msel("デバイス", "device")
chans = msel("流入媒体", "channel")
budget = st.sidebar.number_input("月次予算（円）", value=9_000_000, step=500_000)

# ---------------- フィルター適用 ----------------
m = pd.Series(True, index=df.index)
if len(dr) == 2:
    m &= (df["order_date"].dt.date >= dr[0]) & (df["order_date"].dt.date <= dr[1])
m &= df["category"].astype(str).isin(cats)
m &= df["member_rank"].astype(str).isin(ranks)
m &= df["新規/既存"].isin(newold)
m &= df["device"].astype(str).isin(devs)
m &= df["channel"].astype(str).isin(chans)
f = df[m]

if f.empty:
    st.warning("条件に合うデータがありません。分析軸の絞り込みを緩めてください。")
    st.stop()

# ---------------- KPIカード ----------------
sales = f["sales_amount"].sum()
gp = f["粗利"].sum()
orders = f["order_id"].nunique()
gpr = gp / sales * 100 if sales else 0
aov = sales / orders if orders else 0

k = st.columns(4)
k[0].metric("売上", f"¥{sales:,.0f}")
k[1].metric("粗利", f"¥{gp:,.0f}")
k[2].metric("粗利率", f"{gpr:.1f}%")
k[3].metric("客単価", f"¥{aov:,.0f}")

# ---------------- 売上進捗（月次 実績 vs 予算） ----------------
st.subheader("売上進捗（月次 実績 vs 予算）")
mon = f.groupby("月")["sales_amount"].sum().reset_index()
fig = px.bar(mon, x="月", y="sales_amount", labels={"sales_amount": "売上", "月": ""})
fig.add_hline(y=budget, line_dash="dash", annotation_text="月次予算")
st.plotly_chart(fig, use_container_width=True)

# ---------------- 2カラム ----------------
c1, c2 = st.columns(2)
with c1:
    st.subheader("流入媒体別 売上")
    ch = (
        f.groupby("channel")["sales_amount"]
        .sum()
        .sort_values()
        .reset_index()
    )
    st.plotly_chart(
        px.bar(ch, x="sales_amount", y="channel", orientation="h",
               labels={"sales_amount": "売上", "channel": "媒体"}),
        use_container_width=True,
    )
with c2:
    st.subheader("カテゴリ別 売上・粗利")
    cat = f.groupby("category")[["sales_amount", "粗利"]].sum().reset_index()
    st.plotly_chart(
        px.bar(cat, x="category", y=["sales_amount", "粗利"], barmode="group",
               labels={"value": "金額", "category": "カテゴリ", "variable": ""}),
        use_container_width=True,
    )

# ---------------- 曜日 × 時間帯 ヒートマップ ----------------
st.subheader("曜日 × 時間帯 の売上ヒートマップ")
wd_order = ["月", "火", "水", "木", "金", "土", "日"]
hb_order = ["深夜(0-6)", "午前(6-12)", "午後(12-18)", "夜(18-24)"]
pivot = (
    f.pivot_table(index="時間帯", columns="曜日", values="sales_amount",
                  aggfunc="sum", observed=False)
    .reindex(index=hb_order, columns=wd_order)
)
st.plotly_chart(
    px.imshow(pivot, aspect="auto", labels=dict(color="売上"), text_auto=False),
    use_container_width=True,
)

with st.expander("明細データを見る"):
    st.dataframe(f, use_container_width=True)
