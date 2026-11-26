import { useEffect } from "react"
import { useLocation } from "react-router-dom"
import gsap from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"
import Lenis from "lenis"

gsap.registerPlugin(ScrollTrigger)

let lenis: Lenis | null = null

/** True when the reader's device asks for less motion (an operating system setting). */
export const prefersReducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches

/** Background clips play only on wider screens, and never with "reduce motion" or data
 *  saver on. Everyone else gets the still poster, so the clip is not downloaded. */
export function canPlayBackgroundVideo() {
  const saveData = (navigator as Navigator & { connection?: { saveData?: boolean } }).connection?.saveData
  return window.matchMedia("(min-width: 768px)").matches && !prefersReducedMotion() && !saveData
}

// The pause button in a hero stops every looping animation on the page (see styles.css,
// ".motion-paused"). Canvases that animate listen for MOTION_EVENT to stop and restart.
export const MOTION_EVENT = "serein:motion"
export const motionPaused = () => document.documentElement.classList.contains("motion-paused")
export function setMotionPaused(paused: boolean) {
  document.documentElement.classList.toggle("motion-paused", paused)
  window.dispatchEvent(new Event(MOTION_EVENT))
}

/** Smooth scrolling (Lenis) driving GSAP ScrollTrigger, plus reveal-on-scroll for any
 *  element marked data-reveal. Re-scans the page after every route change. With
 *  "reduce motion" on, scrolling is the browser's own and nothing slides with it. */
export function useSiteMotion() {
  const { pathname } = useLocation()
  useEffect(() => {
    document.documentElement.classList.add("js")
    if (prefersReducedMotion()) return
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
      if (!prefersReducedMotion()) document.querySelectorAll<HTMLElement>("[data-parallax]").forEach(el => {
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
