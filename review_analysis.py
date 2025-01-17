import requests
from bs4 import BeautifulSoup
import pandas as pd
import nltk
from dotenv import load_dotenv
import os
import google.generativeai as genai
import json
import re  # Importing regular expressions for parsing
import streamlit as st

load_dotenv()
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
 
api_key1 = os.getenv('API_KEY1')
api_key2 = os.getenv('API_KEY2')
api_key3 = os.getenv('API_KEY3')
API_Vault = [api_key1, api_key2, api_key3]
api_key_index = 0

def analyze_review(review):
    def limit_text_by_word_count(text, max_words):
        words = nltk.word_tokenize(text)
        if len(words) > max_words:
            return ' '.join(words[:max_words])
        return text

    template = """You are expert in sentiment analysis and can give GenAI solution suggestion to each problem:

    Analyze following review and give feedback on them about following parameters:
    1) Sentiment of the review Good or Bad Review
    2) Give the problem in one word like: Customer Support / Product Quality / Delivery etc. 
    3) If the Review is Bad Provide a Generative AI solution to it, like: if customer support is bad give solution to use GenAI chatbot etc. 
    4) If the Review is Good give any suggestion of how can we increase the Good points by using GenAI solution to it.

    ### text to perform review analysis on:
    {text}

    ---

    ### Please provide the information in highly structured json format having following keys as Sentiment, Problem,Bad_review_soln,good_review_soln. Just provide answers in for each in the provided format only. Don't include further explanation or introductory part in chat. Also don't include any unnecessary prefixes or suffixes.
    Also if the review is good keep the bad_review_soln field empty, if the review is bad keep the good_review_soln field empty.
    """

    def get_next_api_key():
        global api_key_index
        api_key = API_Vault[api_key_index]
        api_key_index = (api_key_index + 1) % len(API_Vault)
        return api_key

    max_input_words = 50000
    limited_text = limit_text_by_word_count(review, max_input_words)

    genai.configure(api_key=get_next_api_key())

    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )

    chat_session = model.start_chat(history=[])

    prompt_text = template.format(text=limited_text)

    response = chat_session.send_message(prompt_text)

    return response.text

def extract_json_content(response):
    # Use regex to find content between the first '{' and the last '}'
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        json_str = match.group(0)
        try:
            return json.loads(json_str)  # Parse the JSON content
        except json.JSONDecodeError:
            print("Error decoding JSON:", json_str)
            return None  # Return None if parsing fails
    else:
        print("No JSON content found in the response.")
        return None

def append_reviews_to_excel(all_reviews, file_name):
    # Load existing data
    try:
        existing_df = pd.read_excel(file_name)
    except FileNotFoundError:
        existing_df = pd.DataFrame()  # Create an empty DataFrame if file does not exist

    # Convert the list of review analyses to DataFrame
    new_data_df = pd.DataFrame(all_reviews)

    # Concatenate along rows
    combined_df = pd.concat([existing_df, new_data_df], axis=0, ignore_index=True)

    # Save back to the same file without removing previous data
    combined_df.to_excel(file_name, index=False)
    print(f"Appended reviews to {file_name}")

def llm_analysis(path, save_every=500):
    df = pd.read_excel(path)
    all_review_analysis = []
    processed_count = 0  # Counter to track processed entries

    progress_bar2 = st.progress(0)
    progress_text2 = st.empty()

    for index, row in df.iterrows():
        cell_content = row.get('user_review', '')  # Safely get the 'user_review' column content
        total_row = len(df)
        progress_bar2.progress(index/total_row)
        progress_text2.text(f"Analyzing Review in LLM: {index}/{total_row}")
        try:
            # Analyze each review and append the result
            review_analysis = analyze_review(cell_content)
            print(index, "@@@@", review_analysis)
            
            # Extract and parse JSON content
            analysis_dict = extract_json_content(review_analysis)
            
            if analysis_dict:  # Only append if parsing was successful
                all_review_analysis.append(analysis_dict)
                processed_count += 1

            # Save after every 'save_every' records
            if processed_count % save_every == 0:
                append_reviews_to_excel(all_review_analysis, file_name=path)
                all_review_analysis = []  # Reset list after saving
                print(f"Saved {processed_count} entries so far.")

        except Exception as e:
            print(f"Error processing entry {index}: {e}")
            continue  # Skip to the next entry if an error occurs

    # Save any remaining data after the loop
    if all_review_analysis:
        append_reviews_to_excel(all_review_analysis, file_name=path)
        print("Final save completed for remaining entries.")

# Run the analysis on an existing file
#llm_analysis("company_reviews.xlsx")
