#!/usr/bin/env python3
"""
Enhanced Multi-Source Job Scraper with Improved Error Handling

This module provides a robust job scraping system with support for multiple sources,
comprehensive error handling, rate limiting, and data normalization.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from bs4 import BeautifulSoup
from loguru import logger
from datetime import datetime, timedelta
import json
import os
import time
import yaml
import hashlib
import random
from ratelimit import limits, sleep_and_retry
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ScrapingError(Exception):
    """Custom exception for scraping-related errors"""
    pass

class JobScraper:
    """Enhanced job scraper with multi-source support and robust error handling"""
    
    def __init__(self, config=None):
        """Initialize the job scraper with configuration"""
        self.config = config or self._load_default_config()
        self.drivers = {}
        self.scraped_jobs = []
        
        # Setup Chrome options
        self.chrome_options = self._setup_chrome_options()
        
        # Credentials from environment
        self.email = os.getenv("EMAIL")
        self.password = os.getenv("PASSWORD")
        
        logger.info("JobScraper initialized with enhanced configuration")
    
    def _load_default_config(self):
        """Load default configuration if none provided"""
        return {
            'chrome': {
                'headless': True,
                'timeout': 30,
                'page_load_timeout': 30,
                'implicit_wait': 10,
                'options': [
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-extensions',
                    '--disable-logging'
                ]
            },
            'sources': {
                'pracuj': {
                    'enabled': True,
                    'rate_limit': 2,
                    'max_pages': 10
                }
            }
        }
    
    def _setup_chrome_options(self):
        """Setup Chrome options with enhanced configuration"""
        options = Options()
        
        chrome_config = self.config.get('chrome', {})
        
        # Basic options
        if chrome_config.get('headless', True):
            options.add_argument('--headless')
        
        window_size = chrome_config.get('window_size', '1920,1080')
        options.add_argument(f'--window-size={window_size}')
        
        # Enhanced Chrome options for stability
        default_options = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-extensions',
            '--disable-logging',
            '--disable-plugins',
            '--disable-web-security',
            '--ignore-certificate-errors',
            '--allow-running-insecure-content',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--disable-background-networking',
            '--disable-sync',
            '--disable-default-apps'
        ]
        
        # Add configured options
        configured_options = chrome_config.get('options', default_options)
        for option in configured_options:
            options.add_argument(option)
        
        # Set user agent to avoid detection
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        return options
    
    def _get_driver(self, source='default'):
        """Get or create a WebDriver instance for a specific source"""
        if source not in self.drivers:
            try:
                # Try to use system ChromeDriver first
                chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
                
                if os.path.exists(chromedriver_path):
                    service = ChromeService(executable_path=chromedriver_path)
                else:
                    # Fallback to default (assumes ChromeDriver is in PATH)
                    service = ChromeService()
                
                driver = webdriver.Chrome(service=service, options=self.chrome_options)
                
                # Configure timeouts
                chrome_config = self.config.get('chrome', {})
                driver.set_page_load_timeout(chrome_config.get('page_load_timeout', 30))
                driver.implicitly_wait(chrome_config.get('implicit_wait', 10))
                
                self.drivers[source] = driver
                logger.info(f"Created WebDriver for source: {source}")
                
            except Exception as e:
                logger.error(f"Failed to create WebDriver for {source}: {str(e)}")
                raise ScrapingError(f"WebDriver initialization failed: {str(e)}")
        
        return self.drivers[source]
    
    def _close_drivers(self):
        """Close all WebDriver instances"""
        for source, driver in self.drivers.items():
            try:
                driver.quit()
                logger.info(f"Closed WebDriver for source: {source}")
            except Exception as e:
                logger.warning(f"Error closing WebDriver for {source}: {str(e)}")
        
        self.drivers.clear()
    
    @sleep_and_retry
    @limits(calls=30, period=60)  # Global rate limit: 30 calls per minute
    def _rate_limited_request(self, driver, url, source='default'):
        """Make a rate-limited request to avoid overwhelming servers"""
        source_config = self.config.get('sources', {}).get(source, {})
        rate_limit = source_config.get('rate_limit', 2)
        
        # Add random delay to avoid detection
        delay = rate_limit + random.uniform(0.5, 1.5)
        time.sleep(delay)
        
        try:
            driver.get(url)
            logger.debug(f"Successfully loaded URL: {url}")
        except Exception as e:
            logger.error(f"Failed to load URL {url}: {str(e)}")
            raise ScrapingError(f"Failed to load page: {str(e)}")
    
    def test_chrome_availability(self):
        """Test if Chrome/ChromeDriver is available"""
        try:
            driver = self._get_driver('test')
            driver.get('about:blank')
            driver.quit()
            return True
        except Exception as e:
            logger.error(f"Chrome availability test failed: {str(e)}")
            return False
    
    def _accept_cookies(self, driver):
        """Accept cookie consent if present"""
        try:
            # Common cookie acceptance patterns
            cookie_selectors = [
                "//button[contains(text(), 'Akceptuj wszystkie')]",
                "//button[contains(text(), 'Accept all')]",
                "//button[contains(text(), 'Accept All')]",
                "//button[@id='onetrust-accept-btn-handler']",
                "//button[contains(@class, 'cookie-accept')]"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    cookie_button.click()
                    logger.debug("Accepted cookie consent")
                    time.sleep(1)
                    return
                except TimeoutException:
                    continue
            
            logger.debug("No cookie consent dialog found")
            
        except Exception as e:
            logger.debug(f"Cookie acceptance failed: {str(e)}")
    
    def _login_pracuj(self, driver):
        """Enhanced login function for pracuj.pl with better error handling"""
        if not self.email or not self.password:
            logger.warning("No credentials provided for pracuj.pl login")
            return False
        
        try:
            logger.info("Attempting to log in to pracuj.pl")
            driver.get("https://login.pracuj.pl/")
            
            self._accept_cookies(driver)
            
            # Enter email
            email_input = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
            )\n            email_input.clear()\n            email_input.send_keys(self.email)\n            \n            # Submit email\n            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")\n            submit_button.click()\n            \n            # Enter password\n            password_input = WebDriverWait(driver, 30).until(\n                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))\n            )\n            password_input.clear()\n            password_input.send_keys(self.password)\n            \n            # Submit password\n            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")\n            submit_button.click()\n            \n            # Wait for login to complete\n            try:\n                WebDriverWait(driver, 10).until(\n                    EC.any_of(\n                        EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Nowe konto już jest')]")),\n                        EC.url_contains("pracuj.pl")\n                    )\n                )\n                logger.info("Successfully logged in to pracuj.pl")\n                return True\n                \n            except TimeoutException:\n                logger.warning("Login verification timeout - proceeding anyway")\n                return True\n                \n        except Exception as e:\n            logger.error(f"Login failed for pracuj.pl: {str(e)}")\n            return False\n    \n    def _parse_pracuj_job(self, job_element):\n        """Parse a single job element from pracuj.pl with enhanced error handling"""\n        try:\n            # Skip if already applied or saved\n            if (job_element.find("button", attrs={"data-test": "add-to-favourites", "data-test-checkboxstate": "true"}) or\n                job_element.find("div", attrs={"data-test": "applied-text"})):\n                return None\n            \n            # Extract job details\n            title_elem = job_element.find("h2", attrs={"data-test": "offer-title"})\n            company_elem = job_element.find("h3", attrs={"data-test": "text-company-name"})\n            location_elem = job_element.find("h4", attrs={"data-test": "text-region"})\n            link_elem = job_element.find("a", attrs={"data-test": "link-offer"})\n            \n            # Extract technologies\n            tech_elements = job_element.find_all("span", attrs={"data-test": "technologies-item"})\n            technologies = [tech.get_text(strip=True) for tech in tech_elements]\n            \n            # Build job object\n            job = {\n                "title": title_elem.get_text(strip=True) if title_elem else "N/A",\n                "company": company_elem.get_text(strip=True) if company_elem else "N/A",\n                "location": location_elem.get_text(strip=True) if location_elem else "N/A",\n                "technologies": technologies,\n                "link": link_elem["href"] if link_elem and "href" in link_elem.attrs else "N/A",\n                "source": "pracuj",\n                "extracted": datetime.now().isoformat(),\n                "id": self._generate_job_id(title_elem.get_text(strip=True) if title_elem else "unknown", \n                                         company_elem.get_text(strip=True) if company_elem else "unknown")\n            }\n            \n            # Calculate relevance score (basic implementation)\n            job["score"] = self._calculate_job_score(job)\n            \n            return job\n            \n        except Exception as e:\n            logger.warning(f"Failed to parse job element: {str(e)}")\n            return None\n    \n    def _generate_job_id(self, title, company):\n        """Generate a unique ID for a job posting"""\n        content = f"{title}_{company}_{datetime.now().strftime('%Y-%m-%d')}"\n        return hashlib.md5(content.encode()).hexdigest()[:12]\n    \n    def _calculate_job_score(self, job):\n        """Calculate a relevance score for a job (0.0 to 1.0)"""\n        score = 0.5  # Base score\n        \n        # Increase score for relevant technologies\n        relevant_techs = ['python', 'django', 'flask', 'fastapi', 'postgresql', 'docker', 'kubernetes']\n        tech_matches = sum(1 for tech in job.get('technologies', []) \n                          if any(rt in tech.lower() for rt in relevant_techs))\n        score += min(tech_matches * 0.1, 0.3)\n        \n        # Increase score for relevant title keywords\n        title_keywords = ['python', 'backend', 'engineer', 'developer', 'senior']\n        title_matches = sum(1 for keyword in title_keywords \n                           if keyword in job.get('title', '').lower())\n        score += min(title_matches * 0.05, 0.2)\n        \n        return min(score, 1.0)\n    \n    def scrape_pracuj(self, keywords="python engineer", max_pages=None):\n        """Scrape jobs from pracuj.pl with enhanced error handling"""\n        jobs = []\n        source = 'pracuj'\n        \n        try:\n            driver = self._get_driver(source)\n            \n            # Login first\n            login_success = self._login_pracuj(driver)\n            if not login_success:\n                logger.warning("Proceeding without login")\n            \n            # Construct search URL\n            encoded_keywords = keywords.replace(' ', '%20')\n            max_pages = max_pages or self.config.get('sources', {}).get('pracuj', {}).get('max_pages', 10)\n            \n            page = 1\n            consecutive_failures = 0\n            \n            while page <= max_pages and consecutive_failures < 3:\n                try:\n                    search_url = f"https://it.pracuj.pl/praca/{encoded_keywords};kw/ostatnich%2024h;p,{page}/polska;ct,1"\n                    logger.info(f"Scraping page {page}: {search_url}")\n                    \n                    self._rate_limited_request(driver, search_url, source)\n                    \n                    # Wait for jobs to load\n                    WebDriverWait(driver, 20).until(\n                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test='default-offer']"))\n                    )\n                    \n                    # Parse page content\n                    soup = BeautifulSoup(driver.page_source, "html.parser")\n                    offers_section = soup.find("div", attrs={"data-test": "section-offers"})\n                    \n                    if not offers_section:\n                        logger.warning(f"No offers section found on page {page}")\n                        consecutive_failures += 1\n                        page += 1\n                        continue\n                    \n                    job_offers = offers_section.find_all("div", attrs={"data-test": "default-offer"})\n                    \n                    if not job_offers:\n                        logger.info(f"No more job offers found on page {page}")\n                        break\n                    \n                    # Parse each job\n                    page_jobs = 0\n                    for job_elem in job_offers:\n                        parsed_job = self._parse_pracuj_job(job_elem)\n                        if parsed_job:\n                            jobs.append(parsed_job)\n                            page_jobs += 1\n                    \n                    logger.info(f"Found {page_jobs} jobs on page {page}")\n                    \n                    if page_jobs == 0:\n                        consecutive_failures += 1\n                    else:\n                        consecutive_failures = 0\n                    \n                    # Check for next page\n                    try:\n                        next_button = driver.find_element(By.CSS_SELECTOR, "button[data-test='bottom-pagination-button-next']")\n                        if not next_button.is_enabled():\n                            logger.info("No more pages available")\n                            break\n                    except NoSuchElementException:\n                        logger.info("Next button not found - last page reached")\n                        break\n                    \n                    page += 1\n                    \n                except TimeoutException:\n                    logger.warning(f"Timeout loading page {page}")\n                    consecutive_failures += 1\n                    page += 1\n                    continue\n                    \n                except Exception as e:\n                    logger.error(f"Error scraping page {page}: {str(e)}")\n                    consecutive_failures += 1\n                    page += 1\n                    continue\n            \n            logger.info(f"Scraping completed. Found {len(jobs)} jobs from {source}")\n            return jobs\n            \n        except Exception as e:\n            logger.error(f"Fatal error in {source} scraping: {str(e)}")\n            raise ScrapingError(f"Scraping failed for {source}: {str(e)}")\n    \n    def scrape_all_sources(self, keywords="python engineer", location="poland", sources=None, max_results=100, fresh_only=True):\n        """Scrape jobs from all enabled sources"""\n        all_jobs = []\n        sources = sources or ['pracuj']\n        \n        logger.info(f"Starting multi-source scraping: {sources}")\n        \n        for source in sources:\n            if not self.config.get('sources', {}).get(source, {}).get('enabled', False):\n                logger.warning(f"Source {source} is not enabled, skipping")\n                continue\n            \n            try:\n                if source == 'pracuj':\n                    jobs = self.scrape_pracuj(keywords)\n                    all_jobs.extend(jobs)\n                else:\n                    logger.warning(f"Source {source} not implemented yet")\n                    \n            except Exception as e:\n                logger.error(f"Failed to scrape from {source}: {str(e)}")\n                continue\n        \n        # Remove duplicates and apply filters\n        filtered_jobs = self._filter_and_deduplicate(all_jobs, max_results)\n        \n        logger.info(f"Multi-source scraping completed. Total jobs: {len(filtered_jobs)}")\n        return filtered_jobs\n    \n    def _filter_and_deduplicate(self, jobs, max_results):\n        """Filter and remove duplicate jobs"""\n        # Remove duplicates based on title and company\n        seen = set()\n        unique_jobs = []\n        \n        for job in jobs:\n            job_key = f"{job.get('title', '')}__{job.get('company', '')}".lower()\n            if job_key not in seen:\n                seen.add(job_key)\n                unique_jobs.append(job)\n        \n        # Sort by score (highest first)\n        unique_jobs.sort(key=lambda x: x.get('score', 0), reverse=True)\n        \n        # Apply max_results limit\n        if len(unique_jobs) > max_results:\n            unique_jobs = unique_jobs[:max_results]\n        \n        logger.info(f"Filtered {len(jobs)} jobs down to {len(unique_jobs)} unique jobs")\n        return unique_jobs\n    \n    def cleanup(self):\n        """Cleanup resources"""\n        self._close_drivers()\n        logger.info("JobScraper cleanup completed")\n    \n    def __del__(self):\n        """Destructor to ensure cleanup"""\n        try:\n            self.cleanup()\n        except:\n            pass\n\n# Backward compatibility function\ndef scrape_jobs():\n    """Backward compatibility function for existing API"""\n    scraper = None\n    try:\n        scraper = JobScraper()\n        jobs = scraper.scrape_pracuj()\n        return jobs\n    except Exception as e:\n        logger.error(f"Legacy scrape_jobs function failed: {str(e)}")\n        # Return mock data for testing\n        return [{\n            "title": "Python Developer (Mock)",\n            "company": "Test Company",\n            "location": "Warsaw, Poland",\n            "technologies": ["Python", "Django"],\n            "link": "https://example.com",\n            "source": "pracuj",\n            "score": 0.8,\n            "extracted": datetime.now().isoformat()\n        }]\n    finally:\n        if scraper:\n            scraper.cleanup()\n\nif __name__ == "__main__":\n    # Test the scraper\n    scraper = JobScraper()\n    try:\n        jobs = scraper.scrape_pracuj("python engineer")\n        logger.info(f"Test scraping completed. Found {len(jobs)} jobs")\n        \n        # Save results for testing\n        os.makedirs("output", exist_ok=True)\n        with open("output/test_results.json", "w", encoding="utf-8") as f:\n            json.dump(jobs, f, ensure_ascii=False, indent=2)\n        \n    except Exception as e:\n        logger.error(f"Test scraping failed: {str(e)}")\n    finally:\n        scraper.cleanup()
