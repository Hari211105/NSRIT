"""
UPSKILL AI - Multi-Sector Data Catalog (Phase 9)

Defines sectors, roles, competencies, role mappings, learning resources, and
diagnostic questions across:
1. Governance & Official Statistics (GOV_STATS)
2. Information Technology & AI (TECH_IT)
3. Healthcare & Life Sciences (HEALTHCARE)
4. Banking, Finance & Accounting (FINANCE_BFSI)
5. Agriculture & Rural Development (AGRICULTURE)
6. Education & Teaching (EDUCATION)
"""

SECTORS_DATA = [
    {
        "code": "GOV_STATS",
        "name": "Governance & Official Statistics",
        "description": "Public administration, national survey operations, and official statistical dissemination.",
        "icon": "landmark",
        "display_order": 1,
    },
    {
        "code": "TECH_IT",
        "name": "Information Technology & AI",
        "description": "Software engineering, cloud infrastructure, AI/ML development, and data systems.",
        "icon": "cpu",
        "display_order": 2,
    },
    {
        "code": "HEALTHCARE",
        "name": "Healthcare & Life Sciences",
        "description": "Clinical protocols, medical diagnostics, patient care, and healthcare informatics.",
        "icon": "activity",
        "display_order": 3,
    },
    {
        "code": "FINANCE_BFSI",
        "name": "Banking, Finance & Accounting",
        "description": "Financial accounting, credit appraisal, risk assessment, and FinTech operations.",
        "icon": "trending-up",
        "display_order": 4,
    },
    {
        "code": "AGRICULTURE",
        "name": "Agriculture & Rural Development",
        "description": "Agronomy, precision farming, soil health management, and agri-supply chain.",
        "icon": "sun",
        "display_order": 5,
    },
    {
        "code": "EDUCATION",
        "name": "Education & Teaching",
        "description": "Instructional design, pedagogical methods, digital classrooms, and student assessment.",
        "icon": "book-open",
        "display_order": 6,
    },
]

MULTI_SECTOR_ROLES = [
    # TECH_IT
    {
        "name": "Full Stack Developer",
        "description": "Designs, builds, and maintains web applications, client interfaces, APIs, and database architectures.",
        "sector_code": "TECH_IT",
        "is_demo": False,
    },
    {
        "name": "Data Scientist / AI Specialist",
        "description": "Develops predictive models, applies machine learning algorithms, and derives insights from complex datasets.",
        "sector_code": "TECH_IT",
        "is_demo": False,
    },
    {
        "name": "Cybersecurity Analyst",
        "description": "Protects digital assets, monitors network vulnerabilities, implements security protocols, and manages incidents.",
        "sector_code": "TECH_IT",
        "is_demo": False,
    },
    # HEALTHCARE
    {
        "name": "Community Health Officer",
        "description": "Delivers primary healthcare services, coordinates public health programs, and manages patient reporting.",
        "sector_code": "HEALTHCARE",
        "is_demo": False,
    },
    {
        "name": "Medical Laboratory Technician",
        "description": "Conducts clinical laboratory tests, maintains quality control standards, and analyzes diagnostic specimens.",
        "sector_code": "HEALTHCARE",
        "is_demo": False,
    },
    # FINANCE_BFSI
    {
        "name": "Financial Analyst",
        "description": "Evaluates financial data, prepares economic forecasts, analyzes investment performance, and builds valuation models.",
        "sector_code": "FINANCE_BFSI",
        "is_demo": False,
    },
    {
        "name": "Credit & Risk Officer",
        "description": "Appraises credit applications, assesses borrower solvency, manages portfolio risk, and enforces compliance.",
        "sector_code": "FINANCE_BFSI",
        "is_demo": False,
    },
    # AGRICULTURE
    {
        "name": "Agronomist / Agri-Officer",
        "description": "Implements modern agronomic practices, advises on soil fertility and crop health, and improves farm productivity.",
        "sector_code": "AGRICULTURE",
        "is_demo": False,
    },
    # EDUCATION
    {
        "name": "STEM Educator",
        "description": "Delivers hands-on science and technology instruction, designs learning modules, and leverages digital education tools.",
        "sector_code": "EDUCATION",
        "is_demo": False,
    },
]

MULTI_SECTOR_COMPETENCIES = [
    # TECH
    {
        "name": "Software Engineering Principles",
        "description": "Modern software architecture, clean code practices, modular design, and version control workflows.",
    },
    {
        "name": "Cloud Computing & DevOps",
        "description": "Deployment automation, containerization, cloud infrastructure (AWS/Azure/GCP), and CI/CD pipelines.",
    },
    {
        "name": "Database Architecture & SQL",
        "description": "Relational schema design, query optimization, indexing, and data persistence guarantees.",
    },
    {
        "name": "Applied Machine Learning",
        "description": "Feature engineering, model training, evaluation metrics, and supervised/unsupervised learning techniques.",
    },
    {
        "name": "Cybersecurity & Network Defense",
        "description": "Vulnerability scanning, encryption standards, threat intelligence, and identity management.",
    },
    # HEALTHCARE
    {
        "name": "Public Health & Clinical Protocols",
        "description": "Standard operating procedures for primary clinical care, epidemic control, and preventive healthcare.",
    },
    {
        "name": "Medical Diagnostics & Lab Safety",
        "description": "Specimen collection, biomedical equipment handling, diagnostic interpretation, and biosafety protocols.",
    },
    {
        "name": "Healthcare Informatics",
        "description": "Electronic health records (EHR), patient data privacy, and medical classification coding.",
    },
    # FINANCE
    {
        "name": "Financial Accounting & Reporting",
        "description": "Corporate financial statements, cash flow analysis, IFRS/Ind-AS compliance, and ledger audits.",
    },
    {
        "name": "Credit Appraisal & Risk Assessment",
        "description": "Creditworthiness evaluation, collateral assessment, debt-service coverage, and delinquency mitigation.",
    },
    # AGRICULTURE
    {
        "name": "Crop Science & Soil Health",
        "description": "Soil nutrient management, integrated pest management (IPM), irrigation techniques, and crop rotation.",
    },
    # EDUCATION
    {
        "name": "Pedagogy & Digital Learning Tools",
        "description": "Curriculum planning, learner-centric instructional design, educational technology platforms, and formative assessment.",
    },
]

MULTI_SECTOR_ROLE_MAPPINGS = {
    "Full Stack Developer": [
        {"competency_name": "Software Engineering Principles", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Database Architecture & SQL", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Cloud Computing & DevOps", "required_level": 2, "priority": "MEDIUM"},
    ],
    "Data Scientist / AI Specialist": [
        {"competency_name": "Applied Machine Learning", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Statistical Data Analysis", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Data Visualization", "required_level": 2, "priority": "MEDIUM"},
        {"competency_name": "Database Architecture & SQL", "required_level": 2, "priority": "MEDIUM"},
    ],
    "Cybersecurity Analyst": [
        {"competency_name": "Cybersecurity & Network Defense", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Cloud Computing & DevOps", "required_level": 2, "priority": "MEDIUM"},
        {"competency_name": "Software Engineering Principles", "required_level": 2, "priority": "MEDIUM"},
    ],
    "Community Health Officer": [
        {"competency_name": "Public Health & Clinical Protocols", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Healthcare Informatics", "required_level": 2, "priority": "MEDIUM"},
        {"competency_name": "Data Quality & Validation", "required_level": 2, "priority": "MEDIUM"},
    ],
    "Medical Laboratory Technician": [
        {"competency_name": "Medical Diagnostics & Lab Safety", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Public Health & Clinical Protocols", "required_level": 2, "priority": "MEDIUM"},
        {"competency_name": "Data Quality & Validation", "required_level": 2, "priority": "MEDIUM"},
    ],
    "Financial Analyst": [
        {"competency_name": "Financial Accounting & Reporting", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Credit Appraisal & Risk Assessment", "required_level": 2, "priority": "HIGH"},
        {"competency_name": "Statistical Data Analysis", "required_level": 2, "priority": "MEDIUM"},
    ],
    "Credit & Risk Officer": [
        {"competency_name": "Credit Appraisal & Risk Assessment", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Financial Accounting & Reporting", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Data Quality & Validation", "required_level": 2, "priority": "MEDIUM"},
    ],
    "Agronomist / Agri-Officer": [
        {"competency_name": "Crop Science & Soil Health", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Data Quality & Validation", "required_level": 2, "priority": "MEDIUM"},
        {"competency_name": "Survey Methodology", "required_level": 2, "priority": "LOW"},
    ],
    "STEM Educator": [
        {"competency_name": "Pedagogy & Digital Learning Tools", "required_level": 3, "priority": "HIGH"},
        {"competency_name": "Software Engineering Principles", "required_level": 2, "priority": "MEDIUM"},
        {"competency_name": "Data Visualization", "required_level": 2, "priority": "MEDIUM"},
    ],
}

MULTI_SECTOR_LEARNING_RESOURCES = [
    # TECH_IT (SWAYAM / NPTEL / OPEN)
    {
        "title": "Software Engineering Fundamentals and System Design",
        "description": "Comprehensive design patterns, SOLID principles, testing paradigms, and maintainable software architecture.",
        "source": "SWAYAM_NPTEL_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Software Engineering Principles",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 30,
        "url": "https://swayam.gov.in/courses/nptel-se-fundamentals",
    },
    {
        "title": "Cloud Computing Platforms and DevOps Automation",
        "description": "Hands-on cloud orchestration with Docker, Kubernetes, CI/CD pipelines, and infrastructure as code.",
        "source": "SWAYAM_NPTEL_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Cloud Computing & DevOps",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 24,
        "url": "https://swayam.gov.in/courses/nptel-cloud-devops",
    },
    {
        "title": "Relational Database Design and High-Performance SQL",
        "description": "Master SQL query optimization, transaction management (ACID), table partitioning, and indexing.",
        "source": "SWAYAM_NPTEL_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Database Architecture & SQL",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 20,
        "url": "https://swayam.gov.in/courses/nptel-db-sql",
    },
    {
        "title": "Applied Machine Learning and Predictive Analytics",
        "description": "End-to-end ML workflow: classification, regression, model evaluation, and deployment using scikit-learn.",
        "source": "SWAYAM_NPTEL_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Applied Machine Learning",
        "minimum_level": 1,
        "maximum_level": 4,
        "duration_hours": 36,
        "url": "https://swayam.gov.in/courses/nptel-ml-applied",
    },
    {
        "title": "Cybersecurity Foundations and Network Threat Defense",
        "description": "Security protocols, intrusion detection, cryptography basics, and ethical defense strategies.",
        "source": "SKILL_INDIA_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Cybersecurity & Network Defense",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 25,
        "url": "https://skillindiadigital.gov.in/courses/cyber-defense",
    },
    # HEALTHCARE
    {
        "title": "Primary Healthcare & Clinical Protocols for Community Officers",
        "description": "Evidence-based community clinical practice, preventive immunisation guidelines, and triage management.",
        "source": "SKILL_INDIA_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Public Health & Clinical Protocols",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 28,
        "url": "https://skillindiadigital.gov.in/courses/public-health-protocols",
    },
    {
        "title": "Clinical Laboratory Techniques & Quality Standards",
        "description": "Pathology diagnostics, reagent handling, microscope calibrations, and biosafety protocols.",
        "source": "SKILL_INDIA_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Medical Diagnostics & Lab Safety",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 22,
        "url": "https://skillindiadigital.gov.in/courses/medical-lab-tech",
    },
    {
        "title": "Healthcare Information Systems and Patient Data Ethics",
        "description": "EHR system workflows, telemedicine documentation, data privacy, and Ayushman Bharat Digital Mission (ABDM).",
        "source": "SWAYAM_NPTEL_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Healthcare Informatics",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 16,
        "url": "https://swayam.gov.in/courses/healthcare-informatics",
    },
    # FINANCE
    {
        "title": "Financial Accounting Standards, Ledger Audit & Reporting",
        "description": "Balance sheets, profit & loss accounting, auditing standards, and Indian Accounting Standards (Ind-AS).",
        "source": "SWAYAM_NPTEL_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Financial Accounting & Reporting",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 30,
        "url": "https://swayam.gov.in/courses/financial-accounting",
    },
    {
        "title": "Credit Risk Appraisal and Commercial Lending",
        "description": "Financial ratio analysis, working capital assessment, DSCR calculations, and credit underwriting.",
        "source": "SKILL_INDIA_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Credit Appraisal & Risk Assessment",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 20,
        "url": "https://skillindiadigital.gov.in/courses/credit-risk",
    },
    # AGRICULTURE
    {
        "title": "Sustainable Agronomy, Soil Fertility & Crop Nutrition",
        "description": "Soil testing methodologies, micronutrient balance, drip irrigation, and climate-smart agronomy.",
        "source": "SWAYAM_NPTEL_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Crop Science & Soil Health",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 26,
        "url": "https://swayam.gov.in/courses/crop-science",
    },
    # EDUCATION
    {
        "title": "Digital Pedagogy, Instructional Design & Modern Teaching",
        "description": "Interactive classroom methodologies, hybrid teaching, formative assessment, and educational technology.",
        "source": "SWAYAM_NPTEL_DEMO",
        "resource_type": "COURSE",
        "competency_name": "Pedagogy & Digital Learning Tools",
        "minimum_level": 1,
        "maximum_level": 3,
        "duration_hours": 18,
        "url": "https://swayam.gov.in/courses/digital-pedagogy",
    },
]

MULTI_SECTOR_DIAGNOSTIC_QUESTIONS = [
    # Software Engineering Principles
    {
        "competency_name": "Software Engineering Principles",
        "question": "What is the primary benefit of the Single Responsibility Principle (SRP) in software design?",
        "options": [
            "It eliminates the need for unit tests",
            "It ensures each class has only one reason to change, improving maintainability",
            "It makes the compiled binary execute faster",
            "It automatically optimizes database queries"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "SRP states that a class or module should have one, and only one, reason to change, making code modular and easier to maintain."
    },
    {
        "competency_name": "Software Engineering Principles",
        "question": "In continuous integration (CI), what is the main purpose of automated regression test suites?",
        "options": [
            "To replace human code reviews entirely",
            "To detect breaks and defects immediately upon merging new code commits",
            "To compress the application bundle for production",
            "To generate user documentation automatically"
        ],
        "correct_option": 1,
        "difficulty": "MEDIUM",
        "explanation": "Automated regression tests run on every commit or pull request to verify that existing features remain functional when new changes are added."
    },
    # Cloud Computing & DevOps
    {
        "competency_name": "Cloud Computing & DevOps",
        "question": "What is the key advantage of containerization with Docker compared to traditional virtual machines?",
        "options": [
            "Containers include a full guest operating system kernel",
            "Containers share the host kernel and are lightweight, starting up in seconds",
            "Containers cannot run on Linux servers",
            "Containers eliminate the need for networking"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "Containers virtualize at the OS level and share the host kernel, making them significantly more lightweight and fast to start than full VMs."
    },
    {
        "competency_name": "Cloud Computing & DevOps",
        "question": "What is the primary purpose of an Infrastructure as Code (IaC) tool like Terraform?",
        "options": [
            "To write front-end web pages using HTML and CSS",
            "To define, provision, and version cloud infrastructure deterministically using declarative files",
            "To monitor database query execution times in real time",
            "To automatically generate CSS media queries"
        ],
        "correct_option": 1,
        "difficulty": "MEDIUM",
        "explanation": "IaC allows infrastructure to be defined in code files, enabling automated, repeatable, and version-controlled provisioning."
    },
    # Database Architecture & SQL
    {
        "competency_name": "Database Architecture & SQL",
        "question": "What does the 'A' in ACID transaction properties stand for in relational databases?",
        "options": [
            "Authentication",
            "Atomicity (all operations succeed or none do)",
            "Asynchronous execution",
            "Aggregation"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "Atomicity ensures that a database transaction is treated as a single unit: either all statements execute successfully, or the entire transaction rolls back."
    },
    {
        "competency_name": "Database Architecture & SQL",
        "question": "Why is adding a B-Tree index on a frequently filtered column beneficial for SQL SELECT queries?",
        "options": [
            "It converts the table into a NoSQL database",
            "It reduces the query search complexity from O(N) full table scan to O(log N) tree traversal",
            "It automatically encrypts the column data",
            "It removes duplicate rows from the table"
        ],
        "correct_option": 1,
        "difficulty": "MEDIUM",
        "explanation": "B-Tree indexes allow the database engine to quickly locate matching rows in logarithmic time without scanning every row in the table."
    },
    # Applied Machine Learning
    {
        "competency_name": "Applied Machine Learning",
        "question": "What problem occurs when a machine learning model performs exceptionally well on training data but poorly on unseen test data?",
        "options": [
            "Underfitting",
            "Overfitting",
            "Feature scaling",
            "Data normalization"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "Overfitting happens when a model memorizes noise and specific details of the training set rather than learning generalizable patterns."
    },
    {
        "competency_name": "Applied Machine Learning",
        "question": "When evaluating a binary classifier on an imbalanced dataset (e.g., 99% negative, 1% positive), why is raw Accuracy misleading?",
        "options": [
            "Accuracy cannot be calculated on binary outcomes",
            "A naive model predicting always 'negative' achieves 99% accuracy while missing all true positive cases",
            "Accuracy is only defined for regression models",
            "Accuracy depends on the learning rate parameter"
        ],
        "correct_option": 1,
        "difficulty": "MEDIUM",
        "explanation": "On imbalanced data, high accuracy can be achieved by trivial majority-class prediction. Metrics like F1-score, Precision, and Recall are necessary."
    },
    # Cybersecurity & Network Defense
    {
        "competency_name": "Cybersecurity & Network Defense",
        "question": "What is the primary objective of Multi-Factor Authentication (MFA)?",
        "options": [
            "To make user passwords public",
            "To require two or more distinct authentication factors before granting access, mitigating credential theft",
            "To allow users to bypass login screens",
            "To increase network bandwidth"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "MFA strengthens security by requiring multiple independent pieces of evidence (something you know, something you have, or something you are)."
    },
    # Public Health & Clinical Protocols
    {
        "competency_name": "Public Health & Clinical Protocols",
        "question": "What is the primary purpose of triage in emergency and community healthcare?",
        "options": [
            "To bill patients before treatment",
            "To prioritize patients based on the clinical urgency and severity of their medical condition",
            "To assign hospital rooms in alphabetical order",
            "To schedule non-urgent medical checkups"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "Triage categorizes patients based on how urgently they require clinical intervention, ensuring critical conditions receive immediate care."
    },
    # Medical Diagnostics & Lab Safety
    {
        "competency_name": "Medical Diagnostics & Lab Safety",
        "question": "What is the purpose of standard calibration runs in clinical diagnostic analyzers?",
        "options": [
            "To clean the laboratory floors",
            "To verify measurement accuracy against verified reference standards and ensure consistent diagnostic results",
            "To store extra blood samples",
            "To generate patient invoices"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "Calibration aligns the analyzer's output to standard reference values, preventing erroneous diagnostic readings."
    },
    # Healthcare Informatics
    {
        "competency_name": "Healthcare Informatics",
        "question": "In digital health systems, why is interoperability between Electronic Health Record (EHR) platforms critical?",
        "options": [
            "It allows games to run on clinical monitors",
            "It enables seamless, secure sharing of patient health records across different hospitals and clinics",
            "It converts medical charts into printable flyers",
            "It replaces the need for doctors"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "Interoperability ensures that a patient's medical history can be accessed accurately and securely by authorized providers anywhere."
    },
    # Financial Accounting & Reporting
    {
        "competency_name": "Financial Accounting & Reporting",
        "question": "What is the fundamental accounting equation in financial reporting?",
        "options": [
            "Assets = Liabilities + Equity",
            "Assets = Revenue - Expenses",
            "Equity = Liabilities + Revenue",
            "Net Income = Assets + Liabilities"
        ],
        "correct_option": 0,
        "difficulty": "EASY",
        "explanation": "The fundamental accounting equation states that a company's total assets equal the sum of its liabilities and shareholders' equity."
    },
    # Credit Appraisal & Risk Assessment
    {
        "competency_name": "Credit Appraisal & Risk Assessment",
        "question": "What does a Debt Service Coverage Ratio (DSCR) below 1.0 indicate about a commercial borrower?",
        "options": [
            "The borrower has excess cash flow to cover debt obligations comfortably",
            "The borrower's operating income is insufficient to cover its current debt obligations",
            "The borrower is exempt from interest payments",
            "The loan has zero risk of default"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "A DSCR less than 1.0 means net operating income does not fully cover debt service, signaling heightened default risk."
    },
    # Crop Science & Soil Health
    {
        "competency_name": "Crop Science & Soil Health",
        "question": "What is the primary role of nitrogen (N) as an essential macronutrient in plant growth?",
        "options": [
            "It produces fruit color only",
            "It is a key building block for amino acids, proteins, and chlorophyll necessary for vegetative growth",
            "It prevents soil water evaporation",
            "It acts as a mechanical root barrier"
        ],
        "correct_option": 1,
        "difficulty": "EASY",
        "explanation": "Nitrogen is essential for synthesis of proteins, nucleic acids, and chlorophyll, driving vigorous leaf and stem development."
    },
    # Pedagogy & Digital Learning Tools
    {
        "competency_name": "Pedagogy & Digital Learning Tools",
        "question": "What distinguishes formative assessment from summative assessment in modern education?",
        "options": [
            "Formative assessment occurs during the learning process to guide ongoing instruction, while summative evaluates learning at the end",
            "Formative assessment is always graded with letter marks",
            "Summative assessment is conducted before classes begin",
            "Formative assessment is only used for university professors"
        ],
        "correct_option": 0,
        "difficulty": "EASY",
        "explanation": "Formative assessments provide real-time feedback during instruction to improve learning, whereas summative assessments evaluate competency achievement at completion."
    },
]
