# Tennis Daily

Tennis Daily is a static, multilingual site for amateur tennis in Tashkent. The shared repository is `dandesdet/tennisdaily`. GitHub Pages publishes `main` to https://tennisdaily.uz/.

## Work in the same repository

- Read `PROJECT_NOTES.md` at the start of each task. Record user-supplied sources, durable decisions, and open questions there so the other assistant can pick them up. Keep the notes short and leave out credentials and private material.

- Before each new task, including in an existing session, run `git fetch origin`, then check `git status -sb` and compare the current branch with `origin/main`.
- If the current branch is `main`, the working tree is clean, and the remote is only ahead, run `git merge --ff-only origin/main` before editing. If there are uncommitted edits or the histories diverged, preserve the changes and report the difference. If the fetch fails, say that freshness could not be verified.
- Use separate branches or worktrees for simultaneous edits. Before continuing on an existing feature branch, review any new commits on `origin/main` that affect the task.
- Before handing off, record the branch, commit or local changes, verification performed, and next step in a short note. Keep GitHub as the shared reference when moving between computers.
- Show local changes for review. Push to `main` when the user asks to publish, then verify the live site.
- For a local preview, run `python3 -m http.server 8788 --bind 127.0.0.1` from the repository root and open http://127.0.0.1:8788/.

## Project conventions

- `index.html` contains the site, court directory, filters and map. Keep Russian, Uzbek and English in sync.
- Keep each court location in one record. Associate each photo with the matching court type. Use confirmed details for opening hours, access and booking.
- Link to the live booking calendar for slot-dependent prices. Publish a fixed court tariff only with a current primary source and the date it was verified. Remove a tariff when the source no longer confirms it.
- Keep post IDs stable. After editing posts or their images, run `python3 scripts/build_post_previews.py` with Pillow installed and include the updated `post/` files with the site changes.
- For news, keep the date above the headline and cite the original source below the text. Mark missing sources explicitly.
- The Telegram digest is scheduled separately in Codex for 07:00 Tashkent time. The repository workflow can send a teaser when `tg/teaser.txt` changes, so keep that file out of unrelated site updates.
