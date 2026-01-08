import unittest
from unittest.mock import MagicMock, patch
import time
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

# Mock dependencies before importing core
sys.modules["orchestrator.audio"] = MagicMock()
sys.modules["orchestrator.llm"] = MagicMock()
sys.modules["orchestrator.main"] = MagicMock()

try:
    from orchestrator.core import AssistantLoop
except ImportError:
    # If run from root, path might be different
    from orchestrator.core import AssistantLoop

class TestAssistantLoop(unittest.TestCase):
    def setUp(self):
        self.loop = AssistantLoop()
        # Mock recorder
        self.loop.recorder = MagicMock()
        
    def test_wake_word_fuzzy(self):
        """Test fuzzy matching."""
        self.assertTrue(self.loop._is_wake_word("hey gimme something"))
        self.assertTrue(self.loop._is_wake_word("hi jimmy open browser"))
        self.assertTrue(self.loop._is_wake_word("hyy gimi"))
        self.assertFalse(self.loop._is_wake_word("hello world"))
        self.assertFalse(self.loop._is_wake_word("hey"))

if __name__ == "__main__":
    unittest.main()
