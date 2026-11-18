"""Hindi language layer — Python port of src/lib/hindi.ts."""
from __future__ import annotations

import re
from datetime import datetime

Lang = str  # "en" | "hi"

_DEV_RE = re.compile(r"[\u0900-\u097F]")


def has_devanagari(s: str) -> bool:
    return bool(_DEV_RE.search(s))


# Lightweight language detection for the two response languages supported by
# the Python edition. It handles Devanagari Hindi and common Romanized Hindi /
# Hinglish without requiring a network API or an extra package.
_ROMAN_HINDI_SIGNALS = {
    "aaj", "kal", "parso", "abhi", "kya", "kyu", "kyun", "kab",
    "kahan", "kahaan", "kidhar", "kaise", "kaisa", "kaisi", "kitna",
    "kitni", "kitne", "kaun", "kaunsa", "kaunsi", "mujhe", "mujhko",
    "mera", "meri", "mere", "hamara", "hamari", "aapka", "aapki",
    "aapke", "hai", "hain", "ho", "tha", "thi", "the", "hoga",
    "hogi", "honge", "nahi", "nahin", "haan", "batao", "dikhao",
    "chahiye", "karo", "karna", "kahan", "namaste", "shukriya",
    "dhanyavaad", "khali", "kaali", "classen", "classes", "mein", "koi",
}
_ROMAN_HINDI_STRONG = {
    "aaj", "parso", "kya", "kyu", "kyun", "kab", "kahan", "kahaan",
    "kidhar", "kaise", "kaisa", "kaisi", "kitna", "kitni", "kitne",
    "kaun", "kaunsa", "kaunsi", "mujhe", "mujhko", "mera", "meri",
    "mere", "hamara", "hamari", "aapka", "aapki", "aapke", "hai", "hain",
    "ho", "kal", "batao", "dikhao", "chahiye", "nahi", "nahin", "haan", "namaste", "shukriya",
    "dhanyavaad", "khali", "mein", "abhi",
}
_ENGLISH_SIGNALS = {
    "what", "when", "where", "who", "why", "how", "is", "are", "do",
    "does", "can", "could", "would", "my", "your", "the", "please",
    "tell", "show", "today", "tomorrow", "yesterday", "next", "class",
}


def detect_language(text: str) -> str:
    """Return 'hi' or 'en'; currently Hindi and English are supported."""
    if has_devanagari(text):
        return "hi"
    tokens = re.findall(r"[a-z]+", (text or "").lower())
    if not tokens:
        return "en"
    hindi_tokens = [t for t in tokens if t in _ROMAN_HINDI_SIGNALS]
    strong_hindi = sum(t in _ROMAN_HINDI_STRONG for t in tokens)
    english = sum(t in _ENGLISH_SIGNALS for t in tokens)
    # Prefer Hindi when the query has multiple Hindi markers, or one strong
    # marker and no clear English sentence framing. This also supports code-
    # switching such as "meri next class kab hai?".
    if strong_hindi >= 2 or (strong_hindi >= 1 and strong_hindi >= english):
        return "hi"
    if len(hindi_tokens) >= 2 and len(hindi_tokens) > english:
        return "hi"
    return "en"


_DEV_DIGITS = {"०": "0", "१": "1", "२": "2", "३": "3", "४": "4", "५": "5", "६": "6", "७": "7", "८": "8", "९": "9"}


def _dev_digits(s: str) -> str:
    return re.sub(r"[०-९]", lambda m: _DEV_DIGITS.get(m.group(0), m.group(0)), s)


# keep Devanagari + latin alphanumerics, strip punctuation
_PUNCT_RE = re.compile(r"[^\u0900-\u097Fa-z0-9\s-]")


def normalize_hi(raw: str) -> str:
    s = _dev_digits(raw.lower())
    s = _PUNCT_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return " " + s + " "


HI_PHRASES: list[tuple[str, str]] = [
    ("दिन के बाद कल", "day after tomorrow"),
    ("कितने बजे", "what time"),
    ("किस जगह", "where"),
    ("कहाँ पर", "where"),
    ("कहाँ होता", "where"),
    ("कहाँ होती", "where"),
    ("कौन पढ़ाता", "who teaches"),
    ("कौन पढ़ाते", "who teaches"),
    ("कौन सी", "which"),
    ("कौन से", "which"),
    ("कौन सा", "which"),
    ("ऑफिस आवर्स", "office hours"),
    ("ऑफिस अवर्स", "office hours"),
    ("इस हफ्ते", "this week"),
    ("अगले हफ्ते", "next week"),
    ("के बारे में", "about"),
]

HI_WORDS: dict[str, str] = {
    "नमस्ते": "hello", "नमस्कार": "hello", "हेलो": "hello", "हाय": "hi",
    "धन्यवाद": "thank you", "शुक्रिया": "thank you", "थैंक्स": "thanks",
    "अलविदा": "goodbye", "बाय": "bye",
    "क्लासें": "classes", "क्लासेस": "classes", "क्लासिस": "classes", "क्लास": "class",
    "कक्षा": "class", "टाइमटेबल": "timetable", "शेड्यूल": "schedule",
    "लेक्चर": "lecture", "पीरियड": "period", "सब्जेक्ट": "subject", "सब्जेक्ट्स": "subjects",
    "टिमटेबल": "timetable", "पढ़ाई": "study",
    "आज": "today", "कल": "tomorrow", "परसों": "day after tomorrow",
    "अभी": "now", "समय": "time", "हफ्ते": "week", "हफ्ता": "week",
    "सोमवार": "monday", "मंगलवार": "tuesday", "बुधवार": "wednesday",
    "गुरुवार": "thursday", "वीरवार": "thursday", "शुक्रवार": "friday",
    "शनिवार": "saturday", "रविवार": "sunday", "इतवार": "sunday",
    "सुबह": "morning", "दोपहर": "afternoon", "शाम": "evening",
    "कमरा": "room", "कमरे": "room", "रूम्स": "rooms", "रूम": "room",
    "लैब्स": "labs", "लैब": "lab", "हॉल": "hall",
    "खाली": "free", "फ़्री": "free", "फ्री": "free", "उपलब्ध": "available",
    "नोटिसेस": "notices", "नोटिस": "notice",
    "सूचनाएं": "notices", "सूचनाएँ": "notices", "सूचना": "notice",
    "घोषणा": "announcement", "घोषणाएं": "announcements",
    "परीक्षा": "exam", "एग्जाम": "exam", "मिडसेम": "midsem",
    "रिजल्ट": "result", "बैकलॉग": "backlog", "रजिस्ट्रेशन": "registration",
    "फीस": "fees", "छुट्टी": "holiday", "छुट्टियाँ": "holidays",
    "वाईफाई": "wifi", "आईडी": "id",
    "प्लेसमेंट": "placement", "इंटर्नशिप": "internship", "कंपनी": "company", "नौकरी": "job",
    "इवेंट्स": "events", "इवेंट": "event", "कार्यक्रम": "event", "फेस्ट": "fest",
    "हैकैथॉन": "hackathon", "हैकाथॉन": "hackathon", "वर्कशॉप": "workshop",
    "क्लब": "club", "कंपटीशन": "competition", "प्रतियोगिता": "competition",
    "कॉन्सर्ट": "concert", "मैच": "match", "स्पोर्ट्स": "sports", "खेल": "sports",
    "फुटबॉल": "football", "क्रिकेट": "cricket", "ट्रायल्स": "trials", "ट्रायल": "trials",
    "लाइब्रेरी": "library", "कैंटीन": "canteen", "कैफेटेरिया": "cafeteria",
    "ऑडिटोरियम": "auditorium", "हॉस्टल": "hostel", "अस्पताल": "hospital",
    "क्लिनिक": "clinic", "स्वास्थ्य": "health",
    "प्रोफेसर": "professor", "प्रोफ़ेसर": "professor", "प्रो": "prof",
    "फैकल्टी": "faculty", "ऑफिस": "office", "ईमेल": "email",
    "ऑवर्स": "hours", "अवर्स": "hours", "डीन": "dean", "एचओडी": "hod",
    "पढ़ाता": "teaches", "पढ़ाते": "teaches", "पढ़ाती": "teaches", "पड़ाते": "teaches",
    "मिलना": "meet", "मिलें": "meet",
    "कहाँ": "where", "किधर": "where", "कब": "when", "कौन": "who",
    "क्या": "what", "कितने": "how many", "कितनी": "how many", "कितना": "how many",
    "कोई": "any", "नई": "new", "नया": "new", "लेटेस्ट": "latest",
    "अगली": "next", "अगला": "next", "नेक्स्ट": "next", "पूरी": "full", "पूरा": "full",
    "मुझे": "", "मेरी": "my", "मेरे": "my", "बताओ": "tell", "बताइए": "tell",
    "बताइये": "tell", "बता": "tell", "दिखाओ": "show", "दीजिए": "", "चाहिए": "",
    "हैं": "", "है": "", "होता": "", "होती": "", "होगा": "", "होगी": "",
    "की": "", "के": "", "का": "", "में": "", "पे": "", "पर": "", "से": "",
    "और": "and", "भी": "", "तो": "", "ये": "", "वो": "", "बारे": "about",
    "मेहता": "mehta", "राव": "rao", "राओ": "rao", "अय्यर": "iyer", "ऐयर": "iyer",
    "अली": "ali", "आनंद": "anand", "आनन्द": "anand", "शर्मा": "sharma",
    "नायर": "nair", "कुरैशी": "qureshi", "कुरेशी": "qureshi", "मेनन": "menon",
    "चंद्रन": "chandran", "वर्मा": "verma", "डॉक्टर": "dr", "डॉ": "dr",
}


def with_english_map(hi_normalized: str) -> str:
    s = hi_normalized
    # Normalize common Romanized Hindi words as well, so AUTO works for
    # queries such as "meri next class kab hai" as well as Devanagari Hindi.
    roman_map = {
        "aaj": "today", "kal": "tomorrow", "parso": "day after tomorrow",
        "abhi": "now", "kya": "what", "kab": "when", "kahan": "where",
        "kahaan": "where", "kaha": "where", "kidhar": "where", "kaise": "how",
        "kitna": "how many", "kitni": "how many", "kitne": "how many",
        "kaun": "who", "kaunsa": "which", "kaunsi": "which",
        "meri": "my", "mera": "my", "mere": "my", "mujhe": "me",
        "mujhko": "me", "hai": "is", "hain": "are", "ho": "are",
        "tha": "was", "thi": "was", "nahi": "not",
        "nahin": "not", "haan": "yes", "koi": "any", "batao": "tell", "dikhao": "show",
        "chahiye": "need", "khali": "free", "mein": "in", "aapka": "your",
        "aapki": "your", "aapke": "your", "namaste": "hello",
        "shukriya": "thank you", "dhanyavaad": "thank you",
    }
    tokens0 = [roman_map.get(t, t) if t else t for t in s.split(" ")]
    s = " ".join(tokens0)
    # token-aware code transliteration: बी-208 → b-208 (digits already latinized)
    s = re.sub(r"(\s)बी(\s*-?\s*[0-9])", r"\1b\2", s)
    s = re.sub(r"(\s)एल(\s*-?\s*[0-9])", r"\1l\2", s)
    s = re.sub(r"(\s)ए(\s*-?\s*[0-9])", r"\1a\2", s)
    s = re.sub(r"(\s)सी(\s*-?\s*[0-9])", r"\1c\2", s)
    s = re.sub(r"(\s)डी(\s*-?\s*[0-9])", r"\1d\2", s)
    for src, dst in HI_PHRASES:
        s = s.replace(f" {src} ", f" {dst} ")
    tokens = [HI_WORDS.get(t, t) if t else t for t in s.split(" ")]
    out = " " + " ".join(tokens)
    return " " + re.sub(r"\s+", " ", out).strip() + " "


COURSE_HI: dict[str, list[str]] = {
    "CS-301": ["डेटा स्ट्रक्चर", "डेटास्ट्रक्चर", "डीएसए", "अल्गोरिदम"],
    "CS-302": ["ओएस", "ऑपरेटिंग सिस्टम", "ओपरेटिंग सिस्टम"],
    "CS-303": ["डीबीएमएस", "डेटाबेस"],
    "CS-304": ["नेटवर्क्स", "नेटवर्क", "कंप्यूटर नेटवर्क"],
    "CS-305": ["एआई", "आर्टिफिशियल", "आर्टिफ़िशियल", "एआइ"],
    "MA-301": ["गणित", "डिस्क्रेट", "मैथ्स", "मैथ"],
    "HM-203": ["एथिक्स", "ह्यूमैनिटी", "ह्यूमैनिटीज", "इथिक्स"],
    "CS-391": ["डीबीएमएस लैब", "डेटाबेस लैब"],
    "CS-392": ["नेटवर्क्स लैब", "नेटवर्क लैब"],
    "EC-301": ["सिग्नल्स", "सिगनल", "सिग्नल"],
}

HI_DAYS = ["", "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]


def hi_day_label(day: int, today: int) -> str:
    if day == today:
        return "आज"
    if day == today % 7 + 1:
        return "कल"
    return HI_DAYS[day]


def hi_day_phrase(day: int, today: int) -> str:
    if day == today:
        return "आज"
    if day == today % 7 + 1:
        return "कल"
    return f"{HI_DAYS[day]} को"


def time_ago_hi(d: datetime, now: datetime | None = None) -> str:
    now = now or datetime.now()
    diff = max(0, (now - d).total_seconds())
    mins = int(diff // 60)
    if mins < 1:
        return "अभी-अभी"
    if mins < 60:
        return f"{mins} मिनट पहले"
    hrs = mins // 60
    if hrs < 24:
        return f"{hrs} घंटे पहले"
    days = hrs // 24
    if days == 1:
        return "कल"
    if days < 7:
        return f"{days} दिन पहले"
    return f"{days // 7} हफ़्ते पहले"


def in_days_label_hi(starts_at: datetime, now: datetime | None = None) -> str:
    now = now or datetime.now()
    diff = (starts_at.date() - now.date()).days
    if diff <= 0:
        return "आज"
    if diff == 1:
        return "कल"
    if diff < 7:
        return f"{diff} दिन में"
    weeks = diff // 7
    return "अगले हफ़्ते" if weeks == 1 else f"{weeks} हफ़्ते में"


_HI_LETTERS = {"A": "ए", "B": "बी", "C": "सी", "L": "एल"}


def hi_voice_code(code: str) -> str:
    out = []
    for ch in code.replace("-", " "):
        mapped = _HI_LETTERS.get(ch.upper())
        out.append(mapped if mapped else ch)
    return re.sub(r"\s+", " ", " ".join(out)).strip()
