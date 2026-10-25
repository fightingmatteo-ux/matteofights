# Ep 2 b-roll: Lomachenko fight tape, line by line

Footage: official Top Rank Boxing uploads (get_footage.sh), on the `media` release as `loma-<fight>-toprank.mp4`.
Claude picks the exact frames after watching them; this file says what each clip must SHOW, so no clip is decoration.

## Rules (fewer clips, the right ones, protects you)
- **Short and transformed.** Each clip 1 to 3 s, about 15 s of fight footage in total across 4 fights. Every clip has
  our commentary on it (voice + graphics): this is a breakdown, not a highlight reel.
- **Muted.** Never the broadcast audio or commentary. Our voice + a quiet bed only.
- **Shown as "tape":** the full 16:9 frame in a panel inside the vertical reel (both men's feet visible), never
  cropped to a face. Freeze frames and slow motion count as our analysis.
- **Credit in the caption:** "Fight footage: Top Rank Boxing." No logo covering, no watermark removal.
- If Instagram mutes or claims it anyway, the fallback cut swaps the tape for Matteo's own demo shots (already on the
  shot list), so the reel still works.

## Clip map (variant C order; A and B open on their own hook clip)

| Line (spoken) | Clip must show | Source to search | Graphic, timed to the word |
|---|---|---|---|
| Hook A "Four straight opponents quit on their stool" | An opponent on the stool, the corner waving it off / the ref signalling the end | Rigondeaux (after R6), Walters (after R7), Marriaga (after R7); the 4th (Sosa, after R9) isn't downloaded, so 3 shots + the "4" lands on Loma | Counter "1 → 2 → 3 → 4" ticking per stool shot, word **stool** hits on the last |
| Hook B "Always getting pushed to the ropes?" | An opponent with his back on the ropes while Loma has the angle | any | Red rope line glows under the trapped man |
| Hook C "Most boxers move back. Lomachenko moves around." | Split: an opponent retreating straight back (left) / Loma stepping around (right) | Linares or Walters | Arrows: straight red arrow back vs curved white arrow around, drawn on "back" / "around" |
| "They just couldn't find him." | Opponent throws, Loma is already gone, the punch hits air | any, best clean miss | Freeze on the miss, ring on the empty spot |
| "When we get pressured, we step back. Back is where the ropes are." | Matteo's own demo: backing into the corner (filmed) | own footage | Red X on the corner |
| "Loma steps around. A small pivot off their lead foot" | THE pivot: Loma's lead foot outside the opponent's lead foot, a pivot, he ends at an angle | best clean pivot in all 4 fights, wide angle with both men's feet in frame | Circle the opponent's lead foot on "lead foot", trail the pivot path in white, slow motion 0.5x for the pivot only |
| "...and suddenly they're facing nothing." | Same clip continued: opponent facing the spot Loma left | same clip | Freeze, opponent's facing line drawn as an arrow into empty canvas |
| "And here's the part that breaks people." | Opponent turning, frustrated, or shaking his head | any | Music drops out, slow push |
| "Now he can hit them. To hit him back, they have to turn first." | Loma lands from the angle while the opponent is still turning | ideally the same pivot sequence | Card: `they have to **TURN**` (slam) right after the punch lands |
| (optional) "First time I tried it in sparring..." | Matteo's own pivot demo | own footage | none |
| Pearl "Don't move back. Move around." | Back on Matteo's face (no tape) | | white card, keyword AROUND |

## What Claude checks before locking a clip
- The move on screen is the move the line names, at the moment the word is said (not a nearby exchange).
- Feet visible for any footwork line.
- No clip longer than 3 s; nothing from the same exchange twice.
- Stool shots: the corner/ref actually stopping it, not just a man sitting between rounds of a fight he continued.
