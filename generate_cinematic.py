#!/usr/bin/env python3
"""
CleanOps Cinematic SVG Generator v2
Generates all animated SVG assets for the cinematic README experience.
Each SVG tells a story through sequenced SMIL animation.
"""
import os

BASE = r"C:\Users\ebraa\Desktop\Test-repo\assets\v2"

def save(name, content):
    path = os.path.join(BASE, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(content)
    print(f"  [OK] {name}")

# ─────────────────────────────────────────────────────
# SHARED DEFS
# ─────────────────────────────────────────────────────
DEFS = """<defs>
  <filter id="g1" x="-40%" y="-40%" width="180%" height="180%">
    <feGaussianBlur stdDeviation="8" result="b"/>
    <feComposite in="SourceGraphic" in2="b" operator="over"/>
  </filter>
  <filter id="g2" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur stdDeviation="4" result="b"/>
    <feComposite in="SourceGraphic" in2="b" operator="over"/>
  </filter>
  <filter id="g3" x="-20%" y="-20%" width="140%" height="140%">
    <feGaussianBlur stdDeviation="2" result="b"/>
    <feComposite in="SourceGraphic" in2="b" operator="over"/>
  </filter>
  <filter id="soft" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="12"/>
  </filter>
  <linearGradient id="bgG" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#060910"/>
    <stop offset="50%" stop-color="#0A0F1D"/>
    <stop offset="100%" stop-color="#060910"/>
  </linearGradient>
  <linearGradient id="oG" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#F97316" stop-opacity="0"/>
    <stop offset="30%" stop-color="#F97316" stop-opacity="1"/>
    <stop offset="70%" stop-color="#F97316" stop-opacity="1"/>
    <stop offset="100%" stop-color="#F97316" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="orbG">
    <stop offset="0%" stop-color="#F97316" stop-opacity="0.3"/>
    <stop offset="100%" stop-color="#F97316" stop-opacity="0"/>
  </radialGradient>
  <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
    <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#1B2A52" stroke-width="0.4" opacity="0.4"/>
  </pattern>
</defs>"""

def bg(w, h):
    """Dark atmospheric background with grid and ambient orbs"""
    return f"""<rect width="{w}" height="{h}" fill="url(#bgG)"/>
  <rect width="{w}" height="{h}" fill="url(#grid)"/>
  <!-- ambient orbs -->
  <circle cx="{w*0.15}" cy="{h*0.3}" r="80" fill="url(#orbG)" opacity="0.5">
    <animate attributeName="r" values="80;100;80" dur="6s" repeatCount="indefinite"/>
  </circle>
  <circle cx="{w*0.85}" cy="{h*0.7}" r="60" fill="url(#orbG)" opacity="0.4">
    <animate attributeName="r" values="60;80;60" dur="8s" repeatCount="indefinite"/>
  </circle>
  <circle cx="{w*0.5}" cy="{h*0.1}" r="40" fill="url(#orbG)" opacity="0.3">
    <animate attributeName="r" values="40;55;40" dur="5s" repeatCount="indefinite"/>
  </circle>"""

def signal_line(x, h, delay="0s"):
    """The continuous orange signal line with traveling particle"""
    return f"""<!-- signal line -->
  <line x1="{x}" y1="0" x2="{x}" y2="{h}" stroke="url(#oG)" stroke-width="2" opacity="0.6"/>
  <circle r="3" fill="#F97316" filter="url(#g2)">
    <animate attributeName="cy" values="0;{h}" dur="4s" begin="{delay}" repeatCount="indefinite"/>
    <animate attributeName="cx" values="{x};{x}" dur="4s" begin="{delay}" repeatCount="indefinite"/>
  </circle>
  <circle r="2" fill="#FFFFFF" filter="url(#g3)">
    <animate attributeName="cy" values="0;{h}" dur="4s" begin="2s" repeatCount="indefinite"/>
    <animate attributeName="cx" values="{x};{x}" dur="4s" begin="2s" repeatCount="indefinite"/>
  </circle>"""

def boss_character(x, y, pose="idle", scale=1.0):
    """The canonical Boss character - consistent across all appearances.
    Poses: idle, wave, point, think, acknowledge
    """
    s = scale
    # Boss is ~120 units tall at scale 1
    parts = f"""<g transform="translate({x},{y}) scale({s})">
    <!-- shadow -->
    <ellipse cx="0" cy="55" rx="30" ry="6" fill="#000" opacity="0.4"/>

    <!-- body -->
    <rect x="-22" y="5" width="44" height="50" rx="8" fill="#111C38" stroke="#1B2A52" stroke-width="1.5"/>
    <!-- chest panel -->
    <rect x="-12" y="14" width="24" height="14" rx="3" fill="#0A0F1D" stroke="#F97316" stroke-width="0.8" opacity="0.8"/>
    <text x="0" y="24" font-family="Arial,sans-serif" font-size="8" font-weight="bold" fill="#F97316" text-anchor="middle">CO</text>
    <!-- panel lines -->
    <line x1="-18" y1="35" x2="18" y2="35" stroke="#1B2A52" stroke-width="0.6"/>
    <line x1="-18" y1="42" x2="18" y2="42" stroke="#1B2A52" stroke-width="0.6"/>

    <!-- head halo -->
    <circle cx="0" cy="-22" r="34" fill="none" stroke="#F97316" stroke-width="1" opacity="0.2" filter="url(#g1)"/>

    <!-- head -->
    <circle cx="0" cy="-22" r="28" fill="#142042" stroke="#1B2A52" stroke-width="1.5"/>

    <!-- antenna -->
    <line x1="0" y1="-50" x2="0" y2="-58" stroke="#94A3B8" stroke-width="2" stroke-linecap="round"/>
    <circle cx="0" cy="-60" r="3" fill="#F97316" filter="url(#g2)">
      <animate attributeName="r" values="3;4;3" dur="2s" repeatCount="indefinite"/>
    </circle>

    <!-- visor -->
    <rect x="-20" y="-32" width="40" height="18" rx="9" fill="#0A0F1D" stroke="#F97316" stroke-width="1.2" filter="url(#g3)"/>
    <!-- eyes -->
    <circle cx="-8" cy="-23" r="3" fill="#F97316" filter="url(#g2)">
      <animate attributeName="r" values="3;3.5;3" dur="3s" repeatCount="indefinite"/>
    </circle>
    <circle cx="8" cy="-23" r="3" fill="#F97316" filter="url(#g2)">
      <animate attributeName="r" values="3;3.5;3" dur="3s" repeatCount="indefinite" begin="0.15s"/>
    </circle>
    <!-- smile -->
    <path d="M -6 -14 Q 0 -10 6 -14" fill="none" stroke="#94A3B8" stroke-width="1.2" stroke-linecap="round"/>
"""

    # Pose-specific arm positions
    if pose == "wave":
        parts += """
    <!-- left arm -->
    <rect x="-32" y="10" width="12" height="30" rx="6" fill="#142042" stroke="#1B2A52" stroke-width="1"/>
    <!-- right arm waving -->
    <g transform-origin="26 10">
      <animateTransform attributeName="transform" type="rotate" values="-15;15;-15" dur="1.5s" repeatCount="indefinite"/>
      <rect x="22" y="-10" width="12" height="30" rx="6" fill="#142042" stroke="#1B2A52" stroke-width="1"/>
    </g>
"""
    elif pose == "point":
        parts += """
    <!-- left arm -->
    <rect x="-32" y="10" width="12" height="30" rx="6" fill="#142042" stroke="#1B2A52" stroke-width="1"/>
    <!-- right arm pointing -->
    <g>
      <rect x="22" y="8" width="35" height="12" rx="6" fill="#142042" stroke="#1B2A52" stroke-width="1"/>
      <!-- pointing indicator -->
      <circle cx="62" cy="14" r="4" fill="#F97316" filter="url(#g2)">
        <animate attributeName="r" values="4;6;4" dur="1.5s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="1;0.5;1" dur="1.5s" repeatCount="indefinite"/>
      </circle>
    </g>
"""
    elif pose == "think":
        parts += """
    <!-- left arm at chin -->
    <rect x="-32" y="10" width="12" height="30" rx="6" fill="#142042" stroke="#1B2A52" stroke-width="1"/>
    <!-- right arm thinking -->
    <rect x="22" y="-15" width="12" height="28" rx="6" fill="#142042" stroke="#1B2A52" stroke-width="1" transform="rotate(15,28,-1)"/>
    <!-- thought particles -->
    <circle cx="35" cy="-45" r="3" fill="#F97316" opacity="0">
      <animate attributeName="opacity" values="0;0.8;0" dur="3s" repeatCount="indefinite"/>
      <animate attributeName="cy" values="-40;-55" dur="3s" repeatCount="indefinite"/>
    </circle>
    <circle cx="42" cy="-55" r="2" fill="#F97316" opacity="0">
      <animate attributeName="opacity" values="0;0.6;0" dur="3s" begin="0.5s" repeatCount="indefinite"/>
      <animate attributeName="cy" values="-50;-65" dur="3s" begin="0.5s" repeatCount="indefinite"/>
    </circle>
    <circle cx="48" cy="-60" r="1.5" fill="#F97316" opacity="0">
      <animate attributeName="opacity" values="0;0.4;0" dur="3s" begin="1s" repeatCount="indefinite"/>
      <animate attributeName="cy" values="-58;-73" dur="3s" begin="1s" repeatCount="indefinite"/>
    </circle>
"""
    elif pose == "acknowledge":
        parts += """
    <!-- both arms slightly raised -->
    <rect x="-35" y="0" width="12" height="30" rx="6" fill="#142042" stroke="#1B2A52" stroke-width="1" transform="rotate(15,-29,15)"/>
    <rect x="23" y="0" width="12" height="30" rx="6" fill="#142042" stroke="#1B2A52" stroke-width="1" transform="rotate(-15,29,15)"/>
    <!-- success sparkles -->
    <circle cx="-30" cy="-50" r="2" fill="#10B981" opacity="0">
      <animate attributeName="opacity" values="0;1;0" dur="2s" repeatCount="indefinite"/>
    </circle>
    <circle cx="30" cy="-55" r="2" fill="#10B981" opacity="0">
      <animate attributeName="opacity" values="0;1;0" dur="2s" begin="0.4s" repeatCount="indefinite"/>
    </circle>
    <circle cx="0" cy="-65" r="2" fill="#F97316" opacity="0">
      <animate attributeName="opacity" values="0;1;0" dur="2s" begin="0.8s" repeatCount="indefinite"/>
    </circle>
"""
    else:  # idle
        parts += """
    <!-- arms at sides -->
    <rect x="-32" y="10" width="12" height="30" rx="6" fill="#142042" stroke="#1B2A52" stroke-width="1"/>
    <rect x="20" y="10" width="12" height="30" rx="6" fill="#142042" stroke="#1B2A52" stroke-width="1"/>
"""

    parts += "  </g>"
    return parts


def city_silhouette(w, y_base, opacity=0.15):
    """Abstract city skyline silhouette"""
    buildings = []
    import random
    random.seed(42)  # deterministic
    x = 0
    while x < w:
        bw = random.randint(20, 50)
        bh = random.randint(30, 120)
        buildings.append(f'<rect x="{x}" y="{y_base - bh}" width="{bw}" height="{bh}" fill="#1B2A52" opacity="{opacity}"/>')
        # windows
        for wy in range(y_base - bh + 8, y_base - 5, 12):
            for wx in range(x + 5, x + bw - 3, 8):
                if random.random() > 0.4:
                    buildings.append(f'<rect x="{wx}" y="{wy}" width="3" height="4" fill="#F97316" opacity="{random.uniform(0.05, 0.2)}"/>')
        x += bw + random.randint(3, 15)
    return "\n  ".join(buildings)


# ─────────────────────────────────────────────────────
# SCENE 01: HERO
# ─────────────────────────────────────────────────────
def gen_hero():
    W, H = 1200, 550
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  {DEFS}
  {bg(W, H)}

  <!-- city silhouette -->
  {city_silhouette(W, H - 60, 0.12)}

  <!-- ground plane glow -->
  <ellipse cx="{W//2}" cy="{H - 80}" rx="400" ry="40" fill="#F97316" opacity="0.04" filter="url(#soft)"/>

  <!-- floating data particles -->
  <g opacity="0.5">
    <circle cx="200" cy="150" r="2" fill="#F97316">
      <animate attributeName="cy" values="150;120;150" dur="7s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.3;0.8;0.3" dur="7s" repeatCount="indefinite"/>
    </circle>
    <circle cx="350" cy="200" r="1.5" fill="#3B82F6">
      <animate attributeName="cy" values="200;170;200" dur="5s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.2;0.6;0.2" dur="5s" repeatCount="indefinite"/>
    </circle>
    <circle cx="850" cy="180" r="2" fill="#F97316">
      <animate attributeName="cy" values="180;140;180" dur="6s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.4;0.9;0.4" dur="6s" repeatCount="indefinite"/>
    </circle>
    <circle cx="950" cy="250" r="1.5" fill="#10B981">
      <animate attributeName="cy" values="250;220;250" dur="8s" repeatCount="indefinite"/>
    </circle>
    <circle cx="100" cy="300" r="1" fill="#F97316">
      <animate attributeName="cy" values="300;260;300" dur="9s" repeatCount="indefinite"/>
    </circle>
    <circle cx="1050" cy="130" r="1.5" fill="#F97316">
      <animate attributeName="cy" values="130;100;130" dur="6.5s" repeatCount="indefinite"/>
    </circle>
    <circle cx="500" cy="100" r="1" fill="#8B5CF6">
      <animate attributeName="cy" values="100;80;100" dur="4s" repeatCount="indefinite"/>
    </circle>
    <circle cx="700" cy="160" r="2" fill="#F97316">
      <animate attributeName="cy" values="160;130;160" dur="5.5s" repeatCount="indefinite"/>
    </circle>
  </g>

  <!-- signal line -->
  {signal_line(W//2, H)}

  <!-- horizontal signal paths -->
  <line x1="0" y1="{H - 80}" x2="{W}" y2="{H - 80}" stroke="#F97316" stroke-width="1" opacity="0.15" stroke-dasharray="4 8"/>

  <!-- BOSS CHARACTER -->
  {boss_character(W//2, H - 190, "wave", 1.8)}

  <!-- data ring around boss -->
  <g transform="translate({W//2},{H - 190})">
    <circle cx="0" cy="-40" r="130" fill="none" stroke="#1B2A52" stroke-width="0.8" stroke-dasharray="6 12" opacity="0.5">
      <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="30s" repeatCount="indefinite"/>
    </circle>
    <circle cx="0" cy="-40" r="160" fill="none" stroke="#F97316" stroke-width="0.5" stroke-dasharray="3 20" opacity="0.3">
      <animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="25s" repeatCount="indefinite"/>
    </circle>
    <!-- orbiting nodes -->
    <circle cx="130" cy="-40" r="4" fill="#F97316" filter="url(#g3)" opacity="0.7">
      <animateTransform attributeName="transform" type="rotate" from="0 0 -40" to="360 0 -40" dur="30s" repeatCount="indefinite"/>
    </circle>
    <circle cx="-160" cy="-40" r="3" fill="#3B82F6" filter="url(#g3)" opacity="0.5">
      <animateTransform attributeName="transform" type="rotate" from="0 0 -40" to="-360 0 -40" dur="25s" repeatCount="indefinite"/>
    </circle>
  </g>

  <!-- title block with cinematic fade -->
  <g opacity="0">
    <animate attributeName="opacity" values="0;1" dur="2s" fill="freeze" begin="0.5s"/>
    <text x="{W//2}" y="80" font-family="Arial Black,Arial,sans-serif" font-size="56" font-weight="900" fill="#F8FAFC" text-anchor="middle" letter-spacing="12">CLEANOPS</text>
  </g>
  <g opacity="0">
    <animate attributeName="opacity" values="0;1" dur="2s" fill="freeze" begin="1.2s"/>
    <text x="{W//2}" y="110" font-family="Arial,sans-serif" font-size="13" fill="#94A3B8" text-anchor="middle" letter-spacing="6">AI-POWERED WASTE REPORTING &#38; SMART CLEANING MANAGEMENT</text>
  </g>
  <g opacity="0">
    <animate attributeName="opacity" values="0;1" dur="2s" fill="freeze" begin="2s"/>
    <text x="{W//2}" y="140" font-family="Arial,sans-serif" font-size="15" fill="#F97316" text-anchor="middle" letter-spacing="3" font-style="italic">From citizen reports to verified action.</text>
  </g>

  <!-- bottom accent line -->
  <rect x="0" y="{H-3}" width="{W}" height="3" fill="#F97316" opacity="0.6"/>
</svg>"""
    save("hero.svg", svg)


# ─────────────────────────────────────────────────────
# SCENE 02: PROJECT PORTAL
# ─────────────────────────────────────────────────────
def gen_portal():
    W, H = 1200, 450
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  {DEFS}
  {bg(W, H)}
  {signal_line(W//2, H)}

  <!-- BOSS pointing toward portal -->
  {boss_character(280, H//2 + 30, "point", 1.5)}

  <!-- PORTAL INTERFACE -->
  <g transform="translate(700, {H//2})" opacity="0">
    <animate attributeName="opacity" values="0;1" dur="1.5s" fill="freeze" begin="0.5s"/>

    <!-- outer frame -->
    <rect x="-230" y="-150" width="460" height="300" rx="8" fill="#0A0F1D" stroke="#1B2A52" stroke-width="2"/>
    <!-- inner frame -->
    <rect x="-220" y="-140" width="440" height="280" rx="4" fill="#111C38"/>

    <!-- title bar -->
    <rect x="-220" y="-140" width="440" height="28" fill="#0A0F1D" rx="4"/>
    <circle cx="-200" cy="-126" r="4" fill="#EF4444"/>
    <circle cx="-188" cy="-126" r="4" fill="#F59E0B"/>
    <circle cx="-176" cy="-126" r="4" fill="#10B981"/>
    <text x="-160" y="-122" font-family="Arial,sans-serif" font-size="10" fill="#64748B">cleanops-hq.pages.dev</text>

    <!-- sidebar -->
    <rect x="-220" y="-112" width="100" height="252" fill="#0A0F1D" opacity="0.5"/>
    <!-- sidebar items -->
    <rect x="-210" y="-100" width="80" height="8" rx="2" fill="#1B2A52" opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.3s" fill="freeze" begin="1.5s"/>
    </rect>
    <rect x="-210" y="-84" width="65" height="8" rx="2" fill="#1B2A52" opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.3s" fill="freeze" begin="1.7s"/>
    </rect>
    <rect x="-210" y="-68" width="75" height="8" rx="2" fill="#F97316" opacity="0">
      <animate attributeName="opacity" values="0;0.8" dur="0.3s" fill="freeze" begin="1.9s"/>
    </rect>
    <rect x="-210" y="-52" width="60" height="8" rx="2" fill="#1B2A52" opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.3s" fill="freeze" begin="2.1s"/>
    </rect>
    <rect x="-210" y="-36" width="70" height="8" rx="2" fill="#1B2A52" opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.3s" fill="freeze" begin="2.3s"/>
    </rect>

    <!-- main content cards -->
    <g opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="2.5s"/>
      <!-- project phase card -->
      <rect x="-110" y="-100" width="200" height="60" rx="4" fill="#142042" stroke="#1B2A52" stroke-width="1"/>
      <rect x="-100" y="-90" width="120" height="6" rx="2" fill="#E2E8F0"/>
      <rect x="-100" y="-78" width="80" height="4" rx="2" fill="#64748B"/>
      <!-- progress bar -->
      <rect x="-100" y="-66" width="180" height="8" rx="4" fill="#0A0F1D"/>
      <rect x="-100" y="-66" width="0" height="8" rx="4" fill="#F97316">
        <animate attributeName="width" values="0;110" dur="1.5s" fill="freeze" begin="3s"/>
      </rect>
    </g>

    <g opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="3s"/>
      <!-- task grid -->
      <rect x="-110" y="-30" width="95" height="80" rx="4" fill="#142042" stroke="#1B2A52" stroke-width="1"/>
      <rect x="-100" y="-20" width="60" height="5" rx="2" fill="#3B82F6"/>
      <rect x="-100" y="-10" width="75" height="4" rx="2" fill="#64748B"/>
      <rect x="-100" y="0" width="55" height="4" rx="2" fill="#64748B"/>
      <rect x="-100" y="15" width="40" height="14" rx="3" fill="#10B981" opacity="0.8"/>
      <text x="-80" y="25" font-family="Arial,sans-serif" font-size="8" fill="#FFF" text-anchor="middle">Active</text>

      <rect x="-5" y="-30" width="95" height="80" rx="4" fill="#142042" stroke="#1B2A52" stroke-width="1"/>
      <rect x="5" y="-20" width="50" height="5" rx="2" fill="#F97316"/>
      <rect x="5" y="-10" width="70" height="4" rx="2" fill="#64748B"/>
      <rect x="5" y="0" width="60" height="4" rx="2" fill="#64748B"/>
      <rect x="5" y="15" width="40" height="14" rx="3" fill="#F59E0B" opacity="0.8"/>
      <text x="25" y="25" font-family="Arial,sans-serif" font-size="8" fill="#FFF" text-anchor="middle">Review</text>
    </g>

    <!-- metrics row -->
    <g opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="3.5s"/>
      <rect x="-110" y="60" width="60" height="55" rx="4" fill="#142042" stroke="#1B2A52" stroke-width="1"/>
      <text x="-80" y="90" font-family="Arial,sans-serif" font-size="18" font-weight="bold" fill="#F97316" text-anchor="middle">42</text>
      <text x="-80" y="105" font-family="Arial,sans-serif" font-size="8" fill="#64748B" text-anchor="middle">Tasks</text>

      <rect x="-40" y="60" width="60" height="55" rx="4" fill="#142042" stroke="#1B2A52" stroke-width="1"/>
      <text x="-10" y="90" font-family="Arial,sans-serif" font-size="18" font-weight="bold" fill="#10B981" text-anchor="middle">16</text>
      <text x="-10" y="105" font-family="Arial,sans-serif" font-size="8" fill="#64748B" text-anchor="middle">Done</text>

      <rect x="30" y="60" width="60" height="55" rx="4" fill="#142042" stroke="#1B2A52" stroke-width="1"/>
      <text x="60" y="90" font-family="Arial,sans-serif" font-size="18" font-weight="bold" fill="#3B82F6" text-anchor="middle">10</text>
      <text x="60" y="105" font-family="Arial,sans-serif" font-size="8" fill="#64748B" text-anchor="middle">Members</text>
    </g>

    <!-- scanning line -->
    <line x1="-220" y1="-140" x2="220" y2="-140" stroke="#F97316" stroke-width="1" opacity="0.3">
      <animate attributeName="y1" values="-140;140;-140" dur="5s" repeatCount="indefinite"/>
      <animate attributeName="y2" values="-140;140;-140" dur="5s" repeatCount="indefinite"/>
    </line>

    <!-- activation pulse from Boss direction -->
    <line x1="-230" y1="0" x2="-280" y2="0" stroke="#F97316" stroke-width="2" filter="url(#g2)" opacity="0">
      <animate attributeName="opacity" values="0;0.8;0" dur="3s" repeatCount="indefinite" begin="2s"/>
    </line>
  </g>

  <!-- label -->
  <text x="{W//2}" y="40" font-family="Arial,sans-serif" font-size="14" fill="#94A3B8" text-anchor="middle" letter-spacing="6">PROJECT ENGINEERING HUB</text>
</svg>"""
    save("portal.svg", svg)


# ─────────────────────────────────────────────────────
# SCENE 03: PIPELINE / OVERVIEW
# ─────────────────────────────────────────────────────
def gen_pipeline():
    W, H = 1200, 350
    stages = [
        ("CITIZEN", "#E2E8F0"),
        ("REPORT", "#3B82F6"),
        ("AI ANALYSIS", "#8B5CF6"),
        ("PRIORITY", "#F97316"),
        ("DISPATCH", "#F59E0B"),
        ("CLEAN", "#10B981"),
        ("VERIFIED", "#10B981"),
    ]
    n = len(stages)
    pad = 80
    spacing = (W - 2*pad) / (n - 1)

    nodes = ""
    path_d = f"M {pad} {H//2}"
    for i, (label, color) in enumerate(stages):
        cx = pad + i * spacing
        cy = H // 2
        path_d += f" L {cx} {cy}"

        # node
        nodes += f"""
    <g transform="translate({cx},{cy})">
      <circle cx="0" cy="0" r="28" fill="#111C38" stroke="{color}" stroke-width="2.5" opacity="0">
        <animate attributeName="opacity" values="0;1" dur="0.4s" fill="freeze" begin="{0.3 + i*0.4}s"/>
      </circle>
      <circle cx="0" cy="0" r="28" fill="none" stroke="{color}" stroke-width="1" opacity="0">
        <animate attributeName="opacity" values="0;0.4;0" dur="3s" begin="{1 + i*0.5}s" repeatCount="indefinite"/>
        <animate attributeName="r" values="28;40;28" dur="3s" begin="{1 + i*0.5}s" repeatCount="indefinite"/>
      </circle>
      <text x="0" y="50" font-family="Arial,sans-serif" font-size="10" font-weight="bold" fill="{color}" text-anchor="middle" opacity="0">
        <animate attributeName="opacity" values="0;1" dur="0.4s" fill="freeze" begin="{0.5 + i*0.4}s"/>
        {label}
      </text>
    </g>"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  {DEFS}
  {bg(W, H)}
  {signal_line(W//2, H)}

  <!-- connection path -->
  <path id="flow" d="{path_d}" fill="none" stroke="#1B2A52" stroke-width="2" stroke-dasharray="6 6"/>

  <!-- animated signal along path -->
  <circle r="6" fill="#F97316" filter="url(#g1)">
    <animateMotion dur="5s" repeatCount="indefinite">
      <mpath href="#flow"/>
    </animateMotion>
  </circle>
  <circle r="3" fill="#FFFFFF">
    <animateMotion dur="5s" repeatCount="indefinite">
      <mpath href="#flow"/>
    </animateMotion>
  </circle>

  <!-- trailing glow -->
  <circle r="12" fill="#F97316" filter="url(#soft)" opacity="0.3">
    <animateMotion dur="5s" repeatCount="indefinite">
      <mpath href="#flow"/>
    </animateMotion>
  </circle>

  <!-- nodes -->
  {nodes}

  <!-- return path (loop back) -->
  <path d="M {pad + (n-1)*spacing} {H//2 + 30} Q {W//2} {H//2 + 100} {pad} {H//2 + 30}" fill="none" stroke="#1B2A52" stroke-width="1" stroke-dasharray="4 8" opacity="0.4"/>
  <circle r="3" fill="#10B981" filter="url(#g3)" opacity="0.6">
    <animateMotion dur="6s" repeatCount="indefinite">
      <mpath href="#flow"/>
    </animateMotion>
  </circle>

  <!-- label -->
  <text x="{W//2}" y="30" font-family="Arial,sans-serif" font-size="12" fill="#94A3B8" text-anchor="middle" letter-spacing="5">END-TO-END OPERATIONAL PIPELINE</text>
</svg>"""
    save("pipeline.svg", svg)


# ─────────────────────────────────────────────────────
# SCENE 04: THE PROBLEM
# ─────────────────────────────────────────────────────
def gen_problem():
    W, H = 1200, 400
    import random
    random.seed(99)

    # scattered chaotic reports
    dots = ""
    for i in range(25):
        x = random.randint(100, W-100)
        y = random.randint(80, H-60)
        r = random.uniform(3, 8)
        delay = random.uniform(0, 4)
        color = random.choice(["#EF4444", "#F59E0B", "#EF4444", "#DC2626"])
        dots += f"""
    <circle cx="{x}" cy="{y}" r="0" fill="{color}" opacity="0.7">
      <animate attributeName="r" values="0;{r};{r}" dur="0.5s" fill="freeze" begin="{delay:.1f}s"/>
    </circle>"""
        # chaotic connecting lines
        x2 = x + random.randint(-80, 80)
        y2 = y + random.randint(-60, 60)
        dots += f"""
    <line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="0.5" stroke-dasharray="3 5" opacity="0">
      <animate attributeName="opacity" values="0;0.3;0" dur="4s" begin="{delay + 0.5:.1f}s" repeatCount="indefinite"/>
    </line>"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  {DEFS}
  {bg(W, H)}
  {signal_line(W//2, H)}

  <!-- chaotic reports -->
  <g>{dots}
  </g>

  <!-- pulsing warning zones -->
  <circle cx="350" cy="200" r="60" fill="none" stroke="#EF4444" stroke-width="1" opacity="0.3">
    <animate attributeName="r" values="40;70;40" dur="3s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.3;0.1;0.3" dur="3s" repeatCount="indefinite"/>
  </circle>
  <circle cx="800" cy="250" r="50" fill="none" stroke="#F59E0B" stroke-width="1" opacity="0.3">
    <animate attributeName="r" values="30;60;30" dur="4s" repeatCount="indefinite"/>
  </circle>

  <!-- problem labels appearing -->
  <g transform="translate(150, 60)" opacity="0">
    <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="2s"/>
    <rect x="-60" y="-12" width="120" height="24" rx="4" fill="#0A0F1D" stroke="#EF4444" stroke-width="1"/>
    <text x="0" y="4" font-family="Arial,sans-serif" font-size="9" fill="#EF4444" text-anchor="middle">FRAGMENTED DATA</text>
  </g>
  <g transform="translate(500, 340)" opacity="0">
    <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="2.5s"/>
    <rect x="-70" y="-12" width="140" height="24" rx="4" fill="#0A0F1D" stroke="#F59E0B" stroke-width="1"/>
    <text x="0" y="4" font-family="Arial,sans-serif" font-size="9" fill="#F59E0B" text-anchor="middle">QUEUE SATURATION</text>
  </g>
  <g transform="translate(900, 100)" opacity="0">
    <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="3s"/>
    <rect x="-70" y="-12" width="140" height="24" rx="4" fill="#0A0F1D" stroke="#EF4444" stroke-width="1"/>
    <text x="0" y="4" font-family="Arial,sans-serif" font-size="9" fill="#EF4444" text-anchor="middle">NO VERIFICATION</text>
  </g>
  <g transform="translate(700, 350)" opacity="0">
    <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="3.5s"/>
    <rect x="-70" y="-12" width="140" height="24" rx="4" fill="#0A0F1D" stroke="#F59E0B" stroke-width="1"/>
    <text x="0" y="4" font-family="Arial,sans-serif" font-size="9" fill="#F59E0B" text-anchor="middle">SUBJECTIVE DISPATCH</text>
  </g>
</svg>"""
    save("problem.svg", svg)


# ─────────────────────────────────────────────────────
# SCENE 05: THE SOLUTION
# ─────────────────────────────────────────────────────
def gen_solution():
    W, H = 1200, 400
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  {DEFS}
  {bg(W, H)}
  {signal_line(W//2, H)}

  <!-- central unified core -->
  <g transform="translate({W//2},{H//2})">
    <!-- outer ring pulsing -->
    <circle cx="0" cy="0" r="90" fill="none" stroke="#F97316" stroke-width="1.5" opacity="0">
      <animate attributeName="opacity" values="0;0.5;0.3" dur="2s" fill="freeze" begin="1s"/>
      <animate attributeName="r" values="60;90" dur="2s" fill="freeze" begin="1s"/>
    </circle>
    <circle cx="0" cy="0" r="120" fill="none" stroke="#F97316" stroke-width="0.8" stroke-dasharray="4 8" opacity="0">
      <animate attributeName="opacity" values="0;0.3" dur="2s" fill="freeze" begin="1.5s"/>
      <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="20s" repeatCount="indefinite"/>
    </circle>

    <!-- core circle -->
    <circle cx="0" cy="0" r="55" fill="#111C38" stroke="#F97316" stroke-width="3" filter="url(#g2)" opacity="0">
      <animate attributeName="opacity" values="0;1" dur="1s" fill="freeze" begin="0.5s"/>
    </circle>
    <text x="0" y="-5" font-family="Arial,sans-serif" font-size="14" font-weight="bold" fill="#F8FAFC" text-anchor="middle" opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="1.5s"/>CLEANOPS</text>
    <text x="0" y="12" font-family="Arial,sans-serif" font-size="9" fill="#94A3B8" text-anchor="middle" opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="1.8s"/>UNIFIED CORE</text>
  </g>

  <!-- satellite capabilities pulling IN toward core -->
  <g>
    <!-- INTAKE -->
    <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="2s"/>
      <circle cx="200" cy="120" r="20" fill="#111C38" stroke="#10B981" stroke-width="2"/>
      <text x="200" y="124" font-family="Arial,sans-serif" font-size="8" fill="#10B981" text-anchor="middle">INTAKE</text>
      <line x1="220" y1="130" x2="{W//2 - 55}" y2="{H//2}" stroke="#10B981" stroke-width="1" stroke-dasharray="4 6" opacity="0.5"/>
      <circle r="3" fill="#10B981" filter="url(#g3)">
        <animate attributeName="cx" values="220;{W//2 - 55}" dur="2s" repeatCount="indefinite"/>
        <animate attributeName="cy" values="130;{H//2}" dur="2s" repeatCount="indefinite"/>
      </circle>
    </g>
    <!-- TRIAGE -->
    <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="2.4s"/>
      <circle cx="300" cy="320" r="20" fill="#111C38" stroke="#3B82F6" stroke-width="2"/>
      <text x="300" y="324" font-family="Arial,sans-serif" font-size="8" fill="#3B82F6" text-anchor="middle">TRIAGE</text>
      <line x1="318" y1="310" x2="{W//2 - 40}" y2="{H//2 + 40}" stroke="#3B82F6" stroke-width="1" stroke-dasharray="4 6" opacity="0.5"/>
      <circle r="3" fill="#3B82F6" filter="url(#g3)">
        <animate attributeName="cx" values="318;{W//2 - 40}" dur="2.5s" repeatCount="indefinite"/>
        <animate attributeName="cy" values="310;{H//2 + 40}" dur="2.5s" repeatCount="indefinite"/>
      </circle>
    </g>
    <!-- SPATIAL -->
    <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="2.8s"/>
      <circle cx="1000" cy="120" r="20" fill="#111C38" stroke="#8B5CF6" stroke-width="2"/>
      <text x="1000" y="124" font-family="Arial,sans-serif" font-size="8" fill="#8B5CF6" text-anchor="middle">SPATIAL</text>
      <line x1="980" y1="130" x2="{W//2 + 55}" y2="{H//2}" stroke="#8B5CF6" stroke-width="1" stroke-dasharray="4 6" opacity="0.5"/>
      <circle r="3" fill="#8B5CF6" filter="url(#g3)">
        <animate attributeName="cx" values="980;{W//2 + 55}" dur="2.2s" repeatCount="indefinite"/>
        <animate attributeName="cy" values="130;{H//2}" dur="2.2s" repeatCount="indefinite"/>
      </circle>
    </g>
    <!-- AUDIT -->
    <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="3.2s"/>
      <circle cx="900" cy="320" r="20" fill="#111C38" stroke="#F59E0B" stroke-width="2"/>
      <text x="900" y="324" font-family="Arial,sans-serif" font-size="8" fill="#F59E0B" text-anchor="middle">AUDIT</text>
      <line x1="882" y1="310" x2="{W//2 + 40}" y2="{H//2 + 40}" stroke="#F59E0B" stroke-width="1" stroke-dasharray="4 6" opacity="0.5"/>
      <circle r="3" fill="#F59E0B" filter="url(#g3)">
        <animate attributeName="cx" values="882;{W//2 + 40}" dur="2.8s" repeatCount="indefinite"/>
        <animate attributeName="cy" values="310;{H//2 + 40}" dur="2.8s" repeatCount="indefinite"/>
      </circle>
    </g>
  </g>
</svg>"""
    save("solution.svg", svg)


# ─────────────────────────────────────────────────────
# SCENE 06: PRIORITY ENGINE
# ─────────────────────────────────────────────────────
def gen_priority():
    W, H = 1200, 450
    cx, cy = W//2, H//2 + 20
    factors = [
        ("SEVERITY", 0, -1, "#EF4444"),
        ("AGE", 1, 0, "#F59E0B"),
        ("DENSITY", 0, 1, "#3B82F6"),
        ("RECURRENCE", -1, 0, "#8B5CF6"),
    ]
    radius = 140

    factor_elements = ""
    for i, (name, dx, dy, color) in enumerate(factors):
        fx = cx + dx * (radius + 60)
        fy = cy + dy * (radius + 60)
        delay = 0.5 + i * 0.5

        factor_elements += f"""
    <!-- {name} -->
    <g opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="{delay}s"/>
      <circle cx="{fx}" cy="{fy}" r="22" fill="#111C38" stroke="{color}" stroke-width="2"/>
      <text x="{fx}" y="{fy + 4}" font-family="Arial,sans-serif" font-size="8" font-weight="bold" fill="{color}" text-anchor="middle">{name}</text>
      <!-- data stream toward center -->
      <line x1="{fx}" y1="{fy}" x2="{cx}" y2="{cy}" stroke="{color}" stroke-width="1.5" stroke-dasharray="4 6" opacity="0.4"/>
      <circle r="4" fill="{color}" filter="url(#g2)">
        <animate attributeName="cx" values="{fx};{cx}" dur="{2 + i*0.3:.1f}s" repeatCount="indefinite"/>
        <animate attributeName="cy" values="{fy};{cy}" dur="{2 + i*0.3:.1f}s" repeatCount="indefinite"/>
      </circle>
    </g>"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  {DEFS}
  {bg(W, H)}
  {signal_line(W//2, H)}

  <!-- radar background -->
  <g transform="translate({cx},{cy})">
    <circle cx="0" cy="0" r="{radius}" fill="none" stroke="#1B2A52" stroke-width="1"/>
    <circle cx="0" cy="0" r="{radius*2//3}" fill="none" stroke="#1B2A52" stroke-width="0.5" stroke-dasharray="4 4"/>
    <circle cx="0" cy="0" r="{radius//3}" fill="none" stroke="#1B2A52" stroke-width="0.5" stroke-dasharray="2 4"/>
    <line x1="0" y1="-{radius}" x2="0" y2="{radius}" stroke="#1B2A52" stroke-width="0.5" stroke-dasharray="4 4"/>
    <line x1="-{radius}" y1="0" x2="{radius}" y2="0" stroke="#1B2A52" stroke-width="0.5" stroke-dasharray="4 4"/>

    <!-- animated data shape -->
    <polygon points="0,-{int(radius*0.7)} {int(radius*0.8)},0 0,{int(radius*0.5)} -{int(radius*0.6)},0"
             fill="#F97316" fill-opacity="0.15" stroke="#F97316" stroke-width="2" filter="url(#g3)">
      <animate attributeName="points"
               values="0,-{int(radius*0.7)} {int(radius*0.8)},0 0,{int(radius*0.5)} -{int(radius*0.6)},0;
                       0,-{int(radius*0.85)} {int(radius*0.6)},0 0,{int(radius*0.7)} -{int(radius*0.75)},0;
                       0,-{int(radius*0.7)} {int(radius*0.8)},0 0,{int(radius*0.5)} -{int(radius*0.6)},0"
               dur="6s" repeatCount="indefinite"/>
    </polygon>

    <!-- center node -->
    <circle cx="0" cy="0" r="16" fill="#111C38" stroke="#F97316" stroke-width="2.5" filter="url(#g2)"/>
    <text x="0" y="4" font-family="Arial,sans-serif" font-size="7" font-weight="bold" fill="#F97316" text-anchor="middle">SCORE</text>
  </g>

  <!-- factor streams -->
  {factor_elements}

  <!-- output -->
  <g transform="translate({cx},{cy + radius + 90})" opacity="0">
    <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="3s"/>
    <rect x="-50" y="-14" width="100" height="28" rx="14" fill="#F97316" filter="url(#g1)"/>
    <text x="0" y="5" font-family="Arial,sans-serif" font-size="11" font-weight="bold" fill="#FFF" text-anchor="middle">PRIORITY</text>
  </g>

  <text x="{W//2}" y="35" font-family="Arial,sans-serif" font-size="12" fill="#94A3B8" text-anchor="middle" letter-spacing="5">ALGORITHMIC SCORING MATRIX</text>
</svg>"""
    save("priority.svg", svg)


# ─────────────────────────────────────────────────────
# SCENE 07: HOTSPOT CLUSTERING
# ─────────────────────────────────────────────────────
def gen_hotspot():
    W, H = 1200, 450
    import random
    random.seed(77)

    # street grid
    streets = ""
    for i in range(0, W, 80):
        streets += f'<line x1="{i}" y1="60" x2="{i}" y2="{H}" stroke="#1B2A52" stroke-width="0.3" opacity="0.3"/>'
    for i in range(60, H, 60):
        streets += f'<line x1="0" y1="{i}" x2="{W}" y2="{i}" stroke="#1B2A52" stroke-width="0.3" opacity="0.3"/>'

    # individual reports appearing
    reports = ""
    # cluster zone around (450, 250)
    cluster_cx, cluster_cy = 450, 250
    cluster_points = []
    for i in range(8):
        x = cluster_cx + random.randint(-50, 50)
        y = cluster_cy + random.randint(-40, 40)
        cluster_points.append((x, y))
        delay = 0.5 + i * 0.3
        reports += f"""
    <circle cx="{x}" cy="{y}" r="0" fill="#F97316" filter="url(#g3)">
      <animate attributeName="r" values="0;5;4" dur="0.8s" fill="freeze" begin="{delay:.1f}s"/>
    </circle>"""

    # isolated reports
    for i in range(6):
        x = random.choice([random.randint(100, 300), random.randint(700, 1100)])
        y = random.randint(100, H-80)
        delay = 1.5 + i * 0.4
        reports += f"""
    <circle cx="{x}" cy="{y}" r="0" fill="#3B82F6" opacity="0.6">
      <animate attributeName="r" values="0;4;3" dur="0.8s" fill="freeze" begin="{delay:.1f}s"/>
    </circle>"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  {DEFS}
  {bg(W, H)}
  {signal_line(W//2, H)}

  <!-- street grid -->
  {streets}

  <!-- reports -->
  {reports}

  <!-- cluster detection ring -->
  <circle cx="{cluster_cx}" cy="{cluster_cy}" r="0" fill="none" stroke="#F97316" stroke-width="2" opacity="0">
    <animate attributeName="r" values="0;70" dur="1s" fill="freeze" begin="4s"/>
    <animate attributeName="opacity" values="0;0.8" dur="1s" fill="freeze" begin="4s"/>
  </circle>
  <circle cx="{cluster_cx}" cy="{cluster_cy}" r="0" fill="#F97316" opacity="0" filter="url(#soft)">
    <animate attributeName="r" values="0;50" dur="1s" fill="freeze" begin="4s"/>
    <animate attributeName="opacity" values="0;0.1" dur="1s" fill="freeze" begin="4s"/>
  </circle>
  <!-- pulsing ring -->
  <circle cx="{cluster_cx}" cy="{cluster_cy}" r="70" fill="none" stroke="#F97316" stroke-width="1" opacity="0">
    <animate attributeName="opacity" values="0;0.5;0" dur="2s" begin="5s" repeatCount="indefinite"/>
    <animate attributeName="r" values="70;90;70" dur="2s" begin="5s" repeatCount="indefinite"/>
  </circle>

  <!-- hotspot label -->
  <g transform="translate({cluster_cx},{cluster_cy - 85})" opacity="0">
    <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="4.5s"/>
    <rect x="-55" y="-12" width="110" height="24" rx="4" fill="#0A0F1D" stroke="#F97316" stroke-width="1.5"/>
    <text x="0" y="4" font-family="Arial,sans-serif" font-size="10" font-weight="bold" fill="#F97316" text-anchor="middle">HOTSPOT DETECTED</text>
  </g>

  <!-- signal going to operations -->
  <path id="hotpath" d="M {cluster_cx + 70} {cluster_cy} Q {cluster_cx + 200} {cluster_cy} {W - 200} {H//2}" fill="none" stroke="#F97316" stroke-width="1" stroke-dasharray="4 6" opacity="0">
    <animate attributeName="opacity" values="0;0.5" dur="0.5s" fill="freeze" begin="5.5s"/>
  </path>
  <circle r="4" fill="#F97316" filter="url(#g2)" opacity="0">
    <animate attributeName="opacity" values="0;1" dur="0.3s" fill="freeze" begin="5.5s"/>
    <animateMotion dur="2s" begin="5.5s" repeatCount="indefinite"><mpath href="#hotpath"/></animateMotion>
  </circle>

  <!-- operations endpoint -->
  <g transform="translate({W - 200},{H//2})" opacity="0">
    <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="6s"/>
    <circle cx="0" cy="0" r="18" fill="#111C38" stroke="#10B981" stroke-width="2"/>
    <text x="0" y="30" font-family="Arial,sans-serif" font-size="9" fill="#10B981" text-anchor="middle">OPERATIONS</text>
  </g>

  <text x="{W//2}" y="35" font-family="Arial,sans-serif" font-size="12" fill="#94A3B8" text-anchor="middle" letter-spacing="5">GEOSPATIAL INCIDENT CLUSTERING</text>
</svg>"""
    save("hotspot.svg", svg)


# ─────────────────────────────────────────────────────
# SCENE 08: OPERATIONS LIFECYCLE
# ─────────────────────────────────────────────────────
def gen_operations():
    W, H = 1200, 300
    states = ["REPORTED", "PRIORITIZED", "ASSIGNED", "IN PROGRESS", "EVIDENCE", "VERIFIED"]
    colors = ["#94A3B8", "#3B82F6", "#F59E0B", "#F97316", "#8B5CF6", "#10B981"]
    n = len(states)
    pad = 100
    sp = (W - 2*pad) / (n - 1)

    path_d = f"M {pad} {H//2}"
    nodes = ""
    for i, (st, col) in enumerate(zip(states, colors)):
        cx = pad + i * sp
        cy = H // 2
        path_d += f" L {cx} {cy}"
        nodes += f"""
    <g transform="translate({cx},{cy})">
      <rect x="-40" y="-16" width="80" height="32" rx="16" fill="#111C38" stroke="{col}" stroke-width="2"/>
      <text x="0" y="4" font-family="Arial,sans-serif" font-size="8" font-weight="bold" fill="{col}" text-anchor="middle">{st}</text>
    </g>"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  {DEFS}
  {bg(W, H)}
  {signal_line(W//2, H)}

  <!-- track -->
  <path id="optrack" d="{path_d}" fill="none" stroke="#1B2A52" stroke-width="3"/>

  <!-- progressive fill -->
  <path d="{path_d}" fill="none" stroke="#F97316" stroke-width="3" stroke-dasharray="0 2000" filter="url(#g3)">
    <animate attributeName="stroke-dasharray" values="0 2000;2000 2000" dur="6s" repeatCount="indefinite"/>
  </path>

  <!-- traveling case -->
  <g>
    <circle r="8" fill="#F97316" filter="url(#g1)">
      <animateMotion dur="6s" repeatCount="indefinite"><mpath href="#optrack"/></animateMotion>
    </circle>
    <circle r="4" fill="#FFFFFF">
      <animateMotion dur="6s" repeatCount="indefinite"><mpath href="#optrack"/></animateMotion>
    </circle>
  </g>

  {nodes}

  <text x="{W//2}" y="30" font-family="Arial,sans-serif" font-size="12" fill="#94A3B8" text-anchor="middle" letter-spacing="5">STATE-MANAGED AUDIT TRAIL</text>
</svg>"""
    save("operations.svg", svg)


# ─────────────────────────────────────────────────────
# SCENE 09: VERIFICATION LOOP
# ─────────────────────────────────────────────────────
def gen_verification():
    W, H = 1200, 450
    cx, cy = W//2, H//2 + 10
    R = 140

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  {DEFS}
  {bg(W, H)}
  {signal_line(W//2, H)}

  <g transform="translate({cx},{cy})">
    <!-- orbit track -->
    <circle cx="0" cy="0" r="{R}" fill="none" stroke="#1B2A52" stroke-width="2" stroke-dasharray="8 8"/>

    <!-- loop path for animation -->
    <path id="looppath" d="M 0 -{R} A {R} {R} 0 1 1 -0.01 -{R}" fill="none"/>

    <!-- progressive draw -->
    <circle cx="0" cy="0" r="{R}" fill="none" stroke="#10B981" stroke-width="3" stroke-dasharray="0 900" filter="url(#g3)">
      <animate attributeName="stroke-dasharray" values="0 900;880 900" dur="5s" repeatCount="indefinite"/>
    </circle>

    <!-- traveling signal -->
    <circle r="8" fill="#10B981" filter="url(#g1)">
      <animateMotion dur="5s" repeatCount="indefinite"><mpath href="#looppath"/></animateMotion>
    </circle>
    <circle r="3" fill="#FFFFFF">
      <animateMotion dur="5s" repeatCount="indefinite"><mpath href="#looppath"/></animateMotion>
    </circle>

    <!-- center verification icon -->
    <circle cx="0" cy="0" r="45" fill="#111C38" stroke="#10B981" stroke-width="2.5" filter="url(#g2)"/>
    <path d="M -18 0 L -6 12 L 18 -10" fill="none" stroke="#F8FAFC" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>

    <!-- cardinal labels -->
    <text x="0" y="-{R + 20}" font-family="Arial,sans-serif" font-size="10" font-weight="bold" fill="#E2E8F0" text-anchor="middle">1. REPORT SUBMITTED</text>
    <text x="{R + 30}" y="4" font-family="Arial,sans-serif" font-size="10" font-weight="bold" fill="#E2E8F0" text-anchor="start">2. WORK COMPLETED</text>
    <text x="0" y="{R + 30}" font-family="Arial,sans-serif" font-size="10" font-weight="bold" fill="#10B981" text-anchor="middle">3. EVIDENCE VERIFIED</text>
    <text x="-{R + 30}" y="4" font-family="Arial,sans-serif" font-size="10" font-weight="bold" fill="#E2E8F0" text-anchor="end">4. CITIZEN NOTIFIED</text>

    <!-- cardinal nodes -->
    <circle cx="0" cy="-{R}" r="8" fill="#111C38" stroke="#E2E8F0" stroke-width="2"/>
    <circle cx="{R}" cy="0" r="8" fill="#111C38" stroke="#E2E8F0" stroke-width="2"/>
    <circle cx="0" cy="{R}" r="8" fill="#111C38" stroke="#10B981" stroke-width="2"/>
    <circle cx="-{R}" cy="0" r="8" fill="#111C38" stroke="#E2E8F0" stroke-width="2"/>
  </g>

  <text x="{W//2}" y="35" font-family="Arial,sans-serif" font-size="12" fill="#94A3B8" text-anchor="middle" letter-spacing="5">CLOSED VERIFICATION LOOP</text>
</svg>"""
    save("verification.svg", svg)


# ─────────────────────────────────────────────────────
# SCENE 10: ARCHITECTURE
# ─────────────────────────────────────────────────────
def gen_architecture():
    W, H = 1200, 500
    tiers = [
        ("PRESENTATION LAYER", "Mobile &#183; Web &#183; Admin", "#3B82F6", 90),
        ("EDGE / API LAYER", "Routing &#183; Auth &#183; Logic", "#F97316", 180),
        ("INTELLIGENCE", "AI Vision &#183; GIS &#183; Scoring", "#10B981", 270),
        ("PERSISTENCE", "Database &#183; Storage &#183; RLS", "#E2E8F0", 360),
    ]

    tier_elems = ""
    for i, (name, sub, color, y) in enumerate(tiers):
        delay = 0.5 + i * 0.6
        tier_elems += f"""
    <g opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.6s" fill="freeze" begin="{delay}s"/>
      <rect x="200" y="{y}" width="800" height="60" rx="6" fill="#111C38" stroke="{color}" stroke-width="2"/>
      <text x="600" y="{y + 28}" font-family="Arial,sans-serif" font-size="14" font-weight="bold" fill="{color}" text-anchor="middle">{name}</text>
      <text x="600" y="{y + 45}" font-family="Arial,sans-serif" font-size="10" fill="#64748B" text-anchor="middle">{sub}</text>
    </g>"""

    # data flow lines between tiers
    flow_lines = ""
    for i in range(len(tiers) - 1):
        y1 = tiers[i][3] + 60
        y2 = tiers[i+1][3]
        flow_lines += f"""
    <line x1="600" y1="{y1}" x2="600" y2="{y2}" stroke="#1B2A52" stroke-width="2" stroke-dasharray="4 6"/>
    <circle r="4" fill="#F97316" filter="url(#g2)">
      <animate attributeName="cy" values="{y1};{y2}" dur="{1.5 + i*0.3}s" repeatCount="indefinite"/>
      <animate attributeName="cx" values="600;600" dur="{1.5 + i*0.3}s" repeatCount="indefinite"/>
    </circle>"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  {DEFS}
  {bg(W, H)}
  {signal_line(W//2, H)}

  {tier_elems}
  {flow_lines}

  <text x="{W//2}" y="45" font-family="Arial,sans-serif" font-size="12" fill="#94A3B8" text-anchor="middle" letter-spacing="5">N-TIER SYSTEM ARCHITECTURE</text>
</svg>"""
    save("architecture.svg", svg)


# ─────────────────────────────────────────────────────
# SCENE 11: AI ANALYSIS
# ─────────────────────────────────────────────────────
def gen_ai():
    W, H = 1200, 400
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  {DEFS}
  {bg(W, H)}
  {signal_line(W//2, H)}

  <!-- input: report card -->
  <g transform="translate(180, {H//2})" opacity="0">
    <animate attributeName="opacity" values="0;1" dur="0.8s" fill="freeze" begin="0.3s"/>
    <rect x="-80" y="-60" width="160" height="120" rx="6" fill="#142042" stroke="#1B2A52" stroke-width="2"/>
    <!-- image placeholder -->
    <rect x="-65" y="-48" width="130" height="70" rx="3" fill="#0A0F1D"/>
    <text x="0" y="-10" font-family="Arial,sans-serif" font-size="9" fill="#64748B" text-anchor="middle">REPORT IMAGE</text>
    <!-- metadata lines -->
    <rect x="-65" y="30" width="80" height="5" rx="2" fill="#1B2A52"/>
    <rect x="-65" y="40" width="50" height="5" rx="2" fill="#1B2A52"/>
  </g>

  <!-- data path to AI -->
  <path id="aipath" d="M 260 {H//2} L 500 {H//2}" fill="none" stroke="#F97316" stroke-width="1.5" stroke-dasharray="4 6" opacity="0.5"/>
  <circle r="4" fill="#F97316" filter="url(#g2)">
    <animate attributeName="cx" values="260;500" dur="2s" repeatCount="indefinite"/>
    <animate attributeName="cy" values="{H//2};{H//2}" dur="2s" repeatCount="indefinite"/>
  </circle>

  <!-- AI PROCESSING CORE -->
  <g transform="translate({W//2}, {H//2})">
    <!-- analysis grid background -->
    <rect x="-80" y="-80" width="160" height="160" rx="4" fill="#0A0F1D" stroke="#F97316" stroke-width="2" filter="url(#g2)"/>
    <!-- grid lines -->
    <g opacity="0.3">
      <line x1="-80" y1="-40" x2="80" y2="-40" stroke="#F97316" stroke-width="0.5"/>
      <line x1="-80" y1="0" x2="80" y2="0" stroke="#F97316" stroke-width="0.5"/>
      <line x1="-80" y1="40" x2="80" y2="40" stroke="#F97316" stroke-width="0.5"/>
      <line x1="-40" y1="-80" x2="-40" y2="80" stroke="#F97316" stroke-width="0.5"/>
      <line x1="0" y1="-80" x2="0" y2="80" stroke="#F97316" stroke-width="0.5"/>
      <line x1="40" y1="-80" x2="40" y2="80" stroke="#F97316" stroke-width="0.5"/>
    </g>
    <!-- feature nodes activating -->
    <circle cx="-40" cy="-40" r="6" fill="#F97316" opacity="0">
      <animate attributeName="opacity" values="0;0.8;0.3" dur="0.5s" fill="freeze" begin="1.5s"/>
    </circle>
    <circle cx="40" cy="-40" r="6" fill="#F97316" opacity="0">
      <animate attributeName="opacity" values="0;0.8;0.3" dur="0.5s" fill="freeze" begin="1.8s"/>
    </circle>
    <circle cx="0" cy="0" r="8" fill="#F97316" opacity="0">
      <animate attributeName="opacity" values="0;1;0.5" dur="0.5s" fill="freeze" begin="2.1s"/>
    </circle>
    <circle cx="-40" cy="40" r="6" fill="#F97316" opacity="0">
      <animate attributeName="opacity" values="0;0.8;0.3" dur="0.5s" fill="freeze" begin="2.4s"/>
    </circle>
    <circle cx="40" cy="40" r="6" fill="#F97316" opacity="0">
      <animate attributeName="opacity" values="0;0.8;0.3" dur="0.5s" fill="freeze" begin="2.7s"/>
    </circle>

    <!-- scanning line -->
    <line x1="-80" y1="-80" x2="80" y2="-80" stroke="#F97316" stroke-width="2" opacity="0.5">
      <animate attributeName="y1" values="-80;80;-80" dur="3s" repeatCount="indefinite"/>
      <animate attributeName="y2" values="-80;80;-80" dur="3s" repeatCount="indefinite"/>
    </line>

    <text x="0" y="100" font-family="Arial,sans-serif" font-size="12" font-weight="bold" fill="#F97316" text-anchor="middle">AI ANALYSIS ENGINE</text>
  </g>

  <!-- output path -->
  <path d="M 680 {H//2} L 900 {H//2}" fill="none" stroke="#10B981" stroke-width="1.5" stroke-dasharray="4 6" opacity="0.5"/>
  <circle r="4" fill="#10B981" filter="url(#g2)">
    <animate attributeName="cx" values="680;900" dur="2s" repeatCount="indefinite"/>
    <animate attributeName="cy" values="{H//2};{H//2}" dur="2s" repeatCount="indefinite"/>
  </circle>

  <!-- output cards -->
  <g transform="translate(970, {H//2})">
    <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="3s"/>
      <rect x="-60" y="-70" width="120" height="30" rx="4" fill="#111C38" stroke="#10B981" stroke-width="1.5"/>
      <text x="0" y="-51" font-family="Arial,sans-serif" font-size="9" font-weight="bold" fill="#10B981" text-anchor="middle">CLASSIFICATION</text>
    </g>
    <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="3.4s"/>
      <rect x="-60" y="-30" width="120" height="30" rx="4" fill="#111C38" stroke="#F59E0B" stroke-width="1.5"/>
      <text x="0" y="-11" font-family="Arial,sans-serif" font-size="9" font-weight="bold" fill="#F59E0B" text-anchor="middle">SEVERITY</text>
    </g>
    <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="3.8s"/>
      <rect x="-60" y="10" width="120" height="30" rx="4" fill="#111C38" stroke="#3B82F6" stroke-width="1.5"/>
      <text x="0" y="29" font-family="Arial,sans-serif" font-size="9" font-weight="bold" fill="#3B82F6" text-anchor="middle">RECOMMENDATION</text>
    </g>
  </g>

  <!-- Human-in-the-Loop indicator -->
  <g transform="translate({W//2}, {H - 40})" opacity="0">
    <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="4s"/>
    <rect x="-100" y="-12" width="200" height="24" rx="4" fill="#0A0F1D" stroke="#10B981" stroke-width="1"/>
    <text x="0" y="4" font-family="Arial,sans-serif" font-size="9" fill="#10B981" text-anchor="middle">HUMAN OPERATOR MAKES FINAL DECISION</text>
  </g>

  <text x="{W//2}" y="35" font-family="Arial,sans-serif" font-size="12" fill="#94A3B8" text-anchor="middle" letter-spacing="5">COMPUTATIONAL VISION PIPELINE</text>
</svg>"""
    save("ai-analysis.svg", svg)


# ─────────────────────────────────────────────────────
# SCENE 12: TEAM NETWORK
# ─────────────────────────────────────────────────────
def gen_team():
    W, H = 1200, 400
    import math
    cx, cy = W//2, H//2 + 10
    R = 140
    n_members = 9

    nodes = ""
    # center: leader
    nodes += f"""
    <circle cx="{cx}" cy="{cy}" r="22" fill="#111C38" stroke="#F97316" stroke-width="3" filter="url(#g2)"/>
    <text x="{cx}" y="{cy + 4}" font-family="Arial,sans-serif" font-size="8" font-weight="bold" fill="#F97316" text-anchor="middle">LEAD</text>"""

    # members around
    for i in range(n_members):
        angle = (2 * math.pi * i / n_members) - math.pi/2
        mx = cx + R * math.cos(angle)
        my = cy + R * math.sin(angle)
        delay = 0.3 + i * 0.2
        colors = ["#3B82F6", "#10B981", "#8B5CF6", "#F59E0B", "#3B82F6", "#10B981", "#8B5CF6", "#F59E0B", "#3B82F6"]
        col = colors[i]

        nodes += f"""
    <!-- member {i+1} -->
    <g opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.4s" fill="freeze" begin="{delay:.1f}s"/>
      <line x1="{cx}" y1="{cy}" x2="{mx:.0f}" y2="{my:.0f}" stroke="#1B2A52" stroke-width="1.5"/>
      <circle cx="{mx:.0f}" cy="{my:.0f}" r="14" fill="#111C38" stroke="{col}" stroke-width="2"/>
    </g>"""
        # pulse from leader to member
        nodes += f"""
    <circle r="3" fill="#F97316" filter="url(#g3)" opacity="0">
      <animate attributeName="opacity" values="0;0.8;0" dur="{2 + i*0.2:.1f}s" begin="{1 + i*0.3:.1f}s" repeatCount="indefinite"/>
      <animate attributeName="cx" values="{cx};{mx:.0f}" dur="{2 + i*0.2:.1f}s" begin="{1 + i*0.3:.1f}s" repeatCount="indefinite"/>
      <animate attributeName="cy" values="{cy};{my:.0f}" dur="{2 + i*0.2:.1f}s" begin="{1 + i*0.3:.1f}s" repeatCount="indefinite"/>
    </circle>"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  {DEFS}
  {bg(W, H)}
  {signal_line(W//2, H)}

  <!-- connection ring -->
  <circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="#1B2A52" stroke-width="1" stroke-dasharray="6 10">
    <animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="40s" repeatCount="indefinite"/>
  </circle>

  {nodes}

  <!-- label appearing -->
  <g opacity="0">
    <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="3s"/>
    <text x="{cx}" y="{cy + R + 40}" font-family="Arial,sans-serif" font-size="16" font-weight="bold" fill="#F97316" text-anchor="middle" letter-spacing="3">TEAM 21</text>
  </g>

  <text x="{W//2}" y="35" font-family="Arial,sans-serif" font-size="12" fill="#94A3B8" text-anchor="middle" letter-spacing="5">COLLABORATIVE ENGINEERING NETWORK</text>
</svg>"""
    save("team.svg", svg)


# ─────────────────────────────────────────────────────
# SCENE 13: ACADEMIC CONTEXT
# ─────────────────────────────────────────────────────
def gen_academic():
    W, H = 1200, 400
    cx = W // 2
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  {DEFS}
  {bg(W, H)}
  {signal_line(cx, H)}

  <!-- document frame -->
  <g transform="translate({cx}, {H//2})">
    <!-- outer glow -->
    <rect x="-220" y="-140" width="440" height="280" rx="6" fill="#0A0F1D" stroke="#F97316" stroke-width="1.5" filter="url(#g3)" opacity="0">
      <animate attributeName="opacity" values="0;1" dur="1s" fill="freeze" begin="0.5s"/>
    </rect>

    <!-- header bar -->
    <rect x="-220" y="-140" width="440" height="40" fill="#111C38" rx="6" opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="1s"/>
    </rect>
    <text x="0" y="-114" font-family="Arial,sans-serif" font-size="12" font-weight="bold" fill="#F97316" text-anchor="middle" letter-spacing="3" opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="1.2s"/>
      GRADUATION PROJECT DOSSIER
    </text>

    <!-- content lines appearing sequentially -->
    <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="1.8s"/>
      <text x="0" y="-70" font-family="Arial,sans-serif" font-size="16" font-weight="bold" fill="#F8FAFC" text-anchor="middle">Egyptian E-Learning University (EELU)</text>
    </g>
    <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="2.2s"/>
      <text x="0" y="-48" font-family="Arial,sans-serif" font-size="12" fill="#94A3B8" text-anchor="middle">Faculty of Computers and Information Technology</text>
    </g>
    <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="2.5s"/>
      <text x="0" y="-30" font-family="Arial,sans-serif" font-size="11" fill="#64748B" text-anchor="middle">Fayoum Center &#183; Academic Year 2026-2027</text>
    </g>

    <!-- divider -->
    <line x1="-150" y1="-10" x2="150" y2="-10" stroke="#F97316" stroke-width="1" opacity="0">
      <animate attributeName="opacity" values="0;0.6" dur="0.5s" fill="freeze" begin="2.8s"/>
    </line>

    <!-- Project title -->
    <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="3s"/>
      <text x="0" y="15" font-family="Arial,sans-serif" font-size="11" fill="#E2E8F0" text-anchor="middle" font-style="italic">An AI-Powered Application for Waste Reporting</text>
      <text x="0" y="32" font-family="Arial,sans-serif" font-size="11" fill="#E2E8F0" text-anchor="middle" font-style="italic">and Smart Cleaning Management</text>
    </g>

    <!-- Supervisors -->
    <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="3.5s"/>
      <text x="0" y="65" font-family="Arial,sans-serif" font-size="10" fill="#94A3B8" text-anchor="middle" letter-spacing="2">SUPERVISION</text>
    </g>
    <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="3.8s"/>
      <text x="0" y="85" font-family="Arial,sans-serif" font-size="12" font-weight="bold" fill="#F8FAFC" text-anchor="middle">Dr. Yasser Abdelhamid Abdelfattah</text>
    </g>
    <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" fill="freeze" begin="4.1s"/>
      <text x="0" y="105" font-family="Arial,sans-serif" font-size="12" font-weight="bold" fill="#F8FAFC" text-anchor="middle">Eng. George Hany Milad</text>
    </g>

    <!-- seal/stamp effect -->
    <circle cx="170" cy="95" r="25" fill="none" stroke="#F97316" stroke-width="2" opacity="0">
      <animate attributeName="opacity" values="0;0.5" dur="0.5s" fill="freeze" begin="4.5s"/>
    </circle>
    <text x="170" y="99" font-family="Arial,sans-serif" font-size="8" font-weight="bold" fill="#F97316" text-anchor="middle" opacity="0">
      <animate attributeName="opacity" values="0;0.5" dur="0.5s" fill="freeze" begin="4.5s"/>
      TEAM 21
    </text>
  </g>
</svg>"""
    save("academic.svg", svg)


# ─────────────────────────────────────────────────────
# SCENE 14: FINAL VISION
# ─────────────────────────────────────────────────────
def gen_vision():
    W, H = 1200, 500
    cx = W // 2
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  {DEFS}
  {bg(W, H)}

  <!-- city silhouette -->
  {city_silhouette(W, H - 60, 0.08)}

  <!-- full pipeline path across the bottom -->
  <path id="visionpath" d="M 100 {H - 100} L 300 {H - 100} L 500 {H - 100} L 700 {H - 100} L 900 {H - 100} L 1100 {H - 100}"
        fill="none" stroke="#1B2A52" stroke-width="2" stroke-dasharray="6 6"/>
  <!-- progressive illumination -->
  <path d="M 100 {H - 100} L 300 {H - 100} L 500 {H - 100} L 700 {H - 100} L 900 {H - 100} L 1100 {H - 100}"
        fill="none" stroke="#F97316" stroke-width="3" filter="url(#g1)" stroke-dasharray="0 2000">
    <animate attributeName="stroke-dasharray" values="0 2000;2000 2000" dur="4s" fill="freeze" begin="1s"/>
  </path>

  <!-- pipeline nodes -->
  <g transform="translate(100,{H - 100})">
    <circle cx="0" cy="0" r="10" fill="#111C38" stroke="#F97316" stroke-width="2"/>
    <text x="0" y="25" font-family="Arial,sans-serif" font-size="9" fill="#94A3B8" text-anchor="middle">REPORT</text>
  </g>
  <g transform="translate(300,{H - 100})">
    <circle cx="0" cy="0" r="10" fill="#111C38" stroke="#F97316" stroke-width="2"/>
    <text x="0" y="25" font-family="Arial,sans-serif" font-size="9" fill="#94A3B8" text-anchor="middle">AI</text>
  </g>
  <g transform="translate(500,{H - 100})">
    <circle cx="0" cy="0" r="10" fill="#111C38" stroke="#F97316" stroke-width="2"/>
    <text x="0" y="25" font-family="Arial,sans-serif" font-size="9" fill="#94A3B8" text-anchor="middle">PRIORITY</text>
  </g>
  <g transform="translate(700,{H - 100})">
    <circle cx="0" cy="0" r="10" fill="#111C38" stroke="#F97316" stroke-width="2"/>
    <text x="0" y="25" font-family="Arial,sans-serif" font-size="9" fill="#94A3B8" text-anchor="middle">ACTION</text>
  </g>
  <g transform="translate(900,{H - 100})">
    <circle cx="0" cy="0" r="10" fill="#111C38" stroke="#10B981" stroke-width="2"/>
    <text x="0" y="25" font-family="Arial,sans-serif" font-size="9" fill="#10B981" text-anchor="middle">VERIFIED</text>
  </g>
  <g transform="translate(1100,{H - 100})">
    <circle cx="0" cy="0" r="10" fill="#10B981" filter="url(#g2)"/>
  </g>

  <!-- traveling signal -->
  <circle r="6" fill="#F97316" filter="url(#g1)">
    <animateMotion dur="4s" repeatCount="indefinite"><mpath href="#visionpath"/></animateMotion>
  </circle>

  <!-- BOSS acknowledging the system -->
  {boss_character(cx, 200, "acknowledge", 1.6)}

  <!-- ripple from boss -->
  <circle cx="{cx}" cy="200" r="60" fill="none" stroke="#F97316" stroke-width="1" opacity="0">
    <animate attributeName="r" values="60;200" dur="4s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.4;0" dur="4s" repeatCount="indefinite"/>
  </circle>

  <!-- title -->
  <text x="{cx}" y="60" font-family="Arial Black,Arial,sans-serif" font-size="40" font-weight="900" fill="#F8FAFC" text-anchor="middle" letter-spacing="10" opacity="0">
    <animate attributeName="opacity" values="0;1" dur="1.5s" fill="freeze" begin="2s"/>
    CLEANOPS
  </text>
  <text x="{cx}" y="85" font-family="Arial,sans-serif" font-size="14" fill="#F97316" text-anchor="middle" letter-spacing="4" opacity="0">
    <animate attributeName="opacity" values="0;1" dur="1s" fill="freeze" begin="3s"/>
    FROM CITIZEN REPORTS TO VERIFIED ACTION
  </text>
</svg>"""
    save("vision.svg", svg)


# ─────────────────────────────────────────────────────
# TRANSITION DIVIDER
# ─────────────────────────────────────────────────────
def gen_transition():
    W, H = 1200, 70
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  {DEFS}
  <rect width="{W}" height="{H}" fill="url(#bgG)"/>
  <rect width="{W}" height="{H}" fill="url(#grid)"/>

  <!-- signal line continues -->
  <line x1="{W//2}" y1="0" x2="{W//2}" y2="{H}" stroke="url(#oG)" stroke-width="2" opacity="0.6"/>

  <!-- center node -->
  <circle cx="{W//2}" cy="{H//2}" r="5" fill="#F97316" filter="url(#g2)">
    <animate attributeName="r" values="5;8;5" dur="2s" repeatCount="indefinite"/>
  </circle>

  <!-- horizontal accent lines -->
  <line x1="{W//2 - 100}" y1="{H//2}" x2="{W//2 - 15}" y2="{H//2}" stroke="#1B2A52" stroke-width="1"/>
  <line x1="{W//2 + 15}" y1="{H//2}" x2="{W//2 + 100}" y2="{H//2}" stroke="#1B2A52" stroke-width="1"/>

  <!-- traveling particle -->
  <circle r="3" fill="#FFFFFF" filter="url(#g3)">
    <animate attributeName="cy" values="0;{H}" dur="1.5s" repeatCount="indefinite"/>
    <animate attributeName="cx" values="{W//2};{W//2}" dur="1.5s" repeatCount="indefinite"/>
  </circle>
</svg>"""
    save("transition.svg", svg)


# ─────────────────────────────────────────────────────
# GENERATE ALL
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating CleanOps Cinematic SVGs...")
    gen_hero()
    gen_portal()
    gen_pipeline()
    gen_problem()
    gen_solution()
    gen_priority()
    gen_hotspot()
    gen_operations()
    gen_verification()
    gen_architecture()
    gen_ai()
    gen_team()
    gen_academic()
    gen_vision()
    gen_transition()
    print(f"\nAll assets generated in: {BASE}")
