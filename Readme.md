# AI-Powered College Assistant

A web-based chatbot for students, faculty members, and college
administrators. It answers college-related questions by retrieving
relevant passages from institutional documents and passing those
passages to a language model.

> **Important:** The current `college_handbook.pdf` is sample/demo
> content. Replace it with verified, approved college documents before
> using the system for real student guidance.

## 1. Project overview

  Area               Technology / purpose
  ------------------ ----------------------------------------------
  Frontend           HTML, CSS, Bootstrap, JavaScript
  Backend            Python, FastAPI, Uvicorn
  Database           SQLite, SQLAlchemy
  PDF processing     pypdf
  Embeddings         Sentence Transformers
  Vector search      FAISS
  LLM                Ollama, configured as `llama3.2:3b`
  Password hashing   `pwdlib` with Argon2
  API validation     Pydantic
  Development        Windows, VS Code, Python virtual environment

## 2. Problem statement and objectives

College information can be spread across handbooks, notices, forms, and
policy documents. Users may spend time searching for routine
information, and support teams may repeatedly answer similar questions.

This project aims to: 1. Offer a simple natural-language chat interface.
2. Search college documents for relevant information. 3. Generate
answers grounded in retrieved passages. 4. Show source filename and page
information where available. 5. Establish user registration and role
data. 6. Provide a modular foundation for future administration and
access control.

## 3. System architecture

``` text
STUDENT / FACULTY / ADMIN
          |
          v
    WEB BROWSER
 HTML / CSS / Bootstrap / JavaScript
 index.html | login.html | register.html | dashboard.html
          |
      HTTP + JSON
          |
          v
    FASTAPI APPLICATION (app.py)
       |                  |
       |                  +------------------------+
       |                                           |
       v                                           v
  CHAT / RAG FLOW                            USER FLOW
       |                                      schemas.py
       v                                      models.py
  rag.py / retrieval                              |
       |                                      SQLAlchemy
       |                                          |
       v                                          v
  FAISS VECTOR INDEX                         SQLite college.db
       |
       v
  RETRIEVED TEXT + SOURCE + PAGE
       |
       v
  PROMPT CONSTRUCTION
       |
       v
  OLLAMA LOCAL MODEL (llama3.2:3b)
       |
       v
  GENERATED ANSWER
       |
       v
  JSON RESPONSE TO FRONTEND


DOCUMENT INDEXING (OFFLINE / PREPARATION FLOW)
PDF files in documents/
       |
       v
pypdf text extraction (page-aware)
       |
       v
text cleaning and chunking
       |
       v
Sentence Transformers embeddings
       |
       v
FAISS index + chunk metadata
       |
       +---- college_faiss.index
       +---- college_chunks.pkl
```

The diagram describes the logical design. An administrator upload
portal, complete role-based authorization, and production deployment are
future extensions unless they are present and tested in the current
code.

## 4. RAG processing details

### 4.1 Document ingestion and indexing

1.  Place approved PDFs in `documents/`.
2.  Extract text page by page using pypdf.
3.  Split text into smaller overlapping or appropriately sized chunks.
4.  Store metadata with each chunk, including source filename and page
    number.
5.  Generate vector embeddings with Sentence Transformers.
6.  Add vectors to a FAISS index.
7.  Save the index and chunk metadata, currently represented by
    `college_faiss.index` and `college_chunks.pkl`.

### 4.2 Question answering

1.  The user submits a question in the browser.
2.  JavaScript sends it to `POST /ask`.
3.  FastAPI calls the retrieval function in `rag.py`.
4.  FAISS returns the most relevant chunks.
5.  The backend builds context containing chunk text, source, and page.
6.  The backend sends instructions, context, and the question to Ollama.
7.  The LLM generates an answer using the supplied context.
8.  FastAPI returns JSON and the frontend displays the answer.

### 4.3 Grounding rules

The model prompt should instruct the assistant to use the supplied
context, avoid inventing college policies or dates, and say when the
answer is not available in the documents. Retrieval does not guarantee
correctness; important answers must be checked against the original
approved document.

## 5. Technology components

-   **FastAPI:** API routes, request validation integration, and serving
    frontend pages.
-   **Uvicorn:** local ASGI server.
-   **HTML/CSS/Bootstrap/JavaScript:** user interface and asynchronous
    API requests.
-   **SQLite:** local relational database for application records.
-   **SQLAlchemy:** Python ORM and database session handling.
-   **pypdf:** PDF text extraction.
-   **Sentence Transformers:** converts document chunks and questions
    into embeddings.
-   **FAISS:** similarity search over document vectors.
-   **Ollama:** local model-serving runtime.
-   **Pydantic:** validates incoming data.
-   **Argon2:** one-way password hashing for user passwords.
-   **JWT:** can provide signed access tokens when login and token
    validation are fully implemented.

## 6. Project folder structure

Based on the current workspace files:

``` text
College_Assist/
├── app.py                       # FastAPI app, routes, chat/RAG orchestration
├── database.py                  # SQLite engine, session factory, Base, get_db()
├── models.py                    # SQLAlchemy models, including User
├── schemas.py                   # Pydantic request schemas
├── rag.py                       # Document retrieval helper functions
├── documents/
│   └── college_handbook.pdf     # Current sample handbook; replace for real use
├── Frontend/
│   ├── index.html               # Chat interface
│   ├── login.html                # Login page
│   ├── register.html             # Registration page
│   └── dashboard.html            # Dashboard page
├── college.db                    # SQLite database
├── college_faiss.index            # FAISS vector index
├── college_chunks.pkl             # Retrieved-chunk text and metadata
├── test_pdf.py                    # PDF extraction test
├── test_search.py                 # Retrieval test
└── venv/                          # Local Python virtual environment
```

### Module responsibilities

  -----------------------------------------------------------------------
  File                                Responsibility
  ----------------------------------- -----------------------------------
  `app.py`                            Creates FastAPI application, serves
                                      pages, handles chat and
                                      registration routes, calls
                                      retrieval and Ollama.

  `database.py`                       Defines SQLite connection,
                                      SQLAlchemy session factory,
                                      declarative Base, and database
                                      dependency.

  `models.py`                         Defines relational tables.

  `schemas.py`                        Validates user input using
                                      Pydantic.

  `rag.py`                            Retrieves relevant document chunks
                                      and associated metadata.

  `test_pdf.py`                       Tests PDF extraction.

  `test_search.py`                    Tests semantic retrieval.
  -----------------------------------------------------------------------

## 7. Database design

The current `User` model contains:

  Column              Meaning
  ------------------- ----------------------------------------
  `id`                Integer primary key
  `full_name`         Required user name
  `email`             Required, unique, indexed email
  `hashed_password`   Argon2 password hash; never plain text
  `role`              User role; defaults to `student`
  `is_active`         Account active/inactive flag
  `created_at`        Database-generated creation timestamp

``` text
USER
----
id (PK)
full_name
email (UNIQUE)
hashed_password
role
is_active
created_at
```

The user database is separate from the FAISS index and its chunk
metadata.

## 8. API endpoints

The development history confirms the following routes. Check
`http://127.0.0.1:8000/docs` for the exact current API schema and route
availability.

  Method   Endpoint      Purpose
  -------- ------------- -----------------------------------------------------
  GET      `/chat`       Serves the chatbot page
  POST     `/ask`        Retrieves document passages and generates an answer
  POST     `/register`   Validates and stores a new user

Example `/ask` request:

``` json
{
  "message": "When is the Student Support Office open?"
}
```

Example response shape:

``` json
{
  "question": "When is the Student Support Office open?",
  "answer": "The office is open Monday to Friday, from 9:30 AM to 4:30 PM. Source: college_handbook.pdf, Page 1."
}
```

Example registration request:

``` json
{
  "full_name": "Test Student",
  "email": "student@example.com",
  "password": "Choose-A-Strong-Password"
}
```

The backend must hash the password before saving it. Never put real
passwords, tokens, or signing secrets in this README.

## 9. Local installation and run instructions

### Requirements

-   Windows 10/11
-   Python 3.13 (or a compatible version for installed dependencies)
-   VS Code
-   Ollama installed and running
-   The configured Ollama model downloaded

### Create and activate virtual environment

``` powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation in the current terminal session:

``` powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

### Install dependencies

Use the packages actually imported by your final code. The project has
used packages from these groups:

``` powershell
pip install fastapi uvicorn python-multipart sqlalchemy pydantic
pip install pypdf sentence-transformers faiss-cpu
pip install ollama pwdlib[argon2] python-jose[cryptography] email-validator
```

### Download the configured model

``` powershell
ollama pull llama3.2:3b
```

Ensure the Ollama service is running.

### Start the API server

``` powershell
python -m uvicorn app:app --reload
```

Open: - Chat: `http://127.0.0.1:8000/chat` - API docs:
`http://127.0.0.1:8000/docs`

Keep the terminal open while using the application. Press `Ctrl+C` to
stop Uvicorn.

## 10. Testing plan

### PDF and retrieval

-   Confirm PDF text extraction works.
-   Check that page numbers are correct.
-   Ask questions whose answers are present in the PDF.
-   Inspect the retrieved chunks and verify source metadata.
-   Test questions that are not covered by the document.

### API

-   Submit a valid `/ask` request through Swagger.
-   Test missing or invalid request fields.
-   Check the response when Ollama is unavailable.
-   Confirm the assistant does not invent answers when context is
    missing.

### Registration and database

-   Register a test account.
-   Verify the row exists in `college.db`.
-   Verify the stored password is an Argon2 hash, not the original
    password.
-   Try registering the same email twice.
-   Test invalid email and short password inputs.

### Frontend

-   Submit questions from the chat page.
-   Check that user and assistant messages render correctly.
-   Test error messages and responsive layout.
-   Verify login and registration pages against their backend routes.

## 11. Security, privacy, and production requirements

Before real deployment: 1. Keep password hashing enabled; never store or
log plain passwords. 2. Keep JWT signing keys in environment variables
or a secret manager. 3. Use HTTPS. 4. Validate every request on the
server. 5. Implement token validation and protect private endpoints. 6.
Enforce role permissions on the backend, not just by hiding frontend
buttons. 7. Restrict document uploads by file type and size, and
validate uploaded files. 8. Do not index confidential student records
without institutional approval and suitable access controls. 9. Avoid
returning internal exception traces or secrets to users. 10. Back up the
database, original documents, FAISS index, and chunk metadata. 11.
Verify policy answers against official documents before relying on them.

## 12. Current prototype status

Development checkpoints indicate that: - FastAPI runs locally with
Uvicorn. - The chatbot page is served by the backend. - `POST /ask` has
returned successful responses. - PDF extraction and page-aware retrieval
have been tested. - FAISS has returned relevant sample handbook
chunks. - Ollama is configured in the chat route with `llama3.2:3b`. -
SQLite and the `User` table have been created. - Registration was tested
and the password was confirmed to be Argon2-hashed.

**Not yet confirmed as complete:** full login/JWT flow, token
validation, protected routes, server-side role authorization, admin
document management, production deployment, and comprehensive security
testing. Update this section as those features are completed.

## 13. Future enhancements

-   Complete login and JWT token validation.
-   Add protected student, faculty, and administrator routes.
-   Build an admin dashboard to upload, approve, replace, and remove
    documents.
-   Rebuild the vector index when documents change.
-   Add chat history and answer feedback.
-   Track document versions and effective dates.
-   Create a standard test set to evaluate retrieval and answer quality.
-   Add multilingual support if required.
-   Deploy with HTTPS, monitoring, backups, and a production-grade
    database when needed.

## 14. Expected outcome

The project provides a modular web-based assistant that accepts
natural-language questions, retrieves relevant passages from college
documents, and generates a concise response with source information. The
current prototype demonstrates the core document-grounded
question-answering flow. Real-world use requires verified institutional
content, complete authentication and authorization, further testing, and
secure deployment.

## Disclaimer

This is an academic prototype. The sample handbook and example answers
are demonstration data, not verified college policy. Users should
consult official college offices and approved institutional publications
for authoritative decisions.
