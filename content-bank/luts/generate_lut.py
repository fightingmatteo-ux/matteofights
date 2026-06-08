"""
Generate matteofights-v1.cube
Warm gritty look for Rec.709 footage (applied after camera input transform in DaVinci):
  - Lifted blacks (no crush)
  - S-curve contrast punch
  - Warm grade: boost red, reduce blue
  - Orange midtone push (skin tones)
  - Slight midtone saturation boost
"""

LUT_SIZE = 33

def s_curve(x, strength=0.18):
    """Darkens shadows, brightens highlights — adds punch."""
    return x + strength * x * (1 - x) * (2 * x - 1)

def clamp(x):
    return max(0.0, min(1.0, x))

def transform(r, g, b):
    # 1. Lift blacks — prevent shadow crush
    lift = 0.03
    r = lift + (1 - lift) * r
    g = lift + (1 - lift) * g
    b = lift + (1 - lift) * b

    # 2. S-curve contrast
    r = s_curve(r, 0.18)
    g = s_curve(g, 0.18)
    b = s_curve(b, 0.18)

    # 3. Warm grade: boost red, pull blue
    r = r * 1.035
    b = b * 0.91

    # 4. Orange midtone push (targets skin tones)
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    midtone = max(0.0, 1.0 - abs(luma - 0.45) / 0.35)
    warmth  = max(0.0, r - b)
    push = midtone * warmth * 0.04
    r = r + push * 0.6
    g = g + push * 0.15
    b = b - push * 0.25

    # 5. Midtone saturation lift
    luma2 = 0.2126 * r + 0.7152 * g + 0.0722 * b
    sat = max(0.0, 1.0 - abs(luma2 - 0.5) / 0.4) * 0.06
    r = luma2 + (r - luma2) * (1 + sat)
    g = luma2 + (g - luma2) * (1 + sat)
    b = luma2 + (b - luma2) * (1 + sat)

    return clamp(r), clamp(g), clamp(b)

def generate():
    step = 1.0 / (LUT_SIZE - 1)
    lines = [
        'TITLE "matteofights-v1"',
        f'LUT_3D_SIZE {LUT_SIZE}',
        'DOMAIN_MIN 0.0 0.0 0.0',
        'DOMAIN_MAX 1.0 1.0 1.0',
        '',
    ]
    # .cube order: R outer, G middle, B inner (B changes fastest)
    for ri in range(LUT_SIZE):
        for gi in range(LUT_SIZE):
            for bi in range(LUT_SIZE):
                ro, go, bo = transform(ri * step, gi * step, bi * step)
                lines.append(f'{ro:.6f} {go:.6f} {bo:.6f}')
    return '\n'.join(lines)

if __name__ == '__main__':
    import os
    out = os.path.join(os.path.dirname(__file__), 'matteofights-v1.cube')
    print('Generating 33x33x33 LUT...')
    content = generate()
    with open(out, 'w') as f:
        f.write(content)
    print(f'Done → {out}')
    print(f'Entries: {LUT_SIZE**3}')
