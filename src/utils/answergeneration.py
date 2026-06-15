from src.utils.groqclient import GroqClient,GroqClientError
class AnswerGenerationError(Exception):
    pass
class AnswerGenerator:
    
    def __init__(self,groq_client: GroqClient):
        self.groq = groq_client
    def generate_answer(self,query: str,context: str) -> str:
        try:
            system_prompt = """
            You are a helpful AI assistant.

            Answer the user's question ONLY using the provided context.

            Do not use outside knowledge.

            If the answer cannot be found in the context, say:
            'I could not find the answer in the provided documents.'

            Give clear and concise answers.
            """

            user_prompt = f"""
            ================ QUESTION ================

            {query}

            ================ CONTEXT ================

            {context}

            ================ ANSWER ================
            """

            answer = self.groq.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            return answer
        except Exception as e:
            raise AnswerGenerationError(
                f"Answer generation failed: {str(e)}"
            )

   