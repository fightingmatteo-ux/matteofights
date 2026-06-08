"""
Generate matteofights-v1.cube
Mix of warm-gritty (B) + red/black high contrast (C):
  - Deep near-black shadows with warm-red tint (not cold/blue)
  - High contrast S-curve (fight poster punch)
  - Strong red grade, hard blue reduction
  - Orange skin tone push in midtones
  - Shadows trend toward dark red-brown (not neutral grey)
"""

LUT_SIZE = 33

def s_curve(x, strength=0.28):
    """Darkens shadows, brightens highlights — adds punch."""
    return x + strength * x * (1 - x) * (2 * x - 1)

def clamp(x):
    return max(0.0, min(1.0, x))

def transform(r, g, b):
    # 1. Lift blacks slightly — deep but not fully crushed
    lift = 0.015
    r = lift + (1 - lift) * r
    g = lift + (1 - lift) * g
    b = lift + (1 - lift) * b

    # 2. High contrast S-curve — fight poster punch
    r = s_curve(r, 0.28)
    g = s_curve(g, 0.28)
    b = s_curve(b, 0.28)

    # 3. Strong warm-red grade: hard red boost, hard blue pull
    r = r * 1.07
    b = b * 0.84

    # 4. Shadow red tint — dark areas trend toward deep red-brown, not grey
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    shadow = max(0.0, 1.0 - luma / 0.25)  # only affects very dark regions
    r = r + shadow * 0.018
    b = b - shadow * 0.015

    # 5. Orange midtone push (skin tones — warm doc side of the blend)
    luma2 = 0.2126 * r + 0.7152 * g + 0.0722 * b
    midtone = max(0.0, 1.0 - abs(luma2 - 0.45) / 0.35)
    warmth  = max(0.0, r - b)
    push = midtone * warmth * 0.055
    r = r + push * 0.6
    g = g + push * 0.1
    b = b - push * 0.3

    # 6. Saturation boost in midtones — makes the grade pop
    luma3 = 0.2126 * r + 0.7152 * g + 0.0722 * b
    sat = max(0.0, 1.0 - abs(luma3 - 0.5) / 0.4) * 0.09
    r = luma3 + (r - luma3) * (1 + sat)
    g = luma3 + (g - luma3) * (1 + sat)
    b = luma3 + (b - luma3) * (1 + sat)

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
