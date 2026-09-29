"""Generic, safe next-step checklists (pure, no I/O).

No legal claims, no outcomes, no certainty. Items only remind the reader to
keep papers, note the deadline, and contact the office named in the notice.
"""
from __future__ import annotations

_CHECKLISTS: dict[str, dict[str, list[str]]] = {
    "property_tax_notice": {
        "en": [
            "Keep the notice and any payment receipts together safely.",
            "Note the deadline and amount written in the notice.",
            "Visit or contact the issuing office named in the notice.",
            "Carry an ID proof when you visit the office.",
            "Do not ignore the notice.",
        ],
        "hi": [
            "नोटिस और भुगतान की रसीदें संभालकर एक साथ रखें।",
            "नोटिस में लिखी अंतिम तारीख और रकम नोट कर लें।",
            "नोटिस में लिखे कार्यालय से संपर्क करें या वहां जाएं।",
            "कार्यालय जाते समय पहचान पत्र साथ रखें।",
            "इस नोटिस को नजरअंदाज न करें।",
        ],
        "mr": [
            "नोटीस आणि भरल्याच्या पावत्या जपून एकत्र ठेवा.",
            "नोटिशीत लिहिलेली अंतिम तारीख आणि रक्कम नोंद करून घ्या.",
            "नोटिशीत लिहिलेल्या कार्यालयाशी संपर्क साधा किंवा तिथे जा.",
            "कार्यालयात जाताना ओळखपत्र सोबत ठेवा.",
            "या नोटिशीकडे दुर्लक्ष करू नका.",
        ],
    },
    "traffic_challan_summons": {
        "en": [
            "Keep the challan or summons paper safely.",
            "Note the court date and place written in the notice.",
            "Visit or contact the office or court named in the notice.",
            "Carry an ID proof and your vehicle papers.",
            "Do not ignore the notice.",
        ],
        "hi": [
            "चालान या समन का कागज संभालकर रखें।",
            "नोटिस में लिखी अदालत की तारीख और जगह नोट कर लें।",
            "नोटिस में लिखे कार्यालय या अदालत से संपर्क करें।",
            "पहचान पत्र और वाहन के कागजात साथ रखें।",
            "इस नोटिस को नजरअंदाज न करें।",
        ],
        "mr": [
            "चलन किंवा समन्सचा कागद जपून ठेवा.",
            "नोटिशीत लिहिलेली कोर्टाची तारीख आणि ठिकाण नोंद करून घ्या.",
            "नोटिशीत लिहिलेल्या कार्यालयाशी किंवा कोर्टाशी संपर्क साधा.",
            "ओळखपत्र आणि वाहनाची कागदपत्रे सोबत ठेवा.",
            "या नोटिशीकडे दुर्लक्ष करू नका.",
        ],
    },
    "bank_recovery_notice": {
        "en": [
            "Keep the notice and your loan papers together safely.",
            "Note the deadline written in the notice.",
            "Visit or contact the bank or office named in the notice.",
            "Carry an ID proof when you visit.",
            "Do not ignore the notice.",
        ],
        "hi": [
            "नोटिस और लोन के कागजात संभालकर एक साथ रखें।",
            "नोटिस में लिखी अंतिम तारीख नोट कर लें।",
            "नोटिस में लिखे बैंक या कार्यालय से संपर्क करें।",
            "जाते समय पहचान पत्र साथ रखें।",
            "इस नोटिस को नजरअंदाज न करें।",
        ],
        "mr": [
            "नोटीस आणि कर्जाची कागदपत्रे जपून एकत्र ठेवा.",
            "नोटिशीत लिहिलेली अंतिम तारीख नोंद करून घ्या.",
            "नोटिशीत लिहिलेल्या बँकेशी किंवा कार्यालयाशी संपर्क साधा.",
            "जाताना ओळखपत्र सोबत ठेवा.",
            "या नोटिशीकडे दुर्लक्ष करू नका.",
        ],
    },
}

_GENERIC: dict[str, list[str]] = {
    "en": [
        "Keep the notice safely.",
        "Note the deadline written in the notice.",
        "Visit or contact the office named in the notice.",
        "Carry an ID proof when you visit.",
    ],
    "hi": [
        "नोटिस संभालकर रखें।",
        "नोटिस में लिखी अंतिम तारीख नोट कर लें।",
        "नोटिस में लिखे कार्यालय से संपर्क करें।",
        "जाते समय पहचान पत्र साथ रखें।",
    ],
    "mr": [
        "नोटीस जपून ठेवा.",
        "नोटिशीत लिहिलेली अंतिम तारीख नोंद करून घ्या.",
        "नोटिशीत लिहिलेल्या कार्यालयाशी संपर्क साधा.",
        "जाताना ओळखपत्र सोबत ठेवा.",
    ],
}


def checklist_for(document_type: str, lang: str) -> list[str]:
    """4-6 generic, safe items for the type in en/hi/mr (hi fallback)."""
    language = lang if lang in ("en", "hi", "mr") else "hi"
    per_type = _CHECKLISTS.get(document_type)
    if per_type:
        items = per_type.get(language, per_type["hi"])
    else:
        items = _GENERIC.get(language, _GENERIC["hi"])
    return list(items)
