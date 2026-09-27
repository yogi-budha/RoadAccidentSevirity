# fix_locations.py v2 - sabai spelling variations handle
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from records.models import AccidentRecord

# Step 1: Nepali spelling normalize (sabai variations -> ek standard Nepali)
LOCATION_FIX = {
    "एरीचोक": "एरिचोक","एरपोष चोक": "एरपोट चोक",
    "गंगामाला पेट्रोल पम्म": "गंगामाला पेट्रोल पम्प",
    "गंगामाला पेट्रोल पम्प ": "गंगामाला पेट्रोल पम्प",
    "टेम्पो पार्क": "टेम्पोपार्क",
    "ट्रमा सेन्टर": "सुर्खेत अस्पताल",
    "ढोडेखालि पुल": "ढोडेखाली", "ढोडेखाली चोक": "ढोडेखाली",
    "ढोदेखालि चोक": "ढोडेखाली", "ढोलेखाली": "ढोडेखाली",
    "दैलेखी चोक": "दैलेखि चोक",
    "बजाज स्वरुम": "बजाज शोरुम", "हुन्डा सोरुम": "बजाज शोरुम",
    "बसपार्क अगाडी": "बसपार्क", "बसपार्क गेट": "बसपार्क",
    "बुदबुदे  चोक": "बुलबुले चोक", "बुबुले गेट": "बुलबुले गेट",
    "बुलबुलले पेट्रोल पम्प": "बुलबुले पेट्रोल पम्प",
    "बुलबुले पट्रोलपम्प": "बुलबुले पेट्रोल पम्प",
    "बुलबुले  चोक": "बुलबुले चोक", "बुलबुले  गेट": "बुलबुले गेट",
    "मंजलगढि चोक": "मंगलगढी चोक", "मंगलगढी": "मंगलगढी चोक",
    "मोडेलकलेज": "मोडल कलेज", "मोडेल कलेज": "मोडल कलेज",
    "राष्टिय बानिज्य बैक अगाडि": "बाणिज्य बैक अगाडी",
    "राष्‍ट्रिय बाणिज्य बैक": "बाणिज्य बैक अगाडी",
    "रेडियो  नेपाल": "रेडियो नेपाल",
    "रेडियो  नेपाल अगाडि": "रेडियो नेपाल", "रेडियो नेपाल चोक": "रेडियो नेपाल",
    "रेडियोनेपाल चोक": "रेडियो नेपाल",
    "लपानि चोक": "मुलपानि चोक",
    "नारायण पेट्रोल पम्प अगाडि": "नारायण पेट्रोल पम्प",
    "हिलेखाली चोक": "हिलेखाली",
    "पिपिराचोक": "पिपिरा चोक", "पिपिरट चोक": "पिपिरा चोक",
    "मुलापानि चोक": "मुलपानि चोक", "सुर्खेत हस्पिटल": "सुर्खेत अस्पताल",
    "धुलयाविट पुल": "धुलियाबिट पुल", "धुलयाविट": "धुलियाबिट",
    "ढोलेखाली": "ढोडेखाली",
}

# Step 2: Standard Nepali -> English
LOCATION_EN = {
    "बसपार्क": "Bus Park", "मंगलगढी चोक": "Mangalgadhi Chowk",
    "एरिचोक": "Yeri Chowk",  "एरपोट चोक": "Airport Chowk","दैलेखि चोक": "Dailekh Chowk",
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
    # --- naya locations (timro UNKNOWN list bata) ---
    "आमाको भान्साघर अगाडी": "Aama Ko Bhanashaghar",
    "देउती स्टोर पसल अगाडी": "Deuti Store",
    "धुस्रा चोक": "Ghushra chowk",
    "भुवनेश्वर पेट्रोल पम्प": "Bhuvaneshwar Petrol Pump",
    "मनाकामना ज्यरेज": "Manakamana Garage",
    "माया पेट्रोल पम्प": "Maya Petrol Pump",
    "शेरा बोढिङ": "Seda Boarding",
    "सिप्रदि अगाडी": "Sipradi Showroom",
    "सुब्बाकुना": "Subbakuna",
}

def is_devanagari(s):
    return any("\u0900" <= ch <= "\u097F" for ch in str(s))

locs = set(AccidentRecord.objects.values_list("location_name", flat=True))
nep_locs = [l for l in locs if is_devanagari(l)]

print(f"DB ma Devanagari locations: {len(nep_locs)}\n")

updated, unknown = 0, []
for l in sorted(nep_locs):
    # 1) normalize spelling, 2) double-space safai, 3) translate
    fixed = LOCATION_FIX.get(l, l).strip()
    fixed = " ".join(fixed.split())          # multiple spaces -> single
    eng = LOCATION_EN.get(fixed)

    if eng:
        n = AccidentRecord.objects.filter(location_name=l).update(location_name=eng)
        updated += n
        print(f"  ✅ '{l}' → {eng}  ({n})")
    else:
        c = AccidentRecord.objects.filter(location_name=l).count()
        unknown.append((l, c))

print(f"\nTotal records updated: {updated}")

if unknown:
    print("\n❓ AJHAI UNKNOWN:")
    for l, c in unknown:
        print(f"   '{l}' — {c}")
else:
    print("🎉 SABAI locations English ma translate bhaye!")