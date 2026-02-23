from django.core.management.base import BaseCommand

from resultsdb.models import Athlete, Event, Result

BATCH_SIZE = 500


class Command(BaseCommand):
    help = "create performance scores table"

    def handle(self, *args, **options):
        event_map = get_event_map()
        # for e in event_map:
        #     print(e)
        results = Result.objects.select_related("event")
        rows_to_update = []
        for result in results.iterator(chunk_size=BATCH_SIZE):
            if result.event:
                id, a, b, c, wa_conversion, min_units = event_map[result.event.id]
                if result.event_category in ["Jump", "Throws", "Vault"]:
                    units = result.millimeters / 1000.0
                else:
                    units = result.units / 1000.0
                units *= wa_conversion
                units = min(min_units, units)
                wa_points = a * units * units + b * units + c
                result.wa_points = wa_points
                rows_to_update.append(result)
                if len(rows_to_update) >= 500:
                    try:
                        Result.objects.bulk_update(rows_to_update, ["wa_points"])
                    except Exception as e:
                        print("ERROR when bulk updating result" + str(e))
                    rows_to_update.clear()
        if rows_to_update:
            try:
                Result.objects.bulk_update(rows_to_update, ["wa_points"])
            except Exception as e:
                print("ERROR when bulk updating result" + str(e))
            rows_to_update.clear()


def get_results():
    results = Result.objects.all()


def get_event_map():
    events = Event.objects.values_list(
        "id", "coeffA", "coeffB", "coeffC", "wa_conversion", "min"
    )
    event_map = {}
    for event in events:
        event_map[event[0]] = event
    return event_map
