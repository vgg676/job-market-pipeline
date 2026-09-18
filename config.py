import os

USE_MOCK = False
LLM_PROVIDER = "deepseek"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

DATA_DIR = "data"
JOBS_CSV = os.path.join(DATA_DIR, "jobs.csv")
CANDIDATES_CSV = os.path.join(DATA_DIR, "candidates.csv")
APPLICATIONS_CSV = os.path.join(DATA_DIR, "applications.csv")

RAW_JOBS_CSV = os.path.join(DATA_DIR, "raw_jobs.csv")
STRUCTURED_JOBS_CSV = os.path.join(DATA_DIR, "structured_jobs.csv")
DB_PATH = os.path.join(DATA_DIR, "jobs.db")

os.makedirs(DATA_DIR, exist_ok=True)