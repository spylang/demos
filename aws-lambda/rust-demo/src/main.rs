use lambda_http::{run, service_fn, Body, Error, Request, RequestExt, Response};

const CDN: &str = concat!(
    r#"<link rel="stylesheet" href=""#,
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
    r#"">"#
);

async fn handler(req: Request) -> Result<Response<Body>, Error> {
    let path   = req.uri().path();
    let method = req.method().as_str();
    match (method, path) {
        ("GET", "/")      => index_handler(),
        ("GET", "/greet") => greet_handler(&req),
        _                 => not_found(),
    }
}

fn index_handler() -> Result<Response<Body>, Error> {
    let body = format!(
        r#"<!doctype html>
<html>
  <head>{CDN}<title>Rust Demo</title></head>
  <body class="container mt-5">
    <h1>Rust on AWS Lambda</h1>
    <form method="get" action="/greet">
      <label class="form-label">What's your name?</label>
      <input class="form-control mb-2" type="text" name="name" autofocus>
      <button class="btn btn-primary" type="submit">Say hello</button>
    </form>
  </body>
</html>"#
    );
    Ok(Response::builder()
        .status(200)
        .header("Content-Type", "text/html")
        .body(body.into())?)
}

fn greet_handler(req: &Request) -> Result<Response<Body>, Error> {
    let name = req
        .query_string_parameters()
        .first("name")
        .unwrap_or("World")
        .to_string();
    let body = format!(
        r#"<!doctype html>
<html>
  <head>{CDN}<title>Hello, {name}!</title></head>
  <body class="container mt-5">
    <h1>Hello, {name}!</h1>
    <p>Greetings from a Rust Lambda.</p>
    <a href="/">&#8592; back home</a>
  </body>
</html>"#
    );
    Ok(Response::builder()
        .status(200)
        .header("Content-Type", "text/html")
        .body(body.into())?)
}

fn not_found() -> Result<Response<Body>, Error> {
    Ok(Response::builder()
        .status(404)
        .header("Content-Type", "application/json")
        .body(r#"{"message": "Not Found"}"#.into())?)
}

#[tokio::main(flavor = "current_thread")]
async fn main() -> Result<(), Error> {
    run(service_fn(handler)).await
}
