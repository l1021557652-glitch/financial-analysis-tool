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
    text = df.astype(str).values.flatten()
    text_str = ' '.join(text)
    
    score = {'balance': 0, 'income': 0, 'cashflow': 0}
    
    balance_keywords = ['资产', '负债', '权益', '流动资产', '流动负债', '所有者权益', '固定资产', '无形资产', '短期借款', '长期借款', '货币资金', '应收账款', '存货']
    income_keywords = ['收入', '成本', '利润', '营业利润', '净利润', '毛利率', '营业收入', '营业成本', '销售费用', '管理费用', '财务费用', '主营业务']
    cashflow_keywords = ['现金流量', '经营活动', '投资活动', '筹资活动', '现金流入', '现金流出', '期末现金', '现金及现金等价物']
    
    for kw in balance_keywords:
        if kw in text_str:
            score['balance'] += 1
    
    for kw in income_keywords:
        if kw in text_str:
            score['income'] += 1
    
    for kw in cashflow_keywords:
        if kw in text_str:
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

def parse_number(val):
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    if val_str == '' or val_str.lower() == 'nan':
        return None
    val_str = val_str.replace(',', '').replace(' ', '')
    val_str = val_str.replace('(', '-').replace(')', '')
    val_str = val_str.replace('−', '-').replace('—', '-').replace('–', '-')
    try:
        return float(val_str)
    except:
        return None

def extract_financial_data(df, sheet_type):
    result = {}
    
    balance_mapping = {
        '货币资金': ['货币资金', '现金', '银行存款', '其他货币资金'],
        '应收账款': ['应收账款', '应收款项', '应收款'],
        '存货': ['存货', '库存商品', '原材料'],
        '固定资产': ['固定资产', '累计折旧', '在建工程'],
        '无形资产': ['无形资产', '土地使用权', '专利权'],
        '资产总计': ['资产总计', '资产合计', '流动资产合计', '非流动资产合计'],
        '短期借款': ['短期借款', '短期负债'],
        '应付账款': ['应付账款', '应付款项', '应付款'],
        '流动负债合计': ['流动负债合计', '流动负债'],
        '长期借款': ['长期借款', '长期负债'],
        '负债合计': ['负债合计', '负债总计', '负债总计'],
        '实收资本': ['实收资本', '股本', '注册资本'],
        '资本公积': ['资本公积', '资本溢价'],
        '盈余公积': ['盈余公积', '法定盈余公积'],
        '未分配利润': ['未分配利润', '未分配利润(损失)'],
        '所有者权益合计': ['所有者权益合计', '股东权益合计', '权益合计']
    }
    
    income_mapping = {
        '营业收入': ['营业收入', '主营业务收入', '销售收入', '营业总收入', '本期发生额'],
        '营业成本': ['营业成本', '主营业务成本', '销售成本', '营业成本(损失)'],
        '毛利润': ['毛利润', '毛利'],
        '销售费用': ['销售费用', '营业费用'],
        '管理费用': ['管理费用'],
        '财务费用': ['财务费用'],
        '研发费用': ['研发费用', '研究与开发费用'],
        '营业利润': ['营业利润', '经营利润'],
        '利润总额': ['利润总额', '税前利润'],
        '净利润': ['净利润', '净利润', '本期净利润', '本年累计净利润']
    }
    
    cashflow_mapping = {
        '销售商品提供劳务': ['销售商品提供劳务', '销售商品、提供劳务收到的现金'],
        '经营活动流入': ['经营活动流入', '经营活动现金流入小计'],
        '经营活动流出': ['经营活动流出', '经营活动现金流出小计'],
        '经营活动净流量': ['经营活动产生的现金流量净额', '经营活动净流量', '经营活动现金流量净额'],
        '投资活动净流量': ['投资活动产生的现金流量净额', '投资活动净流量', '投资活动现金流量净额'],
        '筹资活动净流量': ['筹资活动产生的现金流量净额', '筹资活动净流量', '筹资活动现金流量净额'],
        '期末现金': ['期末现金及现金等价物余额', '期末现金', '现金及现金等价物净增加额']
    }
    
    mapping = {'balance': balance_mapping, 'income': income_mapping, 'cashflow': cashflow_mapping}
    
    for row_idx in range(len(df)):
        row_text = ''
        row_values = []
        
        for col_idx in range(min(5, len(df.columns))):
            val = df.iloc[row_idx, col_idx]
            val_str = str(val) if pd.notna(val) else ''
            row_text += val_str + ' '
            
            num = parse_number(val)
            if num is not None:
                row_values.append((col_idx, num))
        
        row_text = row_text.strip().lower()
        
        if not row_values:
            continue
        
        target_mapping = mapping.get(sheet_type, {})
        
        for key, keywords in target_mapping.items():
            if any(kw in row_text for kw in keywords):
                if key in result:
                    result[key] = max(result[key], max(v[1] for v in row_values))
                else:
                    result[key] = max(v[1] for v in row_values)
    
    if not result:
        for row_idx in range(len(df)):
            row_text = ''
            row_values = []
            
            for col_idx in range(len(df.columns)):
                val = df.iloc[row_idx, col_idx]
                num = parse_number(val)
                if num is not None:
                    first_col_val = df.iloc[row_idx, 0]
                    if pd.notna(first_col_val):
                        row_values.append((str(first_col_val).strip(), num))
            
            if row_values:
                for name, num in row_values:
                    name_lower = str(name).lower()
                    if any(kw in name_lower for kw in ['资产', '负债', '权益', '收入', '成本', '利润', '现金']):
                        if name not in result or abs(num) > abs(result.get(name, 0)):
                            result[name] = num
    
    return result

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
    
    total_assets = balance_data.get('资产总计', 0)
    if total_assets == 0:
        for k, v in balance_data.items():
            if '资产' in k and '合计' in k:
                total_assets = v
                break
    
    total_liabilities = balance_data.get('负债合计', 0)
    if total_liabilities == 0:
        for k, v in balance_data.items():
            if '负债' in k and '合计' in k:
                total_liabilities = v
                break
    
    total_equity = balance_data.get('所有者权益合计', 0)
    if total_equity == 0:
        for k, v in balance_data.items():
            if ('权益' in k or '股东' in k) and '合计' in k:
                total_equity = v
                break
    
    if total_assets > 0:
        metrics['资产负债率'] = (total_liabilities / total_assets) * 100
    
    revenue = income_data.get('营业收入', 0)
    if revenue == 0:
        for k, v in income_data.items():
            if '收入' in k and '合计' not in k:
                revenue = v
                break
    
    cost = income_data.get('营业成本', 0)
    if cost == 0:
        for k, v in income_data.items():
            if '成本' in k and '合计' not in k:
                cost = v
                break
    
    expenses = income_data.get('销售费用', 0) + income_data.get('管理费用', 0) + income_data.get('财务费用', 0)
    
    net_profit = income_data.get('净利润', 0)
    if net_profit == 0:
        for k, v in income_data.items():
            if '净利润' in k:
                net_profit = v
                break
    
    if revenue > 0:
        metrics['毛利率'] = ((revenue - cost) / revenue) * 100
        metrics['净利率'] = (net_profit / revenue) * 100
    
    if cashflow_data:
        operating_cf = cashflow_data.get('经营活动净流量', 0)
        if operating_cf == 0:
            for k, v in cashflow_data.items():
                if '经营' in k and '净额' in k:
                    operating_cf = v
                    break
        metrics['经营现金流'] = operating_cf
    
    return metrics, balance_data, income_data, cashflow_data

def generate_charts(balance_data, income_data, cashflow_data):
    charts = []
    
    if balance_data:
        assets = {}
        for k, v in balance_data.items():
            if v > 0 and '资产' in k and '合计' not in k and '负债' not in k and '权益' not in k:
                assets[k] = v
        
        if assets:
            fig = px.pie(
                values=list(assets.values()),
                names=list(assets.keys()),
                title="🏦 资产结构分析",
                hole=0.4
            )
            charts.append(('资产结构', fig))
        
        liab = balance_data.get('负债合计', 0)
        equity = balance_data.get('所有者权益合计', 0)
        
        if liab > 0 or equity > 0:
            fig = px.bar(
                x=['负债', '所有者权益'],
                y=[liab, equity],
                title="⚖️ 负债与权益对比",
                color=['负债', '所有者权益'],
                color_discrete_sequence=['#ff6b6b', '#4ecdc4']
            )
            fig.update_layout(yaxis_title="金额")
            charts.append(('负债权益', fig))
    
    if income_data:
        items = {}
        for k, v in income_data.items():
            if v > 0:
                items[k] = v
        
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
        for k, v in cashflow_data.items():
            if v != 0:
                cf_items[k] = v
        
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
        
        if not results:
            st.warning("未能识别财务报表，请检查Excel文件格式")
            
            st.markdown("### 📋 原始数据预览")
            for sheet_name, df in all_sheets_data.items():
                with st.expander(f"📄 {sheet_name}"):
                    st.dataframe(df.head(20), use_container_width=True)
            st.stop()
        
        st.success(f"✅ 文件上传成功！共识别到 {len(results)} 个财务报表")
        
        tab_names = ["📊 数据总览"]
        tab_names.extend(list(results.keys()))
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
                if debt_ratio > 0:
                    st.metric("资产负债率", f"{debt_ratio:.2f}%", 
                             delta="较高" if debt_ratio > 60 else "正常",
                             delta_color="inverse" if debt_ratio > 60 else "normal")
                else:
                    st.metric("资产负债率", "N/A")
            
            with col2:
                gross_margin = metrics.get('毛利率', 0)
                if gross_margin > 0:
                    st.metric("毛利率", f"{gross_margin:.2f}%")
                else:
                    st.metric("毛利率", "N/A")
            
            with col3:
                net_margin = metrics.get('净利率', 0)
                if net_margin > 0:
                    st.metric("净利率", f"{net_margin:.2f}%")
                else:
                    st.metric("净利率", "N/A")
            
            with col4:
                op_cf = metrics.get('经营现金流', 0)
                st.metric("经营活动现金流", f"{op_cf:,.0f}" if op_cf != 0 else "N/A")
            
            st.markdown("---")
            
            st.markdown("### 📋 各报表提取数据")
            
            for sheet_name, info in results.items():
                type_name = {'balance': '资产负债表', 'income': '利润表', 'cashflow': '现金流量表'}.get(info['type'], info['type'])
                st.markdown(f"#### 📄 {sheet_name} ({type_name})")
                
                if info['data']:
                    data_list = [{'项目': k, '金额': v} for k, v in info['data'].items()]
                    df_display = pd.DataFrame(data_list)
                    st.dataframe(df_display, use_container_width=True)
                else:
                    st.warning("未能提取到数据")
                
                st.markdown("---")
        
        tab_idx = 1
        for sheet_name, info in results.items():
            if tab_idx < len(tabs):
                with tabs[tab_idx]:
                    type_name = {'balance': '资产负债表', 'income': '利润表', 'cashflow': '现金流量表'}.get(info['type'], info['type'])
                    st.markdown(f"### 📄 {sheet_name} - {type_name}")
                    
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
        
        if tab_idx < len(tabs):
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
                
                all_extracted = {}
                for sheet_name, info in results.items():
                    all_extracted.update(info['data'])
                if all_extracted:
                    extracted_df = pd.DataFrame([{'项目': k, '金额': v} for k, v in all_extracted.items()])
                    extracted_df.to_excel(writer, sheet_name='提取数据', index=False)
            
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
