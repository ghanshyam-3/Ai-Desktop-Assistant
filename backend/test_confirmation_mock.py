import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import asyncio

# Adjust path to import server
# backend is at ../backend from here if we run from tests, but let's assume we run from project root
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock necessary modules BEFORE importing server
sys.modules['voice_engine'] = MagicMock()
sys.modules['voice_engine.listener'] = MagicMock()
sys.modules['voice_engine.recognizer'] = MagicMock()
sys.modules['voice_engine.mic_utils'] = MagicMock()
sys.modules['voice_engine.capture'] = MagicMock()
sys.modules['voice_engine.tts'] = MagicMock()
sys.modules['llm'] = MagicMock()
sys.modules['llm.groq_client'] = MagicMock()
sys.modules['automation'] = MagicMock()
sys.modules['automation.launcher'] = MagicMock()
sys.modules['automation.browser'] = MagicMock()
sys.modules['automation.email_sender'] = MagicMock()
sys.modules['automation.system_control'] = MagicMock()
sys.modules['automation.planner'] = MagicMock()
sys.modules['quotes'] = MagicMock() # Mock quotes
sys.modules['pyaudio'] = MagicMock()
sys.modules['socketio'] = MagicMock()
sys.modules['uvicorn'] = MagicMock()
sys.modules['fastapi'] = MagicMock()
sys.modules['fastapi.middleware.cors'] = MagicMock()
# Mock dotenv
sys.modules['dotenv'] = MagicMock()

print("Mocks setup. Importing server...")
try:
    # Now import server
    import server
    print("Server imported successfully.")
except Exception as e:
    print(f"Error importing server: {e}")


class TestVoiceConfirmation(unittest.TestCase):
    def setUp(self):
        # Reset globals
        server.current_state = server.AssistantState.IDLE
        server.chat_history = []
        server.pending_action = None
        server.is_voice_active = True
        
        # Mock dependencies
        self.mock_groq = MagicMock()
        server.groq_client = self.mock_groq
        
        server.launcher = MagicMock()
        server.browser = MagicMock()
        server.email_sender = MagicMock()
        server.sys_control = MagicMock()
        server.planner = MagicMock()
        
        # Mock execute_action and start_speaking locally (we can't easily mock module level functions unless we patch)
        # But since we imported server, we can overwrite them
        self.original_execute = server.execute_action
        self.original_start = server.start_speaking
        
        server.execute_action = MagicMock(return_value="Done")
        server.start_speaking = MagicMock(return_value=True)

        # Mock notify_frontend/chat
        server.notify_frontend = MagicMock()
        server.notify_chat = MagicMock()

    def tearDown(self):
        server.execute_action = self.original_execute
        server.start_speaking = self.original_start

    def test_high_confidence_command(self):
        """High confidence command should execute immediately"""
        print("\n--- Test High Confidence ---")
        # Mock LLM intent response
        self.mock_groq.process_intent.return_value = '{"action": "open_app", "target": "notepad", "confidence": "high"}'
        
        # Test with text input to bypass audio recording
        server.process_command(text_input="Open notepad")
        
        # Verify execute_action was called
        server.execute_action.assert_called_with("open_app", "notepad")
        # State should be IDLE (or whatever finish_interaction leaves it in, mocked start_speaking keeps it IDLE)
        self.assertEqual(server.current_state, server.AssistantState.IDLE)

    def test_low_confidence_command(self):
        """Low confidence command should trigger confirmation"""
        print("\n--- Test Low Confidence ---")
        self.mock_groq.process_intent.return_value = '{"action": "open_app", "target": "notepad", "confidence": "low"}'
        
        server.process_command(text_input="Open notepad")
        
        # Verify execute_action NOT called
        server.execute_action.assert_not_called()
        # State should be CONFIRMATION
        self.assertEqual(server.current_state, server.AssistantState.CONFIRMATION)
        # Pending action set
        self.assertEqual(server.pending_action, {'action': 'open_app', 'target': 'notepad'})

    def test_critical_action_command(self):
        """Critical action should trigger confirmation even if high confidence"""
        print("\n--- Test Critical Action ---")
        self.mock_groq.process_intent.return_value = '{"action": "shutdown", "target": null, "confidence": "high"}'
        
        server.process_command(text_input="Shutdown computer")
        
        server.execute_action.assert_not_called()
        self.assertEqual(server.current_state, server.AssistantState.CONFIRMATION)
        self.assertEqual(server.pending_action, {'action': 'shutdown', 'target': None})

    def test_confirmation_yes(self):
        """Confirming a pending action should execute it"""
        print("\n--- Test Confirmation YES ---")
        # Setup pending action state
        server.current_state = server.AssistantState.CONFIRMATION
        server.pending_action = {'action': 'open_app', 'target': 'notepad'}
        
        # Input "yes"
        server.process_command(text_input="yes")
        
        # Verify execution
        server.execute_action.assert_called_with("open_app", "notepad")
        self.assertIsNone(server.pending_action)
        self.assertEqual(server.current_state, server.AssistantState.IDLE)

    def test_confirmation_no(self):
        """Denying a pending action should cancel it"""
        print("\n--- Test Confirmation NO ---")
        server.current_state = server.AssistantState.CONFIRMATION
        server.pending_action = {'action': 'open_app', 'target': 'notepad'}
        
        # Input "no"
        server.process_command(text_input="no")
        
        # Verify NO execution
        server.execute_action.assert_not_called()
        self.assertIsNone(server.pending_action)
        self.assertEqual(server.current_state, server.AssistantState.IDLE)

    def test_gibberish_input(self):
        """Gibberish inputs should range to null action and be ignored"""
        print("\n--- Test Gibberish ---")
        # LLM returns null action, low confidence
        self.mock_groq.process_intent.return_value = '{"action": null, "target": null, "confidence": "low"}'
        
        server.process_command(text_input="asdfjkl")
        
        server.execute_action.assert_not_called()
        # Should remain IDLE (or whatever it was)
        # Verify notify_frontend called with IDLE/Not sure
        # server.notify_frontend.assert_called() 
        pass

if __name__ == '__main__':
    unittest.main()
