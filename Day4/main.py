from fastapi import FastAPI

app=FastAPI()

@app.get("/")

def read_root():
    return{"Hello": "FastAPI"}

@app.get("/greet/{name}")
def greet_name(name: str, q: str=None):
    return {"greet": name, "q":q}