"""
UPSKILL AI - Demo Data Seeder (Phase 2)

Safe to run multiple times — checks for existing records before inserting.
Creates one demo role, 8 demo competencies, role-competency mappings,
one demo learner, and the learner's initial competency profile.
"""
import json
from datetime import datetime
from app.config import settings
from app.database import SessionLocal
from app.models import Role, Competency, RoleCompetency, User, LearnerCompetency, LearningResource, DiagnosticQuestion, Sector, Course, CourseCompetency
from app.security import hash_password
from app.multi_sector_data import (
    SECTORS_DATA,
    MULTI_SECTOR_ROLES,
    MULTI_SECTOR_COMPETENCIES,
    MULTI_SECTOR_ROLE_MAPPINGS,
    MULTI_SECTOR_LEARNING_RESOURCES,
    MULTI_SECTOR_DIAGNOSTIC_QUESTIONS,
)
from app.course_data import COURSES_DATA, COURSE_LEARNING_RESOURCES, SCENARIO_DIAGNOSTIC_QUESTIONS


# ---------------------------------------------------------------
# Demo role definition
# ---------------------------------------------------------------

DEMO_ROLE = {
    "name": "Statistical / Data Officer",
    "description": (
        "A demonstration role representing a statistical professional working with "
        "official statistical data, surveys, analysis, data management and dissemination."
    ),
    "is_demo": True,
}


# ---------------------------------------------------------------
# Phase 8 - selectable positions for new-user onboarding.
#
# These are competency-framework roles: choosing one at onboarding assigns the
# user that role_id, so the existing RoleCompetency mappings (required levels +
# priorities) drive their assessment, gap analysis and recommendations.
# The two framework roles reuse the seeded framework; the two demo-focused roles
# (Statistical Assistant, Administrative Officer) get their own mappings below.
# ---------------------------------------------------------------

FRAMEWORK_ROLES = [
    {
        "name": "Statistical Officer",
        "description": (
            "Plans, collects and analyses official statistical data, prepares "
            "tables and reports, and supports survey operations."
        ),
        "is_demo": False,
    },
    {
        "name": "Data Analyst",
        "description": (
            "Analyses administrative and survey datasets, builds indicators and "
            "visualisations, and supports evidence-based reporting."
        ),
        "is_demo": False,
    },
    {
        "name": "Statistical Assistant",
        "description": (
            "Supports data collection, compilation, entry and validation of "
            "statistical records under supervision."
        ),
        "is_demo": False,
    },
    {
        "name": "Administrative Officer",
        "description": (
            "Manages administrative processes and programmes, consumes statistical "
            "reports, and coordinates data requirements."
        ),
        "is_demo": False,
    },
    {
        "name": "Research Officer",
        "description": (
            "Designs studies, applies statistical methods to research questions, "
            "and interprets results for policy."
        ),
        "is_demo": False,
    },
    {
        "name": "Data Entry / Data Processing",
        "description": (
            "Handles data capture, digitisation, cleaning and initial validation "
            "of statistical records."
        ),
        "is_demo": False,
    },
]

# Required levels and priorities per framework role. Each mapping list covers a
# subset of the eight seeded competencies, so different positions genuinely get
# different assessment questions, requirements and gaps.
FRAMEWORK_ROLE_MAPPINGS = {
    "Statistical Officer": [
        {"competency_name": "Official Statistics", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Survey Methodology", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Statistical Data Analysis", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Data Management", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Statistical Software", "required_level": 2, "priority": "MEDIUM"},
        {"competency_name": "Data Visualization", "required_level": 2, "priority": "MEDIUM"},
        {"competency_name": "AI/ML for Statistics", "required_level": 2, "priority": "MEDIUM"},
        {"competency_name": "Data Quality & Validation", "required_level": 3, "priority": "HIGH"},
    ],
    "Data Analyst": [
        {"competency_name": "Statistical Data Analysis", "required_level": 4, "priority": "HIGH"},
        {"competency_name": "Statistical Software", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Data Visualization", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Data Management", "required_level": 2, "priority": "MEDIUM"},
        {"competency_name": "Data Quality & Validation", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "AI/ML for Statistics", "required_level": 2, "priority": "MEDIUM"},
    ],
    "Statistical Assistant": [
        {"competency_name": "Official Statistics", "required_level": 2, "priority": "MEDIUM"},
        {"competency_name": "Survey Methodology", "required_level": 2, "priority": "MEDIUM"},
        {"competency_name": "Data Management", "required_level": 2, "priority": "HIGH"},
        {"competency_name": "Data Quality & Validation", "required_level": 2, "priority": "HIGH"},
    ],
    "Administrative Officer": [
        {"competency_name": "Official Statistics", "required_level": 2, "priority": "HIGH"},
        {"competency_name": "Data Visualization", "required_level": 2, "priority": "MEDIUM"},
        {"competency_name": "Data Management", "required_level": 1, "priority": "LOW"},
    ],
    "Research Officer": [
        {"competency_name": "Survey Methodology", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Statistical Data Analysis", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Statistical Software", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "AI/ML for Statistics", "required_level": 2, "priority": "MEDIUM"},
    ],
    "Data Entry / Data Processing": [
        {"competency_name": "Data Management", "required_level": 2, "priority": "HIGH"},
        {"competency_name": "Data Quality & Validation", "required_level": 2, "priority": "HIGH"},
        {"competency_name": "Statistical Software", "required_level": 1, "priority": "MEDIUM"},
    ],
}


# ---------------------------------------------------------------
# Demo competencies
# ---------------------------------------------------------------

DEMO_COMPETENCIES = [
    {
        "name": "Official Statistics",
        "description": (
            "Understanding of official statistical systems, statistical standards, "
            "production processes and dissemination."
        ),
    },
    {
        "name": "Survey Methodology",
        "description": (
            "Knowledge of survey design, sampling, data collection and survey quality principles."
        ),
    },
    {
        "name": "Statistical Data Analysis",
        "description": (
            "Ability to analyze statistical datasets using appropriate statistical methods."
        ),
    },
    {
        "name": "Data Management",
        "description": (
            "Ability to organize, manage, document and maintain statistical data."
        ),
    },
    {
        "name": "Statistical Software",
        "description": (
            "Ability to use statistical software and computational tools for statistical work."
        ),
    },
    {
        "name": "Data Visualization",
        "description": (
            "Ability to communicate statistical information using appropriate visualizations."
        ),
    },
    {
        "name": "AI/ML for Statistics",
        "description": (
            "Understanding of responsible use of artificial intelligence and machine learning "
            "in statistical workflows."
        ),
    },
    {
        "name": "Data Quality & Validation",
        "description": (
            "Ability to identify, validate and improve the quality and consistency of statistical data."
        ),
    },
]


# ---------------------------------------------------------------
# Role → Competency required-level and priority mappings
# ---------------------------------------------------------------

DEMO_ROLE_COMPETENCY_MAPPINGS = [
    {"competency_name": "Official Statistics",        "required_level": 3, "priority": "HIGH"},
    {"competency_name": "Survey Methodology",         "required_level": 3, "priority": "HIGH"},
    {"competency_name": "Statistical Data Analysis",  "required_level": 3, "priority": "HIGH"},
    {"competency_name": "Data Management",            "required_level": 3, "priority": "HIGH"},
    {"competency_name": "Statistical Software",       "required_level": 2, "priority": "MEDIUM"},
    {"competency_name": "Data Visualization",         "required_level": 2, "priority": "MEDIUM"},
    {"competency_name": "AI/ML for Statistics",       "required_level": 2, "priority": "MEDIUM"},
    {"competency_name": "Data Quality & Validation",  "required_level": 3, "priority": "HIGH"},
]


# ---------------------------------------------------------------
# Demo learner definition
# ---------------------------------------------------------------

DEMO_LEARNER = {
    "name": "Demo Statistical Officer",
    "email": "demo@statlearn.local",
    "is_demo": True,
}

# Phase 8 - the demo learner arrives fully onboarded (they carry the seeded
# competency profile), so the app never shows them the onboarding step.
DEMO_LEARNER_PROFILE_COMPLETED = True

# Login password for the demo learner (Phase 7A). Used only by the auth flow;
# the existing get_demo_learner() path still resolves the learner by email.
DEMO_LEARNER_PASSWORD = "Demo@12345"


# ---------------------------------------------------------------
# Demo learner's initial competency levels
# ---------------------------------------------------------------

DEMO_LEARNER_COMPETENCIES = [
    {"competency_name": "Official Statistics",       "current_level": 2},
    {"competency_name": "Survey Methodology",        "current_level": 1},
    {"competency_name": "Statistical Data Analysis", "current_level": 2},
    {"competency_name": "Data Management",           "current_level": 1},
    {"competency_name": "Statistical Software",      "current_level": 1},
    {"competency_name": "Data Visualization",        "current_level": 3},
    {"competency_name": "AI/ML for Statistics",      "current_level": 1},
    {"competency_name": "Data Quality & Validation", "current_level": 2},
]


# ---------------------------------------------------------------
# Demo learning catalog (2 resources per competency, 16 total)
# ---------------------------------------------------------------

DEMO_LEARNING_RESOURCES = [
    # Official Statistics
    {
        "competency_name": "Official Statistics",
        "title": "Foundations of Official Statistics",
        "description": "Comprehensive introduction to India's official statistical system, national accounts, and data dissemination standards.",
        "source": "IGOT_DEMO",
        "resource_type": "COURSE",
        "minimum_level": 1,
        "maximum_level": 2,
        "duration_hours": 4,
        "url": None,
        "is_demo": True,
    },
    {
        "competency_name": "Official Statistics",
        "title": "Official Statistical Systems and Data Dissemination",
        "description": "Advanced course on statistical coordination, data governance, and international statistical standards.",
        "source": "NSSTA_TPAC_DEMO",
        "resource_type": "COURSE",
        "minimum_level": 2,
        "maximum_level": 4,
        "duration_hours": 6,
        "url": None,
        "is_demo": True,
    },
    # Survey Methodology
    {
        "competency_name": "Survey Methodology",
        "title": "Survey Methodology Fundamentals",
        "description": "Core principles of survey design, sampling frames, questionnaire structuring, and primary data collection.",
        "source": "IGOT_DEMO",
        "resource_type": "COURSE",
        "minimum_level": 1,
        "maximum_level": 2,
        "duration_hours": 4,
        "url": None,
        "is_demo": True,
    },
    {
        "competency_name": "Survey Methodology",
        "title": "Advanced Survey Methods",
        "description": "Advanced sampling techniques, non-sampling error reduction, and complex survey estimation.",
        "source": "NSSTA_TPAC_DEMO",
        "resource_type": "COURSE",
        "minimum_level": 2,
        "maximum_level": 3,
        "duration_hours": 8,
        "url": None,
        "is_demo": True,
    },
    # Statistical Data Analysis
    {
        "competency_name": "Statistical Data Analysis",
        "title": "Statistical Data Analysis Essentials",
        "description": "Fundamental methods of descriptive statistics, hypothesis testing, and exploratory data analysis.",
        "source": "IGOT_DEMO",
        "resource_type": "COURSE",
        "minimum_level": 1,
        "maximum_level": 2,
        "duration_hours": 5,
        "url": None,
        "is_demo": True,
    },
    {
        "competency_name": "Statistical Data Analysis",
        "title": "Applied Statistical Analysis",
        "description": "Regression modeling, time-series forecasting, and multivariate analysis for official statistics.",
        "source": "NSSTA_TPAC_DEMO",
        "resource_type": "COURSE",
        "minimum_level": 2,
        "maximum_level": 4,
        "duration_hours": 10,
        "url": None,
        "is_demo": True,
    },
    # Data Management
    {
        "competency_name": "Data Management",
        "title": "Statistical Data Management Fundamentals",
        "description": "Data structuring, database fundamentals, metadata management, and secure statistical storage.",
        "source": "IGOT_DEMO",
        "resource_type": "COURSE",
        "minimum_level": 1,
        "maximum_level": 2,
        "duration_hours": 3,
        "url": None,
        "is_demo": True,
    },
    {
        "competency_name": "Data Management",
        "title": "Data Governance and Documentation",
        "description": "Institutional data governance frameworks, microdata anonymization, and data archival standards.",
        "source": "NSSTA_TPAC_DEMO",
        "resource_type": "COURSE",
        "minimum_level": 2,
        "maximum_level": 3,
        "duration_hours": 6,
        "url": None,
        "is_demo": True,
    },
    # Statistical Software
    {
        "competency_name": "Statistical Software",
        "title": "Statistical Computing Fundamentals",
        "description": "Introduction to automated data processing and statistical computation tools.",
        "source": "IGOT_DEMO",
        "resource_type": "COURSE",
        "minimum_level": 1,
        "maximum_level": 2,
        "duration_hours": 4,
        "url": None,
        "is_demo": True,
    },
    {
        "competency_name": "Statistical Software",
        "title": "Statistical Software for Data Analysis",
        "description": "Practical application of modern statistical software packages for large-scale dataset analysis.",
        "source": "NSSTA_TPAC_DEMO",
        "resource_type": "COURSE",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 6,
        "url": None,
        "is_demo": True,
    },
    # Data Visualization
    {
        "competency_name": "Data Visualization",
        "title": "Data Visualization for Official Statistics",
        "description": "Designing clear charts, infographics, and statistical dashboards for public release.",
        "source": "IGOT_DEMO",
        "resource_type": "COURSE",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 3,
        "url": None,
        "is_demo": True,
    },
    {
        "competency_name": "Data Visualization",
        "title": "Communicating Statistical Insights",
        "description": "Effective statistical storytelling, executive reporting, and visual communication of survey findings.",
        "source": "NSSTA_TPAC_DEMO",
        "resource_type": "COURSE",
        "minimum_level": 2,
        "maximum_level": 4,
        "duration_hours": 4,
        "url": None,
        "is_demo": True,
    },
    # AI/ML for Statistics
    {
        "competency_name": "AI/ML for Statistics",
        "title": "Introduction to AI/ML for Statistical Work",
        "description": "Foundational concepts of machine learning, modern algorithms, and AI integration in statistical workflows.",
        "source": "IGOT_DEMO",
        "resource_type": "COURSE",
        "minimum_level": 1,
        "maximum_level": 2,
        "duration_hours": 5,
        "url": None,
        "is_demo": True,
    },
    {
        "competency_name": "AI/ML for Statistics",
        "title": "Responsible AI for Statistical Applications",
        "description": "Ethical AI considerations, bias detection, transparency, and model auditing in public statistical systems.",
        "source": "NSSTA_TPAC_DEMO",
        "resource_type": "COURSE",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 7,
        "url": None,
        "is_demo": True,
    },
    # Data Quality & Validation
    {
        "competency_name": "Data Quality & Validation",
        "title": "Statistical Data Quality Fundamentals",
        "description": "Data cleaning methods, outlier detection, logical validation rules, and error auditing.",
        "source": "IGOT_DEMO",
        "resource_type": "COURSE",
        "minimum_level": 1,
        "maximum_level": 2,
        "duration_hours": 4,
        "url": None,
        "is_demo": True,
    },
    {
        "competency_name": "Data Quality & Validation",
        "title": "Data Validation and Quality Assurance",
        "description": "Quality assurance frameworks, statistical editing, imputation methods, and validation workflows.",
        "source": "NSSTA_TPAC_DEMO",
        "resource_type": "COURSE",
        "minimum_level": 2,
        "maximum_level": 4,
        "duration_hours": 6,
        "url": None,
        "is_demo": True,
    },
]


# ---------------------------------------------------------------
# Demo diagnostic questions (2 per competency, varying difficulty)
# ---------------------------------------------------------------

DEMO_DIAGNOSTIC_QUESTIONS = [
    # Official Statistics
    {
        "competency_name": "Official Statistics",
        "question": "What is the primary purpose of official statistics?",
        "options": [
            "To provide entertainment content",
            "To inform evidence-based policy and public understanding",
            "To replace private sector data collection",
            "To generate revenue for the government"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "Official statistics are designed to inform evidence-based policy decisions and provide the public with reliable information about social, economic, and environmental conditions."
    },
    {
        "competency_name": "Official Statistics",
        "question": "Which international framework guides the production of official statistics?",
        "options": [
            "ISO 9001",
            "UN Fundamental Principles of Official Statistics",
            "GDPR",
            "IEEE 802.11"
        ],
        "correct_option": 1,
        "difficulty": "MEDIUM",
        "explanation": "The UN Fundamental Principles of Official Statistics provide the international framework for the production and dissemination of official statistics."
    },
    # Survey Methodology
    {
        "competency_name": "Survey Methodology",
        "question": "What is a sampling frame in survey methodology?",
        "options": [
            "A type of questionnaire design",
            "A list or database from which the sample is drawn",
            "The method of data analysis",
            "A budget allocation tool"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "A sampling frame is the source material or device from which the sample is drawn. It is a list of all those within a population who can be sampled."
    },
    {
        "competency_name": "Survey Methodology",
        "question": "Which sampling method gives every member of the population an equal chance of selection?",
        "options": [
            "Convenience sampling",
            "Quota sampling",
            "Simple random sampling",
            "Purposive sampling"
        ],
        "correct_option": 2,
        "difficulty": "MEDIUM",
        "explanation": "Simple random sampling gives every member of the population an equal probability of being selected, making it the most fundamental probability sampling method."
    },
    # Statistical Data Analysis
    {
        "competency_name": "Statistical Data Analysis",
        "question": "What does the mean (average) represent in descriptive statistics?",
        "options": [
            "The most frequently occurring value",
            "The middle value when data is ordered",
            "The sum of all values divided by the number of values",
            "The range between highest and lowest values"
        ],
        "correct_option": 2,
        "difficulty": "EASY",
        "explanation": "The mean is calculated by summing all values and dividing by the count of values, representing the central tendency of the data."
    },
    {
        "competency_name": "Statistical Data Analysis",
        "question": "In hypothesis testing, what does a p-value less than 0.05 typically indicate?",
        "options": [
            "The null hypothesis is definitely true",
            "There is strong evidence against the null hypothesis",
            "The sample size is too small",
            "The result is practically significant"
        ],
        "correct_option": 1,
        "difficulty": "MEDIUM",
        "explanation": "A p-value less than 0.05 indicates that there is less than a 5% probability of observing the data if the null hypothesis were true, suggesting evidence against the null hypothesis."
    },
    # Data Management
    {
        "competency_name": "Data Management",
        "question": "What is metadata in the context of data management?",
        "options": [
            "Data that has been deleted",
            "Data about the data, describing its properties and context",
            "Encrypted data for security",
            "Data stored in the cloud"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "Metadata is data that describes other data, providing information about its structure, content, quality, and context."
    },
    {
        "competency_name": "Data Management",
        "question": "What is the purpose of data documentation in official statistics?",
        "options": [
            "To make data files larger",
            "To ensure reproducibility and enable proper use of data",
            "To restrict access to data",
            "To automate data collection"
        ],
        "correct_option": 1,
        "difficulty": "MEDIUM",
        "explanation": "Data documentation ensures that data can be properly understood, used, and reproduced by others, maintaining transparency and enabling informed analysis."
    },
    # Statistical Software
    {
        "competency_name": "Statistical Software",
        "question": "Which of the following is a widely used open-source statistical software?",
        "options": [
            "Microsoft Word",
            "R",
            "Adobe Photoshop",
            "Windows Explorer"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "R is a widely used open-source programming language and software environment specifically designed for statistical computing and graphics."
    },
    {
        "competency_name": "Statistical Software",
        "question": "What is the primary advantage of using version control for statistical code?",
        "options": [
            "It makes code run faster",
            "It tracks changes and enables reproducibility of analysis",
            "It automatically generates reports",
            "It replaces the need for documentation"
        ],
        "correct_option": 1,
        "difficulty": "MEDIUM",
        "explanation": "Version control tracks changes to code over time, enabling reproducibility, collaboration, and the ability to revert to previous versions if needed."
    },
    # Data Visualization
    {
        "competency_name": "Data Visualization",
        "question": "Which chart type is most appropriate for showing trends over time?",
        "options": [
            "Pie chart",
            "Line chart",
            "Scatter plot",
            "Bar chart"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "Line charts are ideal for showing trends and changes over continuous time periods, making patterns and trajectories easy to identify."
    },
    {
        "competency_name": "Data Visualization",
        "question": "What is a key principle of effective data visualization?",
        "options": [
            "Use as many colors as possible",
            "Maximize the data-ink ratio",
            "Always use 3D effects",
            "Include maximum text labels"
        ],
        "correct_option": 1,
        "difficulty": "MEDIUM",
        "explanation": "The data-ink ratio principle (from Edward Tufte) suggests maximizing the proportion of ink used to present data, minimizing non-data ink like decorations and gridlines."
    },
    # AI/ML for Statistics
    {
        "competency_name": "AI/ML for Statistics",
        "question": "What is the difference between supervised and unsupervised learning?",
        "options": [
            "Supervised learning uses more data",
            "Supervised learning uses labeled data; unsupervised does not",
            "Unsupervised learning is always more accurate",
            "There is no meaningful difference"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "Supervised learning requires labeled training data (input-output pairs), while unsupervised learning finds patterns in data without explicit labels."
    },
    {
        "competency_name": "AI/ML for Statistics",
        "question": "What is a potential risk of using AI in official statistics without proper oversight?",
        "options": [
            "Processing data too quickly",
            "Introduction of bias and lack of transparency in results",
            "Using too little computing power",
            "Generating too few insights"
        ],
        "correct_option": 1,
        "difficulty": "MEDIUM",
        "explanation": "Without proper oversight, AI can introduce hidden biases, lack transparency in decision-making, and produce results that are difficult to explain or audit."
    },
    # Data Quality & Validation
    {
        "competency_name": "Data Quality & Validation",
        "question": "What is data validation in the context of official statistics?",
        "options": [
            "Deleting incorrect data",
            "The process of ensuring data meets defined quality criteria",
            "Converting data to a different format",
            "Backing up data to external storage"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "Data validation is the process of checking whether data conforms to defined rules, standards, and quality criteria before it is used for analysis."
    },
    {
        "competency_name": "Data Quality & Validation",
        "question": "Which type of error occurs when data is consistently off by a fixed amount?",
        "options": [
            "Random error",
            "Systematic error (bias)",
            "Transcription error",
            "Sampling error"
        ],
        "correct_option": 1,
        "difficulty": "MEDIUM",
        "explanation": "Systematic error (bias) causes data to be consistently off in one direction by a roughly fixed amount, unlike random error which varies unpredictably."
    },
    # ---- HARD questions (one per competency, for difficulty-weighted scoring) ----
    {
        "competency_name": "Official Statistics",
        "question": "Under the UN Fundamental Principles of Official Statistics, what does the principle of 'relevance, impartiality and equal access' require?",
        "options": [
            "Statistics must be compiled only for government internal use",
            "Statistical agencies must decide strictly on statistical grounds and disseminate to all users on an equal basis",
            "Statistical releases must be approved by the ministry being measured",
            "Statistics must be published only in aggregate form"
        ],
        "correct_option": 1,
        "difficulty": "HARD",
        "explanation": "The principle requires agencies to collect and disseminate official statistics on an impartial basis, with the choice of methods and timing on strictly statistical considerations, and equal access for all users."
    },
    {
        "competency_name": "Survey Methodology",
        "question": "A survey's sampling frame systematically excludes households without a landline telephone. What is the primary risk introduced?",
        "options": [
            "Increased sampling variance",
            "Coverage bias, because the frame systematically omits part of the target population",
            "Higher measurement error in responses",
            "Greater respondent burden"
        ],
        "correct_option": 1,
        "difficulty": "HARD",
        "explanation": "A frame that omits part of the target population causes coverage error (bias), which no amount of additional sampling within the frame can remove."
    },
    {
        "competency_name": "Statistical Data Analysis",
        "question": "Two variables have a Pearson correlation of -0.9. Which conclusion is valid?",
        "options": [
            "A 10% increase in one variable causes a 9% decrease in the other",
            "The variables have a strong negative linear association, but this alone does not establish causation",
            "The relationship explains 90% of the variance",
            "The data must be non-linear"
        ],
        "correct_option": 1,
        "difficulty": "HARD",
        "explanation": "-0.9 indicates a strong negative linear association. Correlation alone never establishes causation, and -0.9 does not mean 90% of variance is explained (that would be an r-squared of 0.9, which corresponds to r of about -0.95)."
    },
    {
        "competency_name": "Data Management",
        "question": "Which practice best supports reproducibility of a statistical data pipeline?",
        "options": [
            "Storing datasets in personal folders with ad-hoc file names",
            "Version-controlled processing scripts with documented metadata and recorded data lineage",
            "Keeping all processing steps in one analyst's memory",
            "Renaming output files with the publication date only"
        ],
        "correct_option": 1,
        "difficulty": "HARD",
        "explanation": "Reproducibility requires version-controlled code, documented metadata and traceable data lineage so any release can be rebuilt and audited from its inputs."
    },
    {
        "competency_name": "Statistical Software",
        "question": "In R, a numeric vector contains NA values. Why must na.rm = TRUE be passed to mean() before summarising?",
        "options": [
            "Otherwise the function silently drops the last element",
            "Because arithmetic with NA returns NA, so the result would be NA without it",
            "Because mean() cannot handle numeric vectors longer than 10 elements",
            "Otherwise the vector is converted to character"
        ],
        "correct_option": 1,
        "difficulty": "HARD",
        "explanation": "In R any arithmetic involving NA yields NA, so mean() of a vector containing NA returns NA unless the NA values are removed with na.rm = TRUE."
    },
    {
        "competency_name": "Data Visualization",
        "question": "For a chart accompanying a press release that must be readable in greyscale print, which encoding choice is most robust?",
        "options": [
            "Distinguish series only by hue",
            "Use position and length encodings with direct labels or distinct line styles",
            "Use a 3D pie chart with a legend",
            "Rely on small colour differences between similar shades"
        ],
        "correct_option": 1,
        "difficulty": "HARD",
        "explanation": "Position and length are the most accurately perceived encodings and survive greyscale printing, especially with direct labels or line styles; hue-only distinctions do not."
    },
    {
        "competency_name": "AI/ML for Statistics",
        "question": "An ML model is used to flag outlier records for follow-up in a survey. What is the most important integrity safeguard from an official-statistics perspective?",
        "options": [
            "Keeping the model's training code secret so it cannot be gamed",
            "Documenting the model, auditing it for bias, and keeping humans accountable for any data change",
            "Letting the model edit the data automatically to save staff time",
            "Using the most complex model available for best accuracy"
        ],
        "correct_option": 1,
        "difficulty": "HARD",
        "explanation": "Official statistics require transparency, auditability and human accountability: the model must be documented and audited for bias, and any change to published data must remain a human decision."
    },
    {
        "competency_name": "Data Quality & Validation",
        "question": "An editing rule imputes every implausible income value with the survey median. What is the most significant quality risk?",
        "options": [
            "The dataset becomes smaller",
            "Systematic bias, because a single imputed value is applied regardless of the respondent's characteristics",
            "The number of records decreases",
            "Sampling error increases"
        ],
        "correct_option": 1,
        "difficulty": "HARD",
        "explanation": "Applying one uniform imputed value regardless of covariates (like region, household size or employment status) distorts the distribution and introduces systematic bias; imputation should be model-based where possible."
    },
]


# ---------------------------------------------------------------
# Seeder function
# ---------------------------------------------------------------

def seed_demo_data():
    db = SessionLocal()
    try:
        print("Seeding demo data...")

        # 0. Create sectors (Phase 9 - Multi-Sector Expansion)
        sector_map = {}
        for sec_data in SECTORS_DATA:
            sec = db.query(Sector).filter_by(code=sec_data["code"]).first()
            if not sec:
                sec = Sector(**sec_data)
                db.add(sec)
                db.flush()
                print(f"  Created sector: {sec.name} ({sec.code})")
            else:
                sec.name = sec_data["name"]
                sec.description = sec_data["description"]
                sec.icon = sec_data["icon"]
                sec.display_order = sec_data["display_order"]
            sector_map[sec_data["code"]] = sec.id

        gov_sector_id = sector_map.get("GOV_STATS")

        # 1. Create demo role (skip if already exists)
        role = db.query(Role).filter_by(name=DEMO_ROLE["name"]).first()
        if not role:
            role = Role(**DEMO_ROLE, sector_id=gov_sector_id)
            db.add(role)
            db.flush()  # get role.id without committing yet
            print(f"  Created role: {role.name}")
        else:
            if role.sector_id != gov_sector_id:
                role.sector_id = gov_sector_id
            print(f"  Role already exists: {role.name}")

        # 1b. Phase 8 - create the onboarding positions (framework roles)
        framework_role_ids = {}
        for fw_role in FRAMEWORK_ROLES:
            existing_fw = db.query(Role).filter_by(name=fw_role["name"]).first()
            if not existing_fw:
                existing_fw = Role(**fw_role, sector_id=gov_sector_id)
                db.add(existing_fw)
                db.flush()
                print(f"  Created framework role: {existing_fw.name}")
            else:
                if existing_fw.sector_id != gov_sector_id:
                    existing_fw.sector_id = gov_sector_id
            framework_role_ids[fw_role["name"]] = existing_fw.id

        # 1c. Phase 9 - create multi-sector roles
        for ms_role in MULTI_SECTOR_ROLES:
            sec_id = sector_map.get(ms_role["sector_code"])
            existing_ms = db.query(Role).filter_by(name=ms_role["name"]).first()
            if not existing_ms:
                existing_ms = Role(
                    name=ms_role["name"],
                    description=ms_role["description"],
                    is_demo=ms_role["is_demo"],
                    sector_id=sec_id,
                )
                db.add(existing_ms)
                db.flush()
                print(f"  Created multi-sector role: {existing_ms.name}")
            else:
                if existing_ms.sector_id != sec_id:
                    existing_ms.sector_id = sec_id
            framework_role_ids[ms_role["name"]] = existing_ms.id

        # 2. Create demo competencies + multi-sector competencies (skip existing)
        competency_map = {}  # name → Competency object
        all_competencies = DEMO_COMPETENCIES + MULTI_SECTOR_COMPETENCIES
        for comp_data in all_competencies:
            comp = db.query(Competency).filter_by(name=comp_data["name"]).first()
            if not comp:
                comp = Competency(**comp_data, is_demo=True)
                db.add(comp)
                db.flush()
                print(f"  Created competency: {comp.name}")
            else:
                print(f"  Competency already exists: {comp.name}")
            competency_map[comp.name] = comp

        # 3. Create role-competency mappings (skip existing)
        for mapping in DEMO_ROLE_COMPETENCY_MAPPINGS:
            comp = competency_map[mapping["competency_name"]]
            existing = db.query(RoleCompetency).filter_by(
                role_id=role.id, competency_id=comp.id
            ).first()
            if not existing:
                rc = RoleCompetency(
                    role_id=role.id,
                    competency_id=comp.id,
                    required_level=mapping["required_level"],
                    priority=mapping["priority"],
                )
                db.add(rc)
                print(f"  Mapped: {role.name} -> {comp.name} (Level {mapping['required_level']}, {mapping['priority']})")

        # 3b. Apply framework-role & multi-sector competency mappings
        def _apply_role_mappings(target_role_id: int, mappings: list) -> None:
            for mapping in mappings:
                comp = competency_map.get(mapping["competency_name"])
                if comp is None:
                    continue
                existing = db.query(RoleCompetency).filter_by(
                    role_id=target_role_id, competency_id=comp.id
                ).first()
                if not existing:
                    db.add(RoleCompetency(
                        role_id=target_role_id,
                        competency_id=comp.id,
                        required_level=mapping["required_level"],
                        priority=mapping["priority"],
                    ))
                    print(f"  Mapped role {target_role_id} -> {comp.name} (Level {mapping['required_level']}, {mapping['priority']})")

        for fw_role_name, fw_mappings in FRAMEWORK_ROLE_MAPPINGS.items():
            fw_role_id = framework_role_ids.get(fw_role_name)
            if fw_role_id is None:
                continue
            _apply_role_mappings(fw_role_id, fw_mappings)

        _apply_role_mappings(role.id, FRAMEWORK_ROLE_MAPPINGS["Statistical Officer"])

        # 3c. Apply multi-sector role mappings
        for ms_role_name, ms_mappings in MULTI_SECTOR_ROLE_MAPPINGS.items():
            ms_role_id = framework_role_ids.get(ms_role_name)
            if ms_role_id is not None:
                _apply_role_mappings(ms_role_id, ms_mappings)

        # 4 & 5. Create demo learner and initial competency records
        # Restricted strictly to non-production environments (development / testing).
        # In production, learners must be registered legitimately; no hardcoded demo accounts.
        if settings.ENVIRONMENT != "production":
            learner = db.query(User).filter_by(email=DEMO_LEARNER["email"]).first()
            if not learner:
                learner = User(
                    name=DEMO_LEARNER["name"],
                    email=DEMO_LEARNER["email"],
                    is_demo=DEMO_LEARNER["is_demo"],
                    role_id=role.id,
                    # Phase 7A - give the demo learner a login password so the auth
                    # login endpoint works out of the box.
                    hashed_password=hash_password(DEMO_LEARNER_PASSWORD),
                    # Phase 8 - the demo learner is fully onboarded from the start.
                    designation="Statistical / Data Officer",
                    department="National Statistics Office (Demo)",
                    profile_completed=DEMO_LEARNER_PROFILE_COMPLETED,
                )
                db.add(learner)
                db.flush()
                print(f"  Created learner: {learner.name} ({learner.email})")
            else:
                # Phase 7A - backfill a password on a pre-existing demo learner that
                # was created before the hashed_password column existed.
                if not learner.hashed_password:
                    learner.hashed_password = hash_password(DEMO_LEARNER_PASSWORD)
                    print(f"  Backfilled password for existing learner: {learner.email}")
                # Phase 8 - pre-existing demo learner rows must not be pushed into
                # the onboarding flow; they keep their seeded competency profile.
                if not learner.profile_completed:
                    learner.profile_completed = DEMO_LEARNER_PROFILE_COMPLETED
                    learner.designation = learner.designation or "Statistical / Data Officer"
                    print(f"  Backfilled onboarding flag for existing learner: {learner.email}")
                print(f"  Learner already exists: {learner.email}")

            # 5. Create learner competency records (skip existing)
            for lc_data in DEMO_LEARNER_COMPETENCIES:
                comp = competency_map[lc_data["competency_name"]]
                existing = db.query(LearnerCompetency).filter_by(
                    user_id=learner.id, competency_id=comp.id
                ).first()
                if not existing:
                    lc = LearnerCompetency(
                        user_id=learner.id,
                        competency_id=comp.id,
                        current_level=lc_data["current_level"],
                    )
                    db.add(lc)
                    print(f"  Set learner level: {comp.name} -> Level {lc_data['current_level']}")
                else:
                    # Update the level to the seed value if it's different
                    if existing.current_level != lc_data["current_level"]:
                        print(f"  Updating learner level: {comp.name} from Level {existing.current_level} to Level {lc_data['current_level']}")
                        existing.current_level = lc_data["current_level"]
        else:
            print("  Skipping demo learner creation in production environment.")

        # 6. Create learning catalog resources (skip existing by title)
        all_resources = DEMO_LEARNING_RESOURCES + MULTI_SECTOR_LEARNING_RESOURCES + COURSE_LEARNING_RESOURCES
        for res_data in all_resources:
            comp = competency_map.get(res_data["competency_name"])
            if not comp:
                continue
            existing = db.query(LearningResource).filter_by(
                title=res_data["title"]
            ).first()
            if not existing:
                lr = LearningResource(
                    title=res_data["title"],
                    description=res_data["description"],
                    source=res_data["source"],
                    resource_type=res_data["resource_type"],
                    competency_id=comp.id,
                    minimum_level=res_data["minimum_level"],
                    maximum_level=res_data["maximum_level"],
                    duration_hours=res_data["duration_hours"],
                    url=res_data["url"],
                    is_demo=res_data.get("is_demo", True),
                    active=True,
                )
                db.add(lr)
                print(f"  Created learning resource: {lr.title} ({lr.source})")

        # 7. Create diagnostic questions (skip existing by question text)
        all_questions = DEMO_DIAGNOSTIC_QUESTIONS + MULTI_SECTOR_DIAGNOSTIC_QUESTIONS + SCENARIO_DIAGNOSTIC_QUESTIONS
        for q_data in all_questions:
            comp = competency_map.get(q_data["competency_name"])
            if not comp:
                continue
            existing = db.query(DiagnosticQuestion).filter(
                DiagnosticQuestion.question == q_data["question"]
            ).first()
            if not existing:
                dq = DiagnosticQuestion(
                    competency_id=comp.id,
                    question_type=q_data.get("question_type", "MCQ"),
                    question=q_data["question"],
                    options=json.dumps(q_data["options"]),
                    correct_option=q_data["correct_option"],
                    difficulty=q_data["difficulty"],
                    explanation=q_data["explanation"],
                    is_demo=True,
                    active=True,
                    created_at=datetime.utcnow().isoformat(),
                )
                db.add(dq)
                print(f"  Created diagnostic question: {q_data['question'][:60]}... ({q_data['difficulty']} - {dq.question_type})")
            else:
                # Update question_type if existing row does not have it set
                if q_data.get("question_type") and existing.question_type != q_data["question_type"]:
                    existing.question_type = q_data["question_type"]

        # 8. Create demo courses and course-competency mappings (Phase 10)
        for c_data in COURSES_DATA:
            existing_course = db.query(Course).filter_by(code=c_data["code"]).first()
            if not existing_course:
                course = Course(
                    code=c_data["code"],
                    name=c_data["name"],
                    description=c_data["description"],
                    category=c_data["category"],
                    level_hint=c_data.get("level_hint", "Beginner"),
                    is_demo=True,
                    active=True,
                )
                db.add(course)
                db.flush()
                print(f"  Created demo course: {course.name} ({course.category})")

                for comp_spec in c_data.get("competencies", []):
                    comp = competency_map.get(comp_spec["competency_name"])
                    if comp:
                        ccm = CourseCompetency(
                            course_id=course.id,
                            competency_id=comp.id,
                            required_level=comp_spec["required_level"],
                            priority=comp_spec.get("priority", "MEDIUM"),
                        )
                        db.add(ccm)
            else:
                # Ensure mappings exist if course was already created
                for comp_spec in c_data.get("competencies", []):
                    comp = competency_map.get(comp_spec["competency_name"])
                    if comp:
                        existing_ccm = db.query(CourseCompetency).filter_by(
                            course_id=existing_course.id,
                            competency_id=comp.id,
                        ).first()
                        if not existing_ccm:
                            ccm = CourseCompetency(
                                course_id=existing_course.id,
                                competency_id=comp.id,
                                required_level=comp_spec["required_level"],
                                priority=comp_spec.get("priority", "MEDIUM"),
                            )
                            db.add(ccm)

        db.commit()
        print("Demo data seeding complete.")

    except Exception as e:
        db.rollback()
        print(f"ERROR during seeding: {e}")
        raise
    finally:
        db.close()

