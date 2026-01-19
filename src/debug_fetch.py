from src.fetch_kinoprogramm import fetch_schedule_html
import logging

logging.basicConfig(level=logging.INFO)

html = fetch_schedule_html()
if html:
    with open("debug_html.html", "w") as f:
        f.write(html)
    print("Saved debug_html.html")
else:
    print("Failed to fetch HTML")
