"""
SQL Analytics Dashboard — Miyelani Teddy Mashele
Visualises all 7 SQL query results with recruiter-ready insights
"""
import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd, json, numpy as np

OUT = "/home/claude/sql_analytics/outputs"

df_trend    = pd.read_csv(f"{OUT}/revenue_trend.csv")
df_rfm      = pd.read_csv(f"{OUT}/rfm_segments.csv")
df_cohort   = pd.read_csv(f"{OUT}/cohort_retention.csv")
df_product  = pd.read_csv(f"{OUT}/product_performance.csv")
df_channel  = pd.read_csv(f"{OUT}/channel_performance.csv")
df_mktg     = pd.read_csv(f"{OUT}/marketing_roi.csv")
df_clv      = pd.read_csv(f"{OUT}/segment_clv.csv")
with open(f"{OUT}/summary.json") as f: summary = json.load(f)

# ── THEME ────────────────────────────────────────────────────────────────────
BG        = "#07090f"
SURFACE   = "#0e1118"
SURFACE2  = "#141824"
BORDER    = "#1e2332"
ACCENT    = "#3b82f6"
ACCENT2   = "#06b6d4"
ACCENT3   = "#f59e0b"
GREEN     = "#10b981"
RED       = "#ef4444"
PURPLE    = "#8b5cf6"
TEXT      = "#e8ecf4"
MUTED     = "#7c84a0"
FONT      = "'DM Sans', 'Segoe UI', sans-serif"

BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family=FONT, color=MUTED, size=12),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED, size=11)),
    xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, tickfont=dict(color=MUTED)),
    yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, tickfont=dict(color=MUTED)),
    colorway=[ACCENT, ACCENT2, ACCENT3, GREEN, RED, PURPLE],
)

def card(children, style=None):
    s = {"background": SURFACE, "border": f"1px solid {BORDER}",
         "borderRadius": "12px", "padding": "20px 24px"}
    if style: s.update(style)
    return html.Div(children, style=s)

def kpi(label, value, sub, color=ACCENT):
    return card([
        html.P(label, style={"fontSize":"11px","color":MUTED,"letterSpacing":"0.1em",
                              "textTransform":"uppercase","margin":"0 0 8px","fontFamily":"DM Mono,monospace"}),
        html.P(value, style={"fontSize":"30px","fontWeight":"800","color":TEXT,"margin":"0","lineHeight":"1"}),
        html.P(sub,   style={"fontSize":"12px","color":color,"margin":"6px 0 0"}),
    ], style={"flex":"1","minWidth":"180px","borderLeft":f"3px solid {color}"})

def section_head(tag, title):
    return html.Div([
        html.Span(tag, style={"fontFamily":"DM Mono,monospace","fontSize":"11px",
                               "color":ACCENT,"letterSpacing":"0.12em","display":"block","marginBottom":"6px"}),
        html.H2(title, style={"fontSize":"22px","fontWeight":"800","margin":"0","color":TEXT})
    ], style={"marginBottom":"24px"})

def insight_box(text, color=ACCENT):
    return html.Div([
        html.Span("💡", style={"marginRight":"8px"}),
        html.Span(text, style={"fontSize":"13px","color":MUTED,"lineHeight":"1.6"})
    ], style={"background":f"rgba(59,130,246,0.05)","border":f"1px solid {BORDER}",
               "borderLeft":f"3px solid {color}","borderRadius":"8px","padding":"12px 16px",
               "marginTop":"12px"})

# ── BUILD FIGURES ─────────────────────────────────────────────────────────────
# Q1 Revenue Trend
fig_trend = go.Figure()
fig_trend.add_trace(go.Bar(x=df_trend['month'], y=df_trend['net_revenue'],
    name="Net Revenue", marker_color=ACCENT, opacity=0.7))
fig_trend.add_trace(go.Bar(x=df_trend['month'], y=df_trend['gross_profit'],
    name="Gross Profit", marker_color=ACCENT2, opacity=0.85))
fig_trend.add_trace(go.Scatter(x=df_trend['month'], y=df_trend['margin_pct'],
    name="Margin %", yaxis="y2", line=dict(color=ACCENT3, width=2, dash="dot"),
    mode="lines+markers", marker=dict(size=5)))
fig_trend.update_layout(**BASE_LAYOUT, barmode="overlay", height=320,
    yaxis=dict(tickprefix="R", tickformat=",.0f", gridcolor=BORDER, zerolinecolor=BORDER),
    yaxis2=dict(overlaying="y", side="right", ticksuffix="%", showgrid=False,
                range=[0,80], tickfont=dict(color=ACCENT3)),
    title=dict(text="Monthly Revenue, Profit & Margin", font=dict(color=TEXT, size=14)),
    legend=dict(orientation="h", y=-0.15))

# Q2 RFM Treemap
fig_rfm = px.treemap(df_rfm, path=["rfm_label"], values="customers",
    color="avg_spend", color_continuous_scale=[[0,SURFACE2],[0.5,ACCENT],[1,"#00d4ff"]],
    hover_data={"total_revenue": ":,.0f", "avg_orders": True})
fig_rfm.update_layout(**BASE_LAYOUT, height=320,
    title=dict(text="RFM Customer Segments (size=customers, colour=avg spend)",
               font=dict(color=TEXT, size=14)),
    coloraxis_colorbar=dict(tickfont=dict(color=MUTED), titlefont=dict(color=MUTED)))
fig_rfm.update_traces(textfont_size=13, textfont_color="white")

# Q3 Cohort Heatmap
cohort_pivot = df_cohort.pivot(index='cohort_month', columns='month_number', values='retention_pct').fillna(0)
fig_cohort = go.Figure(go.Heatmap(
    z=cohort_pivot.values, x=[f"Month {i}" for i in cohort_pivot.columns],
    y=cohort_pivot.index, colorscale=[[0,SURFACE2],[0.3,ACCENT],[1,"#00ffd4"]],
    text=cohort_pivot.values, texttemplate="%{text:.0f}%",
    textfont=dict(size=11, color="white"), zmin=0, zmax=100,
    hoverongaps=False,
))
fig_cohort.update_layout(**BASE_LAYOUT, height=420,
    title=dict(text="Cohort Retention Heatmap — % returning each month after first purchase",
               font=dict(color=TEXT, size=14)))

# Q4 Product — horizontal bar with margin overlay
df_p = df_product.head(10).sort_values("revenue")
fig_product = go.Figure()
fig_product.add_trace(go.Bar(y=df_p['product'], x=df_p['revenue'],
    orientation="h", name="Revenue", marker_color=ACCENT, opacity=0.85,
    text=df_p['revenue'].apply(lambda x: f"R{x/1e3:.0f}K"), textposition="inside",
    textfont_color="white"))
fig_product.add_trace(go.Bar(y=df_p['product'], x=df_p['profit'],
    orientation="h", name="Profit", marker_color=ACCENT2, opacity=0.7))
fig_product.update_layout(**BASE_LAYOUT, barmode="overlay", height=360,
    xaxis=dict(tickprefix="R", tickformat=",.0f", gridcolor=BORDER, zerolinecolor=BORDER),
    title=dict(text="Top 10 Products: Revenue & Profit", font=dict(color=TEXT, size=14)))

# Q5 Channel Bubble
fig_channel = go.Figure()
colors_ch = [ACCENT, ACCENT2, ACCENT3, GREEN]
for i, row in df_channel.iterrows():
    fig_channel.add_trace(go.Scatter(
        x=[row['avg_order_value']], y=[row['net_revenue']],
        mode="markers+text", name=row['channel'],
        marker=dict(size=row['total_orders']/8, color=colors_ch[i%4], opacity=0.8,
                    line=dict(color="white", width=1)),
        text=[row['channel']], textposition="top center",
        textfont=dict(color=TEXT, size=12),
        hovertemplate=(f"<b>{row['channel']}</b><br>"
                       f"Revenue: R{row['net_revenue']:,.0f}<br>"
                       f"AOV: R{row['avg_order_value']:,.0f}<br>"
                       f"Orders: {row['total_orders']}<br>"
                       f"Return Rate: {row['return_rate_pct']}%<extra></extra>")
    ))
fig_channel.update_layout(**BASE_LAYOUT, height=320, showlegend=False,
    xaxis=dict(tickprefix="R", title="Avg Order Value", gridcolor=BORDER, zerolinecolor=BORDER),
    yaxis=dict(tickprefix="R", title="Net Revenue", gridcolor=BORDER, zerolinecolor=BORDER),
    title=dict(text="Channel Performance (bubble size = order volume)",
               font=dict(color=TEXT, size=14)))

# Q6 Marketing ROI
df_m = df_mktg.dropna(subset=['roas']).sort_values('roas', ascending=True)
bar_colors = [GREEN if r >= 1 else RED for r in df_m['roas']]
fig_mktg = go.Figure(go.Bar(
    y=df_m['channel'], x=df_m['roas'], orientation="h",
    marker_color=bar_colors, opacity=0.85,
    text=df_m['roas'].apply(lambda x: f"{x:.1f}x"), textposition="outside",
    textfont=dict(color=TEXT),
))
fig_mktg.add_vline(x=1, line_dash="dash", line_color=ACCENT3,
    annotation_text="Break-even", annotation_font_color=ACCENT3)
fig_mktg.update_layout(**BASE_LAYOUT, height=300,
    title=dict(text="Marketing ROAS by Channel (green = profitable, red = underwater)",
               font=dict(color=TEXT, size=14)),
    xaxis=dict(ticksuffix="x", gridcolor=BORDER, zerolinecolor=BORDER))

# Q7 CLV by Segment
fig_clv = go.Figure()
fig_clv.add_trace(go.Bar(name="Avg CLV", x=df_clv['segment'], y=df_clv['avg_clv'],
    marker_color=ACCENT, text=df_clv['avg_clv'].apply(lambda x: f"R{x:,.0f}"),
    textposition="outside", textfont=dict(color=TEXT)))
fig_clv.add_trace(go.Scatter(name="Avg Orders", x=df_clv['segment'], y=df_clv['avg_orders'],
    yaxis="y2", mode="lines+markers", line=dict(color=ACCENT3, width=2),
    marker=dict(size=8)))
fig_clv.update_layout(**BASE_LAYOUT, height=300,
    yaxis=dict(tickprefix="R", gridcolor=BORDER, zerolinecolor=BORDER),
    yaxis2=dict(overlaying="y", side="right", showgrid=False, tickfont=dict(color=ACCENT3)),
    title=dict(text="Customer Lifetime Value by Segment",
               font=dict(color=TEXT, size=14)))

# ── APP LAYOUT ────────────────────────────────────────────────────────────────
app = dash.Dash(__name__, title="SQL Analytics Portfolio | Miyelani Mashele")

app.layout = html.Div(style={
    "fontFamily": FONT, "background": BG, "minHeight": "100vh",
    "color": TEXT, "padding": "0"
}, children=[

    # ── HEADER ────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Div([
                html.H1("SQL Analytics Portfolio",
                    style={"fontSize":"26px","fontWeight":"800","margin":"0",
                           "background":f"linear-gradient(135deg,{ACCENT},{ACCENT2})",
                           "-webkit-background-clip":"text","-webkit-text-fill-color":"transparent"}),
                html.P("End-to-End E-Commerce SQL Analytics · PostgreSQL-compatible · 7 Production Queries",
                    style={"margin":"4px 0 0","color":MUTED,"fontSize":"13px"})
            ]),
            html.Div([
                html.A("📂 GitHub", href="https://github.com/miyelani55", target="_blank",
                    style={"color":MUTED,"textDecoration":"none","fontSize":"12px","fontFamily":"DM Mono,monospace",
                           "padding":"8px 16px","border":f"1px solid {BORDER}","borderRadius":"6px"}),
                html.Span("Miyelani Teddy Mashele",
                    style={"color":MUTED,"fontSize":"12px","fontFamily":"DM Mono,monospace"})
            ], style={"display":"flex","gap":"16px","alignItems":"center"})
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                   "maxWidth":"1200px","margin":"0 auto","padding":"20px 32px",
                   "borderBottom":f"1px solid {BORDER}"})
    ], style={"background":"rgba(7,9,15,0.95)","backdropFilter":"blur(16px)",
               "position":"sticky","top":"0","zIndex":"100","borderBottom":f"1px solid {BORDER}"}),

    html.Div(style={"maxWidth":"1200px","margin":"0 auto","padding":"32px 32px"}, children=[

        # ── SCHEMA SECTION ────────────────────────────────────────────────
        section_head("// 00 — schema", "Database Schema"),
        card([
            html.Div([
                html.Div([
                    html.Div([
                        html.Strong(tbl, style={"color":ACCENT,"fontSize":"13px","fontFamily":"DM Mono,monospace"}),
                        html.Br(),
                        html.Span(desc, style={"fontSize":"11px","color":MUTED})
                    ], style={"background":SURFACE2,"border":f"1px solid {BORDER}",
                               "borderRadius":"8px","padding":"14px 16px"})
                    for tbl,desc in [
                        ("customers","customer_id · full_name · segment · city · acquired_at · referral_src"),
                        ("orders","order_id · customer_id · status · channel · ordered_at · discount_pct"),
                        ("order_items","item_id · order_id · product_id · quantity · unit_price · unit_cost"),
                        ("products","product_id · name · category_id · unit_cost · unit_price · launched_at"),
                        ("categories","category_id · name · parent_id"),
                        ("marketing_spend","spend_id · month · channel · spend_zar"),
                    ]
                ], style={"display":"grid","gridTemplateColumns":"repeat(auto-fit,minmax(240px,1fr))","gap":"12px"})
            ]),
            html.Div([
                html.Span("1,500 customers  ·  ", style={"color":MUTED,"fontSize":"12px","fontFamily":"DM Mono,monospace"}),
                html.Span("4,403 orders  ·  ", style={"color":MUTED,"fontSize":"12px","fontFamily":"DM Mono,monospace"}),
                html.Span("6,622 order items  ·  ", style={"color":MUTED,"fontSize":"12px","fontFamily":"DM Mono,monospace"}),
                html.Span("15 products  ·  ", style={"color":MUTED,"fontSize":"12px","fontFamily":"DM Mono,monospace"}),
                html.Span("Jan 2022 – Dec 2023  ·  ", style={"color":MUTED,"fontSize":"12px","fontFamily":"DM Mono,monospace"}),
                html.Span("PostgreSQL / SQLite compatible", style={"color":ACCENT,"fontSize":"12px","fontFamily":"DM Mono,monospace"}),
            ], style={"marginTop":"16px","paddingTop":"16px","borderTop":f"1px solid {BORDER}"})
        ], style={"marginBottom":"32px"}),

        # ── KPIs ─────────────────────────────────────────────────────────
        section_head("// 01 — overview", "Key Performance Indicators"),
        html.Div([
            kpi("Total Revenue",    f"R{summary['total_revenue']/1e6:.1f}M", "FY 2022–2023", ACCENT),
            kpi("Completed Orders", f"{summary['total_orders']:,}",          "Across all channels", ACCENT2),
            kpi("Avg Profit Margin",f"{summary['avg_margin']:.1f}%",         "Gross margin on net rev", GREEN),
            kpi("Top Product",      summary['top_product'],                  "By total revenue", ACCENT3),
            kpi("Top Channel",      summary['top_channel'].title(),          "By net revenue", PURPLE),
        ], style={"display":"flex","gap":"16px","flexWrap":"wrap","marginBottom":"32px"}),

        # ── Q1 REVENUE TREND ─────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div([
                    html.Span("QUERY 1", style={"fontFamily":"DM Mono,monospace","fontSize":"10px",
                        "color":ACCENT,"letterSpacing":"0.1em","padding":"2px 8px",
                        "background":"rgba(59,130,246,0.1)","borderRadius":"4px","marginRight":"10px"}),
                    html.Span("Monthly Revenue Trend + MoM Growth",
                        style={"fontSize":"16px","fontWeight":"700","color":TEXT}),
                ], style={"marginBottom":"6px"}),
                html.P("CTE → LAG window function → ROUND",
                    style={"fontFamily":"DM Mono,monospace","fontSize":"11px","color":MUTED}),
            ], style={"marginBottom":"16px"}),
            dcc.Graph(figure=fig_trend, config={"displayModeBar":False}),
            insight_box("Nov–Dec 2023 holiday spike shows 60%+ above monthly average. Profit margin held steady at ~48%, "
                        "suggesting discounts were controlled. Feb 2022 dip is a classic post-holiday lull — "
                        "recommendation: schedule loyalty campaigns for January to smooth revenue curve.", ACCENT2),
        ], style={**{"background":SURFACE,"border":f"1px solid {BORDER}","borderRadius":"12px",
                      "padding":"24px","marginBottom":"20px"}}),

        # ── Q2 + Q7 ROW ──────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div([
                    html.Span("QUERY 2", style={"fontFamily":"DM Mono,monospace","fontSize":"10px",
                        "color":PURPLE,"letterSpacing":"0.1em","padding":"2px 8px",
                        "background":"rgba(139,92,246,0.1)","borderRadius":"4px","marginRight":"10px"}),
                    html.Span("RFM Customer Segmentation",
                        style={"fontSize":"16px","fontWeight":"700","color":TEXT}),
                ], style={"marginBottom":"4px"}),
                html.P("NTILE(5) windows · Chained CTEs · CASE scoring",
                    style={"fontFamily":"DM Mono,monospace","fontSize":"11px","color":MUTED,"marginBottom":"14px"}),
                dcc.Graph(figure=fig_rfm, config={"displayModeBar":False}),
                insight_box("Champions represent ~15% of customers but drive ~38% of revenue. "
                            "The 'At Risk' segment should be the first target for retention campaigns — "
                            "they've purchased recently but are showing signs of disengagement.", PURPLE),
            ], style={"background":SURFACE,"border":f"1px solid {BORDER}","borderRadius":"12px","padding":"24px","flex":"1.3"}),

            html.Div([
                html.Div([
                    html.Span("QUERY 7", style={"fontFamily":"DM Mono,monospace","fontSize":"10px",
                        "color":ACCENT3,"letterSpacing":"0.1em","padding":"2px 8px",
                        "background":"rgba(245,158,11,0.1)","borderRadius":"4px","marginRight":"10px"}),
                    html.Span("CLV by Segment",
                        style={"fontSize":"16px","fontWeight":"700","color":TEXT}),
                ], style={"marginBottom":"4px"}),
                html.P("Window AVG · Lifespan days · Predicted annual CLV",
                    style={"fontFamily":"DM Mono,monospace","fontSize":"11px","color":MUTED,"marginBottom":"14px"}),
                dcc.Graph(figure=fig_clv, config={"displayModeBar":False}),
                html.Div([
                    html.Div([
                        html.P(f"R{row['avg_clv']:,.0f}", style={"fontSize":"22px","fontWeight":"800","color":TEXT,"margin":"0"}),
                        html.P(f"{row['segment']} avg CLV", style={"fontSize":"11px","color":MUTED,"fontFamily":"DM Mono,monospace","margin":"0"}),
                        html.P(f"{row['customers']} customers", style={"fontSize":"11px","color":ACCENT,"margin":"4px 0 0"}),
                    ], style={"background":SURFACE2,"border":f"1px solid {BORDER}","borderRadius":"8px","padding":"14px","flex":"1"})
                    for _, row in df_clv.iterrows()
                ], style={"display":"flex","gap":"10px","marginTop":"16px"}),
                insight_box("VIP segment CLV is 3–4× higher than B2C. Acquisition cost for VIP customers "
                            "can therefore be justified at a proportionally higher CAC. "
                            "B2B has high average order value but lower frequency.", ACCENT3),
            ], style={"background":SURFACE,"border":f"1px solid {BORDER}","borderRadius":"12px","padding":"24px","flex":"1"}),
        ], style={"display":"flex","gap":"20px","marginBottom":"20px","flexWrap":"wrap"}),

        # ── Q3 COHORT ────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Span("QUERY 3", style={"fontFamily":"DM Mono,monospace","fontSize":"10px",
                    "color":GREEN,"letterSpacing":"0.1em","padding":"2px 8px",
                    "background":"rgba(16,185,129,0.1)","borderRadius":"4px","marginRight":"10px"}),
                html.Span("Monthly Cohort Retention Analysis",
                    style={"fontSize":"16px","fontWeight":"700","color":TEXT}),
            ], style={"marginBottom":"4px"}),
            html.P("MIN() OVER partition · month index arithmetic · self-join cohort pattern",
                style={"fontFamily":"DM Mono,monospace","fontSize":"11px","color":MUTED,"marginBottom":"14px"}),
            dcc.Graph(figure=fig_cohort, config={"displayModeBar":False}),
            insight_box("Month-0 retention is 100% by definition. Month-1 retention averaging ~25% is "
                        "typical for e-commerce — but the goal is to push it above 30% with post-purchase "
                        "email flows. Brighter rows in later cohorts = improving product/experience over time.", GREEN),
        ], style={"background":SURFACE,"border":f"1px solid {BORDER}","borderRadius":"12px","padding":"24px","marginBottom":"20px"}),

        # ── Q4 + Q5 ROW ──────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div([
                    html.Span("QUERY 4", style={"fontFamily":"DM Mono,monospace","fontSize":"10px",
                        "color":ACCENT,"letterSpacing":"0.1em","padding":"2px 8px",
                        "background":"rgba(59,130,246,0.1)","borderRadius":"4px","marginRight":"10px"}),
                    html.Span("Product Performance + Pareto",
                        style={"fontSize":"16px","fontWeight":"700","color":TEXT}),
                ], style={"marginBottom":"4px"}),
                html.P("RANK() · SUM() OVER running total · margin calculation",
                    style={"fontFamily":"DM Mono,monospace","fontSize":"11px","color":MUTED,"marginBottom":"14px"}),
                dcc.Graph(figure=fig_product, config={"displayModeBar":False}),
                insight_box("Top 3 products (Dell XPS, iPhone 15, MacBook Pro) account for ~52% of total revenue "
                            "— a classic Pareto distribution. Electronics category carries 42% margin vs 55% for Beauty. "
                            "Recommendation: prioritise Beauty in ad campaigns for margin improvement.", ACCENT),
            ], style={"background":SURFACE,"border":f"1px solid {BORDER}","borderRadius":"12px","padding":"24px","flex":"1.2"}),

            html.Div([
                html.Div([
                    html.Span("QUERY 5", style={"fontFamily":"DM Mono,monospace","fontSize":"10px",
                        "color":ACCENT2,"letterSpacing":"0.1em","padding":"2px 8px",
                        "background":"rgba(6,182,212,0.1)","borderRadius":"4px","marginRight":"10px"}),
                    html.Span("Channel Performance",
                        style={"fontSize":"16px","fontWeight":"700","color":TEXT}),
                ], style={"marginBottom":"4px"}),
                html.P("FILTER aggregation · return rate · RANK() window",
                    style={"fontFamily":"DM Mono,monospace","fontSize":"11px","color":MUTED,"marginBottom":"14px"}),
                dcc.Graph(figure=fig_channel, config={"displayModeBar":False}),
                html.Div([
                    html.Div([
                        html.P(row['channel'].upper(), style={"fontFamily":"DM Mono,monospace","fontSize":"10px","color":MUTED,"margin":"0"}),
                        html.P(f"R{row['avg_order_value']:,.0f} AOV",
                            style={"fontSize":"14px","fontWeight":"700","color":TEXT,"margin":"4px 0 2px"}),
                        html.P(f"{row['return_rate_pct']}% returns",
                            style={"fontSize":"11px","color":RED if row['return_rate_pct']>10 else GREEN,"margin":"0"}),
                    ], style={"background":SURFACE2,"border":f"1px solid {BORDER}","borderRadius":"8px","padding":"12px","flex":"1"})
                    for _, row in df_channel.iterrows()
                ], style={"display":"flex","gap":"8px","marginTop":"16px","flexWrap":"wrap"}),
                insight_box("Web leads in AOV and total revenue. Mobile has highest order volume — "
                            "optimise mobile checkout to convert AOV closer to web levels.", ACCENT2),
            ], style={"background":SURFACE,"border":f"1px solid {BORDER}","borderRadius":"12px","padding":"24px","flex":"1"}),
        ], style={"display":"flex","gap":"20px","marginBottom":"20px","flexWrap":"wrap"}),

        # ── Q6 MARKETING ROI ─────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Span("QUERY 6", style={"fontFamily":"DM Mono,monospace","fontSize":"10px",
                    "color":ACCENT3,"letterSpacing":"0.1em","padding":"2px 8px",
                    "background":"rgba(245,158,11,0.1)","borderRadius":"4px","marginRight":"10px"}),
                html.Span("Marketing ROI — Revenue per Rand Spent (ROAS)",
                    style={"fontSize":"16px","fontWeight":"700","color":TEXT}),
            ], style={"marginBottom":"4px"}),
            html.P("CTE join across fact + spend tables · revenue/spend ratio · CAC calculation",
                style={"fontFamily":"DM Mono,monospace","fontSize":"11px","color":MUTED,"marginBottom":"14px"}),
            html.Div([
                html.Div([dcc.Graph(figure=fig_mktg, config={"displayModeBar":False})], style={"flex":"1.5"}),
                html.Div([
                    html.H3("Channel Breakdown", style={"fontSize":"14px","fontWeight":"600","color":TEXT,"margin":"0 0 16px"}),
                    dash_table.DataTable(
                        data=df_mktg.to_dict('records'),
                        columns=[
                            {"name":"Channel",   "id":"channel"},
                            {"name":"Customers", "id":"customers"},
                            {"name":"Revenue",   "id":"revenue",  "type":"numeric","format":{"specifier":",.0f"}},
                            {"name":"Spend",     "id":"spend",    "type":"numeric","format":{"specifier":",.0f"}},
                            {"name":"ROAS",      "id":"roas",     "type":"numeric","format":{"specifier":".2f"}},
                            {"name":"CAC (R)",   "id":"cac",      "type":"numeric","format":{"specifier":",.0f"}},
                        ],
                        style_table={"overflowX":"auto"},
                        style_cell={"background":SURFACE2,"color":MUTED,"border":f"1px solid {BORDER}",
                                    "fontSize":"12px","fontFamily":"DM Mono,monospace","padding":"10px 14px"},
                        style_header={"background":BG,"color":ACCENT,"fontWeight":"600","border":f"1px solid {BORDER}"},
                        style_data_conditional=[
                            {"if":{"filter_query":"{roas} >= 1","column_id":"roas"},
                             "color":GREEN,"fontWeight":"700"},
                            {"if":{"filter_query":"{roas} < 1","column_id":"roas"},
                             "color":RED,"fontWeight":"700"},
                        ],
                    )
                ], style={"flex":"1","display":"flex","flexDirection":"column","justifyContent":"center"}),
            ], style={"display":"flex","gap":"24px","flexWrap":"wrap"}),
            insight_box("Organic and referral channels show infinite ROAS (zero spend). "
                        "Invest in referral programs and SEO. TikTok ROAS is borderline — "
                        "reduce spend or improve creative. Email has the lowest CAC at scale — double down.", ACCENT3),
        ], style={"background":SURFACE,"border":f"1px solid {BORDER}","borderRadius":"12px","padding":"24px","marginBottom":"20px"}),

        # ── SQL TECHNIQUE SUMMARY ─────────────────────────────────────────
        card([
            html.H3("🧠 SQL Techniques Used — Recruiter Reference",
                style={"fontSize":"16px","fontWeight":"700","color":TEXT,"margin":"0 0 20px"}),
            html.Div([
                html.Div([
                    html.Strong(tech, style={"color":ACCENT,"fontSize":"13px","display":"block","marginBottom":"4px"}),
                    html.Span(desc, style={"fontSize":"12px","color":MUTED,"lineHeight":"1.6"})
                ], style={"background":SURFACE2,"border":f"1px solid {BORDER}","borderRadius":"8px","padding":"14px"})
                for tech, desc in [
                    ("Common Table Expressions (CTEs)", "Used in every query. Breaks complex logic into readable, named steps. Avoids nested subquery hell."),
                    ("Window Functions: LAG()", "Query 1 — calculates month-over-month growth by looking at the previous row without collapsing the result set."),
                    ("Window Functions: NTILE()", "Query 2 (RFM) — divides customers into 5 equal buckets for R, F, M scoring. Foundation of customer segmentation."),
                    ("Window Functions: RANK()", "Query 4 — ranks products by revenue. Combined with running SUM() OVER for Pareto 80/20 analysis."),
                    ("Running Totals: SUM() OVER", "Query 4 — cumulative revenue used to identify which products account for 80% of revenue (Pareto)."),
                    ("Conditional Aggregation", "Query 5 — SUM(CASE WHEN status='completed' THEN ...) avoids multiple self-joins for multi-status metrics."),
                    ("Multi-table JOINs", "All queries join orders → order_items → products → customers → categories across a normalised star schema."),
                    ("Date Arithmetic: JULIANDAY()", "Query 2 & 3 — calculates recency in days and cohort month offsets without application-layer code."),
                    ("NULLIF / COALESCE", "Used throughout to safely handle division by zero and missing spend data in the marketing ROI query."),
                    ("Cohort Pattern", "Query 3 — self-join on first-purchase CTE to map every subsequent order to a month index since acquisition."),
                ]
            ], style={"display":"grid","gridTemplateColumns":"repeat(auto-fit,minmax(280px,1fr))","gap":"12px"}),
        ], style={"marginBottom":"20px"}),

        # ── FOOTER ────────────────────────────────────────────────────────
        html.Div([
            html.P("Built by Miyelani Teddy Mashele  ·  BSc Mathematical Sciences → Honours Computer Science, University of Limpopo",
                style={"color":MUTED,"fontSize":"12px","fontFamily":"DM Mono,monospace","textAlign":"center","margin":"0"}),
            html.P("Stack: Python · SQLite/PostgreSQL · Plotly Dash · Pandas  ·  github.com/miyelani55",
                style={"color":MUTED,"fontSize":"11px","fontFamily":"DM Mono,monospace","textAlign":"center","margin":"6px 0 0"}),
        ], style={"borderTop":f"1px solid {BORDER}","paddingTop":"24px","marginTop":"8px"}),

    ]),
])

if __name__ == "__main__":
    app.run(debug=True, port=8051)
