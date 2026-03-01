from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from mangum import Mangum

STYLE = """
<style>
  * { box-sizing: border-box; margin: 0; padding: 0 }
  body {
    font-family: system-ui, sans-serif;
    background: #0f172a; color: #e2e8f0;
    min-height: 100vh;
    display: flex; align-items: center; justify-content: center;
  }
  .card {
    background: #1e293b; border-radius: 12px;
    padding: 40px 48px; text-align: center;
    max-width: 520px; width: 90%;
    box-shadow: 0 4px 24px rgba(0,0,0,.4);
  }
  h1 {
    font-size: 2.2rem; margin-bottom: 12px;
    background: linear-gradient(135deg, #38bdf8, #818cf8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  p { color: #94a3b8; margin-bottom: 16px }
  a { color: #38bdf8; text-decoration: none; display: block; margin: 6px 0 }
  a:hover { text-decoration: underline }
  .big { font-size: 3rem; font-weight: bold; color: #38bdf8; margin: 16px 0; line-height: 1 }
  .muted { color: #64748b; font-size: .8rem; margin-top: 24px; display: block }
  label { display: block; color: #94a3b8; margin-bottom: 4px; font-size: .95rem }
  input {
    width: 100%; padding: 12px 14px; border-radius: 8px;
    border: 1px solid #334155; background: #0f172a;
    color: #e2e8f0; font-size: 1rem; margin: 16px 0 10px; outline: none;
  }
  input:focus { border-color: #38bdf8 }
  button {
    background: linear-gradient(135deg, #38bdf8, #818cf8);
    color: #0f172a; border: none; border-radius: 8px;
    padding: 11px 24px; font-size: 1rem; font-weight: 700;
    cursor: pointer; width: 100%; margin-top: 4px;
  }
  button:hover { opacity: .9 }
</style>
"""

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return f"""<!doctype html>
<html>
  <head>
    {STYLE}
    <title>FastAPI Demo</title>
  </head>
  <body>
    <div class="card">
      <h1>FastAPI Lambda</h1>
      <p>A Python app built with FastAPI, running on AWS Lambda.</p>
      <form onsubmit="event.preventDefault(); location='/greet?name=' + this.elements[0].value">
        <label>What's your name?</label>
        <input type="text" placeholder="" autofocus>
        <button type="submit">Say hello &rarr;</button>
      </form>
      <a href="/about">&rarr; about</a>
      <span class="muted">powered by FastAPI + Mangum</span>
    </div>
  </body>
</html>"""


@app.get("/greet", response_class=HTMLResponse)
def greet(name: str = Query(default="World")) -> str:
    return f"""<!doctype html>
<html>
  <head>
    {STYLE}
    <title>Hello, {name}!</title>
  </head>
  <body>
    <div class="card">
      <h1>Hello,</h1>
      <div class="big">{name}!</div>
      <p>Greetings from a FastAPI Lambda.</p>
      <a href="/">&larr; back home</a>
    </div>
  </body>
</html>"""


@app.get("/about", response_class=HTMLResponse)
def about() -> str:
    return f"""<!doctype html>
<html>
  <head>
    {STYLE}
    <title>About</title>
  </head>
  <body>
    <div class="card">
      <h1>About</h1>
      <p>
        This app is built with FastAPI and deployed on AWS Lambda
        via Mangum, which adapts ASGI apps to the Lambda event format.
      </p>
      <a href="/">&larr; back home</a>
      <span class="muted">source: examples/fastapi-lambda-demo/main.py</span>
    </div>
  </body>
</html>"""


# Mangum wraps the FastAPI ASGI app for Lambda's event/context interface.
handler = Mangum(app)
