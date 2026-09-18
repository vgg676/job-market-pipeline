# visualize.py —— 可视化生成 4 张图表
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from config import DATA_DIR
import os

plt.rcParams["font.sans-serif"] = ["SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def plot_top_skills(top_skills, save_path):
    skills = [s for s, _ in top_skills]
    counts = [c for _, c in top_skills]
    plt.figure(figsize=(10, 6))
    plt.barh(skills[::-1], counts[::-1], color="#4C72B0")
    plt.xlabel("岗位覆盖数")
    plt.title("Top 技术技能需求（合并后）")
    plt.tight_layout()
    plt.savefig(save_path, dpi=120)
    plt.close()
    print(f"[step4] 柱状图 -> {save_path}")


def plot_wordcloud(top_skills, save_path):
    freq = {s: c for s, c in top_skills}
    # ✅在这里加上 font_path！！
    wc = WordCloud(
        font_path=r"C:\Windows\Fonts\simhei.ttf",
        width=800,
        height=400,
        background_color="white"
    ).generate_from_frequencies(freq)
    wc.to_file(save_path)
    print(f"[step4] 词云 -> {save_path}")


def plot_city_skill(result, save_path):
    """城市 × Top技能 堆叠柱状图"""
    cities = list(result["skill_by_city"].keys())
    # 取所有城市 Top5 中出现过的技能
    all_skills = set()
    for skills in result["skill_by_city"].values():
        all_skills.update([s for s, _ in skills])
    all_skills = list(all_skills)[:8]

    data = {s: [] for s in all_skills}
    for city in cities:
        d = dict(result["skill_by_city"][city])
        for s in all_skills:
            data[s].append(d.get(s, 0))

    x = range(len(cities))
    width = 0.8 / len(all_skills)
    plt.figure(figsize=(14, 6))
    for i, s in enumerate(all_skills):
        plt.bar([p + i * width for p in x], data[s], width=width, label=s)
    plt.xticks([p + 0.4 for p in x], cities, rotation=45)
    plt.ylabel("岗位覆盖数")
    plt.title("城市 × 技能需求")
    plt.legend(fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(save_path, dpi=120)
    plt.close()
    print(f"[step4] 城市×技能图 -> {save_path}")


def plot_apply_status(result, save_path):
    status_dist = result.get("apply_by_status", {})
    if not status_dist:
        return
    plt.figure(figsize=(8, 5))
    plt.bar(status_dist.keys(), status_dist.values(), color="#55A868")
    plt.title("应聘状态分布")
    plt.ylabel("数量")
    plt.tight_layout()
    plt.savefig(save_path, dpi=120)
    plt.close()
    print(f"[step4] 应聘状态图 -> {save_path}")


def main(result):
    plot_top_skills(result["top_tech_skills"],
                    os.path.join(DATA_DIR, "top_skills.png"))
    plot_wordcloud(result["top_tech_skills"],
                   os.path.join(DATA_DIR, "skill_cloud.png"))
    plot_city_skill(result,
                    os.path.join(DATA_DIR, "city_skills.png"))
    plot_apply_status(result,
                      os.path.join(DATA_DIR, "apply_status.png"))


if __name__ == "__main__":
    from analyze import main as analyze_main
    _, _, _, result = analyze_main()
    main(result)
