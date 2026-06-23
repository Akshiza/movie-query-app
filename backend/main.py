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

client = genai.Client(api_key=os.getenv("GEMINI API KEY"))

import os
DB_PATH = os.path.join(os.path.dirname(__file__), "../data/movies.db")

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

# ── API endpoint ──────────────────────────────────────────────

class Question(BaseModel):
    question: str

@app.post("/ask")
async def ask(q: Question):
    messages = [types.Content(role="user", parts=[types.Part(text=q.question)])]

    max_iterations = 5
    for _ in range(max_iterations):
        response = client.models.generate_content(
            model="gemini-1.5-flash-latest",
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

    return {"answer": final_answer}