import os
import time
from google import genai

def main():
    # Get API key from environment variable
    api_key = os.getenv("GEMINI_API_KEY")

    # Check if API key is set in device
    if not api_key:
        print("Error: GEMINI_API_KEY is not set.")
        return

    # Create a Gemini Client
    client = genai.Client(api_key=api_key)

    print("Gemini Chatbot ready. Type 'quit' to exit.\n")

    # Start Loop
    while True:
        # Error-Handling
        try:   
            # Remove extra whitespaces from user input
            user_input = input("You: ").strip()

            # Check if user wants to quit
            if user_input.lower() == "quit":
                print("Goodbye!")
                break
            
            # Check if user entered nothing
            if not user_input:
                print("Please enter a message.")
                continue
            
            # If neither condition is fulfilled, then get response from Gemini
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=user_input
            )
            time.sleep(1)

            print("Gemini:", response.text)

        except Exception as e:
            print("Error:", str(e))
            print("Try again.\n")


if __name__ == "__main__":
    main()