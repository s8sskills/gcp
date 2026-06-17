---
name: firebase-deploy
description: Use when deploying a frontend, static site, SPA, or full-stack app to Firebase Hosting and/or Cloud Functions for Firebase, or when the user mentions "Firebase", "firebase deploy", "firebase init", or hosting a web app with a serverless backend on GCP.
---

# Deploy to Firebase

Firebase sits on top of GCP and is the fastest path for a web frontend (Firebase
Hosting: global CDN, free TLS) optionally paired with a serverless backend
(Cloud Functions for Firebase). Use it for SPAs, static sites, and JAMstack apps;
use `cloud-run-deploy` instead for arbitrary containers/long-running services.

## Setup

```sh
npm install -g firebase-tools     # or run via: npx firebase-tools <cmd>
firebase login
```
A Firebase project maps to a GCP project. Create/list with `firebase projects:list`.

## Initialize (once per repo)

```sh
firebase init
```
Select **Hosting** (and **Functions** if you need a backend). Key answers:
- **Public directory:** your build output — `dist` (Vite), `build` (CRA),
  `out` (Next static export). Not `public` unless that's truly your build dir.
- **Single-page app rewrite:** `Yes` for React/Vue/SPA routing (rewrites all
  routes to `index.html`); `No` for a multi-page static site.

This writes `firebase.json` (the source of truth) and `.firebaserc` (project alias).

## Deploy

```sh
npm run build          # produce the files in your public directory first
firebase deploy
```
Scope deploys to avoid touching everything:
```sh
firebase deploy --only hosting
firebase deploy --only functions
firebase deploy --only functions:myFunction
```

## Preview before going live

```sh
firebase hosting:channel:deploy preview   # temporary shareable URL, auto-expires
firebase emulators:start                  # run hosting + functions locally
```

## Verify

The deploy prints a **Hosting URL** (`https://PROJECT.web.app`). Confirm:
```sh
curl -fsSI https://PROJECT.web.app | head -1   # expect: HTTP/2 200
```
Then load it in a browser and click through client-side routes (catches a
missing SPA rewrite).

## Troubleshooting

- **404s on refresh / deep links** — missing SPA rewrite; add to `firebase.json`:
  `"rewrites": [{ "source": "**", "destination": "/index.html" }]`.
- **Deployed an empty/old site** — `public` in `firebase.json` points at the
  wrong dir, or you forgot to `build` before `deploy`.
- **Functions deploy fails on billing** — Cloud Functions for Firebase requires
  the **Blaze** (pay-as-you-go) plan; Hosting alone works on Spark (free).
