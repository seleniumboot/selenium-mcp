"""Shared locator strategy map — imported by element_tools and assertion_tools."""

from selenium.webdriver.common.by import By

BY_MAP = {
    "css":          By.CSS_SELECTOR,
    "xpath":        By.XPATH,
    "id":           By.ID,
    "name":         By.NAME,
    "tag":          By.TAG_NAME,
    "class":        By.CLASS_NAME,
    "link":         By.LINK_TEXT,
    "partial_link": By.PARTIAL_LINK_TEXT,
}
