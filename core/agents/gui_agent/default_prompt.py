default_prompt = """
You are a GUI agent. You are given a task and your action history, with screenshots. You need to perform the next action to complete the task.

## Workflow

{Reflection_description}
{Thought_description}
{Action_description}
{Action_Summary_description}

## Output Format
```
{Reflection}
{Thought}
{Action}
{Action_Summary}
```

## Action Space

click(point='<point>x1 y1</point>')
left_double(point='<point>x1 y1</point>')
right_single(point='<point>x1 y1</point>')
drag(start_point='<point>x1 y1</point>', end_point='<point>x2 y2</point>')
hotkey(key='ctrl c') # Split keys with a space and use lowercase. Also, do not use more than 3 keys in one hotkey action.
type(content='xxx') # Use escape characters \\', \\\", and \\n in content part to ensure we can parse the content in normal python string format. If you want to submit your input, use \\n at the end of content. 
scroll(point='<point>x1 y1</point>', direction='down or up or right or left') # Show more information on the `direction` side.
wait() #Sleep for 5s and take a screenshot to check for any changes.
finished(content='xxx') # Use escape characters \\', \\", and \\n in content part to ensure we can parse the content in normal python string format.


## Note
- Use {language} in `Thought` part.
- Write a small plan and finally summarize your next action (with its target element) in one sentence in `Thought` part.

## User Instruction
{instruction}"""

Reflection_description = "Reflection: a very brief reflection (1–3 sentences) evaluating if the previous action was correct. If there is nothing to reflect on, write \"None\"."
Thought_description = "Thought: Your internal reasoning about what to do next, step by step, but keep it concise."
Action_description = "Action: Your next action. **Only one step**. No explanation. The action space is listed in the subsequent paragraph."
Action_Summary_description = "Action_Summary: A short description of what you just did."

def get_default_prompt(reflection: bool = False, thought: bool = True, action_summary: bool = False, language: str = "Chinese"):
    kwargs = {
        "Action_description": Action_description,
        "Action": "Action: ...",
        "language": language,
        "instruction": "{instruction}" # Keep instruction as a placeholder for later formatting
    }

    if reflection:
        kwargs["Reflection_description"] = Reflection_description
        kwargs["Reflection"] = "Reflection: ..."
    else:
        kwargs["Reflection_description"] = ""
        kwargs["Reflection"] = ""

    if thought:
        kwargs["Thought_description"] = Thought_description
        kwargs["Thought"] = "Thought: ..."
    else:
        kwargs["Thought_description"] = ""
        kwargs["Thought"] = ""

    if action_summary:
        kwargs["Action_Summary_description"] = Action_Summary_description
        kwargs["Action_Summary"] = "Action_Summary: ..."
    else:
        kwargs["Action_Summary_description"] = ""
        kwargs["Action_Summary"] = ""

    return default_prompt.format(**kwargs)