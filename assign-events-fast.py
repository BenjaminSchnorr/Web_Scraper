from django.core.management.base import BaseCommand
from django.db import transaction

from resultsdb.models import Event, Result


class Command(BaseCommand):
    help = "Add event to column on results"

    def handle(self, *args, **options):
        event_lookup = get_event_map()
        qs = (
            Result.objects.select_related("athlete", "meet")
            .filter(event__isnull=True)
            .order_by("id")
        )
        BATCH_SIZE = 500
        rows_to_update = []
        for res in qs.iterator(chunk_size=BATCH_SIZE):
            if res.meet.season == "CC":
                event_code = res.event_code + "_cc"
            else:
                event_code = res.event_code
            key = (event_code, res.athlete.gender, res.meet.season_year)
            if key in event_lookup:
                res.event = event_lookup[key]
                rows_to_update.append(res)
            if len(rows_to_update) >= 500:
                try:
                    Result.objects.bulk_update(rows_to_update, ["event"])
                    rows_to_update.clear()

                except Exception as e:
                    print("ERROR in bulk update for results ", str(e))
                    rows_to_update.clear()

        if rows_to_update:
            try:
                Result.objects.bulk_update(rows_to_update, ["event"])
                rows_to_update.clear()
            except Exception as e:
                print("ERROR in bulk update for results ", str(e))
                rows_to_update.clear()


def get_event_map():
    events = list(Event.objects.all())
    event_lookup = {}

    for e in events:
        key = (e.event_code, e.gender, e.year)
        event_lookup[key] = e
    return event_lookup


# def normalize_events(com):

#     qs = (
#         Result.objects.select_related("athlete", "meet")
#         .filter(event__isnull=True)
#         .order_by("id")
#     )
#     BATCH_SIZE = 500
#     total = qs.count()  # uses SQL COUNT(*), not full load
#     print(f"STARTING! ({total} results to process)")
#     found = 0
#     for i, res in enumerate(qs.iterator(chunk_size=BATCH_SIZE), start=1):
#         # Athlete gender
#         gender = (
#             res.athlete.gender.lower()[0] if res.athlete and res.athlete.gender else "m"
#         )
#         gender_key = "women" if gender == "f" else "men"

#         # Base event code and name
#         event_code = (res.event_code or "").lower().strip()
#         event_name = res.event_name or event_code.upper()
#         if not event_code:
#             continue

#         # Handle cross-country events before key creation
#         old_event_code = event_code
#         if hasattr(res.meet, "season") and res.meet.season == "CC":
#             event_code += "_cc"
#             event_name += " Cross Country"

#         # Determine year for uniqueness
#         if res.meet.season_year:
#             year = int(res.meet.season_year)
#         elif res.meet.end_date:
#             year = res.meet.end_date.year
#         else:
#             year = 2001

#         # Unique key: code + gender + year
#         # key = (event_code, gender, year)
#         found_event = Event.objects.filter(
#             year=year, event_code=event_code, gender=gender
#         ).first()
#         if not found_event:
#             found_old_event = Event.objects.filter(
#                 event_code=event_code, gender=gender
#             ).first()
#             found_event = found_old_event
#             found_event.pk = None
#             found_event.year = year
#             found_event.save()
#         if found_event:
#             res.event = found_event
#             res.save(update_fields=["event"])
#             found += 1
#             if found % 100 == 0:
#                 print(f"{100 * found / total}%")
#         if i % BATCH_SIZE == 0:
#             transaction.commit()
#     return found
#     return found
