# 📦 AutoDevOps AI Agents

This project contains a full multi-agent DevOps pipeline powered by Vertex AI Gemini, Google Cloud Pub/Sub, and BigQuery. It automatically reviews code, generates tests, analyzes security, runs tests, and logs everything in a CI/CD workflow using GitHub Actions.

---

### 📁 Project Structure

```
.
👉🔹 agents/
   👉🔹 code-review-agent/
   👉🔹 Test_generator/
   👉🔹 CICD_agent/
   👉🔹 SecurityAgent/
👉🔹 generated_tests/
👉🔹 .github/workflows/ci.yml
👉🔹 .env.local
👉🔹 README.md
```

---

## 🚀 Features

| Agent              | Description                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| 💡 Code Reviewer   | Uses Gemini to review source code and publish summaries to Pub/Sub.         |
| 🧲 Test Generator   | Generates and runs tests based on the code review, logs results to BigQuery. |
| 🔒 Security Agent   | Scans code for security issues and logs findings to BigQuery.              |
| 🌟 CI/CD Agent      | Listens for test results and triggers builds or reports failures.           |

---

## 🔧 Setup Instructions

### 1. 📦 Clone the Repository

```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo
```

---

### 2. 🔐 Environment Configuration

Create a `.env.local` file at the root:

```env
VERTEX_PROJECT_ID=your-gcp-project-id
VERTEX_LOCATION=us-central1

PUBSUB_TOPIC=code_review_done
TEST_GEN_OUTPUT_TOPIC=test_generation_done
TEST_GEN_SUBSCRIPTION_ID=test_generator_sub
```

You may override these via GitHub Actions secrets instead.

---

### 3. ☑️ Google Cloud Setup

#### Enable APIs:

- Vertex AI API
- Pub/Sub API
- BigQuery API

#### Create resources:

```bash
gcloud pubsub topics create code_review_done
gcloud pubsub topics create test_generation_done

gcloud pubsub subscriptions create test_generator_sub --topic=code_review_done
gcloud pubsub subscriptions create cicd_listener_sub --topic=test_generation_done
gcloud pubsub subscriptions create security_agent_sub --topic=test_generation_done
```

#### Grant IAM roles:

```bash
gcloud pubsub subscriptions add-iam-policy-binding test_generator_sub \
  --member="serviceAccount:your-sa@your-project.iam.gserviceaccount.com" \
  --role="roles/pubsub.subscriber"
```

✅ Ensure your GitHub Actions service account has these IAM roles:

- BigQuery Data Editor
- Pub/Sub Publisher
- Pub/Sub Subscriber
- Vertex AI Service Agent

These are needed to insert logs, send/receive messages, and call Gemini.

---

### 4. 📊 BigQuery Tables

Create a dataset called `devops_logs` with the following tables:

#### `test_results` schema:

```json
[
  {"name": "file_path", "type": "STRING"},
  {"name": "language", "type": "STRING"},
  {"name": "test_output", "type": "STRING"},
  {"name": "deps", "type": "STRING"},
  {"name": "review_summary", "type": "STRING"},
  {"name": "timestamp", "type": "TIMESTAMP"},
  {"name": "run_id", "type": "STRING"}
]
```

Same applies to:

- `security_findings`
- `cicd_events`

---

### 5. ✅ GitHub Secrets

| Name                  | Description                       |
|-----------------------|-----------------------------------|
| `GCP_CREDENTIALS`     | JSON key for service account      |
| `GCP_PROJECT`         | Your GCP project ID               |
| `PUBSUB_TOPIC`        | e.g., `code_review_done`          |
| `TEST_GEN_OUTPUT_TOPIC` | e.g., `test_generation_done`    |
| `TEST_GEN_SUBSCRIPTION_ID` | e.g., `test_generator_sub`  |

---

## 💠 CI/CD Workflow

The GitHub Actions workflow:

1. Sets up Python and installs dependencies  
2. Authenticates with Google Cloud  
3. Runs Code Reviewer → Publishes results to Pub/Sub  
4. Test Generator listens via `test_generator_sub` → runs & logs tests  
5. CI/CD and Security Agents listen for results, log findings  
6. Summarizes everything from BigQuery  
7. Optionally fails if test errors are found

---

## 📊 Query Results

The final steps in the workflow display:

- Latest test results from `test_results`
- Security issues from `security_findings`
- CI/CD events from `cicd_events`

Each row includes a `run_id` so you can group logs by workflow run.

---

## 💡 Tips

- Use `print()` statements in each agent to verify message flow in GitHub Actions logs.
- Test individual agents locally with:
  ```bash
  python agents/code-review-agent/main.py path/to/file.py
  ```

---

## 📫 Credits

Built with:
- [Vertex AI Gemini](https://cloud.google.com/vertex-ai/docs/generative-ai)
- [Google Pub/Sub](https://cloud.google.com/pubsub)
- [BigQuery](https://cloud.google.com/bigquery)
- [GitHub Actions](https://docs.github.com/en/actions)

