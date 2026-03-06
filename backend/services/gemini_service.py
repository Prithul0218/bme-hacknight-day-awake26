from google.genai import Client
from google.genai.types import Part
import os
import asyncio
from functools import partial
from typing import Optional
from backend.prompts.templates import (
    build_department_report_prompt,
    build_financial_analysis_prompt,
    build_chat_question_prompt,
    build_studio_asset_prompt,
    build_document_summary_prompt,
)

class GeminiService:
    """Service for interacting with Google Gemini API"""

    # Try stable model names first, then fall back to models available for the key.
    PREFERRED_MODELS = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
    ]
    
    # Models with known vision/PDF support (for OCR)
    VISION_MODELS = [
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro-latest", 
        "gemini-exp-1114",
        "gemini-1.5-flash",
    ]
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        self.client = Client(api_key=api_key)

    async def _generate_content(self, prompt: str):
        """Generate content with model fallback to handle account/model availability differences."""
        loop = asyncio.get_event_loop()
        last_error = None

        for model_name in self.PREFERRED_MODELS:
            try:
                return await loop.run_in_executor(
                    None,
                    partial(
                        self.client.models.generate_content,
                        model=model_name,
                        contents=prompt,
                    ),
                )
            except Exception as e:
                last_error = e

        # If preferred models fail, discover available models and try those with generateContent support.
        try:
            model_list = await loop.run_in_executor(None, self.client.models.list)
            for model in model_list:
                model_name = getattr(model, "name", "")
                supported = getattr(model, "supported_actions", None) or getattr(
                    model, "supported_generation_methods", []
                )
                supports_generate = any(
                    method in ("generateContent", "generate_content") for method in supported
                )
                if not model_name or not supports_generate:
                    continue

                try:
                    clean_name = model_name.replace("models/", "")
                    return await loop.run_in_executor(
                        None,
                        partial(
                            self.client.models.generate_content,
                            model=clean_name,
                            contents=prompt,
                        ),
                    )
                except Exception as e:
                    last_error = e
                    continue
        except Exception as e:
            last_error = e

        raise RuntimeError(f"No usable Gemini model found for this API key: {last_error}")
    
    async def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """
        Extract text from PDF using Gemini's vision API with automatic OCR.
        This works for both text-based PDFs and image-based (scanned) PDFs.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text or None if extraction fails
        """
        import base64
        loop = asyncio.get_event_loop()
        
        try:
            # Read the PDF file
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
            
            # Encode to base64
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            # Create prompt for text extraction
            prompt = """Extract all text content from this PDF document. 
Include all text, tables, and any other readable content.
Preserve the structure and formatting where possible.
Keep tables as table format, like a markdown table.
If this is a scanned document with images of text, use OCR to extract the text."""
            
            # Use vision model with inline PDF data
            # Try vision-capable models specifically
            for model_name in self.VISION_MODELS:
                try:
                    # Create contents with inline PDF data and prompt
                    contents = [
                        Part(inline_data={'mime_type': 'application/pdf', 'data': pdf_base64}),
                        Part(text=prompt)
                    ]
                    
                    response = await loop.run_in_executor(
                        None,
                        lambda: self.client.models.generate_content(
                            model=model_name,
                            contents=contents
                        )
                    )
                    
                    print(f"✅ OCR successful with model: {model_name}")
                    return response.text
                    
                except Exception as e:
                    error_msg = str(e)
                    # Don't spam logs for quota/not-found errors
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        print(f"⚠️  Model {model_name}: Quota exceeded, trying next...")
                    elif "404" in error_msg or "NOT_FOUND" in error_msg:
                        print(f"ℹ️  Model {model_name}: Not available for PDF OCR")
                    else:
                        print(f"Error with model {model_name}: {e}")
                    continue
            
            print("⚠️  All OCR models failed or unavailable. This may be due to:")
            print("   - API quota limits (free tier has daily/minute limits)")
            print("   - Model availability for your API key")
            print("   - PDF format compatibility")
            return None
            
        except Exception as e:
            print(f"Error extracting text from PDF with Gemini: {e}")
            return None
    
    async def analyze_financial_document(self, content: str) -> str:
        """
        Analyze financial document content
        """
        prompt = build_financial_analysis_prompt(content)
        
        response = await self._generate_content(prompt)
        return response.text
    
    async def generate_department_report(
        self, 
        financial_data: str, 
        department: str,
        department_context: str
    ) -> dict:
        """
        Generate a department-specific report from financial data
        """
        prompt = build_department_report_prompt(
            financial_data=financial_data,
            department=department,
            department_context=department_context,
        )
        
        response = await self._generate_content(prompt)
        
        # Parse response - in production, you'd want more robust JSON parsing
        import json
        try:
            # Try to extract JSON from response
            text = response.text
            # Find JSON in the response (sometimes Gemini wraps it in markdown)
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            return json.loads(text.strip())
        except Exception as e:
            # Fallback if JSON parsing fails
            print(f"JSON parsing error: {e}")
            print(f"Response text: {response.text[:500]}")
            return {
                "summary": response.text[:200] if hasattr(response, 'text') else "Error generating summary",
                "key_insights": ["Unable to parse insights from AI response"],
                "metrics": {},
                "recommendations": []
            }

    async def answer_chat_question(
        self,
        financial_data: str,
        question: str,
        department_focus: str,
    ) -> str:
        """Answer a free-form user question grounded in uploaded financial data."""
        prompt = build_chat_question_prompt(
            financial_data=financial_data,
            question=question,
            department_focus=department_focus,
        )
        response = await self._generate_content(prompt)
        return response.text

    async def generate_studio_asset(
        self,
        financial_data: str,
        asset_type: str,
        department: str,
        custom_prompt: str,
    ) -> str:
        """Generate a non-chat artifact in Studio mode (brief, email, outline, etc.)."""
        prompt = build_studio_asset_prompt(
            financial_data=financial_data,
            asset_type=asset_type,
            department=department,
            custom_prompt=custom_prompt,
        )
        response = await self._generate_content(prompt)
        return response.text

    async def generate_document_summary(self, content: str) -> str:
        """Generate a concise summary of a document for storage."""
        # Log the content being summarized for debugging
        # console.log(f"Generating summary for content (first 500 chars): {content[:500]}")
        prompt = build_document_summary_prompt(content)
        response = await self._generate_content(prompt)
        return response.text
