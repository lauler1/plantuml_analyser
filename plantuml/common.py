import inspect
import ast
import tokenize
import io
from pprint import pprint
import plantuml.plantuml_types as pt
import plantuml.connection_routing as cr
import inspect
import math
from enum import Enum

class Arrow(Enum):
    NONE = 0
    SIMPLE = 1
    FILLED = 2
    SQUARE = 3

def rotate_2D_point(x, y, pivot_x, pivot_y, angle_degrees):
    # Convert the angle from degrees to radians
    angle_radians = math.radians(angle_degrees)
    
    # Translate point back to origin (relative to pivot)
    translated_x = x - pivot_x
    translated_y = y - pivot_y
    
    # Apply the rotation formula
    rotated_x = translated_x * math.cos(angle_radians) - translated_y * math.sin(angle_radians)
    rotated_y = translated_x * math.sin(angle_radians) + translated_y * math.cos(angle_radians)
    
    # Translate the point back to the original position (add the pivot back)
    final_x = rotated_x + pivot_x
    final_y = rotated_y + pivot_y
    
    return final_x, final_y

def get_color_style(obj, fill, stroke, stroke_width, font_weight, text_color):
    # pink;line:red;line.bold;text:red
    color_str = get_obj_prop(obj, "color", "")
    if color_str != "":
    
        if not ";" in color_str and not ";" in color_str:
            fill = color_str
        else:
            items = color_str.split(';')
            for item in items:
                attr = item.split(':')
                if len(attr) == 1:
                    if attr[0] == "line.bold":
                        stroke_width = "2"
                        font_weight = "bold"
                    else:
                        fill = attr[0]
                elif len(attr) == 2:
                    if attr[0] == "line":
                        stroke = attr[1]
                    elif attr[0] == "text":
                        text_color = attr[1]

    return fill, stroke, stroke_width, font_weight, text_color

def get_color_style(obj, fill, stroke, stroke_width, font_weight, text_color):
    # pink;line:red;line.bold;text:red
    color_str = get_obj_prop(obj, "color", "")
    if color_str != "":
    
        if not ";" in color_str and not ";" in color_str:
            fill = color_str
        else:
            items = color_str.split(';')
            for item in items:
                attr = item.split(':')
                if len(attr) == 1:
                    if attr[0] == "line.bold":
                        stroke_width = "2"
                        font_weight = "bold"
                    else:
                        fill = attr[0]
                elif len(attr) == 2:
                    if attr[0] == "line":
                        stroke = attr[1]
                    elif attr[0] == "text":
                        text_color = attr[1]

    return fill, stroke, stroke_width, font_weight, text_color

def get_default_color_style(obj_type: str):
    # Default colors for each type are stored in dictionaries
    fills   = {"Activity":"#C5FFA6", "Actor":"url(#grad_actor)", "Component":"url(#grad_component)","Connection":"none"}
    strokes = {"Activity":"#145B17", "Actor":"#145B17",          "Component":"#4E4E97"             ,"Connection":"#4E4E97",}
    text_colors = {"Activity":"085D24", "Actor":"black",          "Component":"black"              ,"Connection":"#4E4E97",}

    fill = fills.get(obj_type, "none")
    stroke = strokes.get(obj_type, "black")
    text_color = text_colors.get(obj_type, "black")
    stroke_width = 1
    font_weight = "normal"

    return fill, stroke, stroke_width, font_weight, text_color

def get_obj_prop(obj, prop, default=0):
    if isinstance(obj, pt.PlantumlType) and prop in obj.metadata_dict:
        res = obj.metadata_dict[prop]
        if res is not None:
            return res
    return default

def create_arrow(conn_dir, type:Arrow):
    center = conn_dir[0]
    from_dir = conn_dir[1]

    print(f'center = {center}, from_dir = {from_dir}')

    if type == Arrow.SIMPLE:
        points = [(center[0] + 9, center[1] - 4), (center[0],center[1]), (center[0] + 9, center[1] + 4), (center[0] + 6, center[1]), (center[0] + 9, center[1] - 4)]
        fill = "black"
    elif type == Arrow.FILLED:
        points = [(center[0] + 9, center[1] - 4), (center[0],center[1]), (center[0] + 9, center[1] + 4), (center[0] + 9, center[1] - 4)]
        fill = "black"
    elif type == Arrow.SQUARE:
        points = [(center[0] + 4, center[1] - 4), (center[0] - 4, center[1] - 4), (center[0] - 4, center[1] + 4), (center[0] + 4, center[1] + 4), (center[0] + 4, center[1] - 4)]
        fill = "white"
    else:
        return None

    if center[0] == from_dir[0] and center[1] > from_dir[1]: #from up
        rotated_points = [rotate_2D_point(x, y, center[0],center[1], -90) for x, y in points]
        
        # p1 = (center[0] - 5, center[1] - 9)
        # p2 = (center[0] + 5, center[1] - 9)
        # res = f'points="{p1[0]},{p1[1]} {center[0]},{center[1]} {p2[0]},{p2[1]}" fill="none"'
    
    elif center[0] == from_dir[0] and center[1] < from_dir[1]: #from own:
        rotated_points = [rotate_2D_point(x, y, center[0],center[1], 90) for x, y in points]

        # p1 = (center[0] - 5, center[1] + 9)
        # p2 = (center[0] + 5, center[1] + 9)
        # res = f'points="{p1[0]},{p1[1]} {center[0]},{center[1]} {p2[0]},{p2[1]}" fill="none"'
    
    elif center[0] > from_dir[0] and center[1] == from_dir[1]: #from left:
        rotated_points = [rotate_2D_point(x, y, center[0],center[1], 180) for x, y in points]

        # p1 = (center[0] - 9, center[1] - 5)
        # p2 = (center[0] - 9, center[1] + 5)
        # res = f'points="{p1[0]},{p1[1]} {center[0]},{center[1]} {p2[0]},{p2[1]}" fill="none"'
    
    else: #from right
        rotated_points = points

        # p1 = (center[0] + 9, center[1] - 5)
        # p2 = (center[0] + 9, center[1] + 5)

    point_str_list = []
    for point in rotated_points:
        point_str_list.append(f"{point[0]},{point[1]}")
    points_str = " ".join(point_str_list)
        
    res = f'points="{points_str}" fill="{fill}"'

    return res

def get_arrow_style(line_text, conn_start, conn_end):
    
    start_type = Arrow.NONE
    if line_text.startswith("<<"):
        start_type = Arrow.FILLED
    elif line_text.startswith("<"):
        start_type = Arrow.SIMPLE
    elif line_text.startswith("#"):
        start_type = Arrow.SQUARE
    arrow1 = create_arrow(conn_start, start_type)

    end_type = Arrow.NONE
    if line_text.endswith(">>"):
        end_type = Arrow.FILLED
    elif line_text.endswith(">"):
        end_type = Arrow.SIMPLE
    elif line_text.endswith("#"):
        end_type = Arrow.SQUARE
    arrow2 = create_arrow(conn_end, end_type)

    stroke_dasharray = "none" # "4, 4"
    if '~' in line_text:
        stroke_dasharray = "2, 2" # "4, 4"
    elif '.' in line_text:
        stroke_dasharray = "4, 4" # "4, 4"

    return stroke_dasharray, arrow1, arrow2


