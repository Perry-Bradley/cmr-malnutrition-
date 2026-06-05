"""
Fix the generate_report.py file:
- Wrap the project title in \\" escaped quotes wherever it appears inside double-quoted strings.
"""
import re

path = r"c:\Users\USER\Desktop\All\data420\scripts\generate_report.py"

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

TITLE = 'Cameroon Malnutrition Atlas:'

fixed = []
i = 0
while i < len(lines):
    line = lines[i]

    # Pattern: "...text "PROJECT TITLE...  -- the inner " breaks the string.
    # Strategy: replace the bare " before the title and " after 'Hotspots' with \'
    # We search for:  entitled "Cameroon  ->  entitled \\"Cameroon
    # and:            Hotspots"            ->  Hotspots\\"
    if TITLE in line:
        # Replace the opening bare quote before title
        line = line.replace('entitled "Cameroon', "entitled \\'Cameroon")
        line = line.replace('entitled "Cameroon', "entitled \\'Cameroon")
        # Same for  'entitled "Cameroon  (already done)
        fixed.append(line)
    else:
        fixed.append(line)
    i += 1

content = "".join(fixed)

# More targeted: fix the two problematic multi-line string literals
# Certification para
OLD_CERT = (
    '     "This is to certify that this project entitled "Cameroon Malnutrition Atlas: "\n'
    '     "A Data Mining Approach to Predicting and Mapping Child Stunting Hotspots" "\n'
)
NEW_CERT = (
    "     'This is to certify that this project entitled \"Cameroon Malnutrition Atlas: "
    "A Data Mining Approach to Predicting and Mapping Child Stunting Hotspots\" '\n"
    "     'has been carried out by SEPO PERRY-BRADLEY DINGA (CT23A145) of the '\n"
)

# Attestation para
OLD_ATT = (
    '     "I hereby declare that this project, entitled "Cameroon Malnutrition Atlas: "\n'
    '     "A Data Mining Approach to Predicting and Mapping Child Stunting Hotspots", "\n'
)
NEW_ATT = (
    "     'I hereby declare that this project, entitled \"Cameroon Malnutrition Atlas: "
    "A Data Mining Approach to Predicting and Mapping Child Stunting Hotspots\", '\n"
    "     'is the result of my own original work and investigation, except where otherwise '\n"
)

# Also fix title page title string
OLD_TITLE_STR = (
    '    "CAMEROON MALNUTRITION ATLAS:\\n"\n'
    '    "A DATA MINING APPROACH TO PREDICTING\\n"\n'
    '    "AND MAPPING CHILD STUNTING HOTSPOTS"\n'
)

# Let's do a clean regex replace for ALL occurrences of unescaped " before/after title
# Just rewrite the whole block directly

import re

# Replace:  "...entitled "Cameroon  ->  "...entitled \\"Cameroon
content = re.sub(r'entitled "Cameroon', 'entitled \\\\"Cameroon', content)
# Replace:  Hotspots" "  ->  Hotspots\\" "
content = re.sub(r'Hotspots" "', 'Hotspots\\\\" "', content)
# Replace:  Hotspots\", "  ->  Hotspots\\\"", "  (attestation comma)
content = re.sub(r'Hotspots", "', 'Hotspots\\\\",  "', content)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

# Verify by compiling
import py_compile
try:
    py_compile.compile(path, doraise=True)
    print("Syntax OK!")
except py_compile.PyCompileError as e:
    print(f"Syntax error: {e}")
