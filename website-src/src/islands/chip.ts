// The site's outlined chip buttons, shared by every island control.
export function chip(tone: "light" | "dark") {
  const base =
    "h-auto cursor-pointer rounded-[.25rem]! border bg-transparent px-[.85rem] py-[.55rem] text-[.84rem] font-bold shadow-none! transition-colors duration-200"
  return tone === "dark"
    ? `${base} border-[#7c9e90]! text-[var(--paper)] hover:bg-[#ffffff14] hover:text-[var(--paper)] data-[state=on]:border-[var(--sage)]! data-[state=on]:bg-[var(--sage)] data-[state=on]:text-[var(--deep)]`
    : `${base} border-[var(--border)]! text-[var(--ink)] hover:bg-[#162d280d] hover:text-[var(--ink)] data-[state=on]:border-[var(--grove)]! data-[state=on]:bg-[var(--grove)] data-[state=on]:text-[var(--paper)]`
}
