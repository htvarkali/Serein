// Numbers in [data-count-up] count up from zero the first time they scroll
// into view. The final text is already in the HTML, so nothing is lost
// without JavaScript or with reduced motion.
export function setupCountUp() {
  const items = [...document.querySelectorAll<HTMLElement>("[data-count-up]")]
  if (!items.length || matchMedia("(prefers-reduced-motion: reduce)").matches) return

  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue
      observer.unobserve(entry.target)
      const el = entry.target as HTMLElement
      const text = el.textContent ?? ""
      const target = Number.parseFloat(text)
      const digits = (text.split(".")[1] ?? "").length
      const start = performance.now()
      const tick = (now: number) => {
        const t = Math.min((now - start) / 1400, 1)
        el.textContent = (target * (1 - (1 - t) ** 3)).toFixed(digits)
        if (t < 1) requestAnimationFrame(tick)
        else el.textContent = text
      }
      requestAnimationFrame(tick)
    }
  }, { threshold: 0.6 })
  for (const el of items) observer.observe(el)
}
