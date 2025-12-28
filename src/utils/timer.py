import time

def question_timer(seconds):
    start = time.time()
    while time.time() - start < seconds:
        yield int(seconds - (time.time() - start))
