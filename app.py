# -*- coding: utf-8 -*-
# ECダッシュボード（Altair版）
# ※ グループ棒の xOffset エンコーディングを使うため Altair 5 以上が必要です。
#    pip install "altair>=5"
import calendar
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st

st.set_page_config(page_title="ECダッシュボード", layout="wide",
                   initial_sidebar_state="collapsed")

# QuickSight風のクリーンなカラーパレット
BLUE, LIGHT, GREEN, AMBER, PURPLE = "#0073bb", "#87c1eb", "#2ca02c", "#d67229", "#8c56cb"
GRAY = "#c8cdd4"
TARGETC, GAPPOS, GAPNEG = "#d62728", "#1d8102", "#d13212"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');

    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Noto Sans JP', sans-serif !important;
    }

    header[data-testid="stHeader"] { height:0; visibility:hidden; }

    /* 全体の背景は白 */
    .stApp { background-color: #ffffff !important; }
    .main .block-container { background-color: #ffffff !important; }
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
    h1, h2, h3 { color: #16191f; font-weight: 700; }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff !important;
        border: 1px solid #e9ebed !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        padding: 2px 4px !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div,
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"],
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"],
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="element-container"],
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] {
        background-color: transparent !important;
    }

    [data-testid="stTabs"] > div:first-child {
        background:#ffffff; border:1px solid #e9ebed; border-bottom:none;
        border-radius:10px 10px 0 0; padding:4px 10px 0 10px;
    }
    button[data-baseweb="tab"] { font-weight:600; color:#5f6b7a; font-size:15px; }
    button[data-baseweb="tab"][aria-selected="true"] { color:#0073bb !important; }
    [data-baseweb="tab-highlight"] { background-color:#0073bb !important; height:3px !important; }
    [data-testid="stTabs"] [role="tabpanel"] { padding-top: 10px; }

    .custom-title {
        background-color: #ffffff;
        border-left: 6px solid #0073bb;
        border-bottom: 1px solid #e9ebed;
        padding: 8px 16px;
        font-size: 16px !important;
        font-weight: 700;
        color: #16191f;
        border-radius: 2px 4px 0 0;
        margin-top: 4px;
        margin-bottom: 16px;
    }
    .axis-group {
        font-weight:700; color:#0073bb; font-size:13.5px;
        border-bottom:1px solid #e9ebed; padding:4px 2px;
        margin:6px 0 4px;
    }
    .sub-head {
        font-weight:700; color:#0073bb;
        border-bottom:2px solid #e9ebed; padding:2px 0 6px; margin-bottom:8px;
    }

    [data-testid="stMetric"], .custom-metric {
        background-color: #ffffff !important;
        border: 1px solid #e9ebed !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
        min-height: 92px;
        display: flex; flex-direction: column; justify-content: center;
        box-sizing: border-box;
    }
    [data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 700; color: #16191f; }
    [data-testid="stMetricLabel"] p, .custom-metric-label {
        font-size: 0.85rem !important;
        color: #5f6b7a !important;
        font-weight: 500 !important;
        margin-bottom: 2px !important;
    }

    [data-testid="stVegaLiteChart"], [data-testid="stVegaLiteChart"] > div,
    [data-testid="stVegaLiteChart"] canvas, [data-testid="stVegaLiteChart"] svg {
        background-color: #ffffff !important;
    }

    .stButton > button {
        background:#ffffff; border:1px solid #d5d9e0; border-radius:6px;
        color:#0073bb; font-weight:700;
    }
    .stButton > button:hover { background:#eaf3fb; border-color:#0073bb; }

    .badge-ok { background:#e6f4ea; color:#1d8102; border:1px solid #b7e1c1;
        border-radius:14px; padding:2px 12px; font-size:12.5px; font-weight:700; }
    .badge-ng { background:#fdeceb; color:#d13212; border:1px solid #f4bdb7;
        border-radius:14px; padding:2px 12px; font-size:12.5px; font-weight:700; }
    </style>
    """,
    unsafe_allow_html=True,
)

REQUIRED = ["order_date", "order_datetime", "member_rank", "cat_l", "cat_m", "cat_s",
            "price", "sales_amount", "cost_amount", "channel", "promo_type",
            "discount_amount", "feature_tag", "order_id"]

# ---- デモ属性のマスタ（CSVに無い分析軸を order_id から決定論的に導出）----
REPS = ["田中", "佐藤", "鈴木", "高橋", "伊藤"]
MAKERS = [f"メーカー{c}" for c in "ABCDEFGH"]
BRANDS = [f"ブランド{i:02d}" for i in range(1, 11)]
AGE_ORDER = ["10代", "20代", "30代", "40代", "50代", "60代", "70代", "80代", "90代"]
PRICE_ORDER = ["〜1,000円", "1,000〜3,000円", "3,000〜5,000円", "5,000〜10,000円", "10,000円〜"]
TRADE_ORDER = ["在庫型", "受注型", "直送型"]
CHOPPLE_ORDER = ["通常", "仕入れ"]
GENDER_ORDER = ["女性", "男性"]
RANK_ORDER = ["通常", "ゴールド"]

# 販促の月次計画予算（デモ）：ポイント45万/月、クーポン26万/月
BUDGET_M = {"ポイント": 450_000, "クーポン": 260_000}


@st.cache_data
def read_data():
    df = pd.read_csv("ec_demo_data.csv", parse_dates=["order_date", "order_datetime"])
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        return df, missing

    df["粗利"] = df["sales_amount"] - df["cost_amount"]
    df["member_rank"] = df["member_rank"].replace({"一般": "通常"})

    # --- デモ属性の導出（order_id の数値部から決定論的に付与） ---
    num = df["order_id"].astype(str).str.extract(r"(\d+)")[0].fillna("0").astype(int)
    n = num.to_numpy()
    df["取引区分"] = np.select([n % 10 < 6, n % 10 < 9], ["在庫型", "受注型"], default="直送型")
    df["営業担当"] = np.array(REPS)[n % len(REPS)]
    df["ちょっプル"] = np.where(n % 7 < 2, "仕入れ", "通常")
    df["メーカー"] = np.array(MAKERS)[(n // 7) % len(MAKERS)]
    df["ブランド"] = np.array(BRANDS)[(n // 3) % len(BRANDS)]
    r = n % 100
    df["年代"] = np.select(
        [r < 2, r < 20, r < 42, r < 64, r < 79, r < 89, r < 95, r < 98],
        AGE_ORDER[:8], default="90代")
    df["性別"] = np.where(n % 97 < 55, "女性", "男性")
    df["価格帯"] = pd.cut(df["price"], bins=[0, 1000, 3000, 5000, 10000, np.inf],
                       labels=PRICE_ORDER, right=False).astype(str)

    # --- 顧客ID（デモ）：ヘビー/ミドル/ライト層で偏りを持たせた決定論的な割当 ---
    h = (n * 2654435761) % 100000
    pool = np.select([h < 15000, h < 50000],
                     [h % 800,                      # ヘビー層：800人に注文の15%
                      800 + (h % 6000)],            # ミドル層：6,000人に35%
                     default=6800 + (h % 26000))    # ライト層：26,000人に50%
    df["顧客ID"] = [f"CUST{p:05d}" for p in pool]

    # --- 施策種類（デモ）：ポイント／クーポンの内訳分類 ---
    pt_types = np.array(["誕生月ポイント", "ランクアップ特典", "レビュー投稿", "新規入会"])
    cp_types = np.array(["10%OFFクーポン", "500円OFFクーポン", "送料無料クーポン", "会員限定クーポン"])
    df["施策種類"] = np.select(
        [df["promo_type"].eq("ポイント"), df["promo_type"].eq("クーポン")],
        [pt_types[n % 4], cp_types[(n // 5) % 4]], default="-")
    return df, []


df, _missing = read_data()
if _missing:
    st.error("CSV（ec_demo_data.csv）が最新版と一致していません。\n\n不足列：" + ", ".join(_missing))
    st.stop()

FULL = pd.Series(True, index=df.index)


def man(v):
    return f"{v/10000:,.0f}万円"


def to_man(s):
    return s / 10000


def _shift(key, delta):
    st.session_state[key] = int(st.session_state.get(key, 0)) + delta


def render_title(title, badge_html=""):
    st.markdown(f"<div class='custom-title'>{title}{badge_html}</div>", unsafe_allow_html=True)


def sub_head(text):
    st.markdown(f"<div class='sub-head'>｜{text}</div>", unsafe_allow_html=True)


def chart_with_nav(chart, show_nav_key, prefix, spacer_px=120):
    """＜＞ボタンをグラフの左右に配置して表示する（Altairチャート）"""
    if show_nav_key:
        c = st.columns([1, 20, 1])
        with c[0]:
            st.markdown(f"<div style='height:{spacer_px}px'></div>", unsafe_allow_html=True)
            st.button("＜", key=f"prev_{prefix}_{show_nav_key}", on_click=_shift,
                      args=(show_nav_key, -1), use_container_width=True)
        with c[1]:
            st.altair_chart(chart, use_container_width=True)
        with c[2]:
            st.markdown(f"<div style='height:{spacer_px}px'></div>", unsafe_allow_html=True)
            st.button("＞", key=f"next_{prefix}_{show_nav_key}", on_click=_shift,
                      args=(show_nav_key, 1), use_container_width=True)
    else:
        st.altair_chart(chart, use_container_width=True)


# 期間（年/月/日）用のX軸：文字は横書き。月ラベルは '/' 区切りで2行に折り返す。
def period_axis(title=None):
    return alt.Axis(labelAngle=0, labelExpr="split(datum.label, '/')", title=title)


def qs_style(chart):
    return (
        chart
        .configure(background="#ffffff", font="'Noto Sans JP', sans-serif")
        .configure_view(strokeWidth=0, fill="#ffffff")
        .configure_axis(
            labelColor="#16191f", titleColor="#16191f",
            gridColor="#f2f3f5", domainColor="#e9ebed", tickColor="#e9ebed",
            labelFontSize=11, titleFontSize=12,
        )
        .configure_axisX(grid=False)
        .configure_legend(orient="top", labelColor="#16191f", titleColor="#16191f",
                          labelFontSize=12, symbolType="square", symbolSize=150,
                          symbolStrokeWidth=0)
    )


# 月次の季節係数（目標側）
seasonality = {1: 1.00, 2: 0.90, 3: 1.025, 4: 0.975, 5: 0.975, 6: 0.95,
               7: 1.20, 8: 0.95, 9: 0.975, 10: 1.00, 11: 1.075, 12: 1.325}


def get_target(y, m, base):
    return base * seasonality.get(m, 1.0)


target_base = 32_000_000  # 月次の目標基準（百貨店規模）


@st.cache_data
def compute_daily_traffic():
    """サイト全体（全カテゴリ）の日次セッション数を作る（デモ推計）。"""
    base, _ = read_data()
    dates = base["order_date"].dt.strftime("%Y-%m-%d")
    months = base["order_date"].dt.strftime("%Y-%m")

    monthly_orders = base.groupby(months)["order_id"].count()
    lo, hi = monthly_orders.min(), monthly_orders.max()
    span = max(hi - lo, 1)
    monthly_sessions = {}
    for p, o in monthly_orders.items():
        s = 3000 + (o - lo) / span * 2000
        s = max(s, o * 1.05)
        monthly_sessions[p] = min(s, 5200)

    dmin, dmax = base["order_date"].min(), base["order_date"].max()
    all_dates = pd.date_range(dmin, dmax, freq="D")
    idx = all_dates.strftime("%Y-%m-%d")
    daily_orders = base.groupby(dates)["order_id"].count().reindex(idx, fill_value=0)
    idx_months = pd.to_datetime(idx).strftime("%Y-%m")

    daily_sessions = []
    for day_ym, day_ord in zip(idx_months, daily_orders):
        m_total_orders = monthly_orders.get(day_ym, 1)
        m_total_sessions = monthly_sessions.get(day_ym, 3000)
        w = (day_ord / m_total_orders) if m_total_orders else 0
        daily_sessions.append(w * m_total_sessions)
    daily_sessions = np.round(np.array(daily_sessions)).astype(int)

    return pd.DataFrame({"order_date": idx, "orders": daily_orders.to_numpy(),
                         "sessions": daily_sessions})


@st.cache_data
def member_trend():
    """会員数の増減（デモ推計：受注件数から新規・退会を導出）。"""
    base, _ = read_data()
    m = base.groupby(base["order_date"].dt.strftime("%Y-%m"))["order_id"].nunique().sort_index()
    new = (m * 0.32).round().astype(int)
    churn = (m * 0.19).round().astype(int)
    net = new - churn
    total = 12000 + net.cumsum()
    return pd.DataFrame({"month": m.index, "新規会員": new.to_numpy(),
                         "退会": churn.to_numpy(), "純増": net.to_numpy(),
                         "会員数": total.to_numpy()})


traffic_all = compute_daily_traffic()


# ==================== 分析軸（共通フィルタ） ====================
def axis_filters(suffix, show_gran=True):
    """企業／商品／ユーザー情報／流入媒体 に分類した分析軸UI。未選択＝すべて。"""
    mask = FULL.copy()
    with st.container(border=True):
        render_title("分析軸・集計単位")
        st.caption("各項目は未選択の場合「すべて」として扱われます。")

        # ---- 企業 ----
        st.markdown("<div class='axis-group'>企業</div>", unsafe_allow_html=True)
        c = st.columns(2)
        v_trade = c[0].multiselect("取引区分", TRADE_ORDER, key=f"trade_{suffix}")
        v_rep = c[1].multiselect("営業担当", REPS, key=f"rep_{suffix}")
        if v_trade:
            mask &= df["取引区分"].isin(v_trade)
        if v_rep:
            mask &= df["営業担当"].isin(v_rep)

        # ---- 商品 ----
        st.markdown("<div class='axis-group'>商品</div>", unsafe_allow_html=True)
        c = st.columns(4)
        v_chop = c[0].multiselect("ちょっプル", CHOPPLE_ORDER, key=f"chop_{suffix}")
        if v_chop:
            mask &= df["ちょっプル"].isin(v_chop)
        all_l = sorted(df["cat_l"].unique())
        v_l = c[1].multiselect("カテゴリ（大）", all_l, key=f"cat_l_{suffix}")
        lmask = df["cat_l"].isin(v_l) if v_l else FULL
        mid = sorted(df.loc[lmask, "cat_m"].unique())
        v_m = c[2].multiselect("カテゴリ（中）", mid, key=f"cat_m_{suffix}")
        mmask = df["cat_m"].isin(v_m) if v_m else FULL
        sopts = sorted(df.loc[lmask & mmask, "cat_s"].unique())
        v_s = c[3].multiselect("カテゴリ（小）", sopts, key=f"cat_s_{suffix}")
        mask &= lmask & mmask
        if v_s:
            mask &= df["cat_s"].isin(v_s)

        c = st.columns(3)
        v_maker = c[0].multiselect("メーカー", MAKERS, key=f"maker_{suffix}")
        v_brand = c[1].multiselect("ブランド", BRANDS, key=f"brand_{suffix}")
        v_price = c[2].multiselect("価格帯", PRICE_ORDER, key=f"price_{suffix}")
        if v_maker:
            mask &= df["メーカー"].isin(v_maker)
        if v_brand:
            mask &= df["ブランド"].isin(v_brand)
        if v_price:
            mask &= df["価格帯"].isin(v_price)

        # ---- ユーザー情報 ----
        st.markdown("<div class='axis-group'>ユーザー情報</div>", unsafe_allow_html=True)
        c = st.columns(3)
        v_rank = c[0].multiselect("会員ランク", RANK_ORDER, key=f"rank_{suffix}")
        v_age = c[1].multiselect("年代", AGE_ORDER, key=f"age_{suffix}")
        v_gender = c[2].multiselect("性別", GENDER_ORDER, key=f"gender_{suffix}")
        if v_rank:
            mask &= df["member_rank"].isin(v_rank)
        if v_age:
            mask &= df["年代"].isin(v_age)
        if v_gender:
            mask &= df["性別"].isin(v_gender)

        # ---- 流入媒体 ----
        st.markdown("<div class='axis-group'>流入媒体</div>", unsafe_allow_html=True)
        v_ch = st.multiselect("流入媒体", sorted(df["channel"].unique()), key=f"ch_{suffix}")
        if v_ch:
            mask &= df["channel"].isin(v_ch)

        gran = None
        if show_gran:
            st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px dashed #e9ebed;'>",
                        unsafe_allow_html=True)
            cg = st.columns([1, 6])
            cg[0].markdown("<div style='font-weight:700; padding-top:8px; color:#16191f;'>表示・集計単位：</div>",
                           unsafe_allow_html=True)
            gran = cg[1].radio("集計単位", ["年別", "月別", "日別"], horizontal=True,
                               label_visibility="collapsed", key=f"gran_{suffix}")
    return mask, gran


# ==================== 期間の組み立て（切替時エラー防止） ====================
def build_periods(f, gran, suffix):
    """集計単位に応じて期間リストを作る。データ欠損・切替時に落ちないようガード。
    返り値: (fd, view, xlabels, nav_key or None, nav_label) / データなしは None"""
    if f.empty:
        return None
    if gran == "年別":
        fd = f.assign(_p=f["order_date"].dt.year.astype(str) + "年")
        view = sorted(fd["_p"].unique())
        if not view:
            return None
        return fd, view, view, None, f"{view[0]}〜{view[-1]}"

    if gran == "月別":
        fd = f.assign(_p=f["order_date"].dt.strftime("%Y-%m"))
        allp = sorted(fd["_p"].unique())
        if not allp:
            return None
        key = f"m_off_{suffix}"
        maxstart = max(0, len(allp) - 12)
        st.session_state.setdefault(key, maxstart)
        # フィルタや単位の切替で範囲が変わっても必ず有効範囲にクランプ
        st.session_state[key] = min(max(int(st.session_state.get(key, maxstart)), 0), maxstart)
        start = st.session_state[key]
        view = allp[start:start + 12]
        if not view:
            return None
        xlabels = [f"{p[:4]}/{int(p[5:7])}月" for p in view]
        return fd, view, xlabels, key, f"{view[0]}〜{view[-1]}"

    # 日別
    mkeys = sorted(f["order_date"].dt.strftime("%Y-%m").unique())
    if not mkeys:
        return None
    key = f"d_off_{suffix}"
    st.session_state.setdefault(key, len(mkeys) - 1)
    st.session_state[key] = min(max(int(st.session_state.get(key, 0)), 0), len(mkeys) - 1)
    selm = mkeys[st.session_state[key]]
    y_dt, mo_dt = int(selm[:4]), int(selm[5:7])
    ndays = calendar.monthrange(y_dt, mo_dt)[1]
    fd = f.assign(_p=f["order_date"].dt.strftime("%Y-%m-%d"))
    view = [f"{selm}-{d:02d}" for d in range(1, ndays + 1)]
    xlabels = [str(d) for d in range(1, ndays + 1)]
    return fd, view, xlabels, key, f"{y_dt}年{mo_dt}月"


# ==================== タブ構成 ====================
tab_yj, tab_hs, tab_cs = st.tabs(["予実推移", "販促結果", "顧客行動分析"])

# ---------------- 予実推移タブ ----------------
with tab_yj:
    digest_ui_yj = st.empty()
    m_yj, gran_yj = axis_filters("yj")
    f_yj = df[m_yj]

    periods_yj = build_periods(f_yj, gran_yj, "yj")
    if f_yj.empty or periods_yj is None:
        st.warning("条件に合うデータがありません。分析軸の絞り込みを緩めてください。")
    else:
        fd_yj, view_yj, xlabels_yj, show_nav_yj, nav_label_yj = periods_yj
        global_last_yj = fd_yj["_p"].max()

        # --- 今月のダイジェスト（最新月固定） ---
        with digest_ui_yj.container(border=False):
            current_month = f_yj["order_date"].max().to_period("M")
            f_current = f_yj[f_yj["order_date"].dt.to_period("M") == current_month]

            sales_current = f_current["sales_amount"].sum()
            gp_current = f_current["粗利"].sum()
            gpr_current = gp_current / sales_current * 100 if sales_current else 0
            target_current = get_target(current_month.year, current_month.month, target_base)
            pred_current = sales_current * 0.15
            sales_plus_pred = sales_current + pred_current
            gap_current = sales_plus_pred - target_current

            badge = ('<span class="badge-ok" style="margin-left:10px;">✓ 目標達成</span>' if gap_current >= 0
                     else '<span class="badge-ng" style="margin-left:10px;">△ 目標未達</span>')
            render_title("今月のダイジェスト（最新月固定）", badge_html=badge)

            k = st.columns(5)
            k[0].metric("目標売上", man(target_current))
            k[1].metric("売上（実績）", man(sales_current))
            k[2].metric("売上＋予測", man(sales_plus_pred))
            gap_color = GAPPOS if gap_current >= 0 else GAPNEG
            gap_sign = "+" if gap_current >= 0 else "−"
            k[3].markdown(
                f"""<div class="custom-metric">
                <p class="custom-metric-label">計画Gap</p>
                <div style="color:{gap_color}; font-size:1.6rem; font-weight:700; line-height:1.2;">
                {gap_sign}{man(abs(gap_current))}</div></div>""",
                unsafe_allow_html=True)
            k[4].metric("粗利率", f"{gpr_current:.1f}%")
            st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

        # --- 集計 ---
        gsum = fd_yj.groupby("_p")["sales_amount"].sum()
        gord = fd_yj.groupby("_p")["order_id"].nunique()
        ggp = fd_yj.groupby("_p")["粗利"].sum()
        gpromo = fd_yj.groupby("_p")["discount_amount"].sum()

        actual = [float(gsum.get(p, 0.0)) for p in view_yj]
        orders = [int(gord.get(p, 0)) for p in view_yj]
        gpv = [float(ggp.get(p, 0.0)) for p in view_yj]
        promov = [float(gpromo.get(p, 0.0)) for p in view_yj]
        marginalv = [gpv[i] - promov[i] for i in range(len(view_yj))]
        pred = [actual[i] * 0.15 if view_yj[i] == global_last_yj else 0.0
                for i in range(len(view_yj))]

        months_present_yj = sorted(f_yj["order_date"].dt.strftime("%Y-%m").unique())
        tgt = []
        for p in view_yj:
            if gran_yj == "年別":
                y_val = int(p[:4])
                mons = [mm for mm in months_present_yj if mm[:4] == str(y_val)]
                t = sum(get_target(y_val, int(mm[5:7]), target_base) for mm in mons)
            elif gran_yj == "月別":
                t = get_target(int(p[:4]), int(p[5:7]), target_base)
            else:
                y_val, mo_val = int(p[:4]), int(p[5:7])
                t = get_target(y_val, mo_val, target_base) / calendar.monthrange(y_val, mo_val)[1]
            tgt.append(t)

        traffic_p = traffic_all.copy()
        if gran_yj == "年別":
            traffic_p["_p"] = pd.to_datetime(traffic_p["order_date"]).dt.year.astype(str) + "年"
        elif gran_yj == "月別":
            traffic_p["_p"] = pd.to_datetime(traffic_p["order_date"]).dt.strftime("%Y-%m")
        else:
            traffic_p["_p"] = traffic_p["order_date"]
        tsess = traffic_p.groupby("_p")["sessions"].sum()
        tord = traffic_p.groupby("_p")["orders"].sum()
        sess = [int(tsess.get(p, 0)) for p in view_yj]
        site_orders = [int(tord.get(p, 0)) for p in view_yj]
        cvr = [round(site_orders[i] / sess[i] * 100, 2) if sess[i] else 0
               for i in range(len(view_yj))]
        aov = [actual[i] / orders[i] if orders[i] else 0 for i in range(len(view_yj))]

        # --- グラフ描画 ---
        top = st.columns([1.2, 1])
        with top[0]:
            with st.container(border=True):
                render_title(f"売上進捗（{nav_label_yj}）")

                bar_df = pd.DataFrame({
                    "period": xlabels_yj,
                    "実績": [a / 1_000_000 for a in actual],
                    "予測": [p / 1_000_000 for p in pred],
                }).melt("period", var_name="種別", value_name="金額")
                bar_df["順"] = bar_df["種別"].map({"実績": 0, "予測": 1})
                tgt_df = pd.DataFrame({"period": xlabels_yj, "種別": "目標",
                                       "金額": [t / 1_000_000 for t in tgt]})

                prog_color = alt.Color("種別:N", title=None,
                                       scale=alt.Scale(domain=["実績", "予測", "目標"],
                                                       range=[BLUE, LIGHT, TARGETC]))
                bars = alt.Chart(bar_df).mark_bar().encode(
                    x=alt.X("period:N", sort=None, title=None, axis=period_axis()),
                    y=alt.Y("金額:Q", stack="zero", title="金額（百万円）",
                            axis=alt.Axis(format=",.0f")),
                    color=prog_color,
                    order=alt.Order("順:Q"),
                    tooltip=[alt.Tooltip("period:N", title="期間"),
                             alt.Tooltip("種別:N"),
                             alt.Tooltip("金額:Q", format=",.1f", title="金額(百万円)")],
                )
                line = alt.Chart(tgt_df).mark_line(
                    strokeDash=[5, 4], strokeWidth=2,
                    point=alt.OverlayMarkDef(size=95, fill=TARGETC,
                                             stroke="#ffffff", strokeWidth=1.6),
                ).encode(
                    x=alt.X("period:N", sort=None, axis=period_axis()),
                    y=alt.Y("金額:Q"),
                    color=prog_color,
                    tooltip=[alt.Tooltip("period:N", title="期間"),
                             alt.Tooltip("金額:Q", format=",.1f", title="目標(百万円)")],
                )
                # 各棒に目標との差分（±・百万円）を表示
                diff_df = pd.DataFrame({
                    "period": xlabels_yj,
                    "合計": [(actual[i] + pred[i]) / 1_000_000 for i in range(len(view_yj))],
                    "目標v": [t / 1_000_000 for t in tgt],
                })
                diff_df["差分"] = diff_df["合計"] - diff_df["目標v"]
                diff_df["表示位置"] = diff_df[["合計", "目標v"]].max(axis=1)
                diff_df["ラベル"] = diff_df["差分"].map(
                    lambda v: f"+{v:,.1f}" if v >= 0 else f"−{abs(v):,.1f}")
                diff_df["色区分"] = np.where(diff_df["差分"] >= 0, "達成", "未達")
                diff_tx = alt.Chart(diff_df).mark_text(
                    dy=-10, fontWeight="bold", fontSize=10,
                ).encode(
                    x=alt.X("period:N", sort=None, axis=period_axis()),
                    y=alt.Y("表示位置:Q"),
                    text="ラベル:N",
                    color=alt.Color("色区分:N", legend=None,
                                    scale=alt.Scale(domain=["達成", "未達"],
                                                    range=[GAPPOS, GAPNEG])),
                    tooltip=[alt.Tooltip("period:N", title="期間"),
                             alt.Tooltip("差分:Q", format="+,.1f", title="目標差分(百万円)")],
                )
                prog = qs_style(alt.layer(bars, line, diff_tx)
                                .resolve_scale(color="independent").properties(height=300))
                chart_with_nav(prog, show_nav_yj, "yj_prog", spacer_px=110)

        with top[1]:
            with st.container(border=True):
                render_title(f"売上構成要素（{nav_label_yj}）")

                comp_df = pd.DataFrame({"period": xlabels_yj, "セッション数": sess,
                                        "客単価": aov, "CVR": cvr})
                color_scale = alt.Scale(domain=["セッション数", "客単価", "CVR(%)"],
                                        range=[BLUE, GREEN, AMBER])
                left = alt.Chart(comp_df).transform_fold(
                    ["セッション数", "客単価"], as_=["指標", "値"]
                ).mark_line(point=True, strokeWidth=2).encode(
                    x=alt.X("period:N", sort=None, title=None, axis=period_axis()),
                    y=alt.Y("値:Q", title="セッション数（回）／客単価（円）", axis=alt.Axis(format=",.0f")),
                    color=alt.Color("指標:N", scale=color_scale, title=None),
                    tooltip=[alt.Tooltip("period:N", title="期間"),
                             alt.Tooltip("指標:N"),
                             alt.Tooltip("値:Q", format=",.0f")],
                )
                right = alt.Chart(comp_df).transform_calculate(
                    指標='"CVR(%)"'
                ).mark_line(point=True, strokeDash=[2, 2], strokeWidth=2).encode(
                    x=alt.X("period:N", sort=None, axis=period_axis()),
                    y=alt.Y("CVR:Q", title="CVR(%)",
                            scale=alt.Scale(domain=[0, 100]),
                            axis=alt.Axis(values=list(range(0, 101, 5)), format=",.0f")),
                    color=alt.Color("指標:N", scale=color_scale, title=None),
                    tooltip=[alt.Tooltip("period:N", title="期間"),
                             alt.Tooltip("CVR:Q", format=".2f", title="CVR(%)")],
                )
                comp = qs_style(alt.layer(left, right)
                                .resolve_scale(y="independent").properties(height=300))
                chart_with_nav(comp, show_nav_yj, "yj_comp", spacer_px=110)

        with st.container(border=True):
            render_title(f"利益内訳の推移（{gran_yj}・{nav_label_yj}）")

            profit_df = pd.DataFrame({
                "period": xlabels_yj,
                "限界利益": [v / 10000 for v in marginalv],
                "変動費": [v / 10000 for v in promov],
            }).melt("period", var_name="種別", value_name="金額")
            profit_df["順"] = profit_df["種別"].map({"限界利益": 0, "変動費": 1})

            profit = alt.Chart(profit_df).mark_bar().encode(
                x=alt.X("period:N", sort=None, title=None, axis=period_axis()),
                y=alt.Y("金額:Q", stack="zero", title="金額（万円）", axis=alt.Axis(format=",.0f")),
                color=alt.Color("種別:N", title=None,
                                scale=alt.Scale(domain=["限界利益", "変動費"], range=[BLUE, AMBER])),
                order=alt.Order("順:Q"),
                tooltip=[alt.Tooltip("period:N", title="期間"),
                         alt.Tooltip("種別:N"),
                         alt.Tooltip("金額:Q", format=",.0f", title="金額(万円)")],
            )
            # 積み上げ合計＝粗利 を棒の上に表示（凡例にも「粗利」を追加）
            gp_df = pd.DataFrame({"period": xlabels_yj,
                                  "粗利": [v / 10000 for v in gpv],
                                  "凡例": "粗利（積み上げ合計）"})
            gp_tx = alt.Chart(gp_df).mark_text(
                dy=-8, fontWeight="bold", fontSize=10,
            ).encode(
                x=alt.X("period:N", sort=None, axis=period_axis()),
                y=alt.Y("粗利:Q"),
                text=alt.Text("粗利:Q", format=",.0f"),
                color=alt.Color("凡例:N", title=None,
                                scale=alt.Scale(domain=["粗利（積み上げ合計）"],
                                                range=["#16191f"])),
                tooltip=[alt.Tooltip("period:N", title="期間"),
                         alt.Tooltip("粗利:Q", format=",.0f", title="粗利(万円)")],
            )
            profit_chart = qs_style(alt.layer(profit, gp_tx)
                                    .resolve_scale(color="independent").properties(height=320))
            chart_with_nav(profit_chart, show_nav_yj, "yj_profit", spacer_px=120)


# ---------------- 販促結果タブ ----------------
with tab_hs:
    digest_ui_hs = st.empty()
    m_hs, gran_hs = axis_filters("hs")
    f_hs = df[m_hs]

    periods_hs = build_periods(f_hs, gran_hs, "hs")
    if f_hs.empty or periods_hs is None:
        st.warning("条件に合うデータがありません。分析軸の絞り込みを緩めてください。")
    else:
        fd_hs, view_hs, xlabels_hs, show_nav_hs, nav_label_hs = periods_hs
        f_view = fd_hs[fd_hs["_p"].isin(view_hs)]

        if f_view.empty:
            st.info("選択された期間（" + nav_label_hs + "）にデータがありません。期間を移動してください。")
        else:
            # --- 今月のダイジェスト（最新月固定） ---
            with digest_ui_hs.container(border=False):
                render_title("今月のダイジェスト（最新月固定）")
                cur_m = f_hs["order_date"].max().to_period("M")
                f_cur = f_hs[f_hs["order_date"].dt.to_period("M") == cur_m]

                budget_total = sum(BUDGET_M.values())               # 販促費予算合計（月次）
                fp = f_cur[f_cur["promo_type"] == "ポイント"]["discount_amount"].sum()
                fc = f_cur[f_cur["promo_type"] == "クーポン"]["discount_amount"].sum()
                grant_total = f_cur["discount_amount"].sum()        # 販促費付与額合計
                total_sales = f_cur["sales_amount"].sum()
                promo_sales = f_cur[f_cur["promo_type"] != "なし"]["sales_amount"].sum()

                k = st.columns([1, 2.2, 1])
                k[0].metric("販促費予算 合計", man(budget_total))
                grant_ratio = grant_total / budget_total * 100 if budget_total else 0
                k[1].markdown(
                    f"""<div class="custom-metric">
                    <p class="custom-metric-label">販促費付与額 合計（予算比 {grant_ratio:.1f}%）</p>
                    <div style="display:flex; align-items:baseline; gap:22px; flex-wrap:wrap;">
                      <div style="font-size:1.6rem; font-weight:700; color:#16191f;">{man(grant_total)}</div>
                      <div style="font-size:0.95rem; color:#5f6b7a; border-left:1px solid #e9ebed; padding-left:18px;">
                        内訳：ポイント付与額 <b style="color:#16191f;">{man(fp)}</b>
                        ／ クーポン付与額 <b style="color:#16191f;">{man(fc)}</b>
                      </div>
                    </div></div>""",
                    unsafe_allow_html=True)
                k[2].metric("施策経由 売上比率",
                            f"{promo_sales/total_sales*100 if total_sales else 0:.1f}%")
                st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

            order_cnt = f_view["order_id"].nunique()
            AOV_view = f_view["sales_amount"].sum() / order_cnt if order_cnt else 0
            months_in_view = max(f_view["order_date"].dt.to_period("M").nunique(), 1)

            st.markdown(
                "<div style='color:#8a94a3; font-size:12px; margin:2px 0 10px;'>"
                "売上・粗利・付与額は実データ。予算／セッション／CVR／配信・広告コスト／ROAS／"
                "退会数／カゴ落ち／会員数は元データがないためデモ用の推計値です。</div>",
                unsafe_allow_html=True)

            # -------- 大分類1：サイト内インセンティブ --------
            with st.container(border=True):
                render_title("サイト内インセンティブ")

                inc_rows = []
                for name in ["ポイント", "クーポン"]:
                    sub = f_view[f_view["promo_type"] == name]
                    used = sub["discount_amount"].sum()
                    budget = BUDGET_M[name] * months_in_view
                    inc_rows.append({"施策": name,
                                     "予算額": budget / 10000,
                                     "利用額": used / 10000,
                                     "予算残": max(budget - used, 0) / 10000})
                inc_df = pd.DataFrame(inc_rows)

                ic = st.columns(2)

                # グラフ1：利用額＋予算残の積み上げ（合計＝予算額）。残額をラベル表示
                with ic[0]:
                    sub_head("予算額・利用額（予算までの残り）")
                    amt_long = inc_df.melt(id_vars=["施策"], value_vars=["利用額", "予算残"],
                                           var_name="種別", value_name="金額")
                    amt_long["順"] = amt_long["種別"].map({"利用額": 0, "予算残": 1})
                    bars1 = alt.Chart(amt_long).mark_bar().encode(
                        x=alt.X("施策:N", title=None, axis=alt.Axis(labelAngle=0)),
                        y=alt.Y("金額:Q", stack="zero", title="金額（万円）",
                                axis=alt.Axis(format=",.0f")),
                        color=alt.Color("種別:N", title=None,
                                        scale=alt.Scale(domain=["利用額", "予算残"],
                                                        range=[BLUE, "#dfe3e8"])),
                        order=alt.Order("順:Q"),
                        tooltip=[alt.Tooltip("施策:N"), alt.Tooltip("種別:N"),
                                 alt.Tooltip("金額:Q", format=",.1f", title="金額(万円)")],
                    )
                    rest_tx = alt.Chart(inc_df).mark_text(
                        dy=-10, fontWeight="bold", color="#16191f",
                    ).encode(
                        x=alt.X("施策:N"),
                        y=alt.Y("予算額:Q"),
                        text=alt.Text("予算残:Q", format=",.1f"),
                        tooltip=[alt.Tooltip("施策:N"),
                                 alt.Tooltip("予算残:Q", format=",.1f", title="予算残(万円)")],
                    )
                    rest_lb = alt.Chart(inc_df).mark_text(
                        dy=-26, fontSize=10.5, color="#5f6b7a",
                    ).encode(x=alt.X("施策:N"), y=alt.Y("予算額:Q"),
                             text=alt.value("残り（万円）"))
                    g1 = qs_style(alt.layer(bars1, rest_tx, rest_lb).properties(height=300))
                    st.altair_chart(g1, use_container_width=True)

                # グラフ2：全体に対する施策経由の売上・粗利（積み上げ）
                with ic[1]:
                    sub_head("キャンペーン経由 売上・粗利（全体に対する構成）")
                    seg_rows = []
                    seg_map = {"なし": "通常（施策なし）", "ポイント": "ポイント経由", "クーポン": "クーポン経由"}
                    tot = {"売上": f_view["sales_amount"].sum(), "粗利": f_view["粗利"].sum()}
                    for raw, seg in seg_map.items():
                        sub = f_view[f_view["promo_type"] == raw]
                        for metric, col in [("売上", "sales_amount"), ("粗利", "粗利")]:
                            v = sub[col].sum()
                            seg_rows.append({
                                "指標": metric, "区分": seg, "金額": v / 10000,
                                "構成比": v / tot[metric] * 100 if tot[metric] else 0,
                            })
                    seg_df = pd.DataFrame(seg_rows)
                    seg_order = ["ポイント経由", "クーポン経由", "通常（施策なし）"]
                    seg_df["順"] = seg_df["区分"].map({s: i for i, s in enumerate(seg_order)})

                    g2 = alt.Chart(seg_df).mark_bar().encode(
                        x=alt.X("指標:N", sort=["売上", "粗利"], title=None,
                                axis=alt.Axis(labelAngle=0)),
                        y=alt.Y("金額:Q", stack="zero", title="金額（万円）",
                                axis=alt.Axis(format=",.0f")),
                        color=alt.Color("区分:N", title=None,
                                        scale=alt.Scale(domain=seg_order,
                                                        range=[BLUE, AMBER, GRAY])),
                        order=alt.Order("順:Q"),
                        tooltip=[alt.Tooltip("指標:N"), alt.Tooltip("区分:N"),
                                 alt.Tooltip("金額:Q", format=",.0f", title="金額(万円)"),
                                 alt.Tooltip("構成比:Q", format=".1f", title="構成比(%)")],
                    ).properties(height=300)
                    st.altair_chart(qs_style(g2), use_container_width=True)

            # -------- 大分類2：施策別の内訳（ポイント・クーポン種類別） --------
            with st.container(border=True):
                render_title("施策別の内訳（ポイント・クーポン種類別）")

                camp = (f_view[f_view["promo_type"] != "なし"]
                        .groupby(["promo_type", "施策種類"])
                        .agg(売上=("sales_amount", "sum"), 粗利=("粗利", "sum"),
                             付与額=("discount_amount", "sum"))
                        .reset_index())
                if camp.empty:
                    st.info("対象期間に施策経由の売上がありません。")
                else:
                    camp["ラベル"] = camp["promo_type"] + "/" + camp["施策種類"]
                    camp = camp.sort_values(["promo_type", "売上"],
                                            ascending=[True, False])
                    lab_order = list(camp["ラベル"])
                    camp["ROI"] = np.where(camp["付与額"] > 0,
                                           camp["売上"] / camp["付与額"] * 100, 0)

                    cp = st.columns(2)
                    with cp[0]:
                        sub_head("種類別 売上・粗利")
                        cl = camp.melt(id_vars=["ラベル"], value_vars=["売上", "粗利"],
                                       var_name="指標", value_name="金額")
                        cl["金額"] = cl["金額"] / 10000
                        cchart = alt.Chart(cl).mark_bar().encode(
                            x=alt.X("ラベル:N", sort=lab_order, title=None,
                                    axis=period_axis()),
                            xOffset=alt.XOffset("指標:N", sort=["売上", "粗利"]),
                            y=alt.Y("金額:Q", title="金額（万円）",
                                    axis=alt.Axis(format=",.0f")),
                            color=alt.Color("指標:N", title=None,
                                            scale=alt.Scale(domain=["売上", "粗利"],
                                                            range=[BLUE, GREEN])),
                            tooltip=[alt.Tooltip("ラベル:N", title="施策"),
                                     alt.Tooltip("指標:N"),
                                     alt.Tooltip("金額:Q", format=",.0f", title="金額(万円)")],
                        ).properties(height=300)
                        st.altair_chart(qs_style(cchart), use_container_width=True)

                    with cp[1]:
                        sub_head("種類別 付与額・ROI（売上÷付与額）")
                        camp2 = camp.assign(付与額万=camp["付与額"] / 10000)
                        gb = alt.Chart(camp2).mark_bar(color=AMBER).encode(
                            x=alt.X("ラベル:N", sort=lab_order, title=None,
                                    axis=period_axis()),
                            y=alt.Y("付与額万:Q", title="付与額（万円）",
                                    axis=alt.Axis(format=",.1f")),
                            tooltip=[alt.Tooltip("ラベル:N", title="施策"),
                                     alt.Tooltip("付与額万:Q", format=",.1f", title="付与額(万円)")],
                        )
                        gpt = alt.Chart(camp2).mark_point(
                            size=110, filled=True, color=PURPLE,
                            stroke="#ffffff", strokeWidth=1.3,
                        ).encode(
                            x=alt.X("ラベル:N", sort=lab_order),
                            y=alt.Y("ROI:Q", title="ROI（%）", axis=alt.Axis(format=",.0f")),
                            tooltip=[alt.Tooltip("ラベル:N", title="施策"),
                                     alt.Tooltip("ROI:Q", format=",.0f", title="ROI(%)")],
                        )
                        g4 = qs_style(alt.layer(gb, gpt)
                                      .resolve_scale(y="independent").properties(height=300))
                        st.altair_chart(g4, use_container_width=True)

            # -------- 大分類2：流入元（指標別に流入元を比較） --------
            with st.container(border=True):
                render_title("流入元")

                # 中分類ごとの想定CVR（セッションを実受注数から逆算するための推計値）
                CH_CVR = {"メルマガ": 0.040, "Google": 0.025, "LINE": 0.045, "Push通知": 0.030}
                CH_DISP = {"メルマガ": "メルマガ", "Google": "Google広告",
                           "LINE": "LINE", "Push通知": "Push通知"}
                SRC_ORDER = ["特集", "バナー", "メルマガ", "Google広告", "LINE", "Push通知"]

                src_rows = []
                feat = f_view[f_view["feature_tag"] != "なし"]
                f_ord = feat["order_id"].nunique()
                f_sess = round(f_ord / 0.035) if f_ord else 0
                src_rows.append({"流入元": "特集",
                                 "売上": feat["sales_amount"].sum() / 10000,
                                 "粗利": feat["粗利"].sum() / 10000,
                                 "セッション": f_sess,
                                 "CVR": round(f_ord / f_sess * 100, 2) if f_sess else 0,
                                 "ROAS": None})
                b_sess = round(f_sess * 0.6)
                b_ord = round(b_sess * 0.02)
                src_rows.append({"流入元": "バナー",
                                 "売上": b_ord * AOV_view / 10000,
                                 "粗利": b_ord * AOV_view * 0.36 / 10000,
                                 "セッション": b_sess,
                                 "CVR": 2.0, "ROAS": None})
                for ch, cvr0 in CH_CVR.items():
                    sub = f_view[f_view["channel"] == ch]
                    o = sub["order_id"].nunique()
                    s = sub["sales_amount"].sum()
                    g = sub["粗利"].sum()
                    sess0 = round(o / cvr0) if o else 0
                    if ch == "Google":
                        cost = round(sess0 * 45)
                    else:
                        crate = {"メルマガ": 0.12, "LINE": 0.18, "Push通知": 0.20}[ch]
                        unit = {"メルマガ": 2.5, "LINE": 3.3, "Push通知": 2.5}[ch]
                        cost = round(round(sess0 / crate) * unit) if sess0 else 0
                    src_rows.append({"流入元": CH_DISP[ch],
                                     "売上": s / 10000, "粗利": g / 10000,
                                     "セッション": sess0,
                                     "CVR": round(o / sess0 * 100, 2) if sess0 else 0,
                                     "ROAS": round(s / cost * 100) if cost else None})
                src_df = pd.DataFrame(src_rows)

                sc = st.columns(3)
                # 売上・粗利（グループ棒）
                with sc[0]:
                    sub_head("売上・粗利")
                    sg = src_df.melt(id_vars=["流入元"], value_vars=["売上", "粗利"],
                                     var_name="指標", value_name="金額")
                    ch1 = alt.Chart(sg).mark_bar().encode(
                        x=alt.X("流入元:N", sort=SRC_ORDER, title=None,
                                axis=alt.Axis(labelAngle=0,
                                              labelExpr="length(datum.label)>5 ? "
                                                        "[slice(datum.label,0,4), slice(datum.label,4)] "
                                                        ": datum.label")),
                        xOffset=alt.XOffset("指標:N", sort=["売上", "粗利"]),
                        y=alt.Y("金額:Q", title="金額（万円）", axis=alt.Axis(format=",.0f")),
                        color=alt.Color("指標:N", title=None,
                                        scale=alt.Scale(domain=["売上", "粗利"],
                                                        range=[BLUE, GREEN])),
                        tooltip=[alt.Tooltip("流入元:N"), alt.Tooltip("指標:N"),
                                 alt.Tooltip("金額:Q", format=",.0f", title="金額(万円)")],
                    ).properties(height=280)
                    st.altair_chart(qs_style(ch1), use_container_width=True)

                # セッション流入数 ＋ CVR（2軸）
                with sc[1]:
                    sub_head("セッション流入数・CVR")
                    xenc = alt.X("流入元:N", sort=SRC_ORDER, title=None,
                                 axis=alt.Axis(labelAngle=0,
                                               labelExpr="length(datum.label)>5 ? "
                                                         "[slice(datum.label,0,4), slice(datum.label,4)] "
                                                         ": datum.label"))
                    sess_bar = alt.Chart(src_df).mark_bar(color=LIGHT).encode(
                        x=xenc,
                        y=alt.Y("セッション:Q", title="セッション流入数（回）",
                                axis=alt.Axis(format=",.0f")),
                        tooltip=[alt.Tooltip("流入元:N"),
                                 alt.Tooltip("セッション:Q", format=",.0f",
                                             title="セッション(回)")],
                    )
                    cvr_pt = alt.Chart(src_df).mark_line(
                        strokeWidth=0,
                        point=alt.OverlayMarkDef(size=110, fill=AMBER,
                                                 stroke="#ffffff", strokeWidth=1.3),
                    ).encode(
                        x=xenc,
                        y=alt.Y("CVR:Q", title="CVR(%)", axis=alt.Axis(format=",.1f")),
                        tooltip=[alt.Tooltip("流入元:N"),
                                 alt.Tooltip("CVR:Q", format=".2f", title="CVR(%)")],
                    )
                    cvr_tx = alt.Chart(src_df).mark_text(
                        dy=-12, color="#b25a1f", fontWeight="bold", fontSize=10,
                    ).encode(x=xenc, y=alt.Y("CVR:Q"),
                             text=alt.Text("CVR:Q", format=".1f"))
                    ch2 = qs_style(alt.layer(sess_bar, cvr_pt, cvr_tx)
                                   .resolve_scale(y="independent").properties(height=280))
                    st.altair_chart(ch2, use_container_width=True)

                # ROAS（コストデータのある流入元のみ）
                with sc[2]:
                    sub_head("ROAS")
                    roas_df = src_df[src_df["ROAS"].notna()]
                    base3 = alt.Chart(roas_df).encode(
                        x=alt.X("流入元:N", sort=SRC_ORDER, title=None,
                                axis=alt.Axis(labelAngle=0,
                                              labelExpr="length(datum.label)>5 ? "
                                                        "[slice(datum.label,0,4), slice(datum.label,4)] "
                                                        ": datum.label")),
                        y=alt.Y("ROAS:Q", title="ROAS（%）", axis=alt.Axis(format=",.0f")),
                    )
                    ch3 = alt.layer(
                        base3.mark_bar(color=PURPLE).encode(
                            tooltip=[alt.Tooltip("流入元:N"),
                                     alt.Tooltip("ROAS:Q", format=",.0f", title="ROAS(%)")]),
                        base3.mark_text(dy=-8, color="#16191f", fontWeight="bold")
                        .encode(text=alt.Text("ROAS:Q", format=",.0f")),
                    ).properties(height=280)
                    st.altair_chart(qs_style(ch3), use_container_width=True)
                    st.caption("※ 特集・バナーはコストデータがないため対象外")


# ---------------- 顧客行動分析タブ ----------------
with tab_cs:
    m_cs, _ = axis_filters("cs", show_gran=False)
    f_cs = df[m_cs]

    if f_cs.empty:
        st.warning("条件に合うデータがありません。分析軸の絞り込みを緩めてください。")
    else:
        st.markdown(
            "<div style='color:#8a94a3; font-size:12px; margin:2px 0 10px;'>"
            "※ 顧客IDは元データに存在しないため、注文IDから決定論的に生成したデモ値です。"
            "リピート率・F2転換・LTV・購入間隔・休眠判定・会員数はその推計に基づきます。</div>",
            unsafe_allow_html=True)

        # ---- 顧客行動（カゴ落ち） ----
        cs_order_cnt = f_cs["order_id"].nunique()
        cs_AOV = f_cs["sales_amount"].sum() / cs_order_cnt if cs_order_cnt else 0

        with st.container(border=True):
            render_title("顧客行動")
            sub_head("カゴ落ち")

            ABANDON_RATE = 0.68
            cart_add = round(cs_order_cnt / (1 - ABANDON_RATE)) if cs_order_cnt else 0
            abandoned = cart_add - cs_order_cnt
            loss = round(abandoned * cs_AOV)

            cc = st.columns(3)
            cc[0].metric("カゴ落ち数", f"{abandoned:,} 件")
            cc[1].metric("損失金額", man(loss))
            cc[2].metric("カゴ落ち率", f"{abandoned/cart_add*100 if cart_add else 0:.1f}%")

            steps = ["カート追加", "情報入力", "配送設定", "支払い方法", "注文確認", "購入完了"]
            reach_rate = [1.00, 0.74, 0.63, 0.52, 0.43, 1 - ABANDON_RATE]
            reach = [round(cart_add * r) for r in reach_rate]
            drop = [0.0] + [round((reach[i - 1] - reach[i]) / reach[i - 1] * 100, 1)
                            if reach[i - 1] else 0 for i in range(1, len(reach))]
            funnel_df = pd.DataFrame({"ステップ": steps, "到達数": reach, "離脱率": drop})
            max_drop = funnel_df["離脱率"].max()
            funnel_df["区分"] = np.where(
                (funnel_df["離脱率"] == max_drop) & (funnel_df["離脱率"] > 0),
                "最大離脱ステップ", "通常")

            fbar = alt.Chart(funnel_df).mark_bar().encode(
                x=alt.X("ステップ:N", sort=steps, title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("到達数:Q", title="到達数（件）", axis=alt.Axis(format=",.0f")),
                color=alt.Color("区分:N", title=None,
                                scale=alt.Scale(domain=["通常", "最大離脱ステップ"],
                                                range=[AMBER, GAPNEG])),
                tooltip=[alt.Tooltip("ステップ:N"),
                         alt.Tooltip("到達数:Q", format=",.0f", title="到達数"),
                         alt.Tooltip("離脱率:Q", format=".1f", title="離脱率(%)")],
            )
            ftext = alt.Chart(funnel_df[funnel_df["離脱率"] > 0]).mark_text(
                dy=-8, color=GAPNEG, fontWeight="bold"
            ).encode(x=alt.X("ステップ:N", sort=steps), y="到達数:Q",
                     text=alt.Text("離脱率:Q", format=".1f"))
            st.altair_chart(qs_style(alt.layer(fbar, ftext).properties(height=280)),
                            use_container_width=True)


        # ---- 顧客単位の集計 ----
        ref_date = df["order_date"].max()
        s_cs = f_cs.sort_values("order_date")
        cust = s_cs.groupby("顧客ID").agg(
            購入回数=("order_id", "nunique"),
            累計購入額=("sales_amount", "sum"),
            初回=("order_date", "min"),
            最終=("order_date", "max"),
        )
        n_cust = len(cust)
        repeat_cust = int((cust["購入回数"] >= 2).sum())
        repeat_rate = repeat_cust / n_cust * 100 if n_cust else 0
        ltv_avg = cust["累計購入額"].mean() if n_cust else 0

        # 2回目購入日（各顧客の2番目の注文日）
        rk = s_cs.assign(_rk=s_cs.groupby("顧客ID").cumcount())
        second = rk[rk["_rk"] == 1].set_index("顧客ID")["order_date"]
        first = cust["初回"]

        # F2転換率：初回購入から90日以上経過した顧客のうち、90日以内に2回目購入した割合
        eligible = first[first <= ref_date - pd.Timedelta(days=90)]
        conv_days = (second.reindex(eligible.index) - eligible).dt.days
        f2_rate = (conv_days <= 90).mean() * 100 if len(eligible) else 0

        # 平均購入間隔（リピート顧客のみ）
        rep = cust[cust["購入回数"] >= 2]
        interval_avg = ((rep["最終"] - rep["初回"]).dt.days
                        / (rep["購入回数"] - 1)).mean() if len(rep) else 0

        # 休眠・離反（最終購入からの経過日数）
        recency = (ref_date - cust["最終"]).dt.days
        seg_labels = ["アクティブ（90日以内）", "休眠予備軍（91〜180日）",
                      "休眠（181〜365日）", "離反（366日以上）"]
        seg = pd.cut(recency, bins=[-1, 90, 180, 365, np.inf], labels=seg_labels)
        seg_counts = seg.value_counts().reindex(seg_labels).fillna(0).astype(int)
        dormant_rate = (seg_counts.iloc[1:].sum() / n_cust * 100) if n_cust else 0

        # ---- ダイジェスト ----
        render_title("顧客ダイジェスト")
        k = st.columns(5)
        k[0].metric("顧客数", f"{n_cust:,} 人")
        k[1].metric("リピート率（2回以上購入）", f"{repeat_rate:.1f}%")
        k[2].metric("F2転換率（90日以内に2回目購入）", f"{f2_rate:.1f}%")
        k[3].metric("平均LTV（1人あたり累計購入額）", man(ltv_avg))
        k[4].metric("平均購入間隔", f"{interval_avg:,.0f} 日")
        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

        # ---- リピート構造 ----
        r1 = st.columns(2)
        with r1[0]:
            with st.container(border=True):
                render_title("購入回数の分布")
                freq_labels = ["1回", "2回", "3〜4回", "5〜9回", "10回以上"]
                freq = pd.cut(cust["購入回数"], bins=[0, 1, 2, 4, 9, np.inf],
                              labels=freq_labels).value_counts().reindex(freq_labels).fillna(0)
                freq_df = pd.DataFrame({"購入回数": freq_labels,
                                        "顧客数": freq.astype(int).to_numpy()})
                freq_df["構成比"] = freq_df["顧客数"] / n_cust * 100 if n_cust else 0
                fb = alt.Chart(freq_df).encode(
                    x=alt.X("購入回数:N", sort=freq_labels, title=None,
                            axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("顧客数:Q", title="顧客数（人）", axis=alt.Axis(format=",.0f")),
                )
                chart = alt.layer(
                    fb.mark_bar(color=BLUE).encode(
                        tooltip=[alt.Tooltip("購入回数:N"),
                                 alt.Tooltip("顧客数:Q", format=",.0f"),
                                 alt.Tooltip("構成比:Q", format=".1f", title="構成比(%)")]),
                    fb.mark_text(dy=-8, color="#16191f", fontWeight="bold")
                    .encode(text=alt.Text("顧客数:Q", format=",.0f")),
                ).properties(height=280)
                st.altair_chart(qs_style(chart), use_container_width=True)

        with r1[1]:
            with st.container(border=True):
                render_title("F2転換までの日数（初回→2回目）")
                f2_days = (second - first.reindex(second.index)).dt.days.dropna()
                if f2_days.empty:
                    st.info("2回以上購入した顧客がいません。")
                else:
                    d_labels = ["〜30日", "31〜60日", "61〜90日", "91〜180日", "181日〜"]
                    dist = pd.cut(f2_days, bins=[-1, 30, 60, 90, 180, np.inf],
                                  labels=d_labels).value_counts().reindex(d_labels).fillna(0)
                    f2_df = pd.DataFrame({"日数": d_labels,
                                          "顧客数": dist.astype(int).to_numpy()})
                    fb2 = alt.Chart(f2_df).encode(
                        x=alt.X("日数:N", sort=d_labels, title=None,
                                axis=alt.Axis(labelAngle=0)),
                        y=alt.Y("顧客数:Q", title="顧客数（人）", axis=alt.Axis(format=",.0f")),
                    )
                    chart = alt.layer(
                        fb2.mark_bar(color=GREEN).encode(
                            tooltip=[alt.Tooltip("日数:N"),
                                     alt.Tooltip("顧客数:Q", format=",.0f")]),
                        fb2.mark_text(dy=-8, color="#16191f", fontWeight="bold")
                        .encode(text=alt.Text("顧客数:Q", format=",.0f")),
                    ).properties(height=280)
                    st.altair_chart(qs_style(chart), use_container_width=True)
                    st.caption(f"中央値：{f2_days.median():,.0f}日で2回目購入")

        # ---- LTV と 休眠/離反 ----
        r2 = st.columns(2)
        with r2[0]:
            with st.container(border=True):
                render_title("年代別 顧客1人あたりの累計購入額（LTV）")
                cust_age = s_cs.groupby("顧客ID")["年代"].first()
                ltv_age = (cust["累計購入額"].to_frame().join(cust_age)
                           .groupby("年代")["累計購入額"].mean()
                           .reindex(AGE_ORDER).dropna() / 10000)
                ltv_df = pd.DataFrame({"年代": ltv_age.index, "平均LTV": ltv_age.to_numpy()})
                lb = alt.Chart(ltv_df).encode(
                    x=alt.X("年代:N", sort=AGE_ORDER, title=None, axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("平均LTV:Q", title="1人あたり累計購入額（万円）", axis=alt.Axis(format=",.1f")),
                )
                chart = alt.layer(
                    lb.mark_bar(color=PURPLE).encode(
                        tooltip=[alt.Tooltip("年代:N"),
                                 alt.Tooltip("平均LTV:Q", format=",.1f", title="累計購入額(万円)")]),
                    lb.mark_text(dy=-8, color="#16191f", fontWeight="bold")
                    .encode(text=alt.Text("平均LTV:Q", format=",.1f")),
                ).properties(height=280)
                st.altair_chart(qs_style(chart), use_container_width=True)

        with r2[1]:
            with st.container(border=True):
                render_title("休眠・離反ステータス（最終購入からの経過）")
                seg_df = pd.DataFrame({"ステータス": seg_labels,
                                       "顧客数": seg_counts.to_numpy()})
                seg_df["構成比"] = seg_df["顧客数"] / n_cust * 100 if n_cust else 0
                sb = alt.Chart(seg_df).encode(
                    x=alt.X("ステータス:N", sort=seg_labels, title=None,
                            axis=alt.Axis(labelAngle=0,
                                          labelExpr="split(datum.label, '（')[0]")),
                    y=alt.Y("顧客数:Q", title="顧客数（人）", axis=alt.Axis(format=",.0f")),
                )
                chart = alt.layer(
                    sb.mark_bar().encode(
                        color=alt.Color("ステータス:N", title=None,
                                        scale=alt.Scale(domain=seg_labels,
                                                        range=[GREEN, AMBER, "#e08b3c", GAPNEG]),
                                        legend=alt.Legend(orient="top", columns=2)),
                        tooltip=[alt.Tooltip("ステータス:N"),
                                 alt.Tooltip("顧客数:Q", format=",.0f"),
                                 alt.Tooltip("構成比:Q", format=".1f", title="構成比(%)")]),
                    sb.mark_text(dy=-8, color="#16191f", fontWeight="bold")
                    .encode(text=alt.Text("顧客数:Q", format=",.0f")),
                ).properties(height=280)
                st.altair_chart(qs_style(chart), use_container_width=True)
                st.caption(f"休眠以上（91日以上購入なし）の割合：{dormant_rate:.1f}%")

        # ---- 会員数の増減 ----
        with st.container(border=True):
            render_title("会員数の増減")

            mem = member_trend()
            mem["label"] = mem["month"].map(lambda p: f"{p[:4]}/{int(p[5:7])}月")
            flow = mem.melt(id_vars=["label"], value_vars=["新規会員", "退会"],
                            var_name="区分", value_name="人数")
            flow["人数"] = np.where(flow["区分"] == "退会", -flow["人数"], flow["人数"])

            mbar = alt.Chart(flow).mark_bar().encode(
                x=alt.X("label:N", sort=list(mem["label"]), title=None, axis=period_axis()),
                y=alt.Y("人数:Q", title="増減（人）", axis=alt.Axis(format=",.0f")),
                color=alt.Color("区分:N", title=None,
                                scale=alt.Scale(domain=["新規会員", "退会"],
                                                range=[GREEN, GAPNEG])),
                tooltip=[alt.Tooltip("label:N", title="月"),
                         alt.Tooltip("区分:N"),
                         alt.Tooltip("人数:Q", format=",.0f")],
            )
            mem["凡例"] = "会員数（累計・折れ線）"
            mline = alt.Chart(mem).mark_line(
                strokeWidth=2.5, point=True,
            ).encode(
                x=alt.X("label:N", sort=list(mem["label"]), axis=period_axis()),
                y=alt.Y("会員数:Q", title="会員数（累計・人）", axis=alt.Axis(format=",.0f")),
                color=alt.Color("凡例:N", title=None,
                                scale=alt.Scale(domain=["会員数（累計・折れ線）"],
                                                range=[BLUE])),
                tooltip=[alt.Tooltip("label:N", title="月"),
                         alt.Tooltip("会員数:Q", format=",.0f", title="会員数"),
                         alt.Tooltip("純増:Q", format=",.0f", title="純増")],
            )
            mchart = qs_style(alt.layer(mbar, mline)
                              .resolve_scale(y="independent", color="independent")
                              .properties(height=300))
            st.altair_chart(mchart, use_container_width=True)