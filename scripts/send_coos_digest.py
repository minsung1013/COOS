import argparse
import os
import re
import smtplib
import sys
from email.message import EmailMessage

import requests
from bs4 import BeautifulSoup

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


COMMUNITY_URL = "https://coos.kr/community"


def log(msg: str) -> None:
    print(msg, flush=True)


def load_env() -> None:
    if load_dotenv:
        load_dotenv()


def fetch_html(use_playwright: bool) -> str:
    if not use_playwright:
        log("Fetching page via requests...")
        resp = requests.get(COMMUNITY_URL, timeout=20)
        resp.raise_for_status()
        return resp.text

    log("Fetching page via Playwright (Chromium)...")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright not installed. Set USE_PLAYWRIGHT=false or install playwright."
        ) from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(COMMUNITY_URL, timeout=30000, wait_until="networkidle")
        html = page.content()
        browser.close()
    return html


def parse_posts(html: str):
    soup = BeautifulSoup(html, "html.parser")

    rows = soup.find_all("tr")
    posts = []
    time_pattern = re.compile(r"^\d{1,2}:\d{2}$")

    for tr in rows:
        cells = tr.find_all(["td", "th"])
        if len(cells) < 3:
            continue

        date_cell = None
        for c in cells:
            text = c.get_text(strip=True)
            if time_pattern.match(text):
                date_cell = text
                break
        if not date_cell:
            continue

        title = None
        link = None
        for c in cells:
            a = c.find("a")
            if a and a.get_text(strip=True):
                title = a.get_text(strip=True)
                href = a.get("href") or ""
                if href.startswith("/"):
                    link = f"https://coos.kr{href}"
                elif href.startswith("http"):
                    link = href
                else:
                    link = None
                break
        if not title:
            title = cells[0].get_text(strip=True) if cells else None
        if not title:
            continue

        posts.append({"title": title, "link": link, "date": date_cell})

    todays = [p for p in posts if time_pattern.match(p["date"])]
    return todays


def build_email_body(posts):
    if not posts:
        return "오늘 올라온 게시글이 없습니다."

    lines = ["오늘 올라온 게시글:"]
    for idx, p in enumerate(posts, 1):
        if p["link"]:
            lines.append(f"{idx}. {p['title']} - {p['link']}")
        else:
            lines.append(f"{idx}. {p['title']}")
    return "\n".join(lines)


def send_email(body: str):
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")
    mail_from = os.environ.get("MAIL_FROM", user)
    mail_to = os.environ.get("MAIL_TO")

    if not user or not password or not mail_to:
        raise RuntimeError("SMTP_USER, SMTP_PASS, MAIL_TO must be set")

    msg = EmailMessage()
    msg["Subject"] = "COOS 커뮤니티 오늘 게시글"
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg.set_content(body)

    log(f"Sending email to {mail_to} via {host}:{port} as {user}...")
    with smtplib.SMTP(host, port, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.login(user, password)
        server.send_message(msg)


def main():
    parser = argparse.ArgumentParser(description="Send COOS community digest for today")
    parser.add_argument(
        "--use-playwright", action="store_true", help="force Playwright fetch"
    )
    args = parser.parse_args()

    load_env()

    use_playwright = (
        args.use_playwright
        or os.environ.get("USE_PLAYWRIGHT", "false").lower() == "true"
    )

    html = fetch_html(use_playwright)
    posts = parse_posts(html)
    log(f"Found {len(posts)} posts for today")
    body = build_email_body(posts)
    send_email(body)
    log("Done")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"Error: {e}")
        sys.exit(1)
