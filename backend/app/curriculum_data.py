"""
UPSKILL AI - Demo Course Curriculum Data (Phase 14)

Provides structured demo modules, lessons (TEXT, LINK, VIDEO_URL), and prerequisites
for the 8 demo courses in the UPSKILL AI catalog.
All records are explicitly labelled as demo data (is_demo=True).
"""

DEMO_PREREQUISITES = [
    # (course_code, prerequisite_course_code)
    ("TECH_WEB_201", "TECH_PY_101"),
    ("TECH_DATA_301", "TECH_PY_101"),
    ("TECH_CLOUD_401", "TECH_WEB_201"),
]

DEMO_COURSE_CURRICULUM = {
    "TECH_PY_101": {
        "min_diagnostic_score": 50.0,
        "modules": [
            {
                "title": "Module 1: Python Core Foundations & Syntax",
                "description": "Introduction to Python data types, operators, flow control, and core runtime concepts.",
                "order": 1,
                "lessons": [
                    {
                        "title": "1.1 Introduction to Python Syntax, Types & Variables",
                        "lesson_type": "TEXT",
                        "estimated_minutes": 15,
                        "order": 1,
                        "body": (
                            "# Python Core Syntax & Variable Types\n\n"
                            "Python is a dynamically typed, high-level language with clean readable syntax. "
                            "In this lesson, we explore foundational syntax constructs:\n\n"
                            "### Primitive Types\n"
                            "- **integers (`int`)**: Arbitrary precision signed integers (e.g. `x = 42`).\n"
                            "- **floating-point (`float`)**: Double-precision 64-bit IEEE 754 floats (`pi = 3.14159`).\n"
                            "- **strings (`str`)**: Immutable sequences of Unicode characters.\n"
                            "- **booleans (`bool`)**: `True` and `False` values.\n\n"
                            "```python\n"
                            "# Demonstration of type inspection\n"
                            "count = 10\n"
                            "rate = 0.05\n"
                            "label = 'Performance Metric'\n"
                            "is_valid = count > 0\n\n"
                            "print(f'{label}: {count} at {rate*100}% -> Active: {is_valid}')\n"
                            "```\n\n"
                            "> **Key Takeaway**: Variables in Python are pointers to heap-allocated objects. "
                            "Variables do not have types; the objects they reference hold the type information."
                        ),
                    },
                    {
                        "title": "1.2 Control Flow: Branching, Loops, and Iterables",
                        "lesson_type": "TEXT",
                        "estimated_minutes": 20,
                        "order": 2,
                        "body": (
                            "# Control Flow & Iteration Patterns\n\n"
                            "Mastering structured execution with `if/elif/else`, `for` loops, and `while` loops.\n\n"
                            "### Idiomatic Iteration\n"
                            "In Python, loops iterate over iterables directly rather than using index counters:\n\n"
                            "```python\n"
                            "data_records = [12, 19, 24, 31, 45]\n"
                            "total = 0\n"
                            "for index, value in enumerate(data_records, start=1):\n"
                            "    if value >= 20:\n"
                            "        total += value\n"
                            "        print(f'Record #{index}: {value} (Qualified)')\n"
                            "```\n\n"
                            "### List Comprehensions\n"
                            "Comprehensions provide concise syntax to transform and filter collections:\n"
                            "```python\n"
                            "squared_evens = [x**2 for x in data_records if x % 2 == 0]\n"
                            "```"
                        ),
                    },
                    {
                        "title": "1.3 Official Python 3 Documentation & Interactive Tutorial",
                        "lesson_type": "LINK",
                        "estimated_minutes": 15,
                        "order": 3,
                        "body": "https://docs.python.org/3/tutorial/",
                    },
                ],
            },
            {
                "title": "Module 2: Collections, Functions & Modular Architecture",
                "description": "Composite data structures, functional patterns, error handling, and modular design.",
                "order": 2,
                "lessons": [
                    {
                        "title": "2.1 Advanced Collections: Dictionaries, Sets & Tuples",
                        "lesson_type": "TEXT",
                        "estimated_minutes": 25,
                        "order": 1,
                        "body": (
                            "# Python Composite Data Structures\n\n"
                            "Data structures determine computational complexity and memory usage:\n\n"
                            "- **Tuples**: Immutable sequences, hashable, memory-compact.\n"
                            "- **Sets**: Unordered collections of unique hashable elements ($O(1)$ lookup time).\n"
                            "- **Dictionaries**: Key-value mappings optimized for fast random access ($O(1)$ average).\n\n"
                            "```python\n"
                            "officer_roles = {\n"
                            "    'SO': 'Statistical Officer',\n"
                            "    'DA': 'Data Analyst',\n"
                            "    'RO': 'Research Officer',\n"
                            "}\n"
                            "for code, title in officer_roles.items():\n"
                            "    print(f'[{code}] -> {title}')\n"
                            "```"
                        ),
                    },
                    {
                        "title": "2.2 Defining Functions, Scope, and Lambda Expressions",
                        "lesson_type": "TEXT",
                        "estimated_minutes": 20,
                        "order": 2,
                        "body": (
                            "# First-Class Functions & Scope Rules\n\n"
                            "Functions in Python are first-class citizens: they can be passed as arguments, "
                            "returned from other functions, and stored in variables.\n\n"
                            "```python\n"
                            "def calculate_weighted_score(scores, weights=None):\n"
                            "    '''Compute weighted average with optional custom weights.'''\n"
                            "    if weights is None:\n"
                            "        return sum(scores) / len(scores) if scores else 0.0\n"
                            "    return sum(s * w for s, w in zip(scores, weights)) / sum(weights)\n"
                            "```"
                        ),
                    },
                    {
                        "title": "2.3 Video Lecture: Idiomatic Python & Practical Coding",
                        "lesson_type": "VIDEO_URL",
                        "estimated_minutes": 20,
                        "order": 3,
                        "body": "https://www.youtube.com/watch?v=kqtD5dpn9C8",
                    },
                ],
            },
        ],
    },

    "TECH_WEB_201": {
        "min_diagnostic_score": 50.0,
        "modules": [
            {
                "title": "Module 1: REST Architecture & High-Performance Backends",
                "description": "RESTful API design, FastAPI routing, request validation, and database pooling.",
                "order": 1,
                "lessons": [
                    {
                        "title": "1.1 RESTful API Principles & HTTP Protocol",
                        "lesson_type": "TEXT",
                        "estimated_minutes": 20,
                        "order": 1,
                        "body": (
                            "# REST Architecture & Web Protocols\n\n"
                            "REST (Representational State Transfer) is a stateless architectural style for network applications.\n\n"
                            "### Key HTTP Methods:\n"
                            "- `GET`: Safe, idempotent retrieval of resource representations.\n"
                            "- `POST`: Creates subordinate resources or initiates non-idempotent processing.\n"
                            "- `PUT`: Idempotent full replacement of the resource.\n"
                            "- `PATCH`: Idempotent partial modification of the resource.\n"
                            "- `DELETE`: Idempotent resource removal.\n\n"
                            "### Status Code Semantics:\n"
                            "- `200 OK`: Request succeeded with body.\n"
                            "- `201 Created`: Resource successfully provisioned.\n"
                            "- `400 Bad Request`: Client validation error.\n"
                            "- `401 Unauthorized`: Authentication missing or invalid.\n"
                            "- `403 Forbidden`: Authenticated user lacks permission.\n"
                            "- `404 Not Found`: Target resource does not exist."
                        ),
                    },
                    {
                        "title": "1.2 FastAPI Framework & Pydantic Validation",
                        "lesson_type": "TEXT",
                        "estimated_minutes": 25,
                        "order": 2,
                        "body": (
                            "# Modern Python Web API with FastAPI\n\n"
                            "FastAPI provides asynchronous request handling, automatic OpenAPI generation, and strict typing.\n\n"
                            "```python\n"
                            "from fastapi import FastAPI, Depends\n"
                            "from pydantic import BaseModel, Field\n\n"
                            "app = FastAPI()\n\n"
                            "class Item(BaseModel):\n"
                            "    name: str = Field(..., min_length=2)\n"
                            "    price: float = Field(..., gt=0)\n\n"
                            "@app.post('/items', status_code=201)\n"
                            "def create_item(item: Item):\n"
                            "    return {'status': 'created', 'data': item.model_dump()}\n"
                            "```"
                        ),
                    },
                    {
                        "title": "1.3 Interactive Reference: FastAPI Official Documentation",
                        "lesson_type": "LINK",
                        "estimated_minutes": 15,
                        "order": 3,
                        "body": "https://fastapi.tiangolo.com/tutorial/",
                    },
                ],
            },
            {
                "title": "Module 2: Frontend State Management & Component Design",
                "description": "Modern React frontend patterns, hooks, state lifecycle, and API integration.",
                "order": 2,
                "lessons": [
                    {
                        "title": "2.1 React Component Hierarchy and State Flow",
                        "lesson_type": "TEXT",
                        "estimated_minutes": 25,
                        "order": 1,
                        "body": (
                            "# Reactive UI Architecture\n\n"
                            "Modern SPAs structure user interfaces into reusable declarative components:\n\n"
                            "- **Props**: One-way data passed down from parents.\n"
                            "- **State**: Local mutable state encapsulated via `useState` and `useReducer`.\n"
                            "- **Effects**: Side-effects such as API calls and subscriptions handled via `useEffect`.\n"
                            "- **Context**: Global shared dependencies (Authentication, Theme, Notifications)."
                        ),
                    },
                    {
                        "title": "2.2 Video Guide: Full Stack Web Architecture",
                        "lesson_type": "VIDEO_URL",
                        "estimated_minutes": 20,
                        "order": 2,
                        "body": "https://www.youtube.com/watch?v=0riHps91AzE",
                    },
                ],
            },
        ],
    },

    "TECH_DATA_301": {
        "min_diagnostic_score": 50.0,
        "modules": [
            {
                "title": "Module 1: Relational Database Modeling & SQL Queries",
                "description": "Query syntax, table joins, aggregations, window functions, and indexing strategies.",
                "order": 1,
                "lessons": [
                    {
                        "title": "1.1 SQL Foundations: SELECT, Filtering, and Joins",
                        "lesson_type": "TEXT",
                        "estimated_minutes": 20,
                        "order": 1,
                        "body": (
                            "# Relational Queries and Joins\n\n"
                            "SQL (Structured Query Language) is the industry standard for querying relational tables.\n\n"
                            "```sql\n"
                            "SELECT \n"
                            "    c.name AS course_name,\n"
                            "    COUNT(e.id) AS total_enrolled,\n"
                            "    AVG(e.progress_percent) AS avg_progress\n"
                            "FROM courses c\n"
                            "INNER JOIN course_enrollments e ON c.id = e.course_id\n"
                            "WHERE c.status = 'PUBLISHED'\n"
                            "GROUP BY c.id, c.name\n"
                            "HAVING COUNT(e.id) > 0\n"
                            "ORDER BY avg_progress DESC;\n"
                            "```"
                        ),
                    },
                    {
                        "title": "1.2 PostgreSQL Official SQL Reference",
                        "lesson_type": "LINK",
                        "estimated_minutes": 15,
                        "order": 2,
                        "body": "https://www.postgresql.org/docs/current/tutorial-sql.html",
                    },
                ],
            },
            {
                "title": "Module 2: Exploratory Data Analysis & Visualization",
                "description": "Summary statistics, outlier detection, distribution analysis, and insight storytelling.",
                "order": 2,
                "lessons": [
                    {
                        "title": "2.1 Statistical Data Distribution & Summary Metrics",
                        "lesson_type": "TEXT",
                        "estimated_minutes": 20,
                        "order": 1,
                        "body": (
                            "# Exploratory Data Analysis (EDA)\n\n"
                            "Before training machine learning models or writing executive summaries, analysts evaluate:\n\n"
                            "1. **Measures of Central Tendency**: Mean, Median, and Mode.\n"
                            "2. **Measures of Dispersion**: Variance, Standard Deviation, Interquartile Range (IQR).\n"
                            "3. **Missing Data Handling**: Listwise deletion vs deterministic mean/median imputation.\n"
                            "4. **Outlier Detection**: Z-score and box-plot thresholds."
                        ),
                    },
                    {
                        "title": "2.2 Video Walkthrough: Data Wrangling and Analytics",
                        "lesson_type": "VIDEO_URL",
                        "estimated_minutes": 20,
                        "order": 2,
                        "body": "https://www.youtube.com/watch?v=r-uOLxNrNk8",
                    },
                ],
            },
        ],
    },

    "TECH_CLOUD_401": {
        "min_diagnostic_score": 50.0,
        "modules": [
            {
                "title": "Module 1: Containerization with Docker",
                "description": "Container architecture, Dockerfile instructions, multi-stage builds, and Compose.",
                "order": 1,
                "lessons": [
                    {
                        "title": "1.1 Docker Fundamentals & Multi-Stage Builds",
                        "lesson_type": "TEXT",
                        "estimated_minutes": 20,
                        "order": 1,
                        "body": (
                            "# Containerization and System Isolation\n\n"
                            "Containers package an application with all runtime dependencies, eliminating environment drift.\n\n"
                            "### Multi-Stage Dockerfile Pattern\n"
                            "Separates compilation tools from the minimal runtime image:\n\n"
                            "```dockerfile\n"
                            "FROM python:3.11-slim AS builder\n"
                            "WORKDIR /app\n"
                            "COPY requirements.txt .\n"
                            "RUN pip install --no-cache-dir -r requirements.txt\n\n"
                            "FROM python:3.11-slim\n"
                            "WORKDIR /app\n"
                            "COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages\n"
                            "COPY . .\n"
                            "CMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]\n"
                            "```"
                        ),
                    },
                    {
                        "title": "1.2 Official Docker Documentation Guide",
                        "lesson_type": "LINK",
                        "estimated_minutes": 15,
                        "order": 2,
                        "body": "https://docs.docker.com/get-started/",
                    },
                ],
            },
            {
                "title": "Module 2: CI/CD Pipelines and Automated Delivery",
                "description": "Continuous Integration, automated testing, container registry push, and deploy hooks.",
                "order": 2,
                "lessons": [
                    {
                        "title": "2.1 GitHub Actions Workflow Engineering",
                        "lesson_type": "TEXT",
                        "estimated_minutes": 25,
                        "order": 1,
                        "body": (
                            "# Continuous Integration & Automated Delivery\n\n"
                            "Robust deployment pipelines enforce tests and security checks before promoting code to production:\n\n"
                            "1. **Linting & Type-Checking**: Flake8, Black, MyPy.\n"
                            "2. **Automated Test Matrix**: Pytest test suite on clean ephemeral databases.\n"
                            "3. **Artifact Container Build**: Validates `docker build` context.\n"
                            "4. **Continuous Deployment Trigger**: Triggers managed host webhooks only upon pipeline green."
                        ),
                    },
                    {
                        "title": "2.2 Video Lecture: Modern DevOps and Deployment Automation",
                        "lesson_type": "VIDEO_URL",
                        "estimated_minutes": 20,
                        "order": 2,
                        "body": "https://www.youtube.com/watch?v=scEDHsr3APg",
                    },
                ],
            },
        ],
    },

    "NONTECH_COMM_101": {
        "min_diagnostic_score": None,
        "modules": [
            {
                "title": "Module 1: Executive Writing & Clear Reporting",
                "description": "Techniques for concise communication, structured briefs, and executive summaries.",
                "order": 1,
                "lessons": [
                    {
                        "title": "1.1 The Pyramid Principle in Professional Writing",
                        "lesson_type": "TEXT",
                        "estimated_minutes": 15,
                        "order": 1,
                        "body": (
                            "# The Minto Pyramid Principle\n\n"
                            "Executive decision makers consume information top-down:\n\n"
                            "1. **Core Recommendation First**: State the primary insight or requested decision upfront.\n"
                            "2. **Supporting Pillars**: Provide 3-4 distinct logical rationales.\n"
                            "3. **Evidentiary Detail**: Supply quantitative statistical data and citations below."
                        ),
                    },
                    {
                        "title": "1.2 Harvard Business Review Guide to Business Writing",
                        "lesson_type": "LINK",
                        "estimated_minutes": 15,
                        "order": 2,
                        "body": "https://hbr.org/topic/subject/business-writing",
                    },
                ],
            },
            {
                "title": "Module 2: Stakeholder Communication & Meetings",
                "description": "Leading productive briefings, managing cross-functional consensus, and actionable minutes.",
                "order": 2,
                "lessons": [
                    {
                        "title": "2.1 Video Lecture: Executive Communication Mastery",
                        "lesson_type": "VIDEO_URL",
                        "estimated_minutes": 20,
                        "order": 1,
                        "body": "https://www.youtube.com/watch?v=Unzc731iCUY",
                    },
                ],
            },
        ],
    },

    "NONTECH_PROD_102": {
        "min_diagnostic_score": None,
        "modules": [
            {
                "title": "Module 1: Focus Frameworks & Time Blocking",
                "description": "Prioritization matrices, deep work rituals, and cognitive load minimization.",
                "order": 1,
                "lessons": [
                    {
                        "title": "1.1 Eisenhower Matrix & Urgency vs Importance",
                        "lesson_type": "TEXT",
                        "estimated_minutes": 15,
                        "order": 1,
                        "body": (
                            "# Prioritization Frameworks\n\n"
                            "Effective time management prioritizes high-impact, non-urgent tasks:\n\n"
                            "- **Quadrant 1 (Urgent & Important)**: Crises, deadlines -> Do immediately.\n"
                            "- **Quadrant 2 (Not Urgent & Important)**: Competency growth, strategic planning -> Schedule time.\n"
                            "- **Quadrant 3 (Urgent & Not Important)**: Interruptions -> Delegate or batch.\n"
                            "- **Quadrant 4 (Not Urgent & Not Important)**: Distractions -> Eliminate."
                        ),
                    },
                    {
                        "title": "1.2 Deep Work Principles & Focus Strategies",
                        "lesson_type": "LINK",
                        "estimated_minutes": 15,
                        "order": 2,
                        "body": "https://calnewport.com/deep-work-rules-for-focused-success-in-a-distracted-world/",
                    },
                ],
            },
        ],
    },

    "NONTECH_FIN_103": {
        "min_diagnostic_score": None,
        "modules": [
            {
                "title": "Module 1: Financial Statements & Cash Flow",
                "description": "Reading balance sheets, income statements, and cash flow fundamentals.",
                "order": 1,
                "lessons": [
                    {
                        "title": "1.1 Cash Flow vs Accrual Accounting",
                        "lesson_type": "TEXT",
                        "estimated_minutes": 20,
                        "order": 1,
                        "body": (
                            "# Foundations of Financial Accounting\n\n"
                            "Understanding the health of organizations and households begins with the three primary statements:\n\n"
                            "- **Income Statement**: Revenue minus expenses across an accounting period.\n"
                            "- **Balance Sheet**: Assets = Liabilities + Equity at a specific point in time.\n"
                            "- **Cash Flow Statement**: Actual liquidity movement categorized by operating, investing, and financing activities."
                        ),
                    },
                    {
                        "title": "1.2 Investopedia Financial Literacy Essentials",
                        "lesson_type": "LINK",
                        "estimated_minutes": 15,
                        "order": 2,
                        "body": "https://www.investopedia.com/financial-literacy-4689770",
                    },
                ],
            },
        ],
    },

    "NONTECH_PEDAGOGY_104": {
        "min_diagnostic_score": None,
        "modules": [
            {
                "title": "Module 1: Outcome-Based Learning Design",
                "description": "Aligning learning outcomes with active assessment and student engagement.",
                "order": 1,
                "lessons": [
                    {
                        "title": "1.1 Bloom's Revised Taxonomy in Digital Instruction",
                        "lesson_type": "TEXT",
                        "estimated_minutes": 20,
                        "order": 1,
                        "body": (
                            "# Outcome-Based Instructional Design\n\n"
                            "Cognitive learning objectives advance through six measurable tiers:\n\n"
                            "1. **Remember**: Recall facts and foundational concepts.\n"
                            "2. **Understand**: Explain ideas or principles.\n"
                            "3. **Apply**: Use information in new situations.\n"
                            "4. **Analyze**: Draw connections and discriminate between concepts.\n"
                            "5. **Evaluate**: Justify a stance or diagnostic decision.\n"
                            "6. **Create**: Produce new or original work."
                        ),
                    },
                    {
                        "title": "1.2 Active Learning in Higher Education Video",
                        "lesson_type": "VIDEO_URL",
                        "estimated_minutes": 15,
                        "order": 2,
                        "body": "https://www.youtube.com/watch?v=Z7m3gG1eWd4",
                    },
                ],
            },
        ],
    },
}
