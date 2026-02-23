import logging
import random
import time

import requests
from requests.exceptions import ProxyError, Timeout

from .constants import FIELDS

logger = logging.getLogger(__name__)


class MilesplitClient:
    def __init__(self, session_list):
        self.session_list = session_list
        self.base_url = "https://ny.milesplit.com/api/v1"
        self.fields = FIELDS
        self.session = None
        self.client_is_new_born = True

    def _get(self, path):
        self.session = random.choice(self.session_list)
        url = self.base_url + path
        try:
            response = self.session.get(url, timeout=(60, 60))
            response.raise_for_status()
            response_json = response.json()
            self.client_is_new_born = False
            return response_json
        except Timeout:
            logger.warning(f"Request timed out after 60s for {url}")
            raise Timeout

        # optional: retry, switch proxy, or skip this URL

        except ProxyError as e:
            logger.warning(f"Proxy failed for {url}: {e}")
            raise ProxyError
        # optional: rebuild the session or rotate proxy
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else None

            if status == 403:
                logger.warning("403 Forbidden")
                raise e
            elif status in (500, 502, 503, 504):
                logger.warning(f"Server error ({status}). Will retry.")
                raise e
            else:
                # logger.warning("Unhandled HTTP error: %s", e)
                return None

    def fetch_athlete_stats(self, athlete_id):
        path = f"/athletes/{athlete_id}/stats{self.fields}"
        return self._get(path)

    def fetch_team(self, team_id):
        path = f"/teams/{team_id}"
        return self._get(path)

    def fetch_venue(self, venue_id):
        path = f"/venues/{venue_id}"

        return self._get(path)
        return self._get(path)
