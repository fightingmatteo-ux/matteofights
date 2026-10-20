// Editorial motion for the PLAN that plan.py writes. Soft, calm, premium: blur-in words, no bounce.
//   Editorial.animate(tl, PLAN, { cam: "#cam-inner" })
window.Editorial = {
  animate(tl, P, o = {}) {
    const IN = 0.22, OUT = 0.08;
    const wordIn = (id, t, key, slam) => {
      if (slam) {
        // over-scaled past the frame edges, settles hard: the one loud moment
        tl.fromTo("#" + id, { opacity: 0, scale: 2.4, filter: "blur(18px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.32, ease: "expo.out" }, t);
      } else if (key) {
        tl.fromTo("#" + id, { opacity: 0, scale: 1.18, y: 10, filter: "blur(16px)" }, { opacity: 1, scale: 1, y: 0, filter: "blur(0px)", duration: 0.3, ease: "expo.out" }, t);
      } else {
        tl.fromTo("#" + id, { opacity: 0, y: 14, filter: "blur(10px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: IN, ease: "expo.out" }, t);
      }
    };

    // captions: phrase shows, words build on the voice, phrase lifts and softens away before the next
    P.phrases.forEach((ph) => {
      const t0 = Math.max(0, ph.t0 - 0.03);
      tl.fromTo("#" + ph.id, { opacity: 0 }, { opacity: 1, duration: 0.01 }, t0);
      ph.words.forEach((w) => wordIn(w.id, Math.max(0, w.s - 0.03), w.key));
      tl.to("#" + ph.id, { opacity: 0, y: -16, filter: "blur(8px)", duration: OUT, ease: "power1.in" }, Math.max(t0 + 0.2, ph.t1 - OUT));
    });

    // quote cards: words build on the voice; the card itself is a hard cut in and out (its clip timing)
    P.cards.forEach((c) => {
      c.words.forEach((w) => wordIn(w.id, Math.max(c.t0, w.s - 0.03), w.key, w.slam));
      tl.fromTo("#" + c.id + " .ed-cardbox", { scale: 1.0 }, { scale: 1.03, duration: c.t1 - c.t0, ease: "none" }, c.t0);
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
