# 💬 Career Conversation App

This project provides an interactive **Gradio chatbot** that simulates a professional career conversation.  
It uses the **OpenAI API** and reads your background from PDFs you place in the `/me` folder (e.g., LinkedIn export or CV).

**Demo (chat-only):**  
👉 [https://huggingface.co/spaces/Uliana333/career_conversation](https://huggingface.co/spaces/Uliana333/career_conversation)

> ⚠️ On Hugging Face Spaces, outbound notifications (Pushover, SMTP email) are typically blocked.  
> For full functionality, run the app locally.

---

## 🧠 Technologies Used

- **Python 3.11** – main programming language  
- **Gradio** – chat-based web interface  
- **OpenAI GPT-4o-mini** – model for conversation and reasoning  
- **OpenAI text-embedding-3-small** – to build semantic document search  
- **FAISS (Facebook AI Similarity Search)** – fast similarity indexing for embedded texts  
- **PyPDF** – extract text from PDFs  
- **Pushover API** – optional push notifications  
- **SMTP (email automation)** – optional email replies to users  
- **dotenv** – secure environment variable management  

---

## 🧩 Features

- Loads all PDFs from `/me` as background knowledge  
- Professional conversation powered by **OpenAI GPT-4o-mini**  
- Optional **Pushover** notifications and **email auto-reply**  
- Secrets are stored locally in `.env` (never committed)

---

## ⚙️ Requirements

- Python **3.10+**  
- **OpenAI API key** → [Get one here](https://platform.openai.com/account/api-keys)  
- *(Optional)* Pushover account for push notifications → [https://pushover.net/](https://pushover.net/)  
- *(Optional)* Gmail or another SMTP account for outgoing emails  

---

## 🚀 Running Locally

### 1️⃣ Clone the repository

```bash
git clone https://github.com/Uliana0203/career_conversation.git
cd career_conversation
```

---

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

### 3️⃣ Create a `.env` file

Create a file named `.env` in the project root with the following content:

```bash
# OpenAI API key
OPENAI_API_KEY=sk-...

# (optional) Pushover notifications
PUSHOVER_USER=uxxxxxxxxxxxxxxxxxxxxxxx
PUSHOVER_TOKEN=xxxxxxxxxxxxxxxxxxxxxxx

# (optional) Outgoing email (example: Gmail)
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

> 💡 If you don’t use notifications or email, you can omit those lines.

---

### 4️⃣ Add your profile documents

Place your **LinkedIn export**, **CV**, or other professional PDFs in the `/me` folder.  
All `.pdf` files in this folder are automatically read when the app starts.

Example structure:

```
career_conversation/
│
├── me/
│   ├── linkedin.pdf
│   ├── cv.pdf
│
├── app.py
├── requirements.txt
└── .env
```

---

### 5️⃣ Run the app

```bash
python app.py
```

After launch, you’ll see something like:

```
Running on local URL:  http://127.0.0.1:7860
```

Open that link in your browser.

---

## 💡 Example Conversation

**User:**  
> Can you send me your publication list to my email?

**Assistant:**  
> Of course! Could you please tell me your name and email address so I can send it to you?

---

## 🛡️ Security Notes

- **Do not upload** your `.env` file or API keys anywhere (especially to GitHub).  
- On Hugging Face Spaces, your `.env` values must be added manually under:  
  **Settings → Variables and Secrets**  
- The online demo does **not** send emails or Pushover notifications — these work only locally.

---

## 🧠 About

Created by **Uliana Zbezhkhovska**  

