import requests
from bs4 import BeautifulSoup
import time

# Function to scrape reviews from a specific reviews URL
def scrape_reviews(reviews_url,company_name,max_pg):
    reviews_list = []
    
    # Start with the first page
    pg_no = 1
     
    while True:
        # Update the reviews URL with the current page number
        current_reviews_url = f"{reviews_url}?page={pg_no}"
        
        # Send a GET request to the reviews URL
        reviews_response = requests.get(current_reviews_url)
        
        if reviews_response.status_code == 200:
            reviews_soup = BeautifulSoup(reviews_response.content, 'html.parser')

            # Find all review cards
            review_cards = reviews_soup.find_all('div', class_='styles_cardWrapper__LcCPA styles_show__HUXRb styles_reviewCard__9HxJJ')

            for card in review_cards:
                try:
                    # Extract user rating
                    user_rating = card.find('div', class_='styles_reviewHeader__iU9Px')['data-service-review-rating']
                except (AttributeError, TypeError):
                    user_rating = None  # Set to None if not found
                
                try:
                    # Extract user review title
                    user_review_title = card.find('h2', class_='typography_heading-s__f7029 typography_appearance-default__AAY17').text.strip()
                except (AttributeError, TypeError):
                    user_review_title = None
                
                try:
                    # Extract user review content
                    user_review = card.find('p', class_='typography_body-l__KUYFJ typography_appearance-default__AAY17 typography_color-black__5LYEn').text.strip()
                except (AttributeError, TypeError):
                    user_review = None
                
                try:
                    # Extract user experience date
                    user_experience_date = card.find('b', class_='typography_body-m__xgxZ_ typography_appearance-default__AAY17 typography_weight-heavy__E1LTj').text.strip()
                except (AttributeError, TypeError):
                    user_experience_date = None

                try:
                    # Extract time of posting
                    time_posting_tag = card.find('div', class_='typography_body-m__xgxZ_ typography_appearance-subtle__8_H2l styles_datesWrapper__RCEKH')
                    time_of_posting = time_posting_tag.find('time')['datetime'] if time_posting_tag else None
                except (AttributeError, TypeError):
                    time_of_posting = None
                
                # Save the extracted information in a dictionary, if available
                review_data = {
                    'Company_name': company_name,
                    'user_rating': user_rating,
                    'user_review_title': user_review_title,
                    'user_review': user_review,
                    'time_of_posting': time_of_posting
                }

                # Check if any key piece of information is missing
                if any(value is None for value in review_data.values()):
                    continue  # Skip this review if any information is missing
                
                print("_______________",company_name,":", pg_no, "_________________")
                print(review_data)
                
                reviews_list.append(review_data)

            # Check for the last page number
            last_page_element = reviews_soup.find('a', class_='link_internal__7XN06 button_button__T34Lr button_m__lq0nA button_appearance-outline__vYcdF button_squared__21GoE link_button___108l pagination-link_item__mkuN3', attrs={'name': 'pagination-button-last'})
            if last_page_element:
                last_page_text = last_page_element.find('span', class_='typography_heading-xxs__QKBS8 typography_appearance-inherit__D7XqR typography_disableResponsiveSizing__OuNP7').text.strip()
                last_page_number = int(last_page_text) if last_page_text.isdigit() else 1

                # If we reach the last page, break the loop
                if(last_page_number >= max_pg):
                    last_page_number = max_pg
                if pg_no >= last_page_number:
                    break
            
            # Prepare for the next page
            pg_no += 1
            
            # Sleep to avoid being blocked by the server
            time.sleep(2)
        else:
            print(f"Failed to retrieve reviews. Status code: {reviews_response.status_code}")
            break

    return reviews_list

# Main function to run the scraping process
def main_function(company_name,max_pg):
    base_url = f'https://www.trustpilot.com/search?query={company_name}' 
    # Send a GET request to the base URL
    response = requests.get(base_url)
    if response.status_code == 200:
        # Parse the response content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the first occurrence of the specified div
        business_unit = soup.find('div', class_='paper_paper__EGeEb paper_outline__bqVmn card_card__yyGgu card_noPadding__OOiac styles_wrapper__Jg8fe styles_businessUnitResult__Q14Q_')
        #paper_paper__1PY90 paper_outline__lwsUX card_card__lQWDv card_noPadding__D8PcU styles_wrapper__2JOo2 styles_businessUnitResult__L3bbC
        
        if business_unit:
            # Extract information safely with checks
            try:
                # Step 3: Get the company name
                extracted_company_name = business_unit.find('p', class_="typography_heading-xs__osRhC typography_appearance-default__t8iAq").text.strip()
                #class_='typography_heading-xs__jSwUz typography_appearance-default__AAY17'
                if (str(company_name).lower()) != (str(extracted_company_name).lower()):
                    return None
            except AttributeError:
                company_name = None

            try:
                # Step 4: Get the company URL
                company_url = business_unit.find('p',class_="typography_body-m__k2UI7 typography_appearance-subtle__PYOVM styles_websiteUrlDisplayed__lSw1A" ).text.strip()
                #class_='typography_body-m__xgxZ_ typography_appearance-subtle__8_H2l styles_websiteUrlDisplayed__QqkCT'
            except AttributeError:
                company_url = None
            
            try:
                # Step 5: Get the star rating from the image alt text
                star_rating_img = business_unit.find('img', class_='star-rating_starRating__sdbkn star-rating_responsive__AzPOl')
                #class_='star-rating_starRating__4rrcf star-rating_responsive__C9oka'
                star_rating = star_rating_img['alt'].strip() if star_rating_img else 'No rating available'
            except AttributeError:
                star_rating = None
            
            try:
                # Step 6: Get the business location
                business_location = business_unit.find('span', class_="typography_body-m__k2UI7 typography_appearance-subtle__PYOVM styles_metadataItem__DOu6t styles_location__wea8G").text.strip()
                #class_='typography_body-m__xgxZ_ typography_appearance-subtle__8_H2l styles_metadataItem__Qn_Q2 styles_location__ILZb0'
            except AttributeError:
                business_location = None
            
            try:
                # Step 7: Get the href for reviews
                reviews_href = business_unit.find('a',class_="link_internal__Eam_b link_wrapper__ahpyq styles_linkWrapper___KiUr" )['href'].strip()
                #class_='link_internal__7XN06 link_wrapper__5ZJEx styles_linkWrapper__UWs5j'
            except (AttributeError, TypeError):
                reviews_href = None
            
            # Check for critical missing values
            if not company_name and not reviews_href:
                print("Missing both company_name and reviews_href. Skipping this entry.")
                return  # Exit the function if both are missing
            
            if not company_name:
                print("Missing company_name. Skipping this entry.")
                return  # Exit if company name is missing
            
            if not reviews_href:
                print("Missing reviews_href. Skipping this entry.")
                return  # Exit if reviews_href is missing
            
            # Output the extracted information
            print(f"Company Name: {company_name}")
            print(f"Company URL: {company_url}")
            print(f"Star Rating: {star_rating}")
            print(f"Business Location: {business_location}")
            print(f"Reviews URL: https://www.trustpilot.com{reviews_href}")

            # Step 8: Scrape all the reviews from the reviews page
            reviews_url = f"https://www.trustpilot.com{reviews_href}"
            reviews_data = scrape_reviews(reviews_url,company_name,max_pg)

            return reviews_data

            # Print all reviews data
            for review in reviews_data:
                print(f"\nUser Rating: {review['user_rating']}")
                print(f"User Review Title: {review['user_review_title']}")
                print(f"User Review: {review['user_review']}")
                print(f"User Experience Date: {review['user_experience_date']}")
                print(f"Time of Posting: {review['time_of_posting']}")
        else:
            print("Business unit div not found.")
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")

# Example usage
#if __name__ == "__main__":
#    base_url = "https://www.trustpilot.com/search?query=your_company_name"  # Replace with the actual company query
#    main_function(base_url)
