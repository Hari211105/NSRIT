"""
UPSKILL AI - Learning Goal Courses Catalog Data (Phase 10)

Defines 6-8 demo courses split between:
- TECHNICAL (Python Fundamentals, Web Development, Data Analysis with SQL, Cloud & DevOps Essentials)
- NON-TECHNICAL (Professional Communication, Time & Productivity Management, Financial Literacy, Digital Pedagogy)

Each course links to target competencies, diagnostic questions, and learning resources.
"""

COURSES_DATA = [
    # ── Technical Courses ──
    {
        "code": "TECH_PY_101",
        "name": "Python Programming Fundamentals",
        "description": "Master core Python syntax, data structures, functional patterns, and modular application development.",
        "category": "TECHNICAL",
        "level_hint": "Beginner",
        "is_demo": True,
        "competencies": [
            {"competency_name": "Software Engineering Principles", "required_level": 3, "priority": "HIGH"},
            {"competency_name": "Statistical Software", "required_level": 2, "priority": "MEDIUM"},
        ],
    },
    {
        "code": "TECH_WEB_201",
        "name": "Modern Full-Stack Web Development",
        "description": "Build responsive web applications with RESTful APIs, database persistence, and robust front-end architectures.",
        "category": "TECHNICAL",
        "level_hint": "Intermediate",
        "is_demo": True,
        "competencies": [
            {"competency_name": "Software Engineering Principles", "required_level": 3, "priority": "HIGH"},
            {"competency_name": "Database Architecture & SQL", "required_level": 3, "priority": "HIGH"},
            {"competency_name": "Cloud Computing & DevOps", "required_level": 2, "priority": "MEDIUM"},
        ],
    },
    {
        "code": "TECH_DATA_301",
        "name": "Data Analysis & SQL for Decision Making",
        "description": "Extract insights from relational databases, perform exploratory data analysis, and craft decision-ready visual reports.",
        "category": "TECHNICAL",
        "level_hint": "Intermediate",
        "is_demo": True,
        "competencies": [
            {"competency_name": "Database Architecture & SQL", "required_level": 3, "priority": "HIGH"},
            {"competency_name": "Statistical Data Analysis", "required_level": 3, "priority": "HIGH"},
            {"competency_name": "Data Visualization", "required_level": 2, "priority": "MEDIUM"},
        ],
    },
    {
        "code": "TECH_CLOUD_401",
        "name": "Cloud Infrastructure & DevOps Essentials",
        "description": "Automate deployments with containerization, continuous integration, cloud architectures, and system resilience.",
        "category": "TECHNICAL",
        "level_hint": "Intermediate",
        "is_demo": True,
        "competencies": [
            {"competency_name": "Cloud Computing & DevOps", "required_level": 3, "priority": "HIGH"},
            {"competency_name": "Cybersecurity & Network Defense", "required_level": 2, "priority": "MEDIUM"},
        ],
    },

    # ── Non-Technical Courses ──
    {
        "code": "NONTECH_COMM_101",
        "name": "Professional Communication & Reporting",
        "description": "Communicate complex concepts with clarity, lead productive meetings, and write persuasive executive briefs.",
        "category": "NON_TECHNICAL",
        "level_hint": "Beginner",
        "is_demo": True,
        "competencies": [
            {"competency_name": "Data Visualization", "required_level": 3, "priority": "HIGH"},
            {"competency_name": "Official Statistics", "required_level": 2, "priority": "MEDIUM"},
        ],
    },
    {
        "code": "NONTECH_PROD_102",
        "name": "Time Management & Workflow Productivity",
        "description": "Techniques for prioritization, project planning, meeting milestones, and maintaining high-output workflows.",
        "category": "NON_TECHNICAL",
        "level_hint": "Beginner",
        "is_demo": True,
        "competencies": [
            {"competency_name": "Data Management", "required_level": 3, "priority": "HIGH"},
            {"competency_name": "Data Quality & Validation", "required_level": 2, "priority": "MEDIUM"},
        ],
    },
    {
        "code": "NONTECH_FIN_103",
        "name": "Financial Literacy & Personal Accounting",
        "description": "Understand cash flow statements, budgeting principles, financial risk management, and tax planning fundamentals.",
        "category": "NON_TECHNICAL",
        "level_hint": "Beginner",
        "is_demo": True,
        "competencies": [
            {"competency_name": "Financial Accounting & Reporting", "required_level": 3, "priority": "HIGH"},
            {"competency_name": "Credit Appraisal & Risk Assessment", "required_level": 2, "priority": "HIGH"},
        ],
    },
    {
        "code": "NONTECH_PEDAGOGY_104",
        "name": "Digital Pedagogy & Active Teaching",
        "description": "Create engaging digital learning modules, formative assessments, and student-centered active learning strategies.",
        "category": "NON_TECHNICAL",
        "level_hint": "Beginner",
        "is_demo": True,
        "competencies": [
            {"competency_name": "Pedagogy & Digital Learning Tools", "required_level": 3, "priority": "HIGH"},
            {"competency_name": "Data Quality & Validation", "required_level": 2, "priority": "MEDIUM"},
        ],
    },
]

# Additional learning resources ensuring each course competency has at least 2 resources
COURSE_LEARNING_RESOURCES = [
    {
        "title": "Python for Programmers: Core Language & Standard Library",
        "description": "Comprehensive reference course covering Python language idioms, data structures, and OOP patterns.",
        "source": "SWAYAM_NPTEL_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Software Engineering Principles",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 20,
        "url": "https://swayam.gov.in/courses/nptel-python-core",
    },
    {
        "title": "Statistical Computing and Scripting with Python & R",
        "description": "Hands-on data manipulation and statistical computing workflows using computational packages.",
        "source": "SWAYAM_NPTEL_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Statistical Software",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 18,
        "url": "https://swayam.gov.in/courses/nptel-stat-computing",
    },
    {
        "title": "Interactive Visual Analytics & Dashboard Design",
        "description": "Learn principles of human visual perception, interactive dashboarding, and narrative communication.",
        "source": "SKILL_INDIA_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Data Visualization",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 15,
        "url": "https://skillindiadigital.gov.in/courses/visual-analytics",
    },
    {
        "title": "Personal Finance, Budgeting & Risk Management Principles",
        "description": "Budget formulation, financial literacy, investment basics, and debt control principles.",
        "source": "SKILL_INDIA_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Financial Accounting & Reporting",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 14,
        "url": "https://skillindiadigital.gov.in/courses/financial-literacy",
    },
    {
        "title": "Credit Fundamentals and Household Solvency Analysis",
        "description": "Understand credit scoring, consumer loan evaluations, and financial solvency indicators.",
        "source": "SWAYAM_NPTEL_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Credit Appraisal & Risk Assessment",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 16,
        "url": "https://swayam.gov.in/courses/credit-fundamentals",
    },
    {
        "title": "Modern Pedagogy and Educational Media Integration",
        "description": "Techniques for hybrid teaching, virtual laboratory simulations, and outcome-based curriculum planning.",
        "source": "SWAYAM_NPTEL_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Pedagogy & Digital Learning Tools",
        "minimum_level": 1,
        "maximum_level": 4,
        "duration_hours": 22,
        "url": "https://swayam.gov.in/courses/nptel-digital-pedagogy",
    },
]
