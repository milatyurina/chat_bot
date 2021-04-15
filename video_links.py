import os
from selenium import webdriver
import traceback
from selenium.webdriver.support.wait import WebDriverWait


def get_links(my_driver):
    my_urls = []
    elements = my_driver.find_elements_by_class_name("ga-link")
    for i in elements:
        if str(i.get_attribute('class').strip()) == 'ga-link':
            my_urls.append(i.get_attribute("href"))
    return my_urls

#os.getcwd()
urls = []
#driver = webdriver.Chrome()
chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)


# we only want videos in English under 6 minutes long
my_page = "https://www.ted.com/talks?sort=newest&duration=0-6&language=en"
driver.get(my_page)
driver.maximize_window()
close_pop_up = '#recommends-banner > div > div > div > div > div > div.css-1srpqz2 > button > svg'
# selector for next page
selector = '#browse-results > div.results__pagination > div > a.pagination__next.pagination__flipper.pagination__link'
driver.implicitly_wait(2)
driver.find_element_by_css_selector(close_pop_up).click()

while True:
    driver.implicitly_wait(10)
# scroll down otherwise the next page is blocked
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
# wait until the function gets all the links of the page
    links = WebDriverWait(driver, timeout=120).until(lambda dr: get_links(dr))
    urls.append(links)

    try:
        driver.implicitly_wait(5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.find_element_by_css_selector(selector).click()

    except Exception as exception:
        traceback.print_exc()
        break

driver.close()

# remove duplicates from the URL list
clean_urls = set()
for page in urls:
    for url in page:
        clean_urls.add(url)
# save URLs to the file so that they could be pulled randomly
with open('urls.txt', 'w') as file:
    for url in clean_urls:
        file.write(url+'\n')
