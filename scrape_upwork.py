import os
import sys
import time
import json
import pickle
import logging
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv

load_dotenv()

# CONFIGURATION
UPWORK_USERNAME = os.getenv("UPWORK_USERNAME")
UPWORK_PASSWORD = os.getenv("UPWORK_PASSWORD")
CHROME_VERSION = int(os.getenv("CHROME_VERSION", 137))
WAIT_TIME = int(os.getenv("VERIFICATION_PAUSE", 30))
COOKIES_FILE = "cookies.pkl"
OUTPUT_FILE = "scraped_jobs.json"

# LOGGING SETUP
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def launch_driver():
    options = uc.ChromeOptions()
    options.headless = False
    return uc.Chrome(options=options, version_main=CHROME_VERSION)

def save_cookies(driver):
    with open(COOKIES_FILE, 'wb') as f:
        pickle.dump(driver.get_cookies(), f)

def load_cookies(driver):
    try:
        with open(COOKIES_FILE, 'rb') as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                if 'expiry' in cookie:
                    del cookie['expiry']
                driver.add_cookie(cookie)
        return True
    except Exception as e:
        logger.warning(f"Cookie load failed: {e}")
        return False

def is_logged_in(driver):
    try:
        driver.get("https://www.upwork.com/")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#nav-right > ul > li.nav-d-none.nav-d-lg-flex.nav-dropdown.nav-dropdown-account.nav-arrow-end.fl-nav-rework > button > div'))
        )
        close_profile_popup(driver)
        return True
    except:
        return False
    
def close_profile_popup(driver):
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.air3-btn.air3-btn-primary"))
        )
        close_button = driver.find_element(By.CSS_SELECTOR, "button.air3-btn.air3-btn-primary")
        if close_button.text.strip().lower() == "close":
            close_button.click()
            logger.info("✅ Closed profile completion popup")
            time.sleep(1)
    except:
        logger.info("✅ No profile popup detected or already closed")

def login_to_upwork(driver):
    logger.info("Navigating to Upwork login")
    driver.get("https://www.upwork.com/ab/account-security/login")

    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.ID, "login_username"))
    ).send_keys(UPWORK_USERNAME + Keys.ENTER)

    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.ID, "login_password"))
    ).send_keys(UPWORK_PASSWORD + Keys.ENTER)

    logger.info(f"Waiting {WAIT_TIME}s for 2FA / CAPTCHA if needed")
    time.sleep(WAIT_TIME)

    save_cookies(driver)
    close_profile_popup(driver)

# attempt to login with cookies if cookies.pkl exists. otherwise login manually
def login_or_restore(driver):
    logger.info("Attempting cookie login")
    driver.get("https://www.upwork.com/")
    if load_cookies(driver):
        driver.refresh()
        if is_logged_in(driver):
            logger.info("✅ Logged in with cookies")
            return
    logger.info("⚠️ Cookie login failed, using credentials")
    login_to_upwork(driver)


# scrape job listings from best matches section
def scrape_jobs(driver, save_to_file=True):
    logger.info("Navigating to Best Matches")
    driver.get("https://www.upwork.com/nx/find-work/best-matches")
    time.sleep(10)

    for _ in range(10):
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
        time.sleep(1)

    job_cards = driver.find_elements(By.CSS_SELECTOR, "section.air3-card-section")
    logger.info(f"Found {len(job_cards)} job cards")

    jobs = []
    for card in job_cards:
        try:
            title_el = card.find_element(By.CSS_SELECTOR, "h3 a")
            title = title_el.text
            link = title_el.get_attribute("href")

            description = card.find_element(By.CSS_SELECTOR, "span[data-test='job-description-text']").text

            tags = [tag.text for tag in card.find_elements(By.CSS_SELECTOR, "[data-test='attr-item']")]

            try:
                proposals = card.find_element(By.CSS_SELECTOR, "strong[data-test='proposals']").text
            except:
                proposals = ""

            try:
                budget = card.find_element(By.CSS_SELECTOR, "span[data-test='budget']").text
            except:
                budget = ""
                
            try:
                hourly_pay = card.find_element(By.CSS_SELECTOR, "[data-test='job-type']").text
            except:
                hourly_pay = ""

            try:
                client_location = card.find_element(By.CSS_SELECTOR, "[data-test='client-country']").text.strip()
            except:
                client_location = ""

            try:
                posted = card.find_element(By.CSS_SELECTOR, "span[data-test='posted-on']").text
            except:
                posted = ""

            jobs.append({
                "title": title,
                "link": link,
                "description": description,
                "tags": tags,
                "proposals": proposals,
                "budget": budget,
                "hourly_pay": hourly_pay,
                "client_location": client_location,
                "posted": posted,
                "scraped_at": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.warning(f"Failed to parse job card: {e}")

    if save_to_file:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2)
        logger.info(f"Saved {len(jobs)} jobs to {OUTPUT_FILE}")

    return jobs


def main():
    driver = launch_driver()
    try:
        login_or_restore(driver)
        scrape_jobs(driver)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
