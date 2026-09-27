# generate_charts.py - real data bata charts banaune (matplotlib)
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

import matplotlib
matplotlib.use("Agg")               # server ma pani chalos (GUI chhaina)
import matplotlib.pyplot as plt
from collections import Counter
from records.models import AccidentRecord

CHARTS = "static/charts"
os.makedirs(CHARTS, exist_ok=True)

qs = AccidentRecord.objects.all().values(
    "location_name", "cause", "season", "hour",
    "deaths", "serious", "minor", "predicted_severity",
    "vehicle_type",
)
print(f"Total records: {len(qs)}")

# -------- Chart 1: Top 10 Locations (hotspots!) --------
locs = Counter(r["location_name"] for r in qs).most_common(10)
plt.figure(figsize=(10, 5))
plt.barh([l for l, _ in locs][::-1], [c for _, c in locs][::-1], color="#d32f2f")
plt.title("Top 10 Accident Hotspots - Birendranagar (2078-2083 BS)", fontweight="bold")
plt.xlabel("Number of Accidents")
plt.tight_layout()
plt.savefig(f"{CHARTS}/top_locations.png", dpi=120)
plt.close()
print("✅ top_locations.png")

# -------- Chart 2: Causes (legend style — overlap fix) --------
causes = Counter(r["cause"] for r in qs).most_common(8)
plt.figure(figsize=(9, 6))
bars = plt.bar([c for c, _ in causes], [c for _, c in causes],
               color=["#d32f2f", "#f57c00", "#fbc02d", "#388e3c",
                      "#1a3d6d", "#7b1fa2", "#00838f", "#757575"])
plt.title("Accident Causes", fontweight="bold", fontsize=14)
plt.ylabel("Number of Accidents")
plt.xticks(rotation=30, ha="right")           # names tirkha — overlap hune chhaina
# bar ko mathi count label
for bar in bars:
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
             int(bar.get_height()), ha="center", fontweight="bold")
plt.tight_layout()
plt.savefig(f"{CHARTS}/causes.png", dpi=120)
plt.close()
print("✅ causes.png")

# -------- Chart 3: Season --------
seasons = Counter(r["season"] for r in qs)
order = ["Normal", "Monsoon", "Festival", "Foggy"]
plt.figure(figsize=(7, 5))
plt.bar(order, [seasons.get(s, 0) for s in order],
        color=["#9e9e9e", "#1e88e5", "#f57c00", "#90a4ae"])
plt.title("Accidents by Season", fontweight="bold")
plt.ylabel("Number of Accidents")
plt.tight_layout()
plt.savefig(f"{CHARTS}/season.png", dpi=120)
plt.close()
print("✅ season.png")

# -------- Chart 4: Hour of day --------
hours = Counter(r["hour"] for r in qs if r["hour"] is not None)
all_hours = [hours.get(h, 0) for h in range(24)]
plt.figure(figsize=(10, 4))
plt.plot(range(24), all_hours, marker="o", color="#1a3d6d", linewidth=2)
plt.fill_between(range(24), all_hours, alpha=0.15, color="#1a3d6d")
plt.title("Accidents by Hour of Day", fontweight="bold")
plt.xlabel("Hour (AM/PM)")
plt.ylabel("Accidents")
hour_labels = ["12AM", "2AM", "4AM", "6AM", "8AM", "10AM",
               "12PM", "2PM", "4PM", "6PM", "8PM", "10PM"]
plt.xticks(range(0, 24, 2), hour_labels, rotation=45)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f"{CHARTS}/hours.png", dpi=120)
plt.close()
print("✅ hours.png")

# -------- Chart 5: Severity --------
sev = Counter(r["predicted_severity"] for r in qs)
labels = ["Slight", "Serious", "Fatal", "None"]
colors = ["#fbc02d", "#f57c00", "#d32f2f", "#9e9e9e"]
plt.figure(figsize=(7, 5))
plt.bar(labels, [sev.get(l, 0) for l in labels], color=colors)
plt.title("Accident Severity Distribution", fontweight="bold")
plt.ylabel("Accidents")
plt.tight_layout()
plt.savefig(f"{CHARTS}/severity.png", dpi=120)
plt.close()
print("✅ severity.png")

# -------- Chart 6: Yearly trend (AD and BS Both)----
from django.db.models.functions import ExtractYear
from django.db.models import Count

yearly = (AccidentRecord.objects
          .annotate(y=ExtractYear("date"))
          .values("y").annotate(c=Count("id"))
          .order_by("y"))

# BS year calculate: AD year + 56/57 (mid-April pachhi 57)
def ad_to_bs_year_label(ad_year):
    # fiscal year ma base garera BS range dekhaunay
    return f"{ad_year+57}/{ad_year+58}"   # e.g. 2021 -> 2078/79

labels = [ad_to_bs_year_label(r["y"]) for r in yearly]
counts = [r["c"] for r in yearly]

plt.figure(figsize=(9, 5))
bars = plt.bar(labels, counts, color="#1a3d6d")
plt.title("Accidents per Year (AD & BS)", fontweight="bold", fontsize=14)
plt.ylabel("Accidents")

# dual labels: BS upar, AD tala (brackets ma)
ax = plt.gca()
ax.set_xticks(range(len(labels)))
ax.set_xticklabels([f"BS {l}\n(AD {r['y']})" for l, r in zip(labels, yearly)],
                   fontsize=10)
# bar mathi counts
for bar in bars:
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
             int(bar.get_height()), ha="center", fontweight="bold")

plt.tight_layout()
plt.savefig(f"{CHARTS}/yearly.png", dpi=120)
plt.close()
print("✅ yearly.png")

# -------- चार्ट ८: प्रति दिनको मौसमी दर (कुल संख्या भ्रम हटाउँछ!) --------
season_days = {"Normal": 304, "Monsoon": 92, "Festival": 61, "Foggy": 61}
season_counts = Counter(r["season"] for r in qs)

labels = ["Normal", "Monsoon", "Festival", "Foggy"]
rates = [season_counts.get(s, 0) / season_days[s] for s in labels]

plt.figure(figsize=(8, 5))
bars = plt.bar(labels, rates,
               color=["#9e9e9e", "#1e88e5", "#d32f2f", "#90a4ae"])
plt.title("Accident Rate per Day by Season — The Real Risk", 
          fontweight="bold")
plt.ylabel("Accidents per Day")
for bar, r in zip(bars, rates):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
             f"{r:.2f}", ha="center", fontweight="bold")
plt.tight_layout()
plt.savefig(f"{CHARTS}/season_rate.png", dpi=120)
plt.close()
print("✅ season_rate.png")