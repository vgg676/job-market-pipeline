# pipeline.py —— 流水线编排：串联 load→extract→analyze→visualize 并每日定时生成简报
import schedule
import time
import datetime
import os
from config import DATA_DIR, RAW_JOBS_CSV

from load_data import main as load_main
from extract_llm import main as extract_main
from analyze import main as analyze_main
from visualize import main as visualize_main


def generate_brief(result):
    date_str = datetime.date.today().strftime("%Y%m%d")
    lines = [f"# 招聘趋势简报 {date_str}\n"]

    lines.append("## Top 技术技能\n")
    for skill, cnt in result["top_tech_skills"][:5]:
        lines.append(f"- {skill}: {cnt} 个岗位")

    lines.append("\n## LLM 从描述中补充的新技能\n")
    for skill, cnt in result["llm_added_skills"][:5]:
        lines.append(f"- {skill}: {cnt} 个岗位")

    if "apply_by_status" in result:
        lines.append(f"\n## 应聘状态\n- {result['apply_by_status']}")

    if "match_score_stats" in result:
        ms = result["match_score_stats"]
        lines.append(f"\n## 匹配度评分\n- 平均: {ms.get('mean', 0):.3f}, "
                     f"最高: {ms.get('max', 0):.3f}")

    path = os.path.join(DATA_DIR, f"report_{date_str}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[step5] 简报 -> {path}")


def pipeline():
    print(f"\n===== 流水线启动 {datetime.datetime.now()} =====")
    load_main()
    extract_main()
    _, _, _, result = analyze_main()
    visualize_main(result)
    generate_brief(result)
    print("===== 流水线结束 =====\n")


if __name__ == "__main__":
    pipeline()
    schedule.every().day.at("08:00").do(pipeline)
    while True:
        schedule.run_pending()
        time.sleep(60)