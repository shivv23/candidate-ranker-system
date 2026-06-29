#!/usr/bin/env python3
"""Central configuration — all weights, thresholds, and constants."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_ARTIFACTS = BASE_DIR / "data" / "artifacts"
DATA_OUTPUT = BASE_DIR / "data" / "output"

TOP_N = 100

# --- Composite scoring weights ---
W_SEMANTIC = 0.20
W_TITLE = 0.15
W_SKILLS = 0.30
W_EXPERIENCE = 0.10
W_COMPANY = 0.05
W_SIGNALS = 0.10
W_LOCATION = 0.05
W_EDUCATION = 0.05
W_HONEYPOT_MODIFIER = 0.0

# --- JD skill focus areas (from actual JD) ---
JD_SKILLS_AI = [
    "machine learning", "deep learning", "artificial intelligence",
    "nlp", "natural language processing", "llm", "large language model",
    "gpt", "transformer", "bert", "neural network",
    "pytorch", "tensorflow", "scikit learn", "sklearn",
    "cnn", "convolutional", "rnn", "lstm",
    "reinforcement learning", "time series",
    "xgboost", "gradient boosting",
    "fine tuning", "fine-tuning",
    "huggingface", "hugging face", "hugging face transformers",
    "llms", "generative ai", "gen ai",
]
JD_SKILLS_RETRIEVAL = [
    "embedding", "vector search", "semantic search", "information retrieval",
    "faiss", "annoy", "milvus", "pinecone", "weaviate", "qdrant",
    "elasticsearch", "opensearch", "bm25", "tf-idf",
    "sentence-transformers", "sentence transformer", "bge", "e5",
    "hybrid search", "hybrid retrieval", "dense retrieval", "sparse retrieval",
]
JD_SKILLS_RANKING = [
    "ranking", "learning to rank", "ltr", "recommendation", "recommender",
    "personalization", "reranking", "ndcg", "mrr", "map",
    "xgboost", "evaluation framework", "offline evaluation", "ab testing",
]
JD_SKILLS_ENGINEERING = [
    "python", "pytorch", "tensorflow", "jax", "huggingface", "transformers",
    "rag", "langchain", "llamaindex", "mlflow", "kubeflow",
    "docker", "kubernetes", "aws", "gcp", "azure", "api",
    "fastapi", "flask", "sql", "nosql", "redis", "postgresql",
    "git", "ci/cd", "mlops",
    "lora", "qlora", "peft", "fine tuning",
    "distributed systems", "inference optimization", "production",
]
JD_SKILLS_ALL = JD_SKILLS_AI + JD_SKILLS_RETRIEVAL + JD_SKILLS_RANKING + JD_SKILLS_ENGINEERING

# NLP/IR vs CV/speech detection (for disqualifier checking)
NLP_IR_SKILLS = [
    "nlp", "natural language processing", "llm", "large language model",
    "information retrieval", "search", "ranking", "recommendation",
    "language", "transformer", "bert", "gpt", "rag",
]
CV_SPEECH_SKILLS = [
    "computer vision", "image", "object detection", "segmentation",
    "face recognition", "speech", "audio", "asr", "speech recognition",
    "robotics", "autonomous", "lidar", "camera",
]

# --- Title relevance scoring ---
TITLE_SCORES = {
    "senior ai engineer": 1.0,
    "ai engineer": 0.95,
    "lead ai engineer": 0.95,
    "staff machine learning engineer": 0.95,
    "senior machine learning engineer": 0.90,
    "machine learning engineer": 0.88,
    "applied ml engineer": 0.88,
    "applied scientist": 0.85,
    "ml engineer": 0.88,
    "senior applied scientist": 0.85,
    "ai research engineer": 0.80,
    "ai specialist": 0.80,
    "search engineer": 0.80,
    "recommendation systems engineer": 0.80,
    "recommendation engineer": 0.80,
    "nlp engineer": 0.80,
    "senior nlp engineer": 0.85,
    "senior data scientist": 0.75,
    "data scientist": 0.70,
    "research engineer": 0.70,
    "computer vision engineer": 0.55,
    "software engineer": 0.25,
    "senior software engineer": 0.30,
    "backend engineer": 0.30,
    "frontend engineer": 0.20,
    "full stack developer": 0.25,
    "devops engineer": 0.25,
    "cloud engineer": 0.30,
    "data engineer": 0.35,
    "junior ml engineer": 0.50,
}
TITLE_DEFAULT = 0.25

NON_TECH_TITLES = [
    "hr manager", "human resources", "recruiter", "marketing manager",
    "sales executive", "accountant", "graphic designer", "content writer",
    "customer support", "operations manager", "business analyst",
    "civil engineer", "mechanical engineer", "project manager",
]

# --- Experience fit ---
TARGET_YOE_MIN = 4
TARGET_YOE_MAX = 10
TARGET_YOE_IDEAL = 7

# --- Company type scoring ---
PRODUCT_COMPANIES = [
    "google", "microsoft", "amazon", "meta", "apple", "netflix", "linkedin",
    "uber", "airbnb", "twitter", "spotify", "slack", "stripe", "square",
    "flipkart", "swiggy", "zomato", "ola", "paytm", "phonepe", "razorpay",
    "cred", "nykaa", "policybazaar", "byju", "unacademy", "upgrad",
    "meesho", "freshworks", "zoho", "postman", "hasura",
    "sarvam ai", "krutrim", "yellow.ai", "haptik", "observe.ai",
    "verloop", "rephrase.ai", "saarthi.ai", "aganitha", "locobuzz",
    "maderas", "mad street den", "wysa", "niramai", "vizzhy",
    "redrob", "redrob ai", "salesforce", "oracle", "adobe", "intuit",
    "dream11", "dream 11", "inmobi", "vedantu", "pharmeasy", "glance",
]
CONSULTING_COMPANIES = [
    "tcs", "infosys", "wipro", "hcl", "tech mahindra", "accenture",
    "capgemini", "cognizant", "mindtree", "l&t infotech", "ltimindtree",
    "ibm", "genpact", "concentrix", "mphasis", "deloitte", "kpmg",
    "pwc", "ey", "zenta", "sutherland",
]
RESEARCH_LABS = [
    "google research", "microsoft research", "meta ai", "deepmind",
    "openai", "anthropic", "cohere", "hugging face",
]

# --- Location preference ---
PUNE_NOIDA = ["pune", "noida", "pune, maharashtra", "noida, uttar pradesh"]
OTHER_INDIAN_CITIES = [
    "bangalore", "bengaluru", "hyderabad", "gurgaon", "mumbai",
    "delhi", "chennai", "kolkata", "ahmedabad", "jaipur", "indore",
    "vizag", "trivandrum", "kochi", "chandigarh", "coimbatore",
    "bhubaneswar", "lucknow", "nagpur",
]
PREFERRED_LOCATION_BONUS = 1.03

# --- Behavioral signal weights ---
SIGNAL_WEIGHTS = {
    "recruiter_response_rate": 0.20,
    "last_active_days_ago": 0.15,
    "open_to_work_flag": 0.15,
    "profile_views_received_30d": 0.10,
    "saved_by_recruiters_30d": 0.10,
    "interview_completion_rate": 0.10,
    "offer_acceptance_rate": 0.05,
    "github_activity_score": 0.05,
    "connection_count": 0.05,
    "profile_completeness": 0.05,
}

# --- Education ---
RELEVANT_FIELDS = [
    "computer science", "computer engineering", "software engineering",
    "artificial intelligence", "machine learning", "data science",
    "electrical engineering", "electronics", "mathematics", "statistics",
    "information technology", "information science",
]

# --- Semantic query (based on actual JD text) ---
SEMANTIC_QUERY = (
    "Senior AI Engineer founding team member at a Series A AI-native talent intelligence startup. "
    "Building production embedding-based retrieval and ranking systems from scratch. "
    "Own the intelligence layer: candidate-JD matching, ranking, retrieval at scale. "
    "Production experience with sentence-transformers, embedding-based retrieval, vector databases, "
    "and hybrid search infrastructure deployed to real users. "
    "Deep expertise in embeddings, retrieval, ranking, LLMs, fine-tuning. "
    "Strong Python, systems thinking, evaluation frameworks for ranking (NDCG, MRR, MAP). "
    "Product-company background preferred, not consulting. "
    "6-8 years experience with 4-5 years in applied ML/AI at product companies. "
    "Located in or willing to relocate to Pune or Noida. "
    "Scrappy, hands-on, writes production code, ships fast. "
    "Built and shipped end-to-end ranking, search, or recommendation systems to real users."
)

# --- Fake/placeholder company names (synthetic profiles) ---
FAKE_COMPANIES = [
    "wayne enterprises", "initech", "pied piper", "globex inc",
    "acme corp", "dunder mifflin", "hooli", "stark industries",
]

# --- Honeypot detection thresholds ---
HONEYPOT_EXPERT_SKILL_ZERO_YEARS = 12
HONEYPOT_MAX_AI_SKILLS_NON_TECH = 8
HONEYPOT_MAX_SKILL_COUNT = 22
HONEYPOT_MIN_RESPONSE_RATE = 0.05
