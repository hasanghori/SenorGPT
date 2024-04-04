from openai import OpenAI
import time

class AI_Assistant:
    def __init__(self, openai_key):
        self.openai_key = openai_key
        self.client = OpenAI(api_key=self.openai_key)

    def generate_teaching_plan(self, language, level, message):
        basic_prompt = """You are an AI that is optimized for creating very detailed guides for learning languages. Detail the necessary vocabulary and aspects that a user needs to become fluent. Focus on what the AI should teach through text messages over the next 1 week."""
        prompt = f"Given the user is trying to learn {language}, is at the {level} level, and describes their language ability as: '{message}', generate a one-week lesson plan."
        # Use OpenAI API to generate response based on the prompt
        # Example placeholder response
        return "This is a placeholder for the generated teaching plan."

    def generate_gpt_message(self, from_number, incoming_msg, daily_plan):
        # Placeholder: Implement your logic for generating responses using GPT
        return "This is a placeholder response. Implement based on your app's logic."
    
    def call_gpt_4(self, prompt):
        time.sleep(1.00)

        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-4-0125-preview",
        )
        return chat_completion.choices[0].message.content

    def call_gpt_3(self, prompt):

        time.sleep(1.00)

        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-3.5-turbo-0125",
        )
        return chat_completion.choices[0].message.content



