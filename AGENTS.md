# Tennis Daily

Tennis Daily is a static, multilingual site for amateur tennis in Tashkent. The shared repository is `dandesdet/tennisdaily`. GitHub Pages publishes `main` to https://tennisdaily.uz/.

## Work in the same repository

- At the start, check `git status -sb` and the latest commits. Preserve uncommitted work from the user or the other assistant. Use separate branches or worktrees for simultaneous edits.
- Before handing off, record the branch, commit or local changes, verification performed, and next step in a short note. Keep GitHub as the shared reference when moving between computers.
- Show local changes for review. Push to `main` when the user asks to publish, then verify the live site.
- For a local preview, run `python3 -m http.server 8788 --bind 127.0.0.1` from the repository root and open http://127.0.0.1:8788/.

## Project conventions

- `index.html` contains the site, court directory, filters and map. Keep Russian, Uzbek and English in sync.
- Keep each court location in one record. Associate each photo with the matching court type. Use confirmed details for opening hours, access and booking.
- Keep post IDs stable. After editing posts or their images, run `python3 scripts/build_post_previews.py` with Pillow installed and include the updated `post/` files with the site changes.
- For news, keep the date above the headline and cite the original source below the text. Mark missing sources explicitly.
- The Telegram digest is scheduled separately in Codex for 07:00 Tashkent time. The repository workflow can send a teaser when `tg/teaser.txt` changes, so keep that file out of unrelated site updates.
