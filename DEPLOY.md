# Deploying

The dashboard in `web/` is a static site. The JSON it reads is already in `web/public/data/`, so
Vercel only needs Node; it never runs the Python pipeline.

## 1. Check it builds locally

```bash
cd web
npm install
npm run build      # creates web/dist
npm run preview    # optional, serves dist at http://localhost:4173
```

## 2. Push to GitHub

Create an empty public repository named `ipl-analytics` on GitHub (no README, no licence, this
folder already has both), then from the project root:

```bash
git init
git add .
git commit -m "IPL analytics v2: pipeline, notebook, dashboard"
git branch -M main
git remote add origin https://github.com/KrishOswal18/ipl-analytics.git
git push -u origin main
```

`.gitignore` already keeps out `data/raw/`, `data/processed/`, `.venv/`, `web/node_modules/` and `web/dist/`.

## 3. Create the Vercel project

1. Go to https://vercel.com/new and import `KrishOswal18/ipl-analytics`.
2. Project name: `iplanalytics-ko`
3. Framework preset: **Vite** (detected automatically)
4. Root directory: **`web`** (click Edit next to Root Directory and pick `web`)
5. Build command: `npm run build`
6. Output directory: `dist`
7. Install command: leave the default (`npm install`)
8. No environment variables are needed. Click **Deploy**.

The site will be at `https://iplanalytics-ko.vercel.app`. `web/vercel.json` pins the same
build settings, so later pushes to `main` redeploy with no extra setup.

## 4. Updating the data after a new season

```bash
source .venv/bin/activate
python -m ipl download     # delete data/raw/ipl_male_csv2.zip first to force a fresh download
python -m ipl run
jupyter nbconvert --to notebook --execute --inplace notebooks/analysis.ipynb
git add web/public/data reports/figures notebooks/analysis.ipynb
git commit -m "Update data to <season>"
git push                   # Vercel redeploys automatically
```

## 5. Link it from the portfolio

Add the Vercel URL and the GitHub repo link to the projects section of the portfolio site.
