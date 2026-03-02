from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from mangum import Mangum

CDN = '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">'

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return f"""<!doctype html>
<html>
  <head>{CDN}<title>FastAPI Demo</title></head>
  <body class="container mt-5">
    <h1>FastAPI on AWS Lambda</h1>
    <form method="get" action="/greet">
      <label class="form-label">What's your name?</label>
      <input class="form-control mb-2" type="text" name="name" autofocus>
      <button class="btn btn-primary" type="submit">Say hello</button>
    </form>
  </body>
</html>"""


@app.get("/greet", response_class=HTMLResponse)
def greet(name: str = Query(default="World")) -> str:
    return f"""<!doctype html>
<html>
  <head>{CDN}<title>Hello, {name}!</title></head>
  <body class="container mt-5">
    <h1>Hello, {name}!</h1>
    <p>Greetings from a FastAPI Lambda.</p>
    <a href="/">← back home</a>
  </body>
</html>"""


# Mangum wraps the FastAPI ASGI app for Lambda's event/context interface.
handler = Mangum(app)
