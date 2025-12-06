import core.llm.code.code_praser
from core.llm.code import code_praser

praser = code_praser.CodePraser

text1 = """
test1
```bash
hi
```
```python
test
```
"""

print(praser(text1))