# analyze.py —— 多维度分析与 SQLite 入库
import sqlite3
import pandas as pd
from collections import Counter
from config import (STRUCTURED_JOBS_CSV, CANDIDATES_CSV,
                    APPLICATIONS_CSV, DB_PATH)


def load_all():
    jobs = pd.read_csv(STRUCTURED_JOBS_CSV)
    candidates = pd.read_csv(CANDIDATES_CSV)
    applications = pd.read_csv(APPLICATIONS_CSV)

    for col in ["skills_merged", "llm_technical_skills", "llm_soft_skills"]:
        jobs[col] = jobs[col].fillna("").apply(
            lambda x: [s.strip() for s in str(x).split(",") if s.strip()])
    candidates["skills"] = candidates["skills"].fillna("").apply(
        lambda x: [s.strip() for s in str(x).split(",") if s.strip()])

    return jobs, candidates, applications


def save_to_sqlite(jobs, candidates, applications):
    conn = sqlite3.connect(DB_PATH)
    for name, df in [("jobs", jobs), ("candidates", candidates), ("applications", applications)]:
        df_out = df.copy()
        for col in df_out.columns:
            if df_out[col].dtype == object:
                df_out[col] = df_out[col].apply(
                    lambda x: ",".join(x) if isinstance(x, list) else x)
        df_out.to_sql(name, conn, if_exists="replace", index=False)
    conn.close()
    print(f"[step3] 三表已写入SQLite -> {DB_PATH}")


def analyze(jobs, candidates, applications):
    result = {}

    # ============ 1. 岗位技能 Top15（用合并后的skills） ============
    tech_counter = Counter()
    for skills in jobs["skills_merged"]:
        tech_counter.update(set(skills))
    result["top_tech_skills"] = tech_counter.most_common(15)

    # ============ 2. LLM补充的新增技能（原skills中没有的） ============
    llm_only = Counter()
    for _, row in jobs.iterrows():
        orig = set(s.strip() for s in str(row.get("skills", "")).split(",") if s.strip())
        llm = set(row["llm_technical_skills"])
        llm_only.update(llm - orig)
    result["llm_added_skills"] = llm_only.most_common(10)

    # ============ 3. 城市 × 技能 ============
    city_skill = {}
    for city, grp in jobs.groupby("city"):
        c = Counter()
        for s in grp["skills_merged"]:
            c.update(set(s))
        city_skill[city] = c.most_common(5)
    result["skill_by_city"] = city_skill

    # ============ 4. 岗位类别 × 技能 ============
    cat_skill = {}
    for cat, grp in jobs.groupby("job_category"):
        c = Counter()
        for s in grp["skills_merged"]:
            c.update(set(s))
        cat_skill[cat] = c.most_common(5)
    result["skill_by_category"] = cat_skill

    # ============ 5. 薪资分布 ============
    result["salary_stats"] = {
        "min": jobs["salary_min"].describe().to_dict(),
        "max": jobs["salary_max"].describe().to_dict(),
        "avg": jobs["salary_avg"].describe().to_dict(),
    }

    # ============ 6. 应聘转化分析（三表关联） ============
    # jobs.views vs applications数量
    merged = applications.merge(jobs[["job_id", "job_category", "city", "salary_avg"]],
                                on="job_id", how="left")
    result["apply_by_status"] = merged["status"].value_counts().to_dict()
    result["apply_by_category"] = merged.groupby("job_category").size().to_dict()

    # 匹配度评分分布
    if "total_match_score" in applications.columns:
        result["match_score_stats"] = applications["total_match_score"].describe().to_dict()

    # is_matched 分布
    if "is_matched" in applications.columns:
        result["is_matched_dist"] = applications["is_matched"].value_counts().to_dict()

    return result


def print_report(result):
    print("\n" + "=" * 60)
    print("【招聘市场分析报告 — 基于天池数据集】")
    print("=" * 60)

    print("\nTop 15 技术技能（岗位覆盖数）：")
    for skill, cnt in result["top_tech_skills"]:
        print(f"  {skill:<18} {cnt}")

    print("\nLLM 从描述中补充的新增技能 Top10：")
    for skill, cnt in result["llm_added_skills"]:
        print(f"  {skill:<18} {cnt}")

    print("\n各城市 Top5 技能：")
    for city, skills in result["skill_by_city"].items():
        print(f"  [{city}] {skills}")

    print("\n各岗位类别 Top5 技能：")
    for cat, skills in result["skill_by_category"].items():
        print(f"  [{cat}] {skills}")

    print(f"\n应聘状态分布: {result['apply_by_status']}")
    print(f"各岗位类别应聘数: {result['apply_by_category']}")

    if "match_score_stats" in result:
        ms = result["match_score_stats"]
        print(f"\n匹配度评分: mean={ms.get('mean', 'N/A'):.3f}, "
              f"std={ms.get('std', 'N/A'):.3f}, "
              f"min={ms.get('min', 'N/A'):.3f}, max={ms.get('max', 'N/A'):.3f}")

    if "is_matched_dist" in result:
        print(f"匹配结果分布: {result['is_matched_dist']}")


def main():
    jobs, candidates, applications = load_all()
    save_to_sqlite(jobs, candidates, applications)
    result = analyze(jobs, candidates, applications)
    print_report(result)
    return jobs, candidates, applications, result


if __name__ == "__main__":
    main()