# blogs.anandvivek.in

AI, backend and database posts from the tech blogs I follow.

Every day a scheduled Claude routine pulls each blog's feed, reads the new posts, keeps the
ones that match [CRITERIA.md](CRITERIA.md), and pushes the result. GitHub Actions then
renders the page and publishes it to GitHub Pages.

- `blogs.json` — the blogs to track.
- `CRITERIA.md` — what counts as relevant. Edit it to change what Claude keeps.
- `ROUTINE.md` — the steps the daily routine follows.
- `build.py` — `fetch` / `apply` / `render` (standard library only).
- `template.html` — the page; the build injects the post data.
- `data/posts.json` — every post with Claude's verdict.

Run it locally:

    python3 build.py && open public/index.html
