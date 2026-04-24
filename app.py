import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

st.set_page_config(page_title="财务财报分析工具", page_icon="📊", layout="wide")

st.title("📊 智能财务财报分析工具")
st.markdown("---")

def get_all_sheets_data(file):
    try:
        xl = pd.ExcelFile(file)
        all_data = {}
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=sheet_name, header=None)
            all_data[sheet_name] = df
        return all_data
    except Exception as e:
        st.error(f"读取Excel失败: {e}")
        return {}

def detect_sheet_type(df):
    first_col = df.iloc[:, 0].astype(str).str.cat(sep=' ')
    second_row = df.iloc[1].astype(str).str.cat(sep=' ') if len(df) > 1 else ''
    
    score = {'balance': 0, 'income': 0, 'cashflow': 0}
    
    balance_keywords = ['资产', '负债', '权益', '流动资产', '流动负债', '所有者权益', '固定资产', '无形资产', '短期借款', '长期借款']
    income_keywords = ['收入', '成本', '利润', '营业利润', '净利润', '毛利率', '营业收入', '营业成本', '销售费用', '管理费用', '财务费用']
    cashflow_keywords = ['现金流量', '经营活动', '投资活动', '筹资活动', '现金流入', '现金流出', '期末现金']
    
    for kw in balance_keywords:
        if kw in first_col or kw in second_row:
            score['balance'] += 1
    
    for kw in income_keywords:
        if kw in first_col or kw in second_row:
            score['income'] += 1
    
    for kw in cashflow_keywords:
        if kw in first_col or kw in second_row:
            score['cashflow'] += 1
    
    max_score = max(score.values())
    if max_score == 0:
        return 'unknown'
    if score['balance'] == max_score:
        return 'balance'
    elif score['income'] == max_score:
        return 'income'
    elif score['cashflow'] == max_score:
        return 'cashflow'
    return 'unknown'

def find_header_row(df):
    for i in range(min(10, len(df))):
        row_str = str(df.iloc[i].astype(str).str.cat(sep=' '))
        if any(kw in row_str for kw in ['资产', '负债', '收入', '利润', '现金流量', '项目']):
            return i
    return 0

def extract_financial_data(df, sheet_type):
    df_clean = df.copy()
    header_row = find_header_row(df_clean)
    df_clean.columns = df_clean.iloc[header_row]
    df_clean = df_clean.iloc[header_row + 1:]
    df_clean = df_clean.reset_index(drop=True)
    
    result = {}
    
    for col in df_clean.columns:
        col_str = str(col).strip()
        if col_str == 'nan' or col_str == '':
            continue
        
        values = []
        for val in df_clean[col]:
            if pd.isna(val):
                continue
            try:
                val_str = str(val).replace(',', '').replace(' ', '').replace('(', '-').replace(')', '')
                val_str = val_str.replace('−', '-')
                num = float(val_str)
                values.append((col_str, num))
            except:
                continue
        
        for name, num in values:
            if sheet_type == 'balance':
                if any(kw in name for kw in ['货币资金', '现金', '存款']):
                    result.setdefault('货币资金', []).append(num)
                elif any(kw in name for kw in ['应收账款', '应收']):
                    result.setdefault('应收账款', []).append(num)
                elif any(kw in name for kw in ['存货']):
                    result.setdefault('存货', []).append(num)
                elif any(kw in name for kw in ['固定资产', '在建工程']):
                    result.setdefault('固定资产', []).append(num)
                elif any(kw in name for kw in ['无形资产', '长期投资']):
                    result.setdefault('无形资产', []).append(num)
                elif any(kw in name for kw in ['资产总计', '流动资产合计', '非流动资产合计']):
                    result.setdefault('资产总计', []).append(num)
                elif any(kw in name for kw in ['短期借款', '应付账款', '应付']):
                    result.setdefault('流动负债', []).append(num)
                elif any(kw in name for kw in ['长期借款', '长期负债']):
                    result.setdefault('长期负债', []).append(num)
                elif any(kw in name for kw in ['负债合计', '流动负债合计', '非流动负债合计']):
                    result.setdefault('负债总计', []).append(num)
                elif any(kw in name for kw in ['实收资本', '资本公积', '盈余公积', '未分配利润', '所有者权益合计', '股东权益']):
                    result.setdefault('所有者权益', []).append(num)
                elif any(kw in name for kw in ['负债和所有者权益', '负债与所有者权益']):
                    result.setdefault('负债加权益', []).append(num)
            
            elif sheet_type == 'income':
                if any(kw in name for kw in ['营业收入', '主营业务收入', '销售收入']):
                    result.setdefault('营业收入', []).append(num)
                elif any(kw in name for kw in ['营业成本', '主营业务成本', '销售成本']):
                    result.setdefault('营业成本', []).append(num)
                elif any(kw in name for kw in ['销售费用', '管理费用', '财务费用', '研发费用', '期间费用']):
                    result.setdefault('期间费用', []).append(num)
                elif any(kw in name for kw in ['毛利润', '毛利']):
                    result.setdefault('毛利润', []).append(num)
                elif any(kw in name for kw in ['营业利润', '利润总额']):
                    result.setdefault('营业利润', []).append(num)
                elif any(kw in name for kw in ['净利润']):
                    result.setdefault('净利润', []).append(num)
            
            elif sheet_type == 'cashflow':
                if any(kw in name for kw in ['销售商品', '提供劳务', '经营活动流入', '经营活动现金流量']):
                    result.setdefault('经营活动流入', []).append(num)
                elif any(kw in name for kw in ['购买商品', '支付税费', '经营活动流出', '支付']):
                    result.setdefault('经营活动流出', []).append(num)
                elif any(kw in name for kw in ['经营活动产生的现金流量', '经营活动净流量']):
                    result.setdefault('经营活动净流量', []).append(num)
                elif any(kw in name for kw in ['投资活动产生的现金流量', '投资活动净流量', '投资收益']):
                    result.setdefault('投资活动净流量', []).append(num)
                elif any(kw in name for kw in ['筹资活动产生的现金流量', '筹资活动净流量', '吸收投资', '借款']):
                    result.setdefault('筹资活动净流量', []).append(num)
                elif any(kw in name for kw in ['期末现金', '现金及现金等价物']):
                    result.setdefault('期末现金', []).append(num)
    
    final_result = {}
    for k, v in result.items():
        if v:
            final_result[k] = max(v) if v else 0
    
    return final_result

def analyze_all_sheets(all_sheets_data):
    results = {}
    summary = {}
    
    for sheet_name, df in all_sheets_data.items():
        sheet_type = detect_sheet_type(df)
        
        if sheet_type != 'unknown':
            data = extract_financial_data(df, sheet_type)
            results[sheet_name] = {
                'type': sheet_type,
                'data': data
            }
            
            type_names = {'balance': '资产负债表', 'income': '利润表', 'cashflow': '现金流量表'}
            summary[sheet_name] = {
                'type': type_names.get(sheet_type, sheet_type),
                'data_count': len(data)
            }
    
    return results, summary

def calculate_metrics(results):
    metrics = {}
    
    balance_data = {}
    income_data = {}
    cashflow_data = {}
    
    for sheet_name, info in results.items():
        if info['type'] == 'balance':
            balance_data.update(info['data'])
        elif info['type'] == 'income':
            income_data.update(info['data'])
        elif info['type'] == 'cashflow':
            cashflow_data.update(info['data'])
    
    if balance_data:
        total_assets = balance_data.get('资产总计', 0)
        total_liabilities = balance_data.get('负债总计', 0)
        total_equity = balance_data.get('所有者权益', 0)
        
        metrics['资产负债率'] = (total_liabilities / total_assets * 100) if total_assets > 0 else 0
        metrics['权益乘数'] = (total_assets / total_equity) if total_equity > 0 else 0
    
    if income_data:
        revenue = income_data.get('营业收入', 0)
        cost = income_data.get('营业成本', 0)
        expenses = income_data.get('期间费用', 0)
        net_profit = income_data.get('净利润', 0)
        
        if revenue > 0:
            metrics['毛利率'] = ((revenue - cost) / revenue) * 100
            metrics['净利率'] = (net_profit / revenue) * 100
        if revenue > 0:
            metrics['成本率'] = (cost / revenue) * 100
            metrics['费用率'] = (expenses / revenue) * 100
    
    if cashflow_data:
        operating_cf = cashflow_data.get('经营活动净流量', 0)
        investing_cf = cashflow_data.get('投资活动净流量', 0)
        financing_cf = cashflow_data.get('筹资活动净流量', 0)
        
        metrics['经营现金流'] = operating_cf
        metrics['投资现金流'] = investing_cf
        metrics['筹资现金流'] = financing_cf
    
    return metrics, balance_data, income_data, cashflow_data

def generate_charts(balance_data, income_data, cashflow_data):
    charts = []
    
    if balance_data:
        assets = {k: v for k, v in balance_data.items() if v > 0 and k not in ['负债总计', '所有者权益', '负债加权益']}
        assets = {k: v for k, v in assets.items() if '负债' not in k and '权益' not in k}
        
        if assets:
            fig = px.pie(
                values=list(assets.values()),
                names=list(assets.keys()),
                title="🏦 资产结构分析",
                hole=0.4
            )
            charts.append(('资产结构', fig))
        
        liab_equity = {}
        if balance_data.get('负债总计', 0) > 0:
            liab_equity['负债'] = balance_data['负债总计']
        if balance_data.get('所有者权益', 0) > 0:
            liab_equity['所有者权益'] = balance_data['所有者权益']
        
        if liab_equity:
            fig = px.bar(
                x=list(liab_equity.keys()),
                y=list(liab_equity.values()),
                title="⚖️ 负债与权益对比",
                color=list(liab_equity.keys()),
                color_discrete_sequence=['#ff6b6b', '#4ecdc4']
            )
            fig.update_layout(yaxis_title="金额")
            charts.append(('负债权益', fig))
    
    if income_data:
        items = {}
        if income_data.get('营业收入', 0) > 0:
            items['营业收入'] = income_data['营业收入']
        if income_data.get('营业成本', 0) > 0:
            items['营业成本'] = income_data['营业成本']
        if income_data.get('毛利润', 0) > 0:
            items['毛利润'] = income_data['毛利润']
        if income_data.get('净利润', 0) > 0:
            items['净利润'] = income_data['净利润']
        
        if items:
            fig = px.bar(
                x=list(items.keys()),
                y=list(items.values()),
                title="💰 收入与利润分析",
                color=list(items.keys()),
                color_discrete_sequence=['#45b7d1', '#ff6b6b', '#96ceb4', '#ffeaa7']
            )
            fig.update_layout(yaxis_title="金额")
            charts.append(('盈利分析', fig))
    
    if cashflow_data:
        cf_items = {}
        if cashflow_data.get('经营活动净流量', 0) != 0:
            cf_items['经营活动'] = cashflow_data['经营活动净流量']
        if cashflow_data.get('投资活动净流量', 0) != 0:
            cf_items['投资活动'] = cashflow_data['投资活动净流量']
        if cashflow_data.get('筹资活动净流量', 0) != 0:
            cf_items['筹资活动'] = cashflow_data['筹资活动净流量']
        
        if cf_items:
            fig = px.bar(
                x=list(cf_items.keys()),
                y=list(cf_items.values()),
                title="💵 现金流量分析",
                color=list(cf_items.keys()),
                color_discrete_sequence=['#00b894', '#e17055', '#0984e3']
            )
            fig.update_layout(yaxis_title="金额")
            charts.append(('现金流', fig))
    
    return charts

st.sidebar.header("📁 文件上传")

uploaded_file = st.sidebar.file_uploader(
    "上传财务报告 (Excel)",
    type=['xlsx', 'xls']
)

if uploaded_file is not None:
    try:
        all_sheets_data = get_all_sheets_data(uploaded_file)
        
        if not all_sheets_data:
            st.error("无法读取Excel文件")
            st.stop()
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📑 工作表列表")
        
        results, summary = analyze_all_sheets(all_sheets_data)
        
        for sheet_name, info in summary.items():
            st.sidebar.success(f"✅ {sheet_name} ({info['type']})")
        
        st.success(f"✅ 文件上传成功！共识别到 {len(results)} 个财务报表")
        
        tab_names = ["📊 数据总览"]
        tab_names.extend(list(results.keys()))
        if len(results) < 3:
            tab_names.append("📈 可视化")
        
        tabs = st.tabs(tab_names)
        
        with tabs[0]:
            st.markdown("### 📊 财务报表总览")
            
            cols = st.columns(3)
            
            balance_count = sum(1 for s in results.values() if s['type'] == 'balance')
            income_count = sum(1 for s in results.values() if s['type'] == 'income')
            cashflow_count = sum(1 for s in results.values() if s['type'] == 'cashflow')
            
            with cols[0]:
                st.metric("资产负债表", balance_count)
            with cols[1]:
                st.metric("利润表", income_count)
            with cols[2]:
                st.metric("现金流量表", cashflow_count)
            
            st.markdown("---")
            
            metrics, balance_data, income_data, cashflow_data = calculate_metrics(results)
            
            st.markdown("### 💡 关键财务指标")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                debt_ratio = metrics.get('资产负债率', 0)
                st.metric("资产负债率", f"{debt_ratio:.2f}%", 
                         delta="较高" if debt_ratio > 60 else "正常",
                         delta_color="inverse" if debt_ratio > 60 else "normal")
            
            with col2:
                gross_margin = metrics.get('毛利率', 0)
                st.metric("毛利率", f"{gross_margin:.2f}%",
                         delta="较高" if gross_margin > 30 else "较低",
                         delta_color="normal" if gross_margin > 30 else "inverse")
            
            with col3:
                net_margin = metrics.get('净利率', 0)
                st.metric("净利率", f"{net_margin:.2f}%")
            
            with col4:
                op_cf = metrics.get('经营现金流', 0)
                st.metric("经营活动现金流", f"{op_cf:,.0f}")
            
            st.markdown("---")
            
            st.markdown("### 📋 各报表数据明细")
            
            for sheet_name, info in results.items():
                with st.expander(f"📄 {sheet_name} ({info['type']})"):
                    type_name = {'balance': '资产负债表', 'income': '利润表', 'cashflow': '现金流量表'}.get(info['type'], info['type'])
                    st.markdown(f"**报表类型:** {type_name}")
                    
                    if info['data']:
                        data_list = [{'项目': k, '金额': v} for k, v in info['data'].items()]
                        st.dataframe(pd.DataFrame(data_list), use_container_width=True)
                    else:
                        st.warning("未能提取到数据，请检查表格格式")
        
        tab_idx = 1
        for sheet_name, info in results.items():
            if tab_idx < len(tabs):
                with tabs[tab_idx]:
                    st.markdown(f"### 📄 {sheet_name} - {info['type']}")
                    
                    type_name = {'balance': '资产负债表', 'income': '利润表', 'cashflow': '现金流量表'}.get(info['type'], info['type'])
                    st.markdown(f"**{type_name}**")
                    
                    if info['data']:
                        data_list = [{'项目': k, '金额': v} for k, v in info['data'].items()]
                        df_display = pd.DataFrame(data_list)
                        
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.dataframe(df_display, use_container_width=True)
                        with col2:
                            total = sum(v for v in info['data'].values() if v > 0)
                            st.metric("合计金额", f"{total:,.2f}")
                    else:
                        st.warning("未能提取到数据")
                
                tab_idx += 1
        
        if len(tabs) > tab_idx:
            with tabs[tab_idx]:
                st.markdown("### 📈 可视化分析")
                
                charts = generate_charts(balance_data, income_data, cashflow_data)
                
                if charts:
                    for chart_name, fig in charts:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("暂无足够数据生成图表")
        
        with st.expander("📥 下载分析报告"):
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                for sheet_name, df in all_sheets_data.items():
                    safe_name = sheet_name[:31]
                    df.to_excel(writer, sheet_name=safe_name, index=False)
                
                metrics_df = pd.DataFrame([metrics])
                metrics_df.to_excel(writer, sheet_name='财务指标', index=False)
            
            st.download_button(
                label="📥 下载完整报告",
                data=buffer.getvalue(),
                file_name="财务分析报告.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    except Exception as e:
        st.error(f"处理文件时出错: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

else:
    st.info("👈 请上传财务报告Excel文件开始分析")
    
    st.markdown("---")
    st.markdown("### 🎯 功能特点")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        ### 📑 多报表识别
        - 自动识别资产负债表
        - 自动识别利润表
        - 自动识别现金流量表
        """)
    with col2:
        st.markdown("""
        ### 🧠 智能提取
        - 自动识别表格类型
        - 提取关键财务数据
        - 计算财务指标
        """)
    with col3:
        st.markdown("""
        ### 📊 可视化分析
        - 资产结构饼图
        - 盈利分析柱状图
        - 现金流对比图
        """)
    
    st.markdown("---")
    st.markdown("### 📝 财务指标说明")
    st.markdown("""
    | 指标 | 说明 |
    |------|------|
    | 资产负债率 | 负债总额/资产总额，越低越稳健 |
    | 毛利率 | (收入-成本)/收入，反映盈利能力 |
    | 净利率 | 净利润/收入，反映最终盈利水平 |
    | 经营活动现金流 | 企业日常经营的现金流动 |
    """)
