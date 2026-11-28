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
- Bind prepositions, conjunctions and particles to the next word with a non-breaking space («на помощь»). `scripts/typo.js` does this on the site at runtime, `scripts/typo.py` in generated pages; extend both word lists together.
- Keep post IDs stable. After editing posts or their images, run `python3 scripts/build_post_previews.py` with Pillow installed and include the updated `post/` files with the site changes.
- In every daily update, run `python3 scripts/youtube_new.py` (needs yt-dlp) and add each listed video from the @dandesdet channel: `shorts` as a vertical video card, `wide` as `vid wide` in the bottom row. The script decides by the frame, not by the channel tab: a horizontal video uploaded as a Short is still `wide`. Do not wait for the user to ask. The script also checks every YouTube cover in `index.html`; fix each `BROKEN` line before pushing (a horizontal video has no `oar2.jpg`, use `maxresdefault.jpg`).
- In every update with results, run `python3 scripts/avatars.py --write` (needs opencv-python and tennis-base in ~/Downloads). It replaces initials with photos from tennis-base, picking the person and photo the same way as people.html (localhost:8766/people.html): user edits, merges, PlayOn links and chosen photos first. Look at every face in `av/review.jpg`; for a wrong photo, a child or no face, add `"Имя Фамилия": "skip"` to `av/people.json` and restore the initials; for a confirmed match under another name, add `"Имя Фамилия": "<id from the base>"`. Do not wait for the user to ask.
- Before every push, open the local preview and look at each added or changed card: cover, headline and text. Never publish a gray placeholder or a broken image.
- Every source label (`.via`) and every source in the Sources list has a logo avatar in `img/groups/<slug>.webp`, 160×160. Take it from the source’s own profile picture (Instagram, Telegram, site). Never publish a card with a text-only source label.
- For news, keep the date above the headline and cite the original source below the text. Mark missing sources explicitly.
- Publish the 07:00 Tashkent Telegram digest only through GitHub Actions by updating `tg/teaser.txt` on `main`. Never run the Mac copy of `tg_channel.py post` to publish. Before pushing, verify the draft date against the current date in Tashkent, check channel history for duplicates, and include an image only if it belongs to this issue. Keep `tg/teaser.txt` out of unrelated site updates. Announce in the channel only events within 7 days of the issue date; later events stay on the site until they come within 7 days.
