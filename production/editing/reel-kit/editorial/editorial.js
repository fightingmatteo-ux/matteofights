// Editorial motion for the PLAN that plan.py writes.
//   Editorial.animate(tl, PLAN, { cam: "#cam-inner", shake: "#cam" })
// Words come into focus (blur -> sharp, ~0.3 s), phrases dissolve into blur while the next focuses in, and each
// keyword gets an effect that means the word (FX). Everything is seeded/deterministic so renders repeat exactly.
window.Editorial = {
  animate(tl, P, o = {}) {
    const IN = 0.3, OUT = 0.18;
    const q = (id) => "#" + id;
    const chars = (id) => Array.from(document.querySelectorAll("#" + id + " .ed-c"));
    const seed = (s) => { let h = 2166136261; for (const ch of s) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return h >>> 0; };
    const rng = (s) => { let a = seed(s); return () => { a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; };
    const SHADOW = "0px 2px 6px rgba(0,0,0,0.45), 0px 6px 28px rgba(0,0,0,0.35)";
    const NOSHADOW = "0px 0px 0px rgba(0,0,0,0), 0px 0px 0px rgba(0,0,0,0)";
    const shake = o.shake || "#cam";

    const focusIn = (sel, t, d = IN, from = {}) =>
      tl.fromTo(sel, { opacity: 0, filter: "blur(14px)", scale: 1.04, ...from },
        { opacity: 1, filter: "blur(0px)", scale: 1, x: 0, y: 0, duration: d, ease: "power2.out" }, Math.max(0, t));
    const show = (sel, t) => tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: 0.01 }, Math.max(0, t));
    const punchCam = (t, a) => {
      tl.fromTo(shake, { scale: 1 }, { scale: 1 + a, duration: 0.06, ease: "power2.out", immediateRender: false }, t);
      tl.to(shake, { scale: 1, duration: 0.2, ease: "power2.out" }, t + 0.06);
    };
    const flash = (t, a) => { if (document.querySelector("#ed-flash"))
      tl.fromTo("#ed-flash", { opacity: a }, { opacity: 0, duration: 0.22, ease: "power2.out", immediateRender: false }, t); };

    const FX = {
      // default: a slower, deeper focus pull than the small words
      focus(id, t) { focusIn(q(id), t - 0.04, 0.36, { scale: 1.12, filter: "blur(20px)" }); },

      // one / two / three: a giant outlined numeral swells behind the word and fades
      count(id, t) {
        focusIn(q(id), t - 0.04, 0.32, { scale: 1.15 });
        const g = q(id) + " .ed-ghost";
        tl.fromTo(g, { opacity: 0, scale: 1.7, xPercent: -50, yPercent: -50 }, { opacity: 0.4, scale: 1, xPercent: -50, yPercent: -50, duration: 0.55, ease: "expo.out" }, t - 0.04);
        tl.to(g, { opacity: 0, scale: 0.9, duration: 0.6, ease: "sine.in" }, t + 0.7);
      },

      // jab: the word is thrown in from the side, overshoots like a straight punch, the camera takes the hit
      jab(id, t) {
        tl.fromTo(q(id), { opacity: 0, x: -620, skewX: -32, scaleX: 1.4, filter: "blur(16px)" },
          { opacity: 1, x: 30, skewX: 0, scaleX: 1, filter: "blur(0px)", duration: 0.18, ease: "power3.out" }, t - 0.16);
        tl.to(q(id), { x: 0, duration: 0.18, ease: "power2.out" }, t + 0.02);
        punchCam(t + 0.02, 0.03);
      },

      // caught: lands hard, shakes, white flash: getting hit
      impact(id, t) {
        tl.fromTo(q(id), { opacity: 0, scale: 1.9, filter: "blur(10px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.1, ease: "power4.in" }, t - 0.1);
        [18, -14, 11, -7, 4, -2, 0].forEach((x, k) => tl.set(q(id), { x, rotation: x * 0.2 }, t + k * 0.035));
        flash(t, 0.3); punchCam(t, 0.04);
      },

      // relax: letters start packed tight and breathe out to their places, then the word floats
      exhale(id, t) {
        show(q(id), t - 0.06);
        const cs = chars(id), mid = (cs.length - 1) / 2;
        cs.forEach((c, i) => tl.fromTo(c, { x: (mid - i) * 16, opacity: 0, filter: "blur(8px)" },
          { x: 0, opacity: 1, filter: "blur(0px)", duration: 0.95, ease: "sine.out" }, t - 0.06));
        tl.fromTo(q(id), { y: 0 }, { y: -10, duration: 1.3, ease: "sine.inOut", immediateRender: false }, t);
      },

      // information: letters scramble through glyphs and lock in left to right
      decode(id, t) {
        show(q(id), t - 0.03);
        const cs = chars(id), orig = cs.map((c) => c.textContent), G = "#%&@$*+=?<>/01234567890abcdefxyz";
        const st = { p: 0 };
        tl.fromTo(st, { p: 0 }, { p: 1, duration: 0.35, ease: "none", onUpdate() {
          cs.forEach((c, i) => { c.textContent = st.p >= (i + 1) / cs.length ? orig[i] : G[(Math.floor(st.p * 30) + i * 7) % G.length]; });
        } }, t - 0.03);
      },

      // reset: the letters are scattered, then rewind back into place and snap (chromatic ghost collapses)
      rewind(id, t, slam, card) {
        show(q(id), t - 0.46);
        const r = rng(id), cs = chars(id).reverse();
        cs.forEach((c, k) => tl.fromTo(c, { x: (r() - 0.5) * 560, y: (r() - 0.5) * 320, rotation: (r() - 0.5) * 100, opacity: 0, filter: "blur(10px)" },
          { x: 0, y: 0, rotation: 0, opacity: 1, filter: "blur(0px)", duration: 0.42, ease: "expo.in" }, t - 0.46 + k * 0.012));
        tl.fromTo(q(id), { textShadow: "-30px 0px 0px rgba(0,210,255,0.7), 30px 0px 0px rgba(255,0,80,0.7)" },
          { textShadow: card ? NOSHADOW : SHADOW, duration: 0.5, ease: "expo.in" }, t - 0.46);
        tl.fromTo(q(id), { scale: slam ? 1.5 : 1.14 }, { scale: 1, duration: 0.2, ease: "power3.out", immediateRender: false }, t + 0.03);
        if (slam) { flash(t + 0.03, 0.25); punchCam(t + 0.03, 0.035); }
      },

      // freeze: arrives ice-blue and shivering, then thaws to red
      freeze(id, t) {
        focusIn(q(id), t - 0.04, 0.3, { scale: 1.1 });
        tl.fromTo(q(id), { color: "#BFEFFF" }, { color: "#E8112D", duration: 0.7, ease: "sine.in" }, t + 0.25);
        [3, -3, 2, -2, 1, 0].forEach((x, k) => tl.set(q(id), { x }, t + 0.05 + k * 0.04));
      },
    };
    const keyIn = (w, card) => (FX[w.fx] || FX.focus)(w.id, w.s, w.slam, card);

    // captions: phrase appears, words focus in on the voice, phrase dissolves while the next focuses in
    P.phrases.forEach((ph) => {
      const t0 = Math.max(0, ph.t0 - 0.06);
      tl.fromTo("#" + ph.id, { opacity: 0, filter: "blur(0px)", scale: 1 }, { opacity: 1, duration: 0.01 }, t0);
      ph.words.forEach((w) => (w.key ? keyIn(w, false) : focusIn(q(w.id), w.s - 0.05)));
      tl.to("#" + ph.id, { opacity: 0, filter: "blur(16px)", scale: 1.03, duration: OUT, ease: "power1.in" }, Math.max(t0 + 0.25, ph.t1 - OUT));
    });

    // quote cards: whip in (motion blur), words build on the voice, face whips back in after
    P.cards.forEach((c) => {
      tl.fromTo("#" + c.id, { filter: "blur(26px)", x: -160 }, { filter: "blur(0px)", x: 0, duration: 0.14, ease: "power3.out" }, c.t0);
      c.words.forEach((w) => (w.key ? keyIn(w, true) : focusIn(q(w.id), Math.max(c.t0, w.s - 0.05))));
      tl.fromTo("#" + c.id + " .ed-cardbox", { scale: 1.0 }, { scale: 1.03, duration: c.t1 - c.t0, ease: "none" }, c.t0);
      if (o.cam) tl.fromTo(o.cam, { filter: "blur(18px)" }, { filter: "blur(0px)", duration: 0.16, ease: "power2.out", immediateRender: false }, c.t1);
    });

    // cutaways (fight tape / b-roll): whip in with a motion blur, like the cards
    (P.broll || []).forEach(([a]) => {
      const el = Array.from(document.querySelectorAll(".ed-broll")).find((v) => Math.abs(parseFloat(v.dataset.start) - a) < 0.002);
      if (el) tl.fromTo(el, { filter: "blur(18px)", scale: 1.08 }, { filter: "blur(0px)", scale: 1, duration: 0.14, ease: "power3.out" }, a);
    });

    // camera: never static. Slow push on every face stretch, alternate framing after each card (jump-cut feel)
    if (o.cam) {
      const last = P.faces.length - 1;
      P.faces.forEach(([a, b], k) => {
        // the last stretch holds frame 0's framing so the loop has no visual jump
        if (k === last && last > 0 && o.loop !== false) { tl.set(o.cam, { scale: 1.0 }, a); return; }
        const z = k % 2 ? 1.1 : 1.0;
        tl.fromTo(o.cam, { scale: z }, { immediateRender: k === 0, scale: z + 0.04, duration: b - a, ease: "none" }, a);
      });
    }

    if (P.dip) {
      tl.fromTo("#ed-dip", { opacity: 0 }, { opacity: 1, duration: P.dip[1] - P.dip[0], ease: "sine.inOut" }, P.dip[0]);
    }
  },
};
