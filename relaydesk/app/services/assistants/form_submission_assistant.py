# relaydesk/app/services/assistants/form_submission_assistant.py

from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from relaydesk.app.services.tools.forms import submit_form
from relaydesk.app.services.assistants.assistant_base import Assistant, llm, CompleteOrEscalate
from pydantic import BaseModel, Field
from typing import Dict, Any

# Define task delegation tool for Form Submission
class ToFormSubmission(BaseModel):
    """Transfers work to a specialized assistant to handle user form submissions."""
    form_data: Dict[str, Any] = Field(description="A dictionary containing form field names as keys and user inputs as values.")

# Form submission assistant prompt
form_submission_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a specialized assistant for handling user form submissions. "
            "Your primary role is to collect necessary information from the user and then use the submit_form tool "
            "to send the data to the specified API endpoint. "
            "The form requires the following mandatory fields: "
            "- 'your-name': The user's full name "
            "- 'your-email': The user's email address "
            "- 'your-subject': The subject of the inquiry "
            "The submission tool adds its required integration fields. Do not invent values for them. "
            "You MUST collect all three mandatory fields from the user before submitting the form. "
            "If the user doesn't provide all required information, politely ask for the missing fields. "
            "Summarize the collected fields and obtain explicit user confirmation before submitting. "
            "If the user's request is not related to form submission, "
            "use the CompleteOrEscalate tool to return control to the main assistant. "
            "Do not reveal or log submitted contact details in diagnostic output. "
            "Current time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

# Form submission assistant tools
form_submission_assistant_tools = [
    submit_form,
    CompleteOrEscalate,
]

# Create the form submission assistant runnable
form_submission_assistant_runnable = form_submission_assistant_prompt | llm.bind_tools(form_submission_assistant_tools)

# Instantiate the form submission assistant
form_submission_assistant = Assistant(form_submission_assistant_runnable)
