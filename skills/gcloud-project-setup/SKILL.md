---
name: gcloud-project-setup
description: Use when starting GCP work in a project for the first time, or when a gcloud command fails with auth, project, billing, or "API not enabled" errors. Sets up the gcloud CLI, authentication, the active project, and required service APIs before deploying.
---

# GCP project setup

Foundational steps every other GCP serverless skill depends on. Run these once
per machine + project before deploying. If a later `gcloud` command fails with
`PERMISSION_DENIED`, `API [...] not enabled`, or `The project ... could not be
found`, come back here.

## Prerequisites

- A Google Cloud account with a project and **billing enabled** (serverless
  products require an active billing account, even within free-tier limits).
- The `gcloud` CLI installed. If `gcloud --version` fails:
  - macOS: `brew install --cask google-cloud-sdk`
  - Other: https://cloud.google.com/sdk/docs/install

## Steps

1. **Authenticate** (opens a browser):
   ```sh
   gcloud auth login
   ```
   For application code that calls Google APIs locally, also set up Application
   Default Credentials:
   ```sh
   gcloud auth application-default login
   ```

2. **Select the project.** Replace `PROJECT_ID` with the target project:
   ```sh
   gcloud config set project PROJECT_ID
   gcloud config set run/region us-central1   # default region for deploys
   ```
   List projects you can access with `gcloud projects list`.

3. **Confirm billing is linked** (serverless deploys fail without it):
   ```sh
   gcloud billing projects describe PROJECT_ID
   ```
   If `billingEnabled` is `false`, link an account in the Cloud Console
   (Billing → Link a billing account).

4. **Enable the APIs** the serverless products need. Enable only what you use;
   enabling is idempotent and safe to re-run:
   ```sh
   gcloud services enable \
     run.googleapis.com \
     cloudbuild.googleapis.com \
     artifactregistry.googleapis.com
   ```
   Cloud Functions / Eventarc also need:
   ```sh
   gcloud services enable cloudfunctions.googleapis.com eventarc.googleapis.com
   ```

## Verify

```sh
gcloud config list           # shows account + project + region
gcloud services list --enabled | grep run.googleapis.com
```

Both should reflect your intended account/project and the enabled APIs.

## Notes

- Prefer setting `--project` / `--region` explicitly in CI rather than relying on
  `gcloud config`, which is per-machine state.
- Least privilege: a deployer typically needs roles `run.admin`,
  `cloudbuild.builds.editor`, `iam.serviceAccountUser`, and
  `artifactregistry.writer`. Grant on the project, not the org.
