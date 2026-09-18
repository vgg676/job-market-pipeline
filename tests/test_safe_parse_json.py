import os
import sys
import json

# 确保能导入项目根目录的 extract_llm 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extract_llm import safe_parse_json, _normalize, EMPTY_RESULT


SAMPLE = {
    "job_title": "数据分析师",
    "technical_skills": ["Python", "SQL"],
    "soft_skills": ["沟通能力"],
    "experience_years": {"min": 3, "max": 5},
    "education": "本科",
}


def test_normal_json():
    r = safe_parse_json(json.dumps(SAMPLE))
    assert r["job_title"] == "数据分析师"
    assert r["technical_skills"] == ["Python", "SQL"]
    assert r["experience_years"] == {"min": 3, "max": 5}
    assert r["education"] == "本科"


def test_markdown_code_block():
    raw = "```json\n" + json.dumps(SAMPLE) + "\n```"
    r = safe_parse_json(raw)
    assert r["job_title"] == "数据分析师"
    assert r["technical_skills"] == ["Python", "SQL"]


def test_surrounded_text():
    raw = "以下是提取结果：\n" + json.dumps(SAMPLE) + "\n希望能帮到你。"
    r = safe_parse_json(raw)
    assert r["job_title"] == "数据分析师"
    assert r["experience_years"] == {"min": 3, "max": 5}


def test_invalid_input_returns_empty_and_no_raise():
    r = safe_parse_json("这根本不是合法的 JSON 内容，完全非法")
    assert r == dict(EMPTY_RESULT)
    assert r["technical_skills"] == []
    assert r["experience_years"] == {"min": None, "max": None}


def test_none_empty_and_non_string():
    assert safe_parse_json(None) == dict(EMPTY_RESULT)
    assert safe_parse_json("") == dict(EMPTY_RESULT)
    assert safe_parse_json(123) == dict(EMPTY_RESULT)
    assert safe_parse_json(["a", "b"]) == dict(EMPTY_RESULT)


def test_normalize_fills_missing_fields():
    partial = {"job_title": "工程师", "technical_skills": ["Java"]}
    r = _normalize(partial)
    assert set(r.keys()) == set(EMPTY_RESULT.keys())
    assert r["job_title"] == "工程师"
    assert r["technical_skills"] == ["Java"]
    assert r["soft_skills"] == []
    assert r["experience_years"] == {"min": None, "max": None}
    assert r["education"] is None
