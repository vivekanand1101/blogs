# Daily routine

Instructions for the scheduled Claude run that updates blogs.anandvivek.in.

1. `python3 build.py fetch` — pulls every feed and writes `data/pending.json`,
   the posts that have no verdict yet. If it lists 0 posts, stop: nothing to do.
2. Read `CRITERIA.md`, then judge every post in `data/pending.json` from its title and
   summary. When the title and summary aren't enough to decide, open the post URL and skim it.
   Posts with `"always_shown": true` come from full-feed blogs and are always kept: set
   `relevant` to true and only choose which topics fit (often none).
3. Write `data/verdicts.json` as one object keyed by post URL:
   `{"<url>": {"relevant": true, "topics": ["ai"], "reason": "One short sentence."}}`
   `topics` uses only `ai`, `backend`, `databases`, and is `[]` when none fit.
   Every URL from `pending.json` must have an entry.
4. `python3 build.py apply data/verdicts.json`, then delete `data/verdicts.json`.
5. Commit `data/posts.json` with the message `Update posts YYYY-MM-DD` and push to `main`.
   The push triggers a Cloudflare Pages build, which publishes the site.

Do not change any other file.
