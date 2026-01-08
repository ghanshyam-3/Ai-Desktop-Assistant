import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Chat History Storage
CHAT_HISTORY = []

def parse_command(command_text: str):
    """
    Sends the user command to Groq (Llama 3) via Raw HTTP and expects a JSON response.
    """
    print(f"DEBUG: Parse Command called with: {command_text}")
    
    if not api_key:
        print("Error: GROQ_API_KEY not found in .env")
        return [{"service": "error", "message": "Groq API Key Missing"}]

    # Groq uses OpenAI-compatible endpoint
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    # System Prompt
    system_prompt = """
    You are AI-assistant, a highly intelligent and helpful Desktop Assistant Orchestrator.
    
    CAPABILITIES:
    1. System Automation: Open apps, type text, manage files.
    2. Browser Automation: Open URLs, search Google, send WhatsApp messages.
    3. Conversational Intelligence: Answer questions, explain concepts, and chat like a helpful AI.
    4. Email: Send emails to recipients.

    Your Goal: Analyze the user's command and return a JSON ARRAY of actions.

    JSON STRUCTURE:
    Every response MUST be a list of objects: [{"service": "...", "action": "...", "params": {...}, "expect_reply": false}]
    
    SERVICES:
    - "system": for local apps (notepad, calculator, settings, etc.) or typing.
    - "browser": for websites, google searches, social media (WhatsApp).
    - "email": for sending emails.
    - "conversational": for general questions, greeting, or when no other tool applies.

    IMPORTANT RULES FOR "conversational":
    - If the user asks a question (e.g., "What is Quantum Physics?", "Tell me a joke"), you MUST use "conversational".
    - The "response" parameter should contain a DETAILED, HELPFUL, and NATURAL answer, just like ChatGPT. 
    - Do NOT be brief. Explain things fully if asked. Use formatting like \n for new lines if needed in the JSON string.
    - Example: {"service": "conversational", "response": "Quantum physics is the study of matter and energy...", "expect_reply": false}

    CLARIFYING QUESTIONS / FOLLOW-UP:
    - If you are missing information to perform an action (e.g. user says "Send email" but no recipient), you MUST ask for it.
    - Set "expect_reply": true in the JSON.
    - Example: {"service": "conversational", "response": "Who would you like to send the email to?", "expect_reply": true}

    SPECIFIC ACTIONS:
    - Open App: "system", "open_app", {"app_name": "..."}
    - Type Text: "system", "type_text", {"text": "..."}
    - Open URL: "browser", "open_url", {"url": "..."}
    - Search Google: "browser", "search_google", {"query": "..."}
    - WhatsApp Message: "system", "send_whatsapp", {"contact_name": "...", "message": "..."} (Only if user explicitly says "send message" or "whatsapp")
    - Send Email: "email", "send_email", {"recipient": "...", "subject": "...", "body": "..."}
    
    IMPORTANT RULES FOR "Send Email":
    - If the user provides only a TOPIC or MAIN IDEA (e.g. "email boss about sick leave"), YOU must GENERATE the full, professional email content for the "body" parameter.
    - Contextualize the email based on the recipient (formal for boss, casual for friend).
    - Example User: "Send email to team that I'm testing the system." -> Body: "Hello Team, just a quick note to let you know I am currently testing the new email automation system. Regards, [Name]"

    CONTEXT:
    - Use the provided chat history.
    - If user says "search for it", look at previous message to know what "it" is.
    """
    
    # Construct Messages with History
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add last 5 turns of history to context
    global CHAT_HISTORY
    messages.extend(CHAT_HISTORY[-10:]) 
    
    # Add current command
    messages.append({"role": "user", "content": command_text})

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code != 200:
            print(f"DEBUG: API Error Body: {response.text}")
            error_msg = f"API Error {response.status_code}: "
            try:
                error_body = response.json()
                if "error" in error_body:
                    error_msg += error_body["error"]["message"]
            except:
                error_msg += response.text[:50]
                
            return {"service": "error", "message": error_msg}
            
        data = response.json()
        
        # Parse OpenAI format
        content = data['choices'][0]['message']['content']
        print(f"DEBUG: LLM Raw Text: {content}")

        import re
        
        # Clean up markdown if present
        content = content.replace("```json", "").replace("```", "")
        
        # Robust Parsing: Try to find a JSON list in the output
        try:
            # Look for substring starting with [ and ending with ] using regex because LLM might be chatty
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                json_candidate = match.group(0)
                parsed = json.loads(json_candidate)
            else:
                # Try direct parse if regex failed (maybe it's a dict or simple structure)
                parsed = json.loads(content)
                
        except json.JSONDecodeError as je:
            print(f"ERROR: Failed to parse JSON. Content was: {content}")
            # Fallback: Treat entire response as conversational
            parsed = [{"service": "conversational", "response": content}]
        
        # Ensure it's always a list
        if isinstance(parsed, dict):
            parsed = [parsed]
            
        # Update History
        CHAT_HISTORY.append({"role": "user", "content": command_text})
        # We store the raw content as assistant response for context
        CHAT_HISTORY.append({"role": "assistant", "content": content})
            
        return parsed
        
    except Exception as e:
        print(f"Error parsing command with Groq: {e}")
        return {"service": "error", "message": str(e)}
