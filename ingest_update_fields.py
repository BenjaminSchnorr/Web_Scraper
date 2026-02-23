import logging

import requests

from resultsdb.models import Athlete, Meet, Result, Venue

from .constants import IDENTITY, JWT_TOKEN
from .mappers import map_athlete, map_meet, map_result, map_team, map_venue
from .queries import (
    create_athlete,
    create_meets,
    create_results,
    create_team,
    create_venues,
    get_existing_venues,
)

logger = logging.getLogger(__name__)


def create_session(proxies):
    session = requests.Session()
    session.cookies.set("jwt_token", JWT_TOKEN)
    session.cookies.set("identity", IDENTITY)
    session.proxies.update(proxies)
    return session


def ingest_update_fields(athlete_id, client, event_map, meet_ids_qs, results_to_create):
    try:
        athlete_json = client.fetch_athlete_stats(athlete_id)
    except Exception as e:
        raise e
    athlete_parsed = map_athlete(athlete_json)
    if not athlete_json or not athlete_parsed:
        logger.warning("Skipping athlete due to error %s", athlete_parsed)
        return None

    results_unparsed = athlete_json.get("data")
    if not results_unparsed:
        logger.warning("Athlete has no results, skipping rest of code")
        return None

    for result in results_unparsed:
        if not result:
            continue
        r, key = map_result(result, athlete_id)
        try:
            if result.get("meetId") and int(result.get("meetId")) in meet_ids_qs:
                found_event = event_map.get(key)
                r["event"] = found_event
                r = Result(**r)
                results_to_create.append(r)
            else:
                logger.warning(
                    "CHECK THIS OUT INVESTIGATE: something messed up with meetId in results for %s",
                    athlete_id,
                )
        except Exception as e:
            logger.warning("ERROR when getting meet id or creating result %s", e)

    # if len(results_to_create) > 1000 or athlete_id == "17213583":
    #     create_results(results_to_create)
    #     results_to_create.clear()
    create_results(results_to_create)
    results_to_create.clear()

    # for athlete_id in athlete_ids:
    #     qs = Result.objects.order_by("id")
    # qs = Result.objects.order_by("id")
    # id_prev = 12891086
    # results_to_update = []
    # for r in Result.objects.all().iterator(chunk_size=1000):

    # # process row without loading everything into memory
    #     if(id_prev != r.athlete_id):
    #         id_prev = r.athlete_id
    #         athlete_json = client.fetch_athlete_stats(athlete_id)
    #         athlete_parsed = map_athlete(athlete_json)
    #         if not athlete_json or not athlete_parsed:
    #             logger.warning("Skipping athlete due to error %s", athlete_parsed)
    #             continue
    #         results_unparsed = athlete_json.get("data")
    #         if not results_unparsed:
    #             logger.warning("Athlete has no results, skipping rest of code")
    #             return None
    #         #update results here as bulk update?
    #         print("test")
    #     else:
    #         #process rows here

    #         print("test")

    # athlete_json = client.fetch_athlete_stats(athlete_id)
    # athlete_parsed = map_athlete(athlete_json)
    # if not athlete_json or not athlete_parsed:
    #     logger.warning("Skipping athlete due to error %s", athlete_parsed)
    #     return None
    # if not athlete_parsed.get("team"):
    #     logger.warning("Athlete has no team, set team as null skip getting team")
    # else:
    #     team_json = client.fetch_team(athlete_parsed.get("team"))
    #     team_parsed = map_team(team_json)
    #     team = create_team(team_parsed)
    #     athlete_parsed["team"] = team
    # create_athlete(athlete_parsed)

    # results_unparsed = athlete_json.get("data")
    # if not results_unparsed:
    #     logger.warning("Athlete has no results, skipping rest of code")
    #     return None

    # results_parsed = []
    # meets_parsed = {}
    # venue_ids = set()
    # meet_map = {}
    # venue_map = {}
    # for result in results_unparsed:
    #     if not result:
    #         continue
    #     result_parsed, key = map_result(result, athlete_id)
    #     found_event = event_map.get(key)
    #     try:
    #         result_parsed["wa_points"] = found_event.get("wa_points")
    #     except Exception as e:
    #         pass
    #     result_parsed["event"] = found_event
    #     results_parsed.append(result_parsed)
    #     meet_parsed = map_meet(result)
    #     meet_id = meet_parsed.get("id")
    #     if meet_id and meet_id not in meets_parsed.keys():
    #         meets_parsed[meet_id] = meet_parsed
    # venue_ids.add(meet_parsed.get("venue"))

    # venues_existing = get_existing_venues(venue_ids)
    # venue_ids_existing = set()
    # for venue in venues_existing:
    #     venue_ids_existing.add(venue.id)
    #     venue_map[venue.id] = venue

    # venues_to_create = [id for id in venue_ids if id not in str(venue_ids_existing)]
    # venue_objects_to_create = []
    # for venue_id in venues_to_create:
    #     try:
    #         parsed_venue = client.fetch_venue(venue_id)
    #         parsed_venue = map_venue(parsed_venue)
    #         venue = Venue(**parsed_venue)
    #         venue_map[venue.id] = venue
    #         venue_objects_to_create.append(venue)
    #     except Exception as e:
    #         logger.warning(
    #             "ERROR: Skipping adding venue. It probably does not exist. %s", e
    #         )

    # for meet_parsed in meets_parsed.values():
    #     # meet_parsed["venue"] = venue_map.get(meet_parsed["venue"])
    #     try:
    #         meet = Meet(**meet_parsed)
    #         meet_map[meet.id] = meet
    #     except Exception as e:
    #         logger.warning("ERROR: Unable to create Meet Object %s", e)
    #         continue

    # results_to_create = []
    # for result_parsed in results_parsed:
    #     result_parsed["meet"] = meet_map.get(result_parsed["meet"])
    #     if not result_parsed["meet"]:
    #         logger.warning(
    #             "ERROR: no valid meet for. Skipping result for athlete %s", athlete_id
    #         )
    #         continue
    #     result_parsed["id"] = None
    #     try:
    #         result = Result(**result_parsed)
    #         results_to_create.append(result)
    #     except Exception as e:
    #         logger.warning("ERROR: failed to create Result object %s", e)

    # create_venues(venue_objects_to_create)
    # create_meets(meet_map)
    # create_results(results_to_create)
