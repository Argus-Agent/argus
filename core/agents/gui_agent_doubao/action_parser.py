import re
import time
import logging
from typing import Dict, Any, Tuple, Optional
from core.tools import mouse, keyboard

def parse_response(response: str) -> str:
    """
    Extract the Action part from the model response.
    """
    if "Action:" in response:
        return response.split("Action:")[-1].strip()
    return response.strip()

def parse_action(action_str: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parse the action string into function name and arguments.
    Example: click(point='<point>450 416</point>') -> ('click', {'point': '<point>450 416</point>'})
    """
    # Match function name and arguments
    match = re.match(r"(\w+)\((.*)\)", action_str)
    if not match:
        # Handle cases without arguments like wait()
        if action_str.endswith("()"):
             return action_str[:-2], {}
        return "", {}

    function_name = match.group(1)
    args_str = match.group(2)
    
    args = {}
    # Parse arguments: key='value' or key="value"
    # This regex handles simple cases. For more complex nested quotes, a parser might be needed.
    # But based on the prompt, args are simple strings.
    # We need to handle escaped characters in content='...'
    
    # A simple split by comma might fail if content contains comma.
    # Let's use a regex to find key='value' pairs.
    # Value can be single quoted or double quoted.
    
    # Pattern to match key='value' or key="value"
    # We use non-greedy match for value content
    arg_pattern = re.compile(r"(\w+)=(['\"])(.*?)\2")
    
    for match in arg_pattern.finditer(args_str):
        key = match.group(1)
        value = match.group(3)
        # Unescape \\n, \\', \\"
        value = value.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"')
        args[key] = value
        
    return function_name, args

def extract_point(point_str: str) -> Optional[Tuple[int, int]]:
    """
    Extract x, y from <point>x y</point>
    """
    match = re.search(r"<point>(\d+)\s+(\d+)</point>", point_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None

def get_action_coordinates(action_name: str, args: Dict[str, Any], screen_width: int, screen_height: int) -> Optional[Dict[str, int]]:
    """
    Get the absolute coordinates for the action.
    Returns dict with keys 'x', 'y' (and 'xx', 'yy' for drag) or None.
    """
    def to_abs(x_rel, y_rel):
        return int(x_rel / 1000 * screen_width), int(y_rel / 1000 * screen_height)

    if action_name in ["click", "left_double", "right_single", "scroll"]:
        if 'point' in args:
            pt = extract_point(args['point'])
            if pt:
                x, y = to_abs(*pt)
                return {'x': x, 'y': y}
    elif action_name == "drag":
        if 'start_point' in args:
            start_pt = extract_point(args['start_point'])
            if start_pt:
                x, y = to_abs(*start_pt)
                result = {'x': x, 'y': y}
                
                if 'end_point' in args:
                    end_pt = extract_point(args['end_point'])
                    if end_pt:
                        xx, yy = to_abs(*end_pt)
                        result['xx'] = xx
                        result['yy'] = yy
                return result
    return None

def map_action_to_function(action_name: str, args: Dict[str, Any], screen_width: int, screen_height: int, offset_x: int = 0, offset_y: int = 0) -> None:
    """
    Map the parsed action to the actual mouse/keyboard function calls.
    """
    logging.info(f"Executing action: {action_name} with args: {args}")
    
    # Helper to convert relative coordinates (0-1000) to absolute
    def to_abs(x_rel, y_rel):
        # return int(x_rel / 1000), int(y_rel / 1000)
        # print (f"origin width: {screen_width}, height: {screen_height}")
        return int(x_rel / 1000 * screen_width) + offset_x, int(y_rel / 1000 * screen_height) + offset_y

    if action_name == "click":
        if 'point' in args:
            pt = extract_point(args['point'])
            if pt:
                x, y = to_abs(*pt)
                print(f"Clicking at: {x}, {y}")
                mouse.click(x, y)
    
    elif action_name == "left_double":
        if 'point' in args:
            pt = extract_point(args['point'])
            if pt:
                x, y = to_abs(*pt)
                print(f"Double clicking at: {x}, {y}")
                mouse.double_click(x, y)
                
    elif action_name == "right_single":
        if 'point' in args:
            pt = extract_point(args['point'])
            if pt:
                x, y = to_abs(*pt)
                print(f"Right clicking at: {x}, {y}")
                mouse.right_click(x, y)
                
    elif action_name == "drag":
        if 'start_point' in args and 'end_point' in args:
            start_pt = extract_point(args['start_point'])
            end_pt = extract_point(args['end_point'])
            if start_pt and end_pt:
                start_x, start_y = to_abs(*start_pt)
                end_x, end_y = to_abs(*end_pt)
                print(f"Dragging from: {start_x}, {start_y} to {end_x}, {end_y}")
                # Move to start, then drag to end
                mouse.move(start_x, start_y)
                mouse.drag(end_x, end_y)
                
    elif action_name == "hotkey":
        if 'key' in args:
            keys = args['key'].split(' ')
            keyboard.hotkey(*keys)
            
    elif action_name == "type":
        if 'content' in args:
            content = args['content']
            if content.endswith('\n'):
                keyboard.type_text(content[:-1])
                keyboard.press('enter')
            else:
                keyboard.type_text(content)
                
    elif action_name == "scroll":
        if 'point' in args and 'direction' in args:
            pt = extract_point(args['point'])
            direction = args['direction']
            if pt:
                x, y = to_abs(*pt)
                print(f"Scrolling at: {x}, {y} direction: {direction}")
                # Move to point first
                mouse.move(x, y)
                
                clicks = 5 # Default amount
                if direction == 'down':
                    mouse.scroll(-clicks)
                elif direction == 'up':
                    mouse.scroll(clicks)
                
    elif action_name == "wait":
        time.sleep(5)
        
    elif action_name == "finished":
        logging.info(f"Task finished: {args.get('content', '')}")
        pass
        
    else:
        logging.warning(f"Unknown action: {action_name}")

    time.sleep(0.5)
