"""Rebuild the local architecture bundle. Python stdlib + Pillow; no network calls.

Draw.io XML, SVG and PNG share the same scene geometry and text. The previews
are local scene renders, not screenshots of the diagrams.net editor.
"""
from pathlib import Path
import base64
import copy
import hashlib
import html
import json
import math
import re
import urllib.parse
import xml.etree.ElementTree as ET
import zlib

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PALETTE = {
    'client': ('#d1fae5', '#047857'),
    'service': ('#dbeafe', '#1d4ed8'),
    'data': ('#ede9fe', '#7c3aed'),
    'external': ('#fef3c7', '#b45309'),
    'note': ('#f1f5f9', '#64748b'),
    'risk': ('#ffe4e6', '#be123c'),
    'success': ('#dcfce7', '#15803d'),
}


def node(key, x, y, w, h, title, lines, kind='service', db=False, size=21):
    return dict(key=key, x=x, y=y, w=w, h=h, title=title, lines=lines,
                kind=kind, db=db, size=size)


def edge(key, source, target, points, label='', at=None,
         color='#475569', dashed=False, both=False):
    return dict(key=key, source=source, target=target, points=points,
                label=label, at=at, color=color, dashed=dashed, both=both)


OVERVIEW = dict(
    name='01 - High-level architecture', file='system-overview', w=2800, h=1840,
    title='Team drawing game | High-level architecture',
    subtitle='PROPOSED BASELINE  /  Next.js + NestJS + FastAPI  /  One active game process  /  Live match state in RAM',
    nodes=[
        node('browser', 80, 220, 420, 240, 'Players in browsers', [
            'Next.js client / React / TypeScript', 'Canvas 2D + Pointer Events',
            'Paint locally; send stroke batches', 'Render team canvas + shared hints',
            'ACK rendered canvas + hint versions'], 'client', size=20),
        node('game', 1140, 220, 600, 280, 'NestJS game backend', [
            'Node.js + TypeScript + NestJS', 'Socket.IO gateway + HTTP controllers',
            'RAM: canvas, clock, roles, scores', 'Serialized match events / dedupe / privacy',
            'AI checkpoints + result validation', 'One active game process; many matches']),
        node('db', 2190, 220, 540, 260, 'PostgreSQL | saved game data', [
            'Match setup + finalized round results', 'Archived drawing events + AI attempts',
            'Input artifacts + model/config versions', 'Prisma access through NestJS services',
            'No SQL wait for live stroke delivery'], 'data', db=True, size=20),
        node('next', 80, 700, 420, 230, 'Next.js web application', [
            'App Router + TypeScript', 'Tailwind CSS + shadcn/ui',
            'Lobby / game / saved replay screens', 'Guest sessions + room codes',
            'Per-stroke drawing stays outside React'], size=20),
        node('render', 1140, 700, 450, 230, 'Canonical render workers', [
            'Render accepted drawing operations', 'PNG/compression off game event loop',
            'Snapshot hash + canvas/hint versions', 'AI release waits for render ACKs'], size=20),
        node('ai', 1810, 700, 390, 230, 'Python AI service', [
            'FastAPI + Pydantic contracts', 'Bounded admission / deadlines',
            'POST jobs; push completions', 'Retry notifications; ACK job IDs',
            'Authenticated internal-only link'], size=19),
        node('models', 2380, 700, 350, 250, 'Loaded GPU models', [
            'PyTorch + Transformers', 'Qwen3-VL-2B: guesser*',
            'Florence-2-base: referee*', 'Loaded weights; fair scheduling',
            'Separate logical jobs per team'], size=19),
        node('trace', 2380, 990, 350, 140, 'Metrics / logs', [
            'Draw latency, queues, reconnects', 'Langfuse optional; sanitized inputs'],
             'external', size=18),
        node('research', 80, 1160, 420, 250, 'Sketch-focused comparison', [
            'Python / pandas / notebooks', 'Authorized matched-sketch exports',
            'No gameplay hints or AI handicap', 'Target correctness is primary',
            'Timing secondary; explanations later'], 'client', size=20),
        node('modules', 1140, 1160, 630, 250, 'Inside the NestJS backend', [
            'Rooms / teams / guest-session services', 'In-process match registry + match engines',
            'Round lifecycle + scoring services', 'AI connector + rendered-view barrier',
            'Prisma persistence + replay/export services'], 'note', size=21),
        node('archive', 2190, 1160, 540, 220, 'Archive + export worker', [
            'NestJS-owned background module', 'Bounded RAM queue; batched SQL writes',
            'Persist replay events and model inputs', 'Flush round events before finalization',
            'Serve authorized replay / research API'], size=20),
        node('policy', 80, 1540, 1300, 200, 'Gameplay and privacy contract', [
            'Agreed team counts/sizes, including unequal teams; one rotating drawer, all others guess.',
            'One team score on its first correct answer; all teams use the same prompt and hint clock.',
            'Only drawers know the target; team canvases and AI guess text remain private until reveal.',
            'Referee flags are public and advisory; private text and image crops stay team-scoped.'],
             'note', size=21),
        node('reliability', 1530, 1540, 1200, 200, 'Acceptance, reconnects and persistence', [
            'Ordered RAM updates and live broadcast; PostgreSQL archival runs in the background.',
            'Reconnects can resume live state while the game process is running.',
            'Game process restart: void unfinished rounds; restore only committed saved results.',
            'Team grace/forfeit and round-wide AI-outage bonus rules remain in effect.'],
             'note', size=20),
    ],
    edges=[
        edge('play', 'browser', 'game', [(500, 310), (1140, 310)], 'Socket.IO / WSS', (820, 284), both=True),
        edge('web', 'browser', 'next', [(290, 460), (290, 700)], 'HTTPS / UI', (390, 580), both=True),
        edge('api', 'next', 'game', [(500, 800), (820, 800), (820, 460), (1140, 460)], 'HTTPS APIs', (660, 774), both=True),
        edge('saved', 'game', 'db', [(1740, 310), (2190, 310)], 'Setup / final results / history', (1965, 284), both=True),
        edge('capture', 'game', 'render', [(1370, 500), (1370, 700)], 'Frozen state', (1485, 595), color='#7c3aed', dashed=True),
        edge('jobs', 'render', 'ai', [(1590, 815), (1810, 815)], 'Image + hints', (1700, 789), color='#7c3aed', dashed=True),
        edge('work', 'ai', 'models', [(2200, 815), (2380, 815)], 'Jobs / results', (2290, 789), color='#7c3aed', dashed=True, both=True),
        edge('complete', 'ai', 'game', [(2000, 700), (2000, 580), (1700, 580), (1700, 500)],
             'Pushed completion + ACK', (1845, 553), color='#7c3aed', dashed=True),
        edge('archive-events', 'game', 'archive', [(1210, 500), (1210, 550), (1040, 550), (1040, 1020), (2100, 1020), (2100, 1270), (2190, 1270)],
             'Async event batches', (1540, 994), color='#7c3aed', dashed=True),
        edge('archive-db', 'archive', 'db', [(2730, 1270), (2770, 1270), (2770, 370), (2730, 370)],
             'Batched writes', (2660, 595), color='#7c3aed', dashed=True),
        edge('exports', 'research', 'archive', [(290, 1410), (290, 1470), (2050, 1470), (2050, 1360), (2190, 1360)],
             'Authorized export API', (1040, 1444), both=True),
        edge('metrics', 'models', 'trace', [(2555, 950), (2555, 990)], color='#b45309', dashed=True),
    ],
    footer='Solid: live / HTTP / control I/O   |   Dashed: asynchronous work   |   * Models are candidates   |   Application code and benchmarks are not included',
)

AI_FLOW = dict(
    name='02 - AI observation and result flow', file='ai-inference-flow', w=2800, h=1690,
    title='AI inference | Matched observations and accepted results',
    subtitle='Each team is a separate logical race. NestJS owns the match and scoring; FastAPI performs inference and pushes completed results.',
    nodes=[
        node('snapshot', 80, 220, 480, 260, '1  Freeze checkpoint input', [
            'Canonical team canvas V + hint state H', 'Worker renders accepted operations',
            'Common scheduled checkpoint', 'Bind match / round / team / attempt',
            'Image hash + renderer/config revisions'], size=20),
        node('barrier', 850, 220, 600, 260, '2  Match engine waits and reserves', [
            'Check every active human guesser:', 'ACK rendered canvas >= V and hints >= H',
            'Reserve the attempt once in match RAM', 'Then release the frozen input to the AI',
            'Lag or disconnect enters team grace', 'ACK is not conscious human perception'], size=21),
        node('api', 1900, 220, 700, 260, '3  Admit an authenticated job', [
            'FastAPI validates bounded Pydantic payloads', 'Accept job ID and reserved attempt identity',
            'Return accepted job identity promptly', 'Enforce queue capacity and per-job deadline',
            'Keep the game loop independent of GPU work']),
        node('worker', 1900, 800, 700, 280, '4  Run bounded GPU inference', [
            'Keep weights loaded; fair scheduling across teams', 'One loaded guesser can serve many logical races',
            'Guesser and referee use separate task adapters', 'Record capture, queue, start, finish and receipt',
            'Push terminal results; retry until acknowledged']),
        node('gate', 850, 800, 600, 280, '5  Validate in the NestJS engine', [
            'Current server instance + round generation', 'Team active; no earlier human solve',
            'Expected job / V / H / hash + deadline', 'Reserved attempt valid and not applied',
            'Serialize with human guesses; update RAM', 'Older checkpoint V can remain valid'], size=20),
        node('accept', 80, 800, 480, 280, '6  Publish permitted outcomes', [
            'Guesser: server checks the secret target', 'Publish progress; hide AI guess text',
            'Referee: public advisory warning only', 'Private text/crops remain team-scoped',
            'Late AI cannot undo a human solve', 'Guesser outage: round-wide bonus off'], 'success', size=20),
        node('privacy', 80, 1250, 480, 240, 'Permitted model input', [
            'Canonical image + allowed hints', 'No secret target or human guesses',
            'No private opposing canvas', 'Models cannot read the game database',
            'Evaluation labels stay outside inference'], 'note', size=20),
        node('late', 850, 1250, 600, 240, 'Rejected or unavailable', [
            'Wrong instance/round, duplicate, or expired', 'Finished / forfeited team: no score change',
            'Canceled work is not an incorrect AI guess', 'A failed required attempt is unavailable',
            'Return idempotent result acknowledgement'], 'risk', size=20),
        node('models', 1900, 1250, 700, 240, 'Model candidates | pilot required', [
            'Guesser: Qwen/Qwen3-VL-2B-Instruct', 'Referee evidence: microsoft/Florence-2-base',
            'OCR regions do not prove a written clue is illegal', 'Incidental writing on objects remains permitted',
            'Measure accuracy, region usefulness and tail latency'], 'note'),
    ],
    edges=[
        edge('observe', 'snapshot', 'barrier', [(560, 345), (850, 345)], 'Frozen input V / H', (705, 319)),
        edge('submit', 'barrier', 'api', [(1450, 345), (1900, 345)], 'Reserved job + input identity', (1675, 319), color='#7c3aed', dashed=True),
        edge('queue', 'api', 'worker', [(2250, 480), (2250, 800)], 'Bounded GPU job', (2400, 640), color='#7c3aed', dashed=True),
        edge('complete', 'worker', 'gate', [(1900, 930), (1450, 930)], 'Push result / retry / ACK', (1675, 904), color='#7c3aed', dashed=True),
        edge('apply', 'gate', 'accept', [(850, 930), (560, 930)], 'Accepted once', (705, 904), color='#15803d'),
        edge('reject', 'gate', 'late', [(1150, 1080), (1150, 1250)], 'Reject / unavailable', (1310, 1160), color='#be123c', dashed=True),
    ],
    footer='Validate the frozen job identity, not the latest canvas version. A new server instance rejects old jobs; live events are ordered in match RAM.',
)

RECOVERY = dict(
    name='03 - Reconnect and restart policies', file='recovery-flow', w=2800, h=1690,
    title='Reconnects and restarts | In-memory game server baseline',
    subtitle='Client resynchronization can use a surviving process. A game-process restart voids unfinished rounds; only committed saved results are restored.',
    nodes=[
        node('failure', 80, 220, 480, 260, 'Connection interrupted', [
            'Reconnect with stable guest identity', 'Present the last applied sequence',
            'Socket ID is not the player identity', 'Check whether the game process survived',
            'Bound reconnect grace by the deadline'], 'risk', size=20),
        node('recover', 850, 220, 600, 260, 'Same live NestJS process', [
            'Authoritative match state remains in RAM', 'Authenticate membership and role',
            'Send a filtered snapshot + missing events', 'Deduplicate retries and detect sequence gaps',
            'Require fresh rendered-view acknowledgements'], size=21),
        node('resume', 1900, 220, 700, 260, 'Return to play', [
            'Surviving process: resume the current challenge', 'Restart: resume the saved match at a fresh round',
            'All active guessers ACK their permitted view', 'Bound reconnect grace by the round deadline',
            'Grace expires: the affected team forfeits'], 'success'),
        node('restart', 80, 800, 480, 280, 'Game process restarted', [
            'Live match state and RAM buffers lost', 'No automatic active-match failover',
            'Assign a new server instance identity', 'Reject AI results from the old instance',
            'Detect rounds without finalization'], 'risk', size=20),
        node('uncertain', 850, 800, 600, 280, 'Void the interrupted round', [
            'Discard its provisional points and bonus', 'Retain committed finalized round scores',
            'Retry the same match round position', 'Use a fresh prompt and round generation',
            'Do not advance the drawer rotation'], 'risk', size=21),
        node('db', 1900, 800, 700, 280, 'Saved records | PostgreSQL', [
            'Match setup, team roster and finalized scores', 'Archived round events and model inputs',
            'Flush events before finalizing a round', 'Unique round finalization / idempotent writes',
            'Unflushed live events can be lost on restart'], 'data', db=True),
        node('disconnect', 80, 1250, 780, 240, 'Human lag / disconnect', [
            'Affected team gets a bounded reconnect grace period.', 'Other teams and the common round clock continue.',
            'Hold affected-team AI delivery until rendered catch-up.', 'Grace expires: forfeit that team; cancel its AI jobs.',
            'Normal reconnect depends on the live game process.'], 'note'),
        node('outage', 960, 1250, 780, 240, 'AI service outage', [
            'Human speed points remain valid.', 'Required guesser attempt unavailable: all round AI bonuses off.',
            'Bonuses stay provisional until round finalization.', 'Normal cancellation after a solve is not a service outage.',
            'Referee outage: advisory flagging unavailable.'], 'note', size=20),
        node('durability', 1840, 1250, 780, 240, 'Persistence and scope', [
            'Live drawing is accepted in RAM and broadcast immediately.', 'PostgreSQL writes are batched in background workers.',
            'Flush round events, then commit the finalized result.', 'The baseline uses one active NestJS game process.',
            'Transparent server failover is outside this baseline.'], 'note', size=20),
    ],
    edges=[
        edge('survives', 'failure', 'recover', [(560, 345), (850, 345)], 'Process survived', (705, 319)),
        edge('resync', 'recover', 'resume', [(1450, 345), (1900, 345)], 'Authenticated resync', (1675, 319), color='#15803d'),
        edge('restarted', 'failure', 'restart', [(320, 480), (320, 800)], 'Process restarted', (480, 640), color='#be123c', dashed=True),
        edge('void', 'restart', 'uncertain', [(560, 930), (850, 930)], 'Void live round', (705, 904), color='#be123c', dashed=True),
        edge('saved', 'uncertain', 'db', [(1450, 1020), (1900, 1020)], 'Load committed results', (1675, 994), both=True),
        edge('return', 'db', 'resume', [(2250, 800), (2250, 480)], 'Saved match / fresh round', (2460, 640), color='#15803d'),
    ],
    footer='This baseline supports client reconnects while the backend is alive. Backend restart interrupts every active match hosted in that process.',
)

PAGES = [OVERVIEW, AI_FLOW, RECOVERY]


def font(size, bold=False):
    name = 'segoeuib.ttf' if bold else 'segoeui.ttf'
    windows = Path('C:/Windows/Fonts') / name
    if windows.exists():
        return ImageFont.truetype(str(windows), size)
    return ImageFont.truetype('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf', size)


def overlap(a, b):
    return (max(a[0], b[0]) < min(a[2], b[2]) and
            max(a[1], b[1]) < min(a[3], b[3]))


def bounds(n):
    return (n['x'], n['y'], n['x'] + n['w'], n['y'] + n['h'])


def line_hits(a, b, box):
    x0, y0, x1, y1 = box
    if a[0] == b[0]:
        return x0 < a[0] < x1 and max(min(a[1], b[1]), y0) < min(max(a[1], b[1]), y1)
    return y0 < a[1] < y1 and max(min(a[0], b[0]), x0) < min(max(a[0], b[0]), x1)


def validate_geometry(page, draw):
    shapes = {n['key']: n for n in page['nodes']}
    for i, n in enumerate(page['nodes']):
        assert n['x'] >= 0 and n['y'] >= 0
        assert n['x'] + n['w'] <= page['w'] and n['y'] + n['h'] <= page['h']
        for other in page['nodes'][i+1:]:
            assert not overlap(bounds(n), bounds(other)), ('overlap', n['key'], other['key'])
        assert draw.textlength(n['title'], font=font(24, True)) <= n['w'] - 36, ('title too wide', n['key'])
        for line in n['lines']:
            assert draw.textlength(line, font=font(n['size'])) <= n['w'] - 36, ('body too wide', n['key'], line)
        start = 95 if n['db'] else 65
        last = start + (len(n['lines']) - 1) * (n['size'] + 8) + n['size'] + 15
        assert last <= n['h'], ('body too tall', n['key'], last, n['h'])
    for e in page['edges']:
        assert len(e['points']) >= 2
        for a, b in zip(e['points'], e['points'][1:]):
            assert a != b and (a[0] == b[0] or a[1] == b[1]), ('nonorthogonal', e['key'])
            for n in page['nodes']:
                if n['key'] not in [e['source'], e['target']]:
                    assert not line_hits(a, b, bounds(n)), ('edge through node', e['key'], n['key'])
        for key, p in [(e['source'], e['points'][0]), (e['target'], e['points'][-1])]:
            x0, y0, x1, y1 = bounds(shapes[key])
            assert x0 <= p[0] <= x1 and y0 <= p[1] <= y1, ('bad port', e['key'], key)
            assert p[0] in [x0, x1] or p[1] in [y0, y1], ('port not on boundary', e['key'], key)
        if e['label']:
            tw = draw.textlength(e['label'], font=font(19)) + 20
            x, y = e['at']
            labelbox = (x-tw/2, y-15, x+tw/2, y+15)
            assert labelbox[0] >= 0 and labelbox[2] <= page['w']
            for n in page['nodes']:
                assert not overlap(labelbox, bounds(n)), ('label over node', e['key'], n['key'])


def make(page):
    W, H = page['w'], page['h']
    mx = ET.Element('mxfile', host='app.diagrams.net', type='device')
    d = ET.SubElement(mx, 'diagram', id=page['file'], name=page['name'])
    model = ET.SubElement(d, 'mxGraphModel', dx=str(W), dy=str(H), grid='1', gridSize='10',
                          guides='1', tooltips='1', connect='1', arrows='1', fold='1',
                          page='1', pageScale='1', pageWidth=str(W), pageHeight=str(H),
                          math='0', shadow='0', background='#ffffff')
    root = ET.SubElement(model, 'root')
    ET.SubElement(root, 'mxCell', id='0')
    ET.SubElement(root, 'mxCell', id='1', parent='0')
    im = Image.new('RGB', (W, H), 'white')
    dr = ImageDraw.Draw(im)
    validate_geometry(page, dr)
    shapes = {n['key']: n for n in page['nodes']}
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<rect width="100%" height="100%" fill="white"/>']

    def svg_text(x, y, text, size=21, color='#334155', bold=False, anchor='start'):
        svg.append(f'<text x="{x}" y="{y}" font-family="Segoe UI,Arial,sans-serif" font-size="{size}" '
                   f'font-weight="{700 if bold else 400}" fill="{color}" text-anchor="{anchor}">{html.escape(text)}</text>')

    def text_cell(key, text, x, y, w, h, size, color='#0f172a', bold=False):
        c = ET.SubElement(root, 'mxCell', id=key, value=text,
                          style=f'text;html=0;align=left;verticalAlign=middle;strokeColor=none;fillColor=none;fontFamily=Segoe UI;fontSize={size};fontColor={color};fontStyle={int(bold)};',
                          vertex='1', parent='1')
        ET.SubElement(c, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), attrib={'as':'geometry'})
        dr.text((x, y), text, font=font(size, bold), fill=color)
        svg_text(x, y+size, text, size, color, bold)

    text_cell('title', page['title'], 70, 30, W-140, 60, 40, bold=True)
    text_cell('subtitle', page['subtitle'], 70, 109, W-140, 42, 22, '#475569')

    for e in page['edges']:
        points = e['points']
        s, t = shapes[e['source']], shapes[e['target']]
        ex, ey = (points[0][0]-s['x'])/s['w'], (points[0][1]-s['y'])/s['h']
        ix, iy = (points[-1][0]-t['x'])/t['w'], (points[-1][1]-t['y'])/t['h']
        style = f'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;strokeWidth=2;strokeColor={e["color"]};exitX={ex};exitY={ey};exitPerimeter=0;entryX={ix};entryY={iy};entryPerimeter=0;'
        if e['dashed']:
            style += 'dashed=1;'
        if e['both']:
            style += 'startArrow=block;startFill=1;'
        c = ET.SubElement(root, 'mxCell', id=e['key'], value='', style=style,
                          edge='1', parent='1', source=e['source'], target=e['target'])
        g = ET.SubElement(c, 'mxGeometry', relative='1', attrib={'as':'geometry'})
        if len(points) > 2:
            array = ET.SubElement(g, 'Array', attrib={'as':'points'})
            for x, y in points[1:-1]:
                ET.SubElement(array, 'mxPoint', x=str(x), y=str(y))
        pts = ' '.join(f'{x},{y}' for x, y in points)
        dash = ' stroke-dasharray="10 7"' if e['dashed'] else ''
        svg.append(f'<polyline points="{pts}" fill="none" stroke="{e["color"]}" stroke-width="3"{dash}/>')
        for a, b in zip(points, points[1:]):
            length = abs(b[0]-a[0]) + abs(b[1]-a[1])
            if not e['dashed']:
                dr.line([a, b], fill=e['color'], width=3)
            else:
                for k in range(0, length, 17):
                    def at(v):
                        return (a[0]+(b[0]-a[0])*v/length, a[1]+(b[1]-a[1])*v/length)
                    dr.line([at(k), at(min(k+10, length))], fill=e['color'], width=3)

        def arrow(prev, end):
            dx, dy = end[0]-prev[0], end[1]-prev[1]
            length = math.hypot(dx, dy)
            ux, uy = dx/length, dy/length
            poly = [end, (end[0]-14*ux+6*uy, end[1]-14*uy-6*ux),
                    (end[0]-14*ux-6*uy, end[1]-14*uy+6*ux)]
            dr.polygon(poly, fill=e['color'])
            svg.append('<polygon points="'+' '.join(f'{x},{y}' for x, y in poly)+f'" fill="{e["color"]}"/>')

        arrow(points[-2], points[-1])
        if e['both']:
            arrow(points[1], points[0])

    for n in page['nodes']:
        x, y, w, h = n['x'], n['y'], n['w'], n['h']
        fill, stroke = PALETTE[n['kind']]
        size = n['size']
        label = '<div style="font-size:24px;font-weight:700;">'+html.escape(n['title'])+'</div>'
        label += f'<div style="font-size:{size}px;line-height:{size+8}px;margin-top:16px;">'
        label += '<br>'.join(html.escape(line) for line in n['lines'])+'</div>'
        shape = 'shape=mxgraph.flowchart.database;' if n['db'] else 'rounded=1;arcSize=10;'
        padding_top = 40 if n['db'] else 18
        style = f'{shape}html=1;whiteSpace=wrap;align=left;verticalAlign=top;spacing=18;spacingTop={padding_top};strokeWidth=2;fillColor={fill};strokeColor={stroke};fontColor=#0f172a;fontFamily=Segoe UI;fontSize={size};'
        c = ET.SubElement(root, 'mxCell', id=n['key'], value=label, style=style, vertex='1', parent='1')
        ET.SubElement(c, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), attrib={'as':'geometry'})
        dr.rounded_rectangle((x, y, x+w, y+h), radius=14, fill=fill, outline=stroke, width=2)
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        if n['db']:
            dr.ellipse((x, y, x+w, y+36), fill=fill, outline=stroke, width=2)
            svg.append(f'<ellipse cx="{x+w/2}" cy="{y+18}" rx="{w/2}" ry="18" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        title_top = y + (46 if n['db'] else 18)
        body_top = y + (95 if n['db'] else 65)
        dr.text((x+18, title_top), n['title'], font=font(24, True), fill='#0f172a')
        svg_text(x+18, title_top+24, n['title'], 24, '#0f172a', True)
        for j, line in enumerate(n['lines']):
            ty = body_top + j*(size+8)
            dr.text((x+18, ty), line, font=font(size), fill='#334155')
            svg_text(x+18, ty+size, line, size)

    for e in page['edges']:
        if not e['label']:
            continue
        x, y = e['at']
        tw = dr.textlength(e['label'], font=font(19))
        width = math.ceil(tw+20)
        c = ET.SubElement(root, 'mxCell', id=e['key']+'-label', value=e['label'],
                          style=f'text;html=0;align=center;verticalAlign=middle;fillColor=#ffffff;strokeColor=none;fontFamily=Segoe UI;fontColor={e["color"]};fontSize=19;',
                          vertex='1', parent='1')
        ET.SubElement(c, 'mxGeometry', x=str(x-width/2), y=str(y-16), width=str(width), height='32', attrib={'as':'geometry'})
        dr.rectangle((x-width/2, y-16, x+width/2, y+16), fill='white')
        dr.text((x-tw/2, y-13), e['label'], font=font(19), fill=e['color'])
        svg.append(f'<rect x="{x-width/2}" y="{y-16}" width="{width}" height="32" fill="white"/>')
        svg_text(x, y+6, e['label'], 19, e['color'], anchor='middle')

    text_cell('footer', page['footer'], 70, H-65, W-140, 35, 19, '#475569')
    ET.indent(mx)
    ET.ElementTree(mx).write(HERE/(page['file']+'.drawio'), encoding='utf-8', xml_declaration=True)
    im.save(HERE/(page['file']+'.png'))
    svg.append('</svg>')
    (HERE/(page['file']+'.svg')).write_text('\n'.join(svg), encoding='utf-8')
    print('Generated and geometry-checked', page['file'])


def combine_pages():
    combined = ET.Element('mxfile', host='app.diagrams.net', type='device')
    for page in PAGES:
        tree = ET.parse(HERE/(page['file']+'.drawio'))
        for diagram in tree.getroot().findall('diagram'):
            combined.append(copy.deepcopy(diagram))
    ET.indent(combined)
    ET.ElementTree(combined).write(HERE/'drawing-game-system-design.drawio', encoding='utf-8', xml_declaration=True)
    print('Combined three editable pages.')


def refresh_launcher():
    raw = (HERE/'drawing-game-system-design.drawio').read_bytes()
    encoded = urllib.parse.quote(raw.decode('utf-8'), safe="~()*!.'-_").encode()
    compressor = zlib.compressobj(wbits=-15)
    payload = base64.b64encode(compressor.compress(encoded)+compressor.flush()).decode()
    revision = hashlib.sha256(raw).hexdigest()[:12]
    url = f'https://app.diagrams.net/?offline=1&proto=json&ui=atlas&rev={revision}#R{payload}'
    (HERE/'editor-url.txt').write_text(url, encoding='utf-8')
    cards = []
    for page in PAGES:
        stem = page['file']
        cards.append(f'<section><h2>{html.escape(page["name"])}</h2><p><a href="{stem}.drawio">Editable page</a> · <a href="{stem}.svg">Zoomable SVG</a> · <a href="{stem}.png">PNG</a></p><img src="{stem}.svg" alt="{html.escape(page["title"])}"></section>')
    doc = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Team drawing game — architecture</title><style>body{{font:18px/1.5 system-ui;margin:32px;color:#0f172a;background:#f8fafc}}main{{max-width:1600px;margin:auto}}a{{color:#1d4ed8}}section{{background:white;border:1px solid #cbd5e1;border-radius:16px;padding:20px;margin:30px 0}}img{{width:100%;height:auto}}.note{{padding:14px;background:#fff7ed;border-radius:8px}}</style>
<main><h1>Team drawing game — consolidated architecture</h1><p>Revision {revision} · Proposed design · Three editable pages</p>
<p><a href="drawing-game-system-design.drawio">Open/download complete Draw.io source</a> · <a href="../../SYSTEM-DESIGN.md">Design notes</a></p>
<p class="note">This local viewer loads no external scripts. The optional link below opens diagrams.net with the diagram embedded in its URL; use Device → Open in a local draw.io installation if you prefer to keep editing local. Local PNG/SVG previews are scene renders, not screenshots of the online editor.</p>
<p><a href="{html.escape(url,quote=True)}" rel="noreferrer">Optional: open the editable online diagram</a></p>
{''.join(cards)}</main></html>'''
    (HERE/'open-system-design.html').write_text(doc, encoding='utf-8')
    manifest = {'revision':revision, 'pages':[{k:p[k] for k in ['name','file','w','h']} for p in PAGES],
                'preview_method':'Shared-scene Pillow PNG and SVG. Native diagrams.net browser rendering not claimed.'}
    (HERE/'diagram-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print('Refreshed local viewer and optional editor URL, revision', revision)


if __name__ == '__main__':
    HERE.mkdir(parents=True, exist_ok=True)
    for page in PAGES:
        make(page)
    combine_pages()
    refresh_launcher()
