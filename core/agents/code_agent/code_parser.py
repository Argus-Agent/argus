import re

def CodeParser(text: str):
    pattern = r"```([\w\+\-\.]*)\n([\s\S]*?)\n```"
    matches = re.findall(pattern, text)
    
    results = []
    for lang, code in matches:
        results.append({"lang": lang.strip() if lang else "text", "code": code})
    return results