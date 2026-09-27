# compute_risk_points.py - 489 records bata risk points compute
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

import json
from django.db.models import Q
from records.models import AccidentRecord

total = AccidentRecord.objects.count()
print(f"Total records: {total}\n")

def rate(qs):
    n = qs.count()
    if n == 0:
        return 0.0
    fatal = qs.filter(deaths__gt=0).count()
    return round(fatal / n * 100, 1)

def or_all(conditions):
    result = conditions[0]
    for c in conditions[1:]:
        result = result | c
    return result

# ---- VEHICLE (max 3) ----
vehicle_rates = {
    "Two-Wheeler": rate(AccidentRecord.objects.filter(
        vehicle_type__icontains="Two-Wheeler")),
    "Three-Wheeler": rate(AccidentRecord.objects.filter(
        vehicle_type__icontains="Three-Wheeler")),
    "Four-Wheeler": rate(AccidentRecord.objects.filter(
        vehicle_type__icontains="Four-Wheeler")),
}
print("VEHICLE fatality rates (%):", vehicle_rates)

# ---- TIME (max 2) ----
time_rates = {
    "Night": rate(AccidentRecord.objects.filter(is_night=True)),
    "Day": rate(AccidentRecord.objects.filter(is_night=False)),
}
print("TIME fatality rates (%):", time_rates)

# ---- SEASON (max 2) ----
season_rates = {}
for s in ["Monsoon", "Festival", "Foggy", "Normal"]:
    season_rates[s] = rate(AccidentRecord.objects.filter(season=s))
print("SEASON fatality rates (%):", season_rates)

# ---- LOCATION (max 3) — real Surkhet places! ----
from django.db.models import Count, Sum as DSum

loc_stats = (AccidentRecord.objects
             .values("location_name")
             .annotate(total=Count("id"), deaths=DSum("deaths"))
             .order_by("-total")[:15])       # top 15 accident locations

loc_rates = {}
for s in loc_stats:
    fatal_pct = round((s["deaths"] or 0) / s["total"] * 100, 1)
    loc_rates[s["location_name"]] = fatal_pct

print("LOCATION fatality rates (%):")
for name, r in sorted(loc_rates.items(), key=lambda x: -x[1]):
    print(f"   {name}: {r}%")

# ---- points: highest rate = max points ----
def rate_to_points(rate_map, max_points):
    r_max = max(rate_map.values()) or 1
    return {k: round(v / r_max * max_points) for k, v in rate_map.items()}

result = {
    "vehicle": {"rates": vehicle_rates,
                "points": rate_to_points(vehicle_rates, 3)},
    "time": {"rates": time_rates,
             "points": rate_to_points(time_rates, 2)},
    "season": {"rates": season_rates,
               "points": rate_to_points(season_rates, 2)},
    "location": {"rates": loc_rates,
                 "points": rate_to_points(loc_rates, 3)},
}

with open("risk_points.json", "w") as f:
    json.dump(result, f, indent=2)

print("\n" + "=" * 45)
print("RISK POINTS TABLE (saved: risk_points.json)")
print(f"  Vehicle:   {result['vehicle']['points']}")
print(f"  Time:      {result['time']['points']}")
print(f"  Season:    {result['season']['points']}")
print(f"  Location:  {result['location']['points']}")
print("Max possible score: 10")