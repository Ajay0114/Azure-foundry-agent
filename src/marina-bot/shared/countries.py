"""Country names, so "I live in the UK" becomes "United Kingdom" and "blah" is not accepted as a country.

Replaces Kore's `country` entity type. The list is the UN member states plus the places customers actually live
(territories and dependencies); `ALIASES` holds the common short forms.
"""

import re

COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Aruba",
    "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize",
    "Benin", "Bermuda", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria",
    "Burkina Faso", "Burundi", "Cambodia", "Cameroon", "Canada", "Cape Verde", "Cayman Islands", "Central African Republic",
    "Chad", "Chile", "China", "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Curacao", "Cyprus",
    "Czech Republic", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador",
    "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "French Polynesia",
    "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Gibraltar", "Greece", "Greenland", "Grenada", "Guadeloupe", "Guam",
    "Guatemala", "Guernsey", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hong Kong", "Hungary", "Iceland",
    "India", "Indonesia", "Iran", "Iraq", "Ireland", "Isle of Man", "Israel", "Italy", "Ivory Coast", "Jamaica", "Japan",
    "Jersey", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kosovo", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon",
    "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Macau", "Madagascar", "Malawi", "Malaysia",
    "Maldives", "Mali", "Malta", "Marshall Islands", "Martinique", "Mauritania", "Mauritius", "Mexico", "Micronesia",
    "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal",
    "Netherlands", "New Caledonia", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia",
    "Norway", "Oman", "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines",
    "Poland", "Portugal", "Puerto Rico", "Qatar", "Reunion", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis",
    "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia",
    "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Sint Maarten", "Slovakia", "Slovenia",
    "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname",
    "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga",
    "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Turks and Caicos Islands", "Tuvalu", "Uganda", "Ukraine",
    "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "US Virgin Islands", "Uzbekistan", "Vanuatu",
    "Vatican City", "Venezuela", "Vietnam", "British Virgin Islands", "Yemen", "Zambia", "Zimbabwe",
]

# Kore's mapping plus the usual short forms. Keys are lower case.
ALIASES = {
    "us": "United States", "usa": "United States", "u.s.": "United States", "u.s.a.": "United States",
    "united states of america": "United States", "america": "United States", "the states": "United States",
    "uk": "United Kingdom", "u.k.": "United Kingdom", "britain": "United Kingdom", "great britain": "United Kingdom",
    "england": "United Kingdom", "scotland": "United Kingdom", "wales": "United Kingdom",
    "northern ireland": "United Kingdom", "uae": "United Arab Emirates", "dubai": "United Arab Emirates",
    "abu dhabi": "United Arab Emirates", "bharat": "India", "deutschland": "Germany", "holland": "Netherlands",
    "the netherlands": "Netherlands", "czechia": "Czech Republic", "the bahamas": "Bahamas", "cote d'ivoire": "Ivory Coast",
    "cabo verde": "Cape Verde", "burma": "Myanmar", "russian federation": "Russia", "south korea": "South Korea",
    "republic of korea": "South Korea", "korea": "South Korea", "viet nam": "Vietnam", "turkiye": "Turkey",
    "swaziland": "Eswatini", "east timor": "Timor-Leste", "macedonia": "North Macedonia", "curaçao": "Curacao",
    "réunion": "Reunion", "uk of great britain": "United Kingdom", "democratic republic of the congo": "Congo",
    "drc": "Congo", "pr": "Puerto Rico", "ksa": "Saudi Arabia", "nz": "New Zealand", "oz": "Australia",
}

_BY_NAME = {name.lower(): name for name in COUNTRIES} | ALIASES
_LONGEST_FIRST = sorted(_BY_NAME, key=len, reverse=True)
_ONLY_ON_THEIR_OWN = {"us", "pr", "oz", "nz", "drc", "ksa"}      # "send it to us" is not the United States


def parse_country(text: str) -> str | None:
    """The standard English name of the country the reply mentions, or None. Several different countries -> None."""
    cleaned = re.sub(r"[^\w\s'’-]", " ", (text or "").lower().replace(".", ""))
    cleaned = " ".join(cleaned.split())
    found: set[str] = set()
    remaining = f" {cleaned} "
    for key in _LONGEST_FIRST:
        needle = f" {key} "
        if needle in remaining and (key not in _ONLY_ON_THEIR_OWN or cleaned == key):
            found.add(_BY_NAME[key])
            remaining = remaining.replace(needle, " # ")           # "niger" must not match inside "nigeria"
    return found.pop() if len(found) == 1 else None
