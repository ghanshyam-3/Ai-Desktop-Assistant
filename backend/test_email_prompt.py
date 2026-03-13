import os
import sys
from llm.groq_client import GroqClient
import json
import datetime

client = GroqClient()
cur_t = datetime.datetime.now().strftime('%I:%M %p')
cur_d = datetime.datetime.now().strftime('%A, %B %d, %Y')
prompt = f"""
        Act as Desktop Assistant. Time: {cur_t}, Date: {cur_d}
        Return JSON: {{ 'action': string, 'target': any, 'confidence': 'high'|'medium'|'low' }}
        IMPORTANT: If command matches an action, confidence MUST be 'high'. Only use 'low' for complete gibberish.
        
        Actions:
        1. 'open_app': Target=App name
        2. 'web_search': Target=Query
        3. 'answer': Target=Answer text
        4. 'send_email': Target={{'to': string, 'subject': string, 'body': string}}. Important: If the user provides a short description of what to email, YOU MUST generate a professional, complete email 'subject' and 'body' based on their request. Missing 'to' info -> return 'chat'.
        5. 'check_email': Target=null
        6. 'read_email': Target=null
        7. 'system_control': Target in ['volume_up', 'volume_down', 'mute', 'wifi_on', 'wifi_off', 'bluetooth_on', 'bluetooth_off', 'hotspot', 'shutdown', 'restart', 'sleep', 'screenshot']
        8. 'analyze_screen': Target=User Question. ONLY if user asks to see screen.
        9. 'add_task': Target=Description
        10. 'list_tasks': Target=null
        11. 'add_note': Target=Content
        12. 'list_notes': Target=null
        13. 'complete_task': Target=Task Name
        14. 'delete_task': Target=Task Name
        15. 'show_dashboard': Target=null
        16. 'reset_conversation': Target=null
        17. 'chat': Target=Reply (Use for greetings, 'how are you', or general questions not covered above).
        18. 'play_media': Target=Song Name / Video Title (e.g. "Blinding Lights", "Python tutorial").

        Examples:
        "Open Chrome" -> {{ "action": "open_app", "target": "Google Chrome", "confidence": "high" }}
        "Play Blinding Lights" -> {{ "action": "play_media", "target": "Blinding Lights", "confidence": "high" }}
        "Emails?" -> {{ "action": "check_email", "target": null, "confidence": "high" }}
        "How are you?" -> {{ "action": "chat", "target": "I'm doing well, thank you!", "confidence": "high" }}
        "Hello" -> {{ "action": "chat", "target": "Hello there!", "confidence": "high" }}
        "Email John to schedule a meeting tomorrow" -> {{ "action": "send_email", "target": {{"to": "John", "subject": "Meeting Request: Tomorrow", "body": "Hi John,\\n\\nI would like to schedule a meeting with you for tomorrow. Please let me know what time works best for you.\\n\\nBest regards,"}}, "confidence": "high" }}
        "asdf vb" -> {{ "action": null, "target": null, "confidence": "low" }}

        """

print(client.process_intent([{'role':'user', 'content':'Send an email to Raj telling him we must review the final project slides tonight'}], prompt))
