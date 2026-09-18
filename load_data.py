# load_data.py —— 加载三表数据、清洗文本并生成 combined_text
import re
import pandas as pd
from html.parser import HTMLParser
from config import (JOBS_CSV, CANDIDATES_CSV, APPLICATIONS_CSV,
                    RAW_JOBS_CSV)
class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return "".join(self.fed)


def strip_html(html_text):
    s = MLStripper()
    s.feed(str(html_text))
    return s.get_data()


def clean_text(text):
    if pd.isna(text):
        return ""
    text = strip_html(str(text))
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\x00-\x1f\x7f]", "", text)
    return text.strip()


def build_combined_text(row) -> str:
    """把岗位描述相关的非结构化文本列拼成一段供LLM阅读"""
    parts = [
        f"岗位名称：{row['job_title']}",
        f"岗位类别：{row['job_category']}",
        f"公司：{row['company_name']}，规模：{row['company_size']}",
        f"城市：{row['city']}，学历：{row['education']}，经验：{row['experience']}",
        f"薪资：{row['salary_min']}-{row['salary_max']}（平均{row['salary_avg']}）",
        f"技能标签：{row['skills']}",
        f"岗位描述：{row['job_description']}",
        f"任职要求：{row['requirements']}",
        f"招聘渠道：{row.get('job_portal', '未知')}",
    ]
    return " ".join([clean_text(p) for p in parts if pd.notna(p)])


def main():
    # 加载三表
    jobs = pd.read_csv(JOBS_CSV)
    candidates = pd.read_csv(CANDIDATES_CSV)
    applications = pd.read_csv(APPLICATIONS_CSV)

    print(f"[step1] 原始数据：jobs={len(jobs)}, candidates={len(candidates)}, applications={len(applications)}")

    # 清洗 jobs 文本列
    text_cols = ["job_title", "job_category", "company_name", "city",
                 "education", "experience", "skills", "job_description",
                 "requirements"]
    for col in text_cols:
        if col in jobs.columns:
            jobs[col] = jobs[col].apply(clean_text)

    # 数值列去重/去空
    jobs = jobs.dropna(subset=["job_title", "job_description"])
    jobs = jobs.drop_duplicates(subset=["job_id"])

    # 生成 combined_text
    jobs["combined_text"] = jobs.apply(build_combined_text, axis=1)

    # 保存
    jobs.to_csv(RAW_JOBS_CSV, index=False, encoding="utf-8-sig")
    print(f"[step1] 岗位清洗完成，共 {len(jobs)} 条 -> {RAW_JOBS_CSV}")

    return jobs, candidates, applications


if __name__ == "__main__":
    main()