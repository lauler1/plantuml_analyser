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

def print_obj_abs_pos_dim(arch: pt.PlantumlArchitecture, obj: pt.PlantumlType, indent = 0):
    x1, y1 = get_absolute_pos(arch, obj)
    print_with_indent(f'  {obj.name} ({x1}, {y1}) ({get_obj_prop(obj, "rect_x_len", None)}, {get_obj_prop(obj, "rect_y_len", None)})', indent)

def get_obj_prop(obj, prop, default=0):
    if isinstance(obj, pt.PlantumlType) and prop in obj.metadata_dict:
        res = obj.metadata_dict[prop]
        if res is not None:
            return res
    return default

def get_absolute_pos(arch, obj):
    """
    Returns the absolute coordinates x and y of obj in the architecture (Left, Top), if valid. Otherwise returns None, None.
    The coordination system starts (0, 0) at Top Left of the architecture and increases towards Right and Down.
    """
    owner_tree = arch.get_owner_tree(obj)
    abs_x = 0
    abs_y = 0
    for index, item in enumerate(owner_tree):
        # print_html_comment_indent(f"{index}: {item.name}, pos=({get_obj_prop(item, 'rect_x_pos', 0)},{get_obj_prop(item, 'rect_y_pos', 0)})", 2)
        #The last element will be assumed as 0, 0, not None, None
        dx = get_obj_prop(item, 'rect_x_pos', 0)
        dy = get_obj_prop(item, 'rect_y_pos', 0)
        if dx == None or dy == None:
            return None, None
        abs_x += dx
        abs_y += dy
    
    dx = get_obj_prop(obj, 'rect_x_pos', None)
    dy = get_obj_prop(obj, 'rect_y_pos', None)
    if dx == None or dy == None:
        return None, None
    abs_x += dx
    abs_y += dy
    return abs_x, abs_y

def get_absolute_center(arch, obj):
    """
    Returns the absolute coordinates x and y of the center of obj in the architecture, if valid. Otherwise returns None, None. 
    The coordination system starts (0, 0) at Top Left of the architecture and increases towards Right and Down.
    """
    abs_x, abs_y = get_absolute_pos(arch, obj)
    dx = get_obj_prop(obj, 'rect_x_len', None)
    dy = get_obj_prop(obj, 'rect_y_len', None)
    if abs_x == None or abs_y == None or dx == None or dy == None:
        return None, None
    abs_x += dx/2
    abs_y += dy/2

    return abs_x, abs_y

def get_absolute_coordinates(arch, obj):
    """
    Returns the absolute coordinates x1, y1, x2 and y2 of the obj in the architecture. If a coordinate could not be found, it return None for all coordinates (e.g. None, None, None, None). 
    The coordination system starts (0, 0) at Top Left of the architecture and increases towards Right and Down.
    """
    x1, y1 = get_absolute_pos(arch, obj)
    dx = get_obj_prop(obj, "rect_x_len", None)
    dy = get_obj_prop(obj, "rect_y_len", None)

    if x1 is not None and y1 is not None and dx is not None and dy is not None: 
        x2 = x1 + dx
        y2 = y1 + dy
        return x1, y1, x2, y2
    return None, None, None, None

def find_rect_border_intersection(x0: int|float, y0: int|float, width: int|float, height: int|float, dx: int|float, dy: int|float) -> tuple[int|float, int|float]:
    """
    Returns the coordinates x, y on the border of a retangles where the vector dx, dy interects it. dx, dt is a vectror that starts from the center of the retangle and point toward some direction.
    Backgrounf for the function: This function is used to create connections between components in the direction of the vector dx, dy. A connection line shall starts always on the border of the component.
    x0: lef position of the retangle.
    y0: top position of the retangle. 
    width: width of the retangle.
    height: height of the retangle .
    dx: horizontal dir of the vector in the center of the rectangle.
    dy: vertical directio of the vector in the center of the rectangle.
    return: a tuple with coordinates (x, y) on the border of the retangle.
    """
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

def are_components_in_same_row(arch: pt.PlantumlArchitecture, comp1: pt.PlantumlType, comp2: pt.PlantumlType, indent=0) -> bool:
    """
    Returns True if the two components have the vertical dimentions overlapping each other.
    arch: is the architecture of type PlantumlArchitecture that contains all the components.
    comp1: is the first component to verified.
    comp2: is the second component to verified.
    """
    
    x1, y1 = get_absolute_pos(arch, comp1)
    x2, y2 = get_absolute_pos(arch, comp2)
    
    res = False
    if y1 < y2:
        if  (y1 + get_obj_prop(comp1, "rect_y_len")) >= y2:
            res = True
    else:
        if  (y2 + get_obj_prop(comp2, "rect_y_len")) >= y1:
            res = True

    print_with_indent(f"    {res}\t= are_components_in_same_row: {comp1} and {comp2}", indent);
    return res

def are_components_in_same_column(arch: pt.PlantumlArchitecture, comp1: pt.PlantumlType, comp2: pt.PlantumlType, indent=0) -> bool:
    """
    Returns True if the two components have the horizontal dimentions overlapping each other.
    arch: is the architecture of type PlantumlArchitecture that contains all the components.
    comp1: is the first component to verified.
    comp2: is the second component to verified.
    """
    
    x1, y1 = get_absolute_pos(arch, comp1)
    x2, y2 = get_absolute_pos(arch, comp2)
    
    # print_obj_abs_pos_dim(arch, comp1)
    # print_obj_abs_pos_dim(arch, comp2)
    
    res = False
    if x1 < x2:
        if  (x1 + get_obj_prop(comp1, "rect_x_len")) >= x2:
            res = True
    else:
        if  (x2 + get_obj_prop(comp2, "rect_x_len")) >= x1:
            res = True

    print_with_indent(f"    {res}\t= are_components_in_same_column: {comp1} and {comp2}", indent);
    return res

def get_vertical_overlapping(arch: pt.PlantumlArchitecture, comp1: pt.PlantumlType, comp2: pt.PlantumlType, indent=0)-> tuple[int|float, int|float]:
    """
    Returns the vertical overlapping  between two components. Returned value is a tuple with the absolute coordinates (y1, y2). If no overlapping, it returns (None, None).
    arch: is the architecture of type PlantumlArchitecture that contains all the components.
    comp1: is the first component to verified.
    comp2: is the second component to verified.
    """
    res = (None, None)
    
    if are_components_in_same_row(arch, comp1, comp2, indent+1): # If they overlap
        L1_x1, L1_y1 = get_absolute_pos(arch, comp1)
        L2_x1, L2_y1 = get_absolute_pos(arch, comp2)
        L1_y2 = L1_y1 + get_obj_prop(comp1, "rect_y_len")
        L2_y2 = L2_y1 + get_obj_prop(comp2, "rect_y_len")

        # Calculate the start and end of the overlap
        overlap_y1 = max(L1_y1, L2_y1)
        overlap_y2 = min(L1_y2, L2_y2)
        
        res = (overlap_y1, overlap_y2)

    print_with_indent(f"    {res}\t= get_vertical_overlapping: {comp1} and {comp2}", indent);
    return res

def get_horizontal_overlapping(arch: pt.PlantumlArchitecture, comp1: pt.PlantumlType, comp2: pt.PlantumlType, indent=0) -> tuple[int|float, int|float]:
    """
    Returns the horizontal overlapping  between two components. Returned value is a tuple with the absolute coordinates (x1, x2). If no overlapping, it returns (None, None).
    arch: is the architecture of type PlantumlArchitecture that contains all the components.
    comp1: is the first component to verified.
    comp2: is the second component to verified.
    """
    res = (None, None)

    if are_components_in_same_column(arch, comp1, comp2, indent+1):
        L1_x1, L1_y1 = get_absolute_pos(arch, comp1)
        L2_x1, L2_y1 = get_absolute_pos(arch, comp2)
        L1_x2 = L1_x1 + get_obj_prop(comp1, "rect_x_len")
        L2_x2 = L2_x1 + get_obj_prop(comp2, "rect_x_len")

        # Calculate the start and end of the overlap
        overlap_x1 = max(L1_x1, L2_x1)
        overlap_x2 = min(L1_x2, L2_x2)
        
        res = (overlap_x1, overlap_x2)

    print_with_indent(f"    {res}\t= get_horizontal_overlapping: {comp1} and {comp2}", indent);
    return res

def is_there_other_component_between(arch: pt.PlantumlArchitecture, comp1: pt.PlantumlType, comp2: pt.PlantumlType, dir_type: DirType, component_type: pt.PlantumlType = pt.PlantumlContainer, indent=0) -> bool:
    """
    Returns True if there is another PlantumlContainer between the two components in one direction type (horizontal or vertical). It will not consider if the component is in the own hierarchy of containers.
    It considers only visible components.
    
    arch: is the architecture of type PlantumlArchitecture that contains all the components.
    comp1: is the first component to verified.
    comp2: is the second component to verified.
    dir_type: direction to use in the analysis, DirType.HORIZONTAL or DirType.VERTICAL.
    component_type: The type of the component to be consider for colision detection.
    """

    res = False
    # comp1_x, comp1_y = get_absolute_center(arch, comp1)
    comp1_x1, comp1_y1, comp1_x2, comp1_y2 = get_absolute_coordinates(arch, comp1)
    # comp2_x1, comp2_y1, comp2_x2, comp2_y2 = get_absolute_coordinates(arch, comp2)
    # comp2_x, comp2_y = get_absolute_center(arch, comp2)
    dist = get_distance_to_component(arch, comp1, comp2, indent+1)
    
    if dir_type == DirType.HORIZONTAL:
        if dist[0] > 0: # component is at right
            coord = (comp1_x2, comp1_y1)
            dist_next_comp = get_distance_to_next_component(arch, coord, Dir.RIGHT, component_type, indent+1)
            print_with_indent(f"    --> Ccomponent is at right, dist_next_comp={dist_next_comp}", indent+1)
            if dist_next_comp < dist[0]:
                res = True
        else: # component is at left
            coord = (comp1_x1, comp1_y1)
            dist_next_comp = get_distance_to_next_component(arch, coord, Dir.LEFT, component_type, indent+1)
            print_with_indent(f"    --> Ccomponent is at left, dist_next_comp={dist_next_comp}", indent+1)
            if dist_next_comp > dist[0]:
                res = True
    
    else: # dir_type == DirType.VERTICAL
        if dist[1] > 0: # component is below
            coord = (comp1_x1, comp1_y2)
            dist_next_comp = get_distance_to_next_component(arch, coord, Dir.DOWN, component_type, indent+1)
            print_with_indent(f"    --> Ccomponent is below, dist_next_comp={dist_next_comp}", indent+1)
            if dist_next_comp < dist[1]:
                res = True
        else: # component is above
            coord = (comp1_x1, comp1_y1)
            dist_next_comp = get_distance_to_next_component(arch, coord, Dir.UP, component_type, indent+1)
            print_with_indent(f"    --> Ccomponent is above, dist_next_comp={dist_next_comp}", indent+1)
            if dist_next_comp > dist[1]:
                res = True
    
    # get_distance_to_next_component(arch, coord, dir, component_type, indent)
    # get_distance_to_component(arch, comp1, comp2, indent) 

    print_with_indent(f"    {res}\t= is_there_other_component_between: {comp1.name} and {comp2.name} dir_type={dir_type}", indent);
    return res

def is_there_activity_between(arch: pt.PlantumlArchitecture, comp1: pt.PlantumlType, comp2: pt.PlantumlType, dir_type: DirType, indent=0) -> bool:
    """
    Returns True if there is another PlantumlActivity between the two components in one direction type (horizontal or vertical)
    It considers only visible components.
    
    Background for this function: Activities are important objects, connections should never pass over them.
    
    arch: is the architecture of type PlantumlArchitecture that contains all the components.
    comp1: is the first component to verified.
    comp2: is the second component to verified.
    dir_type: direction to use in the analysis, DirType.HORIZONTAL or DirType.VERTICAL.
    """
    res = is_there_other_component_between(arch, comp1, comp2, dir_type, pt.PlantumlActivity, indent+1)

    print_with_indent(f"    {res}\t= is_there_activity_between: {comp1.name} and {comp2.name} dir_type={dir_type}", indent);
    return res

def get_distance_to_component(arch: pt.PlantumlArchitecture, comp1: pt.PlantumlType, comp2: pt.PlantumlType, indent=0) -> tuple[int|float, int|float]:
    """
    Returns the closest distance between two components. Returned value is a tuple with the absolute distance vector (dx, dy) from compo1 to comp2.
    arch: is the architecture of type PlantumlArchitecture that contains all the components.
    comp1: is the first component to verified.
    comp2: is the second component to verified.
    return: tuple with the absolute distance vector (dx, dy). The coordination system starts (0, 0) at Top Left of the architecture and increases towards Right and Down.
    """

    comp1_x1, comp1_y1, comp1_x2, comp1_y2 = get_absolute_coordinates(arch, comp1)
    comp2_x1, comp2_y1, comp2_x2, comp2_y2 = get_absolute_coordinates(arch, comp2)
    
    print_obj_abs_pos_dim(arch, comp1, indent+1)
    print_obj_abs_pos_dim(arch, comp2, indent+1)
    
    # discover horizontal direction
    dx = 0
    if comp2_x2 < comp1_x1:
        dx = comp2_x2 - comp1_x1
    elif comp2_x1 > comp1_x2:
        dx = comp2_x1 - comp1_x2

    # discover vertical direction
    dy = 0
    if comp2_y2 < comp1_y1:
        dy = comp2_y2 - comp1_y1
    elif comp2_y1 > comp1_y2:
        dy = comp2_y1 - comp1_y2

    res = (dx, dy)
    print_with_indent(f"    {res}\t= get_distance_to_component: {comp1.name} and {comp2.name}", indent);
    return res

def is_component_in_the_path(arch: pt.PlantumlArchitecture, obj: pt.PlantumlType, coord: tuple[int|float, int|float], dir: Dir, indent=0) -> bool:
    """
    Returns True if the component is in a direction from coord.
    
    arch: is the architecture of type PlantumlArchitecture that contains all the components.
    obj: The object to be verified.
    coord: an arbitrary position (x, y) in the architecture from where the measure shall be done. The coordination system starts (0, 0) at Top Left of the architecture and increases towards Right and Down.

    dir_type: direction to use in the analysis, DirType.HORIZONTAL or DirType.VERTICAL.
    
    return: a PlantumlType object or None.
    """
    coord_overlapp = lambda coord, v1, v2: v1 <= coord <= v2
    # def coord_overlapp(coord, v1, v2):
        # # Returns True if coord is between v1 and v2
        # if v1 <= coord <= v2:
            # return True
        # return False
    
    res = False
    x1, y1, x2, y2 = get_absolute_coordinates(arch, obj)
    
    if x1 is not None and y1 is not None and x2 is not None and y2 is not None: 

        if dir == Dir.RIGHT:
            # print_with_indent(f"          RIGHT");
            if coord_overlapp(coord[1], y1, y2) and x1 > coord[0]:
                # print_with_indent(f"            OK");
                res = True
        elif dir == Dir.LEFT:
            # print_with_indent(f"          LEFT");
            if coord_overlapp(coord[1], y1, y2) and x2 < coord[0]:
                # print_with_indent(f"            OK");
                res = True
        elif dir == Dir.DOWN:
            # print_with_indent(f"          DOWN");
            if coord_overlapp(coord[0], x1, x2) and y1 > coord[1]:
                # print_with_indent(f"            OK");
                res = True
        else: #dir == Dir.UP:
            # print_with_indent(f"          UP");
            if coord_overlapp(coord[0], x1, x2) and y2 < coord[1]:
                # print_with_indent(f"            OK");
                res = True
    
    if res == True:
        print_with_indent(f"        {res}\t= is_component_in_the_path: {obj.name} {coord}, dir={dir}, obj coord = {x1}, {y1}, {x2}, {y2}", indent);
    return res

def get_components_in_the_path(arch: pt.PlantumlArchitecture, coord: tuple[int|float, int|float], dir: Dir, component_type: pt.PlantumlType = pt.PlantumlContainer, indent=0) -> pt.PlantumlType:
    """
    Returns all components of a specific type in a direction. Returned the value is the distance. The measure is done till the border of the architecture area is reached.
    It considers only visible components.
    
    arch: is the architecture of type PlantumlArchitecture that contains all the components.
    coord: an arbitrary position (x, y) in the architecture from where the measure shall be done. The coordination system starts (0, 0) at Top Left of the architecture and increases towards Right and Down.
    dir_type: direction to use in the analysis, DirType.HORIZONTAL or DirType.VERTICAL.
    component_type: The type of the component to be consider for colision detection.
    
    return: a PlantumlType object or None.
    """
    res = []
    def recurrent(arch, obj, coord, dir, component_type, valid_componnents):
        for name, value in inspect.getmembers(obj):
            if not inspect.isroutine(value) and not name.startswith('__'):
                if isinstance(value, pt.PlantumlType) and value.is_visible():
                    if isinstance(value, component_type) and is_component_in_the_path(arch, value, coord, dir, indent+1):
                        valid_componnents.append(value)
                        # return # Does not need to go deeper
                    else:
                        recurrent(arch, value, coord, dir, component_type, valid_componnents)

    recurrent(arch, arch, coord, dir, component_type, res) # Start at root which is the arch itself
    print_with_indent(f"      {res}\t= get_components_in_the_path: {coord}, dir={dir}, component_type={component_type.__name__}", indent);
    return res

def get_next_component(arch: pt.PlantumlArchitecture, coord: tuple[int|float, int|float], dir: Dir, component_type: pt.PlantumlType = pt.PlantumlContainer, indent=0) -> pt.PlantumlType:
    """
    Returns the closest component of a specific type in a direction. Returned the value is the distance. The measure is done till the border of the architecture area is reached.
    It considers only visible components.
    
    arch: is the architecture of type PlantumlArchitecture that contains all the components.
    coord: an arbitrary position (x, y) in the architecture from where the measure shall be done. The coordination system starts (0, 0) at Top Left of the architecture and increases towards Right and Down.
    dir_type: direction to use in the analysis, DirType.HORIZONTAL or DirType.VERTICAL.
    component_type: The type of the component to be consider for colision detection.
    
    return: a PlantumlType object or None.
    """
    res = None
    components = get_components_in_the_path(arch, coord, dir, component_type, indent+1)
    ref = 0
    if dir == Dir.RIGHT:
        ref = get_obj_prop(arch, "rect_x_len", 0)
    elif dir == Dir.DOWN:
        ref = get_obj_prop(arch, "rect_y_len", 0)

    for comp in components:
        x1, y1, x2, y2 = get_absolute_coordinates(arch, comp)
        if x1 is not None and y1 is not None and x2 is not None and y2 is not None: 
            if dir == Dir.RIGHT:
                if ref > x1:
                    ref = x1
                    res = comp
            elif dir == Dir.LEFT:
                if ref < x2:
                    ref = x2
                    res = comp
            elif dir == Dir.DOWN:
                if ref > y1:
                    ref = y1
                    res = comp
            else: #dir == Dir.UP:
                if ref < y2:
                    ref = y2
                    res = comp
    print_with_indent(f"      {res}\t= get_next_component: {coord}, dir={dir}, component_type={component_type.__name__}", indent);
    return res

def get_distance_to_next_component(arch: pt.PlantumlArchitecture, coord: tuple[int|float, int|float], dir: Dir, component_type: pt.PlantumlType = pt.PlantumlContainer, indent=0) -> int | float:
    """
    Returns the closest distance from coord to the next component of a specific type in a direction. Returned the value is the distance. The measure is done till the border of the architecture area is reached.
    It considers only visible components.
    
    arch: is the architecture of type PlantumlArchitecture that contains all the components.
    coord: an arbitrary position (x, y) in the architecture from where the measure shall be done. The coordination system starts (0, 0) at Top Left of the architecture and increases towards Right and Down.
    dir_type: direction to use in the analysis, DirType.HORIZONTAL or DirType.VERTICAL.
    component_type: The type of the component to be measured.
    return a number with the distance to the component (or to the border of the architecture if no component found).
    """
    res = 0
    comp = get_next_component(arch, coord, dir, component_type, indent+1)
    x1, y1, x2, y2 = get_absolute_coordinates(arch, comp)
    if x1 is not None and y1 is not None and x2 is not None and y2 is not None: 
        if dir == Dir.RIGHT:
            res = x1 - coord[0]
        elif dir == Dir.LEFT:
            res = x2 - coord[0]
        elif dir == Dir.DOWN:
            res = y1 - coord[1]
        else: #dir == Dir.UP:
            res = y2 - coord[1]
    else:
        if dir == Dir.RIGHT:
            res = get_obj_prop(arch, "rect_x_len", 0) - coord[0]
        elif dir == Dir.LEFT:
            res = 0 - coord[0]
        elif dir == Dir.DOWN:
            res = get_obj_prop(arch, "rect_y_len", 0) - coord[1]
        else: #dir == Dir.UP:
            res = 0 - coord[1]
    
    print_with_indent(f"    {res}\t= get_distance_to_next_component: {coord}, dir={dir}, component_type={component_type.__name__}", indent);
    return res

def test(arch: pt.PlantumlArchitecture, comp: list[pt.PlantumlType]):
    super_arch1_activity1 = comp[0]
    super_arch1_activity2 = comp[1]
    component1_activity1 = comp[2]
    component2_activity1 = comp[3]

    print_obj_abs_pos_dim(arch, super_arch1_activity1);
    print_obj_abs_pos_dim(arch, super_arch1_activity2);
    print_obj_abs_pos_dim(arch, component1_activity1);
    print_obj_abs_pos_dim(arch, component2_activity1);

    # ----------------------------------------------------------------
    
    # are_components_in_same_row(arch, super_arch1_activity1, super_arch1_activity2)
    # are_components_in_same_column(arch, super_arch1_activity1, super_arch1_activity2)

    # are_components_in_same_row(arch, super_arch1_activity1, component1_activity1)
    # are_components_in_same_column(arch, super_arch1_activity1, component1_activity1)

    get_vertical_overlapping(arch, super_arch1_activity1, super_arch1_activity2)
    get_horizontal_overlapping(arch, super_arch1_activity1, super_arch1_activity2)

    get_vertical_overlapping(arch, super_arch1_activity1, component1_activity1)
    get_horizontal_overlapping(arch, super_arch1_activity1, component1_activity1)


    # ----------------------------------------------------------------

    # get_distance_to_next_component(arch, get_absolute_center(arch, super_arch1_activity2), Dir.UP)
    # get_distance_to_next_component(arch, get_absolute_center(arch, super_arch1_activity2), Dir.UP, pt.PlantumlComponent)
    # get_distance_to_next_component(arch, get_absolute_center(arch, super_arch1_activity2), Dir.UP, pt.PlantumlActivity)

    # get_distance_to_next_component(arch, get_absolute_center(arch, super_arch1_activity2), Dir.DOWN)
    # get_distance_to_next_component(arch, get_absolute_center(arch, super_arch1_activity2), Dir.RIGHT)
    # get_distance_to_next_component(arch, get_absolute_center(arch, super_arch1_activity2), Dir.LEFT)
    # get_distance_to_next_component(arch, get_absolute_center(arch, super_arch1_activity2), Dir.LEFT, pt.PlantumlActivity)
    # ----------------------------------------------------------------

    # print("")
    # get_distance_to_component(arch, super_arch1_activity1, component1_activity1) # UP
    # print("")
    # get_distance_to_component(arch, component1_activity1, super_arch1_activity1) # DOWN
    
    # print("")
    # get_distance_to_component(arch, super_arch1_activity1, component2_activity1) # (+, -)
    # print("")
    # get_distance_to_component(arch, component2_activity1, super_arch1_activity1) # (-, +)
    # print("")

    # ----------------------------------------------------------------
    # print(f"\n{super_arch1_activity1} to {super_arch1_activity2} HORIZONTAL:")  # false
    # is_there_other_component_between(arch, super_arch1_activity1, super_arch1_activity2, DirType.HORIZONTAL)
    # print(f"\n{super_arch1_activity1} to {super_arch1_activity2} VERTICAL:")  # false
    # is_there_other_component_between(arch, super_arch1_activity1, super_arch1_activity2, DirType.VERTICAL)
    
    # print(f"\n{super_arch1_activity1} to {component1_activity1} HORIZONTAL:") # false
    # is_there_other_component_between(arch, super_arch1_activity1, component1_activity1, DirType.HORIZONTAL)
    # print(f"\n{super_arch1_activity1} to {component1_activity1} VERTICAL:")  # true
    # is_there_other_component_between(arch, super_arch1_activity1, component1_activity1, DirType.VERTICAL)
    
    # print(f"\n{super_arch1_activity1} to {component2_activity1} VERTICAL:")   # true
    # is_there_other_component_between(arch, super_arch1_activity1, component2_activity1, DirType.VERTICAL)
    # print(f"\n{super_arch1_activity1} to {component2_activity1} HORIZONTAL:")   # true
    # is_there_other_component_between(arch, super_arch1_activity1, component2_activity1, DirType.HORIZONTAL)
    # print("\n\n")

    # print(f"\n{component1_activity1} to {super_arch1_activity2} HORIZONTAL:") # false
    # is_there_other_component_between(arch, component1_activity1, super_arch1_activity2, DirType.HORIZONTAL)
    # print(f"\n{component1_activity1} to {super_arch1_activity2} VERTICAL:")   # true
    # is_there_other_component_between(arch, component1_activity1, super_arch1_activity2, DirType.VERTICAL)
    
    # print(f"\n{component1_activity1} to {super_arch1_activity1} HORIZONTAL:") # false
    # is_there_other_component_between(arch, component1_activity1, super_arch1_activity1, DirType.HORIZONTAL)
    # print(f"\n{component1_activity1} to {super_arch1_activity1} VERTICAL:") # true
    # is_there_other_component_between(arch, component1_activity1, super_arch1_activity1, DirType.VERTICAL)
    
    # print(f"\n{component1_activity1} to {component2_activity1} HORIZONTAL:") # true
    # is_there_other_component_between(arch, component1_activity1, component2_activity1, DirType.HORIZONTAL)
    # print(f"\n{component1_activity1} to {component2_activity1} VERTICAL:")  # false
    # is_there_other_component_between(arch, component1_activity1, component2_activity1, DirType.VERTICAL)

    # print("\n\n")

    # ----------------------------------------------------------------
    # print(f"\n{super_arch1_activity1} to {super_arch1_activity2} HORIZONTAL:")  # false
    # is_there_activity_between(arch, super_arch1_activity1, super_arch1_activity2, DirType.HORIZONTAL)
    # print(f"\n{super_arch1_activity1} to {super_arch1_activity2} VERTICAL:")  # false
    # is_there_activity_between(arch, super_arch1_activity1, super_arch1_activity2, DirType.VERTICAL)
    
    # print(f"\n{super_arch1_activity1} to {component1_activity1} HORIZONTAL:") # false
    # is_there_activity_between(arch, super_arch1_activity1, component1_activity1, DirType.HORIZONTAL)
    # print(f"\n{super_arch1_activity1} to {component1_activity1} VERTICAL:")  # false
    # is_there_activity_between(arch, super_arch1_activity1, component1_activity1, DirType.VERTICAL)
    
    # print(f"\n{super_arch1_activity1} to {component2_activity1} VERTICAL:")   # false
    # is_there_activity_between(arch, super_arch1_activity1, component2_activity1, DirType.VERTICAL)
    # print(f"\n{super_arch1_activity1} to {component2_activity1} HORIZONTAL:")   # true
    # is_there_activity_between(arch, super_arch1_activity1, component2_activity1, DirType.HORIZONTAL)
    # print("\n\n")

    # print(f"\n{component1_activity1} to {super_arch1_activity2} HORIZONTAL:") # false
    # is_there_activity_between(arch, component1_activity1, super_arch1_activity2, DirType.HORIZONTAL)
    # print(f"\n{component1_activity1} to {super_arch1_activity2} VERTICAL:")   # false
    # is_there_activity_between(arch, component1_activity1, super_arch1_activity2, DirType.VERTICAL)
    
    # print(f"\n{component1_activity1} to {super_arch1_activity1} HORIZONTAL:") # t
    # is_there_activity_between(arch, component1_activity1, super_arch1_activity1, DirType.HORIZONTAL)
    # print(f"\n{component1_activity1} to {super_arch1_activity1} VERTICAL:") # false
    # is_there_activity_between(arch, component1_activity1, super_arch1_activity1, DirType.VERTICAL)
    
    # print(f"\n{component1_activity1} to {component2_activity1} HORIZONTAL:") # true
    # is_there_activity_between(arch, component1_activity1, component2_activity1, DirType.HORIZONTAL)
    # print(f"\n{component1_activity1} to {component2_activity1} VERTICAL:")  # false
    # is_there_activity_between(arch, component1_activity1, component2_activity1, DirType.VERTICAL)

    # print("\n\n")

    # ----------------------------------------------------------------

    # is_there_activity_between(arch, super_arch1_activity1, super_arch1_activity2, DirType.HORIZONTAL)
    # is_there_other_component_between(arch, super_arch1_activity1, super_arch1_activity2, DirType.HORIZONTAL)
    # get_distance_to_component(arch, super_arch1_activity1, super_arch1_activity2)
    # get_next_component(arch, (100, 100), Dir.RIGHT )
    # get_distance_to_next_component(arch, (100, 100), Dir.RIGHT )

    # ----------------------------------------------------------------


