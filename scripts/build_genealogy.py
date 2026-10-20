"""Build the static genealogy page from the researched people and relationships.
Run with Pillow installed: python3 scripts/build_genealogy.py
The website itself has no build or runtime dependencies.
"""
from pathlib import Path
from html import escape
from PIL import Image, ImageOps
import json
import textwrap

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'research/academic-genealogy'
PORTRAITS = ROOT / 'asset/genealogy/portraits'
DATA = json.loads((SOURCE / 'genealogy.json').read_text())
NODES = {n['id']: n for n in DATA['nodes']}
EDGES = DATA['edges']
RESTRICTED = {'ratcliffe', 'needham'}
PORTRAITS.mkdir(parents=True, exist_ok=True)

# Display crops use coordinates in the unchanged, optimized source portraits.
# The originals and uncropped WebP copies remain available in the repository.
FOCUS_BOXES = {
    'hossein': (8, 76, 169, 195), 'bonneau': (53, 8, 221, 255),
    'kleppmann': (75, 45, 143, 165), 'beresford': (104, 56, 143, 165),
    'stajano': (113, 70, 139, 160), 'tartaglia': (59, 15, 175, 202),
    'mersenne': (94, 52, 117, 135), 'sedgwick': (102, 15, 135, 156),
    'hopkins': (113, 25, 118, 136), 'whisson': (63, 43, 143, 165),
    'newton': (80, 0, 164, 189), 'roberval': (5, 57, 169, 195),
    'galileo': (78, 12, 164, 189), 'torricelli': (42, 11, 225, 260),
    'viviani': (42, 15, 212, 245), 'barrow': (48, 28, 211, 244),
    'smith': (83, 10, 180, 208), 'stokes': (32, 35, 168, 194),
    'rayleigh': (25, 24, 140, 162),
}

for ident, node in NODES.items():
    portrait = node['portrait']
    node['image'] = None
    if portrait['status'] == 'available' and ident not in RESTRICTED:
        source = (SOURCE / portrait['local_path']).resolve()
        output = PORTRAITS / (ident + '.webp')
        with Image.open(source) as image:
            image = ImageOps.exif_transpose(image).convert('RGB')
            image.thumbnail((320, 400), Image.Resampling.LANCZOS)
            image.save(output, 'WEBP', quality=84, method=6)
            width, height = image.size
        node['image'] = str(output.relative_to(ROOT))
        box = FOCUS_BOXES.get(ident)
        if box is None:
            # Default to a cover crop, slightly favouring the top of the image.
            crop_width = min(width, height * 52 / 60)
            crop_height = crop_width * 60 / 52
            box = ((width - crop_width) / 2, (height - crop_height) * .25, crop_width, crop_height)
        x, y, crop_width, crop_height = box
        assert 0 <= x < width and 0 <= y < height and x + crop_width <= width and y + crop_height <= height, ident
        node['crop_style'] = f'left:{-x / crop_width * 100:.3f}%;top:{-y / crop_height * 100:.3f}%;width:{width / crop_width * 100:.3f}%;height:{height / crop_height * 100:.3f}%'
        node['crop_viewbox'] = f'{x:g} {y:g} {crop_width:g} {crop_height:g}'
        node['image_size'] = (width, height)
    node['initials'] = ''.join(part[0] for part in node['label'].split() if part not in ['de', 'R.'])[:2]


def h(value):
    return escape(str(value), quote=True)


def portrait_credit(node):
    portrait = node['portrait']
    source = portrait.get('file_page') or portrait.get('source_page') or node['profile_url']
    credit = portrait.get('credit', 'Source portrait').replace('Unknown author Unknown author', 'Unknown author')
    license_name = portrait.get('license', '')
    license_url = portrait.get('license_url', '')
    return ' · '.join(str(part) for part in [credit, license_name, license_url, source, 'Resized WebP; display cropped'] if part)


def portrait_markup(node):
    if node['image']:
        return f'<span class="portrait-frame"><img src="{node["image"]}" alt="" width="52" height="60" loading="lazy" decoding="async" style="{node["crop_style"]}" title="{h(portrait_credit(node))}"></span>'
    return f'<span class="portrait-frame portrait-initials" aria-hidden="true">{h(node["initials"])}</span>'


def person_link(node):
    return f'<a class="person-card" href="{h(node["profile_url"])}" data-person="{node["id"]}">{portrait_markup(node)}<span class="person-name">{h(node["label"])}</span></a>'


# Compact ranks retain every person and every relationship in the researched DAG.
RANKS = {
    'tartaglia': (460, 0), 'ricci': (460, 1), 'galileo': (460, 2),
    'castelli': (460, 3), 'torricelli': (460, 4), 'viviani': (460, 5),
    'mersenne': (820, 3), 'roberval': (820, 4), 'barrow': (460, 6), 'pulleyn': (820, 6),
    'newton': (640, 7), 'cotes': (640, 8), 'smith': (640, 9), 'taylor': (640, 10), 'whisson': (640, 11),
    'postlethwaite': (180, 12), 'cranke': (460, 12), 'waring': (740, 12), 'bracken': (1020, 12),
    'jones': (320, 13), 'dawson': (880, 13), 'sedgwick': (600, 14), 'hopkins': (600, 15),
    'todhunter': (320, 16), 'routh': (320, 17), 'stokes': (880, 17), 'rayleigh': (600, 18),
    'thomson': (600, 19), 'rutherford': (880, 20), 'appleton': (600, 21), 'ratcliffe': (600, 22),
    'wilkes': (600, 23), 'wheeler': (600, 24), 'needham': (600, 25), 'ross': (600, 26),
    'bonneau': (320, 27), 'stajano': (880, 27), 'beresford': (880, 28), 'kleppmann': (880, 29), 'hossein': (600, 30),
}
CARD_WIDTH, CARD_HEIGHT = 220, 80
GRAPH_WIDTH, GRAPH_HEIGHT = 1200, 3280
COORDS = {ident: (x, 40 + rank * 104) for ident, (x, rank) in RANKS.items()}


def graph():
    output = [
        f'<svg class="family-tree" id="family-tree" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {GRAPH_WIDTH} {GRAPH_HEIGHT}" width="{GRAPH_WIDTH}" height="{GRAPH_HEIGHT}" aria-labelledby="graph-title graph-desc">',
        '<title id="graph-title">Academic genealogy of Hossein Hafezi</title>',
        '<desc id="graph-desc">All forty people. Lines run from earlier teachers and supervisors to their students. Dashed lines show historical teaching or mentorship; solid lines show supervision. Each person links directly to their webpage.</desc>',
        '<defs><marker id="graph-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10Z" fill="context-stroke"/></marker></defs>',
    ]
    for edge in EDGES:
        ax, ay = COORDS[edge['advisor']]
        bx, by = COORDS[edge['student']]
        # The visible portraits anchor the lines in the borderless layout.
        source_x, target_x = ax - 74, bx - 74
        start, end = ay + 74, by + 6
        if edge['advisor'] == 'galileo' and edge['student'] == 'viviani':
            side = ax - CARD_WIDTH / 2 - 36
            path = f'M{ax-CARD_WIDTH/2+6} {ay+CARD_HEIGHT/2} C{side} {ay+CARD_HEIGHT/2},{side} {by+CARD_HEIGHT/2},{bx-CARD_WIDTH/2+6} {by+CARD_HEIGHT/2}'
        elif edge['advisor'] == 'hopkins' and edge['student'] == 'routh':
            side = bx - CARD_WIDTH / 2 - 28
            path = f'M{ax-CARD_WIDTH/2+6} {ay+CARD_HEIGHT/2} H{side+12} Q{side} {ay+CARD_HEIGHT/2} {side} {ay+CARD_HEIGHT/2+12} V{by-24} Q{side} {by-12} {side+12} {by-12} H{target_x-12} Q{target_x} {by-12} {target_x} {by} V{end}'
        elif edge['advisor'] == 'roberval' and edge['student'] == 'barrow':
            # Pass below Viviani's name before joining Barrow's portrait.
            lane = by - 10
            path = f'M{source_x} {start} V{lane-12} Q{source_x} {lane} {source_x-12} {lane} H{target_x+12} Q{target_x} {lane} {target_x} {lane+12} V{end}'
        else:
            mid = (start + end) / 2
            path = f'M{source_x} {start} C{source_x} {mid},{target_x} {mid},{target_x} {end}'
        historical = edge['type'] == 'historical_mentorship'
        output.append(f'<path class="tree-edge {"historical-edge" if historical else "supervision-edge"}" data-advisor="{edge["advisor"]}" data-student="{edge["student"]}" d="{path}" marker-end="url(#graph-arrow)"/>')
    for ident, (x, y) in COORDS.items():
        node = NODES[ident]
        output.append(f'<a class="tree-person" href="{h(node["profile_url"])}" data-person="{ident}" data-x="{x}" data-y="{y}" aria-label="{h(node["name"])}" transform="translate({x-CARD_WIDTH/2:g} {y})">')
        output.append(f'<rect class="tree-card" width="{CARD_WIDTH}" height="{CARD_HEIGHT}" rx="7"/>')
        if node['image']:
            width, height = node['image_size']
            output.append(f'<svg class="tree-portrait" aria-hidden="true" x="10" y="10" width="52" height="60" viewBox="{node["crop_viewbox"]}" preserveAspectRatio="xMidYMid slice" overflow="hidden"><title>{h(portrait_credit(node))}</title><image href="{node["image"]}" width="{width}" height="{height}"/></svg>')
        else:
            output.append(f'<rect class="tree-photo-bg" x="10" y="10" width="52" height="60" rx="4"/><text class="tree-initials" x="36" y="47" text-anchor="middle">{h(node["initials"])}</text>')
        lines = textwrap.wrap(node['label'], width=19, break_long_words=False)
        first = 45 if len(lines) == 1 else 36
        for i, line in enumerate(lines):
            output.append(f'<text class="tree-name" x="74" y="{first+i*18}">{h(line)}</text>')
        output.append('</a>')
    # Keep attribution data with the displayed images without adding page sections.
    credits = {ident: {'name': n['name'], 'source': n['portrait'].get('file_page') or n['portrait'].get('source_page'), 'credit': n['portrait'].get('credit', ''), 'license': n['portrait'].get('license', ''), 'license_url': n['portrait'].get('license_url', ''), 'modifications': 'Resized WebP; display cropped'} for ident, n in NODES.items() if n['image']}
    output.append('<metadata id="portrait-attributions">'+escape(json.dumps(credits, ensure_ascii=False))+'</metadata>')
    output.append('</svg>')
    return '\n'.join(output)


people = '\n'.join(f'<li class="directory-item">{person_link(node)}</li>' for node in NODES.values())
page = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Academic genealogy — Hossein Hafezi</title>
    <meta name="description" content="The academic genealogy of Hossein Hafezi, with portraits and links to forty teachers, mentors and supervisors.">
    <link rel="canonical" href="https://hosseinhafezi.com/genealogy.html">
    <link rel="icon" href="asset/cambridge-logo.jpeg">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Hossein Hafezi">
    <meta property="og:title" content="Academic genealogy — Hossein Hafezi">
    <meta property="og:description" content="Forty people and their connections across generations of teaching, mentorship and supervision.">
    <meta property="og:url" content="https://hosseinhafezi.com/genealogy.html">
    <meta name="twitter:card" content="summary">
    <link rel="stylesheet" href="asset/style.css?v=4">
    <link rel="stylesheet" href="asset/genealogy.css?v=5">
    <script src="asset/genealogy.js?v=5" defer></script>
</head>
<body class="genealogy-page">
<a class="genealogy-skip" href="#main">Skip to content</a>
<header class="site-header">
    <div class="wrap">
        <a class="brand" href="index.html">Hossein Hafezi</a>
        <nav class="site-nav" aria-label="Main navigation">
            <a href="index.html">About</a><a href="publication.html">Research</a>
            <a href="blogs.html">Blog</a><a href="personal-life.html">Personal</a>
        </nav>
    </div>
</header>
<main id="main" class="wrap genealogy-main" tabindex="-1">
    <div class="genealogy-hero">
        <h1>Academic genealogy</h1>
    </div>
    <section class="explore-section" id="explore" aria-label="Academic genealogy explorer">
        <nav class="view-switch" aria-label="Ways to explore the genealogy">
            <a href="#tree-view" data-view="tree" class="is-active">Full tree</a>
            <a href="#people-view" data-view="people">All 40 people</a>
        </nav>
        <div class="genealogy-view" id="tree-view" data-panel="tree">
            <p class="view-description">Lines run from teachers and supervisors to their students.</p>
            <div class="tree-viewer" id="tree-viewer">
                <div class="tree-toolbar enhancement-only" aria-label="Tree controls">
                    <div class="zoom-controls"><button type="button" data-zoom="out" aria-label="Zoom out">−</button><output id="tree-zoom" aria-live="polite">100%</output><button type="button" data-zoom="in" aria-label="Zoom in">+</button><button type="button" id="tree-fit">Fit width</button></div>
                    <div class="tree-actions"><button type="button" id="tree-fullscreen" aria-label="View tree in full screen">Expand <span aria-hidden="true">⤢</span></button></div>
                </div>
                <div class="tree-board" id="tree-board" tabindex="0" role="region" aria-label="Scrollable academic family tree. Use arrow keys or scroll to explore.">GRAPH</div>
                <div class="tree-caption"><span><span class="legend-line" aria-hidden="true"></span>Supervision <span class="legend-line historical" aria-hidden="true"></span>Historical teaching</span><span>Scroll to explore</span></div>
            </div>
        </div>
        <div class="genealogy-view" id="people-view" data-panel="people">
            <ul class="people-directory">PEOPLE</ul>
        </div>
    </section>
</main>
</body>
</html>
'''
for key, value in [('GRAPH', graph()), ('PEOPLE', people)]:
    page = page.replace(key, value)
(ROOT / 'genealogy.html').write_text(page)
print(f'Generated genealogy.html with {len(NODES)} people, {len(EDGES)} relationships and {sum(bool(n["image"]) for n in NODES.values())} web portraits.')
print('Portrait transfer size:', sum(p.stat().st_size for p in PORTRAITS.glob('*.webp')), 'bytes')
