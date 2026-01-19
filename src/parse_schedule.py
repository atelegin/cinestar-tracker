import logging
import re
from datetime import datetime, timedelta
import bs4
from bs4 import BeautifulSoup
import pytz

logger = logging.getLogger(__name__)

class Session:
    def __init__(self, title_raw, dt_local, film_url, tags_raw):
        self.title = title_raw
        self.dt_local = dt_local
        self.film_url = film_url
        self.tags = tags_raw

    def __repr__(self):
        return f"<Session {self.title} @ {self.dt_local}>"

def parse_schedule(html_content: str, timezone_str: str = "Europe/Berlin") -> list[Session]:
    soup = BeautifulSoup(html_content, 'html.parser')
    tz = pytz.timezone(timezone_str)
    sessions = []

    # Find the current year from the header if possible, else default to now
    # Example: <span class="text-white">Montag 19.01.2026</span>
    year = datetime.now().year
    header_date = soup.find('div', class_='today')
    if header_date:
        date_text = header_date.get_text()
        match = re.search(r'\d{2}\.\d{2}\.(\d{4})', date_text)
        if match:
            year = int(match.group(1))

    # Iterate over movie rows
    # The container structure is a bit loose. look for div.row that has .city_filmtitel
    movie_rows = soup.find_all('div', class_='row')
    
    for row in movie_rows:
        title_div = row.find('div', class_='city_filmtitel')
        if not title_div:
            continue
            
        # Extract title and link
        # Look for the second <a> tag in .first div usually, or check title attribute
        # HTML: <a class="h3" href="..." title="Kinofilm Title">Title</a>
        link_tag = title_div.find('a', title=re.compile(r'^Kinofilm'))
        title_raw = "Unknown"
        film_url = None
        
        if link_tag:
            title_raw = link_tag.get_text(strip=True)
            href = link_tag.get('href')
            if href:
                # Ensure absolute URL
                if href.startswith('/'):
                    film_url = f"https://www.kinoprogramm.com{href}"
                else:
                    film_url = href

        # Find schedule container for this movie
        # It seems the schedule is in a subsequent row or inside?
        # In the HTML debug:
        # <div class="row mt-5"> ... movie info ... </div>
        # <div class="row"> ... <div class="owl-movie-times"> ... </div> </div>
        # So the schedule is in the NEXT sibling row usually.
        
        schedule_row = row.find_next_sibling('div', class_='row')
        if not schedule_row:
            continue
            
        times_container = schedule_row.find('div', class_='owl-movie-times')
        if not times_container:
            # Maybe it was inside the same row? (Unlikely based on debug)
             continue

        # Parse days
        items = times_container.find_all('div', class_='item')
        for item in items:
            # Date info: <p class="... fw-bold">19.01.</p>
            date_p = item.find_all('p', class_='fw-bold')
            if len(date_p) < 2:
                continue
            
            day_str = date_p[1].get_text(strip=True) # "19.01."
            
            # Times: <p class="mb-1">15:15</p> (not bold)
            # Filter ps that are NOT bold
            time_ps = [p for p in item.find_all('p') if 'fw-bold' not in p.get('class', [])]
            
            for tp in time_ps:
                time_str = tp.get_text(strip=True)
                if not re.match(r'\d{1,2}:\d{2}', time_str):
                    continue
                
                # Parse datetime
                try:
                    # day_str "19.01."
                    day, month = map(int, day_str.strip('.').split('.'))
                    
                    # Handle year rollover if needed (if we didn't find year in header)
                    # But we trust the header year mostly. 
                    # If parsing near December/January, be careful? 
                    # MVP: Trust header year.
                    
                    dt_naive = datetime(year, month, day, 
                                      int(time_str.split(':')[0]), 
                                      int(time_str.split(':')[1]))
                    dt_local = tz.localize(dt_naive)
                    
                    sessions.append(Session(
                        title_raw=title_raw,
                        dt_local=dt_local,
                        film_url=film_url,
                        tags_raw=title_raw # Using title as tags source for now
                    ))
                except ValueError:
                    logger.warning(f"Failed to parse date/time: {day_str} {time_str}")

    return sessions
