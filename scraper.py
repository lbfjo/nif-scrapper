import os
import time
import random
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
from tqdm import tqdm
from urllib.parse import quote
from selenium.webdriver.common.keys import Keys

class RaciusScraper:
    def __init__(self):
        self.base_url = "https://www.racius.com"
        self.setup_driver()
        
    def setup_driver(self):
        options = uc.ChromeOptions()
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')  # Try to avoid detection
        
        try:
            self.driver = uc.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
            
            # Add some randomization to the window size
            width = random.randint(1024, 1920)
            height = random.randint(768, 1080)
            self.driver.set_window_size(width, height)
            
        except Exception as e:
            print(f"Error setting up Chrome driver: {str(e)}")
            raise
            
    def random_sleep(self, min_time=2, max_time=4):
        time.sleep(random.uniform(min_time, max_time))
        
    def normalize_company_name(self, name):
        """Convert company name to URL-friendly format"""
        # Remove common company types
        name = name.lower()
        name = name.replace(', lda.', '').replace(' lda', '')
        name = name.replace(', unipessoal lda.', '').replace(' unipessoal lda', '')
        
        # Replace special characters
        name = name.replace('ç', 'c').replace('ã', 'a').replace('á', 'a').replace('à', 'a')
        name = name.replace('é', 'e').replace('ê', 'e').replace('í', 'i').replace('ó', 'o')
        name = name.replace('õ', 'o').replace('ú', 'u').replace('ü', 'u')
        
        # Replace spaces and special chars with hyphens
        name = re.sub(r'[^a-z0-9]+', '-', name)
        
        # Remove leading/trailing hyphens
        name = name.strip('-')
        
        return name
        
    def try_direct_access(self, company_name):
        """Try to access the company page directly before using Google search"""
        try:
            normalized_name = self.normalize_company_name(company_name)
            direct_url = f"https://www.racius.com/{normalized_name}/"
            
            print(f"Trying direct access: {direct_url}")
            self.driver.get(direct_url)
            self.random_sleep(2, 3)
            
            # Check if we landed on a valid company page
            if "Página não encontrada" not in self.driver.page_source:
                print("Direct access successful!")
                return True
            
            print("Direct access failed, falling back to search...")
            return False
            
        except Exception as e:
            print(f"Error during direct access: {str(e)}")
            return False
            
    def search_company(self, company_name):
        # First try direct access
        if self.try_direct_access(company_name):
            return True
            
        # If direct access fails, fall back to Google search
        try:
            # Format the Google search query
            search_query = f"site:racius.com {company_name}"
            google_url = f"https://www.google.com/search?q={quote(search_query)}"
            
            print(f"Falling back to Google search: {search_query}")
            self.driver.get(google_url)
            self.random_sleep(3, 5)
            
            # Check for CAPTCHA
            if "recaptcha" in self.driver.page_source.lower():
                print("\n*** CAPTCHA detected! ***")
                print("Please solve the CAPTCHA in the browser window.")
                print("The script will continue automatically after the CAPTCHA is solved.")
                print("Waiting for CAPTCHA to be solved...")
                
                # Wait for CAPTCHA to be solved (wait for h3 elements to appear)
                try:
                    WebDriverWait(self.driver, 300).until(  # 5 minute timeout
                        EC.presence_of_element_located((By.TAG_NAME, "h3"))
                    )
                    print("CAPTCHA solved! Continuing with search...")
                    self.random_sleep(2, 3)
                except TimeoutException:
                    print("Timeout waiting for CAPTCHA to be solved")
                    return False
            
            try:
                # First try to find the main link by h3 title
                print("Looking for search results...")
                h3_elements = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "h3"))
                )
                
                print(f"Found {len(h3_elements)} h3 elements")
                for h3 in h3_elements:
                    try:
                        title_text = h3.text
                        print(f"Found title: {title_text}")
                        
                        # Get the parent <a> tag
                        parent = h3.find_element(By.XPATH, "./..")
                        if parent.tag_name != "a":
                            parent = parent.find_element(By.XPATH, "./..")
                        
                        href = parent.get_attribute("href")
                        print(f"Found link: {href}")
                        
                        if href and "racius.com" in href and not "/q/" in href:
                            print(f"Found valid Racius link: {href}")
                            # Navigate directly to the URL
                            self.driver.get(href)
                            self.random_sleep(2, 3)
                            return True
                    except Exception as e:
                        print(f"Error processing h3: {str(e)}")
                        continue
                
                print("No suitable Racius link found in h3 elements, trying alternative method...")
                
                # Fallback: try to find any link to racius.com
                links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    try:
                        href = link.get_attribute("href")
                        if href and "racius.com" in href and not "/q/" in href:
                            print(f"Found Racius link (alternative method): {href}")
                            self.driver.get(href)
                            self.random_sleep(2, 3)
                            return True
                    except:
                        continue
                
                print("No suitable Racius link found")
                return False
                
            except TimeoutException:
                print("Timeout waiting for search results")
                return False
            except Exception as e:
                print(f"Error finding/clicking link: {str(e)}")
                return False
                
        except Exception as e:
            print(f"Error searching for company {company_name}: {str(e)}")
            return False
            
    def extract_nif(self):
        current_url = self.driver.current_url
        print(f"Attempting to extract NIF from URL: {current_url}")
        try:
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            self.random_sleep(2, 3)
            
            # Get the page source
            page_source = self.driver.page_source
            print("Got page source, looking for NIF...")
            
            # Try to find NIF in the page content with various patterns
            nif_patterns = [
                r'NIF:\s*(\d{9})',
                r'NIF\s+(\d{9})',
                r'NIF[^0-9]*(\d{9})',
                r'data-nif="(\d{9})"',
                r'class="nif"[^>]*>(\d{9})<',
                r'>NIF:\s*(\d{9})<',
                r'>Nº Contribuinte:\s*(\d{9})<',
                r'contribuinte de[^>]*>(\d{9})<',
                r'\b\d{9}\b'  # Fallback to any 9-digit number if nothing else works
            ]
            
            for pattern in nif_patterns:
                print(f"Trying pattern: {pattern}")
                match = re.search(pattern, page_source)
                if match:
                    nif = match.group(1)
                    print(f"Found NIF using pattern '{pattern}': {nif}")
                    return nif
            
            print("No NIF found in page source")
            return None
            
        except Exception as e:
            print(f"Error extracting NIF: {str(e)}")
            return None
            
    def close(self):
        if self.driver:
            print("Closing the browser...")
            self.driver.quit()

def main():
    # Read the CSV file without headers and create a column name
    df = pd.read_csv('empresas_lda_com_nif.csv', header=None, names=['company_name'])
    companies = df['company_name'].tolist()
    
    # Initialize results dictionary
    results = {'company_name': [], 'nif': []}
    
    # Initialize scraper
    scraper = RaciusScraper()
    
    try:
        # Process each company
        for i, company in enumerate(companies, 1):
            print(f"\nProcessing company {i}/{len(companies)}: {company}")
            
            nif_found = False
            max_retries = 2
            retry_count = 0
            
            while not nif_found and retry_count < max_retries:
                try:
                    if scraper.search_company(company):
                        nif = scraper.extract_nif()
                        if nif:
                            print(f"Successfully extracted NIF: {nif}")
                            results['company_name'].append(company)
                            results['nif'].append(nif)
                            nif_found = True
                            break
                        else:
                            print("NIF not found on company page.")
                    else:
                        print("Company search failed or no results found.")
                        
                    retry_count += 1
                    if not nif_found and retry_count < max_retries:
                        print(f"Retrying... Attempt {retry_count + 1}/{max_retries}")
                        scraper.random_sleep(5, 7)  # Longer delay between retries
                        
                except Exception as e:
                    print(f"Error during attempt {retry_count + 1}: {str(e)}")
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"Retrying... Attempt {retry_count + 1}/{max_retries}")
                        scraper.random_sleep(5, 7)
                    
            if not nif_found:
                results['company_name'].append(company)
                results['nif'].append("Not found")
                
            # Save progress every 5 companies
            if i % 5 == 0:
                temp_df = pd.DataFrame(results)
                temp_df.to_csv('companies_with_nifs_progress.csv', index=False)
                print(f"Progress saved. Processed {i}/{len(companies)} companies")
            
            # Random delay between companies
            scraper.random_sleep(3, 5)
            
    finally:
        # Close the browser
        scraper.close()
        
        # Save final results
        print("\nSaving final results...")
        results_df = pd.DataFrame(results)
        results_df.to_csv('companies_with_nifs.csv', index=False)
        
        # Print summary
        successful_nifs = len([nif for nif in results['nif'] if nif not in ["Not found", "Error"]])
        not_found_count = len([nif for nif in results['nif'] if nif == "Not found"])
        
        print(f"\n--- Scraping Summary ---")
        print(f"Total companies processed: {len(companies)}")
        print(f"Successfully found NIFs: {successful_nifs}")
        print(f"Companies not found or NIF missing: {not_found_count}")
        print(f"Results saved to companies_with_nifs.csv")
        print(f"--- End Summary ---")

if __name__ == "__main__":
    main() 