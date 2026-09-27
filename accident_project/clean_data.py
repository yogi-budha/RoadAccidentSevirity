# clean_data.py (v4) - silent skips HATAUNE + naya date formats
import pandas as pd
import re
import nepali_datetime

FILE = "data/surkhet_accidents.xlsx"
OUTPUT = "data/cleaned_accidents.csv"

NEPALI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

LOCATION_FIX = {
    "रेडियो नापाल": "रेडियो नेपाल", "रेढियो नापाल": "रेडियो नेपाल",
    "एरपोष चोक": "एरपोट चोक", "एरीचोक": "एरिचोक",
    "रेडियो नेरपाल": "रेडियो नेपाल", "चाईना पुल": "चाईनापुल",
    "पिपिराचोक": "पिपिरा चोक", "पिपिरट चोक": "पिपिरा चोक",
    "वजाज स्वरुम": "बजाज शोरुम", "बाङ्गेसिमल": "बाङगेसिमल",
    "धुलयाविट पुल": "धुलियाबिट पुल", "धुलयाविट": "धुलियाबिट",
    "मुलापानि चोक": "मुलपानि चोक", "मोडेल कलेज": "मोडल कलेज",
    "बुलबुले पेट्राल पम्प": "बुलबुले पेट्रोल पम्प",
    "बुलबुले पेट्रोल पम्म": "बुलबुले पेट्रोल पम्प",
    "नारायण पेट्रोल मप्प": "नारायण पेट्रोल पम्प",
    "सुर्खेत पेट्रोल पम्म": "सुर्खेत पेट्रोल पम्प",
    "सुर्खेत हस्पिटल": "सुर्खेत अस्पताल",
    "ढोलेखाली":"ढोडेखाली",
}
CAUSE_FIX = {
    "लापबाहि": "लापरबाहि", "लापरबाही": "लापरबाहि",
    "लापरवाहि": "लापरबाहि", "लापरवाही": "लापरबाहि",
    "लापवाहि": "लापरबाहि", "लापवाही": "लापरबाहि",
    "चालकको लापबाहि": "चालकको लापरबाहि",
    "ओभरट्याक": "ओभरट्याग", "ओभड्याक": "ओभरट्याग",
    "गलत साईट": "गलत साईड",
    "HIT&run": "Hit and Run", "hit run": "Hit and Run",
    "मा प से": "मा.प.से", "मापसे": "मा.प.से",
    "तिव्रगति": "तिब्र गति", "तिब्रगति": "तिब्र गति",
    "तिव्र गति": "तिब्र गति",
}
CAUSE_EN = {
    "तिब्र गति": "Speeding", "लापरबाहि": "Negligence",
    "चालकको लापरबाहि": "Driver Negligence", "ओभरट्याग": "Overtaking",
    "ब्रेक फेल": "Brake Failure", "Hit and Run": "Hit and Run",
    "गलत साईड": "Wrong Side", "मा.प.से": "Drunk Driving",
    "तिव्रगति मा.प.से": "Speeding + Drunk Driving",
    "एकआपसमा": "Mutual Collision",
    "पैदल यात्रिले झुक्याउदा": "Pedestrian Error",
}
LOCATION_EN = {
    "बसपार्क": "Bus Park", "मंगलगढी चोक": "Mangalgadhi Chowk",
    "एरिचोक": "Yeri chowk", "दैलेखि चोक": "Dailekh Chowk",
    "एरपोट चोक": "Airport Chowk","एरिचोक": "Yeri Chowk",
    "पिपिरा चोक": "Pipira Chowk", "मुलपानि चोक": "Mulpani Chowk",
    "मुलपानि": "Mulpani", "बुलबुले चोक": "Bulbule Chowk",
    "बुलबुले गेट": "Bulbule Gate", "बाङगेसिमल": "Bangeshimal",
    "रेडियो नेपाल": "Radio Nepal", "रेडियो नेपाल पुल": "Radio Nepal Bridge",
    "सुर्खेत अस्पताल": "Surkhet Hospital", "चाईनापुल": "China Pul",
    "खजुरापुल": "Khajura Pul", "खजुरा": "Khajura",
    "टेम्पोपार्क": "Tempo Park", "पदमपुर": "Padampur",
    "पदमपुर चोक": "Padampur Chowk", "बजाज शोरुम": "Bajaj Showroom",
    "गोकुल कटेज": "Gokul Cottage", "मलपानि चोक": "Malpani Chowk",
    "तिनकुने चोक": "Tinkune Chowk", "ईगरब्रिज": "Igar Bridge",
    "धुलियाबिट": "Dhuliyabit", "धुलियाबिट पुल": "Dhuliyabit Bridge",
    "गाग्रेताल": "Gagretal", "हिलेखाली": "Hilekhali",
    "ढोडेखाली": "Dhodhekhali",
    "बुलबुले पेट्रोल पम्प": "Bulbule Petrol Pump",
    "नारायण पेट्रोल पम्प": "Narayan Petrol Pump",
    "उमा पेट्रोल पम्प": "Uma Petrol Pump",
    "सुर्खेत पेट्रोल पम्प": "Surkhet Petrol Pump",
    "गंगामाला पेट्रोल पम्प": "Gangamala Petrol Pump",
    "सिटिजन बैक अगाडी": "Citizen Bank", "बाणिज्य बैक अगाडी": "Banijya Bank",
    "मोडल कलेज": "Model College", "माउटेण्ड स्कुल": "Mountain School",
    "सेडा स्कुल": "Seda School", "नोबेल एकेडेमी": "Nobel Academy",
    "कर्णाली केएर": "Karnali Care", "निर्भाना होटल": "Nirvana Hotel",
    "शंकर आएल स्टोर": "Shankar Oil Store",
    "सुर्खेत आयल स्टोर": "Surkhet Oil Store",
    "ईत्राम खोला पुल": "Itram Khola Bridge",
    "गौरीशंक चोक खजुरा": "Gaurishankar Chowk",
    "१ वडा कार्यालय": "Ward 1 Office", "११ न वडा कार्यालय": "Ward 11 Office",
    "आमाको भान्साघर": "Aama Ko Bhanashaghar",
}
MONTHS_NP = {
    "बैशाख": 1, "जेठ": 2, "जेष्ठ": 2, "असार": 3, "साउन": 4, "श्रावण": 4,
    "भदौ": 5, "भाद्र": 5, "असोज": 6, "आश्विन": 6, "कात्तिक": 7,
    "मंसिर": 8, "पुस": 9, "माघ": 10, "फागुन": 11, "चैत": 12,
}

def clean_value(v):
    if pd.isna(v):
        return 0
    s = str(v).translate(NEPALI_DIGITS).strip()
    if s in ("*", ".", "", "-", "nan"):
        return 0
    try:
        return int(float(s))
    except ValueError:
        return 0

def parse_datetime(raw):
    text = str(raw).translate(NEPALI_DIGITS).strip()
    date_part = text.split("गते")[0]

    year = month = day = None

    # A: 2082.04.01 / 2081.05,24 (danda, dot, COMMA, slash, dash)
    m = re.search(r"(\d{4})\s*[।./,\-]\s*(\d{1,2})\s*[।./,\-]\s*(\d{1,2})", date_part)
    if m:
        year, month, day = int(m[1]), int(m[2]), int(m[3])
    else:
        # B: 2082.0929 (month-day bich separator CHHAINA)
        m = re.search(r"(\d{4})\s*[।./,\-]\s*(\d{2})(\d{2})", date_part)
        if m:
            year, month, day = int(m[1]), int(m[2]), int(m[3])
        else:
            # C: 82.09.15 (2-digit YEAR!)
            m = re.search(r"^(\d{2})\s*[।./,\-]\s*(\d{1,2})\s*[।./,\-]\s*(\d{1,2})", date_part.strip())
            if m:
                year, month, day = int(m[1]) + 2000, int(m[2]), int(m[3])
            else:
                # D: 2080 Saun 15 (mahina ko naam)
                m = re.search(r"(\d{4})\s+([^\d\s।./,\-]+)\s+(\d{1,2})", date_part)
                if m:
                    year, day = int(m[1]), int(m[3])
                    month = MONTHS_NP.get(m[2].strip())

    if year is None or month is None or day is None:
        return None, None, None, None

    if 2065 <= year <= 2074:   # 2070 -> 2080 typo
        print(f"  🔧 year {year} typo -> {year + 10}: {text}")
        year += 10

    if not (2075 <= year <= 2083):
        print(f"  ⚠️ DROPPED (bad year {year}): {text}")
        return None, None, None, None

    ad = None
    try:
        ad = nepali_datetime.date(year, month, day).to_datetime_date()
    except Exception:
        for d_try in (31, 30, 29, 28):
            try:
                ad = nepali_datetime.date(year, month, d_try).to_datetime_date()
                print(f"  🔧 day {day} invalid -> {d_try}: {text}")
                break
            except Exception:
                continue
        if ad is None:
            print(f"  ⚠️ BS date invalid (BS matra): {text}")

    hour = None
    m2 = re.search(r"(\d{1,2})\s*[:;।]\s*\d{2}", text)
    if m2 and int(m2[1]) <= 23:
        hour = int(m2[1])

    return ad, hour, month, f"{year}-{month:02d}-{day:02d}"

def get_season(bs_month):
    if bs_month in (3, 4, 5): return "Monsoon"
    if bs_month in (6, 7): return "Festival"
    if bs_month in (9, 10): return "Foggy"
    return "Normal"

rows_out = []
sheets = pd.read_excel(FILE, sheet_name=None, header=None)

for sheet_name, grid in sheets.items():
    print(f"\n=== Sheet: {sheet_name} ({len(grid)} rows) ===")
    h0 = [str(x) for x in grid.iloc[0].tolist()]
    h2 = [str(x).strip() for x in grid.iloc[2].tolist()]

    def col(header_list, keyword):
        for i, h in enumerate(header_list):
            if keyword in h:
                return i
        return None

    C_LOC  = col(h0, "दुर्घटना भएको स्थान")
    C_DT   = col(h0, "मिति")
    C_CAUSE= col(h0, "दुर्घटनाको कारण")
    C_DEATH= col(h0, "मृत्यु")
    C_SER  = col(h0, "गम्भिर")
    C_MIN  = col(h0, "सामान्य")
    C_V2   = col(h2, "दुई पाग्रे") or (len(grid.columns) - 3)
    C_V3   = col(h2, "तिन पाग्रे") or (len(grid.columns) - 2)
    C_V4   = col(h2, "चार पाङग्रे") or (len(grid.columns) - 1)

    if None in (C_LOC, C_DT, C_CAUSE, C_DEATH, C_SER, C_MIN):
        print("  ⚠️ columns not found — sheet skipped")
        continue

    SKIP_WORDS = ("जम्मा", "Total", "total")
    parsed = 0
    carried = 0
    last_parsed = None   # merged-cell support

    for i in range(3, len(grid)):
        row = grid.iloc[i]
        loc, raw_dt = row[C_LOC], row[C_DT]

        # khali rows + totals row
        if pd.isna(loc) or str(loc).strip() in ("*", "") \
                or any(w in str(loc) for w in SKIP_WORDS):
            continue

        if pd.isna(raw_dt):
            # date cell khali — merged cell? pahileko date use
            if last_parsed is not None:
                carried += 1
                if carried <= 8:
                    print(f"  📅 row {i}: date EMPTY — pahileko use {last_parsed[3]} | loc={loc}")
                ad, hour, bs_month, bs_str = last_parsed
            else:
                print(f"  ❓ row {i}: NO DATE | loc={loc}")
                continue
        else:
            if not re.search(r"\d", str(raw_dt).translate(NEPALI_DIGITS)):
                print(f"  ❓ row {i}: date ma number chhaina | '{raw_dt}' | loc={loc}")
                continue
            ad, hour, bs_month, bs_str = parse_datetime(raw_dt)
            if bs_month is None:
                print(f"  ❓ row {i}: DATE FORMAT? '{raw_dt}' | loc={loc}")
                continue
            last_parsed = (ad, hour, bs_month, bs_str)

        cause_np = CAUSE_FIX.get(str(row[C_CAUSE]).strip(), str(row[C_CAUSE]).strip())
        deaths, serious, minor = (clean_value(row[c])
                                  for c in (C_DEATH, C_SER, C_MIN))
        v2, v3, v4 = (clean_value(row[c]) for c in (C_V2, C_V3, C_V4))

        if deaths > 0:     severity = "Fatal"
        elif serious > 0:  severity = "Serious"
        elif minor > 0:    severity = "Slight"
        else:              severity = "None"

        vt = [x for x, n in (("Two-Wheeler", v2), ("Three-Wheeler", v3),
                              ("Four-Wheeler", v4)) if n > 0]
        loc_np = LOCATION_FIX.get(str(loc).strip(), str(loc).strip())

        rows_out.append({
            "sheet": str(sheet_name), "bs_date": bs_str, "date_ad": ad,
            "hour": hour,
            "is_night": 1 if (hour is not None and (hour >= 22 or hour < 4)) else 0,
            "is_rush_hour": 1 if (hour is not None and (7 <= hour <= 9 or 16 <= hour <= 19)) else 0,
            "is_rainy_season": 1 if bs_month in (3, 4, 5) else 0,
            "is_festive_season": 1 if bs_month in (6, 7) else 0,
            "is_foggy_season": 1 if bs_month in (9, 10) else 0,
            "location_np": loc_np,
            "location_en": LOCATION_EN.get(loc_np, loc_np),
            "cause_np": cause_np, "cause_en": CAUSE_EN.get(cause_np, cause_np),
            "deaths": deaths, "serious": serious, "minor": minor,
            "severity": severity,
            "two_wheeler": v2, "three_wheeler": v3, "four_wheeler": v4,
            "vehicle_type": " + ".join(vt) if vt else "Unknown",
            "bs_month": bs_month, "season": get_season(bs_month),
        })
        parsed += 1

    print(f"  -> parsed: {parsed} | carry-forward dates: {carried}")

df = pd.DataFrame(rows_out)
df.to_csv(OUTPUT, index=False)

print("\n" + "=" * 55)
print(f"✅ CLEANED: {len(df)} records -> {OUTPUT}")
print("\n--- PER-SHEET TOTALS ---")
print(df.groupby("sheet")[["deaths", "serious", "minor"]].sum())
print("\n--- RECORDS PER SHEET ---")
print(df.groupby("sheet").size())