import os
import smtplib
import datetime
import time
from playwright.sync_api import Playwright, sync_playwright
from bs4 import BeautifulSoup
from faker import Faker
import argparse


fake = Faker()
d1 = fake.random.randint(10, 28)
d2 = fake.random.randint(10, 28)
email_credential = ""

CONST_CPH_GOOD_Price = 2100
CONST_Paris_GOOD_Price = 1800

results = []


def check_iwantthatflight(playwright: Playwright, items: [str]) -> None:

    browser = playwright.chromium.launch(headless=False)
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/69.0.3497.100 Safari/537.36"
    )
    context = browser.new_context(user_agent=ua)
    page = context.new_page()

    for idx, itm_str in enumerate(items):
        itm_str = str(itm_str)
        print(itm_str)
        flight_city_from_to = str(itm_str).split(",")

        flight_city = flight_city_from_to[0].strip()
        flight_from = flight_city_from_to[1].strip()
        flight_to = flight_city_from_to[2].strip()
        # url = f"https://fly.iwantthatflight.com.au/flight.ashx?&oc=SYD&dc=CPH&dd=29/Jun/2023&rd=15/Jul/2023&cur=AUD"
        url = f"https://fly.iwantthatflight.com.au/flight.ashx?&oc=SYD&dc={flight_city}&dd={flight_from}&rd={flight_to}&cur=AUD"
        # url = f"https://fly.iwantthatflight.com.au/flight.ashx?&oc=SYD&dc=CPH&dd={d1}/Jun/2023&rd={d2}/Jul/2023&cur=AUD"
        print(url)
        page.goto(url, wait_until='load')

        page.wait_for_timeout(1000)

        page.wait_for_selector('#msgfade', state='attached')
        # document.querySelector('#msgfade')!=null")
        page.wait_for_function("document.querySelector('#msgfade').hasAttribute('class')")
        page.wait_for_function("document.querySelector('#msgfade').getAttribute('class')=='complete'", timeout=60000)

        # page.is_visible('#MessageContainer')
        page.wait_for_selector('#MessageContainer', state='visible')

        page.locator("#Int_Filter_Contents").get_by_text("Scoot").click(delay=3000)

        page.locator("#Int_Filter_Contents").get_by_text("AirAsia X").first.click(delay=3000)

        # page.locator("#Int_Filter_Contents").get_by_text("SAS").click(delay=2000)
        # locator(".slider-duration > .slider > .slider-track > .slider-selection")
        # page.locator(".slider-duration > .slider > .slider-track > .slider-selection").hover()
        # page.locator('.slider-duration > .slider > .max-slider-handle').hover()


        # page.get_by_text("Scoot").click(delay=3000)

        price_list_html = page.inner_html("#LeaveCalender")
        # print(price_list_html)
        soup = BeautifulSoup(price_list_html, 'html.parser')
        price_items = soup.select('.plan-price.PriceResult.Int_PriceResult')

        results.append(f"{itm_str.replace('/2023','').replace('/','-')}")
        results.append(url)

        for idx, price_item in enumerate(price_items):

            price_value = int(str(price_item.contents[0]).replace("$", ""))

            print(f"{price_value}")

            if itm_str.startswith("CPH"):
                if price_value < CONST_CPH_GOOD_Price:
                    price_value = str(price_value) + " ***"

            if itm_str.startswith("CDG"):
                if price_value < CONST_Paris_GOOD_Price:
                    price_value = str(price_value) + " ***"

            results.append(f"- {price_value}")

            if idx == 1:
                results.append("\n")
                break

        time.sleep(10)

    context.close()
    browser.close()


def send_email(subject, body, email="c o d e n a m e m 2 7 @ g m a i l . c o m"):
    user = "rwudev1"
    pwd = email_credential
    recipient = email.replace(" ", "")
    FROM = "Price Checker"
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


def test():
    global email_credential
    email_credential = os.environ["email_mima"]

    ss = "CPH, 30/Jun/2023, 30/Jul/2023"
    print(ss.replace("/2023",""))

    results.append("CPH, 30/Jun, 30/Jul")
    results.append("- $2127")
    results.append("- $2159\n")
    results.append("CPH, 15/Jun, 15/Jul")
    results.append("- $2127")
    results.append("- $2226\n")

    email_body = "\n".join(results)

    aaa = "abc"
    aaa += " ***"
    print(aaa)

    # send_email("test", email_body)
    exit()

def main():

    # test()

    parser = argparse.ArgumentParser()
    parser.add_argument('--flight_list_file', type=str)

    args = parser.parse_args()

    with open(args.flight_list_file) as file:
        flight_items = [line.rstrip() for line in file]

    print(flight_items)

    try:
        global email_credential
        email_credential = os.environ["email_mima"]
        print("Retrieved credential.")
    except KeyError:
        print("email_mima not available!")

    with sync_playwright() as playwright:
        check_iwantthatflight(playwright, flight_items)

    for itm in results:
        print(itm)

    email_body = f"CPH: {CONST_CPH_GOOD_Price}\nCDW: {CONST_Paris_GOOD_Price}\n\n"
    email_body += "\n".join(results)

    send_email("Flight Checker", email_body)

if __name__ == '__main__':
    main()
