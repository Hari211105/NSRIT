"""
UPSKILL AI - Learning Goal Courses Catalog Data (Phase 10 & 11)

Defines 8 demo courses split between:
- TECHNICAL (Python Fundamentals, Web Development, Data Analysis with SQL, Cloud & DevOps Essentials)
- NON-TECHNICAL (Professional Communication, Time & Productivity Management, Financial Literacy, Digital Pedagogy)

Each course links to target competencies, diagnostic questions (MCQ or SCENARIO), and learning resources.
"""

COURSES_DATA = [
    # ── Technical Courses ──
    {
        "code": "TECH_PY_101",
        "name": "Python Programming Fundamentals",
        "description": "Master core Python syntax, data structures, functional patterns, and modular application development.",
        "category": "TECHNICAL",
        "level_hint": "Beginner",
        "estimated_hours": 24,
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
        "estimated_hours": 36,
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
        "estimated_hours": 28,
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
        "estimated_hours": 30,
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
        "estimated_hours": 16,
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
        "estimated_hours": 14,
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
        "estimated_hours": 18,
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
        "estimated_hours": 20,
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

# ─────────────────────────────────────────────────────────────────────────────
# Phase 11: Scenario-based Diagnostic Questions for Non-Technical Courses
# 5 scenario questions per non-technical subject area
# ─────────────────────────────────────────────────────────────────────────────

SCENARIO_DIAGNOSTIC_QUESTIONS = [
    # ── 1. Professional Communication & Reporting (Data Visualization & Official Statistics) ──
    {
        "competency_name": "Data Visualization",
        "question_type": "SCENARIO",
        "difficulty": "EASY",
        "question": (
            "Scenario: You are presenting monthly performance metrics to department heads who have only 10 minutes. "
            "Your deck contains 15 detailed tables with fine print. What is the most effective adjustment to make?"
        ),
        "options": [
            "Read through all 15 tables rapidly to cover every number within the time limit",
            "Synthesize the data into a high-level visual dashboard highlighting top 3 variances, keeping detailed tables in the appendix",
            "Skip the presentation and email the spreadsheet without explanation",
            "Present only the positive metrics and delete rows showing performance shortfalls"
        ],
        "correct_option": 1,
        "explanation": "Executive audiences require high-level executive summaries and variance visualisations, with dense raw tables preserved in backup slides."
    },
    {
        "competency_name": "Data Visualization",
        "question_type": "SCENARIO",
        "difficulty": "MEDIUM",
        "question": (
            "Scenario: A quarterly trend chart displays revenue growth alongside operational expenses over time. "
            "A stakeholder misinterprets the line chart because the vertical axis does not start at zero. How should you address this?"
        ),
        "options": [
            "Keep the truncated axis since it exaggerates small fluctuations dramatically",
            "Reset the vertical baseline to zero or clearly annotate the truncated scale to prevent visual distortion",
            "Convert the data into an unlabelled 3D pie chart",
            "Blame the stakeholder for not reading the tiny axis labels"
        ],
        "correct_option": 1,
        "explanation": "Truncated axes distort perceived magnitudes; starting at zero or clearly annotating breaks maintains visual and analytical honesty."
    },
    {
        "competency_name": "Official Statistics",
        "question_type": "SCENARIO",
        "difficulty": "EASY",
        "question": (
            "Scenario: During a public policy briefing, a journalist asks for preliminary survey estimates before the quality assurance review is signed off. What is your proper protocol?"
        ),
        "options": [
            "Share preliminary drafts off-the-record to gain good media coverage",
            "Decline releasing unverified figures and explain that data releases follow scheduled dissemination and quality audit standards",
            "Make up an approximate round number based on personal memory",
            "Cancel future press conferences indefinitely"
        ],
        "correct_option": 1,
        "explanation": "Official dissemination integrity requires verified release calendars and formal quality reviews before public publication."
    },
    {
        "competency_name": "Data Visualization",
        "question_type": "SCENARIO",
        "difficulty": "HARD",
        "question": (
            "Scenario: You must communicate multi-dimensional demographic survey findings to a non-technical community council. What approach ensures equitable comprehension?"
        ),
        "options": [
            "Deliver raw correlation matrix heatmaps without colour legends",
            "Use clear bar charts and choropleth maps with plain-language subtitles, intuitive color scales, and summary callout boxes",
            "Present logarithmic regression coefficients in mathematical notation",
            "Refuse to present until community members complete statistics courses"
        ],
        "correct_option": 1,
        "explanation": "Accessible communication uses plain-language labeling, intuitive color palettes (colorblind-safe), and direct summary callouts."
    },
    {
        "competency_name": "Official Statistics",
        "question_type": "SCENARIO",
        "difficulty": "MEDIUM",
        "question": (
            "Scenario: Two different administrative datasets report conflicting figures for regional school attendance. What is the first professional action?"
        ),
        "options": [
            "Average the two numbers together without investigating differences",
            "Compare underlying collection methodologies, definitions (e.g. enrolled vs daily attendance), and reference periods to reconcile discrepancies",
            "Discard whichever dataset came from the smaller department",
            "Publish whichever number looks most favorable to regional authorities"
        ],
        "correct_option": 1,
        "explanation": "Reconciling administrative discrepancies requires inspecting concept definitions, enumeration scope, and reference intervals."
    },

    # ── 2. Time Management & Productivity (Data Management & Data Quality) ──
    {
        "competency_name": "Data Management",
        "question_type": "SCENARIO",
        "difficulty": "EASY",
        "question": (
            "Scenario: You receive multiple revisions of a project dataset daily from three team members via email with names like 'final_data.csv' and 'final_data_v2.csv'. How should you organize this workflow?"
        ),
        "options": [
            "Store all attachments on your desktop without renaming them",
            "Establish a centralized repository with ISO date naming (YYYY-MM-DD_dataset_vX) and single-source-of-truth version control",
            "Delete old versions immediately without creating backups",
            "Manually merge files by copying and pasting rows randomly"
        ],
        "correct_option": 1,
        "explanation": "Systematic naming conventions and centralized version storage eliminate duplicate confusion and data corruption."
    },
    {
        "competency_name": "Data Management",
        "question_type": "SCENARIO",
        "difficulty": "MEDIUM",
        "question": (
            "Scenario: Facing a tight deadline for an annual audit, your team discovers missing documentation for several data transformations made six months ago. What should you prioritize?"
        ),
        "options": [
            "Fabricate metadata retroactively to pass inspection",
            "Reconstruct reproducible transformation scripts and document assumptions clearly in a standardized data dictionary",
            "Skip the audit and submit raw uncleaned tables",
            "Delete the transformed columns entirely"
        ],
        "correct_option": 1,
        "explanation": "Reproducible scripts and clear data dictionaries guarantee auditability and data provenance."
    },
    {
        "competency_name": "Data Quality & Validation",
        "question_type": "SCENARIO",
        "difficulty": "EASY",
        "question": (
            "Scenario: While reviewing survey responses, you find 15 questionnaires where the respondent's age is entered as '250'. How do you handle this data entry anomaly?"
        ),
        "options": [
            "Leave the value as 250 because automated algorithms will ignore it",
            "Flag the records as validation errors, review original source forms, and apply standardized imputation/nulling rules if unresolved",
            "Change all 250s to 25 without verifying the records",
            "Delete the entire dataset and cancel the project"
        ],
        "correct_option": 1,
        "explanation": "Out-of-range anomalies must be systematically flagged, audited against source records, and corrected via logged protocols."
    },
    {
        "competency_name": "Data Quality & Validation",
        "question_type": "SCENARIO",
        "difficulty": "MEDIUM",
        "question": (
            "Scenario: You must prioritize weekly tasks under high workload. A critical client report is due in two days, while routine data archival has no immediate deadline. How do you apply time management?"
        ),
        "options": [
            "Work solely on archival because it feels easier and less stressful",
            "Use the Eisenhower Matrix to prioritize the urgent & critical report first, scheduling dedicated time for archival later",
            "Abandon both tasks and wait for reminders",
            "Attempt to do both simultaneously while multitasking continuously"
        ],
        "correct_option": 1,
        "explanation": "Prioritizing urgent and high-impact deliverables first while scheduling important maintenance avoids project failure."
    },
    {
        "competency_name": "Data Quality & Validation",
        "question_type": "SCENARIO",
        "difficulty": "HARD",
        "question": (
            "Scenario: An automated validation pipeline reports a 3% schema mismatch across 500,000 ingested records before a major monthly report. What is your best response?"
        ),
        "options": [
            "Disable validation rules to allow the pipeline to succeed silently",
            "Quarantine the anomalous 3% into an error queue, process the valid 97%, and investigate the root cause in the ingestion script",
            "Halt all company operations indefinitely",
            "Manually inspect each of the 500,000 records row by row"
        ],
        "correct_option": 1,
        "explanation": "Quarantining flawed records enables partial delivery while preserving pipeline integrity and pinpointing ingestion bugs."
    },

    # ── 3. Financial Literacy & Personal Accounting (Financial Accounting & Credit Appraisal) ──
    {
        "competency_name": "Financial Accounting & Reporting",
        "question_type": "SCENARIO",
        "difficulty": "EASY",
        "question": (
            "Scenario: An individual wants to evaluate whether their monthly expenses are sustainable before taking on a mortgage loan. What financial statement is most helpful?"
        ),
        "options": [
            "Credit card rewards points summary",
            "A comprehensive cash flow statement tracking net income versus recurring living expenses and debt obligations",
            "A list of stock market indices from financial newspapers",
            "An estimate of future lottery winnings"
        ],
        "correct_option": 1,
        "explanation": "Cash flow statements clearly reveal net surplus or deficit by tracking actual inflows against all recurring obligations."
    },
    {
        "competency_name": "Financial Accounting & Reporting",
        "question_type": "SCENARIO",
        "difficulty": "MEDIUM",
        "question": (
            "Scenario: A small organization shows high recorded revenues for the quarter but cannot meet its upcoming payroll. What is the most likely financial explanation?"
        ),
        "options": [
            "Revenues were recorded on accrual basis but cash collections from receivables have been delayed",
            "The company has too much cash in its checking accounts",
            "Double-entry bookkeeping is illegal",
            "The organization should increase employee salaries to boost morale"
        ],
        "correct_option": 0,
        "explanation": "Under accrual accounting, revenue is recognized when earned rather than when cash is received; delayed receivables lead to cash shortages."
    },
    {
        "competency_name": "Credit Appraisal & Risk Assessment",
        "question_type": "SCENARIO",
        "difficulty": "EASY",
        "question": (
            "Scenario: A borrower applies for an auto loan with a debt-to-income (DTI) ratio exceeding 65%. How does a risk analyst interpret this profile?"
        ),
        "options": [
            "High creditworthiness with low probability of default",
            "High default risk, as more than half of gross income is committed to existing debt repayments",
            "The borrower has excessive unused savings",
            "DTI ratio is completely irrelevant to credit appraisal"
        ],
        "correct_option": 1,
        "explanation": "A high DTI ratio indicates over-leverage, leaving very little margin for unexpected expenses and significantly elevating default risk."
    },
    {
        "competency_name": "Credit Appraisal & Risk Assessment",
        "question_type": "SCENARIO",
        "difficulty": "MEDIUM",
        "question": (
            "Scenario: When reviewing an emergency loan request, the applicant offers personal real estate as collateral, but clean title documents are missing. What is the prudent assessment?"
        ),
        "options": [
            "Approve the loan immediately assuming documentation will arrive later",
            "Condition loan approval upon legal verification of encumbrance-free title to ensure enforceable collateral security",
            "Waive collateral requirements entirely without adjusting interest rates",
            "Double the loan amount without security"
        ],
        "correct_option": 1,
        "explanation": "Valid collateral requires legal title verification and encumbrance checks to ensure legal enforceability in the event of default."
    },
    {
        "competency_name": "Financial Accounting & Reporting",
        "question_type": "SCENARIO",
        "difficulty": "HARD",
        "question": (
            "Scenario: You are comparing two investment projects. Project A offers higher nominal returns but carries variable interest rate debt; Project B offers moderate steady cash flows with fixed-rate financing. In a rising interest rate environment, which demonstrates superior risk management?"
        ),
        "options": [
            "Project A, because variable rate debt has no downside",
            "Project B, because fixed debt insulates the project against escalating debt service costs during monetary tightening",
            "Neither project should maintain an emergency reserve",
            "Project A, provided accounting records are destroyed"
        ],
        "correct_option": 1,
        "explanation": "Fixed-rate debt hedges against rising interest rate environments, safeguarding cash flows against ballooning interest expense."
    },

    # ── 4. Digital Pedagogy & Active Teaching (Pedagogy & Digital Learning Tools) ──
    {
        "competency_name": "Pedagogy & Digital Learning Tools",
        "question_type": "SCENARIO",
        "difficulty": "EASY",
        "question": (
            "Scenario: In a virtual classroom session, you notice 70% of students have their cameras off and are not interacting in chat. What pedagogical intervention fosters engagement?"
        ),
        "options": [
            "Lecture continuously for another 90 minutes without pauses",
            "Integrate interactive polls, breakout problem-solving rooms, and formative micro-quizzes every 15 minutes",
            "Fail all students who do not speak immediately",
            "Cancel the course entirely"
        ],
        "correct_option": 1,
        "explanation": "Active learning techniques such as micro-polling, peer breakout discussions, and regular checks for understanding sustain engagement in remote environments."
    },
    {
        "competency_name": "Pedagogy & Digital Learning Tools",
        "question_type": "SCENARIO",
        "difficulty": "MEDIUM",
        "question": (
            "Scenario: A diverse cohort of learners has varying levels of prior experience with digital tools. How should an instructor structure module onboarding?"
        ),
        "options": [
            "Assume all learners possess advanced digital literacy and proceed at maximum pace",
            "Provide an orientation walkthrough, asynchronous setup video guides, and foundational prerequisite tutorials with self-paced checkpoints",
            "Prohibit any questions regarding technology or tools",
            "Use only proprietary software that requires expensive personal licenses"
        ],
        "correct_option": 1,
        "explanation": "Scaffolding learner onboarding with asynchronous setup guides and self-paced checkpoints ensures accessibility for diverse skill baselines."
    },
    {
        "competency_name": "Pedagogy & Digital Learning Tools",
        "question_type": "SCENARIO",
        "difficulty": "HARD",
        "question": (
            "Scenario: Formative quiz analytics reveal that 45% of students failed questions related to a specific core concept taught last week. What is the evidence-based pedagogical response?"
        ),
        "options": [
            "Ignore the quiz data and move to the next chapter immediately",
            "Pause progression, conduct a targeted review session with alternative visual analogies, and provide peer-assisted problem workshops",
            "Punish students by doubling homework assignments",
            "Remove the concept from the final examination so everyone passes"
        ],
        "correct_option": 1,
        "explanation": "Formative assessment data serves to inform teaching; high failure rates on key concepts necessitate targeted re-instruction and differentiated support."
    },
    {
        "competency_name": "Pedagogy & Digital Learning Tools",
        "question_type": "SCENARIO",
        "difficulty": "MEDIUM",
        "question": (
            "Scenario: An educator wants to assess practical student competence in team collaboration and real-world problem solving rather than rote memorization. What assessment format is most appropriate?"
        ),
        "options": [
            "A 100-question multiple choice test testing vocabulary definitions",
            "A collaborative project-based assessment with a transparent rubric evaluating technical output, team communication, and reflective peer reviews",
            "A timed oral recitation of textbook passages",
            "Assigning grades based on alphabetical attendance rosters"
        ],
        "correct_option": 1,
        "explanation": "Rubric-based collaborative project assessments evaluate higher-order application, teamwork, and synthesis far more effectively than rote multiple-choice recall."
    },
    {
        "competency_name": "Pedagogy & Digital Learning Tools",
        "question_type": "SCENARIO",
        "difficulty": "EASY",
        "question": (
            "Scenario: When publishing digital course materials, several students report difficulties reading course PDFs on mobile phones. What is the best inclusive design fix?"
        ),
        "options": [
            "Tell students they must purchase laptop computers",
            "Provide responsive, reflowable HTML content and accessible contrast-compliant digital formats alongside PDFs",
            "Convert all text into uncompressed image scans",
            "Reduce the font size to fit more words on small screens"
        ],
        "correct_option": 1,
        "explanation": "Responsive reflowable web formats and accessibility standards (WCAG) allow learners on varied devices to read without cognitive strain."
    },
]
