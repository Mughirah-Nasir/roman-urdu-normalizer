"""
Roman Urdu lexicon and variant dictionary.

Three layers of data live here, in priority order:

1. VARIANT_MAP — exact spellings (especially SMS shorthand like "bht", "nhi",
   "kch") that map directly to a canonical form. These are non-negotiable;
   the phonetic algorithm cannot reach them because they drop too many vowels.
   Lookup is O(1) and runs first.

2. CANONICAL_LEXICON — the set of canonical Roman Urdu words we recognize.
   The phonetic key algorithm builds an index over this set; any input word
   whose phonetic key matches a lexicon word resolves to that word.
   Organized by part of speech for maintainability, then unioned at the end.

3. HOMOGRAPH_GROUPS — pairs of canonical words that share a phonetic key
   but mean different things. The normalizer never silently picks one; it
   flags `ambiguous: true` and returns all candidates.

If a word is neither in VARIANT_MAP nor reachable via phonetic key, the
normalizer flags it as "unknown" rather than silently guessing — silent
guessing is how normalizers poison downstream NLP.

The lexicon below was curated by a native Urdu speaker (Mughirah Nasir).
It targets Pakistani Roman Urdu as actually used on WhatsApp / Twitter /
SMS, not formal/literary Urdu.
"""

# ==========================================================================
# Layer 1: exact-match variant map
# ==========================================================================
# Keys: as people actually type. Values: canonical form.
# This map handles SMS shorthand the phonetic algorithm cannot reach because
# it drops too many vowels (e.g. "bht" has only consonants). Anything that
# the phonetic layer CAN reach should live in the lexicon, not here.

VARIANT_MAP = {
    # --- negation / affirmation ---
    "nhi": "nahi", "nahin": "nahi", "nai": "nahi", "nahe": "nahi",
    "haan": "haan", "han": "haan", "hn": "haan", "haa": "haan",
    "ji": "ji", "jee": "ji",

    # --- quantity / intensifiers ---
    "bht": "bahut", "bhot": "bahut", "bohat": "bahut", "bohot": "bahut", "buhat": "bahut",
    "thora": "thora", "thorra": "thora", "thoda": "thora", "thodi": "thori",
    "zyada": "zyada", "zayada": "zyada", "zada": "zyada", "ziada": "zyada",
    "kam": "kam", "kum": "kam",
    "sirf": "sirf", "srf": "sirf",
    "bilkul": "bilkul", "blkl": "bilkul", "bilkull": "bilkul",
    "zaroor": "zaroor", "zarur": "zaroor", "zroor": "zaroor",
    "shayad": "shayad", "shyd": "shayad", "shaayad": "shayad",

    # --- interrogatives ---
    "kya": "kya", "kia": "kya", "kyaa": "kya", "kiya": "kya",
    "kyun": "kyun", "kiun": "kyun", "kyon": "kyun", "kyu": "kyun", "q": "kyun",
    "kahan": "kahan", "kahaan": "kahan", "khn": "kahan",
    "kab": "kab", "kb": "kab",
    "kese": "kaise", "kaisay": "kaise", "kaise": "kaise", "ksay": "kaise",
    "kon": "kaun", "koun": "kaun", "kaun": "kaun",
    "kisko": "kisko", "ksko": "kisko",
    "kiska": "kiska", "kska": "kiska",
    "kiski": "kiski", "kski": "kiski",
    "kitna": "kitna", "ktna": "kitna",
    "kitni": "kitni", "ktni": "kitni",
    "kitne": "kitne", "ktne": "kitne",

    # --- pronouns ---
    "mein": "main", "mai": "main", "me": "main", "mn": "main",
    "tum": "tum", "tm": "tum", "tu": "tum",
    "ap": "aap", "aap": "aap", "p": "aap",
    "hum": "hum", "hm": "hum", "hmm": "hum",
    "wo": "wo", "woh": "wo", "vo": "wo",
    "ye": "ye", "yeh": "ye",
    "mera": "mera", "mra": "mera",
    "meri": "meri", "mri": "meri",
    "mere": "mere", "mre": "mere",
    "tera": "tera", "tra": "tera",
    "teri": "teri", "tri": "teri",
    "tere": "tere", "tre": "tere",
    "tumhara": "tumhara", "tmhara": "tumhara",
    "tumhari": "tumhari", "tmhari": "tumhari",
    "tumhare": "tumhare", "tmhare": "tumhare",
    "aapka": "aapka", "apka": "aapka",
    "aapki": "aapki", "apki": "aapki",
    "aapke": "aapke", "apke": "aapke",
    "humara": "humara", "hmara": "humara",
    "humari": "humari", "hmari": "humari",
    "humare": "humare", "hmare": "humare",
    "uska": "uska", "uski": "uski", "uske": "uske",
    "iska": "iska", "iski": "iski", "iske": "iske",
    "sab": "sab", "sb": "sab",
    "kuch": "kuch", "kch": "kuch", "kuchh": "kuch",
    "koi": "koi", "ki": "koi",  # context-dependent; phonetic layer handles "ki" otherwise
    "har": "har",
    "apna": "apna", "apni": "apni", "apne": "apne",

    # --- be / have / aux ---
    "hai": "hai", "h": "hai", "hy": "hai", "hi": "hai",
    "hain": "hain", "hen": "hain", "hn": "hain",
    "ho": "ho",
    "hun": "hun", "hoon": "hun", "hu": "hun",
    "tha": "tha", "tha": "tha", "th": "tha",
    "thi": "thi",
    "the": "the", "thay": "the",
    "hota": "hota", "hoti": "hoti", "hote": "hote",
    "hoga": "hoga", "hogi": "hogi", "honge": "honge",

    # --- common verb conjugations (SMS-dropped vowels) ---
    "kr": "kar", "krna": "karna", "krta": "karta", "krti": "karti", "krte": "karte",
    "kr rha": "kar raha", "kr rhi": "kar rahi", "kr rhe": "kar rahe",
    "rha": "raha", "rhi": "rahi", "rhe": "rahe",
    "gya": "gaya", "gyi": "gayi", "gye": "gaye",
    "aaya": "aaya", "ayi": "ayi", "aye": "aye",
    "khaya": "khaya", "khayi": "khayi", "khaye": "khaye",
    "piya": "piya", "piyi": "piyi",
    "dekh": "dekh", "dkh": "dekh",
    "dkha": "dekha", "dekha": "dekha", "dekhi": "dekhi",
    "sun": "sun", "sn": "sun", "suna": "suna", "suni": "suni",
    "bol": "bol", "bola": "bola", "boli": "boli",
    "keh": "keh", "kha": "keh",  # informal/colloquial
    "soch": "soch", "socha": "socha", "sochi": "sochi",
    "samjh": "samajh", "smjh": "samajh", "samjha": "samjha", "samjhi": "samjhi",

    # --- greetings / courtesy ---
    "salam": "salam", "aslam": "salam", "slam": "salam", "asalam": "salam",
    "asalamualikum": "asalam-alaikum",
    "walaikum": "walaikum",
    "shukria": "shukriya", "shukrya": "shukriya", "shukar": "shukriya", "thx": "shukriya",
    "mehrbani": "mehrbani", "meherbani": "mehrbani", "mhrbni": "mehrbani",
    "maaf": "maaf", "maf": "maaf",
    "khuda hafiz": "khuda-hafiz", "allah hafiz": "allah-hafiz",
    "mubarak": "mubarak", "mbrk": "mubarak",

    # --- pleasantries / discourse ---
    "acha": "accha", "achha": "accha", "achi": "acchi", "achhi": "acchi",
    "achay": "acche", "achhe": "acche",
    "theek": "theek", "tk": "theek", "thk": "theek", "thik": "theek",
    "ok": "theek", "okay": "theek",
    "matlab": "matlab", "mtlb": "matlab",
    "yani": "yani", "yaani": "yani",
    "phir": "phir", "fir": "phir", "phr": "phir",
    "lekin": "lekin", "lkn": "lekin", "lkin": "lekin",
    "magar": "magar", "mgr": "magar",
    "agar": "agar", "agr": "agar",
    "warna": "warna", "wrna": "warna",
    "kyunki": "kyunki", "kynki": "kyunki", "kyuke": "kyunki",
    "is liye": "is-liye", "isliye": "is-liye",

    # --- common nouns (high-frequency, SMS forms) ---
    "yr": "yaar", "yaar": "yaar",
    "dst": "dost", "dost": "dost",
    "bhai": "bhai", "bhi": "bhi",  # "bhi" = also; bhai = brother (homograph!)
    "behan": "behan", "behn": "behan", "bhn": "behan",
    "ammi": "ammi", "ami": "ammi",
    "abu": "abu", "abbu": "abu", "abba": "abu",
    "ghar": "ghar", "ghr": "ghar",
    "kaam": "kaam", "kam": "kaam", "kaaam": "kaam",
    "paani": "paani", "pani": "paani", "pny": "paani",
    "khana": "khana", "khna": "khana",
    "chai": "chai", "chae": "chai",
    "kitab": "kitab", "ktab": "kitab",
    "school": "school", "skool": "school", "skul": "school",
    "college": "college", "klg": "college",
    "office": "office", "ofc": "office",

    # --- time ---
    "aaj": "aaj", "aj": "aaj",
    "kal": "kal", "kl": "kal",
    "parsoon": "parsoon", "prson": "parsoon",
    "abhi": "abhi", "abi": "abhi", "abh": "abhi",
    "ab": "ab",
    "phir": "phir",
    "subah": "subah", "sbh": "subah", "subha": "subah",
    "shaam": "shaam", "sham": "shaam",
    "raat": "raat", "rat": "raat",
    "dopahar": "dopahar", "dophar": "dopahar",

    # --- days (Roman Urdu names) ---
    "pir": "pir", "peer": "pir",
    "mangal": "mangal", "mngl": "mangal",
    "budh": "budh",
    "jumeraat": "jumeraat", "jmrat": "jumeraat",
    "jumma": "jumma", "juma": "jumma",
    "hafta": "hafta", "hfta": "hafta",
    "itwar": "itwar", "itvar": "itwar",

    # --- numbers ---
    "ek": "ek", "1": "ek",
    "do": "do", "2": "do",
    "teen": "teen", "tin": "teen", "3": "teen",
    "char": "char", "chr": "char", "4": "char",
    "panch": "panch", "paanch": "panch", "5": "panch",
    "che": "che", "chhe": "che", "chay": "che", "6": "che",
    "saat": "saat", "sat": "saat", "7": "saat",
    "aath": "aath", "ath": "aath", "8": "aath",
    "nau": "nau", "9": "nau",
    "dus": "dus", "das": "dus", "10": "dus",
}


# ==========================================================================
# Layer 2: canonical lexicon (organized by part of speech)
# ==========================================================================
# Each set below is a category of canonical Roman Urdu words we recognize.
# The phonetic algorithm indexes over the union — so adding a word here
# automatically catches its phonetic misspellings.

_PRONOUNS = {
    # Personal — 1st person
    "main", "hum",
    # Personal — 2nd person (informal -> formal)
    "tu", "tum", "aap",
    # Personal — 3rd person
    "wo", "ye", "in", "un",
    # Possessive
    "mera", "meri", "mere",
    "tera", "teri", "tere",
    "tumhara", "tumhari", "tumhare",
    "aapka", "aapki", "aapke",
    "humara", "humari", "humare",
    "uska", "uski", "uske",
    "iska", "iski", "iske",
    # Indefinite
    "kisi", "koi", "kuch", "sab", "har", "kahin", "kabhi",
    # Reflexive
    "apna", "apni", "apne", "khud",
    # Demonstrative
    "yahi", "wahi", "yehi", "wohi",
}

_INTERROGATIVES = {
    "kya", "kyun", "kahan", "kab", "kaise", "kaun",
    "kitna", "kitni", "kitne",
    "kisko", "kiska", "kiski", "kiske",
    "kidhar",
}

_VERBS_INF = {
    # Action — basic
    "karna", "jana", "aana", "lana", "le-jana",
    "khana", "peena", "sona", "uthna", "baithna", "khada-hona",
    "chalna", "daurna", "khelna",
    # Speech / sense
    "bolna", "kehna", "sunna", "dekhna", "padhna", "likhna",
    "samajhna", "sochna", "yaad-karna", "bhulna",
    # Emotion
    "rona", "hansna", "darna", "ghussa-karna",
    "pyaar-karna", "nafrat-karna", "yaqeen-karna",
    # Social
    "milna", "milana", "dena", "lena", "denalena",
    "maafi-mangna", "shukriya-kehna", "salam-karna",
    # Movement / state
    "rakhna", "uthana", "girna", "girana",
    "khulna", "kholna", "bandh-karna", "band-hona",
    "shuru-karna", "khatam-karna",
    # Mental
    "banaana", "banna", "todna", "tutna",
    "dena", "milna", "kharidna", "bechna",
}

_VERBS_CONJ = {
    # karna conjugations
    "karta", "karti", "karte", "kiya", "ki", "karunga", "karoge", "karenge",
    "karega", "karegi", "karein", "karo", "karoon",
    # jana
    "jata", "jati", "jate", "gaya", "gayi", "gaye",
    "jaunga", "jaungi", "jaoge", "jayenge", "jao", "jaayega",
    # aana
    "ata", "ati", "ate", "aya", "ayi", "aye",
    "aunga", "aungi", "aoge", "ayenge",
    # khana
    "khata", "khati", "khate", "khaya", "khayi", "khaye",
    "khaunga", "khaoge", "khayega",
    # peena
    "pita", "piti", "pite", "piya", "piye",
    # sunna
    "sunta", "sunti", "sunte", "suna", "suni", "sune", "sunna",
    # bolna
    "bolta", "bolti", "bolte", "bola", "boli", "bole",
    # kehna
    "kehta", "kehti", "kehte", "kaha", "kahi", "kahe",
    # dekhna
    "dekhta", "dekhti", "dekhte", "dekha", "dekhi", "dekhe",
    # samajhna
    "samajhta", "samajhti", "samajhte", "samjha", "samjhi", "samjhe",
    # sochna
    "sochta", "sochti", "sochte", "socha", "sochi", "soche",
    # dena
    "deta", "deti", "dete", "diya", "di", "diye",
    # lena
    "leta", "leti", "lete", "liya", "li", "liye",
    # raha (progressive aux)
    "raha", "rahi", "rahe",
}

_BE_HAVE = {
    "hai", "hain", "ho", "hun",
    "tha", "thi", "the",
    "hota", "hoti", "hote",
    "hoga", "hogi", "honge",
    "hokar", "hoke",
}

_NOUNS = {
    # People / family
    "dost", "yaar", "bhai", "behan", "ammi", "abu", "papa", "mummy",
    "walid", "walida", "walidain", "bachay", "bachi", "beta", "beti",
    "biwi", "shauhar", "miyan", "mehman", "rishtedar",
    "dada", "dadi", "nana", "nani", "chacha", "chachi",
    "mama", "mami", "phupha", "phuphi", "khala", "khalu",
    "dushman", "ajnabi", "hamsaya",

    # Places
    "ghar", "kamra", "ghar-wale", "bazaar", "dukan",
    "school", "college", "university", "madrassa",
    "masjid", "mandir", "girja", "hospital", "daftar", "office",
    "mulk", "shehr", "gaon", "deh",
    "sarak", "gali", "mohalla", "ilaqa", "duniya", "jagah",
    "rasta", "raasta", "ground", "park",

    # Time
    "din", "raat", "subah", "shaam", "dopahar", "waqt",
    "ghanta", "minute", "second", "lamha", "saal", "mahina", "hafta",
    "saalgirah", "tareekh",

    # Food / drink
    "khana", "chai", "paani", "doodh", "roti", "naan",
    "sabzi", "salan", "chawal", "dal", "gosht", "machli", "anda",
    "mithai", "biryani", "namak", "mirch", "masala", "ghee",
    "makhan", "dahi", "pakora", "samosa", "paratha", "halwa",

    # Body
    "sar", "aankh", "naak", "kaan", "munh", "dant",
    "baal", "haath", "paaon", "ungli", "anguthi",
    "dil", "jigar", "peit", "gardan", "kandha", "kamar",
    "ghutna", "kalai", "honth",

    # Nature
    "phool", "darakht", "patta", "ghaas",
    "hawa", "aag", "mitti", "samandar", "pahar", "nadi",
    "jangal", "saharaa", "suraj", "chand", "sitara", "asmaan",
    "baadal", "baarish", "barf", "tofaan", "garmi", "sardi",

    # Animals
    "kutta", "billi", "gaay", "bakri", "ghora", "sher",
    "chuha", "machhli", "parinda", "kabootar", "tota", "mor",
    "haathi", "oont", "bhediya", "lomri", "bandar",

    # Objects
    "kitab", "qalam", "pencil", "kursi", "mez", "darwaza",
    "gaadi", "mobile", "phone", "computer", "ghari",
    "batti", "pankha", "ac", "fridge", "tv",
    "jhoola", "jutta", "kapra", "libaas", "kameez", "shalwar",
    "dupatta", "topi", "chadar", "kambal", "takiya", "palang",
    "katora", "plate", "glass", "chamcha", "kanta", "chaaku",

    # Concepts / abstract
    "zindagi", "maut", "khushi", "gham", "pyaar", "mohabbat",
    "nafrat", "ghussa", "khauf", "umeed", "hosla",
    "imaan", "sach", "jhoot", "fikar", "salah", "raah",
    "manzil", "safar", "kahaani", "khwaab",
}

_ADJECTIVES = {
    # Quality
    "accha", "acchi", "acche",
    "bura", "buri", "bure",
    "naya", "nayi", "naye",
    "purana", "purani", "purane",
    "bara", "bari", "bare",
    "chota", "choti", "chote",
    "lamba", "lambi", "lambe",
    "mota", "moti", "mote",
    "patla", "patli", "patle",
    # State
    "khush", "udaas", "naraz",
    "pareshan", "thaka", "taaza", "garam", "thanda",
    "saaf", "ganda", "khoobsurat", "badsurat",
    # Character
    "mehnati", "sust", "hoshyar", "samajhdar",
    "bewakuf", "pagal", "dewana",
    "ameer", "ghareeb", "taqatwar", "kamzor",
    "tez", "dheema", "tezz",
    # Judgement
    "sahi", "ghalat", "theek", "kharaab",
    "behtar", "behtareen", "kamaal", "zabardast",
    "aam", "khaas", "mushkil", "asaan",
    # Quantity / scope
    "puri", "poora", "poore", "aadha", "aadhi", "aadhe",
    "sara", "saari", "saare",
    "khali", "bhara",
}

_ADVERBS = {
    # Time
    "abhi", "abh", "ab", "kabhi", "hamesha",
    "phir", "baad", "pehle", "fauran",
    # Place
    "yahan", "wahan", "idhar", "udhar",
    "kahin", "kahin-bhi", "har-jagah", "andar", "bahar",
    "uppar", "neeche", "saamne", "peeche",
    # Manner
    "achi-tarah", "buri-tarah", "asaani-se", "mushkil-se",
    "jaldi", "dheere", "ahista",
    # Degree
    "bohat", "thora", "kam", "zyada", "sirf", "bhi", "hi", "to",
    "bilkul", "shayad", "zaroor",
}

_CONJUNCTIONS = {
    "aur", "ya", "lekin", "magar", "agar", "warna",
    "kyunki", "is-liye", "jab", "tak",
    "ke", "ki", "ka", "se", "ko", "mein", "par", "tak",
    "to", "phir", "balke", "ya-phir",
    "jab-bhi", "agar-bhi", "lekin-phir",
}

_GREETINGS = {
    "salam", "asalam-alaikum", "walaikum-salam",
    "khuda-hafiz", "allah-hafiz",
    "subah-bakhair", "shab-bakhair",
    "shukriya", "mehrbani", "maaf",
    "mubarak", "khush-amdeed",
}

_TIME_WORDS = {
    "aaj", "kal", "parsoon", "abhi", "ab",
    "baad", "pehle", "kabhi",
    "subah", "dopahar", "shaam", "raat", "aadhi-raat",
    "dopahari", "saaljaisi",
}

_DAYS = {
    # Roman Urdu day names
    "pir", "mangal", "budh", "jumeraat", "jumma", "hafta", "itwar",
    # English variants in common use (kept as canonical for code-switching)
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
}

_NUMBERS = {
    # 1-20
    "ek", "do", "teen", "char", "panch", "che", "saat", "aath", "nau", "dus",
    "gyarah", "barah", "terah", "chaudah", "pandrah",
    "solah", "satrah", "atharah", "unnees", "bees",
    # tens
    "tees", "chalees", "pachas", "saath", "sattar", "assi", "nabbe", "soo",
    # large
    "hazaar", "lakh", "crore", "arab",
    # ordinals
    "pehla", "doosra", "teesra", "chautha", "panchwa",
}

# --- homograph members (must be canonical) -------------------------------
# These are added to the lexicon so the phonetic index includes them.
_HOMOGRAPH_MEMBERS = {
    "kaha", "kahan",      # said vs where
    "jana", "janna",      # to go vs to know
    "sona", "sonna",      # to sleep vs gold (rare)
    "mara", "maara",      # died vs hit
    "baal", "bal",        # hair vs strength
    "sher", "sheer",      # lion vs poem
}


# Union of every canonical word, by category
CANONICAL_LEXICON = (
    _PRONOUNS | _INTERROGATIVES | _VERBS_INF | _VERBS_CONJ | _BE_HAVE |
    _NOUNS | _ADJECTIVES | _ADVERBS | _CONJUNCTIONS | _GREETINGS |
    _TIME_WORDS | _DAYS | _NUMBERS | _HOMOGRAPH_MEMBERS
)


# Per-category index (exposed for the /stats endpoint and for debugging).
LEXICON_BY_CATEGORY = {
    "pronouns": _PRONOUNS,
    "interrogatives": _INTERROGATIVES,
    "verbs_infinitive": _VERBS_INF,
    "verbs_conjugated": _VERBS_CONJ,
    "be_have_aux": _BE_HAVE,
    "nouns": _NOUNS,
    "adjectives": _ADJECTIVES,
    "adverbs": _ADVERBS,
    "conjunctions": _CONJUNCTIONS,
    "greetings": _GREETINGS,
    "time_words": _TIME_WORDS,
    "days": _DAYS,
    "numbers": _NUMBERS,
    "homograph_members": _HOMOGRAPH_MEMBERS,
}


# ==========================================================================
# Layer 3: homograph guard
# ==========================================================================
# Phonetic keys that collide between distinct words. The normalizer marks
# these as ambiguous rather than silently picking one.
# Registered: 2026-05-23 — kaha/kahan caught during live demo; rest were
# audited from a sweep through the canonical lexicon at v0.4.

HOMOGRAPH_GROUPS = [
    {"kaha", "kahan"},      # he/she said vs where
    {"jana", "janna"},      # to go vs to know
    {"sona", "sonna"},      # to sleep vs gold (rare in Roman Urdu)
    {"mara", "maara"},      # died vs hit / struck
    {"baal", "bal"},        # hair vs strength
    {"sher", "sheer"},      # lion vs poem (literary form)
]


def all_canonical_words() -> set:
    """Union of every canonical spelling we recognize (map values + lexicon)."""
    return set(VARIANT_MAP.values()) | CANONICAL_LEXICON


def lexicon_stats() -> dict:
    """Diagnostic counts — surfaced by the /stats endpoint."""
    return {
        "variant_map_entries": len(VARIANT_MAP),
        "canonical_total": len(CANONICAL_LEXICON),
        "by_category": {cat: len(words) for cat, words in LEXICON_BY_CATEGORY.items()},
        "homograph_groups": len(HOMOGRAPH_GROUPS),
        "total_recognized_spellings": len(set(VARIANT_MAP.keys()) | CANONICAL_LEXICON),
    }
