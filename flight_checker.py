import os
import smtplib
import datetime
import time
from playwright.sync_api import Playwright, sync_playwright, Page
from bs4 import BeautifulSoup
from faker import Faker
import argparse
import logging

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

fake = Faker()
d1 = fake.random.randint(10, 28)
d2 = fake.random.randint(10, 28)
email_credential = ""

results = []

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[logging.FileHandler("flight_checker.log"), logging.StreamHandler()])


def check_locator_and_click(pg: Page, item_name: str):

    error_score: int = 0

    try:
        element = pg.locator("#Int_Filter_Contents").get_by_text(item_name).first
        if element:
            print(f"Found '{item_name}' and clicked")
            element.click(delay=2000)
            pg.wait_for_timeout(3000)
        else:
            print(f"'{item_name}' is Missing, skipped")
            error_score = 1
    except:
        print(f"** Failed to locate element: {item_name}")
        error_score = 10

    return error_score

def attach_img(msg: MIMEMultipart, image_file: str):
    fp = open(image_file, "rb")
    msg_image = MIMEImage(fp.read())
    fp.close()

    msg_image.add_header("Content-ID", f"<{image_file}>")
    msg.attach(msg_image)

    return msg


def check_iwantthatflight(playwright: Playwright, items: [str]) -> None:

    browser = playwright.chromium.launch(headless=True)
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/69.0.3497.100 Safari/537.36"
    )

    email_msg = MIMEMultipart('related')

    flight_city = ""

    for idx, itm_str in enumerate(items):

        error_score = 0
        error_score_display = ""

        context = browser.new_context(user_agent=ua)
        page = context.new_page()

        itm_str = str(itm_str)
        print(itm_str)
        flight_city_from_to = str(itm_str).split(",")

        flight_city = flight_city_from_to[0].strip()
        flight_from = flight_city_from_to[1].strip()
        flight_to = flight_city_from_to[2].strip()
        flight_threshold = int(flight_city_from_to[3].strip())

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

        error_score += check_locator_and_click(page, "3 Stops")
        error_score += check_locator_and_click(page, "AirAsia X")
        error_score += check_locator_and_click(page, "Scoot")
        error_score += check_locator_and_click(page, "Cebu Pacific")
        error_score += check_locator_and_click(page, "AirAsia")
        # check_locator_and_click(page, "Ryanair")
        error_score += check_locator_and_click(page, "Vietnam Airlines")

        # page.pause()

        price_list_html = page.inner_html("#LeaveCalender")
        # print(price_list_html)
        soup = BeautifulSoup(price_list_html, 'html.parser')
        price_items = soup.select('.plan-price.PriceResult.Int_PriceResult')

        if error_score > 0:
            error_score_display = f"({str(error_score)})"

        results.append(f"<p style='font-size:15px; font-weight: bold;'>{itm_str.replace('/2023', '').replace('/', '-')} {error_score_display}</p>")

        for idx, price_item in enumerate(price_items):

            price_value = int(str(price_item.contents[0]).replace("$", ""))

            print(f"{price_value}")
            if price_value < flight_threshold:
                print(f"threshold: {flight_threshold}")
                results.append(f"{price_value} *****<br>")

                ss_file_name = f"{flight_city}-{flight_from.replace('/', '')}-{flight_to.replace('/', '')}-{fake.random.randint(1000, 2000)}.jpg"
                page.locator(".plan.return-plan").nth(idx).screenshot(path=ss_file_name)

                results.append(f"<img src='cid:{ss_file_name}' alt='Price' ><br>")
                email_msg = attach_img(email_msg, ss_file_name)

            else:
                results.append(f"{price_value} <br>")

            if idx == 1:
                # results.append("\n")
                break

        results.append(f"<p>{url}</p>")

        context.close()
        time.sleep(2)

    browser.close()

    send_html_email(email_msg, "\n".join(results), f"Flight Checker: {flight_city}")


def send_html_email(msg: MIMEMultipart, result_html: str, subject: str):

    print(result_html)

    user = "rwudev1"
    pwd = email_credential

    recipient = "c o d e n a m e m 2 7 ! g m a i l . c o m"
    recipient = recipient.replace(" ", "").replace("!", "@")

    FROM = user
    TO = recipient if isinstance(recipient, list) else [recipient]

    msg['Subject'] = subject

    html = f"""\
    <html>
      <head></head>
        <body>
            {result_html}
        </body>
    </html>
    """

    # Record the MIME types of text/html.
    part2 = MIMEText(html, 'html')
    # Attach parts into message container.
    msg.attach(part2)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(user, pwd)
        server.sendmail(FROM, TO, msg.as_string())
        server.close()
        logging.info('successfully sent the mail')
    except Exception as ex:
        logging.info(f"Failed to send mail:\n{ex}")


def main():

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


if __name__ == '__main__':
    main()
