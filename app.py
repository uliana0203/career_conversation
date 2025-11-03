from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
import smtplib
from email.mime.text import MIMEText
from pypdf import PdfReader
import numpy as np
import faiss
import gradio as gr

# ==============================
# Load environment variables
# ==============================
load_dotenv(override=True)


# --------------------------------------------
# Utility: Send a push notification to Pushover
# --------------------------------------------
def push(text):
    """Send text notifications via Pushover."""
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


# --------------------------------------------
# Utility: Send confirmation email to user
# --------------------------------------------
def send_email(to_email, name, question=""):
    """Send an acknowledgment email to the provided address."""
    sender = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    message_body = f"""Dear {name},

Thank you for getting in touch!
We’ve received your message and the question below:

“{question}”

I’ll reply to you soon.

Kind regards,
Uliana Zbezhkhovska
"""
    msg = MIMEText(message_body)
    msg["Subject"] = "Thank you for reaching out!"
    msg["From"] = sender
    msg["To"] = to_email

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)


# --------------------------------------------
# Tools for recording user actions
# --------------------------------------------
def record_user_details(email, name="Name not provided", notes="not provided", question="not provided"):
    """Record user details and send them a confirmation email."""
    if not email or email.strip().lower() == os.getenv("SMTP_USER", "").lower():
        push(f"No valid user email provided. Skipping email send.\nName: {name}\nQuestion: {question}")
        return {"recorded": "skipped_no_email"}

    push(f"New contact: {name}, {email}\nNotes: {notes}\nQuestion: {question}")
    try:
        send_email(email, name, question)
    except Exception as e:
        push(f"Email failed: {e}")
    return {"recorded": "ok"}


def record_unknown_question(question):
    """Record any question that couldn't be answered."""
    push(f"Recording unknown question: {question}")
    return {"recorded": "ok"}


# Tool schemas for OpenAI function calling
record_user_details_json = {
    "name": "record_user_details",
    "description": "Record a user's contact info and the question they asked.",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "User email"},
            "name": {"type": "string", "description": "User name"},
            "notes": {"type": "string", "description": "Additional info"},
            "question": {"type": "string", "description": "Short summary (3–10 words) of what the user asked"}
        },
        "required": ["email", "question"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Record any question that couldn't be answered.",
    "parameters": {
        "type": "object",
        "properties": {"question": {"type": "string"}},
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json}
]


# ======================================================
# Main class representing the "virtual Uliana"
# ======================================================
class Me:
    def __init__(self, api_key):
        """Initialize chatbot with user's API key."""
        self.openai = OpenAI(api_key=api_key)
        self.name = "Uliana Zbezhkhovska"
        self.folder_path = os.path.join(os.path.dirname(__file__), "me")
        self.docs = self.load_pdfs()
        self.embeddings = self.embed_docs()
        self.index = self.build_index()

    def load_pdfs(self):
        """Read and combine all PDF texts from the 'me' folder."""
        texts = []
        for filename in os.listdir(self.folder_path):
            if filename.lower().endswith(".pdf"):
                file_path = os.path.join(self.folder_path, filename)
                reader = PdfReader(file_path)
                text = "".join(page.extract_text() or "" for page in reader.pages)
                texts.append(text)
        return texts

    def embed_docs(self):
        """Generate embeddings for each PDF document."""
        result = self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=self.docs
        )
        return [np.array(r.embedding) for r in result.data]

    def build_index(self):
        """Build FAISS index for document retrieval."""
        dim = len(self.embeddings[0])
        index = faiss.IndexFlatL2(dim)
        index.add(np.array(self.embeddings))
        return index

    def search(self, query, k=3):
        """Retrieve the most relevant document snippets."""
        q_emb = self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=query
        ).data[0].embedding
        D, I = self.index.search(np.array([q_emb]), k)
        return [self.docs[i] for i in I[0]]

    def handle_tool_call(self, tool_calls):
        """Execute external tools (e.g., record email, log unknown question)."""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id
            })
        return results

    def system_prompt(self):
        """Define system behavior and context."""
        return f"""
    You are acting as {self.name}. You are answering questions on {self.name}'s website.
    Your role is to respond professionally, politely, and clearly to questions about your career, background, and research.

    Ask for the user's **name** and **email** ONLY if the user explicitly asks you to *send* something 
    (e.g., “send me your publications”, “email me the file”, “share materials”, “please send details”).  
    Otherwise, just answer normally without requesting personal data.

    When the user asks you to send something:
    1. Politely ask for their **name** first (e.g., “Could you please tell me your name so I can include it in the message?”).
    2. If the user prefers not to share their name, proceed politely using "Name not provided".
    3. Then ask for their **email address**.
    4. Once a valid email is provided, politely confirm that it is correct before sending anything.
    5. When both name (or "Name not provided") and email are known, call the tool `record_user_details` with:
    - the email,
    - the name (either the provided one or "Name not provided"),
    - a short English summary (3–10 words) of what the user asked — not the raw text.
        Examples:
        - "Question about publications"
        - "Request for collaboration"
        - "Inquiry about AI research"
        - "Asked about current projects"

    Do NOT call `record_user_details` unless the user has clearly requested something to be sent by email.

    If a question cannot be answered, use `record_unknown_question` with a short English summary.

    Always stay polite, concise, and professional.

    ##Profile:
    {' '.join(self.docs)}
    """

    def chat(self, message, history):
        """Main chat logic that combines memory and tool handling."""
        context_snippets = self.search(message, k=2)
        context_text = "\n\n".join(context_snippets)

        messages = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "system", "content": f"Relevant context:\n{context_text}"},
        ] + history + [{"role": "user", "content": message}]

        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools
            )
            if response.choices[0].finish_reason == "tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content


# ======================================================
# Gradio Interface
# ======================================================
def launch_app():
    """Launch the Gradio web app with dynamic OpenAI key input."""
    api_key_box = gr.Textbox(label="Enter your OpenAI API key", type="password")
    status = gr.Markdown("")

    def save_key(api_key):
        global me
        if not api_key.strip().startswith("sk-"):
            return "❌ Invalid API key format."
        me = Me(api_key)
        return "✅ API key saved! You can now chat below."

    def chat_interface(message, history):
        if 'me' not in globals():
            return "Please enter your OpenAI API key above to start chatting."
        return me.chat(message, history)

    with gr.Blocks() as demo:
        gr.Markdown("## 💬 Chat with Uliana Zbezhkhovska")
        with gr.Row():
            api_key_box.render()
            save_button = gr.Button("Save key")
        status.render()
        save_button.click(fn=save_key, inputs=api_key_box, outputs=status)
        gr.ChatInterface(fn=chat_interface, type="messages")
    demo.launch()


if __name__ == "__main__":
    launch_app()
