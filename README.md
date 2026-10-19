# blogs.anandvivek.in

Every post from the people I follow, plus the AI, backend and database posts from company
engineering blogs.

Every day a scheduled Claude routine pulls each blog's feed, reads the new posts, keeps the
company-blog posts that match [CRITERIA.md](CRITERIA.md), tags topics on everything, and pushes the result. GitHub Actions then
renders the page and publishes it to GitHub Pages.

- `blogs.json` — the blogs to track. `"filter": false` means show every post (people);
  `"filter": true` means Claude filters it (companies).
- `CRITERIA.md` — what counts as relevant. Edit it to change what Claude keeps.
- `ROUTINE.md` — the steps the daily routine follows.
- `build.py` — `fetch` / `apply` / `render` (standard library only).
- `template.html` — the page; the build injects the post data.
- `data/posts.json` — every post with Claude's verdict.

Run it locally:

    python3 build.py && open public/index.html
