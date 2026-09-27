# Going public — checklist

The page is finished as an anonymous draft (2026-09-27). Do these when the paper is de-anonymized and the
code is released. Everything below is a placeholder in `index.html` today.

## In `index.html`
- [ ] `<meta name="robots" content="noindex">` (line ~8): delete it so search engines index the page.
- [ ] Authors line (`.authors`): replace "Anonymous authors · paper under double-blind review" with names,
      affiliations (e.g. Technion) and links.
- [ ] Venue badge (`.venue`): replace "Under review · ICLR 2027" with the accepted venue, or "arXiv".
- [ ] Link buttons (`.links`): for Paper, arXiv and Code, drop `aria-disabled="true"` and the `<small>soon</small>`,
      and add `href` (paper PDF / arXiv abs / the DyRad GitHub repo). Consider adding a Supplementary button.
- [ ] BibTeX (`#bibText`): real key, authors, venue/booktitle and year.
- [ ] Footer: replace "draft, not public".
- [ ] Tables: re-check the numbers against the CAMERA-READY PDF (they were transcribed from the submitted
      `~/Projects/DyRad/DyRAD.pdf`, Tables 1–2).
- [ ] Sequence labels in the video viewer are anonymized ("sequence 1–10"). They may stay, or be swapped for
      the RADIal recording names (order: 12_30_20, 12_25_47, 31_22, 14_25_06, 12_20_50, 12_00_45, 08_56_07,
      11_15_06, 12_37_16, 28_47; Boreas: win55_104, sparse4, sparse2).

## On GitHub (org Dyrad-NVS, Free plan)
- [ ] Make `Dyrad-NVS/dyrad-nvs.github.io` PUBLIC — on the Free plan, Pages only serves public repos.
- [ ] Settings → Pages → deploy from branch `main`, root `/`. The site is then at https://dyrad-nvs.github.io.
- [ ] `src/` (the pptx) is gitignored and stays local; nothing else in the repo is private.
- [ ] Optional: add an OG image and `og:`/`twitter:` meta tags for link previews (a still of the teaser works).

## Regenerating figures
- Teaser: `python tools/build_teaser.py`; method + motion model: `python tools/build_method.py`. Both read
  `src/figures/DyRAD_figures.pptx` (slide 2 = teaser, slides 1 and 3 = method/motion) and write between the
  `<!--TEASER-SVG-->` / `<!--METHOD-SVG-->` markers.
- Clips are copies of the supplementary site's media (`mmWaveNVS/results/supp_site/media*`).
