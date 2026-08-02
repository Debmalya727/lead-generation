# 🚀 LeadForgeAI
**Autonomous Multi-Agent Sales Intelligence & B2B Prospecting Platform**

LeadForgeAI is an enterprise-grade AI sales intelligence platform designed to completely automate and replace manual, tedious B2B prospecting. By deploying a team of autonomous AI agents, it discovers leads, audits their web presence, scores their potential, and writes highly personalized outreach campaigns.

---

## ✨ Key Features & The AI Workforce
Our system operates using specialized AI agents that communicate asynchronously to get the job done.

*   🤵 **Manager Agent:** The boss. Takes your high-level query and coordinates the workflow.
*   🧠 **Planner Agent:** Breaks down your goals into actionable scraping and filtering steps.
*   🕷️ **Scraper Agent:** Crawls local directories (like Google Maps & Justdial) to build the initial lead list.
*   🕵️ **Researcher Agent:** Deep-dives into individual websites to extract emails, contacts, and tech stacks.
*   🔬 **Website Analyzer:** Audits the lead's website for mobile performance, missing call-to-actions, and weak copywriting.
*   🎯 **Lead Scorer:** Ranks prospects (0-100) based on how well they match your Ideal Customer Profile (ICP).
*   ✉️ **Outreach Agent:** The closer. Drafts hyper-personalized emails referencing the specific gaps found by the Analyzer.

---

## 🛠️ Technology Stack
Built for high scalability and asynchronous processing, utilizing a modern full-stack web development architecture.

### 💻 Presentation Layer (Frontend)
*   **Core:** React + Vite + TypeScript
*   **3D Visuals:** React Three Fiber, Three.js, and Theatre.js for interactive dashboards
*   **State & Sync:** Zustand and TanStack Query

### ⚙️ Application Layer (Backend)
*   **Core Framework:** FastAPI (Python 3.12)
*   **Real-time Updates:** WebSockets for live streaming scraping sessions

### 🗄️ Processing & Database Layer
*   **Database:** MongoDB utilizing the Motor async driver and Beanie ODM
*   **Task Queue:** Redis caching combined with a Celery Worker Cluster for heavy lifting
*   **Crawling Engine:** Playwright (headless browsing) and BeautifulSoup
*   **AI Inference:** Integrations via OpenRouter or Ollama

---

## 📖 How It Works (The Lead Generation Story)

1.  **The Ask:** You log into the React dashboard and enter a prompt like *"Find HVAC services in Chicago"*.
2.  **The Handoff:** The React UI sends this to the FastAPI backend, which drops a task into the Redis queue.
3.  **The Crawl:** A background Celery worker wakes up, and the **Manager Agent** deploys the **Scraper Agent** to comb through directories using Playwright.
4.  **The Audit:** Newly discovered businesses are saved to MongoDB as "Leads". The **Researcher** and **Analyzer** agents then visit each lead's website to extract missing info and grade their web copy.
5.  **The Pitch:** Finally, the **Outreach Agent** reviews the website's weak points and writes a custom, compelling email draft offering your services as the solution. 
6.  **The Update:** Throughout this whole process, FastAPI pushes live WebSockets updates to your dashboard so you can watch the agents work in real-time.

---

## 🚀 Getting Started (Local Development)

The entire platform is fully containerized for easy deployment.

```bash
# 1️⃣ Clone the repository
git clone <repository_url>
cd LeadForgeAI

# 2️⃣ Create your environment variables
cp .env.example .env

# 3️⃣ Build and start all services
docker-compose up --build
```

**Port Routing Map:**
*   🌐 **React Client:** `http://localhost:5173`
*   🔌 **FastAPI Backend:** `http://localhost:8000`
*   📚 **API Docs:** `http://localhost:8000/docs`
*   🗄️ **MongoDB Database:** `mongodb://localhost:27017`
