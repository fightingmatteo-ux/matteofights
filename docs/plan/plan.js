/* The 4-Week Power Plan: content + page logic. No build step.
 * Sales page at matteofights.me/plan/ ; a buyer's personal page at matteofights.me/plan/#k=TOKEN.
 * Backend: signup-site/functions/api/plan/ (buy.js, me.js). Sessions live in signup-site/lib/plan_content.js. */
(function () {
  "use strict";
  var API = "https://matteo-signup.pages.dev/api/plan";

  // Public teaser for the sales page. The sessions themselves come from the API for paid links only
  // (signup-site/lib/plan_content.js).
  var WEEK_NOTES = ["Learn the moves. Every rep at full intent, full rest. Do the day 1 test before session 1.", "One more rep and one more round. Stop a set when reps slow down.", "Hardest week. Clap push-ups if they stay crisp, 4 rounds holding your round 1 pace.", "Lighter on purpose so you test fresh. Retest on day 28."];
  var TESTS = [
    { f: "jump", label: "Broad jump", how: "Best of 3, toes on a line, measure to your back heel." },
    { f: "pushups", label: "Push-ups in 60 s", how: "Chest to fist height, full lockout. Count clean reps only." },
    { f: "burpees", label: "Burpees in 3 min", how: "One full round. Chest to floor, jump at the top. Pace it like a real round." }
  ];

  // ---------- helpers ----------
  var $ = function (sel) { return document.querySelector(sel); };
  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (a) { if (a === "text") e.textContent = attrs[a]; else e.setAttribute(a, attrs[a]); });
    (kids || []).forEach(function (k) { if (k) e.appendChild(k); });
    return e;
  }
  function store(key, val) {
    try { if (val === undefined) return JSON.parse(localStorage.getItem(key) || "null"); localStorage.setItem(key, JSON.stringify(val)); } catch (e) { return null; }
  }
  var token = (location.hash.match(/k=([A-Za-z0-9_-]{20,40})/) || [])[1];
  var units = store("plan_units") || "in";
  var cm = function (v) { return units === "in" ? v * 2.54 : v; };
  var show = function (vCm) { return units === "in" ? Math.round(vCm / 2.54) + " in" : Math.round(vCm) + " cm"; };
  var DAY = 864e5;

  // ---------- sales page ----------
  function sales() {
    $("#sales").hidden = false;
    var src = (new URLSearchParams(location.search).get("src") || "").replace(/[^\w-]/g, "");
    $("#buy").href = API + "/buy" + (src ? "?src=" + src : "");
    if (/cancelled=1/.test(location.search)) $("#cancelled").hidden = false;
    var list = $("#preview");
    WEEK_NOTES.forEach(function (n, i) {
      list.appendChild(el("li", { text: "Week " + (i + 1) + ": " + n }));
    });
  }

  // ---------- buyer page ----------
  function buyer() {
    $("#mine").hidden = false;
    $("#mylink").value = location.href;
    $("#copy").onclick = function () {
      ($("#mylink").select(), navigator.clipboard ? navigator.clipboard.writeText(location.href) : document.execCommand("copy"));
      $("#copy").textContent = "Copied";
    };
    load(0);
  }
  function load(tries) {
    fetch(API + "/me?k=" + token).then(function (r) { return r.json(); }).then(function (d) {
      if (d.error) return status(d.error === "unknown link" ? "This link isn't a plan link. Check your receipt email for yours." : d.error);
      if (!d.paid) {
        if (tries < 15) return (status("Confirming your payment..."), setTimeout(function () { load(tries + 1); }, 2500));
        return status("Payment not confirmed yet. If you paid, refresh in a minute or DM @matteofights your receipt.");
      }
      status("");
      $("#plan").hidden = false;
      renderTests(d);
      renderPlan(d.plan || []);
    }).catch(function () { status("Can't reach the server. Check your connection and refresh."); });
  }
  function status(t) { $("#status").textContent = t; $("#status").hidden = !t; }

  function renderTests(d) {
    var box = $("#tests");
    box.innerHTML = "";
    var unitBtn = el("button", { class: "ghost", type: "button", text: "Units: " + (units === "in" ? "inches" : "cm") });
    unitBtn.onclick = function () { units = units === "in" ? "cm" : "in"; store("plan_units", units); renderTests(d); };
    if (!d.baseline) return box.appendChild(form("baseline", "Day 1 test", "Do this before your first session. It takes 10 minutes after a warm-up.", d, unitBtn));
    var b = d.baseline;
    var due = Date.parse(b.at) + 27 * DAY;
    if (d.retest) {
      var r = d.retest;
      box.appendChild(el("h2", { text: "Your 4 weeks" }));
      box.appendChild(table([["Broad jump", show(b.jump), show(r.jump)], ["Push-ups 60 s", b.pushups, r.pushups], ["Burpees 3 min", b.burpees, r.burpees]]));
      box.appendChild(el("p", { class: "dim", text: "Run it again from week 1 with your new numbers as the bar to beat." }));
      return box.appendChild(unitBtn);
    }
    box.appendChild(el("h2", { text: "Day 1 numbers" }));
    box.appendChild(table([["Broad jump", show(b.jump), ""], ["Push-ups 60 s", b.pushups, ""], ["Burpees 3 min", b.burpees, ""]]));
    var dueDate = new Date(due);
    if (Date.now() < due) {
      box.appendChild(el("p", { class: "dim", text: "Retest unlocks " + dueDate.toDateString() + ". Put it in your calendar so you come back:" }));
      var ics = el("a", { class: "ghost", download: "power-plan-retest.ics", text: "Add retest to calendar" });
      ics.href = icsFor(dueDate);
      box.appendChild(ics);
      var early = el("button", { class: "ghost", type: "button", text: "Retest now anyway" });
      early.onclick = function () { box.innerHTML = ""; box.appendChild(form("retest", "Retest", "Same tests, same rules as day 1.", d, unitBtn)); };
      box.appendChild(early);
    } else {
      box.appendChild(form("retest", "Retest day", "Same tests, same rules as day 1. Beat your numbers.", d, unitBtn));
    }
    box.appendChild(unitBtn);
  }
  function table(rows) {
    var t = el("table", {}, [el("tr", {}, [el("th", { text: "" }), el("th", { text: "Day 1" }), el("th", { text: rows[0][2] !== "" ? "Day 28" : "" })])]);
    rows.forEach(function (r) { t.appendChild(el("tr", {}, r.map(function (c) { return el("td", { text: String(c) }); }))); });
    return t;
  }
  function form(test, title, sub, d, unitBtn) {
    var f = el("form", {}, [el("h2", { text: title }), el("p", { class: "dim", text: sub })]);
    TESTS.forEach(function (t) {
      var label = t.label + (t.f === "jump" ? " (" + (units === "in" ? "inches" : "cm") + ")" : "");
      f.appendChild(el("label", {}, [el("span", { text: label }), el("small", { text: t.how }),
        el("input", { name: t.f, type: "number", inputmode: "decimal", step: "any", min: "0", required: "" })]));
    });
    var btn = el("button", { type: "submit", text: "Save " + (test === "baseline" ? "my day 1 numbers" : "my retest") });
    f.appendChild(btn);
    f.appendChild(unitBtn);
    f.onsubmit = function (e) {
      e.preventDefault();
      btn.disabled = true;
      var res = { jump: cm(Number(f.jump.value)), pushups: Number(f.pushups.value), burpees: Number(f.burpees.value) };
      fetch(API + "/me", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ k: token, test: test, results: res }) })
        .then(function (r) { return r.json(); })
        .then(function (n) { if (n.error) { btn.disabled = false; return alert(n.error); } renderTests(n); });
    };
    return f;
  }
  function icsFor(date) {
    var dt = date.toISOString().slice(0, 10).replace(/-/g, "");
    var body = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//matteofights//plan//EN", "BEGIN:VEVENT",
      "UID:" + token + "@matteofights.me", "DTSTAMP:" + new Date().toISOString().replace(/[-:]/g, "").slice(0, 15) + "Z",
      "DTSTART;VALUE=DATE:" + dt, "SUMMARY:Power Plan retest", "DESCRIPTION:Beat your day 1 numbers: " + location.href,
      "END:VEVENT", "END:VCALENDAR"].join("\r\n");
    return "data:text/calendar;charset=utf-8," + encodeURIComponent(body);
  }

  function renderPlan(PLAN) {
    var done = store("plan_done_" + token) || {};
    var box = $("#weeks");
    box.innerHTML = "";
    PLAN.forEach(function (w) {
      var det = el("details", {}, [el("summary", { text: "Week " + w.week })]);
      if (w.week === 1) det.open = true;
      det.appendChild(el("p", { class: "dim", text: w.note }));
      w.days.forEach(function (day, i) {
        var key = w.week + "-" + i;
        var cb = el("input", { type: "checkbox" });
        cb.checked = !!done[key];
        cb.onchange = function () { done[key] = cb.checked; store("plan_done_" + token, done); };
        var card = el("div", { class: "day" }, [el("label", { class: "check" }, [cb, el("strong", { text: "Session " + (i + 1) + ": " + day.t })])]);
        var ol = el("ol");
        day.items.forEach(function (it) {
          ol.appendChild(el("li", {}, [el("b", { text: it.ex.n + (it.dose ? " " + it.dose : "") }), el("span", { text: it.ex.d })]));
        });
        card.appendChild(ol);
        det.appendChild(card);
      });
      box.appendChild(det);
    });
  }

  if (token) buyer(); else sales();
})();
