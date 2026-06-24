from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/movies.db")

# ── Fallback model list ───────────────────────────────────────
MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-3.5-flash",
]

# ── MCP-style tools ──────────────────────────────────────────

def get_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
    schema = cursor.fetchall()
    conn.close()
    return str(schema)

def query_database(sql: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        conn.close()
        return {"columns": cols, "rows": rows[:50]}
    except Exception as e:
        return {"error": str(e)}

# ── Tool definitions ──────────────────────────────────────────

tools = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="get_schema",
                description="Returns the database schema. Always call this first before writing SQL.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={}
                )
            ),
            types.FunctionDeclaration(
                name="query_database",
                description="Executes a SQLite SQL query on the movies database and returns results.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "sql": types.Schema(
                            type="STRING",
                            description="A valid SQLite SQL query"
                        )
                    },
                    required=["sql"]
                )
            )
        ]
    )
]

SYSTEM_PROMPT = """You are a movie data analyst assistant.
You have access to a movies database with 9837 movies.
Columns: release_date, title, overview, popularity, vote_count, vote_average, original_language, genre, poster_url.
Always call get_schema first, then query_database with valid SQLite SQL.
After getting results, explain them clearly to the user.
For genre filtering use LIKE e.g. WHERE genre LIKE '%Action%'."""

# ── Core ask function with a single model ────────────────────

def run_with_model(model_name: str, question: str):
    messages = [types.Content(role="user", parts=[types.Part(text=question)])]

    for _ in range(5):
        response = client.models.generate_content(
            model=model_name,
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=tools
            )
        )

        candidate = response.candidates[0].content
        messages.append(candidate)

        has_function_call = False
        tool_results = []

        for part in candidate.parts:
            if part.function_call:
                has_function_call = True
                fn_name = part.function_call.name
                fn_args = dict(part.function_call.args)

                if fn_name == "get_schema":
                    result = get_schema()
                elif fn_name == "query_database":
                    result = query_database(fn_args.get("sql", ""))
                else:
                    result = {"error": "Unknown tool"}

                tool_results.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=fn_name,
                            response={"result": str(result)}
                        )
                    )
                )

        if tool_results:
            messages.append(types.Content(role="user", parts=tool_results))

        if not has_function_call:
            break

    final_answer = ""
    for part in response.candidates[0].content.parts:
        if part.text:
            final_answer += part.text

    return final_answer

# ── API endpoint ──────────────────────────────────────────────

class Question(BaseModel):
    question: str

@app.post("/ask")
async def ask(q: Question):
    last_error = None

    for model_name in MODELS:
        try:
            print(f"Trying model: {model_name}")
            answer = run_with_model(model_name, q.question)
            print(f"Success with model: {model_name}")
            return {"answer": answer, "model_used": model_name}
        except Exception as e:
            error_str = str(e)
            print(f"Model {model_name} failed: {error_str}")
            last_error = error_str

            # Only retry on quota/overload errors
            if "503" in error_str or "429" in error_str or "UNAVAILABLE" in error_str or "EXHAUSTED" in error_str:
                continue
            else:
                # For other errors (404, auth) stop immediately
                break

    return {"answer": f"All models are currently unavailable. Please try again in a few minutes. Error: {last_error}"}