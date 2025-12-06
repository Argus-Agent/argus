from ui_tars.action_parser import parse_action_to_structure_output, parsing_response_to_pyautogui_code

response = "Thought: Click the button\nAction: click(point='<point>200 300</point>')"
original_image_width, original_image_height = 1920, 1080
parsed_dict = parse_action_to_structure_output(
    response,
    factor=1000,
    origin_resized_height=original_image_height,
    origin_resized_width=original_image_width,
    model_type="doubao"
)
print(parsed_dict)
parsed_pyautogui_code = parsing_response_to_pyautogui_code(
    responses=parsed_dict,
    image_height=original_image_height,
    image_width=original_image_width
)
print(parsed_pyautogui_code)