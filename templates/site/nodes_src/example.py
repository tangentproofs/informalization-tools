# Explainer nodes for this site. Every .py file here (except _helpers) defines NODES; engine/tools/write_nodes.py
# turns them into nodes/<id>.md with valid YAML. See prompts/draft-explainer.md for the rules.
NODES = []
def node(id, title, summary, body, quiz, caveats=(), widgets=None):
    NODES.append(dict(id=id, title=title, summary=summary, body=body, quiz=quiz, caveats=list(caveats), widgets=widgets))
def q(text, choices, answer, explain):
    return {"q": text, "type": "choice", "choices": choices, "answer": answer, "explain": explain}
