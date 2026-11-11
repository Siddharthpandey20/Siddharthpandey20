<!--
  Profile README for Siddharthpandey20.
  Header art lives in assets/ (dark and light variants).
  Live widgets: github-stats-extended (top languages), streak-stats.demolab.com, leetcard.jacoblin.cool.
  The old github-readme-stats.vercel.app instance is paused (HTTP 503), and the activity-graph and trophy
  instances return HTTP 402, so they were replaced or removed.
-->

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/header-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/header-light.svg">
    <img alt="Siddharth: Software Engineer. Backend systems, distributed pipelines, applied AI." src="assets/header-dark.svg" width="100%">
  </picture>
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/siddharth-a35a36324"><img alt="LinkedIn" src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white"></a>
  <a href="mailto:siddharthpandey2611official@gmail.com"><img alt="Email" src="https://img.shields.io/badge/Email-0F766E?style=for-the-badge&logo=gmail&logoColor=white"></a>
  <a href="https://leetcode.com/u/_Siddharth_pandey/"><img alt="LeetCode" src="https://img.shields.io/badge/LeetCode-FFA116?style=for-the-badge&logo=leetcode&logoColor=black"></a>
</p>

I build backend systems: task pipelines, multi-tenant APIs, access control, and the retrieval and LLM
layers that sit on top of them. I care about the parts that make software hold up: retries,
rate limits, isolation, tests, and numbers that come from a benchmark rather than a guess.

I'm a CS undergraduate at IIIT Naya Raipur, currently at **Hiring Bazaar** working on a production
AI interview platform. Alongside engineering I do research. I'm first author on two papers
(constraint-based floor-plan generation and reinforcement-learning traffic control), and I'm working
on recovery for compromised multi-agent LLM systems.

<div align="center">

| **82** | **2** | **2** | **9.74** |
|:---:|:---:|:---:|:---:|
| PRs merged in production | First-author papers accepted | Hackathon podiums (300+ & 500+ teams) | CGPA / 10 |

</div>

```python
siddharth = {
    "role"      : "Software Engineer · backend systems & applied AI",
    "now"       : "AI Engineering Intern @ Hiring Bazaar",
    "school"    : "IIIT Naya Raipur · B.Tech CSE · 2024–28",
    "focus"     : ["distributed backends", "API design", "retrieval (RAG)", "agentic systems"],
    "research"  : ["constraint optimisation", "multi-agent RL", "LLM security"],
    "principle" : "Explain the why, not just the what.",
    "open_to"   : "SDE · Backend · AI Engineering roles",
}
```

---

## What I work on

- **Backend and distributed systems.** Celery and BullMQ task pipelines, Redis rate limiting and
  distributed locking, multi-tenant REST APIs, role-based access control, async PostgreSQL, schema migrations.
- **AI engineering.** Hybrid retrieval (BM25 + dense + RRF), multi-provider LLM routing with fallback,
  tool-calling agents, and multi-agent workflows where a human keeps the final decision.
- **Engineering practice.** Claims backed by evaluation sets and benchmarks, real test suites
  (193 tests in ExamPrep AI, 325 in Prove It, 600+ in CausalLine), CI, and explicit fallbacks for every external dependency.

---

## 💼 Experience

<table>
<tr>
<td valign="top">

### 🤖 Hiring Bazaar — AI Engineering Intern
**Mar 2026 – Present** · Remote

- **82 pull requests merged** into the platform's production codebase (private GitHub organization)
- Shipped a **voice recruiter copilot** (STT/TTS + LLM intent parsing) over 1,000+ profiles → manual screening **−60%**
- Restructured async interview pipelines (**BullMQ + TypeScript**) → response latency **−40%**
- Token-usage guardrails + prompt caching → LLM API cost **−30%**
- Built LLM-orchestration microservices in **FastAPI** + **Express.js**, with **Judge0** for live code evaluation

</td>
</tr>
</table>

---

## Featured Projects

### 01 · [ExamPrep AI](https://github.com/Siddharthpandey20/ExamAI)

<sub><b>SOLO BUILD</b> &nbsp;·&nbsp; <a href="https://github.com/Siddharthpandey20/ExamAI">Repository</a> &nbsp;·&nbsp; <a href="https://drive.google.com/file/d/1kkcz9UO09Gd5X8TbkhLUN-eS8pxmH_om/view?usp=sharing">Demo Video</a></sub>

Upload a course's slides and past exam papers once. The backend extracts, structures and indexes every
slide, ranks what matters for the exam, and answers questions from your own material with slide-level citations.

- **Distributed ingestion.** Celery task chains (ingest → structure → index) on Redis with late
  acknowledgement, exponential-backoff retries for transient errors only, and stale-job detection.
  Progress streams to the browser over SSE. The API layer is 30+ FastAPI endpoints.
- **Shared-resource control.** A Redis sliding-window rate limiter and a Lua-scripted distributed
  semaphore coordinate LLM calls across workers, with automatic model fallback on HTTP 429.
  SQLite in WAL mode sustains 91 transactions/s across 8 concurrent writers with zero lock failures.
- **Retrieval.** BM25 and dense search (ChromaDB, e5-large-v2) fused with reciprocal rank fusion:
  Recall@5 **0.816** on a 114-question benchmark (0.754 dense-only), ~95 ms median latency.
- **AI layer.** Multi-LLM routing across local Ollama, Gemini and Groq, plus a tool-calling agent
  (OpenAI Agents SDK, 9 function tools). 193 offline pytest tests; Next.js 15 frontend.

![FastAPI](https://img.shields.io/badge/FastAPI-161B22?style=flat-square&logo=fastapi&logoColor=009688)
![Celery](https://img.shields.io/badge/Celery-161B22?style=flat-square&logo=celery&logoColor=37814A)
![Redis](https://img.shields.io/badge/Redis-161B22?style=flat-square&logo=redis&logoColor=DC382D)
![SQLite](https://img.shields.io/badge/SQLite-161B22?style=flat-square&logo=sqlite&logoColor=4FA8D8)
![ChromaDB + BM25](https://img.shields.io/badge/ChromaDB_+_BM25-161B22?style=flat-square)
![OpenAI Agents SDK](https://img.shields.io/badge/OpenAI_Agents_SDK-161B22?style=flat-square)
![Next.js](https://img.shields.io/badge/Next.js_15-161B22?style=flat-square&logo=nextdotjs&logoColor=white)

### 02 · [CausalLine](https://github.com/Siddharthpandey20/CausalLine)

<sub><b>RESEARCH PROTOTYPE · IN PROGRESS</b> &nbsp;·&nbsp; Lead developer, 3-person team &nbsp;·&nbsp; <a href="https://github.com/Siddharthpandey20/CausalLine">Repository</a></sub>

Selective recovery for multi-agent LLM systems after prompt injection. Once a detector names a poisoned
source, CausalLine decides which completed work has to be recomputed and which can safely be kept,
instead of discarding everything downstream of the compromised agent.

- **Core idea: exposure is not influence.** It records an append-only provenance trace, establishes
  per-pair influence from agent self-report plus counterfactual replay, and spreads contamination only
  along evidenced influence edges rather than call-graph reachability.
- **Recovery engine.** A cost-minimising recovery plan, byte-exact selective replay of the affected
  events, and verification before a recovered run is accepted. It escalates to an agent restart and then to a full restart when verification fails.
- **Evaluation.** Run on a 56-agent, 145-event workflow across 3 inference providers and 15 attack placements, with
  **zero unsafe preservations**. It keeps 7.0 and 15.2 points more correct work than topology-closure recovery in the
  medium and large contamination regimes, loses 17.4 in the small one, and costs more tokens, a trade-off the write-up reports.
- **Engineering.** Python 3.11 with no third-party dependencies in the core, and 600+ unit tests.
- **My part (53 of 73 commits).** I designed and built the original system: the trace layer, the influence estimator,
  the Safe Frontier recovery planner, and splice-and-verify replay. I then led the evaluation. That covered the 56-agent,
  three-provider testbed behind the results above, the safety fix those results rest on, local-GPU and token-cost
  studies, and the paper draft.

![Python](https://img.shields.io/badge/Python_3.11-161B22?style=flat-square&logo=python&logoColor=3776AB)
![Ollama](https://img.shields.io/badge/Ollama-161B22?style=flat-square&logo=ollama&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-161B22?style=flat-square&logo=pytest&logoColor=0A9EDC)
![Multi-agent LLMs](https://img.shields.io/badge/Multi--agent_LLM_security-161B22?style=flat-square)

### 03 · [Study AI](https://github.com/Siddharthpandey20/Study_AI_Complete_Project)

<sub><b>3RD PLACE · APIHUB HACKATHON 2025 (500+ TEAMS)</b> &nbsp;·&nbsp; 3-person team &nbsp;·&nbsp; <a href="https://github.com/Siddharthpandey20/Study_AI_Complete_Project">Repository</a> &nbsp;·&nbsp; <a href="https://drive.google.com/file/d/1bq5EJROvsifbRsGJLoaQP4rgihgUSnEp/view?usp=sharing">Demo Video</a></sub>

A study platform that turns uploaded notes into flashcards, quizzes, mind maps, learning paths,
revision notes and likely exam questions. It also answers questions about a document and lets study groups share both.

- **Backend.** An async FastAPI service with 50+ endpoints over a 7-table SQLAlchemy schema. It handles
  Google OAuth 2.0 sign-in with a signed JWT session cookie, and stores files in Cloudinary with a signed-download fallback.
- **Six generators from one upload.** Each prompt returns a fixed JSON shape that the frontend renders
  directly, and results are persisted per document so they are reused rather than regenerated.
  Rule-based fallbacks keep the app working when the model is unavailable.
- **Document Q&A.** Hybrid FAISS + BM25 retrieval with query rewriting that always searches the
  original question first. Answers are grounded in the document, and the model declines questions the document doesn't cover.
- **Study groups and YouTube.** Groups share documents and generated material via an invite key.
  YouTube transcripts are summarised into study guides, with a yt-dlp + Whisper fallback.

![FastAPI](https://img.shields.io/badge/FastAPI-161B22?style=flat-square&logo=fastapi&logoColor=009688)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-161B22?style=flat-square&logo=sqlalchemy&logoColor=D71F00)
![LangChain](https://img.shields.io/badge/LangChain-161B22?style=flat-square&logo=langchain&logoColor=white)
![FAISS + BM25](https://img.shields.io/badge/FAISS_+_BM25-161B22?style=flat-square)
![Gemini](https://img.shields.io/badge/Gemini-161B22?style=flat-square&logo=googlegemini&logoColor=8E75B2)
![OAuth 2.0](https://img.shields.io/badge/Google_OAuth_2.0-161B22?style=flat-square&logo=google&logoColor=4285F4)

### 04 · [Prove It](https://github.com/Siddharthpandey20/Prove_It-Code_decides-Agents_argue_and_Humans_rule)

<sub><b>FLIP THE SWITCH HACKATHON</b> &nbsp;·&nbsp; 4-person team &nbsp;·&nbsp; <a href="https://github.com/Siddharthpandey20/Prove_It-Code_decides-Agents_argue_and_Humans_rule">Repository</a> &nbsp;·&nbsp; <a href="https://youtu.be/wQ_h16DFlXc">Demo Video</a></sub>

*Code decides, agents argue, humans rule.* AI-written vulnerability reports take seconds to produce and an
hour to check. Prove It makes each report prove itself in a sandbox before a maintainer reads it.

- **Code decides.** The reporter submits a data-only proof, which runs in a Docker sandbox with no network,
  no secrets, non-root, a read-only filesystem and capped memory and processes. A parent-process harness classifies the outcome, and the result
  line is tagged with a one-time code the child process never sees. Eight forgery attempts are tested against it.
- **Agents argue.** An intake agent owns the ticket state machine, a Reproducer (Claude Code) runs the
  sandbox, and a Skeptic (OpenAI Codex) reviews the evidence and can dispute it. Reporter prose never
  reaches the agents, and a canary test enforces that.
- **Humans rule.** Only maintainers can escalate, close or override. Every move is enforced by one
  transition table with 73 tested cases.
- **Results.** It reproduced two real CVEs (PyYAML CVE-2020-14343, sqlparse CVE-2023-30608) on vulnerable
  builds and cleared them on patched ones, with 18/18 consistent sandbox runs and 325 tests green in CI on Linux and Windows.
- **My part.** The data-only proof format and out-of-process harness, the enforced state machine,
  per-agent lockdown, and the CI pipeline.

![Python](https://img.shields.io/badge/Python-161B22?style=flat-square&logo=python&logoColor=3776AB)
![Docker](https://img.shields.io/badge/Docker_sandbox-161B22?style=flat-square&logo=docker&logoColor=2496ED)
![Claude Code](https://img.shields.io/badge/Claude_Code-161B22?style=flat-square&logo=claude&logoColor=D97757)
![OpenAI Codex](https://img.shields.io/badge/OpenAI_Codex-161B22?style=flat-square)
![Mattermost](https://img.shields.io/badge/Mattermost-161B22?style=flat-square&logo=mattermost&logoColor=0058CC)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-161B22?style=flat-square&logo=githubactions&logoColor=2088FF)

### 05 · [Lumen](https://github.com/Siddharthpandey20/Lumen-Financial-Advisor)

<sub><b>2ND PLACE (NATIONAL) · HACK-A-SOL 2025 (300+ TEAMS)</b> &nbsp;·&nbsp; <a href="https://github.com/Siddharthpandey20/Lumen-Financial-Advisor">Repository</a></sub>

A personal and small-business finance tracker. It reads receipts with an LLM, categorises every transaction,
and answers questions about spending through retrieval over the user's own records.

- **Ingestion pipeline.** Receipts and invoices go through OCR (Tesseract or Gemini vision), then structured parsing
  with a regex fallback, then categorisation with a confidence and reason. A Gmail API monitor and n8n webhook endpoints feed transactions in automatically.
- **Isolation by design.** Each user gets a separate FAISS index, so a query can never retrieve another
  user's data. JWT auth covers separate consumer and business profiles (GSTIN, invoice fields).
- **Tamper-evident audit.** Audit records live in a separate PostgreSQL database, and each one stores the
  SHA-256 hash of the previous record.
- **Stack.** FastAPI backend and React + TypeScript (Vite) frontend, with lazy model loading to keep API start-up fast.

![FastAPI](https://img.shields.io/badge/FastAPI-161B22?style=flat-square&logo=fastapi&logoColor=009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-161B22?style=flat-square&logo=postgresql&logoColor=4169E1)
![React](https://img.shields.io/badge/React_+_TypeScript-161B22?style=flat-square&logo=react&logoColor=61DAFB)
![FAISS](https://img.shields.io/badge/FAISS-161B22?style=flat-square)
![Gemini](https://img.shields.io/badge/Gemini-161B22?style=flat-square&logo=googlegemini&logoColor=8E75B2)
![n8n](https://img.shields.io/badge/n8n-161B22?style=flat-square&logo=n8n&logoColor=EA4B71)

---

## More Projects

| Project | What it shows |
|:--|:--|
| **[Finance Access-Control Backend](https://github.com/Siddharthpandey20/Finance-Data-Processing-and-Access-Control-Backend)**<br><sub>FastAPI · asyncpg · SQLAlchemy 2.0 · Alembic</sub> | An async fintech API. RBAC is enforced at both the route and query level (Viewer / Analyst / Admin), money is stored as `Decimal` rather than float, primary keys are UUIDs, and soft deletes preserve the audit trail. |
| **[MP-WMS: Maintenance & Workforce Management](https://github.com/Siddharthpandey20/CSPGCL-WorkManagement-Software)**<br><sub>FastAPI · React + TypeScript · JWT · pytest · Vitest</sub> | A role-based enterprise portal for power-plant maintenance planning. It has a six-level role hierarchy, a work-order state machine, leave approvals and an audit log, and keeps all business rules in the backend. |
| **[Air-Quality Forecasting](https://github.com/Siddharthpandey20/Air_Quality_Forecasting)**<br><sub>XGBoost · LightGBM · RidgeCV stacking</sub> | Multi-pollutant forecasting on CPCB sensor data, reaching PM2.5 R² **0.883**. It is benchmarked against published results (+3.9 to +10.4%) and includes an LSTM baseline to show why tree ensembles win on this data. |

---

## Research & Publications

**2D Floor Plan Generation via Constraint Satisfaction Problem Modeling**<br>
<sub><b>Accepted · MMCITRE 2025 · Springer LNNS Vol. 2101 (forthcoming)</b> &nbsp;·&nbsp; First author &nbsp;·&nbsp; <a href="https://github.com/Siddharthpandey20/Floor_Plan_Generator">Code</a></sub><br>
Formulates floor planning as a CSP on Google OR-Tools CP-SAT, covering area, boundary, non-overlap and weighted adjacency.
It needs no training data and produces deterministic, interpretable layouts. In evaluation it reached 100% hard-constraint satisfaction and
85.82% space utilisation, with average solve times under 8 s.

**Comparative Performance Evaluation of Fixed-Time and Hierarchical Traffic Signal Control Using Real-World Urban Traffic Data**<br>
<sub><b>Accepted · NCA 2026 workshop, Italy (not yet published)</b> &nbsp;·&nbsp; First author &nbsp;·&nbsp; <a href="https://github.com/Siddharthpandey20/Hierarchical-Cooperative-Multi-Agent-RL-for-Secure-Intelligent-Transportation-Systems-">Code</a></sub><br>
A survey of traffic-signal control with a Double-DQN case study in SUMO on real SCATS rush-hour data (Melbourne).
Adaptive control cut average waiting time by over 94% versus fixed-time plans, and cooperative multi-agent control
improved network throughput by 15%. The code also includes an LSTM layer that screens sensor data for false-data-injection attacks.

**CausalLine: Influence-Aware Selective Recovery After Prompt Injection in Multi-Agent LLM Systems**<br>
<sub><b>Ongoing research · paper in preparation</b> &nbsp;·&nbsp; First author, lead developer &nbsp;·&nbsp; <a href="https://github.com/Siddharthpandey20/CausalLine">Code</a></sub><br>
Asks what to recompute after a multi-agent system is found to have consumed poisoned input. The approach is
provenance tracing with counterfactual influence attribution and verified selective replay
(details under Featured Projects, 02).

---

## Tech Stack

<table>
<tr>
<td><b>Languages</b></td>
<td>
<img alt="Python" src="https://img.shields.io/badge/Python-161B22?style=for-the-badge&logo=python&logoColor=3776AB">
<img alt="C++" src="https://img.shields.io/badge/C++-161B22?style=for-the-badge&logo=cplusplus&logoColor=00599C">
<img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-161B22?style=for-the-badge&logo=typescript&logoColor=3178C6">
<img alt="JavaScript" src="https://img.shields.io/badge/JavaScript-161B22?style=for-the-badge&logo=javascript&logoColor=F7DF1E">
<img alt="C" src="https://img.shields.io/badge/C-161B22?style=for-the-badge&logo=c&logoColor=A8B9CC">
<img alt="SQL" src="https://img.shields.io/badge/SQL-161B22?style=for-the-badge&logo=postgresql&logoColor=4169E1">
</td>
</tr>
<tr>
<td><b>Backend & APIs</b></td>
<td>
<img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-161B22?style=for-the-badge&logo=fastapi&logoColor=009688">
<img alt="Node.js" src="https://img.shields.io/badge/Node.js-161B22?style=for-the-badge&logo=nodedotjs&logoColor=5FA04E">
<img alt="Express" src="https://img.shields.io/badge/Express-161B22?style=for-the-badge&logo=express&logoColor=white">
<img alt="Prisma" src="https://img.shields.io/badge/Prisma-161B22?style=for-the-badge&logo=prisma&logoColor=white">
<img alt="SQLAlchemy" src="https://img.shields.io/badge/SQLAlchemy-161B22?style=for-the-badge&logo=sqlalchemy&logoColor=D71F00">
<img alt="Pydantic" src="https://img.shields.io/badge/Pydantic-161B22?style=for-the-badge&logo=pydantic&logoColor=E92063">
<img alt="Zod" src="https://img.shields.io/badge/Zod-161B22?style=for-the-badge&logo=zod&logoColor=3E67B1">
<img alt="LiveKit" src="https://img.shields.io/badge/LiveKit-161B22?style=for-the-badge&logo=livekit&logoColor=white">
<img alt="REST, WebSockets, SSE" src="https://img.shields.io/badge/REST_·_WebSockets_·_SSE-161B22?style=for-the-badge">
</td>
</tr>
<tr>
<td><b>Data & Messaging</b></td>
<td>
<img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-161B22?style=for-the-badge&logo=postgresql&logoColor=4169E1">
<img alt="SQLite" src="https://img.shields.io/badge/SQLite-161B22?style=for-the-badge&logo=sqlite&logoColor=4FA8D8">
<img alt="Redis" src="https://img.shields.io/badge/Redis-161B22?style=for-the-badge&logo=redis&logoColor=DC382D">
<img alt="Celery" src="https://img.shields.io/badge/Celery-161B22?style=for-the-badge&logo=celery&logoColor=37814A">
<img alt="BullMQ" src="https://img.shields.io/badge/BullMQ-161B22?style=for-the-badge">
<img alt="RabbitMQ" src="https://img.shields.io/badge/RabbitMQ-161B22?style=for-the-badge&logo=rabbitmq&logoColor=FF6600">
<img alt="ChromaDB" src="https://img.shields.io/badge/ChromaDB-161B22?style=for-the-badge">
<img alt="FAISS" src="https://img.shields.io/badge/FAISS-161B22?style=for-the-badge">
</td>
</tr>
<tr>
<td><b>AI & LLM Engineering</b></td>
<td>
<img alt="OpenAI Agents SDK" src="https://img.shields.io/badge/OpenAI_Agents_SDK-161B22?style=for-the-badge">
<img alt="LangChain" src="https://img.shields.io/badge/LangChain-161B22?style=for-the-badge&logo=langchain&logoColor=white">
<img alt="LangGraph" src="https://img.shields.io/badge/LangGraph-161B22?style=for-the-badge&logo=langgraph&logoColor=white">
<img alt="Gemini" src="https://img.shields.io/badge/Gemini-161B22?style=for-the-badge&logo=googlegemini&logoColor=8E75B2">
<img alt="Ollama" src="https://img.shields.io/badge/Ollama-161B22?style=for-the-badge&logo=ollama&logoColor=white">
<img alt="Hugging Face" src="https://img.shields.io/badge/Sentence_Transformers-161B22?style=for-the-badge&logo=huggingface&logoColor=FFD21E">
<img alt="Hybrid search" src="https://img.shields.io/badge/Hybrid_Search_(BM25_+_RRF)-161B22?style=for-the-badge">
</td>
</tr>
<tr>
<td><b>ML & Optimisation</b></td>
<td>
<img alt="PyTorch" src="https://img.shields.io/badge/PyTorch-161B22?style=for-the-badge&logo=pytorch&logoColor=EE4C2C">
<img alt="scikit-learn" src="https://img.shields.io/badge/scikit--learn-161B22?style=for-the-badge&logo=scikitlearn&logoColor=F7931E">
<img alt="XGBoost" src="https://img.shields.io/badge/XGBoost-161B22?style=for-the-badge">
<img alt="LightGBM" src="https://img.shields.io/badge/LightGBM-161B22?style=for-the-badge">
<img alt="OR-Tools" src="https://img.shields.io/badge/OR--Tools_CP--SAT-161B22?style=for-the-badge&logo=google&logoColor=4285F4">
<img alt="SUMO" src="https://img.shields.io/badge/SUMO-161B22?style=for-the-badge">
</td>
</tr>
<tr>
<td><b>Frontend</b></td>
<td>
<img alt="React" src="https://img.shields.io/badge/React-161B22?style=for-the-badge&logo=react&logoColor=61DAFB">
<img alt="Next.js" src="https://img.shields.io/badge/Next.js-161B22?style=for-the-badge&logo=nextdotjs&logoColor=white">
<img alt="Vite" src="https://img.shields.io/badge/Vite-161B22?style=for-the-badge&logo=vite&logoColor=9135FF">
</td>
</tr>
<tr>
<td><b>DevOps & Tooling</b></td>
<td>
<img alt="Docker" src="https://img.shields.io/badge/Docker-161B22?style=for-the-badge&logo=docker&logoColor=2496ED">
<img alt="GitHub Actions" src="https://img.shields.io/badge/GitHub_Actions-161B22?style=for-the-badge&logo=githubactions&logoColor=2088FF">
<img alt="Git" src="https://img.shields.io/badge/Git-161B22?style=for-the-badge&logo=git&logoColor=F05032">
<img alt="pytest" src="https://img.shields.io/badge/pytest-161B22?style=for-the-badge&logo=pytest&logoColor=0A9EDC">
<img alt="n8n" src="https://img.shields.io/badge/n8n-161B22?style=for-the-badge&logo=n8n&logoColor=EA4B71">
</td>
</tr>
</table>

---

## Leadership & Achievements

- **Head, AI/ML Club**, IIIT Naya Raipur (2025–26). I organised the AI Impact Summit 2026, Chhattisgarh, with 500+ participants.
- **2nd Place (National)**, Hack-A-Sol 2025, 300+ teams, with [Lumen](https://github.com/Siddharthpandey20/Lumen-Financial-Advisor).
- **3rd Place**, APIHub Hackathon 2025, 500+ teams, with [Study AI](https://github.com/Siddharthpandey20/Study_AI_Complete_Project).
- **National Select**, AlgoUniversity Tech Fellowship 2025 (Top 1000).
- **550+ DSA problems** solved in C++ on LeetCode and GeeksforGeeks.

## Education

**B.Tech, Computer Science & Engineering**, IIIT Naya Raipur · 2024 – 2028 · **CGPA 9.74 / 10**<br>
<sub>Coursework: Data Structures & Algorithms, OOP, Operating Systems, DBMS, Computer Networks, Distributed Systems, System Design · WBJEE All India Rank 536</sub><br>
<sub>Certifications: Agentic AI Engineering (Ed Donner) · FastAPI: The Complete Course (Eric Roby & Chad Darby) · The Complete Web Development Bootcamp (Angela Yu)</sub>

---

## GitHub & Problem Solving

<p align="center">
  <img height="170" alt="Most used languages" src="https://github-stats-extended.vercel.app/api/top-langs?username=Siddharthpandey20&layout=compact&langs_count=3&hide=html,jupyter%20notebook,css,ejs,tex,less,dockerfile,shell,solidity,mako,procfile&hide_border=true&theme=github_dark&bg_color=0D1117&title_color=2DD4BF&text_color=C9D1D9&disable_animations=true">
  <img height="170" alt="GitHub contribution streak" src="https://streak-stats.demolab.com/?user=Siddharthpandey20&hide_border=true&background=0D1117&stroke=30363D&ring=2DD4BF&fire=2DD4BF&currStreakLabel=2DD4BF&sideLabels=C9D1D9&currStreakNum=E6EDF3&sideNums=E6EDF3&dates=8B949E&disable_animations=true">
</p>

<p align="center">
  <a href="https://leetcode.com/u/_Siddharth_pandey/"><img alt="LeetCode stats" src="https://leetcard.jacoblin.cool/_Siddharth_pandey?theme=dark&font=JetBrains%20Mono&ext=heatmap&animation=false" width="500"></a>
</p>

---

<p align="center">
  <b>Open to SDE, backend and AI engineering roles.</b><br>
  <sub>
    <a href="https://www.linkedin.com/in/siddharth-a35a36324">LinkedIn</a> &nbsp;·&nbsp;
    <a href="mailto:siddharthpandey2611official@gmail.com">Email</a> &nbsp;·&nbsp;
    <a href="https://leetcode.com/u/_Siddharth_pandey/">LeetCode</a>
  </sub>
</p>
