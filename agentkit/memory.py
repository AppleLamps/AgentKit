# agentkit/memory.py

class Memory:
    def __init__(self):
        self.store = []

    def save(self, prompt: str, response: str):
        self.store.append({"prompt": prompt, "response": response})

    def history(self):
        return self.store