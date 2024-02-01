
def read_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(path: str, text: str) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
