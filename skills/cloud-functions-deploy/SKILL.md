---
name: cloud-functions-deploy
description: Use when deploying a single event-driven or HTTP function to GCP (Cloud Run functions / Cloud Functions 2nd gen), or when the user mentions "Cloud Functions", "gcloud functions", a Pub/Sub-triggered or Storage-triggered handler, or a lightweight HTTP endpoint without managing a container.
---

# Deploy a Cloud Function (2nd gen)

Cloud Functions 2nd gen (now "Cloud Run functions") runs a single entry-point
function on the Cloud Run infrastructure, triggered by HTTP or an event
(Pub/Sub, Cloud Storage, Eventarc). Reach for this over `cloud-run-deploy` when
you want *just a function* and not a whole server/container.

Always pass `--gen2`. The 1st-gen product is legacy. Requires the
`cloudfunctions`, `run`, `cloudbuild`, `artifactregistry`, and (for event
triggers) `eventarc` APIs — see `gcloud-project-setup`.

## HTTP function

```sh
gcloud functions deploy my-http-fn \
  --gen2 \
  --runtime nodejs20 \
  --region us-central1 \
  --source . \
  --entry-point handler \
  --trigger-http \
  --allow-unauthenticated
```
- `--entry-point` is the exported function name in your source, not the file.
- `--runtime` examples: `nodejs20`, `python312`, `go122`, `java21`.
- The function signature must match the runtime's Functions Framework (e.g. Node:
  `exports.handler = (req, res) => { ... }`).

## Pub/Sub-triggered function

```sh
gcloud functions deploy my-pubsub-fn \
  --gen2 --runtime python312 --region us-central1 \
  --source . --entry-point on_message \
  --trigger-topic my-topic
```

## Cloud Storage-triggered function

```sh
gcloud functions deploy my-gcs-fn \
  --gen2 --runtime nodejs20 --region us-central1 \
  --source . --entry-point on_finalize \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=MY_BUCKET"
```

## Common flags

```sh
--set-env-vars KEY=VAL,KEY2=VAL2
--set-secrets API_KEY=api-key:latest
--memory 256Mi --timeout 60s
--min-instances 0 --max-instances 5
```

## Verify

```sh
# HTTP: get the URL and call it
URL=$(gcloud functions describe my-http-fn --gen2 --region us-central1 --format='value(url)')
curl -fsS "$URL"

# Event-driven: tail logs and trigger the source event
gcloud functions logs read my-pubsub-fn --gen2 --region us-central1 --limit 20
```

## Troubleshooting

- **`entry point not found`** — `--entry-point` must match the exported symbol,
  and the source must use the runtime's Functions Framework.
- **Event trigger deploy hangs/fails** — the Eventarc service agent needs IAM
  propagation time on first use; enable `eventarc.googleapis.com` and retry.
- **Outgrowing a function** (multiple routes, custom server, long startup)?
  Switch to `cloud-run-deploy` — same infra, full container control.
