import concurrent.futures
import json
import os
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def strip_emoji(word):
    char_list = [word[j] for j in range(len(word)) if ord(word[j]) in range(65536)]
    word = ''
    for j in char_list:
        word = word + j
    return word


class Crawler:
    def __init__(self, query, tk):
        self.url = "https://www.google.com/maps/?hl=en"
        self.query = query
        self.browser = None
        self.all_links = []
        self.details = {}
        self.get_init_details()
        self.tk = tk

    def get_browser(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        browser = webdriver.Chrome(options=options, executable_path=ChromeDriverManager().install())
        return browser

    def get_init_details(self):
        self.details = {"name": "", "category": "", "rating": "", "address": "", "website": "", "phone": "",
                        "plus_code": "", "main_image": "", "review_count": 0, "photo_tags": [], "working_hours": [],
                        "location": {"latitude": "", "longitude": ""}}

    def scroll_to_bottom(self):
        scrollbar = self.browser.find_elements_by_xpath("//div[@role='region']")
        for s in scrollbar:
            if "Results for" in s.get_attribute("aria-label"):
                for i in range(0, 8):
                    s.send_keys(Keys.END)
                    time.sleep(1)

    def crawl(self):
        self.tk.add_label("Starting the crawl...")
        self.browser = self.get_browser()
        self.browser.get(self.url)
        # Search the query
        search = self.browser.find_element_by_name("q")
        search.send_keys(self.query)
        search.send_keys(Keys.ENTER)
        self.tk.add_label("Searching the query...")
        # Wait till page loads
        wait = WebDriverWait(self.browser, 100)
        wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@role='region']")))
        # Loop through all the pages
        self.tk.add_label("Getting Businesses...")
        content_count = 0
        content_label = self.tk.add_label("Businesses Fetched...: 0")
        button = self.browser.find_elements_by_xpath('//button[@jsaction="pane.paginationSection.nextPage"]')
        while True:
            # Scroll To Bottom
            self.scroll_to_bottom()
            # Get Link to Business Page on Google Map
            contents = self.browser.find_elements_by_css_selector('div.section-scrollbox > div')
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                {executor.submit(self.handle_content, content) for content in contents}
            # for content in contents:
            #     self.handle_content(content)
            if len(contents) > 0:
                content_label.grid_remove()
                content_count = content_count + len(contents)
                content_label = self.tk.add_label("Businesses Fetched...: " + str(content_count))
            # If there is no next button exit the loop
            if button[0].is_displayed():
                pass
            else:
                self.tk.add_label("Fetched All " + str(content_count) + " Businesses")
                break
            # If the next button is disabled, exit the loop
            if button[0].get_property("disabled") is False:
                try:
                    button[0].click()
                except:
                    time.sleep(0.5)
                    continue
            else:
                self.tk.add_label("Fetched All " + str(content_count) + " Businesses")
                break
        self.get_info()

    def get_info(self):
        self.tk.add_label("Removing duplicate entries...")
        unique_links = []
        for link in self.all_links:
            if link not in unique_links and "maps" in link:
                unique_links.append(link)
        self.all_links = unique_links
        self.tk.add_label("Found " + str(len(self.all_links)) + " businesses...")
        self.tk.add_label("Getting business information...")
        self.details["photo_tags"] = []
        total_info = 0
        fetched_info = self.tk.add_label("Fetched information..: 0")
        for link in self.all_links:
            self.get_init_details()
            self.browser.get(link)
            try:
                WebDriverWait(self.browser, 20).until(EC.url_changes(self.browser.current_url))
            except TimeoutException:
                self.browser.get(link)
                WebDriverWait(self.browser, 20).until(EC.url_changes(self.browser.current_url))
            except Exception:
                continue
            self.get_business_name()
            self.get_business_rating()
            self.get_address()
            self.get_phone_number()
            self.get_website()
            self.get_plus_code()
            self.get_category()
            self.get_main_image()
            self.review_count()
            self.get_photo_tags()
            self.get_location()
            self.get_working_hours()
            total_info += 1
            fetched_info.grid_remove()
            fetched_info = self.tk.add_label("Fetched information..: " + str(total_info))
            self.write_to_file()
            self.tk.insert_row(total_info, self.details)
        self.browser.close()
        self.browser.quit()

    def get_business_rating(self):
        try:
            rating_div = self.browser.find_element_by_xpath("//div[@jsaction='pane.rating.moreReviews']")
            rating = rating_div.find_element_by_css_selector("span > span > span")
            self.details["rating"] = rating.text
        except:
            pass

    def get_business_name(self):
        try:
            title = self.browser.find_element_by_css_selector("h1 > span")
            title = strip_emoji(title.text)
            self.details["name"] = title
        except:
            pass

    def get_location(self):
        current_url = self.browser.current_url
        start = '@'
        end = '/data'
        try:
            lat_long = current_url[current_url.index(start) + len(start):current_url.index(end)]
            lat_long = lat_long.split(",")
            self.details["location"] = {"latitude": lat_long[0], "longitude": lat_long[1]}
        except:
            pass

    def get_working_hours(self):
        try:
            table_div = self.browser.find_element_by_xpath("//div[@data-hide-tooltip-on-mouse-move='true']")
            table_div.click()
            working_hours = self.browser.find_elements_by_tag_name("table > tbody > tr")
            self.details["working_hours"] = []
            for wh in working_hours:
                try:
                    day = wh.find_element_by_tag_name("th > div").text
                    hour = wh.find_element_by_tag_name("td > ul > li").text
                    self.details["working_hours"].append({"day": day, "hour": hour})
                except:
                    continue
        except:
            pass

    def get_address(self):
        try:
            addresses = self.browser.find_elements_by_xpath("//button[@data-item-id='address']")
            for address in addresses:
                if address.get_attribute("aria-label"):
                    address = address.get_attribute("aria-label")
                    self.details["address"] = address.replace("Address: ", "")
        except:
            pass

    def get_phone_number(self):
        try:
            phone_numbers = self.browser.find_elements_by_xpath("//button[@data-tooltip='Copy phone number']")
            for phone_number in phone_numbers:
                if phone_number.get_attribute("data-item-id") and phone_number.get_attribute("aria-label"):
                    phone_number = phone_number.get_attribute("aria-label")
                    self.details["phone"] = phone_number.replace("Phone: ", "")
        except:
            pass

    def get_website(self):
        try:
            websites = self.browser.find_elements_by_xpath("//button[@data-item-id='authority']")
            for website in websites:
                if website.get_attribute("aria-label"):
                    website = website.get_attribute("aria-label")
                    self.details["website"] = website.replace("Website: ", "")
        except:
            pass

    def get_plus_code(self):
        try:
            plus_codes = self.browser.find_elements_by_xpath("//button[@data-item-id='oloc']")
            for plus_code in plus_codes:
                if plus_code.get_attribute("aria-label"):
                    plus_code = plus_code.get_attribute("aria-label")
                    self.details["plus_code"] = plus_code.replace("Plus code: ", "")
        except:
            pass

    def get_category(self):
        try:
            categories = self.browser.find_elements_by_xpath("//button[@jsaction='pane.rating.category']")
            for category in categories:
                self.details["category"] = category.text
        except:
            pass

    def get_main_image(self):
        try:
            images = self.browser.find_elements_by_xpath("//button[@jsaction='pane.heroHeaderImage.click']")
            for image in images:
                img = image.find_element_by_tag_name("img")
                self.details["main_image"] = img.get_attribute("src")
        except:
            pass

    def review_count(self):
        try:
            reviews = self.browser.find_elements_by_xpath("//button[@jsaction='pane.reviewChart.moreReviews']")
            for review in reviews:
                self.details["review_count"] = review.text
        except:
            pass

    def get_photo_tags(self):
        try:
            photo_tags = self.browser.find_elements_by_xpath("//button[@jsaction='pane.carousel.photo']")
            for photo_tag in photo_tags:
                if photo_tag.get_attribute("aria-label"):
                    self.details["photo_tags"].append(photo_tag.get_attribute("aria-label"))
        except:
            pass

    def handle_content(self, content):
        links = content.find_elements_by_tag_name("a")
        for link in links:
            href = link.get_attribute('href')
            self.all_links.append(href)

    def write_to_file(self):
        file = os.getcwd() + "/" + self.query + ".txt"
        with open(file, 'a') as f:
            f.write(json.dumps(self.details) + "\n")
