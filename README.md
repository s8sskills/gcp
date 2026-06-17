# s8sskills / gcp

Serverless skills for **Google Cloud** — reusable, agent-ready instructions that
teach your AI coding agent how to build and deploy serverless apps on GCP.

Part of [s8sskills](https://s8sskills.com): one skill pack per cloud vendor.

## Install

Install every skill in this pack into your agent (Claude Code, etc.):

```sh
npx skills add s8sskills/gcp
```

Or install a single skill:

```sh
npx skills add https://github.com/s8sskills/gcp/tree/main/skills/cloud-run-deploy
```

`npx skills` is the open agent-skills installer ([vercel-labs/skills](https://github.com/vercel-labs/skills)).
It drops each skill into your agent's skills directory (e.g. `.claude/skills/`),
where the agent picks it up automatically when a task matches the skill's
`description`.

## Skills

| Skill | What it does |
| --- | --- |
| [`gcloud-project-setup`](skills/gcloud-project-setup/SKILL.md) | gcloud CLI auth, active project, billing, and enabling the serverless APIs. Foundation the others build on. |
| [`cloud-run-deploy`](skills/cloud-run-deploy/SKILL.md) | Deploy any container / web app / API to Cloud Run (source or image), with env vars, secrets, scaling, and verification. |
| [`cloud-functions-deploy`](skills/cloud-functions-deploy/SKILL.md) | Deploy a single HTTP or event-driven function (Cloud Functions 2nd gen / Cloud Run functions). |
| [`firebase-deploy`](skills/firebase-deploy/SKILL.md) | Deploy a frontend to Firebase Hosting and/or a backend to Cloud Functions for Firebase. |

## Layout

Skills follow the standard discovery layout — one directory per skill, each with
a `SKILL.md` whose YAML frontmatter declares `name` and `description`:

```
skills/
  gcloud-project-setup/SKILL.md
  cloud-run-deploy/SKILL.md
  cloud-functions-deploy/SKILL.md
  firebase-deploy/SKILL.md
```

## Contributing

New GCP serverless skill ideas welcome (App Engine, Workflows, Eventarc,
scheduled jobs, Pub/Sub plumbing, IaC with Terraform). Add a
`skills/<name>/SKILL.md` with `name` + `description` frontmatter and open a PR.
Keep each skill focused on one task, with concrete commands and a verification
step.

## License

See [LICENSE](LICENSE).
