import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

st.set_page_config(page_title="财务财报分析工具", page_icon="📊", layout="wide")

st.title("📊 财务财报分析工具")
st.markdown("---")

def detect_financial_items(df):
    financial_keywords = {
        '资产': ['资产', '现金', '存款', '应收账款', '存货', '固定资产'],
        '负债': ['负债', '应付', '借款', '短期借款', '长期借款', '应付账款'],
        '权益': ['权益', '股东', '资本', '利润', '盈余', '未分配利润'],
        '收入': ['收入', '营业收入', '销售收入', '主营业务收入'],
        '成本': ['成本', '营业成本', '销售成本', '主营业务成本'],
        '费用': ['费用', '管理费用', '销售费用', '财务费用', '研发费用'],
        '利润': ['利润', '净利润', '毛利润', '营业利润', '利润总额']
    }
    
    detected = {category: [] for category in financial_keywords}
    numeric_cols = []
    
    for col in df.columns:
        col_str = str(col)
        for category, keywords in financial_keywords.items():
            if any(kw in col_str for kw in keywords):
                detected[category].append(col)
        if '金额' in col_str or '收入' in col_str or '资产' in col_str or '负债' in col_str or '利润' in col_str:
            numeric_cols.append(col)
    
    return detected, numeric_cols

def analyze_financial_data(df, detected_items):
    analysis_results = {}
    
    if detected_items.get('资产') or detected_items.get('负债') or detected_items.get('权益'):
        analysis_results['资产负债表分析'] = analyze_balance_sheet(df, detected_items)
    
    if detected_items.get('收入') and detected_items.get('成本'):
        analysis_results['利润分析'] = analyze_income(df, detected_items)
    
    if detected_items.get('收入'):
        analysis_results['收入趋势分析'] = analyze_revenue_trend(df, detected_items)
    
    if detected_items.get('费用'):
        analysis_results['费用分析'] = analyze_expenses(df, detected_items)
    
    analysis_results['数据概览'] = generate_overview(df)
    
    return analysis_results

def analyze_balance_sheet(df, detected_items):
    result = {}
    
    all_cols = detected_items.get('资产', []) + detected_items.get('负债', []) + detected_items.get('权益', [])
    
    numeric_cols = []
    for col in all_cols:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                numeric_cols.append(col)
            except:
                pass
    
    if numeric_cols:
        result['资产总计'] = sum(df[col].sum() for col in detected_items.get('资产', []) if col in df.columns)
        result['负债总计'] = sum(df[col].sum() for col in detected_items.get('负债', []) if col in df.columns)
        result['权益总计'] = sum(df[col].sum() for col in detected_items.get('权益', []) if col in df.columns)
        
        if result['负债总计'] and result['权益总计']:
            result['资产负债率'] = (result['负债总计'] / (result['负债总计'] + result['权益总计'])) * 100
    
    return result

def analyze_income(df, detected_items):
    result = {}
    
    revenue_cols = detected_items.get('收入', [])
    cost_cols = detected_items.get('成本', [])
    
    total_revenue = 0
    for col in revenue_cols:
        if col in df.columns:
            try:
                total_revenue += pd.to_numeric(df[col], errors='coerce').sum()
            except:
                pass
    
    total_cost = 0
    for col in cost_cols:
        if col in df.columns:
            try:
                total_cost += pd.to_numeric(df[col], errors='coerce').sum()
            except:
                pass
    
    result['总收入'] = total_revenue
    result['总成本'] = total_cost
    
    if total_revenue > 0:
        result['毛利率'] = ((total_revenue - total_cost) / total_revenue) * 100
    
    return result

def analyze_revenue_trend(df, detected_items):
    result = {}
    
    revenue_cols = detected_items.get('收入', [])
    if revenue_cols:
        for col in revenue_cols[:1]:
            if col in df.columns:
                try:
                    values = pd.to_numeric(df[col], errors='coerce').dropna()
                    if len(values) > 1:
                        growth_rate = ((values.iloc[-1] - values.iloc[0]) / values.iloc[0]) * 100
                        result['收入增长率'] = growth_rate
                except:
                    pass
    
    return result

def analyze_expenses(df, detected_items):
    result = {}
    
    expense_cols = detected_items.get('费用', [])
    for col in expense_cols:
        if col in df.columns:
            try:
                result[f'{col}'] = pd.to_numeric(df[col], errors='coerce').sum()
            except:
                pass
    
    return result

def generate_overview(df):
    result = {}
    result['数据行数'] = len(df)
    result['数据列数'] = len(df.columns)
    result['列名列表'] = list(df.columns)
    
    return result

def plot_financial_charts(df, detected_items):
    charts = []
    
    if detected_items.get('资产'):
        asset_cols = [col for col in detected_items['资产'] if col in df.columns]
        if asset_cols:
            asset_data = {}
            for col in asset_cols:
                try:
                    val = pd.to_numeric(df[col], errors='coerce').sum()
                    if val > 0:
                        asset_data[col] = val
                except:
                    pass
            
            if asset_data:
                fig = px.pie(
                    values=list(asset_data.values()),
                    names=list(asset_data.keys()),
                    title="资产结构分析",
                    hole=0.4
                )
                charts.append(("资产结构", fig))
    
    if detected_items.get('负债') and detected_items.get('权益'):
        liability_cols = [col for col in detected_items['负债'] if col in df.columns]
        equity_cols = [col for col in detected_items['权益'] if col in df.columns]
        
        liability_sum = sum(pd.to_numeric(df[col], errors='coerce').sum() for col in liability_cols)
        equity_sum = sum(pd.to_numeric(df[col], errors='coerce').sum() for col in equity_cols)
        
        if liability_sum > 0 and equity_sum > 0:
            fig = px.bar(
                x=['负债', '权益'],
                y=[liability_sum, equity_sum],
                title="负债与权益对比",
                color=['负债', '权益'],
                color_discrete_sequence=['#ff6b6b', '#4ecdc4']
            )
            charts.append(("负债权益对比", fig))
    
    if detected_items.get('收入') and detected_items.get('成本'):
        revenue_cols = [col for col in detected_items['收入'] if col in df.columns]
        cost_cols = [col for col in detected_items['成本'] if col in df.columns]
        
        revenue_sum = sum(pd.to_numeric(df[col], errors='coerce').sum() for col in revenue_cols)
        cost_sum = sum(pd.to_numeric(df[col], errors='coerce').sum() for col in cost_cols)
        
        if revenue_sum > 0 and cost_sum > 0:
            profit = revenue_sum - cost_sum
            fig = px.bar(
                x=['收入', '成本', '利润'],
                y=[revenue_sum, cost_sum, profit],
                title="收入、成本与利润分析",
                color=['收入', '成本', '利润'],
                color_discrete_sequence=['#45b7d1', '#ff6b6b', '#96ceb4']
            )
            charts.append(("盈利分析", fig))
    
    return charts

with st.sidebar:
    st.header("📁 文件上传")
    uploaded_file = st.file_uploader(
        "上传财务报告 (Excel/CSV)",
        type=['xlsx', 'xls', 'csv']
    )
    
    st.markdown("---")
    st.header("ℹ️ 使用说明")
    st.markdown("""
    1. 上传 Excel 或 CSV 格式的财务报告
    2. 系统自动识别财务数据类别
    3. 查看多维度分析结果
    4. 通过图表可视化数据
    """)

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ 文件上传成功！共 {len(df)} 行数据")
        
        detected_items, numeric_cols = detect_financial_items(df)
        
        st.markdown("### 📋 数据预览")
        st.dataframe(df.head(10), use_container_width=True)
        
        with st.expander("🔍 查看检测到的财务项目"):
            for category, items in detected_items.items():
                if items:
                    st.write(f"**{category}:** {', '.join(items)}")
        
        analysis_results = analyze_financial_data(df, detected_items)
        
        st.markdown("---")
        st.markdown("### 📈 财务分析报告")
        
        tab1, tab2, tab3 = st.tabs(["📊 数据概览", "📉 详细分析", "📈 可视化图表"])
        
        with tab1:
            overview = analysis_results.get('数据概览', {})
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("数据行数", overview.get('数据行数', 0))
            with col2:
                st.metric("数据列数", overview.get('数据列数', 0))
            with col3:
                st.metric("识别项目数", len(set(sum(detected_items.values(), []))))
            
            st.subheader("数据列详情")
            cols_df = pd.DataFrame({'列名': overview.get('列名列表', [])})
            st.dataframe(cols_df, use_container_width=True)
        
        with tab2:
            for analysis_name, results in analysis_results.items():
                if analysis_name != '数据概览':
                    st.markdown(f"#### {analysis_name}")
                    if results:
                        cols = st.columns(min(len(results), 3))
                        for idx, (key, value) in enumerate(results.items()):
                            if isinstance(value, (int, float)) and not isinstance(value, bool):
                                with cols[idx % 3]:
                                    st.metric(key, f"{value:,.2f}")
                            elif key != '列名列表':
                                with cols[idx % 3]:
                                    st.metric(key, value)
                    st.markdown("---")
        
        with tab3:
            charts = plot_financial_charts(df, detected_items)
            if charts:
                for chart_name, fig in charts:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暂无足够的财务数据用于生成图表，请确保数据包含资产、负债、收入、成本等项目")
        
        st.markdown("---")
        with st.expander("📥 下载分析结果"):
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='原始数据', index=False)
                
                summary_data = []
                for analysis_name, results in analysis_results.items():
                    if analysis_name != '数据概览':
                        for key, value in results.items():
                            summary_data.append({'分析项目': key, '数值': value})
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='分析结果', index=False)
            
            st.download_button(
                label="下载 Excel 报告",
                data=buffer.getvalue(),
                file_name="财务分析报告.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    except Exception as e:
        st.error(f"❌ 处理文件时出错: {str(e)}")
        st.info("请确保上传的文件格式正确，且包含有效的财务数据")

else:
    st.info("👈 请在左侧上传财务报告文件开始分析")
    
    st.markdown("---")
    st.markdown("### 🎯 功能特点")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        ### 📤 智能上传
        - 支持 Excel 和 CSV 格式
        - 自动识别财务数据
        - 快速解析多种报表结构
        """)
    with col2:
        st.markdown("""
        ### 🧠 智能分析
        - 自动识别资产、负债、权益
        - 计算财务指标和比率
        - 多维度深度分析
        """)
    with col3:
        st.markdown("""
        ### 📊 可视化展示
        - 交互式图表
        - 结构分析饼图
        - 对比分析柱状图
        """)
