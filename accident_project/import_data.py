# import_data.py - cleaned CSV -> Django database
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

import pandas as pd
from datetime import date, time
from django.db.models import Sum
from records.models import AccidentRecord

df = pd.read_csv("data/cleaned_accidents.csv")
print(f"CSV loaded: {len(df)} records")

if AccidentRecord.objects.count() > 0:
    ans = input("DB ma records chhan — duplicate hunchha! Garnai? (y/n): ")
    if ans.lower() != "y":
        print("Cancelled.")
        exit()

created, skipped = 0, 0
for _, row in df.iterrows():
    if pd.isna(row["date_ad"]):
        skipped += 1
        continue
    try:
        d = date.fromisoformat(str(row["date_ad"])[:10])
    except ValueError:
        skipped += 1
        continue

    hour = int(row["hour"]) if not pd.isna(row["hour"]) else None

    AccidentRecord.objects.create(
        date=d,
        time=time(hour, 0) if hour is not None else None,
        location_name=row["location_en"],
        bs_date=row["bs_date"],
        hour=hour,
        is_night=bool(int(row["is_night"])),
        cause=row["cause_en"],
        vehicle_type=row["vehicle_type"],
        deaths=int(row["deaths"]),
        serious=int(row["serious"]),
        minor=int(row["minor"]),
        injuries=int(row["serious"] + row["minor"]),
        season=row["season"],
        festival="Dashain-Tihar" if int(row["is_festive_season"]) == 1 else None,
        predicted_severity=row["severity"],
    )
    created += 1

print(f"\n✅ Imported: {created} | Skipped: {skipped}")
print(f"Total accidents: {AccidentRecord.objects.count()}")
print(f"Deaths: {AccidentRecord.objects.aggregate(t=Sum('deaths'))['t']}")
print(f"Serious: {AccidentRecord.objects.aggregate(t=Sum('serious'))['t']}")