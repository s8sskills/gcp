---
name: cloud-run-deploy
description: Use when deploying a web app, API, container, or HTTP service to Google Cloud Run, or when the user mentions "Cloud Run", "deploy to GCP", "gcloud run", or wants a serverless container deployed. Covers source-based and container-image deploys, env vars, secrets, and verification.
---

# Deploy to Cloud Run

Cloud Run is GCP's flagship serverless platform: it runs any container that
listens on `$PORT` (default 8080), scales to zero, and bills per request. It is
the right default for web apps, APIs, and background workers.

If `gcloud` auth/project/API is not set up yet, do `gcloud-project-setup` first
(this needs `run`, `cloudbuild`, and `artifactregistry` APIs enabled).

## Decide: source deploy vs image deploy

- **Source deploy (recommended default):** `--source .` — Cloud Build turns your
  code into a container automatically. Uses your `Dockerfile` if present;
  otherwise Google Cloud Buildpacks detect the language (Node, Python, Go, Java,
  ...). No registry juggling.
- **Image deploy:** `--image REGION-docker.pkg.dev/PROJECT/REPO/IMG:TAG` — when
  you already build images in CI.

## Steps (source deploy)

1. **The app must listen on `$PORT`.** Cloud Run sets `PORT=8080`. Examples:
   - Node/Express: `app.listen(process.env.PORT || 8080)`
   - Python/Flask via gunicorn: `gunicorn --bind :$PORT main:app`
   Do not hardcode a different port.

2. **Deploy** from the project directory:
   ```sh
   gcloud run deploy SERVICE_NAME \
     --source . \
     --region us-central1 \
     --allow-unauthenticated
   ```
   - First deploy prompts to create an Artifact Registry repo — accept it.
   - Drop `--allow-unauthenticated` for a private service (requires an IAM
     invoker / ID token to call).

3. **Configuration flags** (all optional, all updatable on redeploy):
   ```sh
   --set-env-vars KEY1=VAL1,KEY2=VAL2     # plain env vars
   --set-secrets DB_PASS=db-pass:latest   # mount a Secret Manager secret
   --memory 512Mi --cpu 1                 # per-instance resources
   --min-instances 0 --max-instances 10   # scaling bounds (0 = scale to zero)
   --concurrency 80                       # max simultaneous requests/instance
   --service-account RUNTIME_SA@PROJECT.iam.gserviceaccount.com
   ```

## Verify

The deploy prints a `Service URL`. Confirm it serves:
```sh
URL=$(gcloud run services describe SERVICE_NAME --region us-central1 --format='value(status.url)')
curl -fsS "$URL" && echo "  <- OK"
```
For a private service, add an auth header:
```sh
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" "$URL"
```

## Troubleshooting

- **`Container failed to start ... listen on PORT`** — the app isn't binding to
  `$PORT`/`0.0.0.0`. Fix the listen address; this is the #1 cause.
- **Build fails, no Dockerfile** — buildpacks couldn't detect the app. Add a
  `Dockerfile`, or ensure a recognized entrypoint (`package.json` start script,
  `requirements.txt` + `main.py`, etc.).
- **`PERMISSION_DENIED` on deploy** — missing roles or disabled API; revisit
  `gcloud-project-setup`.
- Roll back instantly by routing traffic to a prior revision:
  `gcloud run services update-traffic SERVICE_NAME --to-revisions REV=100`.
