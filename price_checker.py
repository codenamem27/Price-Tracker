import datetime
import time

from playwright.sync_api import Playwright, sync_playwright
from bs4 import BeautifulSoup
from faker import Faker

import smtplib


fake = Faker()
d1 = fake.random.randint(10, 28)
d2 = fake.random.randint(10, 28)


def check_amazon_item_price(playwright: Playwright, item_name: str, item_id: str, desired_price: float) -> None:

    browser = playwright.chromium.launch(headless=True)
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/69.0.3497.100 Safari/537.36"
    )
    context = browser.new_context(user_agent=ua)
    page = context.new_page()

    # url = f"https://www.amazon.com.au/dp/B00IMF1CDO"
    url = f"https://www.amazon.com.au/dp/{item_id}"
    page.goto(url, wait_until='domcontentloaded')
    # aaa = page.content()
    page.is_visible('#corePrice_feature_div')

    price_list_html = page.inner_html("#desktop_buybox")
    # print(price_list_html)
    soup = BeautifulSoup(price_list_html, 'html.parser')
    #document.querySelector('#desktop_buybox .a-box-group #corePrice_feature_div .a-price.a-text-price')

    price_item = soup.select('#corePrice_feature_div .a-offscreen')
    if len(price_item) == 0:
        # books
        price_item = soup.select('#booksHeaderInfoContainer #booksHeaderSection #price')

    print(f"{item_name} - Target: {desired_price}")
    current_price = str(price_item[0].string).removeprefix('$')
    print(f"- {current_price}")

    if float(current_price) <= desired_price:
        print("good deal")
        # send_email(subject=f"{item_name} - C: {current_price}: T:{desired_price}", body=f"{item_name}: {url}")
    else:
        pass
        # print("not good")

    context.close()
    browser.close()

    # time.sleep(7200)
    # time.sleep(20)


def main():

  print("foobar")
  
  with sync_playwright() as playwright:
    check_amazon_item_price(playwright, "Wera Ratchet Small Set", "B004VMWZLU", 150)


if __name__ == '__main__':
    main()
