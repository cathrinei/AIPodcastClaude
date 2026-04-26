import csv, re, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('AI_KI_Podcasts.csv', encoding='utf-8') as f:
    rows = list(csv.reader(f))

data_rows = rows[1:]

def js_str(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')

lines = []
for r in data_rows:
    while len(r) < 11:
        r.append('')
    cells = ','.join(f'"{js_str(c)}"' for c in r[:11])
    lines.append(f'  [{cells}]')

new_block = 'const data = [\n' + ',\n'.join(lines) + '\n];'

with open('AI_KI_Podcasts.html', encoding='utf-8') as f:
    html = f.read()

new_html, count = re.subn(
    r'const data = \[[\s\S]*?\];',
    new_block,
    html,
    count=1
)

if count == 0:
    print('ERROR: data array not found in HTML')
    sys.exit(1)

with open('AI_KI_Podcasts.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f'OK: replaced data array with {len(data_rows)} rows')
