---
name: cloud-run-agent-memory
description: Use when setting up persistent serverless memory or chat history for a Cloud Run AI agent or service, or when the user mentions Firestore, agent memory, or database connection from Cloud Run. Covers Firestore Native creation, service account IAM permissions, and Python/Node.js SDK code.
---

# Agent Memory on Cloud Run (using Firestore)

Cloud Run services are stateless and scale to zero. To give your AI agent persistent memory (such as chat histories, session context, or execution state), you should back it with a serverless, scale-to-zero database.

**Google Cloud Firestore (Native Mode)** is the recommended memory store because:
- **Serverless pricing:** Scales to zero and has a generous free tier (50,000 read/write/delete operations per day).
- **No VPC complexity:** It is accessible via Google's secure APIs, avoiding costly Serverless VPC Access connectors or public IP whitelisting.
- **IAM authentication:** The service connects using Application Default Credentials (ADC) via its Service Account. No database passwords or keys in Secret Manager are required.

---

## 1. Create a Firestore Native Database

Ensure the Firestore API is enabled, and create a Firestore Native database in your region (use the same region as your Cloud Run service for lowest latency, e.g., `us-central1`):

```sh
# Enable Firestore API
gcloud services enable firestore.googleapis.com

# Create the (default) database in Native mode
gcloud firestore databases create \
  --location=us-central1 \
  --type=firestore-native
```

---

## 2. Configure Service Account Permissions (IAM)

To access Firestore, your Cloud Run service needs the **Cloud Datastore User** (`roles/datastore.user`) role.

We recommend using a dedicated user-managed service account instead of the default Compute Engine service account:

```sh
# 1. Create a dedicated service account
gcloud iam service-accounts create cloud-run-agent-sa \
  --display-name="Cloud Run Agent Service Account"

# 2. Grant the service account permissions to access Firestore
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:cloud-run-agent-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
```

When deploying or updating your Cloud Run service, attach this service account:
```sh
gcloud run deploy SERVICE_NAME \
  --source . \
  --service-account="cloud-run-agent-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --region=us-central1
```

---

## 3. Implement Agent Memory (Python)

Ensure you install the required SDK:
```sh
pip install google-cloud-firestore
```

### Option A: Standard Firestore SDK (Custom Agent State)
```python
from google.cloud import firestore

# Automatically uses Application Default Credentials (ADC) in Cloud Run
db = firestore.Client()

def save_chat_history(session_id: str, history: list):
    doc_ref = db.collection("agent_memory").document(session_id)
    doc_ref.set({
        "messages": history,
        "updated_at": firestore.SERVER_TIMESTAMP
    }, merge=True)

def load_chat_history(session_id: str):
    doc_ref = db.collection("agent_memory").document(session_id)
    doc = doc_ref.get()
    return doc.to_dict().get("messages", []) if doc.exists else []
```

### Option B: LangChain Integration
```sh
pip install langchain-google-firestore
```
```python
from langchain_google_firestore import FirestoreChatMessageHistory

# Automatically authenticates via Cloud Run's service account
history = FirestoreChatMessageHistory(
    session_id="session_123",
    collection="chat_history",
    project="PROJECT_ID"
)

history.add_user_message("Hello, agent!")
history.add_ai_message("How can I help you today?")
print(history.messages)
```

---

## 4. Implement Agent Memory (Node.js / TypeScript)

Install the required library:
```sh
npm install @google-cloud/firestore
```

### Option A: Standard Firestore SDK (Custom Agent State)
```javascript
const { Firestore } = require('@google-cloud/firestore');

// Automatically detects project and credentials inside Cloud Run
const db = new Firestore();

async function saveChatHistory(sessionId, messages) {
  const docRef = db.collection('agent_memory').doc(sessionId);
  await docRef.set({
    messages,
    updatedAt: Firestore.FieldValue.serverTimestamp()
  }, { merge: true });
}

async function loadChatHistory(sessionId) {
  const docRef = db.collection('agent_memory').doc(sessionId);
  const doc = await docRef.get();
  return doc.exists ? doc.data().messages : [];
}
```

### Option B: LangChain Integration
```sh
npm install @langchain/google-firestore
```
```javascript
const { FirestoreChatMessageHistory } = require("@langchain/google-firestore");

const history = new FirestoreChatMessageHistory({
  collection: "chat_history",
  sessionId: "session_123",
  config: { projectId: "PROJECT_ID" }
});

await history.addUserMessage("Hello, agent!");
await history.addAIChatMessage("How can I help you today?");
console.log(await history.getMessages());
```

---

## 5. Verify

Test the service account's ability to read and write to Firestore:
- Deploy the updated Cloud Run container configured with the custom service account.
- Invoke the agent endpoint that interacts with memory.
- Monitor your container logs in Cloud Logging or via the CLI:
```sh
gcloud logs read --service=SERVICE_NAME --region=us-central1 --limit=30
```
Check that the deployed container logs do not throw any credential or permission errors.

---

## Troubleshooting

- **`PermissionDenied / IAM error`** — Verify the service account on Cloud Run is indeed the custom one, and that the `projects add-iam-policy-binding` command succeeded with `roles/datastore.user`. Wait 1-2 minutes for IAM role propagation.
- **`Database (default) not found`** — Make sure you created the database in Native mode. Run `gcloud firestore databases list` to inspect your active Firestore databases.
- **`Locally getting DefaultCredentialsError`** — When testing locally, set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable pointing to a service account JSON file, or run `gcloud auth application-default login` to use your user credentials.
