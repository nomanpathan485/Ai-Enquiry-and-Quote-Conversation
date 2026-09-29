# 🏨 AI Hotel Enquiry & Quote Engine

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![AI](https://img.shields.io/badge/AI-Groq%20LPU-orange.svg)](https://groq.com/)
[![API](https://img.shields.io/badge/API-RateLoc-green.svg)](https://rateloc.com/)

An intelligent automation prototype designed to streamline the hotel quotation process. This system transforms unstructured guest enquiries into structured travel requirements, interacts with the RateLoc API for real-time availability, and curates a tiered selection of hotel options.

## 🚀 Key Features

- **Intelligent Requirement Extraction**: Uses LLMs to parse natural language enquiries into a structured data format.
- **Dynamic Gap Analysis**: Automatically identifies missing information and generates targeted follow-up questions for the user.
- **Tiered Quote Generation**: Implements a logic-based selection process to provide three distinct options:
  - 💰 **Budget**: The most cost-effective available option.
  - ⭐ **Balanced**: A high-ranking option based on quality/value.
  - 💎 **Premium**: The top-tier luxury experience.
- **Real-time Integration**: Direct connection to the RateLoc API for live pricing and availability.

## 🛠️ Tech Stack

- **Language:** Python
- **LLM Orchestration:** Groq (LPU Inference)
- **Data Source:** RateLoc API
- **Environment:** `.env` for secure credential management

## 📦 Installation & Setup

### Prerequisites
- Python 3.9 or higher
- A Groq API Key
- A RateLoc Bearer Token

### Setup
1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd "AI Enquiry & Quote Conversion"
   ```

2. **Environment Configuration:**
   Create a `.env` file in the root directory and add your credentials:
   ```env
   GROQ_API_KEY=your_groq_key_here
   RATELOC_BEARER_TOKEN=your_rateloc_token_here
   ```

3. **Install Dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

## 🖥️ Usage
Run the application via the CLI:
```bash
python live_app.py
```

## ⚠️ Project Scope & Limitations
*This project is a technical prototype developed for demonstration purposes and is not intended for production use.*

- **Search Accuracy**: Results are based on real-time API responses; availability and pricing may fluctuate.
- **Coverage**: Currently supports single-room searches and a specific set of mapped nationality/residence codes.
- **Verification**: All generated quotes should be manually verified through the official booking channel before being presented to a client.
