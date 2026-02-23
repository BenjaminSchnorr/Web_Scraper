import time

from django.core.management.base import BaseCommand
from requests.exceptions import ProxyError, Timeout

from resultsdb.models import Athlete
from resultsdb.scraper.ingest import create_session, ingest_athlete
from resultsdb.scraper.milesplit_client import MilesplitClient
from resultsdb.scraper.queries import get_events


def backoff_sleep(attempt: int):
    """Sleep with exponential backoff."""
    base = 0.5  # starting delay (seconds)
    factor = 2.0  # multiplier per attempt
    cap = 30.0  # max sleep seconds

    delay = base * (factor**attempt)
    if delay > cap:
        delay = cap
    time.sleep(delay)
    return delay


def query_existing_athletes():
    qs = set(Athlete.objects.all().values_list("id", flat=True))
    return qs


def create_session_list():
    proxy_info = [
        ("45.90.251.109", "12323", "14a92f3decc44", "b57725f266"),
        ("45.90.250.105", "12323", "14a92f3decc44", "b57725f266"),
        ("45.90.250.65", "12323", "14a92f3decc44", "b57725f266"),
        ("45.90.251.120", "12323", "14a92f3decc44", "b57725f266"),
        ("45.133.57.176", "12323", "14a92f3decc44", "b57725f266"),
    ]

    session_list = []
    for host, port, user, password in proxy_info:
        proxy_url = f"http://{user}:{password}@{host}:{port}"
        proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }
        session_list.append(create_session(proxies))
    return session_list


def handle_err(client, athlete_id, event_map):
    for s in client.session_list:
        s.close()
    session_list = create_session_list()
    del client
    client = MilesplitClient(session_list)
    new_born_attempts = 0
    while client.client_is_new_born:
        backoff_sleep(new_born_attempts)
        new_born_attempts += 1
        try:
            ingest_athlete(athlete_id, client, event_map)
        except Exception as e:
            print("ERROR: SOMETHING BAD!! CRASHED PROCESS!!" + str(e))
            pass
    return client


class Command(BaseCommand):
    help = "Run athlete ingest"

    # def add_arguments(self, parser):
    #     parser.add_argument("athlete_id", type=int)

    def handle(self, *args, **options):
        stragglers = query_existing_athletes()
        event_map = get_events()
        session_list = create_session_list()
        client = MilesplitClient(session_list)
        with open("ids_original.csv", "r", encoding="utf-8") as infile:
            lines = [line.strip() for line in infile if line.strip()]
            if not lines:
                print("No IDs left to process.")
                return
        # count = 0
        for l in lines:
            if int(l) not in stragglers:

                athlete_id = l
                try:
                    ingest_athlete(athlete_id, client, event_map)
                except ProxyError:
                    client = handle_err(client, athlete_id, event_map)
                    pass
                except Timeout:
                    client = handle_err(client, athlete_id, event_map)
                    pass
                except Exception as e:
                    print("ERROR: SOMETHING BAD!! CRASHED PROCESS!!" + str(e))
                    client = handle_err(client, athlete_id, event_map)
                    pass
