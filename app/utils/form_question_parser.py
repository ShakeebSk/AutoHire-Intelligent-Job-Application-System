#!/usr/bin/env python3
"""
Form Question Parser for LinkedIn Job Applications
Detects and parses different types of form questions and input elements
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

logger = logging.getLogger(__name__)

class FormQuestion:
    """
    Represents a single form question with its elements and options
    """
    
    def __init__(self, element, question_text: str, input_type: str, options: List[str] = None):
        self.element = element
        self.question_text = question_text.strip()
        self.input_type = input_type
        self.options = options or []
        self.is_required = '*' in question_text or 'required' in question_text.lower()
        self.label_element = None
        self.input_element = None
    
    def __repr__(self):
        return f"FormQuestion(type={self.input_type}, question='{self.question_text[:50]}...', options={len(self.options)})"

class FormQuestionParser:
    """
    Parser to detect and extract form questions from LinkedIn application pages
    """
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.logger = logging.getLogger(__name__)
    
    def find_all_questions(self) -> List[FormQuestion]:
        """
        Find all form questions on the current page
        
        Returns:
            List of FormQuestion objects
        """
        try:
            self.logger.info("🔍 Scanning page for form questions...")
            questions = []
            
            # Different strategies to find questions
            strategies = [
                self._find_fieldset_questions,
                self._find_label_input_pairs,
                self._find_standalone_inputs,
                self._find_textarea_questions,
                self._find_select_questions
            ]
            
            for strategy in strategies:
                try:
                    strategy_questions = strategy()
                    questions.extend(strategy_questions)
                    self.logger.info(f"   Found {len(strategy_questions)} questions using {strategy.__name__}")
                except Exception as e:
                    self.logger.debug(f"Strategy {strategy.__name__} failed: {str(e)}")
            
            # Remove duplicates based on question text
            unique_questions = []
            seen_texts = set()
            
            for q in questions:
                if q.question_text and q.question_text not in seen_texts:
                    unique_questions.append(q)
                    seen_texts.add(q.question_text)
            
            self.logger.info(f" Found {len(unique_questions)} unique form questions")
            return unique_questions
            
        except Exception as e:
            self.logger.error(f"Error finding questions: {str(e)}")
            return []
    
    def _find_fieldset_questions(self) -> List[FormQuestion]:
        """Find questions organized in fieldsets"""
        questions = []
        
        fieldset_selectors = [
            "//fieldset",
            "//div[contains(@class, 'jobs-easy-apply')]//fieldset",
            "//form//fieldset"
        ]
        
        for selector in fieldset_selectors:
            try:
                fieldsets = self.driver.find_elements(By.XPATH, selector)
                for fieldset in fieldsets:
                    if not fieldset.is_displayed():
                        continue
                    
                    # Get legend or first label as question text
                    question_text = ""
                    try:
                        legend = fieldset.find_element(By.TAG_NAME, "legend")
                        question_text = legend.text.strip()
                    except NoSuchElementException:
                        try:
                            label = fieldset.find_element(By.TAG_NAME, "label")
                            question_text = label.text.strip()
                        except NoSuchElementException:
                            continue
                    
                    if not question_text:
                        continue
                    
                    # Find input elements in this fieldset
                    inputs = fieldset.find_elements(By.XPATH, ".//input | .//select | .//textarea")
                    
                    for input_elem in inputs:
                        if not input_elem.is_displayed():
                            continue
                        
                        input_type = self._get_input_type(input_elem)
                        options = self._get_options(input_elem, fieldset)
                        
                        question = FormQuestion(
                            element=fieldset,
                            question_text=question_text,
                            input_type=input_type,
                            options=options
                        )
                        question.input_element = input_elem
                        questions.append(question)
                        break  # One question per fieldset
                        
            except Exception as e:
                self.logger.debug(f"Error in fieldset strategy: {str(e)}")
                
        return questions
    
    def _find_label_input_pairs(self) -> List[FormQuestion]:
        """Find label-input pairs"""
        questions = []
        
        # Find labels that are likely questions
        label_selectors = [
            "//label[contains(@class, 'jobs-easy-apply')]",
            "//label[contains(text(), '?')]",
            "//label[contains(@for, 'input')]",
            "//div[contains(@class, 'jobs-easy-apply')]//label",
            "//form//label"
        ]
        
        processed_labels = set()
        
        for selector in label_selectors:
            try:
                labels = self.driver.find_elements(By.XPATH, selector)
                for label in labels:
                    if not label.is_displayed():
                        continue
                    
                    label_text = label.text.strip()
                    if not label_text or label_text in processed_labels:
                        continue
                    
                    processed_labels.add(label_text)
                    
                    # Find associated input
                    input_elem = self._find_associated_input(label)
                    if not input_elem:
                        continue
                    
                    input_type = self._get_input_type(input_elem)
                    options = self._get_options(input_elem, label.find_element(By.XPATH, ".."))
                    
                    question = FormQuestion(
                        element=label,
                        question_text=label_text,
                        input_type=input_type,
                        options=options
                    )
                    question.label_element = label
                    question.input_element = input_elem
                    questions.append(question)
                    
            except Exception as e:
                self.logger.debug(f"Error in label-input strategy: {str(e)}")
                
        return questions
    
    def _find_standalone_inputs(self) -> List[FormQuestion]:
        """Find standalone inputs with placeholder or nearby text"""
        questions = []
        
        input_selectors = [
            "//input[@type='text']",
            "//input[@type='email']",
            "//input[@type='tel']",
            "//input[@type='number']",
            "//input[@type='url']"
        ]
        
        for selector in input_selectors:
            try:
                inputs = self.driver.find_elements(By.XPATH, selector)
                for input_elem in inputs:
                    if not input_elem.is_displayed():
                        continue
                    
                    # Skip if already processed as part of label-input pair
                    if self._is_input_already_processed(input_elem, questions):
                        continue
                    
                    question_text = ""
                    
                    # Try to find question text from various sources
                    # 1. Placeholder
                    placeholder = input_elem.get_attribute("placeholder")
                    if placeholder and len(placeholder.strip()) > 3:
                        question_text = placeholder.strip()
                    
                    # 2. Nearby text elements
                    if not question_text:
                        question_text = self._find_nearby_question_text(input_elem)
                    
                    # 3. aria-label
                    if not question_text:
                        aria_label = input_elem.get_attribute("aria-label")
                        if aria_label:
                            question_text = aria_label.strip()
                    
                    if not question_text:
                        continue
                    
                    input_type = self._get_input_type(input_elem)
                    
                    question = FormQuestion(
                        element=input_elem,
                        question_text=question_text,
                        input_type=input_type
                    )
                    question.input_element = input_elem
                    questions.append(question)
                    
            except Exception as e:
                self.logger.debug(f"Error in standalone input strategy: {str(e)}")
                
        return questions
    
    def _find_textarea_questions(self) -> List[FormQuestion]:
        """Find textarea questions"""
        questions = []
        
        try:
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            for textarea in textareas:
                if not textarea.is_displayed():
                    continue
                
                question_text = ""
                
                # Try to find associated label
                try:
                    # Find label by for attribute
                    textarea_id = textarea.get_attribute("id")
                    if textarea_id:
                        label = self.driver.find_element(By.XPATH, f"//label[@for='{textarea_id}']")
                        question_text = label.text.strip()
                except NoSuchElementException:
                    pass
                
                # Try placeholder
                if not question_text:
                    placeholder = textarea.get_attribute("placeholder")
                    if placeholder:
                        question_text = placeholder.strip()
                
                # Try nearby text
                if not question_text:
                    question_text = self._find_nearby_question_text(textarea)
                
                if not question_text:
                    question_text = "Please provide additional information"
                
                question = FormQuestion(
                    element=textarea,
                    question_text=question_text,
                    input_type="textarea"
                )
                question.input_element = textarea
                questions.append(question)
                
        except Exception as e:
            self.logger.debug(f"Error in textarea strategy: {str(e)}")
            
        return questions
    
    def _find_select_questions(self) -> List[FormQuestion]:
        """Find select/dropdown questions"""
        questions = []
        
        try:
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            for select_elem in selects:
                if not select_elem.is_displayed():
                    continue
                
                question_text = ""
                
                # Try to find associated label
                try:
                    select_id = select_elem.get_attribute("id")
                    if select_id:
                        label = self.driver.find_element(By.XPATH, f"//label[@for='{select_id}']")
                        question_text = label.text.strip()
                except NoSuchElementException:
                    pass
                
                # Try nearby text
                if not question_text:
                    question_text = self._find_nearby_question_text(select_elem)
                
                if not question_text:
                    question_text = "Please select an option"
                
                # Get options
                options = []
                try:
                    select_obj = Select(select_elem)
                    options = [option.text.strip() for option in select_obj.options if option.text.strip()]
                except Exception as e:
                    self.logger.debug(f"Error getting select options: {str(e)}")
                
                question = FormQuestion(
                    element=select_elem,
                    question_text=question_text,
                    input_type="select",
                    options=options
                )
                question.input_element = select_elem
                questions.append(question)
                
        except Exception as e:
            self.logger.debug(f"Error in select strategy: {str(e)}")
            
        return questions
    
    def _get_input_type(self, input_elem) -> str:
        """Determine the input type"""
        try:
            tag_name = input_elem.tag_name.lower()
            
            if tag_name == "select":
                return "select"
            elif tag_name == "textarea":
                return "textarea"
            elif tag_name == "input":
                input_type = input_elem.get_attribute("type")
                if input_type:
                    return input_type.lower()
                return "text"
            else:
                return "text"
                
        except Exception as e:
            self.logger.debug(f"Error getting input type: {str(e)}")
            return "text"
    
    def _get_options(self, input_elem, container) -> List[str]:
        """Get options for radio buttons, checkboxes, or selects"""
        options = []
        
        try:
            input_type = self._get_input_type(input_elem)
            
            if input_type == "select":
                select_obj = Select(input_elem)
                options = [option.text.strip() for option in select_obj.options if option.text.strip()]
                
            elif input_type in ["radio", "checkbox"]:
                # Find all radio/checkbox inputs with same name
                name = input_elem.get_attribute("name")
                if name:
                    similar_inputs = container.find_elements(
                        By.XPATH, f".//input[@name='{name}']"
                    )
                    
                    for inp in similar_inputs:
                        try:
                            # Try to find associated label
                            inp_id = inp.get_attribute("id")
                            if inp_id:
                                label = container.find_element(By.XPATH, f".//label[@for='{inp_id}']")
                                option_text = label.text.strip()
                                if option_text and option_text not in options:
                                    options.append(option_text)
                        except NoSuchElementException:
                            # Try to find nearby text
                            value = inp.get_attribute("value")
                            if value and value not in options:
                                options.append(value)
                                
        except Exception as e:
            self.logger.debug(f"Error getting options: {str(e)}")
            
        return options
    
    def _find_associated_input(self, label):
        """Find input element associated with a label"""
        try:
            # Try 'for' attribute first
            for_attr = label.get_attribute("for")
            if for_attr:
                try:
                    return self.driver.find_element(By.ID, for_attr)
                except NoSuchElementException:
                    pass
            
            # Try to find input within the label
            try:
                return label.find_element(By.XPATH, ".//input | .//select | .//textarea")
            except NoSuchElementException:
                pass
            
            # Try to find input after the label
            try:
                return label.find_element(By.XPATH, "./following-sibling::*[1]//input | ./following-sibling::*[1]//select | ./following-sibling::*[1]//textarea")
            except NoSuchElementException:
                pass
            
            # Try to find input in parent container
            try:
                parent = label.find_element(By.XPATH, "./..")
                return parent.find_element(By.XPATH, ".//input | .//select | .//textarea")
            except NoSuchElementException:
                pass
                
        except Exception as e:
            self.logger.debug(f"Error finding associated input: {str(e)}")
            
        return None
    
    def _find_nearby_question_text(self, input_elem) -> str:
        """Find question text near an input element"""
        try:
            # Try previous siblings
            try:
                prev_element = input_elem.find_element(By.XPATH, "./preceding-sibling::*[1]")
                text = prev_element.text.strip()
                if text and len(text) > 3:
                    return text
            except NoSuchElementException:
                pass
            
            # Try parent's text
            try:
                parent = input_elem.find_element(By.XPATH, "./..")
                parent_text = parent.text.strip()
                # Remove the input's own value from parent text
                input_value = input_elem.get_attribute("value") or ""
                if input_value:
                    parent_text = parent_text.replace(input_value, "").strip()
                if parent_text and len(parent_text) > 3:
                    return parent_text
            except:
                pass
            
            # Try aria-labelledby
            try:
                labelledby = input_elem.get_attribute("aria-labelledby")
                if labelledby:
                    label_elem = self.driver.find_element(By.ID, labelledby)
                    return label_elem.text.strip()
            except NoSuchElementException:
                pass
                
        except Exception as e:
            self.logger.debug(f"Error finding nearby question text: {str(e)}")
            
        return ""
    
    def _is_input_already_processed(self, input_elem, existing_questions: List[FormQuestion]) -> bool:
        """Check if an input element is already processed"""
        try:
            for question in existing_questions:
                if (question.input_element and 
                    question.input_element == input_elem):
                    return True
            return False
        except:
            return False
    
    def fill_question_answer(self, question: FormQuestion, answer: str) -> bool:
        """
        Fill in the answer for a specific question
        
        Args:
            question: FormQuestion object
            answer: Answer to fill in
            
        Returns:
            True if successfully filled, False otherwise
        """
        try:
            if not question.input_element:
                self.logger.warning(f"No input element for question: {question.question_text}")
                return False
            
            input_elem = question.input_element
            input_type = question.input_type
            
            self.logger.info(f"📝 Filling {input_type} question: '{question.question_text[:50]}...' with '{answer[:50]}...'")
            
            if input_type in ["text", "email", "tel", "number", "url"]:
                # Clear and type text
                input_elem.clear()
                input_elem.send_keys(answer)
                return True
                
            elif input_type == "textarea":
                # Clear and type text in textarea
                input_elem.clear()
                input_elem.send_keys(answer)
                return True
                
            elif input_type == "select":
                # Select from dropdown
                try:
                    select_obj = Select(input_elem)
                    
                    # Try to select by visible text
                    for option in select_obj.options:
                        if answer.lower() in option.text.lower() or option.text.lower() in answer.lower():
                            select_obj.select_by_visible_text(option.text)
                            return True
                    
                    # Try to select by value
                    for option in select_obj.options:
                        if answer.lower() in option.get_attribute("value").lower():
                            select_obj.select_by_value(option.get_attribute("value"))
                            return True
                    
                    # If no match found, select first non-empty option
                    for option in select_obj.options[1:]:  # Skip first option (usually placeholder)
                        if option.text.strip():
                            select_obj.select_by_visible_text(option.text)
                            self.logger.warning(f"No exact match for '{answer}', selected '{option.text}'")
                            return True
                            
                except Exception as e:
                    self.logger.error(f"Error selecting dropdown option: {str(e)}")
                    
            elif input_type == "radio":
                # Select radio button
                try:
                    name = input_elem.get_attribute("name")
                    if name:
                        # Find all radio buttons with same name
                        radio_buttons = self.driver.find_elements(By.XPATH, f"//input[@name='{name}' and @type='radio']")
                        
                        for radio in radio_buttons:
                            # Check associated label
                            try:
                                radio_id = radio.get_attribute("id")
                                if radio_id:
                                    label = self.driver.find_element(By.XPATH, f"//label[@for='{radio_id}']")
                                    if answer.lower() in label.text.lower() or label.text.lower() in answer.lower():
                                        radio.click()
                                        return True
                            except NoSuchElementException:
                                pass
                            
                            # Check value
                            value = radio.get_attribute("value")
                            if value and (answer.lower() in value.lower() or value.lower() in answer.lower()):
                                radio.click()
                                return True
                        
                        # If no match, click first radio button
                        if radio_buttons:
                            radio_buttons[0].click()
                            self.logger.warning(f"No exact match for '{answer}', selected first radio option")
                            return True
                            
                except Exception as e:
                    self.logger.error(f"Error selecting radio button: {str(e)}")
                    
            elif input_type == "checkbox":
                # Handle checkbox
                try:
                    # For checkboxes, if answer suggests "yes", check it
                    should_check = any(word in answer.lower() for word in ['yes', 'true', 'agree', 'accept', 'authorize'])
                    
                    if should_check and not input_elem.is_selected():
                        input_elem.click()
                        return True
                    elif not should_check and input_elem.is_selected():
                        input_elem.click()
                        return True
                    else:
                        return True  # Already in desired state
                        
                except Exception as e:
                    self.logger.error(f"Error handling checkbox: {str(e)}")
            
            return False
            
        except StaleElementReferenceException:
            self.logger.error("Element became stale during filling")
            return False
        except Exception as e:
            self.logger.error(f"Error filling question answer: {str(e)}")
            return False
