history = []

def add(q, a):
    history.append((q, a))

def get():
    return history[-5:]