/* FIRST WORD: the project page. Everything drawn here comes from site/data.json, which tools/site.py writes
   from the repository's own data. No libraries. */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var el = function (tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  };
  var clock = function (frames, fps) {
    var s = frames / fps;
    return Math.floor(s / 60) + ":" + (s % 60 < 10 ? "0" : "") + (s % 60).toFixed(2);
  };

  fetch("site/data.json").then(function (r) { return r.json(); }).then(function (D) {
    var kinds = {};
    D.kinds.forEach(function (k) { kinds[k.key] = k; });
    explorer(D, kinds);
    bars(D);
    $("mara").textContent = D.mara;
    mixer(D);
    dials(D);
    archive(D);
    cost(D);
  }).catch(function (e) {
    var p = el("p", "small", "The page's data did not load (" + e.message + "). The film above and the repository are unaffected.");
    $("explorer").prepend(p);
  });

  /* ------------------------------------------------------------ the shot explorer */
  function explorer(D, kinds) {
    var strip = $("strip"), v = $("exvideo"), fps = D.fps, total = D.frames;
    var cur = 0, loop = true, buttons = [];

    D.passages.forEach(function (p) {
      var s = el("span", "", p.name);
      s.style.flex = (p.end - p.start) + " 0 0";
      $("passages").appendChild(s);
    });
    for (var t = 0; t < 60; t += 5) {
      var a = el("span", "", t + " s");
      a.style.left = (t / 60 * 100) + "%";
      $("axis").appendChild(a);
    }
    D.kinds.forEach(function (k) {
      var li = el("li");
      var sw = el("i"); sw.style.setProperty("--c", k.colour);
      li.appendChild(sw);
      li.appendChild(document.createTextNode(k.name + " "));
      li.appendChild(el("span", "", k.shots + " shots"));
      $("legend").appendChild(li);
    });
    D.shots.forEach(function (s, i) {
      var b = el("button");
      b.type = "button";
      b.style.flex = s.dur + " 0 0";
      b.style.setProperty("--c", kinds[s.kind].colour);
      b.setAttribute("role", "option");
      b.setAttribute("aria-selected", "false");
      b.setAttribute("aria-label", s.id + ", " + kinds[s.kind].name + ", " + s.dur + " frames");
      b.title = s.id + " · " + clock(s.start, fps);
      b.addEventListener("click", function () { select(i, true); });
      strip.appendChild(b);
      buttons.push(b);
    });

    function fill(id, text) {
      var d = $(id);
      d.textContent = text || "None";
      d.className = text ? "" : "none";
    }
    function show(i) {
      var s = D.shots[i], k = kinds[s.kind];
      buttons[cur].setAttribute("aria-selected", "false");
      cur = i;
      buttons[i].setAttribute("aria-selected", "true");
      $("s-id").textContent = s.id;
      var chip = $("s-kind");
      chip.textContent = "";
      var sw = el("i"); sw.style.setProperty("--c", k.colour);
      chip.appendChild(sw);
      chip.appendChild(document.createTextNode(k.name));
      $("s-meta").textContent = "In at " + clock(s.start, fps) + " · " + s.dur + " frames · " + (s.dur / fps).toFixed(2) + " s · shot " + (i + 1) + " of " + D.shots.length;
      fill("s-picture", s.picture);
      fill("s-line", s.line);
      fill("s-sound", s.sound);
      fill("s-cut", s.cut);
    }
    function seek(i) {
      try { v.currentTime = (D.shots[i].start + 0.25) / fps; } catch (e) { /* not ready yet */ }
    }
    function select(i, play) {
      i = (i + D.shots.length) % D.shots.length;
      show(i);
      seek(i);
      if (play) { var p = v.play(); if (p && p.catch) p.catch(function () {}); }
    }
    function shotAt(frame) {
      var lo = 0, hi = D.shots.length - 1;
      while (lo < hi) {
        var mid = (lo + hi + 1) >> 1;
        if (D.shots[mid].start <= frame) lo = mid; else hi = mid - 1;
      }
      return lo;
    }
    function tick() {
      if (!v.paused && v.readyState >= 2) {
        var f = v.currentTime * fps, s = D.shots[cur];
        if (loop) {
          if (f >= s.start + s.dur - 0.15 || f < s.start - 0.5) seek(cur);
        } else {
          if (f >= total - 0.5) { v.currentTime = 0; f = 0; }
          var i = shotAt(Math.floor(f + 0.01));
          if (i !== cur) show(i);
        }
      }
      requestAnimationFrame(tick);
    }

    $("s-prev").addEventListener("click", function () { select(cur - 1, true); });
    $("s-next").addEventListener("click", function () { select(cur + 1, true); });
    $("s-mode").addEventListener("click", function () {
      loop = !loop;
      this.setAttribute("aria-pressed", String(loop));
      this.textContent = loop ? "Looping this shot" : "Playing the film through";
      var p = v.play(); if (p && p.catch) p.catch(function () {});
    });
    $("s-slow").addEventListener("click", function () {
      var on = this.getAttribute("aria-pressed") !== "true";
      this.setAttribute("aria-pressed", String(on));
      v.playbackRate = on ? 0.5 : 1;
    });
    v.addEventListener("click", function () { if (v.paused) v.play(); else v.pause(); });
    strip.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { select(cur + 1, true); buttons[cur].focus(); e.preventDefault(); }
      if (e.key === "ArrowLeft") { select(cur - 1, true); buttons[cur].focus(); e.preventDefault(); }
    });

    var first = D.shots.findIndex(function (s) { return s.id === "B04"; });
    show(first < 0 ? 0 : first);
    v.addEventListener("loadedmetadata", function () { seek(cur); });
    if (v.readyState >= 1) seek(cur);
    // start looping only once the explorer is on screen
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          if (e.isIntersecting) { var p = v.play(); if (p && p.catch) p.catch(function () {}); } else v.pause();
        });
      }, { threshold: 0.25 }).observe(v);
    }
    requestAnimationFrame(tick);
  }

  /* ------------------------------------------------------------ where the picture comes from */
  function bars(D) {
    var box = $("bars"), maxS = 0, maxF = 0;
    D.kinds.forEach(function (k) { maxS = Math.max(maxS, k.shots); maxF = Math.max(maxF, k.frames); });
    ["", "Shots", "Running time"].forEach(function (h) { box.appendChild(el("div", "head", h)); });
    D.kinds.forEach(function (k) {
      var name = el("div", "name");
      var sw = el("i"); sw.style.setProperty("--c", k.colour);
      name.appendChild(sw);
      name.appendChild(document.createTextNode(k.name));
      box.appendChild(name);
      [[k.shots / maxS, k.shots + " shots"], [k.frames / maxF, (k.frames / D.fps).toFixed(1) + " s · " + Math.round(k.frames / D.frames * 100) + "%"]].forEach(function (p) {
        var row = el("div", "bar"), b = el("b");
        b.style.width = (p[0] * 78) + "%";
        b.style.setProperty("--c", k.colour);
        row.appendChild(b);
        row.appendChild(el("span", "", p[1]));
        box.appendChild(row);
      });
    });
  }

  /* ------------------------------------------------------------ the stems */
  function mixer(D) {
    var names = { dialogue: "Dialogue", effects: "Effects", score: "Score", whale: "Whale" };
    var order = ["dialogue", "effects", "score", "whale"].filter(function (k) { return D.stems[k]; });
    var v = $("mixvideo"), btn = $("mixplay"), note = $("mixnote");
    var ctx = null, buffers = {}, gains = {}, sources = [], on = {}, heads = [], loading = false;

    order.forEach(function (k) {
      on[k] = true;
      var row = el("div", "stemrow"), b = el("button", "", names[k]);
      b.type = "button";
      b.setAttribute("aria-pressed", "true");
      b.addEventListener("click", function () {
        on[k] = !on[k];
        b.setAttribute("aria-pressed", String(on[k]));
        row.classList.toggle("off", !on[k]);
        if (gains[k]) gains[k].gain.setTargetAtTime(on[k] ? 1 : 0, ctx.currentTime, 0.015);
      });
      var env = el("div", "env"), NS = "http://www.w3.org/2000/svg";
      var svg = document.createElementNS(NS, "svg");
      var e = D.stems[k], n = 200, step = e.length / n;
      svg.setAttribute("viewBox", "0 0 " + n + " 40");
      svg.setAttribute("preserveAspectRatio", "none");
      svg.setAttribute("role", "img");
      svg.setAttribute("aria-label", names[k] + " level across the minute");
      for (var i = 0; i < n; i++) {
        var m = 0;
        for (var j = Math.floor(i * step); j < Math.floor((i + 1) * step); j++) m = Math.max(m, e[j]);
        var h = Math.max(0.6, m * 40), r = document.createElementNS(NS, "rect");
        r.setAttribute("x", i + 0.12); r.setAttribute("y", (40 - h) / 2);
        r.setAttribute("width", 0.76); r.setAttribute("height", h);
        svg.appendChild(r);
      }
      var head = el("div", "head");
      env.appendChild(svg); env.appendChild(head);
      heads.push(head);
      env.addEventListener("click", function (ev) {
        var box = env.getBoundingClientRect();
        v.currentTime = Math.max(0, Math.min(59.9, (ev.clientX - box.left) / box.width * 60));
      });
      row.appendChild(b); row.appendChild(env);
      $("stems").appendChild(row);
    });

    function stop() {
      sources.forEach(function (s) { try { s.stop(); } catch (e) {} });
      sources = [];
    }
    function start() {
      stop();
      if (!ctx || v.paused) return;
      order.forEach(function (k) {
        var s = ctx.createBufferSource();
        s.buffer = buffers[k];
        s.connect(gains[k]);
        s.start(0, Math.min(v.currentTime, buffers[k].duration - 0.01));
        sources.push(s);
      });
    }
    function load() {
      if (ctx || loading) return Promise.resolve();
      loading = true;
      note.textContent = "Loading the stems…";
      var AC = window.AudioContext || window.webkitAudioContext;
      var c = new AC();
      return Promise.all(order.map(function (k) {
        return fetch("media/stems/" + k + ".m4a").then(function (r) { return r.arrayBuffer(); }).then(function (b) {
          return new Promise(function (ok, no) { c.decodeAudioData(b, ok, no); });
        }).then(function (buf) {
          buffers[k] = buf;
          gains[k] = c.createGain();
          gains[k].gain.value = on[k] ? 1 : 0;
          gains[k].connect(c.destination);
        });
      })).then(function () {
        ctx = c; loading = false;
        note.textContent = "Click a stem's name to switch it off or on. Click its level to jump there.";
      }).catch(function (e) {
        loading = false;
        note.textContent = "The stems could not be played in this browser (" + (e && e.message ? e.message : "decoding failed") + "). They are in the repository under audio/stems.";
        throw e;
      });
    }
    btn.addEventListener("click", function () {
      if (!v.paused) { v.pause(); return; }
      load().then(function () {
        if (ctx.state === "suspended") ctx.resume();
        return v.play();
      }).catch(function () {});
    });
    v.addEventListener("play", function () { btn.textContent = "Pause"; start(); });
    v.addEventListener("pause", function () { btn.textContent = "Play with stems"; stop(); });
    v.addEventListener("seeked", start);
    v.addEventListener("ended", function () { stop(); v.currentTime = 0; });
    v.addEventListener("click", function () { btn.click(); });
    (function head() {
      var x = (v.currentTime / 60 * 100) + "%";
      heads.forEach(function (h) { h.style.left = x; });
      requestAnimationFrame(head);
    })();
  }

  /* ------------------------------------------------------------ the persona's dials */
  function dials(D) {
    D.dials.forEach(function (d) {
      var row = el("div", "dial");
      row.appendChild(el("b", "", d.name));
      row.appendChild(el("div", "end low", d.low));
      var track = el("div", "track");
      track.setAttribute("role", "img");
      track.setAttribute("aria-label", d.name + ": " + d.value + " out of 10");
      for (var i = 1; i <= 10; i++) {
        var t = el("i"); t.style.left = ((i - 1) / 9 * 100) + "%"; track.appendChild(t);
      }
      var m = el("em", "", String(d.value));
      m.style.left = ((d.value - 1) / 9 * 100) + "%";
      track.appendChild(m);
      row.appendChild(track);
      row.appendChild(el("div", "end high", d.high));
      $("dials").appendChild(row);
    });
  }

  /* ------------------------------------------------------------ the real sources */
  function archive(D) {
    var body = $("archive").tBodies[0];
    D.archive.forEach(function (a) {
      var tr = el("tr");
      tr.appendChild(el("td", "", a.shots.join(", ")));
      tr.appendChild(el("td", "", a.title));
      tr.appendChild(el("td", "", a.date.replace(/ \(.*$/, "")));
      var h = el("td");
      if (/^https?:\/\//.test(a.url)) {
        var link = el("a", "", a.holder); link.href = a.url; link.rel = "noopener"; h.appendChild(link);
      } else h.textContent = a.holder;
      tr.appendChild(h);
      tr.appendChild(el("td", "", a.rights.replace(/^public domain/, "Public domain")));
      body.appendChild(tr);
    });
  }

  /* ------------------------------------------------------------ what the generations cost */
  function cost(D) {
    var body = $("cost").tBodies[0], sum = 0, calls = 0;
    D.cost.forEach(function (c) {
      var tr = el("tr");
      tr.appendChild(el("td", "", c.what));
      tr.appendChild(el("td", "", String(c.calls)));
      tr.appendChild(el("td", "", c.usd.toFixed(2)));
      body.appendChild(tr);
      sum += c.usd; calls += c.calls;
    });
    var tr = el("tr", "total");
    tr.appendChild(el("td", "", "Total"));
    tr.appendChild(el("td", "", String(calls)));
    tr.appendChild(el("td", "", sum.toFixed(2)));
    body.appendChild(tr);
  }
})();
