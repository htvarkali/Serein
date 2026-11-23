# Website islands

React components (built with shadcn/ui on Radix) that enhance a few parts of
the static site in `website/`. The HTML in `website/` stays the source of
truth: each island reads its content from the page, and the page works the
same without JavaScript.

Current islands:

- Every `[data-switcher]` block becomes accessible tabs (arrow keys move
  between options).
- On the SmokeCast page, the horizon tabs also show a bar comparison of
  SmokeCast and fallback RMSE on one shared scale.

Build after changing anything in `src/`:

```
npm install
npm run build
```

This writes `website/assets/islands/islands.js` and `islands.css`. Commit
them, because GitHub Pages publishes `website/` without a build step.

Tailwind's base reset is left out on purpose so it cannot restyle the rest of
the site; `website/assets/site.css` owns the base styles.
