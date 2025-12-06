import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.llm.gui.action_parser import parse_response, parse_action, map_action_to_function

class TestGUIAgentActionParser(unittest.TestCase):

    def test_parse_response(self):
        response = "Thought: I need to click.\nAction: click(point='<point>100 200</point>')"
        self.assertEqual(parse_response(response), "click(point='<point>100 200</point>')")
        
        response_no_thought = "click(point='<point>100 200</point>')"
        self.assertEqual(parse_response(response_no_thought), "click(point='<point>100 200</point>')")

    def test_parse_action(self):
        action_str = "click(point='<point>100 200</point>')"
        name, args = parse_action(action_str)
        self.assertEqual(name, "click")
        self.assertEqual(args, {'point': '<point>100 200</point>'})
        
        action_str = "type(content='hello world')"
        name, args = parse_action(action_str)
        self.assertEqual(name, "type")
        self.assertEqual(args, {'content': 'hello world'})
        
        action_str = "drag(start_point='<point>10 10</point>', end_point='<point>20 20</point>')"
        name, args = parse_action(action_str)
        self.assertEqual(name, "drag")
        self.assertEqual(args, {'start_point': '<point>10 10</point>', 'end_point': '<point>20 20</point>'})

        action_str = "wait()"
        name, args = parse_action(action_str)
        self.assertEqual(name, "wait")
        self.assertEqual(args, {})

    @patch('core.llm.gui.action_parser.mouse')
    def test_map_action_click(self, mock_mouse):
        # Screen size 1000x1000 for simplicity
        map_action_to_function("click", {'point': '<point>500 500</point>'}, 1000, 1000)
        mock_mouse.click.assert_called_with(500, 500)
        
        # Screen size 2000x1000
        map_action_to_function("click", {'point': '<point>500 500</point>'}, 2000, 1000)
        mock_mouse.click.assert_called_with(1000, 500)

    @patch('core.llm.gui.action_parser.mouse')
    def test_map_action_drag(self, mock_mouse):
        map_action_to_function("drag", 
                               {'start_point': '<point>100 100</point>', 'end_point': '<point>200 200</point>'}, 
                               1000, 1000)
        mock_mouse.move.assert_called_with(100, 100)
        mock_mouse.drag.assert_called_with(200, 200)

    @patch('core.llm.gui.action_parser.keyboard')
    def test_map_action_type(self, mock_keyboard):
        map_action_to_function("type", {'content': 'hello'}, 1000, 1000)
        mock_keyboard.type_text.assert_called_with('hello')
        
        map_action_to_function("type", {'content': 'hello\n'}, 1000, 1000)
        mock_keyboard.type_text.assert_called_with('hello')
        mock_keyboard.press.assert_called_with('enter')

    @patch('core.llm.gui.action_parser.keyboard')
    def test_map_action_hotkey(self, mock_keyboard):
        map_action_to_function("hotkey", {'key': 'ctrl c'}, 1000, 1000)
        mock_keyboard.hotkey.assert_called_with('ctrl', 'c')

    def test_get_action_coordinates(self):
        from core.llm.gui.action_parser import get_action_coordinates
        
        # Click
        coords = get_action_coordinates("click", {'point': '<point>500 500</point>'}, 1000, 1000)
        self.assertEqual(coords, {'x': 500, 'y': 500})
        
        # Drag
        coords = get_action_coordinates("drag", {'start_point': '<point>100 100</point>', 'end_point': '<point>200 200</point>'}, 1000, 1000)
        self.assertEqual(coords, {'x': 100, 'y': 100, 'xx': 200, 'yy': 200})
        
        # No coords
        coords = get_action_coordinates("type", {'content': 'hello'}, 1000, 1000)
        self.assertIsNone(coords)

if __name__ == '__main__':
    unittest.main()
