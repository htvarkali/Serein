# Serein website

Edit the React app in `src/` and static assets in `public/`. GitHub Pages publishes
`website/` at `/Serein/`, so the build uses relative asset URLs and hash routes.
The HTML redirects in `public/` preserve older research and AirPlan links.

From `website-src/`, use Node.js 24 to install the locked dependencies and start
local development:

```sh
npm ci
npm run dev
```

Build the deployable site with `npm run build`. This type-checks the app and
regenerates `../website/`. Use `npm run preview` to inspect the built version.
From the repository root, run `python3 scripts/check_website.py` to check the
output's links. Commit both the source and generated site when publishing.

Use `scripts/build_website.sh` from the repository root if you also want to
refresh available research figures and the live forecast export before building.
