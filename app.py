import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

st.set_page_config(page_title="财务财报分析工具", page_icon="📊", layout="wide")

st.title("📊 智能财务财报分析工具")
st.markdown("---")

def get_excel_sheets(file):
    try:
        xl = pd.ExcelFile(file)
        return xl.sheet_names
    except:
        return ["Sheet1"]

def parse_financial_value(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).replace(',', '').replace(' ', '')
    try:
        return float(val_str)
    except:
        return 0.0

def detect_financial_data(df):
    results = {
        'assets': [],
        'liabilities': [],
        'equity': [],
        'revenue': [],
        'cost': [],
        'expense': [],
        'profit': []
    }
    
    all_keywords = {
        'assets': ['资产', '现金', '货币资金', '应收账款', '应收票据', '存货', '固定资产', '无形资产', '长期投资', '流动资产', '非流动资产', '在建工程'],
        'liabilities': ['负债', '应付', '借款', '短期借款', '长期借款', '应付账款', '应付票据', '应付职工薪酬', '应交税费', '流动负债', '非流动负债', '长期应付款'],
        'equity': ['权益', '股东', '资本', '利润', '盈余', '未分配利润', '实收资本', '资本公积', '盈余公积', '所有者权益', '留存收益'],
        'revenue': ['收入', '营业收入', '销售收入', '主营业务收入', '其他业务收入', '营业总收', '本期发生', '本年累计'],
        'cost': ['成本', '营业成本', '销售成本', '主营业务成本', '其他业务成本', '制造费用'],
        'expense': ['费用', '管理费用', '销售费用', '财务费用', '研发费用', '营业费用', '期间费用'],
        'profit': ['利润', '净利润', '毛利润', '营业利润', '利润总额', '息税前利润', 'EBIT']
    }
    
    for col in df.columns:
        col_str = str(col).strip()
        
        for category, keywords in all_keywords.items():
            if any(kw in col_str for kw in keywords):
                if col not in results[category]:
                    results[category].append(col)
    
    return results

def analyze_balance_sheet(df, detected):
    result = {}
    
    asset_cols = [col for col in detected['assets'] if col in df.columns]
    liab_cols = [col for col in detected['liabilities'] if col in df.columns]
    equity_cols = [col for col in detected['equity'] if col in df.columns]
    
    total_assets = 0
    for col in asset_cols:
        values = df[col].apply(parse_financial_value)
        total_assets += values.sum()
    
    total_liabilities = 0
    for col in liab_cols:
        values = df[col].apply(parse_financial_value)
        total_liabilities += values.sum()
    
    total_equity = 0
    for col in equity_cols:
        values = df[col].apply(parse_financial_value)
        total_equity += values.sum()
    
    result['资产总计'] = total_assets
    result['负债总计'] = total_liabilities
    result['所有者权益总计'] = total_equity
    
    if total_assets > 0:
        result['资产负债率'] = (total_liabilities / total_assets) * 100
    if total_liabilities + total_equity > 0:
        result['负债占总计比例'] = (total_liabilities / (total_liabilities + total_equity)) * 100
    
    return result, {
        'assets': {col: df[col].apply(parse_financial_value).sum() for col in asset_cols},
        'liabilities': {col: df[col].apply(parse_financial_value).sum() for col in liab_cols},
        'equity': {col: df[col].apply(parse_financial_value).sum() for col in equity_cols}
    }

def analyze_income(df, detected):
    result = {}
    
    revenue_cols = [col for col in detected['revenue'] if col in df.columns]
    cost_cols = [col for col in detected['cost'] if col in df.columns]
    expense_cols = [col for col in detected['expense'] if col in df.columns]
    profit_cols = [col for col in detected['profit'] if col in df.columns]
    
    total_revenue = sum(df[col].apply(parse_financial_value).sum() for col in revenue_cols)
    total_cost = sum(df[col].apply(parse_financial_value).sum() for col in cost_cols)
    total_expense = sum(df[col].apply(parse_financial_value).sum() for col in expense_cols)
    total_profit = sum(df[col].apply(parse_financial_value).sum() for col in profit_cols)
    
    result['营业收入'] = total_revenue
    result['营业成本'] = total_cost
    result['期间费用'] = total_expense
    
    if total_revenue > 0:
        result['毛利率'] = ((total_revenue - total_cost) / total_revenue) * 100
        result['成本率'] = (total_cost / total_revenue) * 100
    
    if total_revenue > 0:
        result['费用率'] = (total_expense / total_revenue) * 100
    
    gross_profit = total_revenue - total_cost
    result['毛利润'] = gross_profit
    net_profit = gross_profit - total_expense
    result['净利润'] = net_profit
    
    if total_revenue > 0:
        result['净利率'] = (net_profit / total_revenue) * 100
    
    return result, {
        'revenue': {col: df[col].apply(parse_financial_value).sum() for col in revenue_cols},
        'cost': {col: df[col].apply(parse_financial_value).sum() for col in cost_cols},
        'expense': {col: df[col].apply(parse_financial_value).sum() for col in expense_cols}
    }

def analyze_trends(df, detected):
    result = {}
    
    for category in ['revenue', 'cost', 'expense', 'profit']:
        cols = [col for col in detected[category] if col in df.columns]
        if len(cols) >= 2:
            values = [df[col].apply(parse_financial_value).sum() for col in cols]
            if values[0] != 0:
                change = ((values[-1] - values[0]) / abs(values[0])) * 100
                result[f'{category.capitalize()}变化率'] = change
    
    return result

def generate_insights(balance_data, income_data, balance_details, income_details):
    insights = []
    
    if balance_data.get('资产负债率'):
        rate = balance_data['资产负债率']
        if rate > 70:
            insights.append(f"⚠️ 资产负债率为 {rate:.1f}%，处于较高水平，建议关注债务风险")
        elif rate < 30:
            insights.append(f"✅ 资产负债率为 {rate:.1f}%，财务结构较为稳健")
    
    if income_data.get('毛利率'):
        gross_margin = income_data['毛利率']
        if gross_margin > 40:
            insights.append(f"✅ 毛利率为 {gross_margin:.1f}%，盈利能力较强")
        elif gross_margin < 10:
            insights.append(f"⚠️ 毛利率为 {gross_margin:.1f}%，盈利能力较弱，需关注成本控制")
    
    if income_data.get('净利率'):
        net_margin = income_data['净利率']
        if net_margin > 15:
            insights.append(f"✅ 净利率为 {net_margin:.1f}%，经营效率较高")
        elif net_margin < 5:
            insights.append(f"⚠️ 净利率为 {net_margin:.1f}%，利润空间有限")
    
    if income_data.get('费用率'):
        expense_rate = income_data['费用率']
        if expense_rate > 30:
            insights.append(f"⚠️ 费用率为 {expense_rate:.1f}%，费用支出较高")
    
    return insights

def plot_balance_sheet(balance_details):
    charts = []
    
    assets = {k: v for k, v in balance_details['assets'].items() if v > 0}
    if assets:
        fig = px.pie(
            values=list(assets.values()),
            names=list(assets.keys()),
            title="🏦 资产结构分析",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Blues
        )
        charts.append(fig)
    
    liab_equity = {}
    liab_sum = sum(v for v in balance_details['liabilities'].values() if v > 0)
    equity_sum = sum(v for v in balance_details['equity'].values() if v > 0)
    if liab_sum > 0:
        liab_equity['负债'] = liab_sum
    if equity_sum > 0:
        liab_equity['所有者权益'] = equity_sum
    
    if liab_equity:
        fig = px.bar(
            x=list(liab_equity.keys()),
            y=list(liab_equity.values()),
            title="⚖️ 负债与权益对比",
            color=list(liab_equity.keys()),
            color_discrete_sequence=['#ff6b6b', '#4ecdc4']
        )
        fig.update_layout(yaxis_title="金额")
        charts.append(fig)
    
    return charts

def plot_income_statement(income_details):
    charts = []
    
    revenue = {k: v for k, v in income_details['revenue'].items() if v > 0}
    if revenue:
        fig = px.bar(
            x=list(revenue.keys()),
            y=list(revenue.values()),
            title="💰 收入构成分析",
            color=list(revenue.keys()),
            color_discrete_sequence=['#45b7d1']
        )
        fig.update_layout(yaxis_title="金额")
        charts.append(fig)
    
    cost_expense = {}
    for k, v in income_details['cost'].items():
        if v > 0:
            cost_expense[f'成本-{k[:10]}'] = v
    for k, v in income_details['expense'].items():
        if v > 0:
            cost_expense[f'费用-{k[:10]}'] = v
    
    if cost_expense:
        fig = px.bar(
            x=list(cost_expense.keys()),
            y=list(cost_expense.values()),
            title="📉 成本与费用分析",
            color=list(cost_expense.keys()),
            color_discrete_sequence=['#ff6b6b', '#ffa502']
        )
        fig.update_layout(yaxis_title="金额")
        charts.append(fig)
    
    all_items = {}
    all_items.update({k: v for k, v in income_details['revenue'].items() if v > 0})
    all_items.update({k: -v for k, v in income_details['cost'].items() if v > 0})
    all_items.update({k: -v for k, v in income_details['expense'].items() if v > 0})
    
    if all_items and len(all_items) >= 2:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=list(all_items.keys()),
            y=list(all_items.values()),
            marker_color=['#45b7d1' if v > 0 else '#ff6b6b' for v in all_items.values()],
            name='金额'
        ))
        fig.update_layout(title="📊 收入成本费用对比", yaxis_title="金额")
        charts.append(fig)
    
    return charts

st.sidebar.header("📁 文件上传")

uploaded_file = st.sidebar.file_uploader(
    "上传财务报告 (Excel/CSV)",
    type=['xlsx', 'xls', 'csv']
)

if 'df' not in st.session_state:
    st.session_state.df = None
    st.session_state.detected = None

if uploaded_file is not None:
    try:
        sheets = get_excel_sheets(uploaded_file)
        
        if len(sheets) > 1:
            selected_sheet = st.sidebar.selectbox("选择工作表", sheets)
        else:
            selected_sheet = sheets[0]
        
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
        
        st.session_state.df = df
        detected = detect_financial_data(df)
        st.session_state.detected = detected
        
        st.success(f"✅ 文件上传成功！当前工作表: {selected_sheet}，共 {len(df)} 行数据")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### 📋 数据预览")
            st.dataframe(df.head(15), use_container_width=True)
        with col2:
            st.markdown("### 🔍 识别结果")
            total_detected = sum(len(v) for v in detected.values())
            st.metric("识别财务项目", total_detected)
            
            with st.expander("查看详情"):
                for category, cols in detected.items():
                    if cols:
                        st.write(f"**{category}:** {len(cols)} 项")
        
        balance_result, balance_details = analyze_balance_sheet(df, detected)
        income_result, income_details = analyze_income(df, detected)
        trend_result = analyze_trends(df, detected)
        insights = generate_insights(balance_result, income_result, balance_details, income_details)
        
        st.markdown("---")
        
        if insights:
            st.markdown("### � 智能分析结论")
            for insight in insights:
                st.markdown(f"> {insight}")
            st.markdown("---")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📊 资产负债表", "� 利润分析", "📈 趋势分析", "📉 可视化图表"])
        
        with tab1:
            st.markdown("### 🏦 资产负债表分析")
            if balance_result:
                cols = st.columns(4)
                metrics = ['资产总计', '负债总计', '所有者权益总计', '资产负债率']
                for idx, metric in enumerate(metrics):
                    if metric in balance_result:
                        with cols[idx % 4]:
                            if '率' in metric:
                                st.metric(metric, f"{balance_result[metric]:.2f}%")
                            else:
                                st.metric(metric, f"{balance_result[metric]:,.2f}")
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### 资产明细")
                    assets_data = [{'项目': k, '金额': v} for k, v in balance_details['assets'].items() if v > 0]
                    if assets_data:
                        st.dataframe(pd.DataFrame(assets_data), use_container_width=True)
                
                with col2:
                    st.markdown("#### 负债与权益明细")
                    liab_data = [{'项目': k, '金额': v} for k, v in balance_details['liabilities'].items() if v > 0]
                    equity_data = [{'项目': k, '金额': v} for k, v in balance_details['equity'].items() if v > 0]
                    all_data = liab_data + equity_data
                    if all_data:
                        st.dataframe(pd.DataFrame(all_data), use_container_width=True)
            else:
                st.warning("未识别到资产负债表数据，请检查数据格式")
        
        with tab2:
            st.markdown("### 💰 利润表分析")
            if income_result:
                cols = st.columns(4)
                metrics = ['营业收入', '营业成本', '毛利润', '净利润']
                for idx, metric in enumerate(metrics):
                    if metric in income_result:
                        with cols[idx % 4]:
                            if '率' in metric:
                                st.metric(metric, f"{income_result[metric]:.2f}%")
                            else:
                                st.metric(metric, f"{income_result[metric]:,.2f}")
                
                st.markdown("---")
                
                cols = st.columns(4)
                metrics = ['毛利率', '成本率', '费用率', '净利率']
                for idx, metric in enumerate(metrics):
                    if metric in income_result:
                        with cols[idx % 4]:
                            st.metric(metric, f"{income_result[metric]:.2f}%")
            else:
                st.warning("未识别到利润表数据，请检查数据格式")
        
        with tab3:
            st.markdown("### 📈 趋势变化分析")
            if trend_result:
                cols = st.columns(3)
                for idx, (metric, value) in enumerate(trend_result.items()):
                    with cols[idx % 3]:
                        trend_icon = "📈" if value > 0 else "📉"
                        st.metric(f"{trend_icon} {metric}", f"{value:+.2f}%")
            else:
                st.info("数据行数不足，无法进行趋势分析")
        
        with tab4:
            st.markdown("### 📉 可视化图表")
            
            balance_charts = plot_balance_sheet(balance_details)
            for fig in balance_charts:
                st.plotly_chart(fig, use_container_width=True)
            
            income_charts = plot_income_statement(income_details)
            for fig in income_charts:
                st.plotly_chart(fig, use_container_width=True)
            
            if not balance_charts and not income_charts:
                st.info("暂无足够的财务数据用于生成图表")
        
        st.markdown("---")
        
        with st.expander("📥 下载完整分析报告"):
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='原始数据', index=False)
                
                summary_data = []
                for k, v in balance_result.items():
                    if isinstance(v, (int, float)):
                        summary_data.append({'分析项目': k, '数值': v, '类别': '资产负债表'})
                for k, v in income_result.items():
                    if isinstance(v, (int, float)):
                        summary_data.append({'分析项目': k, '数值': v, '类别': '利润表'})
                
                if summary_data:
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='分析结果', index=False)
            
            st.download_button(
                label="📥 下载 Excel 分析报告",
                data=buffer.getvalue(),
                file_name="财务分析报告.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    except Exception as e:
        st.error(f"❌ 处理文件时出错: {str(e)}")
        st.info("请确保上传的 Excel 文件格式正确")

else:
    st.info("👈 请在左侧上传财务报告文件开始分析")
    
    st.markdown("---")
    st.markdown("### 🎯 功能特点")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        ### 📤 智能上传
        - 支持多 Sheet Excel
        - 支持 CSV 格式
        - 自动识别数据
        """)
    with col2:
        st.markdown("""
        ### 🧠 智能分析
        - 自动识别资产/负债
        - 收入成本费用分析
        - 智能结论建议
        """)
    with col3:
        st.markdown("""
        ### 📊 可视化
        - 资产结构饼图
        - 负债权益对比
        - 收入成本分析
        """)
    with col4:
        st.markdown("""
        ### 📈 趋势分析
        - 同比变化分析
        - 多种财务比率
        - 导出分析报告
        """)
    
    st.markdown("---")
    st.markdown("### 📝 支持的财务数据格式")
    st.markdown("""
    | 数据类型 | 识别关键词 |
    |----------|------------|
    | 资产 | 现金、应收账款、存货、固定资产 |
    | 负债 | 短期借款、应付账款、长期借款 |
    | 权益 | 资本公积、盈余公积、未分配利润 |
    | 收入 | 营业收入、销售收入、主营业务收入 |
    | 成本 | 营业成本、制造费用 |
    | 费用 | 管理费用、销售费用、财务费用 |
    | 利润 | 净利润、毛利润、营业利润 |
    """)
