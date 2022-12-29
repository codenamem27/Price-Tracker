import os
import smtplib
import datetime
import time
from playwright.sync_api import Playwright, sync_playwright
from bs4 import BeautifulSoup
from faker import Faker


fake = Faker()
d1 = fake.random.randint(10, 28)
d2 = fake.random.randint(10, 28)
email_credential = ""

def check_amazon_item_price(playwright: Playwright, item_name: str, item_id: str, 
                            desired_price: float, is_gh_action: False) -> None:

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

    print(f"item url is: {url}")
    page.goto(url, wait_until='domcontentloaded')

    if is_gh_action:

        page.locator("#nav-global-location-popover-link").click(delay=2000)

        page.get_by_role("textbox", name="or enter a postcode in Australia").click()
        page.get_by_role("textbox", name="or enter a postcode in Australia").type(text="2000", delay=10)

        page.locator("#GLUXPostalCodeWithCity_DropdownList").select_option('HAYMARKET')

        page.get_by_role("button", name="Submit").click()
        page.wait_for_load_state(state="domcontentloaded", timeout=2000)
        
        start_time = datetime.datetime.now().replace(microsecond=0)
        page.wait_for_selector('#qualifiedBuybox', state='visible', timeout=50000)
        end_time = datetime.datetime.now().replace(microsecond=0)
        print(f"waited '#qualifiedBuybox' for: {end_time-start_time}")
    
    # page.is_visible('#corePrice_feature_div')
    page.wait_for_selector('#corePrice_feature_div', state='visible', timeout=30000)


    price_list_html = page.inner_html("#desktop_buybox")

    # debug
    # print(price_list_html)

    soup = BeautifulSoup(price_list_html, 'html.parser')
    #document.querySelector('#desktop_buybox .a-box-group #corePrice_feature_div .a-price.a-text-price')

    price_item = soup.select('#corePrice_feature_div .a-offscreen')
    print(f"print_item: {price_item}")
    if len(price_item) == 0:    
        price_item = soup.select('#booksHeaderInfoContainer #booksHeaderSection #price')

    print(f"{item_name} - Target: {desired_price}")
    current_price = str(price_item[0].string).removeprefix('$')
    print(f"- {current_price}")

    if float(current_price) <= desired_price:
        print("good deal")
        send_email(subject=f"{item_name} - Current:{current_price}, Target:{desired_price}", body=f"{item_name}: {url}")
    else:
        pass
        # print("not good")

    context.close()
    browser.close()


def send_email(subject, body):

    user = "rwudev1"
    pwd = email_credential
    recipient = "codenamem27@gmail.com"
    FROM = "Price Checker<rwudev1@gmail.com>"
    TO = recipient if isinstance(recipient, list) else [recipient]
    # SUBJECT = subject
    # TEXT = body

    message = f"Subject: {subject} \n\n{body}"
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(user, pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        print('Email notification sent successfully.')
    except Exception as ex: 
        print(f"failed to send mail with exception:\n{ex}")


def main():
    
    try:
        global email_credential
        email_credential = os.environ["email_mima"]
        print("Retrieved credential.")
    except KeyError:
        email_credential = "email_mima not available!"
    
    with sync_playwright() as playwright:
        check_amazon_item_price(playwright, "Wera Ratchet Small Set", "B004VMWZLU", 150, True)


if __name__ == '__main__':
    main()
