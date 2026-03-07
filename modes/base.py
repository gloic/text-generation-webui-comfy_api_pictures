"""Mode base class for all operation modes."""

from abc import ABC, abstractmethod


class Mode(ABC):
    """Abstract base class for all operation modes."""

    @abstractmethod
    def process_input(self, text):
        """Process input text before sending to LLM.

        Args:
            text: Input text from user

        Returns:
            Modified text
        """
        pass

    @abstractmethod
    def process_output(self, text, state):
        """Process output text from LLM.

        Args:
            text: Output text from LLM
            state: Current state object

        Returns:
            Modified text (possibly with images)
        """
        pass
