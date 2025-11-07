import os
import json
from typing import Dict, Any
from openai import AsyncOpenAI
import asyncio

class GPTService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"
    
    async def analyze_resume_async(
        self, 
        resume_text: str, 
        job_description: str
    ) -> Dict[str, Any]:
        """Analyze resume using GPT-4o mini asynchronously"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert HR recruiter. Analyze the resume against the job description and provide:
1. A score from 0-10 (10 being perfect match)
2. A brief explanation of why the candidate was/wasn't shortlisted
3. Key strengths and weaknesses

Return your response in this exact JSON format:
{
    "score": 7.5,
    "explanation": "Brief explanation of the decision",
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"]
}"""
                    },
                    {
                        "role": "user",
                        "content": f"""Job Description:
{job_description}

Resume:
{resume_text[:3000]}

Analyze this resume against the job description and provide your assessment."""
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            analysis = json.loads(result)
            
            return {
                "score": float(analysis.get("score", 0)),
                "explanation": analysis.get("explanation", "No explanation provided"),
                "strengths": analysis.get("strengths", []),
                "weaknesses": analysis.get("weaknesses", [])
            }
        except json.JSONDecodeError as json_error:
            print(f"GPT Analysis: JSON parsing failed: {json_error}")
            print(f"GPT Analysis: Raw response: {result}")
            return {
                "score": 5.0,
                "explanation": "Unable to parse detailed analysis",
                "strengths": [],
                "weaknesses": []
            }
        except Exception as e:
            print(f"Error in GPT analysis: {e}")
            import traceback
            traceback.print_exc()
            return {
                "score": 0.0,
                "explanation": "Error occurred during analysis",
                "strengths": [],
                "weaknesses": []
            }
    
    async def analyze_resumes_batch(
        self,
        resumes: list,
        job_description: str,
        max_concurrent: int = 5
    ) -> list:
        """Analyze multiple resumes in parallel with concurrency limit"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_limit(resume_data: Dict[str, str]):
            async with semaphore:
                return await self.analyze_resume_async(
                    resume_data['text'],
                    job_description
                )
        
        tasks = [analyze_with_limit(resume) for resume in resumes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error processing resume {i}: {result}")
                processed_results.append({
                    "score": 0.0,
                    "explanation": f"Error: {str(result)}",
                    "strengths": [],
                    "weaknesses": []
                })
            else:
                processed_results.append(result)
        
        return processed_results

# Global instance
gpt_service = GPTService()

