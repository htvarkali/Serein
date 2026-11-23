"use strict";

function setupMenu() {
  const toggle = document.querySelector(".menu-toggle");
  const menu = document.querySelector("#site-menu");
  if (!toggle || !menu) return;

  const label = toggle.querySelector("span");
  const links = [...menu.querySelectorAll("a")];
  const wordmark = document.querySelector(".site-header .wordmark");
  const background = document.querySelectorAll("body > main, body > footer, .chapter-nav, .skip-link");

  function setOpen(open) {
    toggle.setAttribute("aria-expanded", String(open));
    label.textContent = open ? "Close" : "Menu";
    menu.classList.toggle("is-open", open);
    document.body.classList.toggle("menu-open", open);
    for (const element of background) element.inert = open;
    if (open) (menu.querySelector('[aria-current="page"]') || links[0]).focus();
    else toggle.focus();
  }

  toggle.addEventListener("click", () => setOpen(toggle.getAttribute("aria-expanded") !== "true"));
  menu.addEventListener("click", event => {
    if (event.target === menu || event.target.closest('a[href^="#"]')) setOpen(false);
  });
  document.addEventListener("keydown", event => {
    if (toggle.getAttribute("aria-expanded") !== "true") return;
    if (event.key === "Escape") {
      event.preventDefault();
      setOpen(false);
    }
    // The header brand, toggle, and links remain reachable while the page is inert.
    if (event.key === "Tab") {
      const first = wordmark || toggle;
      const last = links.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  });

  window.addEventListener("pagehide", () => {
    if (toggle.getAttribute("aria-expanded") === "true") setOpen(false);
  });
  document.documentElement.classList.add("js");
}

function setupSwitchers() {
  for (const group of document.querySelectorAll("[data-switcher]")) {
    const controls = group.querySelector(".switch-controls");
    const buttons = [...group.querySelectorAll("button[data-panel]")];
    const panels = [...group.querySelectorAll(".switch-panel")];
    if (!controls || !buttons.length || !panels.length) continue;
    if (buttons.some(button => !panels.some(panel => panel.id === button.dataset.panel))) continue;

    function show(id) {
      for (const panel of panels) panel.hidden = panel.id !== id;
      for (const button of buttons) button.setAttribute("aria-pressed", String(button.dataset.panel === id));
    }
    const initial = buttons.find(button => button.getAttribute("aria-pressed") === "true") || buttons[0];
    show(initial.dataset.panel);
    controls.hidden = false;
    controls.addEventListener("click", event => {
      const button = event.target.closest("button[data-panel]");
      if (button) show(button.dataset.panel);
    });
  }
}

function setupChapters() {
  const chapters = [...document.querySelectorAll(".chapter-nav a")].map(link => ({
    link, section: document.getElementById(link.hash.slice(1)),
  })).filter(chapter => chapter.section);
  if (!chapters.length) return;

  let scheduled = false;
  function update() {
    let active = chapters[0];
    for (const chapter of chapters) {
      if (chapter.section.getBoundingClientRect().top <= window.innerHeight * .38) active = chapter;
    }
    for (const chapter of chapters) {
      if (chapter === active) chapter.link.setAttribute("aria-current", "location");
      else chapter.link.removeAttribute("aria-current");
    }
    scheduled = false;
  }
  function schedule() {
    if (!scheduled) {
      scheduled = true;
      window.requestAnimationFrame(update);
    }
  }
  window.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", schedule);
  update();
}

// Photos stay in place and looping clips fade in over them while on screen.
// Every clip has a pause button (WCAG 2.2.2), and pausing is remembered.
function setupMotionVideos() {
  const videos = document.querySelectorAll("video[data-motion]");
  if (!videos.length || !("IntersectionObserver" in window)) return;
  const key = "serein-motion";
  const stored = () => { try { return localStorage.getItem(key); } catch { return null; } };
  const store = value => { try { localStorage.setItem(key, value); } catch { /* private mode */ } };
  const buttons = [];

  for (const video of videos) {
    let visible = false;
    video.playbackRate = .8;
    video.addEventListener("loadedmetadata", () => { video.playbackRate = .8; });

    const button = document.createElement("button");
    button.type = "button";
    button.className = "motion-toggle";
    video.parentElement.append(button);
    buttons.push(button);

    function sync() {
      const paused = stored() === "paused";
      button.setAttribute("aria-label", paused ? "Play background video" : "Pause background video");
      button.dataset.state = paused ? "paused" : "playing";
      if (visible && !document.hidden && !paused) video.play().catch(() => {});
      else video.pause();
    }
    video.sync = sync;
    button.addEventListener("click", () => {
      store(stored() === "paused" ? "playing" : "paused");
      for (const other of videos) other.sync();
    });
    video.addEventListener("playing", () => video.classList.add("is-playing"));
    new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      sync();
    }).observe(video);
    document.addEventListener("visibilitychange", sync);
  }
}

function setupAtmosphere() {
  const canvas = document.querySelector(".hero-atmosphere");
  if (!canvas || !("IntersectionObserver" in window) || !("ResizeObserver" in window)) return;
  const context = canvas.getContext("2d");
  if (!context) return;

  const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const points = Array.from({ length: 120 }, () => ({
    x: Math.random(), y: Math.random() * .79, size: .7 + Math.random() * 1.45,
    speed: .002 + Math.random() * .005, opacity: .14 + Math.random() * .38,
  }));
  let width = 0;
  let height = 0;
  let visible = false;
  let frame = 0;
  let last = 0;

  function draw() {
    context.clearRect(0, 0, width, height);
    for (const point of points) {
      context.fillStyle = `rgba(242, 186, 132, ${point.opacity})`;
      context.fillRect(point.x * width, point.y * height, point.size, point.size);
    }
  }

  function tick(now) {
    const elapsed = last ? Math.min((now - last) / 1000, .05) : 0;
    last = now;
    for (const point of points) {
      point.x = (point.x + point.speed * elapsed) % 1;
      point.y = (point.y - point.speed * .25 * elapsed + .79) % .79;
    }
    draw();
    frame = window.requestAnimationFrame(tick);
  }

  function syncMotion() {
    if (frame) window.cancelAnimationFrame(frame);
    frame = 0;
    last = 0;
    if (visible && !document.hidden && !motion.matches) frame = window.requestAnimationFrame(tick);
  }

  new ResizeObserver(() => {
    width = canvas.clientWidth;
    height = canvas.clientHeight;
    const scale = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(width * scale);
    canvas.height = Math.floor(height * scale);
    context.setTransform(scale, 0, 0, scale, 0, 0);
    draw();
  }).observe(canvas);
  new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    syncMotion();
  }).observe(canvas);
  motion.addEventListener("change", syncMotion);
  document.addEventListener("visibilitychange", syncMotion);
}

setupMenu();
setupMotionVideos();
setupSwitchers();
setupChapters();
setupAtmosphere();
