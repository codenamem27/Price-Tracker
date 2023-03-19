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
from datetime import datetime

from bs4 import Tag


fake = Faker()
d1 = fake.random.randint(10, 28)
d2 = fake.random.randint(10, 28)
email_credential = ""

results = []

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[logging.FileHandler("momondo_checker.log"), logging.StreamHandler()])


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


def check_momondo(playwright: Playwright, all_flight_items: [str]) -> None:

    result = []
    email_msg = MIMEMultipart('related')
    flight_city = "undefined"

    browser = playwright.chromium.launch(headless=False)
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/69.0.3497.100 Safari/537.36"
    )


    for idx, flight_item_str in enumerate(all_flight_items):

        context = browser.new_context(user_agent=ua)
        page = context.new_page()

        flight_item_data = str(flight_item_str).split(",")
        flight_city = flight_item_data[0].strip()
        flight_from = datetime.strptime(flight_item_data[1].strip(), "%d/%b/%Y").strftime("%Y-%m-%d")
        flight_to = datetime.strptime(flight_item_data[2].strip(), "%d/%b/%Y").strftime("%Y-%m-%d")
        flight_threshold = int(flight_item_data[3].strip())

        d1 = fake.random.randint(10, 28)
        d2 = fake.random.randint(10, 28)

        url = f"https://www.momondo.com.au/flight-search/SYD-{flight_city}/{flight_from}/{flight_to}?sort=price_a"
        # url = f"https://www.momondo.com.au/flight-search/SYD-CPH/2023-06-{d1}/2023-07-{d2}?sort=price_a"
        print(url)

        page.goto(url, wait_until='domcontentloaded', timeout=3000)
        # page.wait_for_timeout(5000)

        page.wait_for_function("document.querySelector('.skp2.skp2-inlined').getAttribute('aria-hidden')=='true'", timeout=90000)
        results.append(f"<p style='font-size:15px; font-weight: bold;'>{flight_item_str.replace('/2023', '').replace('/', '-')}</p>")

        # price_list_html = page.inner_html(".Ui-Flights-Results-Components-ListView-container")
        items = page.query_selector_all(".Ui-Flights-Results-Components-ListView-container div[data-resultid]")
        for idx, flight_itm in enumerate(items):
            if idx ==0:
                # skip the advertisement fare
                continue

            item_price = flight_itm.query_selector("div[class*='-price-text-container'] div")
            price_value = int(item_price.inner_html().replace("$", "").replace(",", ""))

            if price_value < flight_threshold:
                results.append(f"{price_value} *****<br>")
            else:
                results.append(f"{price_value} <br>")

            print(item_price.inner_html().replace("$", "").replace(",", ""))
            if idx == 2:
                break
        results.append(f"{url}<br><br>")

        context.close()
        time.sleep(3)


        # soup = BeautifulSoup(price_list_html, 'html.parser')
        # all_items = soup.select("div[data-resultid]")
        #
        # first_item: Tag = all_items[0]
        #
        # result: Tag = first_item.select("div[class*='-price-text-container'] div")[0]
        # print(result.next_element)
        # page.pause()

    browser.close()

    send_html_email(email_msg, "\n".join(results), f"Flight Checker: {flight_city} - Momondo")


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
        check_momondo(playwright, flight_items)


if __name__ == '__main__':
    main()
