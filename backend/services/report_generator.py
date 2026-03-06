from typing import List, Dict, Any
from backend.models.schemas import Department, DepartmentReport
from backend.services.gemini_service import GeminiService
from backend.prompts.templates import DEPARTMENT_CONTEXTS

class ReportGenerator:
    """Service for generating department-specific reports"""
    
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service
    
    async def generate_reports(
        self, 
        document_content: Dict[str, Any],
        departments: List[Department]
    ) -> List[DepartmentReport]:
        """
        Generate reports for specified departments
        """
        reports = []
        financial_text = document_content.get("text", "")
        
        for department in departments:
            context = DEPARTMENT_CONTEXTS.get(department.value, "")
            
            # Generate department-specific report using Gemini
            report_data = await self.gemini_service.generate_department_report(
                financial_text,
                department.value,
                context
            )
            
            # Create DepartmentReport object
            report = DepartmentReport(
                department=department,
                summary=report_data.get("summary", "No summary available"),
                key_insights=report_data.get("key_insights", []),
                metrics=report_data.get("metrics", {}),
                recommendations=report_data.get("recommendations", [])
            )
            
            reports.append(report)
        
        return reports
