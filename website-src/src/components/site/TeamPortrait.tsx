import { asset, type team } from "@/data/site"

export function TeamPortrait({ member, className }: { member: (typeof team)[number]; className: string }) {
  return (
    <span className={`block shrink-0 overflow-hidden bg-[#e7dfcc] ${className}`}>
      <img
        src={asset(`img/team/${member.photo}`)}
        alt=""
        className="size-full object-cover"
        style={member.photoStyle}
        loading="lazy"
        decoding="async"
      />
    </span>
  )
}
