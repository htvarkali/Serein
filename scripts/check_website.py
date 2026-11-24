"""Check that the static site can be published at a project-relative URL."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

WEBSITE = Path(__file__).resolve().parents[1] / "website"
SPA_ROUTES = {"/", "/smokecast", "/airplan", "/about", "/world", "/results", "/replay", "/plan"}
LEGACY_ROUTES = {"research.html": "./#/smokecast", "airplan.html": "./#/airplan"}


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.references = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name == "id" and value:
                self.ids.add(value)
            if name == "src" or (tag in {"a", "link"} and name == "href"):
                self.references.append((self.getpos()[0], value or ""))


def validate_website(root: Path) -> list[str]:
    root = root.resolve()
    index = root / "index.html"
    if not index.is_file():
        return ["website/index.html is missing"]

    pages = {}
    for path in root.rglob("*.html"):
        page = PageLinks()
        page.feed(path.read_text(encoding="utf-8"))
        page.close()
        pages[path] = page

    errors = []
    for filename, destination in LEGACY_ROUTES.items():
        page = pages.get(root / filename)
        if page is None or not any(reference == destination for _, reference in page.references):
            errors.append(f"{filename}: missing link to {destination!r}")

    for path, page in pages.items():
        for line, reference in page.references:
            location = f"{path.relative_to(root)}:{line}"
            link = urlsplit(reference)
            if link.scheme in {"https", "http"} and link.netloc:
                continue
            if link.scheme == "mailto" and "@" in link.path and not any(
                c.isspace() for c in unquote(link.path)
            ):
                continue
            if not reference or link.scheme or link.netloc or link.path.startswith("/"):
                errors.append(f"{location}: invalid or non-relative URL {reference!r}")
                continue

            target = (path.parent / unquote(link.path)).resolve() if link.path else path
            if not target.is_relative_to(root):
                errors.append(f"{location}: URL leaves the site: {reference!r}")
                continue
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                errors.append(f"{location}: missing file for {reference!r}")
            elif link.fragment and target in pages:
                fragment = unquote(link.fragment)
                is_spa_route = target == index and fragment.split("#", 1)[0] in SPA_ROUTES
                if not is_spa_route and fragment not in pages[target].ids:
                    errors.append(f"{location}: missing anchor for {reference!r}")
    return errors


if __name__ == "__main__":
    problems = validate_website(WEBSITE)
    if problems:
        raise SystemExit("\n".join(problems))
    print("Website files and internal links verified.")
