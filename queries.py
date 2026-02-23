import logging

from resultsdb.models import Athlete, Event, Meet, Result, Team, Venue

logger = logging.getLogger(__name__)


def get_events():
    event_qs = Event.objects.all()
    event_map = {}
    for event in event_qs:
        try:
            key = (event.event_code, event.gender, event.year)
            event_map[key] = event
        except Exception as e:
            logger.warning("ERROR: Event mapping error %e", e)
            continue
    return event_map


def get_existing_venues(venue_ids):
    venues_existing = list(Venue.objects.filter(id__in=venue_ids))
    return venues_existing


def create_team(team_parsed):
    if not team_parsed or not team_parsed.get("id"):
        logger.warning(
            "ERROR: Failed to create team. Either team_parsed is None or id is None"
        )
        return None

    team, created = Team.objects.get_or_create(
        id=team_parsed.get("id"), defaults=team_parsed
    )
    if not created:
        logger.warning("Duplicate row detected for Team %s", team_parsed.get("id"))

    return team


def create_athlete(athlete_parsed):
    if not athlete_parsed or not athlete_parsed.get("id"):
        logger.warning(
            "Dit not create athlete. Either athlete_parsed is None or id is None"
        )
        return None

    athlete, created = Athlete.objects.get_or_create(
        id=athlete_parsed.get("id"), defaults=athlete_parsed
    )
    if not created:
        logger.warning(
            "Duplicate row detected for Athlete %s, Row not created",
            athlete_parsed.get("id"),
        )

    return athlete


def create_meets(meet_map):
    if not meet_map:
        logger.warning("Did not create meets. meet_map is None")
        return None

    existing_meets = set(
        Meet.objects.filter(id__in=[int(id) for id in meet_map.keys()]).values_list(
            "id", flat=True
        )
    )

    meets_to_create = [e for e in meet_map.values() if int(e.id) not in existing_meets]

    if not meets_to_create:
        logger.warning("Did not create meets, meets_to_create is none")
    Meet.objects.bulk_create(meets_to_create)

    return None


def create_results(results_to_create):
    if not results_to_create:
        logger.warning("Did not create results, results_to_create is None")
        return None
    try:
        Result.objects.bulk_create(results_to_create)
    except Exception as e:
        logger.warning("ERROR occurred when trying to create results: %s", e)


def create_venues(venue_objects_to_create):
    if not venue_objects_to_create:
        logger.warning("Did not create venues. venue_objects_to_create is none")
        return None
    Venue.objects.bulk_create(venue_objects_to_create)
