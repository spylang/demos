package main

import (
	"context"
	"fmt"
	"net/url"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
)

const cdn = `<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">`

func handler(ctx context.Context, req events.LambdaFunctionURLRequest) (events.LambdaFunctionURLResponse, error) {
	method := req.RequestContext.HTTP.Method
	path := req.RawPath

	switch {
	case method == "GET" && path == "/":
		return indexHandler()
	case method == "GET" && path == "/greet":
		return greetHandler(req.RawQueryString)
	default:
		return events.LambdaFunctionURLResponse{
			StatusCode: 404,
			Headers:    map[string]string{"Content-Type": "application/json"},
			Body:       `{"message": "Not Found"}`,
		}, nil
	}
}

func indexHandler() (events.LambdaFunctionURLResponse, error) {
	body := fmt.Sprintf(`<!doctype html>
<html>
  <head>%s<title>Go Demo</title></head>
  <body class="container mt-5">
    <h1>Go on AWS Lambda</h1>
    <form method="get" action="/greet">
      <label class="form-label">What's your name?</label>
      <input class="form-control mb-2" type="text" name="name" autofocus>
      <button class="btn btn-primary" type="submit">Say hello</button>
    </form>
  </body>
</html>`, cdn)
	return events.LambdaFunctionURLResponse{
		StatusCode: 200,
		Headers:    map[string]string{"Content-Type": "text/html"},
		Body:       body,
	}, nil
}

func greetHandler(rawQuery string) (events.LambdaFunctionURLResponse, error) {
	name := "World"
	if q, err := url.ParseQuery(rawQuery); err == nil {
		if n := q.Get("name"); n != "" {
			name = n
		}
	}
	body := fmt.Sprintf(`<!doctype html>
<html>
  <head>%s<title>Hello, %s!</title></head>
  <body class="container mt-5">
    <h1>Hello, %s!</h1>
    <p>Greetings from a Go Lambda.</p>
    <a href="/">&#8592; back home</a>
  </body>
</html>`, cdn, name, name)
	return events.LambdaFunctionURLResponse{
		StatusCode: 200,
		Headers:    map[string]string{"Content-Type": "text/html"},
		Body:       body,
	}, nil
}

func main() {
	lambda.Start(handler)
}
