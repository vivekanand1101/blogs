# blogs.anandvivek.in

Every post from the blogs I read in full, plus the AI, backend and database posts from
company engineering blogs.

Every day a scheduled Claude routine pulls each blog's feed, reads the new posts, keeps the
company-blog posts that match [CRITERIA.md](CRITERIA.md), tags topics on everything, and pushes the result. Cloudflare Pages
builds every push to `main` (`python3 build.py render`, output `public/`) and serves it.

- `blogs.json` — the blogs to track. `"filter": false` shows every post;
  `"filter": true` keeps only what Claude judges to be AI, backend or databases.
- `CRITERIA.md` — what counts as relevant. Edit it to change what Claude keeps.
- `ROUTINE.md` — the steps the daily routine follows.
- `build.py` — `fetch` / `apply` / `render` (standard library only).
- `template.html` — the page; the build injects the post data.
- `data/posts.json` — every post with Claude's verdict.

Run it locally:

    python3 build.py && open public/index.html
