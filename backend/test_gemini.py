import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import errors


def main():
    # 1. Load environment variables from .env file
    # This will locate the .env file in the current directory or parents.
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        print(f"Loading environment variables from: {env_path}")
        load_dotenv(dotenv_path=env_path)
    else:
        print(
            "Warning: No .env file found in the backend root directory. Falling back to system environment variables."
        )
        load_dotenv()

    # 2. Retrieve GEMINI_API_KEY
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n[ERROR] GEMINI_API_KEY is missing or empty in the environment.")
        print("Please check that GEMINI_API_KEY is defined in your backend/.env file.")
        sys.exit(1)

    print(
        f"API key successfully retrieved: {api_key[:6]}...{api_key[-6:] if len(api_key) > 12 else ''}"
    )

    # 3. Initialize the Google GenAI Client
    # We pass the loaded api_key directly to the Client constructor.
    try:
        print("\nInitializing Gemini client using the latest google-genai SDK...")
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"\n[ERROR] Failed to initialize the Gemini client: {e}")
        sys.exit(1)

    # 4. Generate content using a simple prompt
    prompt = "Hello, who are you?"
    model_name = "gemini-2.5-flash"  # The recommended default model for general tasks in google-genai

    print(f"Sending prompt: '{prompt}' to model: '{model_name}'...")

    try:
        # Call models.generate_content (the standard API call for google-genai)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )

        # 5. Output the response
        print("\n=== Gemini Response ===")
        if response.text:
            print(response.text)
        else:
            print("[Warning] Response was empty or blocked.")
        print("=======================")

    except errors.APIError as api_err:
        print("\n[API ERROR] The Gemini API returned an error:")
        print(f"Details: {api_err}")
        print(
            "\nNote: Please verify that your GEMINI_API_KEY is a valid Google AI Studio key."
        )
    except Exception as e:
        print("\n[UNEXPECTED ERROR] An error occurred during request execution:")
        print(f"Details: {e}")


if __name__ == "__main__":
    main()
