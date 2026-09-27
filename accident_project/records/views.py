from .location_coords import LOCATION_COORDS
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count
from .models import AccidentRecord, Alert, Hospital, PoliceStation
from datetime import date
import nepali_datetime
import joblib
from functools import lru_cache
import requests as api_requests
import pandas as _pd
from django.contrib import messages as _msgs

CAUSE_CHOICES = [
    "Speeding", "Negligence", "Overtaking", "Drunk Driving",
    "Wrong Side", "Brake Failure", "Hit and Run", "Pedestrian Error",
    "Mutual Collision", "Other",
]
VEHICLE_CHOICES = [
    "Two-Wheeler", "Three-Wheeler", "Four-Wheeler",
    "Two-Wheeler + Four-Wheeler", "Two-Wheeler + Three-Wheeler",
    "Three-Wheeler + Four-Wheeler", "Other",
]


def calculate_severity(deaths, serious, minor):
    """Transparent rule-based severity — no AI, if-else logic."""
    if deaths > 0:
        return "Fatal"
    if serious > 0:
        return "Serious"
    if minor > 0:
        return "Slight"
    return "None"


def bs_info(ad_date):
    """AD date -> BS date string, BS month, season, festival."""
    bs = nepali_datetime.date.from_datetime_date(ad_date)
    m = bs.month
    if m in (3, 4, 5):
        season = "Monsoon"
    elif m in (6, 7):
        season = "Festival"
    elif m in (9, 10):
        season = "Foggy"
    else:
        season = "Normal"
    festival = "Dashain-Tihar" if m in (6, 7) else None
    bs_str = f"{bs.year}-{m:02d}-{bs.day:02d}"
    return bs_str, m, season, festival


@login_required
def home(request):
    context = {
        "total_accidents": AccidentRecord.objects.count(),
        "total_deaths": AccidentRecord.objects.aggregate(t=Sum("deaths"))["t"] or 0,
        "total_injuries": AccidentRecord.objects.aggregate(t=Sum("injuries"))["t"] or 0,
        "unread_alerts": Alert.objects.filter(is_read=False).count(),
    }
    return render(request, "records/home.html", context)


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
@login_required
def accident_entry(request):
    locations = (AccidentRecord.objects
                 .values_list("location_name", flat=True)
                 .distinct().order_by("location_name"))

    if request.method == "POST":
        # ---- BS date input: BS -> AD conversion ----
        bs_raw = request.POST.get("bs_date", "").strip()
        try:
            y_s, m_s, d_s = bs_raw.split("-")
            bs_y, bs_m, bs_d = int(y_s), int(m_s), int(d_s)
            if not (2075 <= bs_y <= 2090):
                raise ValueError("year")
            ad_date = nepali_datetime.date(
                bs_y, bs_m, bs_d).to_datetime_date()
        except Exception:
            messages.error(request,
                "❌ Invalid BS date! Format: 2082-06-15 (year-month-day)")
            return redirect("entry")

        try:
            hour = int(request.POST["hour"])
        except (ValueError, KeyError):
            messages.error(request, "❌ Time is missing!")
            return redirect("entry")

        location = (request.POST.get("other_location") or "").strip() \
            or request.POST.get("location")
        if not location:
            messages.error(request, "❌ Location is required!")
            return redirect("entry")

        deaths = int(request.POST.get("deaths") or 0)
        serious = int(request.POST.get("serious") or 0)
        minor = int(request.POST.get("minor") or 0)

        # ---- user gives the BS date directly — use as-is ----
        severity = calculate_severity(deaths, serious, minor)
        bs_str = f"{bs_y}-{bs_m:02d}-{bs_d:02d}"

        if bs_m in (3, 4, 5):
            season = "Monsoon"
        elif bs_m in (6, 7):
            season = "Festival"
        elif bs_m in (9, 10):
            season = "Foggy"
        else:
            season = "Normal"

        if bs_m in (6, 7):
            festival = "Dashain-Tihar"
        else:
            festival = None

        is_night = hour >= 22 or hour < 4

        weather, temperature = get_current_weather(location)

        record = AccidentRecord.objects.create(
            date=ad_date,
            hour=hour,
            is_night=is_night,
            location_name=location,
            bs_date=bs_str,
            cause=request.POST.get("cause", "Other"),
            vehicle_type=request.POST.get("vehicle", "Other"),
            deaths=deaths, serious=serious, minor=minor,
            injuries=serious + minor,
            season=season, festival=festival,
            weather=weather,
            predicted_severity=severity,
            reported_by=request.user,
        )

        # ---- AUTO ALERT (severity-based + weather) ----
        if severity == "Fatal":
            Alert.objects.create(
                level="urgent", accident=record,
                message=(f"🚨 FATAL accident at {location} ({bs_str}) — "
                         f"{deaths} death(s). Weather: {weather}. "
                         f"Immediate response needed!"))
        elif severity == "Serious":
            Alert.objects.create(
                level="high", accident=record,
                message=(f"⚠️ SERIOUS accident at {location} ({bs_str}) — "
                         f"{serious} seriously injured. "
                         f"Weather: {weather}."))
        elif severity == "Slight":
            Alert.objects.create(
                level="info", accident=record,
                message=(f"ℹ️ Accident recorded at {location} — "
                         f"{minor} minor injuries. "
                         f"Weather: {weather}."))

        messages.success(
            request,
            f"✅ Accident saved! Severity: {severity} | "
            f"Weather: {weather} ({temperature}°C)")
        return redirect("records_list")

    return render(request, "records/entry.html", {
        "locations": locations,
        "causes": CAUSE_CHOICES,
        "vehicles": VEHICLE_CHOICES,
        "hours": range(24),
    })


@login_required
def records_list(request):
    qs = AccidentRecord.objects.all().order_by("-date", "-id")
    paginator = Paginator(qs, 25)          # 25 per page
    page = request.GET.get("page", 1)
    records = paginator.get_page(page)
    return render(request, "records/records_list.html", {"records": records})


@login_required
def alerts_list(request):
    alerts = Alert.objects.all().order_by("-created_at")
    return render(request, "records/alerts.html", {"alerts": alerts})


@login_required
def alerts_read_all(request):
    Alert.objects.filter(is_read=False).update(is_read=True)
    messages.success(request, "✅ All Alerts Are Read.")
    return redirect("alerts")


@login_required
def analysis(request):
    from django.db.models import Count

    top_locations = (AccidentRecord.objects
                     .values("location_name")
                     .annotate(total=Count("id"),
                               deaths=Sum("deaths"))
                     .order_by("-total")[:10])

    top_causes = (AccidentRecord.objects
                  .values("cause")
                  .annotate(total=Count("id"))
                  .order_by("-total")[:8])

    # festival vs normal per-day rate (report statistic!)
    total = AccidentRecord.objects.count()
    festival = AccidentRecord.objects.filter(
        festival="Dashain-Tihar").count()
    # festival = 2 months/year = 61 days, normal = 304 days
    fest_rate = festival / 61
    norm_rate = (total - festival) / 304
    ratio = round(fest_rate / norm_rate, 1) if norm_rate else 0

    return render(request, "records/analysis.html", {
        "top_locations": top_locations,
        "top_causes": top_causes,
        "festival_count": festival,
        "festival_rate": round(fest_rate, 2),
        "normal_rate": round(norm_rate, 2),
        "festival_ratio": ratio,
    })


def hotspot_map(request):
    import folium

    season = request.GET.get("season", "all")

    qs = AccidentRecord.objects.all()
    if season != "all":
        qs = qs.filter(season=season.capitalize())

    stats = (qs.values("location_name")
             .annotate(total=Count("id"), deaths=Sum("deaths"),
                       serious=Sum("serious"))
             .order_by("-total"))

    # statistical hotspot threshold: mean + 1 std
    counts = [s["total"] for s in stats]
    if counts:
        mean = sum(counts) / len(counts)
        std = (sum((c - mean) ** 2 for c in counts) / len(counts)) ** 0.5
        threshold = mean + std
    else:
        threshold = 999

    m = folium.Map(location=[28.6040, 81.6280], zoom_start=13, height=550,
                   tiles="CartoDB positron")

    hotspots = 0
    unknown = []
    for s in stats:
        name = s["location_name"]
        coords = LOCATION_COORDS.get(name)
        if coords is None:
            unknown.append((name, s["total"]))
            continue

        is_hot = s["total"] > threshold
        if is_hot:
            hotspots += 1
            color, radius = "#d32f2f", 14 + s["total"] * 0.35
        else:
            color, radius = "#f57c00", 5 + s["total"] * 0.35

        popup_html = (f"<b style='font-size:14px'>{name}</b><br>"
                      f"Accidents: <b>{s['total']}</b><br>"
                      f"Deaths: <b style='color:red'>{s['deaths']}</b> | "
                      f"Serious: {s['serious']}<br>"
                      + ("🔥 <b>STATISTICAL HOTSPOT</b>" if is_hot else ""))

        folium.CircleMarker(
            location=coords, radius=radius, color=color,
            fill=True, fill_opacity=0.5, weight=2,
            popup=folium.Popup(popup_html, max_width=220),
        ).add_to(m)

    legend_html = """
    <div style="position: fixed; bottom: 20px; left: 20px; z-index: 9999;
                background: white; padding: 10px 14px; border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                font-family: Arial; font-size: 13px;">
        <b>🚦 Legend</b><br>
        <span style="color:#d32f2f;">⬤</span> Hotspot (&gt; """ + str(round(threshold, 1)) + """ accidents)<br>
        <span style="color:#f57c00;">⬤</span> Accident location<br>
        <i>Circle size = accident count</i>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    return render(request, "records/hotspot_map.html", {
        "map_html": m._repr_html_(),
        "threshold": round(threshold, 1),
        "season": season,
        "hotspot_count": hotspots,
        "total_locations": len(stats),
        "unknown": unknown,
    })


import json as _json
from django.db.models import Q

def load_risk_points():
    try:
        with open("risk_points.json") as f:
            return _json.load(f)
    except FileNotFoundError:
        return None


@login_required
def risk_calculator(request):
    points = load_risk_points()
    if points is None:
        return render(request, "records/risk.html",
                      {"error": "risk_points.json not found — please run compute_risk_points.py!"})

    context = {
        "vehicle_options": points["vehicle"]["points"].keys(),
        "season_options": points["season"]["points"].keys(),
        "location_options": points["location"]["points"].keys(),
        "total_records": AccidentRecord.objects.count(),
        "error": None,
    }

    if request.method == "POST":
        vehicle = request.POST.get("vehicle")
        time_slot = request.POST.get("time")
        season = request.POST.get("season")
        location = request.POST.get("location")

        score = (points["vehicle"]["points"].get(vehicle, 1)
                 + points["time"]["points"].get(time_slot, 1)
                 + points["season"]["points"].get(season, 1)
                 + points["location"]["points"].get(location, 1))

        if score >= 8:
            band, color, emoji = "CRITICAL", "#b71c1c", "🚨"
        elif score >= 6:
            band, color, emoji = "HIGH", "#d32f2f", "⚠️"
        elif score >= 4:
            band, color, emoji = "MEDIUM", "#f57c00", "🟠"
        else:
            band, color, emoji = "LOW", "#388e3c", "🟢"

        context.update({
            "score": score, "band": band, "color": color, "emoji": emoji,
            "vehicle": vehicle, "time_slot": time_slot,
            "season": season, "location": location,
            "vehicle_pct": points["vehicle"]["rates"].get(vehicle),
            "time_pct": points["time"]["rates"].get(time_slot),
            "season_pct": points["season"]["rates"].get(season),
            "location_pct": points["location"]["rates"].get(location),
        })

    return render(request, "records/risk.html", context)


@lru_cache(maxsize=1)
def load_models():
    """Load models only once (for speed)"""
    rf = joblib.load("models/model_rf.joblib")
    xgb_model = joblib.load("models/model_xgb.joblib")
    encoders = joblib.load("models/encoders.joblib")
    target_le = joblib.load("models/target_encoder.joblib")
    return rf, xgb_model, encoders, target_le


def predict_severity(request):
    rf, xgb_model, encoders, target_le = load_models()

    context = {
        "locations": list(encoders["location_name"].classes_),
        "vehicles": list(encoders["vehicle_type"].classes_),
        "causes": list(encoders["cause"].classes_),
        "seasons": list(encoders["season"].classes_),
        "hours": range(24),
    }

    if request.method == "POST":
        location = request.POST["location"]
        vehicle = request.POST["vehicle"]
        cause = request.POST["cause"]
        season = request.POST["season"]
        hour = int(request.POST["hour"])

        festival = 1 if season == "Festival" else 0
        is_night = 1 if (hour >= 22 or hour < 4) else 0

        def safe_encode(le, val):
            classes = list(le.classes_)
            return classes.index(val) if val in classes else 0

        features = [[hour, is_night, festival,
                     safe_encode(encoders["season"], season),
                     safe_encode(encoders["cause"], cause),
                     safe_encode(encoders["vehicle_type"], vehicle),
                     safe_encode(encoders["location_name"], location)]]

        rf_pred = target_le.inverse_transform(rf.predict(features))[0]
        xgb_pred = target_le.inverse_transform(xgb_model.predict(features))[0]

        # probabilities (confidence)
        rf_probs = rf.predict_proba(features)[0]
        xgb_probs = xgb_model.predict_proba(features)[0]

        rf_conf = round(max(rf_probs) * 100)
        xgb_conf = round(max(xgb_probs) * 100)

        agree = "✅ Both models AGREE" if rf_pred == xgb_pred \
            else "⚠️ Models DISAGREE — borderline case"

        def sev_color(s):
            return {"Fatal": "#d32f2f", "Serious": "#f57c00",
                    "Slight": "#388e3c"}.get(s, "#757575")

        context.update({
            "rf_pred": rf_pred, "xgb_pred": xgb_pred,
            "rf_conf": rf_conf, "xgb_conf": xgb_conf,
            "rf_color": sev_color(rf_pred), "xgb_color": sev_color(xgb_pred),
            "agree": agree, "show_result": True,
            "sel_location": location, "sel_vehicle": vehicle,
            "sel_cause": cause, "sel_season": season, "sel_hour": hour,
        })

    return render(request, "records/predict.html", context)

import math


def distance_km(lat1, lon1, lat2, lon2):
    """Flat-earth approximation (accurate enough at district scale)"""
    dlat = (lat1 - lat2) * 111
    dlon = (lon1 - lon2) * 111 * math.cos(math.radians(lat1))
    return round(math.sqrt(dlat ** 2 + dlon ** 2), 1)


WEATHER_CODES = {
    0: "Clear", 1: "Clear", 2: "Cloudy", 3: "Cloudy",
    45: "Fog", 48: "Fog",
    51: "Drizzle", 53: "Drizzle", 55: "Drizzle",
    61: "Rain", 63: "Rain", 65: "Rain",
    80: "Rain", 81: "Rain", 82: "Rain",
    71: "Snow", 73: "Snow", 75: "Snow",
    95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm",
}


def get_current_weather(location_name):
    """Get today's weather for a location from Open-Meteo (free, no API key)"""
    coords = LOCATION_COORDS.get(location_name)
    if coords is None:
        return "Unknown", None

    lat, lon = coords
    try:
        r = api_requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon,
                    "current": "temperature_2m,precipitation,weather_code"},
            timeout=4)
        data = r.json()["current"]
        condition = WEATHER_CODES.get(int(data["weather_code"]), "Other")
        temp = data["temperature_2m"]
        if data["precipitation"] and data["precipitation"] > 0 \
                and condition not in ("Rain", "Drizzle", "Thunderstorm"):
            condition = "Rain"
        return condition, temp
    except Exception:
        return "Unknown", None   # internet fail -> system never blocks


def get_emergency_info(location_name):
    """Find nearest hospital + police station from a location's coordinates"""
    coords = LOCATION_COORDS.get(location_name)
    if coords is None:
        return None

    lat, lon = coords
    hospitals = sorted(
        Hospital.objects.all(),
        key=lambda h: distance_km(lat, lon, h.latitude, h.longitude))
    police_stations = sorted(
        PoliceStation.objects.all(),
        key=lambda p: distance_km(lat, lon, p.latitude, p.longitude))

    result = {"ambulance_hotline": "102", "traffic_hotline": "100"}

    if hospitals:
        h = hospitals[0]
        result["hospital"] = h
        result["hospital_km"] = distance_km(
            lat, lon, h.latitude, h.longitude)
        # ROUTE link: hospital -> accident location (driving)
        result["hospital_map"] = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={h.latitude},{h.longitude}"
            f"&destination={lat},{lon}&travelmode=driving")

    if police_stations:
        p = police_stations[0]
        result["police"] = p
        result["police_km"] = distance_km(
            lat, lon, p.latitude, p.longitude)
        # ROUTE link: police -> accident location (driving)
        result["police_map"] = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={p.latitude},{p.longitude}"
            f"&destination={lat},{lon}&travelmode=driving")

    # clickable pin for the accident location
    result["accident_map"] = f"https://maps.google.com/?q={lat},{lon}"
    return result

@login_required
def emergency_lookup(request):
    result = None
    selected = None

    if request.method == "POST":
        selected = request.POST.get("location")
        result = get_emergency_info(selected)

    return render(request, "records/emergency.html", {
        "locations": sorted(LOCATION_COORDS.keys()),
        "result": result,
        "selected": selected,
    })




@login_required
def bulk_upload(request):
    upload_result = None

    if request.method == "POST" and request.FILES.get("csv_file"):
        csv_file = request.FILES["csv_file"]

        if not csv_file.name.endswith(".csv"):
            _msgs.error(request, "❌ Only CSV files allowed! (.csv extension)")
            return redirect("bulk_upload")

        if csv_file.size > 5 * 1024 * 1024:
            _msgs.error(request, "❌ File is too large! (max 5MB)")
            return redirect("bulk_upload")

        try:
            df = _pd.read_csv(csv_file)
        except Exception:
            _msgs.error(request, "❌ Could not read the CSV! Please check the file.")
            return redirect("bulk_upload")

        REQUIRED = ["date", "location", "hour", "vehicle",
                    "cause", "deaths", "serious", "minor"]
        missing = [c for c in REQUIRED if c not in df.columns]
        if missing:
            _msgs.error(request,
                        f"❌ These columns are missing: {missing}. "
                        f"Please download the template!")
            return redirect("bulk_upload")

        created, errors = 0, []
        for i, row in df.iterrows():
            row_num = i + 2
            try:
                from datetime import date as _date

                # CSV has a BS date (e.g. 2082-06-15) — convert to AD
                b_y, b_m, b_d = str(row["date"]).strip().split("-")
                b_y, b_m, b_d = int(b_y), int(b_m), int(b_d)
                if not (2075 <= b_y <= 2090):
                    raise ValueError("year range")
                d = nepali_datetime.date(
                    b_y, b_m, b_d).to_datetime_date()
                hour = int(row["hour"])
                if not (0 <= hour <= 23):
                    raise ValueError("hour")
                deaths = int(row["deaths"] or 0)
                serious = int(row["serious"] or 0)
                minor = int(row["minor"] or 0)
                if min(deaths, serious, minor) < 0:
                    raise ValueError("negative")

                location = str(row["location"]).strip()
                if not location:
                    raise ValueError("location")

                severity = calculate_severity(deaths, serious, minor)
                bs_str = f"{b_y}-{b_m:02d}-{b_d:02d}"
                if b_m in (3, 4, 5):
                    season = "Monsoon"
                elif b_m in (6, 7):
                    season = "Festival"
                elif b_m in (9, 10):
                    season = "Foggy"
                else:
                    season = "Normal"
                festival = "Dashain-Tihar" if b_m in (6, 7) else None
                record = AccidentRecord.objects.create(
                    date=d, hour=hour,
                    is_night=hour >= 22 or hour < 4,
                    location_name=location,
                    bs_date=bs_str,
                    cause=str(row["cause"]).strip(),
                    vehicle_type=str(row["vehicle"]).strip(),
                    deaths=deaths, serious=serious, minor=minor,
                    injuries=serious + minor,
                    season=season, festival=festival,
                    predicted_severity=severity,
                    reported_by=request.user,
                )

                if severity == "Fatal":
                    Alert.objects.create(
                        level="urgent", accident=record,
                        message=(f"🚨 FATAL (bulk) at {location} "
                                 f"({bs_str}) — {deaths} death(s)"))
                elif severity == "Serious":
                    Alert.objects.create(
                        level="high", accident=record,
                        message=(f"⚠️ SERIOUS (bulk) at {location} "
                                 f"({bs_str}) — {serious} injured"))
                created += 1

            except Exception:
                errors.append(f"Row {row_num}: invalid data "
                              f"({row.get('date', '?')})")

        upload_result = {
            "total": len(df), "created": created,
            "failed": len(errors), "errors": errors[:10],
        }
        _msgs.success(request,
                      f"✅ {created} records added! "
                      f"{len(errors)} rejected.")

    # ---- this part runs on GET requests (i.e. outside the if block) ----
    locs = (AccidentRecord.objects
            .values_list("location_name", flat=True)
            .distinct().order_by("location_name"))

    return render(request, "records/bulk_upload.html",
                  {"upload_result": upload_result,
                   "locations": locs,
                   "hours": range(24)})

@login_required
def download_template(request):
    """Sample CSV template download"""
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = \
        'attachment; filename="accident_template.csv"'

    writer = csv.writer(response)
    writer.writerow(["date", "location", "hour", "vehicle",
                     "cause", "deaths", "serious", "minor"])
    writer.writerow(["date", "location", "hour", "vehicle",
                     "cause", "deaths", "serious", "minor"])
    writer.writerow(["2082-06-15", "Airchowk", 20,
                     "Two-Wheeler", "Speeding", 0, 1, 2])
    writer.writerow(["2082-01-16", "Bus Park", 14,
                     "Four-Wheeler", "Negligence", 0, 0, 1])
    writer.writerow(["2025-01-16", "Bus Park", 14,
                     "Four-Wheeler", "Negligence", 0, 0, 1])
    return response


import subprocess
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def retrain_model(request):
    result = None
    if request.method == "POST":
        try:
            output = subprocess.run(
                ["python", "train_model.py"],
                capture_output=True, text=True, timeout=120,
                cwd="D:\\accident_project")
            result = output.stdout[-2500:] if output.stdout else "No output"
        except Exception as e:
            result = f"Error: {str(e)}"

    total = AccidentRecord.objects.count()
    return render(request, "records/retrain.html",
                  {"result": result, "total_records": total})