import json

def load_questions():
    with open("src/exam/questions.json") as f:
        return json.load(f)
