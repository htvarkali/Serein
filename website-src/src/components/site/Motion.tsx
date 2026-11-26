import { useEffect, useRef } from "react"
import { useLocation } from "react-router-dom"
import gsap from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"
import Lenis from "lenis"

gsap.registerPlugin(ScrollTrigger)

// Aadi's call (Nov 22): animations always run, with no reduced-motion switch.

/** A twinkling, slowly drifting star field with a few rising embers, drawn on a canvas
 *  that fills its positioned parent. Decorative only. */
export function StarField({ density = 1, embers = true, className = "" }: { density?: number; embers?: boolean; className?: string }) {
  const ref = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return
    let w = 0, h = 0, frame = 0, visible = true
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    type Star = { x: number; y: number; r: number; p: number; s: number; gold: boolean }
    type Ember = { x: number; y: number; vx: number; vy: number; life: number; max: number; r: number }
    let stars: Star[] = []
    const sparks: Ember[] = []

    function resize() {
      const box = canvas!.parentElement!.getBoundingClientRect()
      w = box.width; h = box.height
      canvas!.width = Math.round(w * dpr); canvas!.height = Math.round(h * dpr)
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0)
      const n = Math.round((w * h) / 2600 * density)
      stars = Array.from({ length: n }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        r: Math.random() ** 3 * 1.5 + 0.25, p: Math.random() * Math.PI * 2,
        s: 0.4 + Math.random() * 1.6, gold: Math.random() < 0.12,
      }))
    }
    const ro = new ResizeObserver(resize)
    ro.observe(canvas.parentElement!)
    resize()
    const io = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting })
    io.observe(canvas)

    let last = performance.now()
    function draw(now: number) {
      frame = requestAnimationFrame(draw)
      if (!visible || document.hidden) { last = now; return }
      const dt = Math.min(0.05, (now - last) / 1000); last = now
      ctx!.clearRect(0, 0, w, h)
      const t = now / 1000
      for (const st of stars) {
        st.x += dt * 2.2 * st.r
        if (st.x > w + 2) st.x = -2
        const a = 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(t * st.s + st.p))
        ctx!.globalAlpha = a
        ctx!.fillStyle = st.gold ? "#ecd3a0" : "#f4f1ff"
        ctx!.beginPath(); ctx!.arc(st.x, st.y, st.r, 0, Math.PI * 2); ctx!.fill()
        if (st.r > 1.35) {
          ctx!.globalAlpha = a * 0.35
          ctx!.fillRect(st.x - st.r * 3, st.y - 0.25, st.r * 6, 0.5)
          ctx!.fillRect(st.x - 0.25, st.y - st.r * 3, 0.5, st.r * 6)
        }
      }
      if (embers) {
        if (sparks.length < 26 && Math.random() < dt * 3) {
          sparks.push({ x: Math.random() * w, y: h + 4, vx: (Math.random() - 0.5) * 8, vy: -(14 + Math.random() * 22), life: 0, max: 6 + Math.random() * 7, r: 0.6 + Math.random() * 1.3 })
        }
        for (let i = sparks.length - 1; i >= 0; i--) {
          const e = sparks[i]
          e.life += dt; e.x += (e.vx + Math.sin(t + i) * 4) * dt; e.y += e.vy * dt
          const k = e.life / e.max
          if (k >= 1 || e.y < -4) { sparks.splice(i, 1); continue }
          ctx!.globalAlpha = Math.sin(Math.PI * k) * 0.8
          const g = ctx!.createRadialGradient(e.x, e.y, 0, e.x, e.y, e.r * 4)
          g.addColorStop(0, "#ffd9a0"); g.addColorStop(1, "#e08a4f00")
          ctx!.fillStyle = g
          ctx!.beginPath(); ctx!.arc(e.x, e.y, e.r * 4, 0, Math.PI * 2); ctx!.fill()
        }
      }
      ctx!.globalAlpha = 1
    }
    frame = requestAnimationFrame(draw)
    return () => { cancelAnimationFrame(frame); ro.disconnect(); io.disconnect() }
  }, [density, embers])
  return <canvas ref={ref} aria-hidden="true" className={`pointer-events-none absolute inset-0 -z-10 size-full ${className}`} />
}

let lenis: Lenis | null = null
export const scrollToTop = () => (lenis ? lenis.scrollTo(0) : window.scrollTo({ top: 0, behavior: "smooth" }))

/** Smooth scrolling (Lenis) driving GSAP ScrollTrigger, plus reveal-on-scroll for any
 *  element marked data-reveal. Re-scans the page after every route change. */
export function useSiteMotion() {
  const { pathname } = useLocation()
  useEffect(() => {
    document.documentElement.classList.add("js")
    lenis = new Lenis({ lerp: 0.09, smoothWheel: true })
    lenis.on("scroll", ScrollTrigger.update)
    const tick = (time: number) => lenis?.raf(time * 1000)
    gsap.ticker.add(tick)
    gsap.ticker.lagSmoothing(0)
    return () => { gsap.ticker.remove(tick); lenis?.destroy(); lenis = null }
  }, [])

  useEffect(() => {
    // Reveals use an IntersectionObserver, and a MutationObserver catches sections that
    // lazy pages render later, so nothing marked data-reveal can stay hidden.
    const seen = new WeakSet<Element>()
    const io = new IntersectionObserver(entries => {
      for (const entry of entries) if (entry.isIntersecting) { entry.target.classList.add("is-in"); io.unobserve(entry.target) }
    }, { rootMargin: "0px 0px -8% 0px" })
    const tweens: gsap.core.Tween[] = []
    function scan() {
      document.querySelectorAll<HTMLElement>("[data-reveal]").forEach(el => {
        if (seen.has(el)) return
        seen.add(el)
        if (el.dataset.revealDelay) el.style.setProperty("--d", `${el.dataset.revealDelay}s`)
        io.observe(el)
      })
      document.querySelectorAll<HTMLElement>("[data-parallax]").forEach(el => {
        if (seen.has(el)) return
        seen.add(el)
        const amount = Number(el.dataset.parallax || 12)
        tweens.push(gsap.fromTo(el, { yPercent: -amount / 2 }, {
          yPercent: amount / 2, ease: "none",
          scrollTrigger: { trigger: el.parentElement ?? el, start: "top bottom", end: "bottom top", scrub: true },
        }))
      })
      ScrollTrigger.refresh()
    }
    let pending = 0
    const mo = new MutationObserver(() => { window.clearTimeout(pending); pending = window.setTimeout(scan, 80) })
    mo.observe(document.body, { childList: true, subtree: true })
    scan()
    return () => {
      window.clearTimeout(pending); mo.disconnect(); io.disconnect()
      tweens.forEach(t => { t.scrollTrigger?.kill(); t.kill() })
    }
  }, [pathname])
}
