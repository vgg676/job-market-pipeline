# app.py —— 运行：streamlit run app.py，Streamlit 仪表盘
import streamlit as st
import pandas as pd
from collections import Counter
from config import STRUCTURED_JOBS_CSV, CANDIDATES_CSV, APPLICATIONS_CSV

st.set_page_config(page_title="招聘智能分析", layout="wide")
st.title("招聘信息智能分析仪表盘")

# 加载
jobs = pd.read_csv(STRUCTURED_JOBS_CSV)
candidates = pd.read_csv(CANDIDATES_CSV)
applications = pd.read_csv(APPLICATIONS_CSV)

# 侧边栏
st.sidebar.header("筛选条件")
category = st.sidebar.multiselect("岗位类别", jobs["job_category"].dropna().unique())
city = st.sidebar.multiselect("城市", jobs["city"].dropna().unique())
company_size = st.sidebar.multiselect("公司规模", jobs["company_size"].dropna().unique())
status_filter = st.sidebar.multiselect("应聘状态", applications["status"].dropna().unique())

if category:
    jobs = jobs[jobs["job_category"].isin(category)]
if city:
    jobs = jobs[jobs["city"].isin(city)]
if company_size:
    jobs = jobs[jobs["company_size"].isin(company_size)]

# 指标卡
c1, c2, c3, c4 = st.columns(4)
c1.metric("岗位数", len(jobs))
c2.metric("求职者数", len(candidates))
c3.metric("应聘记录数", len(applications))
c4.metric("匹配岗位数", int(applications["is_matched"].sum()) if "is_matched" in applications else "N/A")

# 技能统计
st.subheader("Top 技术技能（合并后）")
counter = Counter()
for s in jobs["skills_merged"].fillna(""):
    counter.update(set(x.strip() for x in str(s).split(",") if x.strip()))
top = counter.most_common(15)
if top:
    st.bar_chart(pd.DataFrame(top, columns=["技能", "岗位数"]).set_index("技能"))

# 多维
col1, col2 = st.columns(2)
with col1:
    st.subheader("岗位类别分布")
    st.bar_chart(jobs["job_category"].value_counts())
with col2:
    st.subheader("城市分布")
    st.bar_chart(jobs["city"].value_counts())

col3, col4 = st.columns(2)
with col3:
    st.subheader("学历要求分布")
    st.bar_chart(jobs["education"].value_counts())
with col4:
    st.subheader("应聘状态分布")
    st.bar_chart(applications["status"].value_counts())

# 匹配度
if "total_match_score" in applications.columns:
    st.subheader("匹配度评分分布")
    st.bar_chart(applications["total_match_score"].value_counts(bins=10).sort_index())

# 原始数据
with st.expander("查看结构化岗位数据"):
    st.dataframe(jobs)