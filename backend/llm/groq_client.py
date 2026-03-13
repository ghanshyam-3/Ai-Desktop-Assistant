import os
from groq import Groq

class GroqClient:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Error: GROQ_API_KEY not found in environment.")
        self.client = Groq(api_key=api_key)

    def transcribe(self, audio_file_path, prompt=None):
        """
        Transcribes audio file using Groq Whisper.
        """
        try:
            with open(audio_file_path, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(audio_file_path, file.read()),
                    model="whisper-large-v3",
                    prompt=prompt, # Add prompt for phrase biasing
                    response_format="json",
                    language="en",
                    temperature=0.0
                )
            text = transcription.text.strip()
            
            # Filter common Whisper hallucinations strings
            hallucinations = [
                "Thank you.", "You're welcome.", 
                "MBC News", "Copyright", 
                "Amara.org", "Uncredited"
            ]
            
            for h in hallucinations:
                if h.lower() in text.lower():
                    return ""
            
            return text
        except Exception as e:
            print(f"Transcription Error: {e}")
            return ""

    def process_intent(self, chat_history, system_prompt):
        """
        Sends conversation history to Llama 3 70B for intent classification.
        """
        try:
            messages = [{"role": "system", "content": system_prompt}] + chat_history
            
            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant", # Faster model for latency
                messages=messages,
                temperature=0.1, # Keep low for JSON
                max_tokens=512, 
                top_p=1,
                stop=None,
                response_format={"type": "json_object"}, # FORCE JSON
                stream=False
            )
            content = completion.choices[0].message.content
            print(f"LLM Raw Output: {content}") # Debugging
            return content
        except Exception as e:
            print(f"LLM Error: {e}")
            return "{}"

    def analyze_image(self, prompt, image_path):
        """
        Analyzes an image using Llama 3.2 Vision.
        """
        import base64
        
        def encode_image(image_path):
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')

        try:
            base64_image = encode_image(image_path)
            
            completion = self.client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                temperature=0.5,
                max_tokens=1024,
                top_p=1,
                stream=False,
                stop=None,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Vision Error: {e}")
            if "model_decommissioned" in str(e):
                return "The Vision model is currently unavailable (Decommissioned). I cannot see the screen right now."
            return "I couldn't analyze the screen."

    def get_chat_completion(self, chat_history, system_prompt=None):
        """
        Simple chat completion for general conversation fallback.
        """
        try:
            messages = chat_history
            if system_prompt:
                messages = [{"role": "system", "content": system_prompt}] + chat_history
                
            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=0.7,
                max_tokens=200,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Chat Error: {e}")
            return "I'm having trouble thinking right now."
