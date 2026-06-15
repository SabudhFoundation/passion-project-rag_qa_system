from src.utils.groqclient import GroqClient,GroqClientError
class QueryDecompositionError(Exception):
    pass

class QueryDecomposer:
    def __init__(self):
        self.groq=GroqClient()
        
    def decompose(self,query:str) -> list[str]:
        try:
            prompt = f"""
        You are a query decomposition system.
        Rules:
        - If the query expresses ONE intent, return ONLY one question
        - Only split when the query clearly contains MULTIPLE distinct intents
        - Do NOT create redundant or overlapping questions
        - Maximum 3 sub-questions
        - Preserve original meaning
        - Do not add new information

        Return JSON only.

        Format:
        {{"questions": ["q1", "q2"]}}

        Query:
        "{query}"
        """
            result=self.groq.generate_json(prompt)
            if not isinstance(result,dict):
                return [query]
            if "questions" not in result:
                return [query] # if the returned json from groq has any other structure this will not break my code
            questions = result["questions"]
            if not isinstance(questions,list) or len(questions)==0:  #returns query as list if the groq retuned quesions as string instaed of list[str] or does not returned anything
                return [query]
            cleaned_questions=[]
            for q in questions:
                q=str(q).strip()
                if q:
                    cleaned_questions.append(q)
            if not cleaned_questions:
                return [query]
            return cleaned_questions
        
        except GroqClientError as e:
            raise QueryDecompositionError(f"Query decomposition failed: {str(e)}") 
        except Exception as e:
            raise QueryDecompositionError(f"Unexpected error in decomposition: {str(e)}")
            