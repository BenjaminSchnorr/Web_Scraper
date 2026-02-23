import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def check_date_time_field(date_time_string):
    try:
        parsed = datetime.strptime(date_time_string, "%Y-%m-%d %H:%M:%S")
        return date_time_string
    except Exception as e:
        print(e)
        return None


def check_date_field(date_string):
    try:
        parsed = datetime.strptime(date_string, "%Y-%m-%d").date()

        return date_string
    except Exception as e:
        print(e)
        return None


def check_bool(bool):
    if bool != "1" and bool != "0":
        return None
    else:
        return bool


def check_float(f):
    try:
        float(f)
        return f
    except Exception as e:
        return None


def check_int(value):
    try:
        int(value)
        return value
    except Exception as e:
        # print("error for check int " + str(e))
        return None


def map_athlete(data):
    if not data:
        return None
    athlete = data.get("_embedded").get("athlete")
    id = athlete.get("id")
    if not id:
        logger.warning("Skipping athlete: no id")
        return None

    return {
        "id": check_int(athlete.get("id")),
        "first_name": athlete.get("firstName"),
        "last_name": athlete.get("lastName"),
        "gender": athlete.get("gender"),
        "grad_year": check_int(athlete.get("gradYear")),
        "birth_year": check_int(athlete.get("birthYear")),
        "hs_class": athlete.get("gradYear"),
        "city": athlete.get("city"),
        "state": athlete.get("state"),
        "country": athlete.get("country"),
        "native_country": None,  # trash?
        "has_committed": athlete.get("tfrrsId")
        != "",  # just check if athlete has tfrrs id? not sure if this makes sense, not sure if milesplit has a field for this
        "tffrs_id": athlete.get("tfrrsId"),
        "team": check_int(athlete.get("teamId")),
    }


def map_team(data):
    if not data:
        return None
    team = data.get("data")
    id = team.get("id")
    if not id:
        logger.warning("Skipping team: no id")
        return None
    name = team.get("name")
    if not name:
        logger.warning("NO TEAM NAME FOR %s", id)
        return None
    return {
        "id": check_int(team.get("id")),
        "name": team.get("name"),
        "abbreviation": team.get("abbreviation"),
        "site_subdomain": team.get("siteSubdomain"),
        "state": team.get("state"),
        "city": team.get("city"),
        "country": team.get("country"),
        "team_type": team.get("type"),
        "is_logo": check_bool(team.get("isLogo")),
    }


def map_meet(data):
    if not data:
        return None
    if not data.get("meetId"):
        logger.warning("Skipping meet: no id")
        return None
    return {
        "id": check_int(data.get("meetId")),
        "name": data.get("meetName"),
        "start_date": check_date_field(data.get("meetStartDate")),
        "end_date": check_date_field(data.get("meetEndDate")),
        "meet_type": data.get("meetType"),
        "season": data.get("season"),
        "season_year": data.get("seasonYear"),
        "level": data.get("level"),
        "general_meet_id": check_int(data.get("generalMeetId")),
        "is_logo": False,
        "venue_id_unique": check_int(data.get("venueId")),
        "venue": None,
        "ranking": 0,
    }


def map_venue(data):
    if not data:
        return None
    venue = data.get("data")
    if not venue or type(venue) != dict:
        logger.warning("skipping venue %s", data)
        return None
    if not venue.get("id"):
        logger.warning("Skipping venue: no id")
        return None
    return {
        "id": check_int(venue.get("id")),
        "name": venue.get("name"),
        "state": venue.get("state"),
        "city": venue.get("city"),
        "country": venue.get("country"),
    }


def map_result(data, athlete_id):
    result = data
    if not result:
        logger.warning("Skipping result: returning None")
        return None

    year = result.get("seasonYear")
    year = int(year)
    gender = result.get("gender")
    event_code_key = result.get("eventCode")
    if not year or not gender or not event_code_key:
        key = None
    else:
        season = result.get("season")
        if season == "CC":
            event_code_key += "_cc"
        gender = gender.lower()
        key = (event_code_key, gender, year)

    # maybe at some point decide to error check for season=None and decide what to do for this case
    return (
        {
            "id": None,
            "event_name": result.get("eventName"),
            "event_short_name": result.get("eventCode"),
            "event_code": result.get("eventCode"),
            "event_type": result.get("eventType"),
            "event_category": result.get("eventGenre"),  # calculate ourselves
            "event_distance": result.get("eventDistance"),
            "mark": result.get("mark"),
            "place": check_int(result.get("place")),
            "round": result.get("round"),
            "heat": result.get("heat"),
            "is_hand_timed": result.get("isHandTimed"),
            "is_converted": result.get("isConverted"),
            "is_wind_aided": result.get("isWindAided"),
            "is_season_best": check_bool(result.get("isSeasonBest")),
            "is_verified": check_bool(result.get("isVerified")),
            "wind_reading": check_float(result.get("windReading")),
            "age_group_name": result.get("level"),
            "age_group_low_age": None,  # trash
            "age_group_high_age": None,  # trash
            "note": result.get("note"),
            "units": check_int(result.get("units")),
            "millimeters": check_float(result.get("millimeters")),
            "added": None,  # can not get this to work with timezone do we even need this
            "results_division_id": check_int(result.get("resultsDivisionId")),
            "athlete_id": check_int(athlete_id),
            "meet_id": check_int(result.get("meetId")),
            "ref_id": check_int(result.get("id")),
            "wa_points": None,  # calc ourselves
            "event": None,  # calc ourselves
        },
        key,
    )
