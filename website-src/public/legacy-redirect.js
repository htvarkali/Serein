// Preserve section links from the static site when opening the React app.
const continuation = document.getElementById("continue")
const sections = continuation.dataset.sections.split(" ")
const section = window.location.hash.slice(1)
const destination = new URL(continuation.href)

if (sections.includes(section)) {
  destination.hash += `#${section}`
}

window.location.replace(destination.href)
