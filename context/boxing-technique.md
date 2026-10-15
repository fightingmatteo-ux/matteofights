# What good technique looks like (for picking footage)

_Used to grade clip moments for reels: `production/listicles/moment-sheets/` → `moments.json`. The question is not
"is he moving" but "would a coach and a fighter watching this think he can fight?"_

## Every frame
- **In frame:** whole body visible (head to feet) or a clean waist-up shot; fighter fills a good part of the frame,
  sharp, not cut off, nobody (and no dog) walking through.
- **Stance:** feet about shoulder width or a bit wider, staggered (lead foot forward), weight between the feet,
  knees soft. Not square, not crossed, not flat-footed and stiff.
- **Guard:** between strikes both hands are up by the face, rear hand by the cheek/chin, lead hand in front at eye
  height, elbows in by the ribs. Hands at the chest or waist = bad (unless it's clearly a Muay Thai long guard).
- **Chin and eyes:** chin tucked, eyes on the target. Not looking at the floor or the phone.

## Strikes (what makes them look sharp)
- **Jab:** straight from the guard, full extension, shoulder up to protect the chin, rear hand stays home, snaps back.
- **Cross:** rear foot pivots, hip and shoulder rotate through, full extension, lead hand back to the face.
- **Hook:** elbow up near shoulder height, arm bent ~90°, pivot on the lead foot, rotation from the hips.
- **Uppercut:** short, legs and hips drive it, not a wind-up from the waist.
- **Teep / roundhouse (Muay Thai):** turn the standing foot, hip through, kick with the shin, arm swings down for
  counterbalance, guard returns, lands back in stance. Balanced from start to finish.
- **Knees / clinch:** hips forward, posture tall, hands controlling the head.
- Combos flow and the fighter ends **back in stance with hands up**. Every strike returns.

## Footwork and rhythm
- Light on the balls of the feet, small steps, angles off after combos, never crossing the feet.
- Moves with intent: in, strike, out. Not bouncing aimlessly or walking around.

## Instant reject
Resting, walking, talking, laughing, fixing gloves/wraps/phone, looking at the camera, dropping both hands for
long, off-balance or falling-in strikes, flailing arms with no form, half-speed pawing, someone else in focus,
blurry or dark footage, the end of the clip where he walks toward the phone.

## What tends to look best on a reel
1. A clean 2-3 punch combo or a combo that ends with a kick, then hands back up.
2. Sharp pad or bag work with visible snap (bag moves, pads pop).
3. Controlled sparring exchange where he lands or slips cleanly.
4. Fast footwork with the guard up.
Rank moments in that order when several are good.

## The pose check (tools/listicle/technique.py)
Each moment on the sheet also shows a pose check from body tracking: `guard` (share of frames with the hands up
between strikes), `strikes` (arms reaching full extension), `stance` (feet apart, head between them). It vetoes the
obvious failures in red (not visible enough, too small, walks up to the camera, hands down most of the time,
barely moving). From one phone angle its numbers are rough: use them as a second opinion, never instead of
looking. A vetoed moment can still be good (say so in notes) and a passed one can still be bad.
