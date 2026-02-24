import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# PAGE CONFIG
st.set_page_config(
    page_title="StockLens",
    page_icon="📊",
    layout="wide"
)

# CUSTOM CSS
st.markdown("""
<style>
    .stApp { background-color: #f0f4f8; color: #1a2332; }

/* Fix all text colors */
h1, h2, h3, h4, h5, h6, p, span, label, div {
    color: #1a2332;
}

/* Fix metric labels */
[data-testid="stMetricLabel"] {
    color: #64748b !important;
}

/* Fix metric values */
[data-testid="stMetricValue"] {
    color: #1a2332 !important;
}

/* Fix radio buttons */
.stRadio label {
    color: #1a2332 !important;
}

/* Fix sidebar text */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {
    color: #1a2332 !important;
}
    
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0;
        min-width: 220px !important;
        max-width: 220px !important;
    }
    
    [data-testid="stSidebar"] * {
        font-size: 14px !important;
        font-weight: 500 !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    div[data-testid="metric-container"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 16px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }

    div[data-testid="metric-container"] label {
        color: #64748b !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }

    div[data-testid="metric-container"] [data-testid="metric-value"] {
        color: #1a2332 !important;
        font-size: 18px !important;
        font-weight: 700 !important;
    }

    .ticker-header {
        background: white;
        border-radius: 12px;
        padding: 20px 24px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        margin-bottom: 16px;
    }

    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 14px 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        margin-bottom: 10px;
    }

    .badge-green {
        background: #f0fdf4;
        color: #16a34a;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin: 2px;
    }

    .badge-red {
        background: #fef2f2;
        color: #dc2626;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin: 2px;
    }

    .section-title {
        font-size: 13px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)


# HELPER FUNCTIONS
def format_number(num):
    if num is None or (isinstance(num, float) and pd.isna(num)):
        return "N/A"
    if abs(num) >= 1e12:
        return f"${num/1e12:.2f}T"
    elif abs(num) >= 1e9:
        return f"${num/1e9:.2f}B"
    elif abs(num) >= 1e6:
        return f"${num/1e6:.2f}M"
    else:
        return f"${num:,.2f}"

def format_percent(num):
    if num is None or (isinstance(num, float) and pd.isna(num)):
        return "N/A"
    return f"{num*100:.2f}%"

def calculate_cagr(start, end, years):
    try:
        if start is None or end is None or start <= 0 or years == 0:
            return None
        return (end/start)**(1/years) - 1
    except:
        return None

def get_cagr_badges(series):
    if series is None or len(series) < 2:
        return {}
    series = series.dropna()
    if len(series) < 2:
        return {}
    current = series.iloc[-1]
    badges = {}
    periods = {"1Y": 1, "3Y": 3, "5Y": 5, "10Y": 10}
    for label, years in periods.items():
        idx = -min(years + 1, len(series))
        start_val = series.iloc[idx]
        cagr = calculate_cagr(float(start_val), float(current), years)
        if cagr is not None:
            badges[label] = cagr
    return badges

def render_cagr_badges(badges):
    html = ""
    for label, value in badges.items():
        pct = f"{value*100:.2f}%"
        css = "badge-green" if value >= 0 else "badge-red"
        html += f'<span class="{css}">{label}: {pct}</span>'
    return html

def create_bar_chart(x, y, title, color="#6366f1"):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x, y=y,
        marker_color=color,
        marker_opacity=0.85,
        hovertemplate='%{x}: %{y:,.2f}<extra></extra>'
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#1a2332"), x=0.5),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=10, color="#64748b"),
            type='category'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f1f5f9",
            tickfont=dict(size=10, color="#64748b")
        ),
        height=250,
        showlegend=False
    )
    return fig

def create_line_chart(x, y, title, color="#0ea5a0"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode='lines+markers',
        line=dict(color=color, width=2.5),
        marker=dict(size=4, color=color),
        fill='tozeroy',
        fillcolor='rgba(14,165,160,0.08)',
        hovertemplate='%{x}: %{y:,.2f}<extra></extra>'
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#1a2332"), x=0.5),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=10, color="#64748b"),
            type='category'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f1f5f9",
            tickfont=dict(size=10, color="#64748b")
        ),
        height=250,
        showlegend=False
    )
    return fig


# SIDEBAR
with st.sidebar:
    st.markdown("### 📊 StockLens")
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["🏠 Main", "💵 Cash", "🏦 Debt", "⚖️ Valuation", "🔍 Intrinsic Value", "📋 Shares"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("**Data Sources**")
    st.markdown("• Yahoo Finance")
    st.markdown("• Financial Modeling Prep")
    st.markdown("---")
    st.markdown("*Updates daily*")


# TOP SEARCH
st.markdown('<h2 style="color:#1a2332;">📊 StockLens Dashboard</h2>', unsafe_allow_html=True)
col_search, col_view = st.columns([3, 2])

with col_search:
    ticker_input = st.text_input(
        "Ticker",
        value="AAPL",
        placeholder="Enter ticker symbol...",
        label_visibility="collapsed"
    )

with col_view:
    view = st.radio(
        "View",
        ["TTM", "Quarterly", "Yearly"],
        horizontal=True,
        label_visibility="collapsed"
    )

ticker_input = ticker_input.upper().strip()


# LOAD DATA
@st.cache_data(ttl=3600)
def load_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    income_annual = stock.financials
    income_quarterly = stock.quarterly_financials
    cashflow_annual = stock.cashflow
    cashflow_quarterly = stock.quarterly_cashflow
    balance_annual = stock.balance_sheet
    balance_quarterly = stock.quarterly_balance_sheet
    hist = stock.history(period="10y")
    earnings_dates = stock.earnings_dates
    return {
        "info": info,
        "income_annual": income_annual,
        "income_quarterly": income_quarterly,
        "cashflow_annual": cashflow_annual,
        "cashflow_quarterly": cashflow_quarterly,
        "balance_annual": balance_annual,
        "balance_quarterly": balance_quarterly,
        "earnings_dates": earnings_dates,
        "hist": hist
    }


if ticker_input:
    try:
        with st.spinner(f"Loading {ticker_input}..."):
            data = load_data(ticker_input)

        info = data["info"]

        if view == "Quarterly":
            income = data["income_quarterly"]
            cashflow = data["cashflow_quarterly"]
            balance = data["balance_quarterly"]
        else:
            income = data["income_annual"]
            cashflow = data["cashflow_annual"]
            balance = data["balance_annual"]

        # TICKER HEADER
        company_name = info.get("longName", ticker_input)
        current_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
        prev_close = info.get("previousClose", current_price)
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        change_color = "#16a34a" if change >= 0 else "#dc2626"
        change_arrow = "▲" if change >= 0 else "▼"

        st.markdown(f"""
        <div class="ticker-header">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:26px; font-weight:700; color:#0ea5a0;">{ticker_input}</span>
                    &nbsp;&nbsp;
                    <span style="font-size:18px; font-weight:600; color:#1a2332;">{company_name}</span><br>
                    <span style="font-size:12px; color:#64748b;">{info.get('sector','')} &nbsp;·&nbsp; {info.get('exchange','')} &nbsp;·&nbsp; {info.get('industry','')}</span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:30px; font-weight:700; color:#1a2332;">${current_price:,.2f}</span><br>
                    <span style="color:{change_color}; font-size:14px; font-weight:600;">{change_arrow} ${abs(change):.2f} ({abs(change_pct):.2f}%) today</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


        # MAIN PAGE
        if "Main" in page:

            # KEY STATS
            market_cap = info.get("marketCap")
            pe_ratio = info.get("trailingPE")
            eps = info.get("trailingEps")
            revenue = info.get("totalRevenue")
            net_margin = info.get("profitMargins")
            roe = info.get("returnOnEquity")

            c1, c2, c3, c4, c5, c6 = st.columns(6)
            with c1:
                st.metric("Market Cap", format_number(market_cap))
            with c2:
                st.metric("P/E Ratio", f"{pe_ratio:.1f}x" if pe_ratio else "N/A")
            with c3:
                st.metric("EPS (TTM)", f"${eps:.2f}" if eps else "N/A")
            with c4:
                st.metric("Revenue", format_number(revenue))
            with c5:
                st.metric("Net Margin", format_percent(net_margin))
            with c6:
                st.metric("ROE", format_percent(roe))

            st.markdown("<br>", unsafe_allow_html=True)

            # CHARTS
            col1, col2 = st.columns(2)

            with col1:
                if income is not None and not income.empty and "Total Revenue" in income.index:
                    rev_data = income.loc["Total Revenue"].dropna().sort_index()
                    years = [str(d.year) for d in rev_data.index]
                    values = (rev_data.values / 1e9).tolist()
                    fig = create_bar_chart(years, values, "Revenue ($B)", "#6366f1")
                    st.plotly_chart(fig, use_container_width=True)
                    badges = get_cagr_badges(rev_data)
                    st.markdown(f"<center>{render_cagr_badges(badges)}</center>", unsafe_allow_html=True)

            with col2:
                if income is not None and not income.empty and "Basic EPS" in income.index:
                    eps_data = income.loc["Basic EPS"].dropna().sort_index()
                    years = [str(d.year) for d in eps_data.index]
                    values = eps_data.values.tolist()
                    fig = create_bar_chart(years, values, "Earnings Per Share (EPS)", "#7c3aed")
                    st.plotly_chart(fig, use_container_width=True)
                    badges = get_cagr_badges(eps_data)
                    st.markdown(f"<center>{render_cagr_badges(badges)}</center>", unsafe_allow_html=True)

            col3, col4 = st.columns(2)

            with col3:
                if income is not None and not income.empty and "Net Income" in income.index:
                    ni_data = income.loc["Net Income"].dropna().sort_index()
                    years = [str(d.year) for d in ni_data.index]
                    values = (ni_data.values / 1e9).tolist()
                    fig = create_bar_chart(years, values, "Net Income ($B)", "#0ea5a0")
                    st.plotly_chart(fig, use_container_width=True)
                    badges = get_cagr_badges(ni_data)
                    st.markdown(f"<center>{render_cagr_badges(badges)}</center>", unsafe_allow_html=True)

            with col4:
                if income is not None and not income.empty and "Gross Profit" in income.index:
                    gp_data = income.loc["Gross Profit"].dropna().sort_index()
                    years = [str(d.year) for d in gp_data.index]
                    values = (gp_data.values / 1e9).tolist()
                    fig = create_bar_chart(years, values, "Gross Profit ($B)", "#16a34a")
                    st.plotly_chart(fig, use_container_width=True)
                    badges = get_cagr_badges(gp_data)
                    st.markdown(f"<center>{render_cagr_badges(badges)}</center>", unsafe_allow_html=True)

            # EBITDA + OPERATING INCOME
            col5, col6 = st.columns(2)

            with col5:
                if income is not None and not income.empty and "EBITDA" in income.index:
                    ebitda_data = income.loc["EBITDA"].dropna().sort_index()
                    years = [str(d.year) for d in ebitda_data.index]
                    values = (ebitda_data.values / 1e9).tolist()
                    fig = create_bar_chart(years, values, "EBITDA ($B)", "#f59e0b")
                    st.plotly_chart(fig, use_container_width=True)
                    badges = get_cagr_badges(ebitda_data)
                    st.markdown(f"<center>{render_cagr_badges(badges)}</center>", unsafe_allow_html=True)

            with col6:
                if income is not None and not income.empty and "Operating Income" in income.index:
                    oi_data = income.loc["Operating Income"].dropna().sort_index()
                    years = [str(d.year) for d in oi_data.index]
                    values = (oi_data.values / 1e9).tolist()
                    fig = create_bar_chart(years, values, "Operating Income ($B)", "#ec4899")
                    st.plotly_chart(fig, use_container_width=True)
                    badges = get_cagr_badges(oi_data)
                    st.markdown(f"<center>{render_cagr_badges(badges)}</center>", unsafe_allow_html=True)

            # EARNINGS EVENTS
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📅 Earnings Events")

            earn_col1, earn_col2 = st.columns(2)

            with earn_col1:
                st.markdown('<div class="section-title">Upcoming Earnings</div>', unsafe_allow_html=True)
                if data["earnings_dates"] is not None:
                    try:
                        now = pd.Timestamp.now(tz='America/New_York')
                        upcoming = data["earnings_dates"][data["earnings_dates"].index > now]
                        if not upcoming.empty:
                            for date, row in upcoming.head(3).iterrows():
                                eps_est = row.get('EPS Estimate')
                                eps_str = f"${eps_est:.2f}" if pd.notna(eps_est) else "TBD"
                                st.markdown(f"""
                                <div class="metric-card">
                                    <span style="color:#0ea5a0;font-size:13px;font-weight:600;">{date.strftime('%b %d, %Y')}</span>
                                    <span style="background:#e6f7f7;color:#0ea5a0;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:700;float:right;">UPCOMING</span><br>
                                    <span style="font-weight:600;font-size:14px;">Earnings Report</span><br>
                                    <span style="color:#64748b;font-size:12px;">Est. EPS: {eps_str}</span>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("No upcoming earnings found")
                    except Exception:
                        st.info("Earnings data unavailable")

            with earn_col2:
                st.markdown('<div class="section-title">Historical Earnings</div>', unsafe_allow_html=True)
                if data["earnings_dates"] is not None:
                    try:
                        now = pd.Timestamp.now(tz='America/New_York')
                        historical = data["earnings_dates"][data["earnings_dates"].index <= now]
                        if not historical.empty:
                            for date, row in historical.head(4).iterrows():
                                eps_actual = row.get('Reported EPS')
                                eps_est = row.get('EPS Estimate')
                                if pd.notna(eps_actual) and pd.notna(eps_est):
                                    beat = float(eps_actual) >= float(eps_est)
                                    result_color = "#16a34a" if beat else "#dc2626"
                                    result_text = "Beat ✓" if beat else "Miss ✗"
                                else:
                                    result_color = "#64748b"
                                    result_text = ""
                                eps_actual_str = f"${float(eps_actual):.2f}" if pd.notna(eps_actual) else "N/A"
                                eps_est_str = f"${float(eps_est):.2f}" if pd.notna(eps_est) else "N/A"
                                st.markdown(f"""
                                <div class="metric-card">
                                    <span style="color:#0ea5a0;font-size:13px;font-weight:600;">{date.strftime('%b %d, %Y')}</span>
                                    <span style="color:{result_color};font-weight:700;float:right;font-size:15px;">{eps_actual_str}</span><br>
                                    <span style="font-weight:600;font-size:14px;">Quarterly Earnings &nbsp;<span style="color:{result_color};">{result_text}</span></span><br>
                                    <span style="color:#64748b;font-size:12px;">Est: {eps_est_str}</span>
                                </div>
                                """, unsafe_allow_html=True)
                    except Exception:
                        st.info("Historical earnings unavailable")

        elif "Cash" in page:
            st.info("💵 Cash Page — Coming soon!")

        elif "Debt" in page:
            st.info("🏦 Debt Page — Coming soon!")

        elif "Valuation" in page:
            st.info("⚖️ Valuation Page — Coming soon!")

        elif "Intrinsic" in page:
            st.info("🔍 Intrinsic Value Page — Coming soon!")

        elif "Shares" in page:
            st.info("📋 Shares Page — Coming soon!")

    except Exception as e:
        st.error(f"Error loading {ticker_input}. Please check the ticker and try again.")
        st.error(str(e))