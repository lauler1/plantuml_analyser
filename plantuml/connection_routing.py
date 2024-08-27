import inspect
import ast
import tokenize
import io
from pprint import pprint
import plantuml.plantuml_types as pt
import inspect
import math
from enum import Enum

class Dir(Enum):
    RIGHT = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    
class DirType(Enum):
    HORIZONTAL = 0
    VERTICAL = 1

def print_with_indent(text, indent = 0):
    print('    ' * indent + text)
    
def print_html_comment_indent(text, indent = 0):
    print('    ' * indent + "<!--", text, "-->")

def find_rect_border_intersection(x0, y0, width, height, dx, dy):

    print_html_comment_indent(f"    find_rect_border_intersection pos=({x0},{y0}) dim=({width},{height}) dir=({dx},{dy})")
    # Calculate the center of the rectangle
    xc = x0 + width / 2
    yc = y0 + height / 2
    
    # Normalize the direction vector
    magnitude = math.sqrt(dx**2 + dy**2)
    dx_norm = dx / magnitude
    dy_norm = dy / magnitude
    
    tan_rect = height / width # always positive
    
    if dx_norm != 0:  # Avoid division by zero    
        tg_vec = dy_norm/dx_norm
        
        if abs(tg_vec) <= tan_rect: #It is left or right intersection
            if dx < 0: # It is a left intersection
                print_html_comment_indent("         1")
                t_left = (x0 - xc) / dx_norm
                y_left = yc + t_left * dy_norm
                return (x0, y_left)
            
            else: # It is a right intersection
                print_html_comment_indent("         2")
                t_right = (x0 + width - xc) / dx_norm
                y_right = yc + t_right * dy_norm
                return (x0 + width, y_right)
                
        
        else: # Else the intersection is top or bottom
            if dy > 0: # It is a bottom intersection
                print_html_comment_indent("         3")
                t_bottom = (y0 + height - yc) / dy_norm
                x_bottom = xc + t_bottom * dx_norm
                return (x_bottom, y0 + height)


            else: # It is a top intersection

                print_html_comment_indent("         4")
                t_top = (y0 - yc) / dy_norm
                x_top = xc + t_top * dx_norm
                return (x_top, y0)

    else:
        print_html_comment_indent("         5")

        if dy > 0: # It is a bottom intersection
            return (x0 + width/2, y0 + height)
        else: # It is a top intersection
            return (x0 + width/2, 0)


def are_components_in_same_row(arch, comp1, comp2):
    """
    Returns True if the two components have the vertical dimentions overlapping each other
    arch: is the architecture of type PlantumlArchitecture.
    comp1: is the first component to verified.
    comp2: is the second component to verified.
    """
    return False

def are_components_in_same_column(arch, comp1, comp2):
    """
    Returns True if the two components have the horizontal dimentions overlapping each other
    arch: is the architecture of type PlantumlArchitecture.
    comp1: is the first component to verified.
    comp2: is the second component to verified.
    """
    return False

def is_there_activity_between(arch, comp1, comp2, dir_type):
    """
    Returns True if there is another PlantumlActivity between the two components in one direction type (horizontal or vertical)
    arch: is the architecture of type PlantumlArchitecture.
    comp1: is the first component to verified.
    comp2: is the second component to verified.
    dir_type: direction to use in the analysis, DirType.HORIZONTAL or DirType.VERTICAL
    """
    return False

def is_there_other_component_between(arch, comp1, comp2):
    """
    Returns True if there is another PlantumlContainer between the two components in one direction type (horizontal or vertical). It will not consider if the component is in the own hierarchy of containers
    arch: is the architecture of type PlantumlArchitecture.
    comp1: is the first component to verified.
    comp2: is the second component to verified.
    dir_type: direction to use in the analysis, DirType.HORIZONTAL or DirType.VERTICAL
    """
    return False

def get_distance_to_component(arch, comp1, comp2):
    """
    Returns the closest distance between two components. Returned value is a tuple with the absolute distance vector (dx, dy) from compo1 to comp2.
    arch: is the architecture of type PlantumlArchitecture.
    comp1: is the first component to verified.
    comp2: is the second component to verified.
    """
    return (0, 0)

def get_distance_to_next_component(arch, comp, dir, component_type = pt.PlantumlContainer):
    """
    Returns the closest distance from comp to the next component of a specific type in a direction. Returned value is a tuple with the absolute distance vector (dx, dy). The measure is done till the border of the architecture area is reached.
    arch: is the architecture of type PlantumlArchitecture.
    comp1: is the first component to verified.
    comp2: is the second component to verified.
    """
    return 0


