import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import ast
import extracter

# Load the Excel file


# Create an empty list to store all main companies

 
# Configure the WebDriver
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode (without a browser window)
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    
    # Set the path to your ChromeDriver
    service = Service('c:\\Program Files\\chromedriver.exe')  # Update to the correct path for your ChromeDriver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Function to scrape a company's reviews
def scrape_google_reviews(company_name,max_pg=10):
    reviews = []
    #max_pg = 10
    reviews = extracter.main_function( company_name,max_pg)
    

    return reviews

# Save all reviews to a single Excel file
def save_reviews_to_excel(all_reviews, file_name='company_reviews.xlsx'):
    df = pd.DataFrame(all_reviews)
    df.to_excel(file_name, index=False)
    print(f"Saved reviews to {file_name}")


def main_f(file_path,max_pg):
    main_companies = []
    #file_path = 'competitor_google_news.xlsx'  # Update the path to your Excel file
    df = pd.read_excel(file_path)
    # Loop through the column that contains the data
    for index, row in df.iterrows():
        # Assume the column name with the data is 'analysis', adjust as needed
        cell_content = row['analysis']  
    
        # Strip extra characters like ```python and ```
        if cell_content.startswith("```python"):
            cell_content = cell_content.replace("```python", "").replace("```", "").strip()
    
        # Parse the cell content into a Python dictionary
        try:
            parsed_dict = ast.literal_eval(cell_content)
            main_company = parsed_dict.get('Main Company', [])
            main_companies.extend(main_company)  # Add all companies from the list
        except Exception as e:
            print(f"Error parsing row {index}: {e}")

    # Remove duplicates from the main companies list
    main_companies = list(set(main_companies))

    # Print the extracted list of companies
    print(main_companies)

    # Initialize an empty list to store all reviews
    all_reviews = []

    # Scrape reviews for each company and append to the all_reviews list
    for company in main_companies:
        print(f"Scraping reviews for {company}...")
        reviews = scrape_google_reviews(company,max_pg)
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",reviews,"@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        if reviews != None:
            all_reviews.extend(reviews)

    # Save all reviews to a single Excel file
    save_reviews_to_excel(all_reviews)


# Main code execution
if __name__ == "__main__":
    main_f('competitor_google_news.xlsx')