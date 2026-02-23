from django.core.management.base import BaseCommand

from resultsdb.models import Athlete, Event, PerformanceScore, Result

BATCH_SIZE = 1000


class Command(BaseCommand):
    help = "create performance scores table"

    def handle(self, *args, **options):
        athletes = get_athletes_and_results()
        rows_to_create = []
        for athlete in athletes.iterator(chunk_size=BATCH_SIZE):
            hs_results = (
                athlete.results.filter(
                    meet__season_year__gte=athlete.grad_year - 4,
                    meet__season_year__lte=athlete.grad_year,
                )
                .exclude(is_wind_aided="w")
                .exclude(is_verified=False)
                .exclude(wa_points__isnull=True)
                .order_by("-wa_points")
            )

            best_hs_result = hs_results.first()
            peaks_by_event_type = {}
            for result in hs_results:
                if result.event.category not in peaks_by_event_type:
                    peaks_by_event_type[result.event.category] = result.wa_points

            percent_to_qual = 0.90
            qualifying_events = 0
            percent_increase = 1
            for key, value in peaks_by_event_type.items():
                if value == best_hs_result.wa_points:
                    continue
                percent_difference = value / best_hs_result.wa_points
                if percent_difference >= percent_to_qual:
                    qualifying_events += 1

                    percent_increase += percent_difference * 0.0125

            if qualifying_events >= 3:
                is_range_machine = True
            else:
                is_range_machine = False

            num_groups = qualifying_events

            range_bonus = percent_increase
            if best_hs_result:
                final_score = round(best_hs_result.wa_points * percent_increase)
                if final_score >= 1250:
                    stars = 5
                elif final_score >= 1050:
                    stars = 4
                elif final_score >= 850:
                    stars = 3
                elif final_score >= 650:
                    stars = 2
                else:
                    stars = 1

                performance_score_template = {
                    "athlete": athlete,
                    "final_score": final_score,
                    "base_score": round(best_hs_result.wa_points),
                    "range_bonus": range_bonus,
                    "num_groups": num_groups,
                    "stars": stars,
                    "is_blue_chip": False,
                    "is_range_machine": is_range_machine,
                }
                try:
                    row = PerformanceScore(**performance_score_template)
                    rows_to_create.append(row)
                except Exception as e:
                    print("ERROR creating performancescore object" + str(e))

            else:
                performance_score_template = {
                    "athlete": athlete,  # will be set dynamically
                    "final_score": 0,
                    "base_score": 0,
                    "range_bonus": 0,
                    "num_groups": 0,
                    "stars": 1,
                    "is_blue_chip": False,
                    "is_range_machine": False,
                }
                try:
                    row = PerformanceScore(**performance_score_template)
                    rows_to_create.append(row)
                except Exception as e:
                    print("ERROR creating performancescore object" + str(e))
            if len(rows_to_create) >= BATCH_SIZE:
                try:
                    PerformanceScore.objects.bulk_create(rows_to_create)
                    rows_to_create.clear()
                except Exception as e:
                    print("ERROR bulk_creating " + str(e))
                    rows_to_create.clear()
        if rows_to_create:
            try:
                PerformanceScore.objects.bulk_create(rows_to_create)
                rows_to_create.clear()
            except Exception as e:
                print("ERROR bulk_creating " + str(e))
                rows_to_create.clear()


def get_athletes_and_results():
    athletes = Athlete.objects.prefetch_related(
        "results", "results__meet", "results__event"
    )
    return athletes


def set_performance_score(self):
    """Compute and save the athlete's score using their hs results"""

    def range_bonus(evbt, max_score):
        percent_to_qual = 0.90
        qualifying_events = 0
        percent_increase = 1
        for typ in evbt.keys():
            group_max = max(evbt[typ], key=lambda r: r.wa_points).wa_points
            print(typ)
            if group_max == max_score:
                continue
            percent_difference = group_max / max_score
            if percent_difference >= percent_to_qual:
                qualifying_events += 1
                print(percent_difference * 0.0125)
                percent_increase += percent_difference * 0.0125
        return qualifying_events, percent_increase

    results = self.get_results("HS")
    events, events_by_type = self.get_events("HS")
    peak_points = max([r.wa_points for r in results])
    num_groups, range_pct = range_bonus(events_by_type, peak_points)
    score, _ = PerformanceScore.objects.get_or_create(athlete=self)
    score.base_score = peak_points
    score.num_groups = num_groups
    score.range_bonus = range_pct
    score.compute_fields()
    score.save()


def get_results_by_event_category(athlete):
    results = (
        athlete.results.filter(
            meet__season_year__gte=athlete.grad_year - 4,
            meet__season_year__lte=athlete.grad_year,
        )
        .exclude(is_wind_aided="w")
        .exclude(is_verified=False)
        .exclude(wa_points__isnull=True)
        .order_by("-wa_points")
    )
