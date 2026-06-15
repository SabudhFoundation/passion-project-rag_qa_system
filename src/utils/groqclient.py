import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class GroqClientError(Exception):
    pass

class GroqClient:
    
    def __init__(self):
        api_key=os.getenv("GROQ_API_KEY")
        if not api_key:
            raise GroqClientError("GROQ_API_KEY not found in .env file")
        self.client=Groq(
            api_key=api_key
        )
        self.model="llama-3.3-70b-versatile"
        
    #give question,get answer simple
    def generate(self,prompt:str) -> str:
        
        try:
            response=self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                
            )
            content = response.choices[0].message.content
            if not content:
                raise GroqClientError("Empty response from Groq")
            return content.strip()
        except Exception as e:
            raise GroqClientError(f"Groq generation failed: {str(e)}")
    
    def generate_json(self,prompt:str) -> dict:
        
        try:
            print("Sending request to Groq...")
            response=self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type":"json_object"},
                temperature=0.0
            )
            print("Received response from Groq")
            raw = response.choices[0].message.content
            if not raw:
                raise GroqClientError("Empty JSON response from Groq")
            
            return json.loads(raw) #converting text to pyhton dictionary
        
        except json.JSONDecodeError as e:   #extra text before { breaks load function so we catch error here
            raise GroqClientError(f"Groq returned invalid JSON: {str(e)}")
        except Exception as e:
            raise GroqClientError(f"Groq JSON generation failed: {str(e)}")
        
    def generate_with_system(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt}
                ],
                temperature=0.0,
            )
            content = response.choices[0].message.content
            if not content:
                raise GroqClientError("Empty response from Groq")
            return content.strip()

        except Exception as e:
            raise GroqClientError(f"Groq system generation failed: {str(e)}")
        