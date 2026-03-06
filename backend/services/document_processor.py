import pdfplumber
import pandas as pd
import openpyxl
from typing import Dict, Any, Optional

class DocumentProcessor:
    """Service for processing various document formats"""
    
    def __init__(self, gemini_service=None):
        """
        Initialize processor with optional Gemini service for advanced PDF processing.
        
        Args:
            gemini_service: Optional GeminiService instance for OCR capabilities
        """
        self.gemini_service = gemini_service
    
    async def process_file(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        Process uploaded file and extract content
        """
        if file_type == '.pdf':
            return await self._process_pdf(file_path)
        elif file_type in ['.xlsx', '.xls']:
            return self._process_excel(file_path)
        elif file_type == '.csv':
            return self._process_csv(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    async def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF using pdfplumber first, then Gemini OCR if needed.
        This handles both regular text PDFs and image-based (scanned) PDFs.
        """
        text_content = []
        tables = []
        
        # First try pdfplumber (fast for text-based PDFs)
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    # Extract text
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                    
                    # Extract tables
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
        except Exception as e:
            print(f"pdfplumber extraction error: {e}")
        
        full_text = "\n\n".join(text_content)
        
        # If we got minimal or no text, try Gemini with OCR
        # This handles scanned PDFs or PDFs with images of text
        if len(full_text.strip()) < 100 and self.gemini_service:
            print(f"PDF has minimal text ({len(full_text)} chars), attempting Gemini OCR...")
            try:
                gemini_text = await self.gemini_service.extract_text_from_pdf(file_path)
                
                if gemini_text and len(gemini_text.strip()) > len(full_text.strip()):
                    print(f"✅ Gemini OCR successful, extracted {len(gemini_text)} chars")
                    full_text = gemini_text
                else:
                    print(f"⚠️  Gemini OCR didn't improve extraction. Using pdfplumber result.")
                    
            except Exception as e:
                print(f"⚠️  Gemini OCR error: {e}")
                print(f"ℹ️  Note: Gemini OCR requires available API quota. Using pdfplumber result.")
                # Fall back to pdfplumber text even if minimal
        
        return {
            "type": "pdf",
            "text": full_text,
            "tables": tables,
            "summary": full_text[:1000] + "..." if len(full_text) > 1000 else full_text
        }
    
    def _process_excel(self, file_path: str) -> Dict[str, Any]:
        """Extract data from Excel file"""
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        sheets_data = {}
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            sheets_data[sheet_name] = df.to_dict('records')
        
        # Create text summary
        text_parts = []
        for sheet_name, data in sheets_data.items():
            text_parts.append(f"Sheet: {sheet_name}")
            df = pd.DataFrame(data)
            text_parts.append(df.to_string())
        
        full_text = "\n\n".join(text_parts)
        
        return {
            "type": "excel",
            "sheets": sheets_data,
            "text": full_text,
            "summary": full_text[:1000] + "..." if len(full_text) > 1000 else full_text
        }
    
    def _process_csv(self, file_path: str) -> Dict[str, Any]:
        """Extract data from CSV file"""
        df = pd.read_csv(file_path)
        
        text = df.to_string()
        
        return {
            "type": "csv",
            "data": df.to_dict('records'),
            "text": text,
            "summary": text[:1000] + "..." if len(text) > 1000 else text
        }
