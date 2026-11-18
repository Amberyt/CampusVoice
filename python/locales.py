"""Localized response builders — Python port of src/lib/locales.ts."""
from __future__ import annotations

Say = dict  # {"text": str, "speak": str}


def _say(text: str, speak: str) -> Say:
    return {"text": text, "speak": speak}


# ============================================================ ENGLISH
def _en_sugg(kind: str, arg: str | None = None) -> list[str]:
    a = arg or ""
    table = {
        "thanks": ["What's my next class?", "Any new notices?"],
        "notices": ["Any exam notices?", "Events this week", "Today's timetable"],
        "events": ["When is the hackathon?", "Latest notices", "My classes tomorrow"],
        "eventsDetail": ["Events this week", "Latest notices", "Free rooms right now"],
        "freeRooms": ["My classes today", "Where is DBMS held?", "Latest notices"],
        "facility": ["Free rooms right now", "Any facility notices?", "What's on this week"],
        "faculty": ["Who teaches DBMS?", "Free rooms right now", "Latest notices"],
        "roomInfo": ["Free rooms right now", "What's my next class?", "Latest notices"],
        "nowActive": ["What's next?", "Free rooms right now", "Latest notices"],
        "nowFree": ["Today's timetable", "Free rooms right now", "Latest notices"],
        "nowDone": ["Events this week", "My classes tomorrow"],
        "next": [f"{a or 'Monday'} full timetable", "Free rooms right now", "Latest notices"],
        "courseWhere": [f"When is the next {a or 'DBMS'} class?", "Free rooms right now", "Any exam notices?"],
        "courseSchedule": [f"Where is {a or 'DBMS'} held?", f"Who teaches {a or 'DBMS'}?", "Today's timetable"],
        "count": [f"Classes on {a or 'Monday'}", "Free rooms right now"],
        "day": ["Tomorrow's classes", "Free rooms right now", "Latest notices"],
        "week": ["Today's timetable", "Tomorrow's classes", "Free rooms now"],
    }
    return table.get(kind, [
        "What classes do I have today?", "Free rooms right now", "Latest notices",
        "When is the hackathon?", "Where is the library?",
    ])


EN = {
    "greeting": lambda: _say(
        "Hello! I'm AURA, Astra University's voice assistant. Ask me about your timetable, rooms, notices, events, or faculty — try \"What classes do I have on Monday?\"",
        "Hello! I'm Aura, Astra University's voice assistant. Ask me about your timetable, rooms, notices, events, or faculty.",
    ),
    "thanks": lambda: _say(
        "Anytime. I'm right here whenever you need the campus — just tap the orb and ask.",
        "Anytime. I'm right here whenever you need me.",
    ),
    "bye": lambda: _say("See you around campus. Good luck with your classes!", "See you around campus. Good luck with your classes!"),
    "help": lambda: _say(
        "Here's what I can answer: daily timetables (\"classes on Friday\"), what's on right now or next, where a course is held, free rooms and labs, room details (\"where is B-208\"), the latest notices by category, upcoming events, and faculty offices, hours and emails.",
        "I can answer questions about your timetable, free rooms, notices, events, and faculty. Try asking: what classes do I have today?",
    ),
    "identity": lambda: _say(
        "I'm AURA — the Astra Unified Response Assistant. I live on top of the campus database, so timetables, rooms, notices and events are all one question away.",
        "I'm Aura, the Astra Unified Response Assistant, your campus on call.",
    ),
    "fallback": lambda: _say(
        "I couldn't quite map that to the campus database. Try asking about your timetable (\"classes on Monday\"), rooms (\"where is B-208\" / \"free labs\"), notices (\"any exam notices\"), events (\"when is the hackathon\") or faculty (\"Dr. Mehta's office hours\").",
        "I couldn't quite map that. Try asking about your timetable, rooms, notices, events, or faculty — for example, what classes do I have on Monday?",
    ),
    "noticesEmpty": lambda cat: _say(
        f"There are no {cat or ''} notices on the board right now. All clear.",
        f"There are no {cat or ''} notices right now.",
    ),
    "noticesList": lambda a: _say(
        (f"Here are the latest {a['catLabel']} notices. " if a.get("catLabel") else "Here's what's fresh on the notice board. ") + a["itemsTxt"] + ".",
        (f"I found {a['count']} {a['catLabel']} notices. The latest: {a['firstTitle']}. Details are on your screen."
         if a.get("catLabel") else
         f"I found {a['count']} fresh notices. The latest: {a['firstTitle']}. Details are on your screen."),
    ),
    "eventsEmpty": lambda: _say(
        "No matching events on the calendar yet. I'll flag them as soon as the clubs publish.",
        "There are no matching events on the calendar yet.",
    ),
    "eventsDetail": lambda a: _say(
        f"{a['title']} — {a['when']}, at {a['location']}. Hosted by {a['organizer']}. {a['description']}",
        f"{a['title']} is {a['when']} at {a['location']}. Full details are on your screen.",
    ),
    "eventsList": lambda a: _say(
        f"Here's what's coming up{(' in ' + a['catLabel']) if a.get('catLabel') else ''}{a['whenPhrase']}: {a['itemsTxt']}.",
        f"Coming up: {a['speakItems']}. Details are on your screen.",
    ),
    "roomsFree": lambda a: _say(
        "It's Sunday — every teaching room and lab is free today. The campus is yours."
        if a["sunday"] else
        (f"All {a['total']} {'labs' if a['wantLabs'] else 'teaching rooms'} are free right now — take your pick: {a['picksTxt']}{', and more' if a['more'] else ''}."
         if a["allFree"] else
         f"{a['count']} of {a['total']} {'labs' if a['wantLabs'] else 'teaching rooms'} are free right now ({a['busy']} occupied). {a['picksTxt']}{', and more' if a['more'] else ''}."),
        "It's Sunday — every teaching room and lab is free today. The campus is yours."
        if a["sunday"] else
        (f"All {a['total']} {'labs' if a['wantLabs'] else 'rooms'} are free. The list is on your screen."
         if a["allFree"] else
         f"{a['count']} {'labs' if a['wantLabs'] else 'rooms'} are free right now, including {a['picksSpeak']}. The full list is on your screen."),
    ),
    "facility": lambda a: _say(
        (f"{a['name']} — {a['block']}. {a['meta']}").strip(),
        f"{a['name']}. {a['meta'] or 'Details are on your screen.'}",
    ),
    "facultyCourse": lambda a: _say(
        f"{a['prof']} ({a['profTitle']}, {a['dept']}) teaches {a['title']} — {a['code']}. Office: {a['office']}. Office hours: {a['hours']}. Email: {a['email']}.",
        f"{a['prof']} teaches {a['title']}. Office hours: {a['hours']}, at {a['office']}. The email is on your screen.",
    ),
    "faculty": lambda a: _say(
        f"{a['name']} — {a['title']}, {a['dept']}. Office: {a['office']}. Office hours: {a['hours']}. Email: {a['email']}.",
        f"{a['name']}, {a['title']} of {a['dept']}. Office: {a['office']}. Office hours: {a['hours']}. The email address is on your screen.",
    ),
    "roomInfo": lambda a: _say(
        f"{a['code']} is {a['name']}, on {a['floor']} of {a['block']}.{a['capacity']}{a['statusTxt']}",
        f"{a['voiceCode']} is the {a['name']}, in {a['block']}.{a['capacity']}{a['statusTxt']}",
    ),
    "courseWhere": lambda a: _say(
        f"{a['title']} ({a['code']}) is held in {a['placesTxt']}. This week: {a['timesTxt']}.{a['roomDetail']}",
        f"{a['title']} is held in {a['placesSpeak']}, {a['blockFirst']}. Times are on your screen.",
    ),
    "nowSunday": lambda: _say("It's Sunday — no classes today. Perfect for the library or the football ground.", "It's Sunday. No classes today."),
    "nowActive": lambda a: _say(
        f"Right now: {a['title']} with {a['professor']} in {a['room']}, until {a['endTime']}."
        + (f" Up next at {a['nextTime']}: {a['nextTitle']} in {a['nextRoom']}." if a.get("nextTitle") else " Nothing after this — you're done for the day."),
        f"Right now you have {a['title']} in {a['voiceRoom']}, until {a['endTime']}."
        + (f" Next up: {a['nextTitle']} at {a['nextTime']}." if a.get("nextTitle") else ""),
    ),
    "nowFree": lambda a: _say(
        f"No class in session right now. Your next one is {a['title']} at {a['time']} in {a['room']}.",
        f"No class right now. Your next one is {a['title']} at {a['time']} in {a['voiceRoom']}.",
    ),
    "nowDone": lambda: _say(
        "No class right now — you're done for the day. Maybe check what's happening on campus this week?",
        "No class right now, you're done for the day.",
    ),
    "nextClass": lambda a: _say(
        f"Your next class is {a['title']} {a['when']} at {a['time']}, in {a['room']}{(' with ' + a['professor']) if a.get('professor') else ''}.",
        f"Your next class is {a['title']}, {a['when']} at {a['time']}, in {a['voiceRoom']}.",
    ),
    "nextNone": lambda: _say("There are no classes scheduled for the entire week. Enjoy the break!", "No classes scheduled this week."),
    "courseScheduleNone": lambda a: _say(
        f"{a['title']} has no session on {a['dayName']}. It meets {a['weekly']} times a week — ask \"when is {a['code']}\" for the full picture.",
        f"{a['title']} has no session that day.",
    ),
    "courseSchedule": lambda a: _say(
        f"{a['title']} ({a['code']}) with {a['professor']} — {'1 session' if a['count'] == 1 else str(a['count']) + ' sessions'} {a['scope']}: {a['timesTxt']}.",
        f"{a['title']} meets {a['count']} time{'s' if a['count'] > 1 else ''}: {a['speakTxt']}.",
    ),
    "countZero": lambda a: _say(
        "Zero classes {phrase}{sun}. Enjoy the breathing room.".format(phrase=a["phrase"], sun=" — it's Sunday" if a["sunday"] else ""),
        f"You have no classes {a['phrase']}.",
    ),
    "count": lambda a: _say(
        f"You have {a['count']} class{'es' if a['count'] > 1 else ''} {a['phrase']}, from {a['start']} to {a['end']}.",
        f"You have {a['count']} classes {a['phrase']}, starting at {a['start']}.",
    ),
    "dayEmpty": lambda a: _say(
        f"No classes {a['phrase']}{' — Sunday is a holiday at Astra' if a['sunday'] else ''}. "
        + (f"The week picks up again with {a['afterTitle']} on {a['afterDay']} at {a['afterTime']}." if a.get("afterTitle") else ""),
        f"No classes {a['phrase']}. " + (f"Next up, {a['afterTitle']} on {a['afterDay']}." if a.get("afterTitle") else ""),
    ),
    "day": lambda a: _say(
        (f"You have {a['count']} class{'es' if a['count'] > 1 else ''} {a['phrase']}: {a['itemsTxt']}." if a["relative"]
         else f"{a['dayName']} has {a['count']} classes: {a['itemsTxt']}.") ,
        ((f"You have {a['count']} classes {a['phrase']}" if a["relative"] else f"On {a['dayName']} you have {a['count']} classes")
         + f". {a['speakTxt']}{' — plus ' + str(a['more']) + ' more, on your screen.' if a['more'] > 0 else ''}"),
    ),
    "todayEmpty": lambda: _say("No classes today — a free day at Astra. Ask me for tomorrow\'s plan.", "No classes today."),
    "week": lambda a: _say(
        f"The week at a glance for CSE Semester 5, Section A: {a['parts']}. Sunday is free.",
        "Here's your week at a glance. The next few sessions are on your screen.",
    ),
    "weekEmpty": lambda: _say("No classes this week.", "No classes this week."),
    "sugg": _en_sugg,
}


# ============================================================ हिंदी
def _hi_sugg(kind: str, arg: str | None = None) -> list[str]:
    a = arg or "सोमवार"
    table = {
        "thanks": ["मेरी अगली क्लास क्या है?", "कोई नई सूचना?"],
        "notices": ["कोई एग्जाम की सूचना?", "इस हफ्ते के इवेंट", "आज का टाइमटेबल"],
        "events": ["हैकैथॉन कब है?", "ताज़ा सूचनाएँ", "कल की क्लासें"],
        "eventsDetail": ["इस हफ्ते के इवेंट", "ताज़ा नोटिस", "अभी खाली रूम"],
        "freeRooms": ["आज की क्लासें", "डीबीएमएस कहाँ होता है?", "ताज़ा सूचनाएँ"],
        "facility": ["अभी खाली रूम", "कोई फैसिलिटी नोटिस?", "इस हफ्ते के इवेंट"],
        "faculty": ["डीबीएमएस कौन पढ़ाता है?", "अभी खाली रूम", "ताज़ा सूचनाएँ"],
        "roomInfo": ["अभी खाली रूम", "मेरी अगली क्लास क्या है?", "ताज़ा सूचनाएँ"],
        "nowActive": ["अगली क्लास क्या है?", "अभी खाली रूम", "ताज़ा सूचनाएँ"],
        "nowFree": ["आज का टाइमटेबल", "अभी खाली रूम", "ताज़ा सूचनाएँ"],
        "nowDone": ["इस हफ्ते के इवेंट", "कल की क्लासें"],
        "next": [f"{a} का पूरा टाइमटेबल", "अभी खाली रूम", "ताज़ा सूचनाएँ"],
        "courseWhere": [f"{a} कब है?", "अभी खाली रूम", "कोई एग्जाम की सूचना?"],
        "courseSchedule": [f"{a} कहाँ होता है?", f"{a} कौन पढ़ाता है?", "आज का टाइमटेबल"],
        "count": [f"{a} का टाइमटेबल", "अभी खाली रूम"],
        "day": ["कल की क्लासें", "अभी खाली रूम", "ताज़ा सूचनाएँ"],
        "week": ["आज का टाइमटेबल", "कल की क्लासें", "अभी खाली रूम"],
    }
    return table.get(kind, [
        "आज कितनी क्लासें हैं?", "कौन से रूम अभी खाली हैं?", "नई सूचनाएँ",
        "हैकैथॉन कब है?", "लाइब्रेरी कहाँ है?",
    ])


HI = {
    "greeting": lambda: _say(
        "नमस्ते! मैं ओरा हूँ — आस्त्रा यूनिवर्सिटी की वॉइस असिस्टेंट। आप मुझसे टाइमटेबल, रूम, नोटिस, इवेंट या फैकल्टी के बारे में पूछ सकते हैं — जैसे \"सोमवार को कौन सी क्लासें हैं?\"",
        "नमस्ते! मैं ओरा हूँ, आस्त्रा यूनिवर्सिटी की वॉइस असिस्टेंट। आप मुझसे टाइमटेबल, रूम, नोटिस, इवेंट और फैकल्टी के बारे में पूछ सकते हैं।",
    ),
    "thanks": lambda: _say(
        "आपका बहुत-बहुत स्वागत है। जब भी कैंपस की ज़रूरत हो, ऑर्ब दबाएँ और पूछ लीजिए।",
        "कोई बात नहीं। जब भी ज़रूरत हो, मैं यहीं हूँ।",
    ),
    "bye": lambda: _say("फिर मिलते हैं कैंपस में। क्लासें मुबारक!", "फिर मिलते हैं। अपना ख़याल रखिए।"),
    "help": lambda: _say(
        "आप ये पूछ सकते हैं: दिन भर का टाइमटेबल (\"सोमवार को क्लासें बताओ\"), अभी या अगली क्लास, किसी कोर्स की जगह, अभी खाली रूम या लैब, किसी रूम की जानकारी, ताज़ा नोटिस, आने वाले इवेंट, और फैकल्टी के ऑफिस, टाइम और ईमेल।",
        "मैं टाइमटेबल, खाली रूम, नोटिस, इवेंट और फैकल्टी के सवालों के जवाब दे सकती हूँ। पूछकर देखिए: आज कितनी क्लासें हैं?",
    ),
    "identity": lambda: _say(
        "मैं ओरा हूँ — आस्त्रा यूनिफ़ाइड रिस्पॉन्स असिस्टेंट। कैंपस डेटाबेस से सीधे जुड़ी हूँ, इसलिए टाइमटेबल, रूम, नोटिस और इवेंट बस एक सवाल दूर हैं।",
        "मैं ओरा हूँ, आस्त्रा यूनिफ़ाइड रिस्पॉन्स असिस्टेंट, आपकी कैंपस साथी।",
    ),
    "fallback": lambda: _say(
        "यह मुझे समझ नहीं आया। आप इनसे पूछ सकते हैं: टाइमटेबल (\"सोमवार को क्लासें\"), रूम (\"बी-208 कहाँ है?\" / \"खाली लैब\"), नोटिस (\"कोई एग्जाम की सूचना?\"), इवेंट (\"हैकैथॉन कब है?\") या फैकल्टी (\"डॉक्टर मेहता के ऑफिस आवर्स\")।",
        "यह मुझे समझ नहीं आया। टाइमटेबल, रूम, नोटिस, इवेंट या फैकल्टी के बारे में पूछिए — मसलन, सोमवार को कौन सी क्लासें हैं?",
    ),
    "noticesEmpty": lambda cat: _say(
        f"इस समय कोई {cat or ''} नोटिस नहीं है। सब साफ़ है।",
        f"इस समय कोई {cat or ''} नोटिस नहीं है।",
    ),
    "noticesList": lambda a: _say(
        (f"ताज़ा {a['catLabel']} नोटिस इस प्रकार हैं। " if a.get("catLabel") else "नोटिस बोर्ड की ताज़ा बातें। ") + a["itemsTxt"] + "।",
        f"मुझे {a['count']} नोटिस मिले। सबसे ताज़ा: {a['firstTitle']}। पूरी जानकारी स्क्रीन पर है।",
    ),
    "eventsEmpty": lambda: _say(
        "इस समय कोई मैचिंग इवेंट कैलेंडर पर नहीं है। जैसे ही आएगा, बता दूँगी।",
        "इस समय कोई मैचिंग इवेंट कैलेंडर पर नहीं है।",
    ),
    "eventsDetail": lambda a: _say(
        f"{a['title']} — {a['when']}, जगह: {a['location']}। आयोजक: {a['organizer']}। {a['description']}",
        f"{a['title']} {a['when']} है, {a['location']} में। पूरी जानकारी स्क्रीन पर है।",
    ),
    "eventsList": lambda a: _say(
        f"आने वाले इवेंट{(' (' + a['catLabel'] + ')') if a.get('catLabel') else ''}{a['whenPhrase']}: {a['itemsTxt']}।",
        f"आने वाले इवेंट: {a['speakItems']}। विवरण स्क्रीन पर है।",
    ),
    "roomsFree": lambda a: _say(
        "आज रविवार है — हर टीचिंग रूम और लैब खाली है। कैंपस आपका है।"
        if a["sunday"] else
        (f"सभी {a['total']} {'लैब' if a['wantLabs'] else 'टीचिंग रूम'} अभी खाली हैं — जो चाहें ले लें: {a['picksTxt']}{', और भी' if a['more'] else ''}।"
         if a["allFree"] else
         f"{a['total']} में से {a['count']} {'लैब' if a['wantLabs'] else 'टीचिंग रूम'} अभी खाली हैं ({a['busy']} व्यस्त)। {a['picksTxt']}{', और भी' if a['more'] else ''}।"),
        "आज रविवार है — सभी टीचिंग रूम और लैब खाली हैं।"
        if a["sunday"] else
        (f"सभी {a['total']} {'लैब' if a['wantLabs'] else 'रूम'} खाली हैं। पूरी सूची स्क्रीन पर है।"
         if a["allFree"] else
         f"इस समय {a['count']} {'लैब' if a['wantLabs'] else 'रूम'} खाली हैं, जैसे {a['picksSpeak']}। पूरी सूची स्क्रीन पर है।"),
    ),
    "facility": lambda a: _say(
        (f"{a['name']} — {a['block']}। {a['meta']}").strip(),
        f"{a['name']}। {a['meta'] or 'जानकारी स्क्रीन पर है।'}",
    ),
    "facultyCourse": lambda a: _say(
        f"{a['title']} ({a['code']}) {a['prof']} ({a['profTitle']}, {a['dept']}) पढ़ाते हैं। ऑफिस: {a['office']}। ऑफिस आवर्स: {a['hours']}। ईमेल: {a['email']}।",
        f"{a['title']} {a['prof']} पढ़ाते हैं। ऑफिस आवर्स: {a['hours']}, {a['office']} में। ईमेल स्क्रीन पर है।",
    ),
    "faculty": lambda a: _say(
        f"{a['name']} — {a['title']}, {a['dept']}। ऑफिस: {a['office']}। ऑफिस आवर्स: {a['hours']}। ईमेल: {a['email']}।",
        f"{a['name']}, {a['dept']} में {a['title']}। ऑफिस: {a['office']}। ऑफिस आवर्स: {a['hours']}। ईमेल स्क्रीन पर है।",
    ),
    "roomInfo": lambda a: _say(
        f"{a['code']} यानी {a['name']}, {a['block']} में, {a['floor']} पर।{a['capacity']}{a['statusTxt']}",
        f"{a['voiceCode']} यानी {a['name']}, {a['block']} में है।{a['capacity']}{a['statusTxt']}",
    ),
    "courseWhere": lambda a: _say(
        f"{a['title']} ({a['code']}) {a['placesTxt']} में होता है। इस हफ्ते: {a['timesTxt']}।{a['roomDetail']}",
        f"{a['title']} {a['placesSpeak']} में होता है, {a['blockFirst']}। समय स्क्रीन पर है।",
    ),
    "nowSunday": lambda: _say(
        "आज रविवार है — आज कोई क्लास नहीं। लाइब्रेरी या फुटबॉल ग्राउंड बढ़िया विकल्प हैं।",
        "आज रविवार है। कोई क्लास नहीं।",
    ),
    "nowActive": lambda a: _say(
        f"इस समय: {a['title']}, {a['professor']} के साथ, {a['room']} में, {a['endTime']} तक।"
        + (f" इसके बाद {a['nextTime']}: {a['nextTitle']}, {a['nextRoom']} में।" if a.get("nextTitle") else " इसके बाद कुछ नहीं — आज का काम ख़त्म।"),
        f"इस समय आपकी {a['title']} चल रही है, {a['voiceRoom']} में, {a['endTime']} तक।"
        + (f" अगली क्लास: {a['nextTitle']}, {a['nextTime']} पर।" if a.get("nextTitle") else ""),
    ),
    "nowFree": lambda a: _say(
        f"अभी कोई क्लास नहीं चल रही। अगली क्लास {a['title']} है, {a['time']} पर, {a['room']} में।",
        f"अभी कोई क्लास नहीं है। अगली क्लास {a['title']}, {a['time']} पर, {a['voiceRoom']} में।",
    ),
    "nowDone": lambda: _say(
        "अभी कोई क्लास नहीं — आज का काम ख़त्म। कैंपस में इस हफ्ते क्या हो रहा है, वो देख लें?",
        "अभी कोई क्लास नहीं, आज का काम ख़त्म।",
    ),
    "nextClass": lambda a: _say(
        f"आपकी अगली क्लास {a['title']} है, {a['when']}, {a['time']} पर, {a['room']} में{(', ' + a['professor'] + ' के साथ') if a.get('professor') else ''}।",
        f"आपकी अगली क्लास {a['title']} है, {a['when']}, {a['time']} पर, {a['voiceRoom']} में।",
    ),
    "nextNone": lambda: _say("पूरे हफ्ते कोई क्लास शेड्यूल नहीं है। ब्रेक मुबारक!", "इस हफ्ते कोई क्लास नहीं है।"),
    "courseScheduleNone": lambda a: _say(
        f"{a['title']} की {a['dayName']} को कोई क्लास नहीं है। यह हफ्ते में {a['weekly']} बार होता है — पूरा शेड्यूल जानने के लिए पूछें \"{a['code']} कब है\"।",
        f"उस दिन {a['title']} नहीं है।",
    ),
    "courseSchedule": lambda a: _say(
        f"{a['title']} ({a['code']}), {a['professor']} के साथ — {a['scope']} {a['count']} क्लास{'ें' if a['count'] > 1 else ''}: {a['timesTxt']}।",
        f"{a['title']} {a['count']} बार होता है: {a['speakTxt']}।",
    ),
    "countZero": lambda a: _say(
        f"{a['phrase']} कोई क्लास नहीं है{' — रविवार का दिन' if a['sunday'] else ''}। आराम कीजिए।",
        f"{a['phrase']} आपकी कोई क्लास नहीं है।",
    ),
    "count": lambda a: _say(
        f"{a['phrase']} आपकी {a['count']} क्लास{'ें' if a['count'] > 1 else ''} हैं, {a['start']} से {a['end']} तक।",
        f"{a['phrase']} आपकी {a['count']} क्लासें हैं, {a['start']} से शुरू।",
    ),
    "dayEmpty": lambda a: _say(
        f"{a['phrase']} कोई क्लास नहीं है{' — रविवार को आस्त्रा में छुट्टी रहती है' if a['sunday'] else ''}।"
        + (f" हफ्ता फिर शुरू होगा: {a['afterDay']} {a['afterTime']} पर {a['afterTitle']} से।" if a.get("afterTitle") else ""),
        f"{a['phrase']} कोई क्लास नहीं है।" + (f" अगली क्लास {a['afterDay']} को {a['afterTitle']}।" if a.get("afterTitle") else ""),
    ),
    "day": lambda a: _say(
        (f"{a['phrase']} आपकी {a['count']} क्लासें हैं: {a['itemsTxt']}।" if a["relative"]
         else f"{a['dayName']} को {a['count']} क्लासें हैं: {a['itemsTxt']}।"),
        ((f"{a['phrase']} आपकी {a['count']} क्लासें हैं" if a["relative"] else f"{a['dayName']} को आपकी {a['count']} क्लासें हैं")
         + f"। {a['speakTxt']}{' — और ' + str(a['more']) + ' क्लासें स्क्रीन पर।' if a['more'] > 0 else ''}"),
    ),
    "todayEmpty": lambda: _say("आज कोई क्लास नहीं — आस्त्रा में खाली दिन। कल का प्लान पूछ लीजिए।", "आज कोई क्लास नहीं है।"),
    "week": lambda a: _say(
        f"पूरे हफ्ते की झलक, CSE सेमेस्टर 5, सेक्शन A: {a['parts']}। रविवार खाली है।",
        "आपके हफ्ते की झलक ये रही। आने वाली क्लासें स्क्रीन पर हैं।",
    ),
    "weekEmpty": lambda: _say("इस हफ्ते कोई क्लास नहीं।", "इस हफ्ते कोई क्लास नहीं।"),
    "sugg": _hi_sugg,
}


def pack_for(lang: str) -> dict:
    return HI if lang == "hi" else EN
