import re

THRESHOLD = 260
fillers = []
with open("log.txt") as f:
    for line in f:
        m = re.match(r"\s*(\d+)\s+(.*\S)\s*$", line)
        if not m:
            continue
        count, phrase = int(m.group(1)), m.group(2)
        if count >= THRESHOLD:
            fillers.append(phrase)

print("FILLER_PREFIXES = (")
for ph in fillers:
    print(f"    {ph!r},")
print(")")
