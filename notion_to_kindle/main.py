import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import smtplib
from readability import Document
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

# notion
from notion_client import Client
from .config import (
    NOTION_API_KEY,
    NOTION_DATABASE_ID,
    GMAIL_EMAIL,
    GMAIL_PASSWORD,
    KINDLE_EMAIL,
)


notion = Client(auth=NOTION_API_KEY)


def send_email(subject, html_content, attachment_name="Article.html"):
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = GMAIL_EMAIL
    msg["To"] = KINDLE_EMAIL

    attachment = MIMEApplication(html_content, _subtype="html")
    attachment.add_header("Content-Disposition", "attachment", filename=attachment_name)
    msg.attach(attachment)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_EMAIL, GMAIL_PASSWORD)
        server.sendmail(GMAIL_EMAIL, [KINDLE_EMAIL], msg.as_string())


def extract_article_bs(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    doc = Document(response.text)
    content_html = doc.summary()

    # Remove the body tag from content
    content_soup = BeautifulSoup(content_html, "html.parser")
    body_tag = content_soup.find("body")
    content = body_tag.decode_contents() if body_tag else content_html

    # Extract the title using BeautifulSoup
    title_tag = soup.find("h1", class_="entry-title")
    if not title_tag:
        title_tag = soup.find("h1", class_=lambda x: x and "post__title__title" in x)
    if not title_tag:
        title_tag = soup.find("title")
    title = title_tag.get_text() if title_tag else ""

    return title, content


def get_notion_articles():
    database_response = notion.databases.query(
        **{
            "database_id": NOTION_DATABASE_ID,
            # "filter": {
            # "property": "Landmark",
            # "rich_text": {
            #     "contains": "Bridge",
            # },
            # },
        }
    )

    pages = database_response["results"]
    html_contents = []

    for page in pages:
        page_url = page["properties"]["URL"]["url"]

        if page_url.endswith(".pdf"):
            continue

        article_title, content = extract_article_bs(page_url)
        html_contents.append((article_title, content))

        with open(f"page_content_{article_title}.html", "w") as f:
            f.write(str(content))

        # Update the Notion page
        notion.pages.update(page["id"], properties={"read": {"checkbox": True}})

    utc_now = datetime.utcnow()
    humanized_date = utc_now.strftime("%B %d, %Y")
    random_3_digit_number = str(utc_now.microsecond)[:3]

    title = (
        f"Today's Feed {datetime.now().strftime('%B %d, %Y')} {random_3_digit_number}"
    )
    # Create an index
    index_html = f"<html><head><title>{title}</title></head><body>"
    index_html += f"<h1>{title}</h1>"
    index_html += "<hr>"
    index_html += "<h2>Index</h2>"
    for i, (article_title, _) in enumerate(html_contents):
        index_html += f'<h3><a href="#article-{i}">{article_title}</a></h3>'
    index_html += "<hr>"

    # Concatenate all HTML content with anchors
    combined_content = index_html
    for i, (article_title, content_tags) in enumerate(html_contents):
        combined_content += f'<a name="article-{i}"></a><h2>{article_title}</h2>'
        for tag in content_tags:
            combined_content += str(tag)
        combined_content += "<hr>"

    combined_content += "</body></html>"

    # Save the final HTML that is going to be sent
    with open("final_output.html", "w") as f:
        f.write(combined_content)
    # Send a single email with the concatenated content and index
    send_email(title, combined_content, attachment_name=f"{title}.html")

    with open("response.json", "w") as f:
        f.write(json.dumps(database_response, indent=4))


def main():
    get_notion_articles()


if __name__ == "__main__":
    main()
