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

class DirectRaciusScraper:
    def __init__(self):
        self.base_url = "https://www.racius.com"
        self.setup_driver()
        
    def setup_driver(self):
        options = uc.ChromeOptions()
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        try:
            self.driver = uc.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
        except Exception as e:
            print(f"Error setting up Chrome driver: {str(e)}")
            raise
            
    def random_sleep(self, min_time=2, max_time=4):
        time.sleep(random.uniform(min_time, max_time))
        
    def normalize_company_name(self, name):
        """Convert company name to URL-friendly format"""
        # First try with Lda
        name_with_lda = self._normalize_name(name, keep_lda=True)
        name_without_lda = self._normalize_name(name, keep_lda=False)
        return [name_with_lda, name_without_lda]
        
    def _normalize_name(self, name, keep_lda=False):
        """Helper function to normalize names with option to keep or remove Lda"""
        # Convert to lowercase
        name = name.lower().strip()
        
        # Handle special company types
        if keep_lda:
            # Just clean up the Lda format
            name = re.sub(r',?\s*unipessoal\s*lda\.?', '-lda', name, flags=re.IGNORECASE)
            name = re.sub(r',?\s*lda\.?', '-lda', name, flags=re.IGNORECASE)
        else:
            # Remove company types completely
            name = re.sub(r',?\s*unipessoal\s*lda\.?', '', name, flags=re.IGNORECASE)
            name = re.sub(r',?\s*lda\.?', '', name, flags=re.IGNORECASE)
        
        # Replace special characters
        chars_map = {
            'ç': 'c', 'ã': 'a', 'á': 'a', 'à': 'a', 'â': 'a',
            'é': 'e', 'ê': 'e', 'í': 'i', 'ó': 'o', 'õ': 'o',
            'ô': 'o', 'ú': 'u', 'ü': 'u', 'ñ': 'n'
        }
        for old, new in chars_map.items():
            name = name.replace(old, new)
        
        # Handle special characters and spaces
        name = re.sub(r'[&+]', 'e', name)  # Replace & and + with 'e'
        name = re.sub(r'[^a-z0-9]+', '-', name)  # Replace any non-alphanumeric chars with single hyphen
        name = name.strip('-')  # Remove leading/trailing hyphens
        
        return name
        
    def access_company_page(self, company_name):
        try:
            # Try both with and without Lda in the URL
            normalized_names = self.normalize_company_name(company_name)
            
            for normalized_name in normalized_names:
                url = f"{self.base_url}/{normalized_name}/"
                print(f"Trying URL: {url}")
                
                self.driver.get(url)
                self.random_sleep(1, 2)
                
                # Check if page exists
                if "Página não encontrada" not in self.driver.page_source:
                    print("Page found successfully")
                    return True
                    
                print("Page not found, trying alternative URL...")
            
            print("All URL variations failed")
            return False
            
        except Exception as e:
            print(f"Error accessing company page: {str(e)}")
            return False
            
    def extract_nif(self):
        try:
            # Wait for page content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get the page source
            page_source = self.driver.page_source
            
            # Try various NIF patterns
            nif_patterns = [
                r'NIF:\s*(\d{9})',
                r'NIF\s+(\d{9})',
                r'NIF[^0-9]*(\d{9})',
                r'data-nif="(\d{9})"',
                r'class="nif"[^>]*>(\d{9})<',
                r'>NIF:\s*(\d{9})<',
                r'>Nº Contribuinte:\s*(\d{9})<',
                r'contribuinte[^>]*>(\d{9})<'
            ]
            
            for pattern in nif_patterns:
                match = re.search(pattern, page_source)
                if match:
                    nif = match.group(1)
                    print(f"Found NIF: {nif}")
                    return nif
            
            print("No NIF found")
            return None
            
        except Exception as e:
            print(f"Error extracting NIF: {str(e)}")
            return None
            
    def close(self):
        if self.driver:
            print("Closing browser...")
            self.driver.quit()

def main():
    # Read the CSV file
    df = pd.read_csv('empresas_lda_com_nif.csv', header=None, names=['company_name'])
    companies = df['company_name'].tolist()
    
    # Initialize results dictionary
    results = {'company_name': [], 'nif': []}
    
    # Initialize scraper
    scraper = DirectRaciusScraper()
    
    try:
        # Process each company
        for i, company in enumerate(companies, 1):
            print(f"\nProcessing company {i}/{len(companies)}: {company}")
            
            if scraper.access_company_page(company):
                nif = scraper.extract_nif()
                if nif:
                    results['company_name'].append(company)
                    results['nif'].append(nif)
                else:
                    results['company_name'].append(company)
                    results['nif'].append("Not found")
            else:
                results['company_name'].append(company)
                results['nif'].append("Page not found")
            
            # Save progress every 5 companies
            if i % 5 == 0:
                temp_df = pd.DataFrame(results)
                temp_df.to_csv('companies_with_nifs_progress.csv', index=False)
                print(f"Progress saved. Processed {i}/{len(companies)} companies")
            
            # Random delay between requests
            time.sleep(random.uniform(1, 2))
            
    finally:
        # Close the browser
        scraper.close()
        
        # Save final results
        print("\nSaving final results...")
        results_df = pd.DataFrame(results)
        results_df.to_csv('companies_with_nifs.csv', index=False)
        
        # Print summary
        successful_nifs = len([nif for nif in results['nif'] if nif not in ["Not found", "Page not found"]])
        not_found = len([nif for nif in results['nif'] if nif == "Not found"])
        page_not_found = len([nif for nif in results['nif'] if nif == "Page not found"])
        
        print(f"\n--- Scraping Summary ---")
        print(f"Total companies processed: {len(companies)}")
        print(f"Successfully found NIFs: {successful_nifs}")
        print(f"NIFs not found on page: {not_found}")
        print(f"Pages not found: {page_not_found}")
        print(f"Results saved to companies_with_nifs.csv")
        print(f"--- End Summary ---")

if __name__ == "__main__":
    main() 