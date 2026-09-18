# extract_llm.py —— 用 LLM 从 JD 文本提取扩展 Schema（含 safe_parse_json 四级降级）
import json
import re
import time
import pandas as pd
from config import (RAW_JOBS_CSV, STRUCTURED_JOBS_CSV,
                    LLM_PROVIDER, OPENAI_API_KEY, DEEPSEEK_API_KEY)

SYSTEM_PROMPT = """你是一个招聘数据分析专家。你的任务是从非结构化的招聘JD文本中，提取出结构化信息，用于后续的数据分析。

## 核心规则

1. **只提取显式陈述的内容**：JD中没有明确写出的信息，一律填 null 或 []。严禁根据岗位名称"推测"技能（例如看到"数据分析师"就自动补上 SQL，即使JD里没写）。
2. **技能列表必须归一化**：
   - 统一使用该技能的**标准大小写写法**（Python 不是 python，SQL 不是 sql，Java 不是 java）
   - 统一使用**通用简称**（"Spring Boot" 不写成 "SpringBoot"，"PostgreSQL" 不写成 "PG"）
   - 合并同义项，避免重复（"REST API" 和 "RESTful" 统一为 "RESTful"）
3. **技术技能 vs 软技能**：
   - technical_skills：编程语言、框架、数据库、工具、平台、方法论（如 A/B测试、敏捷开发）
   - soft_skills：沟通能力、团队协作、责任心、学习能力、抗压能力、逻辑思维、表达能力、业务理解能力等**非技术类**素质
   - 学历、经验年限**不属于**技能，不要放进技能列表
4. **经验年限**：
   - 区间形式（如"3-5年"）→ {"min": 3, "max": 5}
   - 下限形式（如"3年以上"）→ {"min": 3, "max": null}
   - 上限形式（如"最多2年"）→ {"min": null, "max": 2}
   - 未提及 → {"min": null, "max": null}
5. **只输出一个JSON对象**，不要输出任何解释文字、不要用Markdown代码块包裹。

## 输出格式

严格按以下JSON Schema输出：

{
  "job_title": "string 或 null",
  "technical_skills": ["string"],
  "soft_skills": ["string"],
  "experience_years": {"min": number 或 null, "max": number 或 null},
  "education": "string 或 null"
}

## 示例

输入：
岗位名称：数据分析师
岗位描述：负责业务数据分析，搭建指标体系，输出数据报告。
技能要求：Python, SQL, Tableau
任职要求：3-5年经验，本科及以上学历。具备良好的沟通能力和业务理解能力。

输出：
{"job_title": "数据分析师", "technical_skills": ["Python", "SQL", "Tableau"], "soft_skills": ["沟通能力", "业务理解能力"], "experience_years": {"min": 3, "max": 5}, "education": "本科"}

输入：
岗位名称：高级后端开发工程师
岗位描述：负责核心服务架构设计与开发。
任职要求：5年以上经验，精通Java、Spring Boot、MySQL、Redis。熟悉微服务架构。

输出：
{"job_title": "高级后端开发工程师", "technical_skills": ["Java", "Spring Boot", "MySQL", "Redis", "微服务"], "soft_skills": [], "experience_years": {"min": 5, "max": null}, "education": null}
"""


def build_user_prompt(text):
    return f"JD文本：\n{text}"


EMPTY_RESULT = {
    "job_title": None,
    "technical_skills": [],
    "soft_skills": [],
    "experience_years": {"min": None, "max": None},
    "education": None,
}


def safe_parse_json(raw):
    if not raw or not isinstance(raw, str):
        return dict(EMPTY_RESULT)
    text = raw.strip()

    try:
        return _normalize(json.loads(text))
    except Exception:
        pass

    text2 = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return _normalize(json.loads(text2))
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            return _normalize(json.loads(match.group()))
        except Exception:
            pass

    print(f"[warn] JSON解析失败。前100字符: {text[:100]}")
    return dict(EMPTY_RESULT)


def _normalize(obj):
    result = dict(EMPTY_RESULT)
    if isinstance(obj, dict):
        for k in EMPTY_RESULT:
            if k in obj and obj[k] is not None:
                result[k] = obj[k]
    return result


def call_llm_real(text):
    from openai import OpenAI
    if LLM_PROVIDER == "deepseek":
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")
        model = "deepseek-v4-flash"
    else:
        client = OpenAI(api_key=OPENAI_API_KEY)
        model = "gpt-4o-mini"

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(text)},
        ],
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )
    return resp.choices[0].message.content


def extract_one(text):
    raw = call_llm_real(text)
    return safe_parse_json(raw)


def merge_skills(original_skills, llm_skills):
    orig = [s.strip() for s in str(original_skills).split(",") if s.strip()]
    merged = list(dict.fromkeys(orig + llm_skills))
    return ",".join(merged)


def main():
    df = pd.read_csv(RAW_JOBS_CSV)
    records = []

    for i, row in df.iterrows():
        parsed = extract_one(row["combined_text"])
        merged_skills = merge_skills(row.get("skills", ""), parsed["technical_skills"])

        records.append({
            "job_id": row["job_id"],
            "job_title": row["job_title"],
            "job_category": row.get("job_category"),
            "company_name": row.get("company_name"),
            "company_size": row.get("company_size"),
            "company_type": row.get("company_type"),
            "city": row.get("city"),
            "education": row.get("education"),
            "experience": row.get("experience"),
            "salary_min": row.get("salary_min"),
            "salary_max": row.get("salary_max"),
            "salary_avg": row.get("salary_avg"),
            "skills_merged": merged_skills,
            "llm_technical_skills": ",".join(parsed["technical_skills"]),
            "llm_soft_skills": ",".join(parsed["soft_skills"]),
            "publish_date": row.get("publish_date"),
            "views": row.get("views"),
            "applications": row.get("applications"),
        })

        print(f"[step2] ({i+1}/{len(df)}) {row['job_title']} | "
              f"原技能:{str(row.get('skills',''))[:30]} | "
              f"LLM补充:{parsed['technical_skills']}")
        time.sleep(0.5)

    out = pd.DataFrame(records)
    out.to_csv(STRUCTURED_JOBS_CSV, index=False, encoding="utf-8-sig")
    print(f"[step2] 完成，共 {len(out)} 条 -> {STRUCTURED_JOBS_CSV}")


if __name__ == "__main__":
    main()