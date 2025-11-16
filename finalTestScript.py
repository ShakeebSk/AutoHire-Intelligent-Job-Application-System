"""
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=

GitHub:     https://github.com/ShakeebSk
"""

###################################################### CONFIGURE YOUR TOOLS HERE ######################################################


# Login Credentials for LinkedIn (Optional)
username = ""  # Enter your username in the quotes
password = ""  # Enter your password in the quotes


## Artificial Intelligence (Beta Not-Recommended)
# Use AI
use_AI = False  # True or False, Note: True or False are case-sensitive
"""
Note: Set it as True only if you want to use AI, and If you either have a
1. Local LLM model running on your local machine, with it's APIs exposed. Example softwares to achieve it are:
    a. Ollama - https://ollama.com/
    b. llama.cpp - https://github.com/ggerganov/llama.cpp
    c. LM Studio - https://lmstudio.ai/ (Recommended)
    d. Jan - https://jan.ai/
2. OR you have a valid OpenAI API Key, and money to spare, and you don't mind spending it.
CHECK THE OPENAI API PIRCES AT THEIR WEBSITE (https://openai.com/api/pricing/). 
"""

##> ------ Yang Li : MARKYangL - Feature ------
##> ------ Tim L : tulxoro - Refactor ------
# Select AI Provider
ai_provider = "openai"  # "openai", "deepseek", "gemini"
"""
Note: Select your AI provider.
* "openai" - OpenAI API (GPT models) OR OpenAi-compatible APIs (like Ollama)
* "deepseek" - DeepSeek API (DeepSeek models)
* "gemini" - Google Gemini API (Gemini models)
* For any other models, keep it as "openai" if it is compatible with OpenAI's api.
"""


# Your LLM url or other AI api url and port
llm_api_url = ""  # Examples: "https://api.openai.com/v1/", "http://127.0.0.1:1234/v1/", "http://localhost:1234/v1/", "https://api.deepseek.com", "https://api.deepseek.com/v1"
"""
Note: Don't forget to add / at the end of your url. You may not need this if you are using Gemini.
"""

# Your LLM API key or other AI API key
llm_api_key = "not-needed"  # Enter your API key in the quotes, make sure it's valid, if not will result in error.
"""
Note: Leave it empty as "" or "not-needed" if not needed. Else will result in error!
If you are using ollama, you MUST put "not-needed".
"""

# Your LLM model name or other AI model name
llm_model = ""  # Examples: "gpt-3.5-turbo", "gpt-4o", "llama-3.2-3b-instruct", "qwen3:latest", "gemini-pro", "gemini-1.5-flash", "gemini-2.5-flash", "deepseek-llm:latest"

llm_spec = "openai"  # Examples: "openai", "openai-like", "openai-like-github", "openai-like-mistral"
"""
Note: Currently "openai", "deepseek", "gemini" and "openai-like" api endpoints are supported.
Most LLMs are compatible with openai, so keeping it as "openai-like" will work.
"""

# # Yor local embedding model name or other AI Embedding model name
# llm_embedding_model = "nomic-embed-text-v1.5"

# Do you want to stream AI output?
stream_output = False  # Examples: True or False. (False is recommended for performance, True is recommended for user experience!)
"""
Set `stream_output = True` if you want to stream AI output or `stream_output = False` if not.
"""
##

# Imports
import os
import csv
import re
import pyautogui

# Set CSV field size limit to prevent field size errors
csv.field_size_limit(1000000)  # Set to 1MB instead of default 131KB

from random import choice, shuffle, randint
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    NoSuchWindowException,
    ElementNotInteractableException,
    WebDriverException,
)

from config.personals import *
from config.questions import *
from config.search import *
from config.secrets import use_AI, username, password, ai_provider
from config.settings import *

from modules.open_chrome import *
from modules.helpers import *
from modules.clickers_and_finders import *
from modules.validator import validate_config
from modules.ai.openaiConnections import (
    ai_create_openai_client,
    ai_extract_skills,
    ai_answer_question,
    ai_close_openai_client,
)
from modules.ai.deepseekConnections import (
    deepseek_create_client,
    deepseek_extract_skills,
    deepseek_answer_question,
)
from modules.ai.geminiConnections import (
    gemini_create_client,
    gemini_extract_skills,
    gemini_answer_question,
)

from typing import Literal


pyautogui.FAILSAFE = False
# if use_resume_generator:    from resume_generator import is_logged_in_GPT, login_GPT, open_resume_chat, create_custom_resume


# < Global Variables and logics

if run_in_background == True:
    pause_at_failed_question = False
    pause_before_submit = False
    run_non_stop = False

first_name = first_name.strip()
middle_name = middle_name.strip()
last_name = last_name.strip()
full_name = (
    first_name + " " + middle_name + " " + last_name
    if middle_name
    else first_name + " " + last_name
)

useNewResume = True
randomly_answered_questions = set()

tabs_count = 1
easy_applied_count = 0
external_jobs_count = 0
failed_count = 0
skip_count = 0
dailyEasyApplyLimitReached = False

re_experience = re.compile(
    r"[(]?\s*(\d+)\s*[)]?\s*[-to]*\s*\d*[+]*\s*year[s]?", re.IGNORECASE
)

desired_salary_lakhs = str(round(desired_salary / 100000, 2))
desired_salary_monthly = str(round(desired_salary / 12, 2))
desired_salary = str(desired_salary)

current_ctc_lakhs = str(round(current_ctc / 100000, 2))
current_ctc_monthly = str(round(current_ctc / 12, 2))
current_ctc = str(current_ctc)

notice_period_months = str(notice_period // 30)
notice_period_weeks = str(notice_period // 7)
notice_period = str(notice_period)

aiClient = None
about_company_for_ai = None 


# < Login Functions
def is_logged_in_LN() -> bool:
    """
    Function to check if user is logged-in in LinkedIn
    * Returns: `True` if user is logged-in or `False` if not
    """
    if driver.current_url == "https://www.linkedin.com/feed/":
        return True
    if try_linkText(driver, "Sign in"):
        return False
    if try_xp(driver, '//button[@type="submit" and contains(text(), "Sign in")]'):
        return False
    if try_linkText(driver, "Join now"):
        return False
    print_lg("Didn't find Sign in link, so assuming user is logged in!")
    return True


def login_LN() -> None:
    """
    Function to login for LinkedIn
    * Tries to login using given `username` and `password` from `secrets.py`
    * If failed, tries to login using saved LinkedIn profile button if available
    * If both failed, asks user to login manually
    """
    # Find the username and password fields and fill them with user credentials
    driver.get("https://www.linkedin.com/login")
    try:
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Forgot password?")))
        try:
            text_input_by_ID(driver, "username", username, 1)
        except Exception as e:
            print_lg("Couldn't find username field.")
            # print_lg(e)
        try:
            text_input_by_ID(driver, "password", password, 1)
        except Exception as e:
            print_lg("Couldn't find password field.")
            # print_lg(e)
        # Find the login submit button and click it
        driver.find_element(
            By.XPATH, '//button[@type="submit" and contains(text(), "Sign in")]'
        ).click()
    except Exception as e1:
        try:
            profile_button = find_by_class(driver, "profile__details")
            profile_button.click()
        except Exception as e2:
            # print_lg(e1, e2)
            print_lg("Couldn't Login!")

    try:
        # Wait until successful redirect, indicating successful login
        wait.until(
            EC.url_to_be("https://www.linkedin.com/feed/")
        )  # wait.until(EC.presence_of_element_located((By.XPATH, '//button[normalize-space(.)="Start a post"]')))
        return print_lg("Login successful!")
    except Exception as e:
        print_lg(
            "Seems like login attempt failed! Possibly due to wrong credentials or already logged in! Try logging in manually!"
        )
        # print_lg(e)
        manual_login_retry(is_logged_in_LN, 2)


# >


def get_applied_job_ids() -> set:
    """
    Function to get a `set` of applied job's Job IDs
    * Returns a set of Job IDs from existing applied jobs history csv file
    """
    job_ids = set()
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                job_ids.add(row[0])
    except FileNotFoundError:
        print_lg(f"The CSV file '{file_name}' does not exist.")
    return job_ids


def set_search_location() -> None:
    """
    Function to set search location
    """
    if search_location.strip():
        try:
            print_lg(f'Setting search location as: "{search_location.strip()}"')
            search_location_ele = try_xp(
                driver,
                ".//input[@aria-label='City, state, or zip code'and not(@disabled)]",
                False,
            )  #  and not(@aria-hidden='true')]")
            text_input(actions, search_location_ele, search_location, "Search Location")
        except ElementNotInteractableException:
            try_xp(
                driver,
                ".//label[@class='jobs-search-box__input-icon jobs-search-box__keywords-label']",
            )
            actions.send_keys(Keys.TAB, Keys.TAB).perform()
            actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
            actions.send_keys(search_location.strip()).perform()
            sleep(2)
            actions.send_keys(Keys.ENTER).perform()
            try_xp(driver, ".//button[@aria-label='Cancel']")
        except Exception as e:
            try_xp(driver, ".//button[@aria-label='Cancel']")
            print_lg(
                "Failed to update search location, continuing with default location!", e
            )


def apply_filters() -> None:
    """
    Function to apply job search filters
    """
    set_search_location()

    try:
        recommended_wait = 1 if click_gap < 1 else 0

        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//button[normalize-space()="All filters"]')
            )
        ).click()
        buffer(recommended_wait)

        wait_span_click(driver, sort_by)
        wait_span_click(driver, date_posted)
        buffer(recommended_wait)

        multi_sel_noWait(driver, experience_level)
        multi_sel_noWait(driver, companies, actions)
        if experience_level or companies:
            buffer(recommended_wait)

        multi_sel_noWait(driver, job_type)
        multi_sel_noWait(driver, on_site)
        if job_type or on_site:
            buffer(recommended_wait)

        if easy_apply_only:
            boolean_button_click(driver, actions, "Easy Apply")

        multi_sel_noWait(driver, location)
        multi_sel_noWait(driver, industry)
        if location or industry:
            buffer(recommended_wait)

        multi_sel_noWait(driver, job_function)
        multi_sel_noWait(driver, job_titles)
        if job_function or job_titles:
            buffer(recommended_wait)

        if under_10_applicants:
            boolean_button_click(driver, actions, "Under 10 applicants")
        if in_your_network:
            boolean_button_click(driver, actions, "In your network")
        if fair_chance_employer:
            boolean_button_click(driver, actions, "Fair Chance Employer")

        wait_span_click(driver, salary)
        buffer(recommended_wait)

        multi_sel_noWait(driver, benefits)
        multi_sel_noWait(driver, commitments)
        if benefits or commitments:
            buffer(recommended_wait)

        show_results_button: WebElement = driver.find_element(
            By.XPATH, '//button[contains(@aria-label, "Apply current filters to show")]'
        )
        show_results_button.click()

        global pause_after_filters
        if pause_after_filters and "Turn off Pause after search" == pyautogui.confirm(
            "These are your configured search results and filter. It is safe to change them while this dialog is open, any changes later could result in errors and skipping this search run.",
            "Please check your results",
            ["Turn off Pause after search", "Look's good, Continue"],
        ):
            pause_after_filters = False

    except Exception as e:
        print_lg("Setting the preferences failed!")
        # print_lg(e)


def get_page_info() -> tuple[WebElement | None, int | None]:
    """
    Function to get pagination element and current page number
    """
    try:
        pagination_element = try_find_by_classes(
            driver,
            [
                "jobs-search-pagination__pages",
                "artdeco-pagination",
                "artdeco-pagination__pages",
            ],
        )
        scroll_to_view(driver, pagination_element)
        current_page = int(
            pagination_element.find_element(
                By.XPATH, "//button[contains(@class, 'active')]"
            ).text
        )
    except Exception as e:
        print_lg("Failed to find Pagination element, hence couldn't scroll till end!")
        pagination_element = None
        current_page = None
        print_lg(e)
    return pagination_element, current_page


def get_job_main_details(
    job: WebElement, blacklisted_companies: set, rejected_jobs: set
) -> tuple[str, str, str, str, str, bool]:
    """
    # Function to get job main details.
    Returns a tuple of (job_id, title, company, work_location, work_style, skip)
    * job_id: Job ID
    * title: Job title
    * company: Company name
    * work_location: Work location of this job
    * work_style: Work style of this job (Remote, On-site, Hybrid)
    * skip: A boolean flag to skip this job
    """
    job_details_button = job.find_element(
        By.TAG_NAME, "a"
    )  # job.find_element(By.CLASS_NAME, "job-card-list__title")  # Problem in India
    scroll_to_view(driver, job_details_button, True)
    job_id = job.get_dom_attribute("data-occludable-job-id")
    title = job_details_button.text
    title = title[: title.find("\n")]
    # company = job.find_element(By.CLASS_NAME, "job-card-container__primary-description").text
    # work_location = job.find_element(By.CLASS_NAME, "job-card-container__metadata-item").text
    other_details = job.find_element(
        By.CLASS_NAME, "artdeco-entity-lockup__subtitle"
    ).text
    index = other_details.find(" · ")
    company = other_details[:index]
    work_location = other_details[index + 3 :]
    work_style = work_location[work_location.rfind("(") + 1 : work_location.rfind(")")]
    work_location = work_location[: work_location.rfind("(")].strip()

    # Skip if previously rejected due to blacklist or already applied
    skip = False
    if company in blacklisted_companies:
        print_lg(
            f'Skipping "{title} | {company}" job (Blacklisted Company). Job ID: {job_id}!'
        )
        skip = True
    elif job_id in rejected_jobs:
        print_lg(
            f'Skipping previously rejected "{title} | {company}" job. Job ID: {job_id}!'
        )
        skip = True
    try:
        if (
            job.find_element(By.CLASS_NAME, "job-card-container__footer-job-state").text
            == "Applied"
        ):
            skip = True
            print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')
    except:
        pass
    try:
        if not skip:
            job_details_button.click()
    except Exception as e:
        print_lg(
            f'Failed to click "{title} | {company}" job on details button. Job ID: {job_id}!'
        )
        # print_lg(e)
        discard_job()
        job_details_button.click()  # To pass the error outside
    buffer(click_gap)
    return (job_id, title, company, work_location, work_style, skip)


