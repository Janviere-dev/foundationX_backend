#!/usr/bin/env python3

mathematics = {
    "Numbers": [
        "Integers",
        "Fractions",
        "Decimals",
        "Percentages",
        "Ratio and Proportion",
        "Indices",
        "Surds",
        "Logarithms",
    ],
    "Algebra": [
        "Algebraic Expressions",
        "Linear Equations",
        "Quadratic Equations",
        "Simultaneous Equations",
        "Inequalities",
        "Polynomials",
        "Sequences",
        "Series",
    ],
    "Functions": [
        "Linear Functions",
        "Quadratic Functions",
        "Exponential Functions",
        "Logarithmic Functions",
        "Inverse Functions",
    ],
    "Geometry": [
        "Angles",
        "Triangles",
        "Circles",
        "Polygons",
        "Coordinate Geometry",
        "Transformations",
        "Congruence",
        "Similarity",
    ],
    "Trigonometry": [
        "Trigonometric Ratios",
        "Sine Rule",
        "Cosine Rule",
        "Identities",
        "Bearings",
    ],
    "Statistics": [
        "Data Collection",
        "Frequency Tables",
        "Mean",
        "Median",
        "Mode",
        "Variance",
        "Standard Deviation",
        "Histograms",
    ],
    "Probability": [
        "Sample Space",
        "Tree Diagrams",
        "Conditional Probability",
    ],
    "Vectors": [
        "Vector Addition",
        "Scalar Product",
        "Magnitude",
    ],
    "Matrices": [
        "Matrix Operations",
        "Determinants",
        "Inverse Matrix",
    ],
    "Calculus": [
        "Limits",
        "Differentiation",
        "Applications of Differentiation",
        "Integration",
        "Applications of Integration",
    ],
}

physics = {
    "Measurement": [
        "SI Units",
        "Errors and Uncertainty",
        "Scientific Notation",
    ],
    "Mechanics": [
        "Motion",
        "Velocity",
        "Acceleration",
        "Newton's Laws",
        "Momentum",
        "Circular Motion",
        "Gravitation",
    ],
    "Energy": [
        "Work",
        "Power",
        "Kinetic Energy",
        "Potential Energy",
        "Conservation of Energy",
    ],
    "Waves": [
        "Wave Properties",
        "Sound",
        "Light",
        "Reflection",
        "Refraction",
        "Diffraction",
        "Interference",
    ],
    "Electricity": [
        "Electric Current",
        "Voltage",
        "Resistance",
        "Ohm's Law",
        "Series Circuits",
        "Parallel Circuits",
    ],
    "Magnetism": [
        "Magnetic Fields",
        "Electromagnetism",
        "Motors",
        "Generators",
    ],
    "Thermal Physics": [
        "Heat",
        "Heat Transfer",
        "Gas Laws",
        "Thermodynamics",
    ],
    "Modern Physics": [
        "Atomic Structure",
        "Radioactivity",
        "Nuclear Physics",
        "Semiconductors",
    ],
}

chemistry = {
    "Atomic Structure": [
        "Atoms",
        "Subatomic Particles",
        "Electron Configuration",
        "Isotopes",
    ],
    "Periodic Table": [
        "Groups",
        "Periods",
        "Periodic Trends",
    ],
    "Chemical Bonding": [
        "Ionic Bonding",
        "Covalent Bonding",
        "Metallic Bonding",
    ],
    "Chemical Reactions": [
        "Balancing Equations",
        "Stoichiometry",
        "Reaction Rates",
        "Redox Reactions",
    ],
    "States of Matter": [
        "Solids",
        "Liquids",
        "Gases",
        "Gas Laws",
    ],
    "Acids and Bases": [
        "pH",
        "Indicators",
        "Neutralization",
        "Titration",
    ],
    "Organic Chemistry": [
        "Hydrocarbons",
        "Alcohols",
        "Carboxylic Acids",
        "Esters",
        "Polymers",
    ],
    "Electrochemistry": [
        "Electrolysis",
        "Electrochemical Cells",
        "Corrosion",
    ],
}

biology = {
    "Cell Biology": [
        "Cell Structure",
        "Cell Division",
        "Microscopy",
    ],
    "Classification": [
        "Kingdoms",
        "Taxonomy",
        "Biodiversity",
    ],
    "Human Physiology": [
        "Digestive System",
        "Respiratory System",
        "Circulatory System",
        "Nervous System",
        "Endocrine System",
        "Excretory System",
    ],
    "Plant Biology": [
        "Photosynthesis",
        "Transport in Plants",
        "Plant Reproduction",
        "Tropisms",
    ],
    "Genetics": [
        "DNA",
        "Genes",
        "Inheritance",
        "Mutation",
    ],
    "Evolution": [
        "Natural Selection",
        "Adaptation",
        "Speciation",
    ],
    "Ecology": [
        "Ecosystems",
        "Food Chains",
        "Food Webs",
        "Conservation",
    ],
}

english = {
    "Grammar": [
        "Parts of Speech",
        "Tenses",
        "Active and Passive Voice",
        "Direct and Indirect Speech",
        "Sentence Structure",
    ],
    "Reading": [
        "Comprehension",
        "Inference",
        "Vocabulary in Context",
    ],
    "Writing": [
        "Paragraph Writing",
        "Essay Writing",
        "Letters",
        "Reports",
        "Creative Writing",
    ],
    "Literature": [
        "Poetry",
        "Drama",
        "Short Stories",
        "Literary Devices",
    ],
    "Communication": [
        "Listening",
        "Speaking",
        "Presentations",
        "Debates",
    ],
}

computer_science = {
    "Computer Fundamentals": [
        "Computer Components",
        "Hardware",
        "Software",
        "Operating Systems",
    ],
    "Productivity Tools": [
        "Microsoft Word",
        "Excel",
        "PowerPoint",
    ],
    "Programming": [
        "Algorithms",
        "Flowcharts",
        "Python",
        "Java",
        "Problem Solving",
    ],
    "Databases": [
        "Database Concepts",
        "SQL",
        "Normalization",
    ],
    "Networking": [
        "Internet",
        "Network Types",
        "Protocols",
        "Network Security",
    ],
    "Web Development": [
        "HTML",
        "CSS",
        "JavaScript",
    ],
}

history = {
    "Ancient Civilizations": [
        "Ancient Egypt",
    ],
    "African History": [
        "Kingdom of Rwanda",
        "Colonialism in Africa",
        "African Independence",
    ],
    "World History": [
        "World War I",
        "World War II",
    ],
    "History of Rwanda": [
        "Pre-colonial Rwanda",
        "Colonial Rule",
        "Independence",
        "The 1994 Genocide against the Tutsi",
        "National Unity and Reconciliation",
    ],
    "Civics": [
        "Citizenship",
        "Democracy",
    ],
}

geography = {
    "Physical Geography": [
        "Earth Structure",
        "Landforms",
        "Rocks",
        "Weathering",
        "Volcanoes",
        "Earthquakes",
    ],
    "Climate": [
        "Weather",
        "Climate",
        "Climate Change",
        "Rainfall",
        "Temperature",
    ],
    "Population": [
        "Population Growth",
        "Migration",
        "Urbanization",
        "Settlement",
    ],
    "Economic Geography": [
        "Agriculture",
        "Mining",
        "Industry",
        "Trade",
        "Transport",
        "Tourism",
    ],
    "Environmental Geography": [
        "Natural Resources",
        "Environmental Conservation",
        "Pollution",
        "Sustainable Development",
    ],
    "Map Work": [
        "Map Reading",
        "Topographic Maps",
        "Scale",
        "Grid References",
        "GIS",
    ],
}

economics = {
    "Introduction to Economics": [
        "Scarcity",
        "Choice",
        "Opportunity Cost",
        "Economic Systems",
    ],
    "Microeconomics": [
        "Demand",
        "Supply",
        "Elasticity",
        "Consumer Behaviour",
    ],
    "Macroeconomics": [
        "Inflation",
        "Economic Growth",
    ],
    "Money and Banking": [
        "Functions of Money",
        "Monetary Policy",
    ],
    "International Economics": [
        "International Trade",
        "Exchange Rates",
        "Balance of Payments",
        "Globalization",
    ],
}

accounting = {
    "Accounting Fundamentals": [
        "Accounting Principles",
        "Users of Accounting",
        "Accounting Equation",
    ],
    "Double Entry": [
        "Debit",
        "Credit",
        "Journals",
        "Ledgers",
    ],
    "Books of Accounts": [
        "Cash Book",
        "Sales Journal",
        "Purchases Journal",
        "General Ledger",
    ],
    "Financial Statements": [
        "Trial Balance",
        "Income Statement",
        "Balance Sheet",
        "Cash Flow Statement",
    ],
    "Adjustments": [
        "Depreciation",
        "Accruals",
        "Prepayments",
        "Bad Debts",
    ],
    "Business Accounts": [
        "Partnership Accounts",
        "Company Accounts",
        "Manufacturing Accounts",
    ],
}

entrepreneurship = {
    "Entrepreneurship Basics": [
        "Entrepreneur",
        "Characteristics of Entrepreneurs",
        "Business Ideas",
        "Innovation",
    ],
    "Business Planning": [
        "Business Plan",
        "Market Research",
        "Feasibility Study",
    ],
    "Marketing": [
        "Marketing Mix",
        "Branding",
        "Pricing",
        "Promotion",
    ],
    "Business Finance": [
        "Sources of Capital",
        "Budgeting",
        "Financial Management",
    ],
    "Business Operations": [
        "Production",
        "Customer Service",
        "Business Ethics",
        "Risk Management",
    ],
    "Business Growth": [
        "Expansion",
        "Franchising",
        "E-commerce",
    ],
}

french = {
    "Grammar": [
        "Articles",
        "Pronouns",
        "Verb Conjugation",
        "Tenses",
        "Sentence Structure",
    ],
    "Vocabulary": [
        "Daily Life",
        "Education",
        "Travel",
    ],
    "Communication": [
        "Listening",
        "Speaking",
        "Reading",
        "Writing",
    ],
}

kinyarwanda = {
    "Grammar": [
        "Nouns",
        "Verbs",
        "Sentence Structure",
        "Parts of Speech",
    ],
    "Vocabulary": [
        "Daily Communication",
        "Traditional Vocabulary",
        "Modern Vocabulary",
    ],
    "Literature": [
        "Poetry",
        "Proverbs",
        "Folktales",
    ],
    "Writing": [
        "Composition",
        "Essays",
        "Reports",
    ],
    "Communication": [
        "Listening",
        "Speaking",
        "Reading",
    ],
}

leadership_and_self_development = {
    "Self Awareness": [
        "Personal Values",
        "Strengths",
        "Weaknesses",
        "Growth Mindset",
    ],
    "Leadership": [
        "Leadership Styles",
        "Vision",
        "Decision Making",
        "Influence",
    ],
    "Communication": [
        "Public Speaking",
        "Listening Skills",
        "Conflict Resolution",
    ],
    "Emotional Intelligence": [
        "Self Management",
        "Empathy",
        "Relationships",
    ],
    "Teamwork": [
        "Collaboration",
        "Delegation",
        "Problem Solving",
    ],
    "Career Development": [
        "Goal Setting",
        "Time Management",
    ],
}

finance = {
    "Financial Literacy": [
        "Income",
        "Expenses",
        "Budgeting",
        "Saving",
    ],
    "Banking": [
        "Bank Accounts",
        "Loans",
        "Interest",
        "Credit",
    ],
    "Investing": [
        "Stocks",
        "Bonds",
        "Mutual Funds",
        "Risk and Return",
    ],
    "Personal Finance": [
        "Emergency Fund",
        "Retirement Planning",
        "Insurance",
    ],
    "Business Finance": [
        "Capital",
        "Cash Flow",
        "Financial Statements",
    ],
}

psychology = {
    "Introduction to Psychology": [
        "History of Psychology",
        "Branches of Psychology",
    ],
    "Human Development": [
        "Child Development",
        "Adolescence",
        "Adult Development",
    ],
    "Learning": [
        "Learning Theories",
        "Memory",
        "Motivation",
    ],
    "Personality": [
        "Personality Theories",
        "Individual Differences",
    ],
    "Mental Health": [
        "Stress",
        "Anxiety",
        "Well-being",
        "Resilience",
    ],
    "Social Psychology": [
        "Attitudes",
        "Group Behaviour",
        "Communication",
    ],
}

backend_engineering = {
    "Programming Fundamentals": [
        "Variables",
        "Data Types",
        "Control Flow",
        "Functions",
        "Object-Oriented Programming",
    ],
    "Python": [
        "Modules",
        "Packages",
        "Virtual Environments",
        "Type Hints",
    ],
    "APIs": [
        "REST APIs",
        "HTTP Methods",
        "Status Codes",
        "JSON",
    ],
    "FastAPI": [
        "Routing",
        "Dependency Injection",
        "Pydantic",
        "Authentication",
        "Background Tasks",
    ],
    "Databases": [
        "SQL",
        "MongoDB",
        "ORMs",
        "Database Design",
    ],
    "Authentication": [
        "JWT",
        "OAuth",
        "Password Hashing",
    ],
    "Deployment": [
        "Docker",
    ],
}

agentic_ai = {
    "LLM Fundamentals": [
        "Large Language Models",
        "Prompt Engineering",
        "Tokenization",
        "Embeddings",
    ],
    "LangChain": [
        "Chains",
        "Agents",
        "Tools",
        "Memory",
        "Runnables",
    ],
    "Retrieval-Augmented Generation": [
        "Document Loaders",
        "Chunking",
        "Vector Databases",
        "Retrieval",
        "Reranking",
    ],
    "Vector Databases": [
        "Qdrant",
        "FAISS",
        "Pinecone",
        "Embeddings Search",
    ],
    "AI Agents": [
        "Planning",
        "Reasoning",
        "Tool Calling",
        "Multi-Agent Systems",
    ],
    "Evaluation": [
        "Hallucination Detection",
        "Prompt Evaluation",
        "RAG Evaluation",
    ],
    "Deployment": [
        "FastAPI Integration",
        "Docker",
        "Monitoring",
        "Production Best Practices",
    ],
}


def get_all_subjects() -> list[dict]:
    """Return every subject as one dict of {"subject": ..., "topics": {...}}."""
    return [
        {"subject": "Mathematics", "topics": mathematics},
        {"subject": "Physics", "topics": physics},
        {"subject": "Chemistry", "topics": chemistry},
        {"subject": "Biology", "topics": biology},
        {"subject": "English", "topics": english},
        {"subject": "Computer Science", "topics": computer_science},
        {"subject": "History", "topics": history},
        {"subject": "Geography", "topics": geography},
        {"subject": "Economics", "topics": economics},
        {"subject": "Accounting", "topics": accounting},
        {"subject": "Entrepreneurship", "topics": entrepreneurship},
        {"subject": "French", "topics": french},
        {"subject": "Kinyarwanda", "topics": kinyarwanda},
        {"subject": "Leadership and Self-Development", "topics": leadership_and_self_development},
        {"subject": "Finance", "topics": finance},
        {"subject": "Psychology", "topics": psychology},
        {"subject": "Backend Engineering", "topics": backend_engineering},
        {"subject": "Agentic AI (LangChain)", "topics": agentic_ai},
    ]
