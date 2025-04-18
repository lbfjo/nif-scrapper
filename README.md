# Racius NIF Scraper

This project aims to scrape the NIF (Número de Identificação Fiscal - Portuguese Tax ID) for a list of Portuguese companies using the Racius.com website.

## Development Process & Learnings

The development of this scraper involved several iterations and adaptations to overcome challenges presented by the target website.

1.  **Initial Approach (Selenium + Google Search):**
    *   The first version (`scraper.py`) used Selenium to:
        *   Search for each company name on Google (`site:racius.com "company name"`).
        *   Click the first Racius link from the Google search results.
        *   Extract the NIF from the Racius company page.
    *   **Challenges:**
        *   Frequent CAPTCHAs encountered during Google searches, blocking the scraping process.
        *   Website blocking (403 errors) even when accessing Racius directly sometimes.
        *   Issues with identifying and clicking the correct search result link.
        *   Problems interacting with cookie consent banners.
        *   Difficulty finding robust CSS selectors for company names and NIFs due to potential variations in page structure.

2.  **Refinement & Debugging (`scraper.py`):**
    *   Increased timeouts and added more robust error handling (e.g., for `TimeoutException`, `NoSuchElementException`).
    *   Refined CSS selectors based on inspecting the HTML structure of search results and company pages.
    *   Added debugging logs to better understand where the script was failing.

3.  **Exploring Direct URL Access (`scraper.py` modification):**
    *   Hypothesized that accessing company pages via direct URLs (`https://www.racius.com/company-name/`) might bypass Google CAPTCHAs and potentially other blocking mechanisms.
    *   Implemented a `normalize_company_name` function to convert company names into a URL-friendly format (lowercase, hyphenated, special characters removed).
    *   Modified the script to *try* direct access first, falling back to Google search if the direct URL failed.
    *   **Challenges:** Initial name normalization was too simple and didn't account for variations like including/excluding "Lda" or handling specific Portuguese characters and symbols correctly, leading to many "Page not found" errors.

4.  **Dedicated Direct Access Scraper (`direct_scraper.py`):**
    *   Created a new script focused *solely* on direct URL access, removing the complexity of Google Search interaction.
    *   **Key Improvements:**
        *   **Advanced Name Normalization:** Significantly improved the `normalize_company_name` function. It now:
            *   Handles Portuguese characters (ç, ã, é, etc.).
            *   Replaces symbols like '&' and '+' appropriately.
            *   Cleans up various forms of company type suffixes (", Lda.", " Unipessoal Lda", etc.).
            *   Generates *two* potential URL slugs for each company: one potentially *with* `-lda` appended and one *without*, attempting both to maximize success.
        *   **Robust NIF Extraction:** Implemented multiple regex patterns to find the NIF, accounting for different formatting found on the pages (e.g., `NIF: XXXXXXXXX`, `data-nif="XXXXXXXXX"`, `Nº Contribuinte: XXXXXXXXX`).
        *   **Progress Saving:** Added logic to save the results to a `_progress.csv` file periodically, preventing data loss during long runs.
        *   **Clearer Logging & Summary:** Improved console output to show which URLs are being tried and provided a final summary of successful scrapes, NIFs not found, and pages not found.
        *   **Simplified Flow:** Removed dependencies on search engine results, making the script faster and less prone to external blocking factors.

## Key Learnings

*   **Direct Access is Often Superior:** For scraping specific entity pages (like companies), constructing direct URLs is generally more reliable and faster than relying on intermediate search engines, primarily due to avoiding CAPTCHAs and simplifying the navigation logic.
*   **Normalization is Critical:** Accurately converting real-world names (like company names) into the specific format expected in URLs requires careful handling of lowercase conversion, special characters, symbols, and common patterns/suffixes. Iterative refinement based on failures is often necessary.
*   **Expect Anti-Scraping:** Websites employ various measures (CAPTCHAs, IP blocking, changing HTML structure). Scrapers need to be designed with flexibility, error handling, and potentially mimicking browser behavior (like `undetected-chromedriver` attempts).
*   **Multiple Patterns Increase Robustness:** When extracting data (like NIFs), relying on a single CSS selector or regex pattern can be brittle. Using multiple patterns based on observed variations increases the chance of successful extraction.
*   **Incremental Progress:** For long scraping tasks, saving progress regularly is crucial to avoid losing work due to interruptions or errors.

## How to Run (`direct_scraper.py`)

1.  **Ensure Dependencies:** Make sure you have Python installed, along with the necessary libraries:
    ```bash
    pip install pandas undetected-chromedriver tqdm
    ```
    *Note: `undetected-chromedriver` requires a compatible Chrome browser installation.*
2.  **Prepare Input:** Place your list of company names in a CSV file named `empresas_lda_com_nif.csv` in the same directory as the script. The file should have one column with no header, containing one company name per row.
3.  **Run the Script:**
    ```bash
    python3 direct_scraper.py
    ```
4.  **Output:** The script will print its progress to the console. Final results will be saved in `companies_with_nifs.csv`, and intermediate progress might be saved in `companies_with_nifs_progress.csv`. # nif-scrapper
# nif-scrapper
