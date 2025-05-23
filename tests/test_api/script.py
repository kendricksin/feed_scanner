import sys
import PyPDF2
import requests
from openai import OpenAI

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        sys.exit(1)

# Function to call the Model Studio API using OpenAI library
def call_model_studio_api(prompt):
    # Replace this with your actual API key
    key = "sk-c27b1e2a155d4fbfaddd9b1a463d3ea7"
    
    client = OpenAI(
        # If the environment variable is not configured, replace the following line with: api_key="sk-xxx",
        api_key=key,
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    )

    try:
        response = client.chat.completions.create(
            model="qwen-plus",  # Replace with the model you want to use
            messages=[prompt]
        )
        
        # Assuming the API returns a JSON object with the key "choices"
        result = response.choices[0].message.content.strip()
        return result
    
    except Exception as e:
        print(f"Error calling Model Studio API: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <pdf_file>")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    
    # Step 1: Extract text from the PDF
    pdf_text = extract_text_from_pdf(pdf_file)
    
    # Step 2: Combine the extracted text with your custom prompt
    custom_prompt = "{{project_title: (thai text), department: (thai text), announcement_date: (gregorian dd-mm-yyyy), submission_date: (gregorian cal dd-mm-yyyy), project_budget: (float), contact_info: {{email:, phone:, website:}}, key_details: (english text)}}"
    combined_prompt = {custom_prompt, pdf_text}
    
    # Step 3: Call the Model Studio API with the combined prompt
    api_output = call_model_studio_api(combined_prompt)
    
    # Step 4: Print the output returned by the API
    print("API Output:")
    print(api_output)

if __name__ == "__main__":
    main()

# {project_title: (thai text), department: (thai text), announcement_date: (gregorian dd-mm-yyyy), submission_date: (gregorian cal dd-mm-yyyy), project_budget: (float), contact_info: {email:, phone:, website:}, key_details: (english text)}
# sk-c27b1e2a155d4fbfaddd9b1a463d3ea7
