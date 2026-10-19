# blogs.anandvivek.in

A one-page tracker for the tech blogs I follow. A GitHub Action runs `build.py`
every day, pulls each blog's feed, and publishes `public/index.html` to GitHub Pages.

- `blogs.json` — the blogs to track. Add or remove entries here.
- `build.py` — fetches feeds (standard library only) and renders the page.
- `template.html` — the page itself; the build injects the post data.
- `data/posts.json` — post history the Action commits back each day.

Run it locally:

    python3 build.py && open public/index.html
