#------------------- IMPORT PACKAGES FOR DATA PROCESSING ----------------------#

# Manage datasets
import pandas as pd

# Pause between requests, and work with dates
import time
from datetime import date

# Regular expressions for cleaning text
import re

# Make folders for diagnostic files
import os

# Parse and prettify HTML obtained from scraping
from bs4 import BeautifulSoup

#------------------- IMPORT PACKAGES FOR WEB SCRAPING -------------------------#

# Automate navigating within the browser (SELENIUM)
#------ webdriver: open and control Chrome
#------ Options:   browser configuration (e.g. headless)
#------ By:        common locator strategies (xpath)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by      import By
