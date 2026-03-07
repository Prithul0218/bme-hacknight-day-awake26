"""Central place for all LLM prompts.

Edit prompts here without touching service logic.
"""

DEPARTMENT_CONTEXTS = {
    "engineering": """
Engineering cares about:
- Infrastructure and cloud costs (AWS, Azure, GCP)
- Software licenses and tools (GitHub, IDEs, monitoring)
- R&D spending and innovation budget
- Team size and hiring costs
- Hardware and equipment expenses
- Technical debt and optimization opportunities
Focus on technical efficiency and resource allocation.
""",
    "sales": """
Sales cares about:
- Commission expenses and sales compensation
- Customer Acquisition Cost (CAC)
- Revenue per sales rep
- Territory performance and regional breakdown
- Sales tools and CRM costs
- Travel and entertainment expenses
- Pipeline value and conversion rates
Focus on revenue generation and sales efficiency.
""",
    "marketing": """
Marketing cares about:
- Campaign spending by channel (digital, content, events)
- Customer Acquisition Cost (CAC)
- Marketing ROI and ROAS
- Brand and advertising expenses
- Marketing tools and software (ads platforms, analytics)
- Agency and contractor costs
- Lead generation costs
Focus on marketing efficiency and customer acquisition.
""",
    "hr": """
HR cares about:
- Total payroll and compensation
- Benefits costs (health insurance, 401k, perks)
- Recruitment and hiring expenses
- Employee turnover costs
- Training and development budget
- HR systems and tools
- Headcount by department
Focus on people costs and workforce planning.
""",
    "operations": """
Operations cares about:
- Vendor and supplier spending
- Office and facilities costs
- Supply chain expenses
- Operational efficiency metrics
- Equipment and maintenance
- Logistics and shipping costs
- Process optimization opportunities
Focus on operational efficiency and cost management.
""",
    "executive": """
Executive leadership cares about:
- Overall profitability and margins
- Cash flow and runway
- Revenue trends and growth rate
- Major cost categories
- Strategic investments
- Financial health indicators
- Burn rate and sustainability
Focus on strategic financial health and business performance.
""",
}


def build_financial_analysis_prompt(content: str) -> str:
    return f"""
You are a financial analyst AI. Analyze the following financial document and provide:
1. A brief summary of the financial data
2. Key financial metrics identified
3. Notable trends or patterns (none of your own recommendations)

Document content:
{content}

Provide a structured analysis.
"""


def build_department_report_prompt(
    financial_data: str,
    department: str,
    department_context: str,
) -> str:
    return f"""
You are translating financial data into actionable insights for the {department.upper()} department.

Financial Data:
{financial_data}

Department Context:
{department_context}

Generate a report with:
1. Executive Summary (2-3 sentences specific to {department})
2. Key Insights (3-5 bullet points most relevant to {department})
3. Key Metrics (extract 3-5 specific numbers/percentages that matter to {department})
4. Minor Recommendations (2-3 actionable suggestions for {department}, but keep it brief and try not to add your own recommendations unless they are very obvious from the data)

Format your response as JSON with keys: summary, key_insights (array), metrics (object), recommendations (array)
Focus ONLY on what matters to the {department} department. Use their language and priorities.
"""


def build_chat_question_prompt(
    financial_data: str,
    question: str,
    department_focus: str,
) -> str:
    return f"""
You are a finance intelligence assistant for business teams. 

Financial Data:
{financial_data}

Question:
{question}

Department Focus:
{department_focus}

Instructions:
- Answer directly and clearly.
- Use only data-grounded statements.
- If a data point is missing, say what is missing.
- Keep the answer concise but useful.
"""


def build_studio_asset_prompt(
    financial_data: str,
    asset_type: str,
    department: str,
    custom_prompt: str,
) -> str:
    return f"""
You are a finance content studio assistant.

Financial Data:
{financial_data}

Requested Asset Type: {asset_type}
Target Department: {department}
Custom Instructions: {custom_prompt}

Create a polished artifact that is ready to share internally.

Guidelines by asset type:
- department_report: concise department-oriented report with summary, key insights, metrics, and actions.
- executive_brief: leadership-level brief focused on risk, opportunity, and strategic implications.
- email_draft: clear internal email draft with subject and body.
- infographic_outline: structured infographic blueprint with sections, key numbers, and visual suggestions.
- slide_outline: 6-8 slide outline with title + bullet points per slide.

Return plain text only.
"""


def build_document_summary_prompt(content: str) -> str:
    """Build a prompt for generating a concise document summary"""
    return f"""
You are a financial document summarizer. Create a concise yet comprehensive summary of the following document.

Document Content:
{content}

Guidelines:
- If there is a table, keep a table in csv format instead of converting it to paragraph, but make it concise
- Preserve all key financial metrics, numbers, and dates
- Include major findings, trends, and conclusions
- Keep essential context and department-specific information
- Maintain functional tone thats concise but information dense
- Aim for 1 paragraph (200-400 words)
- Ensure the summary is detailed enough to answer questions about the document

Return only the summary text, no additional formatting or commentary.
"""
