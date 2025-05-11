class Document:
    def __init__(self, id: str, content: str):
        self.id = id
        self.content = content

    def to_file(self, file_path: str):
        with open(file_path, 'w') as f:
            f.write(self.content)

def doc_from_file(file_path: str) -> Document:
    with open(file_path, 'r') as f:
        content = f.read()
    return Document(id=file_path, content=content)