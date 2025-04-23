# gemini/client.py
import google.generativeai as genai
import os
import json
from flask import current_app, Flask # Import Flask for standalone testing context

# Placeholder for the actual prompt loading
def load_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), 'prompt.txt')
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        # Default fallback prompt
        print("Warning: prompt.txt not found. Using default prompt.")
        return """
Analyze the following task description provided by a user.
Based on the text, classify it into one of the following categories:
- Shopping List
- Schedule / Events
- Notes
- Long-Term Tasks

Extract key details relevant to the category. For example:
- Shopping List: Extract the items as a list in the "items" key.
- Schedule / Events: Extract the date, time, and event description.
- Notes: Provide a concise summary.
- Long-Term Tasks: Provide a concise summary.

Return the result *only* as a valid JSON object with the following structure:
{
  "category": "...",
  "summary": "...",
  "details": { ... } // e.g., {"date": "YYYY-MM-DD", "time": "HH:MM AM/PM", "items": [...], "description": "..."}
}

If the category is ambiguous, choose the most likely one. Ensure the output is *only* the JSON object, without any introductory text or markdown formatting.

User Task: "{user_input}"
JSON Output:
"""

# Placeholder function for classifying task using Gemini
def classify_task(user_input_text, api_key):
    """
    Classifies the user's task text using the Gemini API.

    Args:
        user_input_text (str): The natural language task input from the user.
        api_key (str): The Google AI Studio API key.

    Returns:
        dict: A dictionary containing the classification results (category, summary, details).
              Returns a default structure with 'Uncategorized' on error.
    """
    logger = current_app.logger if current_app else None # Use Flask logger if in app context

    if not api_key:
        if logger: logger.error("Gemini API Key is not configured.")
        else: print("Error: Gemini API Key is not configured.")
        # Return dummy data immediately if no API key
        return {
            "category": "Notes", # Default category without API key
            "summary": user_input_text[:50] + "..." if len(user_input_text) > 50 else user_input_text,
            "details": {"error": "API Key not configured"}
        }

    try:
        genai.configure(api_key=api_key)

        # Model configuration (adjust as needed)
        generation_config = {
            "temperature": 0.6, # Slightly lower temp for more predictable JSON
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 2048,
            "response_mime_type": "application/json", # Request JSON output
        }
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]

        model = genai.GenerativeModel(model_name="gemini-1.5-flash", # Using flash model
                                      generation_config=generation_config,
                                      safety_settings=safety_settings)

        prompt_template = load_prompt()
        full_prompt = prompt_template.format(user_input=user_input_text)

        response = model.generate_content(full_prompt)

        # Attempt to parse the JSON response directly from response.text
        # The API in JSON mode should return just the JSON string
        result_json = json.loads(response.text)

        # Basic validation of expected keys
        if not all(k in result_json for k in ["category", "summary", "details"]):
             raise ValueError("Gemini response missing required keys.")
        if not isinstance(result_json["details"], dict):
             # Ensure details is always a dictionary
             result_json["details"] = {"info": result_json["details"]} if result_json.get("details") else {}

        return result_json

    except json.JSONDecodeError as e:
        err_msg = f"Gemini response was not valid JSON: {e}"
        raw_resp = getattr(response, 'text', 'No response text available')
        if logger: logger.error(err_msg)
        else: print(err_msg)
        if logger: logger.error(f"Raw Gemini response text: {raw_resp}")
        else: print(f"Raw Gemini response text: {raw_resp}")
        # Fallback if JSON parsing fails
        return {
            "category": "Uncategorized",
            "summary": user_input_text[:50] + "..." if len(user_input_text) > 50 else user_input_text,
            "details": {"error": "Failed to parse Gemini response", "raw_response": raw_resp}
        }
    except Exception as e:
        err_msg = f"Error calling Gemini API: {e}"
        if logger: logger.error(err_msg)
        else: print(err_msg)
        # General fallback
        return {
            "category": "Uncategorized",
            "summary": user_input_text[:50] + "..." if len(user_input_text) > 50 else user_input_text,
            "details": {"error": str(e)}
        }

# Example usage (for testing purposes)
if __name__ == '__main__':
    # Create a dummy Flask app context for testing logger
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'testing' # Needed for context
    # Set environment variable GEMINI_API_KEY for this to run
    # You can use a .env file or set it directly in your terminal
    from dotenv import load_dotenv
    load_dotenv() # Load .env file if it exists

    test_api_key = os.environ.get("GEMINI_API_KEY")
    if test_api_key:
        with app.app_context(): # Need app context for current_app.logger
            test_inputs = [
                "Buy milk, eggs, and bread for the weekend",
                "Meeting with the marketing team next Tuesday at 2 PM in the main conference room",
                "Remember to research new project management software options",
                "Plan the summer vacation trip for August",
                "Get apples and oranges",
                "Finish the report by Friday EOD"
            ]
            for test_input in test_inputs:
                print(f"\n--- Testing classification for: '{test_input}' ---")
                result = classify_task(test_input, test_api_key)
                print("Classification Result:")
                print(json.dumps(result, indent=2))
    else:
        print("\nPlease set the GEMINI_API_KEY environment variable (e.g., in a .env file) to run the test.") 