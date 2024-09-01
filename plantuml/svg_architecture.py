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

class Orientation(Enum):
    LEFT_RIGHT = 0
    TOP_DOWN = 1
    
default_style = { \

         "root_margin":20, # Extra separation space outside the rectangle border of the root architeture\
         "margin":15, # Separation space outside the rectangle border of a component\
         "padding":10, # Separation space inside the rectangle border of a component\
         "title-height": 25,\
         "title-font-family":"Consolas",\
         "title-font-size":15
         }

def print_with_indent(text, indent = 0):
    print('    ' * indent + text)
    
def print_html_comment_indent(text, indent = 0):
    print('    ' * indent + "<!--", text, "-->")

def calculate_icon_space(obj, style):
    return 50 # TODO: Improve this

def calculate_text_dim(text, font_size=15, font_weight="normal"):
    num_chars = len(text)
    char_height = font_size
    char_width = 0.6 * font_size
    width = num_chars * char_width
    height = char_height
    return width#, height

def calculate_note_dim(text, font_size=15, font_weight="normal"):

    # Replace the literal '\n' in raw text with actual newline characters
    processed_text = text.replace('\\n', '\n')

    lines = processed_text.splitlines()

    char_height = font_size
    char_width = 0.6 * font_size
    width = 0
    for line in lines:
        width = max(width, char_width * len(line))
    height = char_height * len(lines)
    return lines, width, height

def print_svg_comment(text_lines, x, y, width, height, line_to_x, line_to_y, title_font_family="Courier New", title_font_size=15, indent=0):

        width += 10
        height += 20
        # Calculate the size of the folded corner
        fold_size = 10  # 10% of the smaller dimension

        # Calculate points for the folded corner polygon
        main_fold = []
        main_fold.append((x, y))
        main_fold.append((x + width - fold_size, y))
        main_fold.append((x + width, y + fold_size))
        main_fold.append((x + width, y + height))
        main_fold.append((x, y + height))
        
        fold = []
        fold.append((x+ width - fold_size, y))
        fold.append((x+ width, y + fold_size))
        fold.append((x+ width - fold_size, y + fold_size))

        print_with_indent(f'<line x1="{x+width/2}" y1="{y+height/2}" x2="{line_to_x}" y2="{line_to_y}" stroke="black" stroke-width="1" stroke-dasharray="2, 2" />', indent)

        # print_with_indent(f'<rect x="{x}" y="{y}" width="{width+10}" height="{height+20}"  fill="lightyellow" stroke="black" stroke-width="1"/>', indent)


        #Folded corner
        print_with_indent(f'<polygon points="{main_fold[0][0]},{main_fold[0][1]} {main_fold[1][0]},{main_fold[1][1]} {main_fold[2][0]},{main_fold[2][1]} {main_fold[3][0]},{main_fold[3][1]} {main_fold[4][0]},{main_fold[4][1]}" fill="#FFFFCB" stroke="#FFCC66" stroke-width="1"/>', indent)

        print_with_indent(f'<polygon points="{fold[0][0]},{fold[0][1]} {fold[1][0]},{fold[1][1]} {fold[2][0]},{fold[2][1]}" fill="#FFFFCB" stroke="#FFCC66" stroke-width="1"/>', indent)



        for index, line in enumerate(text_lines):
            print_with_indent(f'<text x="{x+5}" y="{y+20+(title_font_size*index)}" font-family="{title_font_family}" font-size="{title_font_size}px" font-weight="bold">{line}</text>', indent)

def draw_single_connection(name, pos1, pos2, style, indent=0):
    return f'<line x1="{pos1[0]}" y1="{pos1[1]}" x2="{pos2[0]}" y2="{pos2[1]}" stroke="{style["color"]}" stroke-width="1" />'

def predict_single_connection(arch, obj1, obj2):
    def normalize_vector(v):
        magnitude = math.sqrt(v[0]**2 + v[1]**2)
        if magnitude == 0:
            return (0, 0)
        return (v[0] / magnitude, v[1] / magnitude)

    if not isinstance(obj1, pt.PlantumlType) or not isinstance(obj2, pt.PlantumlType):
        return (0, 0)
    x1, y1 = cr.get_absolute_center(arch, obj1)
    x2, y2 = cr.get_absolute_center(arch, obj2)
    
    return normalize_vector((x2-x1, y2-y1))

def calc_bord_pos(arch, obj, comp1_vec):
    # print_html_comment_indent(f"  calc_bord_pos obj name = {obj.name}")
    
    x, y = cr.get_absolute_pos(arch, obj)
    # x = obj.metadata_dict["rect_x_pos"]
    # y = obj.metadata_dict["rect_y_pos"]
    width = obj.metadata_dict["rect_x_len"]
    height = obj.metadata_dict["rect_y_len"]
    
    res = cr.find_rect_border_intersection(x, y, width, height, comp1_vec[0], comp1_vec[1])
    # print_html_comment_indent(f"   calc_bord_pos res = {res}")
    return res

def create_svg_comonnection(arch, name, plantuml_obj, indent=0):
    def is_hexadecimal(s):
        # Return True if the string represents a hexa value
        try:
            print ("OK")
            int(s, 16)
            return True
        except ValueError:
            print ("EXCEPTION")
            return False
    def invert_vec(v):
        # Invert the signal of the items of the vector
        x = -v[0]
        y = -v[1]
        return (x,y)
    def average_vec(vec_list):
        # Return a vector (normalized) representing the average of the list of vectors
        x = 0
        y = 0
        for idx, v in enumerate(vec_list):
            # print_html_comment_indent(f"   average_vec ({v[0]}, {v[1]})")
            x += v[0]
            y += v[1]
        
        magnitude = math.sqrt(x**2 + y**2)
        if magnitude == 0:
            return (0, 0)
        # print_html_comment_indent(f"   average_vec ret ({x / magnitude}, {y / magnitude})")
        return (x / magnitude, y / magnitude)
        
    style = {"color":"black"} # Provision for ... TBD
    # color = ""
    if "color" in plantuml_obj.metadata_dict:
        color_str = plantuml_obj.metadata_dict["color"]
        if is_hexadecimal(color_str):
            style["color"] = "#"+color_str
        else:
            style["color"] = color_str
    
    # line = "-[norank]-"
    # if "line" in plantuml_obj.metadata_dict:
        # line = plantuml_obj.metadata_dict["line"]
    # elif plantuml_obj.metadata_dict["direction"] == "out":
        # line = "-[norank]->"
    # elif plantuml_obj.metadata_dict["direction"] == "in":
        # line = "<-[norank]-"

    # First create an approximation of direction by getting the average of the multiple center-2-center lines
    comp1_vec = []
    comp2_vec = []
    if isinstance(plantuml_obj.comp1, list):
        # print_html_comment_indent(f"Case 1 (multiples to one)")
        comp2 = plantuml_obj.comp2.ref
        for item in plantuml_obj.comp1:
            comp1 = item.ref
            # conn_vec_comp.append(predict_single_connection(arch, comp1, comp2))
            comp1_vec.append(predict_single_connection(arch, comp1, comp2))
        # print_html_comment_indent(f"   comp1_vec {comp1_vec}")
        comp2_vec.append(invert_vec(average_vec(comp1_vec)))
        # print_html_comment_indent(f"   comp1_vec = {comp1_vec} comp2_vec = {comp2_vec[0]}")
    elif isinstance(plantuml_obj.comp2, list):
        # print_html_comment_indent(f"Case 2 (one to multiples)")
        comp1 = plantuml_obj.comp1.ref
        for item in plantuml_obj.comp2:
            comp2 = item.ref
            # conn_vec_comp.append(predict_single_connection(arch, comp1, comp2))
            comp2_vec.append(invert_vec(predict_single_connection(arch, comp1, comp2)))
            # print_html_comment_indent(f"   before comp1_vec {predict_single_connection(arch, comp1, comp2)}")
        comp1_vec.append(invert_vec(average_vec(comp2_vec))) # Invert again because 1 should use 2 not inverted
        # print_html_comment_indent(f"   comp1_vec = {comp1_vec[0]} comp2_vec = {comp2_vec}")
    else:
        # print_html_comment_indent(f"Case 3 (one to one)")
        comp2 = plantuml_obj.comp1.ref
        comp1 = plantuml_obj.comp2.ref
        # conn_vec_comp.append(predict_single_connection(arch, comp1, comp2))
        comp1_vec.append(predict_single_connection(arch, comp1, comp2))
        comp2_vec.append(invert_vec(comp1_vec[0]))
        # print_html_comment_indent(f"  case 3 {comp1.name} vec1=({comp1_vec[0][0]},{comp1_vec[0][1]}); {comp2.name} vec2=({comp2_vec[0][0]},{comp2_vec[0][1]})")

    conn_str = ""
    if isinstance(plantuml_obj.comp1, list):
        # print_html_comment_indent(f"Case 1")
        comp2 = plantuml_obj.comp2.ref
        pos2 = calc_bord_pos(arch, comp2, comp2_vec[0])
        for index, item in enumerate(plantuml_obj.comp1):
            comp1 = item.ref
            if comp1.is_visible_recursive(arch) and comp2.is_visible_recursive(arch):
                pos1 = calc_bord_pos(arch, comp1, comp1_vec[index])
                conn_str += draw_single_connection(name, pos1, pos2, style, indent) #f"{path1} {line} {path2} {color} : {name}\n"
        
    elif isinstance(plantuml_obj.comp2, list):
        comp1 = plantuml_obj.comp1.ref
        pos1 = calc_bord_pos(arch, comp1, comp1_vec[0])
        for index, item in enumerate(plantuml_obj.comp2):
            # print(f" Case 2 {index}")
            comp2 = item.ref
            if comp1.is_visible_recursive(arch) and comp2.is_visible_recursive(arch):
                pos2 = calc_bord_pos(arch, comp2, comp2_vec[index])
                conn_str += draw_single_connection(name, pos1, pos2, style, indent) #f"{path1} {line} {path2} {color} : {name}\n"
    else:
        # print_html_comment_indent(f"Case 3")
        comp1 = plantuml_obj.comp2.ref
        comp2 = plantuml_obj.comp1.ref
        if comp1.is_visible_recursive(arch) and comp2.is_visible_recursive(arch):
            pos1 = calc_bord_pos(arch, comp1, comp1_vec[0])
            pos2 = calc_bord_pos(arch, comp2, comp2_vec[0])
            conn_str = draw_single_connection(name, pos1, pos2, style, indent) #f"{path1} {line} {path2} {color} : {name}"
    return {name:conn_str}

def get_all_connections(arch, connections, highway_map):
    
    def get_all_connections_recurrent(arch, obj, connections):
        if isinstance(obj, pt.PlantumlContainer):
           for name, value in inspect.getmembers(obj):
                if isinstance(value, pt.PlantumlConnection):
                    if value.is_visible():
                        # Add this connection to the connections dictionary
                        # connections.update(create_svg_comonnection(arch, value.name, value)) # Old method
                        connections.update(cr.route_svg_comonnection(arch, value.name, value, highway_map)) # New Method
                        

                elif isinstance(value, pt.PlantumlType):
                    get_all_connections_recurrent(arch, value, connections)
    
    get_all_connections_recurrent(arch, arch, connections)
    
def get_all_comments(obj, comments):

    if isinstance(obj, pt.PlantumlType) and obj.is_visible():
        if "note" in obj.metadata_dict:
            lines, width, height = calculate_note_dim(obj.metadata_dict["note"])
            comments.append([lines, obj, width, height])
        for name, value in inspect.getmembers(obj):
            if isinstance(value, pt.PlantumlType):
                get_all_comments(value, comments)

def shift_to_right(x, width, target_x, right_most, margin=50):
    limit = min(target_x+width+margin, right_most)
    delta = limit - (x + width + margin)
    if delta > 0:
        return x + delta
    return x

def split_top_bottom_comments(arch, comments, right_end, height, margin=50):
    _top_comments = []
    _bottom_comments = []

    # Split the list of comments to the closest list on vertical axis, _top_comments or _bottom_comments
    for comment in comments:
        x, y = cr.get_absolute_center(arch, comment[1])
        
        # Add center position of the related component, pos 4, 5
        comment += ([x, y])
        if y < height/2:
            _top_comments.append(comment)
        else:
            _bottom_comments.append(comment)

    # Sort the list according to the x position of the related component 
    _top_comments.sort(key=lambda row: row[4])
    _bottom_comments.sort(key=lambda row: row[4])

    top_comments = []
    bottom_comments = []

    # Calculate the x, y of the comments sequentially.
    x=0
    for comment in _top_comments:
        # Add note x, y position, pos 6, 7
        comment += ([x, 0])
        x += (comment[2]+margin)
        top_comments.append(comment)
    x=0
    comment_width, comment_height = calculate_comments_dim(top_comments, margin)    
    for comment in _bottom_comments:
        comment += ([x, comment_height+height])
        x += (comment[2]+margin)
        bottom_comments.append(comment)

    # Adjust x position of the comments by moving to right, closest to the related component
    right_most = right_end
    for comment in reversed(top_comments):
        comment[6] = shift_to_right(comment[6], comment[2], comment[4], right_most, margin)
        right_most = comment[6]
    right_most = right_end
    for comment in reversed(bottom_comments):
        comment[6] = shift_to_right(comment[6], comment[2], comment[4], right_most, margin)
        right_most = comment[6]

    return top_comments, bottom_comments

def calculate_comments_dim(comments, margin=50):
    comment_width = 0
    comment_height = 0
    for comment in comments:
        comment_width = max(comment_width, comment[2] + comment[6] + margin)
        comment_height = max(comment_height, comment[3] + margin)
        
    return comment_width, comment_height

def print_svg_component(name, obj, indent=0):
    x = cr.get_obj_prop(obj, "rect_x_pos")
    y = cr.get_obj_prop(obj, "rect_y_pos")
    width = cr.get_obj_prop(obj, "rect_x_len", 50)
    height = cr.get_obj_prop(obj, "rect_y_len", 50)
    # x = obj.metadata_dict["rect_x_pos"]
    # y = obj.metadata_dict["rect_y_pos"]
    # width = obj.metadata_dict["rect_x_len"]
    # height = obj.metadata_dict["rect_y_len"]
    text_length = width
    
    title_font_family = cr.get_obj_prop(obj, "title-font-family", "Consolas")
    title_font_size = cr.get_obj_prop(obj, "title-font-size", "15px")
    
  # BackgroundColor #C5FFA6
  # BorderColor #145B17
  # FontColor #085D24

    # print_with_indent(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" style="fill: none; stroke: red; stroke-width: 2px;"/>', indent)
    if isinstance(obj, pt.PlantumlActivity):
        print_with_indent(f'<rect x="{x}" y="{y}" width="{width}" height="{height}"  fill="#C5FFA6" stroke="#145B17" stroke-width="1"/>', indent)

        print_with_indent(f'<rect x="{x+10}" y="{y+10}" width="20" height="18" fill="white" stroke="black" stroke-width="1"/>', indent)
        print_with_indent(f'<rect x="{x+6}" y="{y+12}" width="6" height="4" fill="white" stroke="black" stroke-width="1"/>', indent)
        print_with_indent(f'<rect x="{x+6}" y="{y+20}" width="6" height="4" fill="white" stroke="black" stroke-width="1"/>', indent)
        print_with_indent(f'<text x="{x+20}" y="{y+24}" font-family="Arial" font-size="14px" font-weight="bold" text-anchor="middle" fill="black">A</text>', indent)

        print_with_indent(f'<text x="{x+50}" y="{y+25}" font-family="{title_font_family}" font-size="{title_font_size}px" font-weight="bold" fill=#085D24>{name}</text>', indent)

    elif isinstance(obj, pt.PlantumlActor):
        print_with_indent(f'<rect x="{x}" y="{y}" width="{width}" height="{height}"  fill="url(#grad2)" stroke="#145B17" stroke-width="1" filter="url(#shadow)"/>', indent)

        print_with_indent(f'<rect x="{x+10}" y="{y+10}" width="20" height="18" fill="white" stroke="black" stroke-width="1"/>', indent)
        print_with_indent(f'<rect x="{x+6}" y="{y+12}" width="6" height="4" fill="white" stroke="black" stroke-width="1"/>', indent)
        print_with_indent(f'<rect x="{x+6}" y="{y+20}" width="6" height="4" fill="white" stroke="black" stroke-width="1"/>', indent)
        print_with_indent(f'<text x="{x+21}" y="{y+24}" font-family="Arial" font-size="12px" font-weight="bold" text-anchor="middle" fill="black">LA</text>', indent)

        print_with_indent(f'<text x="{x+50}" y="{y+25}" font-family="{title_font_family}" font-size="{title_font_size}px" font-weight="bold">{name}</text>', indent)
        
    elif isinstance(obj, pt.PlantumlComponent):
        print_with_indent(f'<rect x="{x}" y="{y}" width="{width}" height="{height}"  fill="url(#grad1)" stroke="#4E4E97" stroke-width="1" filter="url(#shadow)"/>', indent)

        print_with_indent(f'<rect x="{x+10}" y="{y+10}" width="20" height="18" fill="white" stroke="black" stroke-width="1"/>', indent)
        print_with_indent(f'<rect x="{x+6}" y="{y+12}" width="6" height="4" fill="white" stroke="black" stroke-width="1"/>', indent)
        print_with_indent(f'<rect x="{x+6}" y="{y+20}" width="6" height="4" fill="white" stroke="black" stroke-width="1"/>', indent)
        print_with_indent(f'<text x="{x+20}" y="{y+24}" font-family="Arial" font-size="14px" font-weight="bold" text-anchor="middle" fill="black">L</text>', indent)

        print_with_indent(f'<text x="{x+50}" y="{y+25}" font-family="{title_font_family}" font-size="{title_font_size}px" font-weight="bold">{name}</text>', indent)
        
    else:
        print_with_indent(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" style="fill: none; stroke: black; stroke-width: 1px;" stroke-dasharray="2, 2"/>', indent)
        print_with_indent(f'<text x="{x+5}" y="{y+20}" font-family="{title_font_family}" font-size="{title_font_size}px" font-weight="bold">{name}</text>', indent)

def print_svg_rect(name: str, rect: list[int|float, int|float, int|float, int|float], color: str = "red", fill: str ="gray", fill_opacity: str="0.2"):
    """
    This function can be use to draw a svg rectangle with name for debugging
    name: a String with the lable name
    rect: a list[x, y, width, height]
    color: optional svg color (text and border). Default = red
    fill: optional svg color to fill the rectangle. Default = none (transparent)
    """
    print_with_indent(f'<rect x="{rect[0]}" y="{rect[1]}" width="{rect[2]}" height="{rect[3]}" fill="{fill}" stroke="{color}" stroke-width="1" fill-opacity="{fill_opacity}"/>')
    print_with_indent(f'<text x="{rect[0]+5}" y="{rect[1]+10}" font-family="Consolas" font-size="15px", fill="{color}" >{name}</text>')
    
def do_svg_architecture(plantuml_arch, style=default_style, **kwargs):
    """
    This function creates a simple svg layout output representation of the architecture.
    
    This is an alternative to plantuml_architecture using SVG instead. It places the components always in a predictable orientation.

    highway_map is a dictionary that is filled by the inner function recurrent_layout_sizing that contains the roads where connections can pass, the addresses of the componnets on the roads and the allocation of connections in the lanes of the road. A road can be main or secundary. Each component may have multiple lanes along the orientation of the component (row or column), the name of the road contains 3 parts separated by space: a charactyer stating if it is a main ('M') or secundary ('S'), the name of the component owning the lane, and an index starting on 0. Secundary roads are placed only in the beginning and at the end of a component to connect main roads. The dictionary has the following structure:
    - roads: Contains the definition and states of all lanes.
        - rects: The screen representation of a lane as a long rectangle.
        - orientations: The direction of the roads, HORIZONTAL or VERTICAL.
        - allocations: Used to control the lane state (perpendicular position on a road) where a connection passes through.
    - addresses: Contains all the components with the information what are the lanes passing by and the allocations of the connections around the componnet.
    - final: Just lists all the lanes that are the last one (bottom most or left most) inside a component.

    Argumnets:
        plantuml_arch: A class of a PlantumlType type.
        style: The style dictionary (E.g. pading, colors, fonts) expected for this layout.
        kwargs: Optional key/value arguments (TBD).
    """
    
    highway_map = { # Creates a map of roads and streets for connection routing
    "roads": { # Contains the definition and states of all lanes.
        "rects": {}, # The screen representation of a lane as a long rectangle.
        "orientations": {}, # The direction of the roads, HORIZONTAL or VERTICAL.
        "allocations": {} # Used to control the lane state (perpendicular position on a road) where a connection passes through.
        },
    "addresses": {}, # Contains all the components with the information what are the lanes passing by and the allocations of the connections.
    "final": [] # Just lists all the lanes that are the last one (bottom most or left most) inside a component.
    }

    def recurrent_layout_sizing(obj, orientation = Orientation.LEFT_RIGHT, indent=0):
        # Creates the layout retangles of the architecture.
        # All coordinates are relative to the parent component.
        # To get an absolute coordinates use get_absolute_pos or get_absolute_center from plantuml.connection_routing.
        # style and highway_map are accessed using closure principle (captured from the parent function)
        #
        # Chenged coordination names due to the dual orientation possibilities inside the subcomponents loop.
        #   Originally it used variables x and y, but they were good for one orientation only.
        #   Now with the orientation, x could become y and y become x, so it was decided to change the names
        #   Replaced x and y with u and v.
        #   Replaced widht and height with len_u and len_v
        #    current_x -> current_u
        #    current_y -> current_v
        #    row_heights -> line_len_us
        #    max_row_height -> max_line_len_u
        #    max_width -> max_len_u
        #    max_height-> max_len_v
        
        if orientation == Orientation.LEFT_RIGHT:
            rect_min_u_len = 'rect_min_y_len'
            rect_min_v_len = 'rect_min_x_len'
            rect_u_pos = 'rect_y_pos'
            rect_v_pos = 'rect_x_pos'
            rect_u_len = 'rect_y_len'
            rect_v_len = 'rect_x_len'
        else:
            rect_min_u_len = 'rect_min_x_len'
            rect_min_v_len = 'rect_min_y_len'
            rect_u_pos = 'rect_x_pos'
            rect_v_pos = 'rect_y_pos'
            rect_u_len = 'rect_x_len'
            rect_v_len = 'rect_y_len'

        #{"margin":20, "padding":20, "title-height": 50}
        if (isinstance(obj, pt.PlantumlType) or isinstance(obj, pt.ArchBreakLine))and not isinstance(obj, pt.PlantumlConnection) and obj.metadata_dict['remove'] == False:
        
            # print_with_indent(f">>  {obj.name}: min dim=({obj.metadata_dict[rect_min_u_len]}, {obj.metadata_dict[rect_min_v_len]})", indent)
            list_of_obj = inspect.getmembers(obj)
            
            #count how many valid children exists
            valid_children_cont = 0
            for key, child in list_of_obj:
                if not isinstance(child, pt.PlantumlType) or isinstance(child, pt.PlantumlConnection):
                    continue
                valid_children_cont += 1
        
            # Recursively compute the actual sizes of all children first
            if valid_children_cont != 0:
                for key, child in list_of_obj:
                    if not isinstance(child, pt.PlantumlType) or isinstance(child, pt.PlantumlConnection):
                        continue
                    recurrent_layout_sizing(child, orientation, indent+1)
                
                margin = cr.get_obj_prop(obj, 'margin', style['margin'])
                padding = cr.get_obj_prop(obj, 'padding', style['padding'])
                title_height = cr.get_obj_prop(obj, 'title-height', style['title-height'])
                
                current_u = 0
                current_v = 0
                
                extra_margin = 0
                if obj == plantuml_arch: # The root architecture has extra margins for connections
                    extra_margin = style["root_margin"]
                    # print_with_indent(f" ----------------> plantuml_arch={obj}", indent)

                current_u += margin + padding + extra_margin
                current_v += margin + padding + extra_margin
                last_u = current_u
                last_v = current_v
                    
                # else: # Do not add title to architecture
                if orientation == Orientation.LEFT_RIGHT:
                    road_orientation = cr.DirType.VERTICAL
                    current_u += title_height
                    road_w = current_v
                    road_h = current_u
                    addr_pos = [cr.Dir.LEFT, cr.Dir.RIGHT] # The two directions to the closest roads for a component address
                else:
                    road_orientation = cr.DirType.HORIZONTAL
                    current_v += title_height
                    road_w = current_u
                    road_h = current_v
                    addr_pos = [cr.Dir.UP, cr.Dir.DOWN]

                line_len_us = []
                max_line_len_u = 0
                
                
                # highway_map - The main roads follow the main orientation of the layout
                # Create first main road (Up or Left, depending on the orientation)
                main_road_index = 0
                road_name = f"M {obj.path} {main_road_index}"
                local_roads_map = {"rects": {}, "orientations": {}, "allocations": {}}
                road_x = 0
                road_y = 0
                local_roads_map["rects"][road_name] = [int(road_x), int(road_y), int(road_w), int(road_h)]
                local_roads_map["orientations"][road_name] = road_orientation
                local_roads_map["allocations"][road_name] = []

                text_with = calculate_text_dim(obj.name, style["title-font-size"])
                icon_space = calculate_icon_space(obj, style)
                # print_html_comment_indent(f"text_with: {text_with} for {obj.name}")               
                max_len_u  = max(obj.metadata_dict[rect_min_u_len], text_with + icon_space, (2*margin) + (2*padding) + (2*extra_margin))
                max_len_v = max(obj.metadata_dict[rect_min_v_len], (2*margin) + (2*padding) + (2*extra_margin) + title_height)
                
                for key, child in obj.__dict__.items(): # Use __dict__ to keep decl order
                    
                    if isinstance(child, pt.ArchBreakLine):
                        current_u = margin + padding + extra_margin
                        current_v += (max_line_len_u + (2*margin) + (2*extra_margin))
                        # print_with_indent(f" ----------------> Break new pos=({current_u}, {current_v})", indent)
                        
                        # Add a new road
                        main_road_index += 1
                        road_name = f"M {obj.path} {main_road_index}"
                        # else: # Do not add title to architecture
                        if orientation == Orientation.LEFT_RIGHT:
                            # current_u += title_height
                            road_x = (last_v + max_line_len_u)
                            road_y = 0
                            road_w = (2*margin) + (2*extra_margin)
                            road_h = last_u
                        else:
                            # current_v += title_height
                            road_x = 0
                            road_y = (last_v + max_line_len_u)
                            road_w = last_u
                            road_h = (2*margin) + (2*extra_margin)
                        local_roads_map["rects"][road_name] = [int(road_x), int(road_y), int(road_w), int(road_h)]
                        local_roads_map["orientations"][road_name] = road_orientation
                        local_roads_map["allocations"][road_name] = []

                        line_len_us = []
                        max_line_len_u = 0

                
                    if not isinstance(child, pt.PlantumlType) or isinstance(child, pt.PlantumlConnection):
                        continue

                    # print_with_indent(f" ----------------> Pos=({current_u}, {current_v}) of {child.name}", indent)
                    # # Set child's position
                    child.metadata_dict[rect_u_pos] = current_u
                    child.metadata_dict[rect_v_pos] = current_v
                    line_len_us.append(child.metadata_dict[rect_v_len])
                    
                    current_u += (child.metadata_dict[rect_u_len] + (2*margin) + (2*extra_margin))
                    max_line_len_u = max(line_len_us)
                    
                    max_len_u = max(max_len_u, (current_u))# + margin + padding + extra_margin))
                    max_len_v = max(max_len_v, (current_v + max_line_len_u + margin + padding + extra_margin))

                    last_u = current_u
                    last_v = current_v
                    
                    highway_map["addresses"][child.path] = {addr_pos[0]: f"M {obj.path} {main_road_index}", addr_pos[1]:f"M {obj.path} {main_road_index+1}", "allocarions": {cr.Dir.LEFT:[], cr.Dir.RIGHT:[], cr.Dir.UP:[], cr.Dir.DOWN:[] }}

                    # print_with_indent(f"  child={child.name} pos=({child.metadata_dict[rect_u_pos]}, {child.metadata_dict[rect_v_pos]})", indent)

                # Save layout info inside the obj
                obj.metadata_dict[rect_u_len] = max_len_u # Contains the inner components + internal margins and paddings
                obj.metadata_dict[rect_v_len] = max_len_v # Contains the inner components + internal margins and paddings
                obj.metadata_dict["title-font-family"] = style["title-font-family"]
                obj.metadata_dict["title-font-size"] = style["title-font-size"]


                # Add the last road
                main_road_index += 1
                road_name = f"M {obj.path} {main_road_index}"
                # else: # Do not add title to architecture
                if orientation == Orientation.LEFT_RIGHT:
                    # current_u += title_height
                    road_x = last_v + max_line_len_u
                    road_y = 0
                    road_w = padding + margin + extra_margin
                    road_h = last_u
                else:
                    # current_v += title_height
                    road_x = 0
                    road_y = last_v + max_line_len_u
                    road_w = last_u
                    road_h = padding + margin + extra_margin
                local_roads_map["rects"][road_name] = [int(road_x), int(road_y), int(road_w), int(road_h)]
                local_roads_map["orientations"][road_name] = road_orientation
                local_roads_map["allocations"][road_name] = []
                
                highway_map["final"].append(road_name) # List of final road keys, because index is not enougth

                for key, road in local_roads_map["rects"].items():
                    # Adjust w and h for all main roads
                    if key[0] == "M":
                        if orientation == Orientation.LEFT_RIGHT:
                            road[3] = max_len_u
                        else:
                            road[2] = max_len_u

                highway_map["roads"]["rects"].update(local_roads_map["rects"])
                highway_map["roads"]["orientations"].update(local_roads_map["orientations"])
                highway_map["roads"]["allocations"].update(local_roads_map["allocations"])

            else:
                text_with = calculate_text_dim(obj.name, style["title-font-size"])
                icon_space = calculate_icon_space(obj, style)
                # print_html_comment_indent(f"text_with: {text_with} for {obj.name}")

                # Save layout info inside the obj
                # If there are no children, the rectangle keeps its minimal dimensions
                obj.metadata_dict["rect_x_len"] = max(obj.metadata_dict["rect_min_x_len"], text_with + icon_space)
                obj.metadata_dict["rect_y_len"] = obj.metadata_dict["rect_min_y_len"]
                obj.metadata_dict["title-font-family"] = style["title-font-family"]
                obj.metadata_dict["title-font-size"] = style["title-font-size"]
                
            # print_with_indent(f" {obj.name} dim=({obj.metadata_dict[rect_x_len]},{obj.metadata_dict[rect_y_len]})\n", indent)

    def recurrent_draw(obj, connections, indent):
        # Print all the svg commands to be embedded in html
        
        path = ""
        
        for name, value in inspect.getmembers(obj):
            if not inspect.isroutine(value) and not name.startswith('__'):

                if isinstance(value, pt.PlantumlType) and not isinstance(value, pt.PlantumlConnection) and value.metadata_dict['hide'] == False:# and is_container(value):
                    print_svg_component(value.name, value, indent)

                    # TODO: Consider replace this list by some attribute 'is_container' or isinstance pt.PlantumlContainer
                    if isinstance(value, pt.PlantumlContainer):
                        if value.has_sub_objs():
                            print_with_indent(f'<g transform="translate({value.metadata_dict["rect_x_pos"]}, {value.metadata_dict["rect_y_pos"]})">', indent)
                            
                    recurrent_draw(value, connections, indent+1)

                    if isinstance(value, pt.PlantumlContainer):
                        if value.has_sub_objs():
                            print_with_indent("</g>", indent)

    connections = {} # Use dictionary to avoid duplications
    # print("\nSize\n-------------------------------------------------------------------------------\n")
    
    orientation = Orientation.LEFT_RIGHT
    #orientation = Orientation.TOP_DOWN
    # print('plantuml_arch.metadata_dict["orientation"] = ', plantuml_arch.metadata_dict["orientation"])
    if "orientation" in plantuml_arch.metadata_dict and plantuml_arch.metadata_dict["orientation"] == "top to bottom direction":
        orientation = Orientation.TOP_DOWN
        highway_map["orientation"] = orientation
        
    recurrent_layout_sizing(plantuml_arch, orientation)
    
    # Adjust the highway_map adding the absolute positions to the relative ones created by recurrent_layout_sizing
    for key, road in highway_map["roads"]["rects"].items():
        # print(f" Adding offset to {key}")
        # Split the string into a list of words
        words = key.split()
        obj = plantuml_arch.find_sub_obj_by_path_recursive(words[1])
        if obj != None:
            # print(f"   Object found name {obj.name}")
            offset_x, offset_y = cr.get_absolute_pos(plantuml_arch, obj)
            if offset_x != None and offset_y != None:
                road[0] += offset_x
                road[1] += offset_y
        # else:
            # print(f"   ERROR: Object not found: path={words[0]}.")

        
    comments = []
    get_all_comments(plantuml_arch, comments)
    top_comments, bottom_comments = split_top_bottom_comments(plantuml_arch, comments, plantuml_arch.metadata_dict["rect_x_len"], plantuml_arch.metadata_dict["rect_y_len"])
    top_comment_width, top_comment_height = calculate_comments_dim(top_comments)
    bottom_comment_width, bottom_comment_height = calculate_comments_dim(bottom_comments)
    
    svg_height = plantuml_arch.metadata_dict["rect_y_len"] + top_comment_height + bottom_comment_height
    svg_width = max(plantuml_arch.metadata_dict["rect_x_len"], top_comment_width, bottom_comment_width)

    # print("\nSVG\n-------------------------------------------------------------------------------\n")
    
    print(f'    <svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">')

    print(r"""
        <!-- Define gradients and filters for the shadow effect -->
        <defs>
            <linearGradient id="grad1" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:#C2E5FE;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#96B1DA;stop-opacity:1" />
            </linearGradient>
            <linearGradient id="grad2" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:#D9FCFF;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#C6E6FF;stop-opacity:1" />
            </linearGradient>

            <!-- Drop shadow filter -->
            <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                <feOffset result="offOut" in="SourceGraphic" dx="3" dy="3" />
                <feGaussianBlur result="blurOut" in="offOut" stdDeviation="5" />
                <feBlend in="SourceGraphic" in2="blurOut" mode="normal" />
            </filter>
			
        </defs>
    """)

    print_with_indent(f'<g transform="translate(0, {top_comment_height})">', 2)
    
    connections = {} # Use dictionary to avoid duplications
    get_all_connections(plantuml_arch, connections, highway_map)

    print_svg_component(plantuml_arch.name, plantuml_arch, 2)
    recurrent_draw(plantuml_arch, connections, 3)

    # # print all roads.
    if kwargs.get("print_roads", False) == True:
        for key, value in highway_map["roads"]["rects"].items():
            print_svg_rect(key, value)

    # print all connections only in the end.
    for value in connections.values():
        print(value)

    print_with_indent("</g>", 2)

    for comment in top_comments:
        print_html_comment_indent(f"top {comment[1].name}: {comment[0]}, center = ({comment[6]},{comment[7]})")
        print_svg_comment(comment[0], comment[6], comment[7], comment[2], comment[3], comment[4], comment[5] + top_comment_height - cr.get_obj_prop(comment[1], 'rect_y_len')/2)

    for comment in bottom_comments:
        print_html_comment_indent(f"top {comment[1].name}: {comment[0]}, center = ({comment[6]},{comment[7]})")
        print_svg_comment(comment[0], comment[6], comment[7], comment[2], comment[3], comment[4], comment[5]+ top_comment_height + cr.get_obj_prop(comment[1], 'rect_y_len')/2)

    print(f'    </svg>')
