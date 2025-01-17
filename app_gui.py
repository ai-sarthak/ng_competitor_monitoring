import requests
from bs4 import BeautifulSoup
import pandas as pd
import nltk
from dotenv import load_dotenv
import os
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import iterator
import review_analysis
import streamlit as st
import zipfile

def configure_driver():
    chromedriver_path = 'c:\\Program Files\\chromedriver.exe' 
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

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


def get_google_news(keyword, max_pages=1):
    # Open Google News search for the specified keyword
    driver = configure_driver()
    driver.get(f'https://www.google.com/search?q={keyword}&tbm=nws')
    news_items = []
    current_page = 0

    while current_page < max_pages:
        # Wait for results to load
        time.sleep(2)
        
        # Locate news items on the current page
        news_results = driver.find_elements(By.CSS_SELECTOR, 'div#rso > div > div > div > div')
        
        for news_div in news_results:
            try:
                news_item = {'Keyword': keyword}  # Add the keyword to each news item
                news_item['Link'] = news_div.find_element(By.TAG_NAME, 'a').get_attribute('href')
                divs_inside_news = news_div.find_elements(By.CSS_SELECTOR, 'a>div>div>div')

                if len(divs_inside_news) >= 4:
                    news_item['Domain'] = divs_inside_news[1].text
                    news_item['Title'] = divs_inside_news[2].text
                    news_item['Description'] = divs_inside_news[3].text
                    news_item['Date'] = divs_inside_news[4].text

                    news_link = news_item['Link']
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[1])
                    driver.get(news_link)
                    time.sleep(2)

                    try:
                        article_content = driver.find_element(By.TAG_NAME, 'body').text 
                        news_item['Full Content'] = article_content

                        combined_text = news_item['Title'] + ' ' + article_content
                        print(news_item)
                        news_items.append(news_item)

                    except Exception as e:
                        print(f"Error scraping news content: {e}")
                        news_item['Full Content'] = 'N/A'

                    driver.close()  
                    driver.switch_to.window(driver.window_handles[0])
            
            except Exception as e:
                print(f"Error processing news item: {e}")    
        
        # Try to find the "Next" button and go to the next page
        try:
            next_button = driver.find_element(By.XPATH, "//a[@id='pnnext']")
            next_button.click()
            current_page += 1
            time.sleep(2)  # Wait for the next page to load
        except Exception:
            print("No more pages available or pagination limit reached.")
            break
    
    return news_items

def analyze_news(news_text):
    def limit_text_by_word_count(text, max_words):
        words = nltk.word_tokenize(text)
        if len(words) > max_words:
            return ' '.join(words[:max_words])
        return text

    template = """You are an expert in analyzing news from the news provided and you are expert in named entity recogition:
    Please perform analysis on the provided news and return the following analysis:
    1) Main Company name about whom the news is
    2) is main company working in GenAI niche?
    3) Company names involved in this news
    4) who are the clients of the main company invoved in news
    5) names of  the potential customers in the news

    ### News to perform analysis on:
    {text}

    ---

    ### Please provide the extracted information in highly structured python dictionary format like: [Main Company:[],'Names involved':[],'Client list':[],'customers':[]]. Just provide answers in for each in the provided format only. Don't include further explanation or introductory part in chat.
    """

    def get_next_api_key():
        global api_key_index
        api_key = API_Vault[api_key_index]
        api_key_index = (api_key_index + 1) % len(API_Vault)
        return api_key

    max_input_words = 50000
    limited_text = limit_text_by_word_count(news_text, max_input_words)

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

def llm_analysis(articles):
    for article in articles:
        news_text = article['Full Content']
        result = analyze_news(news_text)
        article['analysis'] = result
    return articles

def save_to_excel(data, filename):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"Data saved to {filename}")



def create_zip_file(company_review, review_analysis):

    # Create a zip file
    zip_file = "output.zip"
    with zipfile.ZipFile(zip_file, 'w') as zipf:
        zipf.write(company_review)
        zipf.write(review_analysis)

    # Clean up the CSV files after zipping

    return zip_file

if __name__ == "__main__":
    # List of keywords to search for

    st.set_page_config(page_title="Keyword Scraper & Analyzer", layout="wide")
    st.title("Keyword Scraper & Review Analyzer")


    st.sidebar.header("Configuration")
    num_api_keys = st.sidebar.number_input("Number of API Keys", min_value=1, max_value=10, step=1, value=1)
    api_keys = [st.sidebar.text_input(f"API Key {i+1}", type="password") for i in range(num_api_keys)]
    st.sidebar.write("Stored API Keys:", ["******" for _ in api_keys])

    keywords_input = st.text_input("Enter keywords (comma-separated):", placeholder="e.g., customer service , GenAI in customer service")
    max_pg_for_google_news = st.sidebar.number_input("Enter the number of pages to scrape google_news",min_value=1, max_value=10, step=1, value=1)
    max_pg_for_reviews = st.sidebar.number_input("Enter the number of pages to scrape for reviews",min_value=1, max_value=10, step=1, value=1)
    review_to_save_once = st.sidebar.number_input("Enter the number of reviews to save in batch in excel",min_value=100, max_value=500, step=1, value=100)

    # = ["GenAI in customer service"]
    #max_pg = 10
    #all_articles = []  # List to store news articles for all keywords

    if st.button("Start Process"):
        if not keywords_input.strip():
            st.error("Please enter at least one keyword.")
        else:
            keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
            all_articles = []

            progress_bar = st.progress(0)
            progress_text = st.empty()

            total_keywords = len(keywords)
            for i, keyword in enumerate(keywords, start=1):
                progress_text.text(f"Scraping Google News for keyword '{keyword}' ({i}/{total_keywords})")
                articles = get_google_news(keyword, max_pages=max_pg_for_google_news)
                analyzed_articles = llm_analysis(articles)
                all_articles.extend(analyzed_articles)
                progress_bar.progress(i / total_keywords)

        # If news articles are found for any keyword, save them to a single Excel file
        if all_articles:

            st.success("Scraping completed.")
            articles_file = "google_news_data.xlsx"
            pd.DataFrame(all_articles).to_excel(articles_file, index=False)

            #save_to_excel(all_articles, "all_competitor_google_news.xlsx")
        
            file_path = "google_news_data.xlsx"
            progress_text.text("Gathering reviews...")
            iterator.main_f(file_path,max_pg_for_reviews)
            time.sleep(10)
            print("#########GETTING ANALYSIS ON REVIEWS: #############")
            st.success("Review Gathering completed.")
            review_analysis.llm_analysis('company_reviews.xlsx',review_to_save_once)

            print("***************ANALYSIS ENDS*********************")
            st.download_button("Download Google Scraped Data", data=open(articles_file, "rb").read(), file_name=articles_file)
            st.download_button("Download Review Analysis", data=open("company_reviews.xlsx", "rb").read(), file_name="company_review_file.xlsx")
            zip_file = create_zip_file("company_reviews.xlsx", articles_file)

            # Store the zip file path in session state
            st.session_state.zip_file = zip_file
            if "zip_file" in st.session_state:
                with open(st.session_state.zip_file, "rb") as file:
                    st.download_button("Download All Files", data=file.read(), file_name=st.session_state.zip_file)
            st.write("Files saved to:", zip_file)
        else:
            st.warning("No articles found.")
    
    
 