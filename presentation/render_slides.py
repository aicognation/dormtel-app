import subprocess
import os

output_dir = r"c:\Users\Emil V. Capino\DATA\QWork\Q101\DORMTEL\dormtel-app\presentation"
html_source = os.path.join(output_dir, "slides.html")

edge_paths = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

edge = None
for p in edge_paths:
    if os.path.exists(p):
        edge = p
        break

if not edge:
    print("ERROR: Microsoft Edge not found!")
    exit(1)

print("Using Edge: " + edge)

with open(html_source, 'r', encoding='utf-8') as f:
    html_content = f.read()

for i in range(1, 11):
    slide_id = "slide-" + str(i).zfill(2)
    output_png = os.path.join(output_dir, slide_id + ".png")
    temp_html = os.path.join(output_dir, "_temp_" + slide_id + ".html")

    hide_css = "\n<style>\n.slide { display: none !important; }\n#" + slide_id + " { display: flex !important; }\n</style>\n"
    temp_content = html_content.replace('</head>', hide_css + '</head>')

    with open(temp_html, 'w', encoding='utf-8') as f:
        f.write(temp_content)

    url = "file:///" + temp_html.replace("\\", "/")

    cmd = [
        edge,
        "--headless",
        "--disable-gpu",
        "--screenshot=" + output_png,
        "--window-size=1920,1080",
        "--hide-scrollbars",
        "--device-scale-factor=2",
        url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    os.remove(temp_html)

    if os.path.exists(output_png):
        size = os.path.getsize(output_png)
        status = "OK" if size > 10000 else "SMALL"
        print("  " + slide_id + ".png - " + str(size) + " bytes " + status)
    else:
        print("  " + slide_id + ".png - FAILED")

print("\nDone!")
