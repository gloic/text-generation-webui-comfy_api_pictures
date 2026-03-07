"""Mode base class for all operation modes."""

from abc import ABC, abstractmethod


class Mode(ABC):
    """Abstract base class for all operation modes."""

    def __init__(self, params, picture_response, debug=False):
        """Initialize mode.

        Args:
            params: Parameters dictionary
            picture_response: Picture generation toggle state
            debug: Debug mode flag
        """
        self.params = params
        self.picture_response = picture_response
        self.debug = debug

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
