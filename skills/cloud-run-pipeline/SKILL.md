---
name: cloud-run-pipeline
description: Use when setting up continuous deployment / a CI/CD pipeline that deploys to Google Cloud Run from any CI tool (GitHub Actions, GitLab CI, Jenkins, Buildkite, Cloud Build), or when the user mentions "cloud run ci", "deploy cloud run from github actions", "workload identity federation", "gcp deploy service account", or "rig a pipeline for cloud run".
---

# Rig a CI/CD pipeline for Cloud Run

Set up the **vendor-agnostic rigging** so any CI/CD tool can deploy this project
to Cloud Run on every push: create a least-privilege deploy service account,
wire up keyless auth (Workload Identity Federation) where possible, and hand back
the exact deploy command plus the values the CI job needs. You prepare the cloud
side; the user owns their CI tool and all secrets.

If `gcloud` auth/project/APIs aren't set up, run `gcloud-project-setup` first
(needs the `run`, `cloudbuild`, and `artifactregistry` APIs enabled).

> **Guardrails — do not violate:**
> - **Never** print, store, or commit a real key, token, or secret. A service-account key (if used) is downloaded by the user and pasted straight into their CI tool's secret store — it must never land in a file, in chat, or in the repo.
> - **Never** run an interactive login (`gcloud auth login`) on the user's behalf — hand them the command and wait.
> - **Do not** pick the user's CI tool for them, and **do not** commit or push anything without asking.

## 1. Create a least-privilege deploy service account

```sh
PROJECT=$(gcloud config get-value project)
gcloud iam service-accounts create cloud-run-deployer \
  --display-name="Cloud Run CI deployer"
SA="cloud-run-deployer@${PROJECT}.iam.gserviceaccount.com"

# Deploy the service, build from source, push the image, act as the runtime SA.
for role in roles/run.admin roles/cloudbuild.builds.editor \
            roles/artifactregistry.writer roles/iam.serviceAccountUser \
            roles/storage.admin; do
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="serviceAccount:${SA}" --role="$role" --condition=None >/dev/null
done
```

## 2. Give CI credentials to that account — prefer KEYLESS

### Option A (preferred): Workload Identity Federation — no long-lived key

Federate the CI provider's OIDC token to the deploy SA. This is provider-specific;
set it up for whichever tool the user names. Example for **GitHub Actions**:

```sh
POOL=github-pool
gcloud iam workload-identity-pools create "$POOL" --location=global \
  --display-name="GitHub Actions"
gcloud iam workload-identity-pools providers create-oidc github \
  --location=global --workload-identity-pool="$POOL" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='OWNER/REPO'"   # TODO: the user's repo

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
gcloud iam service-accounts add-iam-policy-binding "$SA" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/OWNER/REPO"
```

The CI job then needs the **provider resource name** and the **deploy SA email** —
neither is a secret.

### Option B (fallback): service-account key

Universal but a long-lived secret. Have the user create and download it, then add
its contents to their CI tool as a secret named `GCP_SA_KEY`:

```sh
# Direct the user to run this and paste the file into their CI secret store — do not print it here.
gcloud iam service-accounts keys create key.json --iam-account="$SA"
```

## 3. The deploy command a CI job runs

After the job authenticates (via WIF or `gcloud auth activate-service-account
--key-file=$GCP_SA_KEY`):

```sh
gcloud run deploy SERVICE_NAME \
  --source . \
  --region "$GCP_REGION" \
  --project "$GCP_PROJECT" \
  --allow-unauthenticated   # drop for a private service
```

## The deploy contract (summarize this back to the user)

- **Command:** the `gcloud run deploy --source .` above.
- **Deploy identity:** `cloud-run-deployer@…` service account (least-privilege).
- **Keyless (Option A):** CI needs `WORKLOAD_IDENTITY_PROVIDER` (provider resource name) + `DEPLOY_SERVICE_ACCOUNT` (the SA email) — neither secret.
- **Key (Option B):** CI needs the `GCP_SA_KEY` **secret** (the key JSON).
- **Non-secret vars either way:** `GCP_PROJECT`, `GCP_REGION`.
- **Trigger:** run on push to the production branch (e.g. `main`).

## Optional: scaffold a starter CI config

If the user names a CI tool, offer to write a starter config with the deploy
command wired in and **every secret/identity left as a placeholder they fill**.
Never insert a real key.

**GitHub Actions (keyless / WIF)** — `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run
on:
  push:
    branches: [main]
permissions:
  contents: read
  id-token: write        # required for keyless WIF
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          project_id: my-project                                    # TODO: your GCP_PROJECT
          workload_identity_provider: ${{ vars.WIF_PROVIDER }}      # TODO: provider resource name (not secret)
          service_account: ${{ vars.DEPLOY_SERVICE_ACCOUNT }}       # TODO: cloud-run-deployer@… (not secret)
      - uses: google-github-actions/setup-gcloud@v2
      - run: gcloud run deploy SERVICE_NAME --source . --region us-central1 --allow-unauthenticated
```

**GitLab CI (key fallback)** — `.gitlab-ci.yml`:

```yaml
deploy_cloud_run:
  image: google/cloud-sdk:slim
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
  # TODO: define GCP_SA_KEY (masked, the key JSON), GCP_PROJECT, GCP_REGION under Settings → CI/CD → Variables
  script:
    - echo "$GCP_SA_KEY" > /tmp/key.json
    - gcloud auth activate-service-account --key-file=/tmp/key.json
    - gcloud run deploy SERVICE_NAME --source . --region "$GCP_REGION" --project "$GCP_PROJECT" --allow-unauthenticated
```

## Troubleshooting

- **`PERMISSION_DENIED` on deploy** — the deploy SA is missing a role; re-check the bindings in step 1 (`run.admin`, `iam.serviceAccountUser`, and the build/registry roles for `--source` deploys).
- **`Permission 'iam.serviceAccounts.getAccessToken' denied`** — the WIF principal isn't bound to the SA; re-check the `workloadIdentityUser` binding and the `attribute.repository` condition matches the repo.
- **First deploy fails creating the Artifact Registry repo** — the SA needs `artifactregistry.writer` (and the API enabled); source deploys build + push an image.
- **`invalid_grant` / key errors** — the `GCP_SA_KEY` secret is malformed or the key was revoked; regenerate and re-add it.
