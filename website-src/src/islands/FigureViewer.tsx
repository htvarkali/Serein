import { useEffect, useState } from "react"
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog"

type Figure = { src: string; alt: string; caption: string }

// Figure links open the full-size image in a dialog instead of leaving the
// page. Without JavaScript the links still open the image directly.
export function FigureViewer({ links }: { links: HTMLAnchorElement[] }) {
  const [figure, setFigure] = useState<Figure | null>(null)

  useEffect(() => {
    function open(event: MouseEvent) {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return
      const link = event.currentTarget as HTMLAnchorElement
      const img = link.querySelector("img")
      event.preventDefault()
      setFigure({
        src: link.href,
        alt: img?.alt ?? "",
        caption: link.closest("figure")?.querySelector("figcaption")?.textContent?.trim() ?? "",
      })
    }
    for (const link of links) link.addEventListener("click", open)
    return () => links.forEach(link => link.removeEventListener("click", open))
  }, [links])

  return (
    <Dialog open={figure !== null} onOpenChange={open => !open && setFigure(null)}>
      <DialogContent className="max-h-[92vh] w-[min(96vw,80rem)] max-w-none! gap-3 overflow-auto rounded-[.45rem] border-[var(--border)] bg-[var(--paper)] p-[clamp(.8rem,2vw,1.4rem)] text-[var(--ink)] [&>button]:cursor-pointer">
        <DialogTitle className="sr-only">{figure?.alt || "Figure"}</DialogTitle>
        {figure && <img src={figure.src} alt={figure.alt} className="w-full rounded-[.3rem]" />}
        <DialogDescription className="pr-8 text-[.88rem] text-[var(--muted)]">{figure?.caption}</DialogDescription>
      </DialogContent>
    </Dialog>
  )
}
