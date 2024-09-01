import inspect
import ast
import tokenize
import io
from pprint import pprint
import plantuml.plantuml_types as pt
import plantuml.connection_state_manager as csm
import inspect
import math
from enum import Enum


Dir = csm.Dir
# class Dir(Enum):
    # RIGHT = 0
    # UP = 1
    # DOWN = 2
    # LEFT = 3
    
def opposit(dir: Dir):
    if dir == Dir.RIGHT:
        return Dir.LEFT
    elif dir == Dir.LEFT:
        return Dir.RIGHT
    elif dir == Dir.DOWN:
        return Dir.UP
    else:
        return Dir.DOWN

DirType = csm.DirType
# class DirType(Enum):
    # HORIZONTAL = 0
    # VERTICAL = 1

def print_with_indent(text, indent = 0):
    print('    ' * indent + text)
    
def print_html_comment_indent(text, indent = 0):
    print('    ' * indent + "<!--", text, "-->")

def print_obj_abs_pos_dim(arch: pt.PlantumlArchitecture, obj: pt.PlantumlType, indent = 0):
    x1, y1 = get_absolute_pos(arch, obj)
    print_html_comment_indent(f'  {obj.name} ({x1}, {y1}) ({get_obj_prop(obj, "rect_x_len", None)}, {get_obj_prop(obj, "rect_y_len", None)})', indent)

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
        return int(x1), int(y1), int(x2), int(y2)
    return None, None, None, None

def subtract_ranges(reference: tuple[int, int], exclusions: list[tuple[int, int]]) -> list[tuple[int, int]]:
    # The result is a list of ranges that are left from the reference range that are not overlapped by the individual exclusion ranges
    x1, x2 = reference
    result = [(x1, x2)]

    for ex1, ex2 in exclusions:
        new_result = []
        for r1, r2 in result:
            # Adjust exclusion range to be within the bounds of the current reference range
            adjusted_ex1 = max(r1, ex1)
            adjusted_ex2 = min(r2, ex2)

            # If the exclusion range does not overlap with the current range, keep the current range
            if adjusted_ex2 <= r1 or adjusted_ex1 >= r2:
                new_result.append((r1, r2))
            else:
                # If the exclusion range overlaps, adjust the range by cutting out the overlap
                if adjusted_ex1 > r1:
                    new_result.append((r1, adjusted_ex1))
                if adjusted_ex2 < r2:
                    new_result.append((adjusted_ex2, r2))
        result = new_result

    return result

def normalize_vector(v):
    magnitude = math.sqrt(v[0]**2 + v[1]**2)
    if magnitude == 0:
        return (0, 0)
    return (v[0] / magnitude, v[1] / magnitude)
    
def find_rect_border_intersection(x0: int, y0: int, width: int, height: int, dx: int, dy: int) -> tuple[int, int]:
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
    # print_html_comment_indent(f"    find_rect_border_intersection pos=({x0},{y0}) dim=({width},{height}) dir=({dx},{dy})")
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
                # print_html_comment_indent("         1")
                t_left = (x0 - xc) / dx_norm
                y_left = yc + t_left * dy_norm
                return (x0, y_left)
            
            else: # It is a right intersection
                # print_html_comment_indent("         2")
                t_right = (x0 + width - xc) / dx_norm
                y_right = yc + t_right * dy_norm
                return (x0 + width, y_right)
                
        
        else: # Else the intersection is top or bottom
            if dy > 0: # It is a bottom intersection
                # print_html_comment_indent("         3")
                t_bottom = (y0 + height - yc) / dy_norm
                x_bottom = xc + t_bottom * dx_norm
                return (x_bottom, y0 + height)


            else: # It is a top intersection

                # print_html_comment_indent("         4")
                t_top = (y0 - yc) / dy_norm
                x_top = xc + t_top * dx_norm
                return (x_top, y0)

    else:
        # print_html_comment_indent("         5")

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

    print_html_comment_indent(f"    {res}\t= are_components_in_same_row: {comp1} and {comp2}", indent);
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

    print_html_comment_indent(f"    {res}\t= are_components_in_same_column: {comp1} and {comp2}", indent);
    return res

def get_vertical_overlapping(arch: pt.PlantumlArchitecture, comp1: pt.PlantumlType, comp2: pt.PlantumlType, indent=0)-> tuple[int, int]:
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

    print_html_comment_indent(f"    {res}\t= get_vertical_overlapping: {comp1} and {comp2}", indent);
    return res

def get_horizontal_overlapping(arch: pt.PlantumlArchitecture, comp1: pt.PlantumlType, comp2: pt.PlantumlType, indent=0) -> tuple[int, int]:
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

    print_html_comment_indent(f"    {res}\t= get_horizontal_overlapping: {comp1} and {comp2}", indent);
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
        avrg_y = (comp1_y1 + comp1_y2) / 2
        if dist[0] > 0: # component is at right
            coord = (comp1_x2, avrg_y)
            dist_next_comp = get_distance_to_next_component(arch, coord, Dir.RIGHT, component_type, indent+1)
            print_html_comment_indent(f"    -> Ccomponent is at right, dist_next_comp={dist_next_comp}", indent+1)
            if dist_next_comp < dist[0]:
                res = True
        else: # component is at left
            coord = (comp1_x1, avrg_y)
            dist_next_comp = get_distance_to_next_component(arch, coord, Dir.LEFT, component_type, indent+1)
            print_html_comment_indent(f"    -> Ccomponent is at left, dist_next_comp={dist_next_comp}", indent+1)
            if dist_next_comp > dist[0]:
                res = True
    
    else: # dir_type == DirType.VERTICAL
        avr_x = (comp1_x1 + comp1_x2) / 2
        if dist[1] > 0: # component is below
            coord = (avr_x, comp1_y2)
            dist_next_comp = get_distance_to_next_component(arch, coord, Dir.DOWN, component_type, indent+1)
            print_html_comment_indent(f"    --> Ccomponent is below, dist_next_comp={dist_next_comp}", indent+1)
            if dist_next_comp < dist[1]:
                res = True
        else: # component is above
            coord = (avr_x, comp1_y1)
            dist_next_comp = get_distance_to_next_component(arch, coord, Dir.UP, component_type, indent+1)
            print_html_comment_indent(f"    --> Ccomponent is above, dist_next_comp={dist_next_comp}", indent+1)
            if dist_next_comp > dist[1]:
                res = True
    
    # get_distance_to_next_component(arch, coord, dir, component_type, indent)
    # get_distance_to_component(arch, comp1, comp2, indent) 

    print_html_comment_indent(f"    {res}\t= is_there_other_component_between: {comp1.name} and {comp2.name} dir_type={dir_type}", indent);
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

    print_html_comment_indent(f"    {res}\t= is_there_activity_between: {comp1.name} and {comp2.name} dir_type={dir_type}", indent);
    return res

def get_distance_to_component(arch: pt.PlantumlArchitecture, comp1: pt.PlantumlType, comp2: pt.PlantumlType, indent=0) -> tuple[int, int]:
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
    print_html_comment_indent(f"    {res}\t= get_distance_to_component: {comp1.name} and {comp2.name}", indent);
    return res

def is_component_in_the_path(arch: pt.PlantumlArchitecture, obj: pt.PlantumlType, coord: tuple[int, int], dir: Dir, indent=0) -> bool:
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
        print_html_comment_indent(f"        {res}\t= is_component_in_the_path: {obj.name} {coord}, dir={dir}, obj coord = {x1}, {y1}, {x2}, {y2}", indent);
    return res

def get_components_in_the_path(arch: pt.PlantumlArchitecture, coord: tuple[int, int], dir: Dir, component_type: pt.PlantumlType = pt.PlantumlContainer, indent=0) -> list[pt.PlantumlType]:
    """
    Returns all components of a specific type in a direction.
    It considers only visible components.
    
    arch: is the architecture of type PlantumlArchitecture that contains all the components.
    coord: an arbitrary position (x, y) in the architecture from where the measure shall be done. The coordination system starts (0, 0) at Top Left of the architecture and increases towards Right and Down.
    dir_type: direction to use in the analysis, DirType.HORIZONTAL or DirType.VERTICAL.
    component_type: The type of the component to be consider for colision detection.
    
    return: a list lantumlType objects or empty.
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
    print_html_comment_indent(f"      {res}\t= get_components_in_the_path: {coord}, dir={dir}, component_type={component_type.__name__}", indent);
    return res

def get_components_rects_in_front(arch: pt.PlantumlArchitecture, src_coord: tuple[int, int, int, int], dst_coord: tuple[int, int, int, int], dir: Dir, component_type: pt.PlantumlType = pt.PlantumlContainer, indent=0)  -> list[tuple[int, int, int, int]]:
    """
    Returns all rectangles of component of a specific type in a direction that are in front of the src (i.e. they are obstruction the direct view from src to dst).
    It considers only visible components.
    
    arch: is the architecture of type PlantumlArchitecture that contains all the components.
    src_coord: the rectabgle coordinates (x1, y1, x2, y2) of the source in the architecture from where the measure shall be done.
    src_coord: the rectangle coordinates (x1, y1, x2, y2) of the destiny (target) in the architecture to where the measure shall be done.
    dir_type: direction to use in the analysis, DirType.HORIZONTAL or DirType.VERTICAL.
    component_type: The type of the component to be consider for colision detection.
    
    return: a list of rectangles coordinates tuple(x1, y1, x2, y2) objects or empty.
    """
    
    res = []
    tmp = []
    if dir == Dir.RIGHT:
        init = int(src_coord[1])    # y1
        end = int(src_coord[3]) +1  # y2

        for offset in range(init, end, 20):
            tmp += get_components_in_the_path(arch, (src_coord[2], offset), dir, component_type, indent+1)
        tmp = list(set(tmp)) # Remove repetitions
        
        # Add to res only the ones in front
        for comp in tmp:
            c_x1, c_y1, c_x2, c_y2 = get_absolute_coordinates(arch, comp)
            if c_x1 < dst_coord[0]:
                res.append((c_x1, c_y1, c_x2, c_y2))
            
    elif dir == Dir.LEFT:
        init = int(src_coord[1])    # y1
        end = int(src_coord[3]) +1  # y2

        for offset in range(init, end, 20):
            tmp += get_components_in_the_path(arch, (src_coord[0], offset), dir, component_type, indent+1)
        tmp = list(set(tmp)) # Remove repetitions

        # Add to res only the ones in front
        for comp in tmp:
            c_x1, c_y1, c_x2, c_y2 = get_absolute_coordinates(arch, comp)
            if c_x2 > dst_coord[2]:
                res.append((c_x1, c_y1, c_x2, c_y2))

    elif dir == Dir.DOWN:
        init = int(src_coord[0])    # x1
        end = int(src_coord[2]) +1  # x2

        for offset in range(init, end, 20):
            tmp += get_components_in_the_path(arch, (offset, src_coord[3]), dir, component_type, indent+1)
        tmp = list(set(tmp)) # Remove repetitions
        
        # Add to res only the ones in front
        for comp in tmp:
            c_x1, c_y1, c_x2, c_y2 = get_absolute_coordinates(arch, comp)
            if c_y1 < dst_coord[1]:
                res.append((c_x1, c_y1, c_x2, c_y2))

    else: #dir == Dir.UP:
        init = int(src_coord[0])   # x1
        end = int(src_coord[2]) +1  # x2

        for offset in range(init, end, 20):
            tmp += get_components_in_the_path(arch, (offset, src_coord[1]), dir, component_type, indent+1)
        tmp = list(set(tmp)) # Remove repetitions

        # Add to res only the ones in front
        for comp in tmp:
            c_x1, c_y1, c_x2, c_y2 = get_absolute_coordinates(arch, comp)
            if c_y2 > dst_coord[3]:
                res.append((c_x1, c_y1, c_x2, c_y2))
    
    # res = get_components_in_the_path(arch, coord, dir, component_type, indent+1)
    
    print_html_comment_indent(f"      {res}\t= get_components_rects_in_front: from {src_coord} to {dst_coord}, dir={dir}, component_type={component_type.__name__}", indent);
    return res    

def get_free_obstacle_ranges(arch: pt.PlantumlArchitecture, src_coord: tuple[int, int, int, int], dst_coord: tuple[int, int, int, int], dir: Dir, component_type: pt.PlantumlType = pt.PlantumlContainer, indent=0) -> list[tuple[int, int]]:
    """
    Returns all the ranges that are free of obstructions of a specific type in a direction.
    It considers only visible components.
    
    arch: is the architecture of type PlantumlArchitecture that contains all the components.
    src_coord: the rectabgle coordinates (x1, y1, x2, y2) of the source in the architecture from where the measure shall be done.
    src_coord: the rectangle coordinates (x1, y1, x2, y2) of the destiny (target) in the architecture to where the measure shall be done.
    dir_type: direction to use in the analysis, DirType.HORIZONTAL or DirType.VERTICAL.
    component_type: The type of the component to be consider for colision detection.
    
    return: a list of tuples with each range on the applicable direction, i.e. if dir is horizontal, ranges are vertical.
    """
    res = []
    components_rects = get_components_rects_in_front(arch, src_coord, dst_coord, dir, component_type, indent+1)

    exclusions = []
    if dir == Dir.RIGHT or dir == Dir.LEFT:
        # Calculate the start and end of the overlap
        overlap_y1 = max(src_coord[1], dst_coord[1])
        overlap_y2 = min(src_coord[3], dst_coord[3])
        src_range = (overlap_y1, overlap_y2) # ranges are y coords
        
        for comp_rect in components_rects:
            exclusions.append((comp_rect[1], comp_rect[3]))
        res = subtract_ranges(src_range, exclusions)

    else: #dir == Dir.DOWN or dir == Dir.UP:
        # Calculate the start and end of the overlap
        overlap_x1 = max(src_coord[0], dst_coord[0])
        overlap_x2 = min(src_coord[2], dst_coord[2])
        src_range = (overlap_x1, overlap_x2) # ranges are x coords
        for comp_rect in components_rects:
            exclusions.append((comp_rect[0], comp_rect[2]))
        res = subtract_ranges(src_range, exclusions)

    print_html_comment_indent(f"      {res}\t= get_free_obstacle_ranges: from {src_coord} to {dst_coord}, dir={dir}, component_type={component_type.__name__}", indent);
    return res    


def get_next_component(arch: pt.PlantumlArchitecture, coord: tuple[int, int], dir: Dir, component_type: pt.PlantumlType = pt.PlantumlContainer, indent=0) -> pt.PlantumlType:
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
    print_html_comment_indent(f"      {res}\t= get_next_component: {coord}, dir={dir}, component_type={component_type.__name__}", indent);
    return res

def get_distance_to_next_component(arch: pt.PlantumlArchitecture, coord: tuple[int, int], dir: Dir, component_type: pt.PlantumlType = pt.PlantumlContainer, indent=0) -> int:
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
    
    print_html_comment_indent(f"    {res}\t= get_distance_to_next_component: {coord}, dir={dir}, component_type={component_type.__name__}", indent);
    return res

def test(arch: pt.PlantumlArchitecture, comp: list[pt.PlantumlType]):
    super_arch1_activity1 = comp[0]
    super_arch1_activity2 = comp[1]
    component1_activity1 = comp[2]
    component2_activity1 = comp[3]

    # print_obj_abs_pos_dim(arch, super_arch1_activity1);
    # print_obj_abs_pos_dim(arch, super_arch1_activity2);
    # print_obj_abs_pos_dim(arch, component1_activity1);
    # print_obj_abs_pos_dim(arch, component2_activity1);

    # ----------------------------------------------------------------
    
    # are_components_in_same_row(arch, super_arch1_activity1, super_arch1_activity2)
    # are_components_in_same_column(arch, super_arch1_activity1, super_arch1_activity2)

    # are_components_in_same_row(arch, super_arch1_activity1, component1_activity1)
    # are_components_in_same_column(arch, super_arch1_activity1, component1_activity1)

    # get_vertical_overlapping(arch, super_arch1_activity1, super_arch1_activity2)
    # get_horizontal_overlapping(arch, super_arch1_activity1, super_arch1_activity2)

    # get_vertical_overlapping(arch, super_arch1_activity1, component1_activity1)
    # get_horizontal_overlapping(arch, super_arch1_activity1, component1_activity1)


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

def route_single_comonnection(arch: pt.PlantumlArchitecture, name: str, comp1: pt.PlantumlType, comp2: pt.PlantumlType, highway_map: dict, indent=0):
    """
    Routes a connection between two components on the layout of the architecture used by do_svg_architecture.
    The function uses different criteria for routing a connection:
        - Componnents with direct sight to other component (direct vertical or horizontral line of sight), then the connection is a straight line.
        - TODO: Components in the same row/column with direct sight to the are in front of another component, then the connection needs a 90 degree curve.
        - Componnets locates inside other different componnets or far from each other, they uses the lanes for routing.
    
    arch: The architecture fo the diagram.
    name: String with the name of the connection, to be print. 
    comp1: The first component of the connection, where the connection starts
    comp2: The second component of the connection. 
    highway_map: The layout context for all the connections, it is created by do_svg_architecture.recurrent_layout_sizing and contains the roads where connections can pass and the addresses of the componnets on the roads.
    
    return: A dictionary entry with the connection poly line where the key is the name of the connection.
    """

    def print_single_conn(x1, y1, x2, y2, text = ""):
        # print_html_comment_indent(f"print_single_conn {type(x1)} {type(y1)} {type(x2)} {type(y2)}")
        text_anchor = "start"
        if x2 < x1:
            text_anchor = "end"

        if int(y2) > int(y1):
            rotate = 90
        elif int(y2) < int(y1):
            rotate = -90
        else:
            rotate = 0


        return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="blue" stroke-width="1" />\n \
<text x="{x1+3}" y="{y1-3}" font-family="Courier New" font-size="12px" fill="blue" text-anchor="{text_anchor}" transform="rotate({rotate} {x1},{y1})">{text}</text>'

    def print_poly_conn(points, text = ""):
        # return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="blue" stroke-width="3" />'
        # <text x="{x1}" y="{y1}" font-family="Courier New" font-size="20px" fill="blue" font-weight="bold">{text}</text>'

        text_anchor = "start"
        if points[1][0] < points[0][0]:
            text_anchor = "end"
        
        rotate = 0
        if points[1][1] > points[0][1]:
            rotate = 90
        elif points[1][1] < points[0][1]:
            rotate = -90
        
        point_str_list = []
        for point in points:
            point_str_list.append(f"{point[0]},{point[1]}")
        points_str = " ".join(point_str_list)
        return f'<polyline points="{points_str}" fill="none" stroke="blue" stroke-width="1" />\n \
<text x="{points[0][0] + 3}" y="{points[0][1] - 3}" font-family="Courier New" font-size="12px" fill="blue" transform="rotate({rotate} {points[0][0]},{points[0][1]})"  text-anchor="{text_anchor}" >{text}</text>'

    print_html_comment_indent(f"route_single_comonnection: {name} {comp1.name} {comp1.path}", indent) # false
    print_html_comment_indent(f"                           {name} {comp2.name} {comp2.path}", indent) # false
    conn_str = ""

    # if name != "Multiple Conn:0": # name != "Conn 3" and name != "Conn 5" and name != "Conn 6": # Turn others of for debugging
        # return {name:""}


    # Estimate direction
    c1_x1, c1_y1, c1_x2, c1_y2 = get_absolute_coordinates(arch, comp1)
    c2_x1, c2_y1, c2_x2, c2_y2 = get_absolute_coordinates(arch, comp2)
    
    # print(f" get_absolute_coordinates {c1_x1}, {c1_y1}, {c1_x2}, {c1_y2}")
    # print(f" get_absolute_coordinates {c2_x1}, {c2_y1}, {c2_x2}, {c2_y2}")
    
    print_html_comment_indent(f"{comp1.name} {highway_map['addresses'][comp1.path]}", indent)
    print_html_comment_indent(f"  pos = ({c1_x1}, {c1_y1}) ({c1_x2}, {c1_y2})", indent)
    print_html_comment_indent(f"{comp2.name} {highway_map['addresses'][comp2.path]}", indent)
    print_html_comment_indent(f"  pos = ({c2_x1}, {c2_y1}) ({c2_x2}, {c2_y2})", indent+1)
    print_html_comment_indent(f"   dir vec = ({c2_x1-c1_x1}, {c2_y1-c1_y1})", indent)

    dir_vec = normalize_vector((c2_x1-c1_x1, c2_y1-c1_y1))
    print_html_comment_indent(f"   normalized dir vec = {dir_vec}", indent)

    is_same_row = are_components_in_same_row(arch, comp1, comp2, indent+1)
    is_same_column = are_components_in_same_column(arch, comp1, comp2, indent+1)
    
    finished = False
    ############################
    # criterion 1: straight line
    if is_same_row:
        if c1_x2 < c2_x1:
            dir = Dir.RIGHT
        else:
            dir = Dir.LEFT
        free_ranges = get_free_obstacle_ranges(arch, (c1_x1, c1_y1, c1_x2, c1_y2), (c2_x1, c2_y1, c2_x2, c2_y2), dir, pt.PlantumlActivity, indent+1)

        if c1_x2 < c2_x1:
            x1 = c1_x2
            x2 = c2_x1
        else: 
            x1 = c2_x2
            x2 = c1_x1
        y = csm.allocate_an_address_on_border(highway_map, comp1.path, dir, free_ranges, [x1, None, x2, None])
        if y != None:
            csm.allocate_the_border_offset(highway_map, comp2.path, opposit(dir), y) # also save this in the other comp
            csm.allocate_offroad_horizontal_lane(highway_map, [x1, y, x2, y]) # also save this as an offroad lane, it has no road
            conn_str = print_single_conn(x1, y, x2, y, name)
            finished = True

    elif is_same_column:

        if c1_y2 < c2_y1:
            dir = Dir.DOWN
        else:
            dir = Dir.UP
        free_ranges = get_free_obstacle_ranges(arch, (c1_x1, c1_y1, c1_x2, c1_y2), (c2_x1, c2_y1, c2_x2, c2_y2), dir, pt.PlantumlActivity, indent+1)
        
        if c1_y2 < c2_y1:
            y1 = c1_y2
            y2 = c2_y1
        else: 
            y1 = c2_y2
            y2 = c1_y1
        x = csm.allocate_an_address_on_border(highway_map, comp1.path, dir, free_ranges, [None, y1, None, y2])
        # x = csm.allocate_an_address_on_border(highway_map, comp2.path, opposit(dir), free_ranges, [None, y, None, y2])
        if x != None:
            csm.allocate_the_border_offset(highway_map, comp2.path, opposit(dir), x) # also save this in the other comp
            csm.allocate_offroad_vertical_lane(highway_map, [x, y1, x, y2]) # also save this as an offroad lane, it has no road
            conn_str = print_single_conn(x, y1, x, y2, name)
            finished = True

    # For simple test inverting direction of a connection (Only for debugging)
    # comp1, comp2 = comp2, comp1
    # c1_x1, c1_y1, c1_x2, c1_y2, c2_x1, c2_y1, c2_x2, c2_y2 = c2_x1, c2_y1, c2_x2, c2_y2, c1_x1, c1_y1, c1_x2, c1_y2


    tree1 = arch.get_owner_tree(comp1) #+ [comp1]
    tree2 = arch.get_owner_tree(comp2) #+ [comp2]
    common = None
    # print_html_comment_indent(f'------------------------------------------')
    for index, item in enumerate(tree1):
        # print_html_comment_indent(f' {comp1.name}: tree {index} = {item}')
        if item in tree2:
            common = item

    ############################
    # criterion 2: same row/column with 90 degrees curve
    if not finished:
        range1 = get_rects_if_components_between_common_horizontal_lanes(highway_map, comp1, comp2, tree1, tree2, indent+1)
        range2 = get_rects_if_components_between_common_vertical_lanes(  highway_map, comp1, comp2, tree1, tree2, indent+1)
        if range1 != None:
            print_html_comment_indent(f' Connection {name}: get_rects_if_components_between_common_horizontal_lanes TRUE ********************************************** {comp1.name} {comp2.name}', indent+1)
            # Give priority to go downwords or horizontally, to avoid passing over titles
            if c1_x2 < c2_x1:
                dir = Dir.RIGHT
            else:
                dir = Dir.LEFT

            if c1_y2 < c2_y2: # Main criterion, comp1 goes down if comp2 side is free
                print_html_comment_indent(f'comp1 goes down if comp2 side is free')
                free_ranges = get_free_obstacle_ranges(arch, (c1_x1, c1_y2, c1_x2, range1[1]), (c2_x1, c2_y1, c2_x2, c2_y2), dir, pt.PlantumlActivity, indent+1)
                if len(free_ranges) > 0:
                    x2 = c2_x1 if dir == Dir.RIGHT else c2_x2
                    x = csm.allocate_an_address_on_border(highway_map, comp1.path, Dir.DOWN, [(c1_x1, c1_x2)])
                    y = csm.allocate_an_address_on_border(highway_map, comp2.path, opposit(dir), free_ranges, [x ,None ,x2 ,None])
                    if y != None and x != None: # and csm.is_free_offroad_horizontal_lane(highway_map, [x ,y ,x2 ,y]):
                        road_points = [(x, c1_y2), (x, y), (x2, y)]

                        csm.allocate_offroad_horizontal_lane(highway_map, [x ,y ,x2 ,y]) # also save this as an offroad lane, it has no road
                        conn_str = print_poly_conn(road_points, name)
                        finished = True
            else: # Criterion 2, comp2 goes down if comp1 side is free
                print_html_comment_indent(f'comp2 goes down if comp1 side is free')
                free_ranges = get_free_obstacle_ranges(arch, (c1_x1, c1_y1, c1_x2, c1_y2), (c2_x1, c2_y2, c2_x2, range1[1]), dir, pt.PlantumlActivity, indent+1)
                if len(free_ranges) > 0:
                    x1 = c1_x2 if dir == Dir.RIGHT else c1_x1
                    x = csm.allocate_an_address_on_border(highway_map, comp2.path, Dir.DOWN, [(c2_x1, c2_x2)])
                    y = csm.allocate_an_address_on_border(highway_map, comp1.path, dir, free_ranges, [x1 ,None ,x ,None])
                    if y != None and x != None: # and csm.is_free_offroad_horizontal_lane(highway_map, [x1 ,y ,x ,y]):
                        road_points = [(x1, y), (x, y), (x, c2_y2)]

                        csm.allocate_offroad_horizontal_lane(highway_map, [x1 ,y ,x ,y]) # also save this as an offroad lane, it has no road
                        conn_str = print_poly_conn(road_points, name)
                        finished = True

        elif range2 != None:    
            print_html_comment_indent(f' Connection {name}: get_rects_if_components_between_common_vertical_lanes TRUE ********************************************** {comp1.name} {comp2.name}', indent+1)
            # print(" Criteria12 elif range2 != None ---------------------------------------------------------------")
            # Give priority to go left or vertically, to avoid passing over titles
            if c1_y2 < c2_y1:
                dir = Dir.DOWN
            else:
                dir = Dir.UP

            if c1_x2 < c2_x2: # Main criterion, comp1 goes Right if comp2 top/bottom is free
                # print(" Criteria12 c1_x2 < c2_x2 ---------------------------------------------------------------")
                free_ranges = get_free_obstacle_ranges(arch, (c1_x2, c1_y2, range2[1], c1_y2), (c2_x1, c2_y1, c2_x2, c2_y2), dir, pt.PlantumlActivity, indent+1)
                # print(f" Criteria12 check dir = {dir}")
                if len(free_ranges) > 0:
                    y2 = c2_y1 if dir == Dir.DOWN else c2_y2
                    y = csm.allocate_an_address_on_border(highway_map, comp1.path, Dir.RIGHT, [(c1_y1, c1_y2)])
                    x = csm.allocate_an_address_on_border(highway_map, comp2.path, opposit(dir), free_ranges, [None, y, None, y2])
                    if y != None and x != None: # and csm.is_free_offroad_vertical_lane(highway_map, [x, y, x, y2]):
                        road_points = [(c1_x2, y), (x, y), (x, y2)]

                        csm.allocate_offroad_vertical_lane(highway_map, [x, y, x, y2]) # also save this as an offroad lane, it has no road
                        conn_str = print_poly_conn(road_points, name)
                        finished = True
            else: # Criterion 2, comp2 goes Right if comp1 side is free
                # print(" Criteria12 else ---------------------------------------------------------------")
                free_ranges = get_free_obstacle_ranges(arch, (c1_x1, c1_y1, c1_x2, c1_y2), (c2_x2, c2_y1, range2[1], c2_y2), dir, pt.PlantumlActivity, indent+1)
                # print(f" Criteria12 check dir = {dir}")
                # print(f" Criteria12 free_ranges = {free_ranges}")
                # print(f" Criteria12 range2 = {range2}")
                # print(f" Criteria12 comp1 range = {(c1_x1, c1_x2)}")
                # print(f" Criteria12 comp2 range = {(c2_x2, range2[1])}")

                if len(free_ranges) > 0:
                    y1 = c1_y2 if dir == Dir.DOWN else c1_y1
                    y = csm.allocate_an_address_on_border(highway_map, comp2.path, Dir.RIGHT, [(c2_y1, c2_y2)])
                    x = csm.allocate_an_address_on_border(highway_map, comp1.path, dir, free_ranges, [None, y1, None, y])
                    if y != None and x != None: # and csm.is_free_offroad_vertical_lane(highway_map, [x, y1, x, y]):
                        road_points = [(x, y1), (x, y), (c2_x2, y)]

                        csm.allocate_offroad_vertical_lane(highway_map, [x, y1, x, y]) # also save this as an offroad lane, it has no road
                        conn_str = print_poly_conn(road_points, name)
                        finished = True


    # print_html_comment_indent(f'------------------------------------------')

    ############################
    # criterion 3: Routing with roads
    if not finished:
        # get the exit direction, according to the dest direction and the orientation.
        
        print_html_comment_indent(f'------------------------------------------')
        print_html_comment_indent(f'Routing comp1 = {comp1.name}')
        # go down the hierarchy of the first comp to find a road belonging the component common to both ends
        # Create a sequence of pairs (road, offset) for each road in the hierarhy down tree
        road_points1 = []
        address = highway_map["addresses"][comp1.path]
        # get the initial closest road of comp1
        print_html_comment_indent(f' {comp1.name}: address map = {address}', indent+1)
        if Dir.LEFT in address or Dir.RIGHT in address:
            if dir_vec[0] > 0:
                # print(f'Criterion 3, con1 starts RIGHT')
                road = address[Dir.RIGHT]
                x = c1_x2
                # y = int(c1_y1 + c1_y2) / 2
                y = csm.allocate_an_address_on_border(highway_map, comp1.path, Dir.RIGHT, [(c1_y1, c1_y2)])
                r_x = lane = csm.allocate_a_road_lane(highway_map, road)
                r_y = y
            else:
                # print(f'Criterion 3, con1 starts LEFT')
                road = address[Dir.LEFT]
                x = c1_x1
                # y = int(c1_y1 + c1_y2) / 2
                y = csm.allocate_an_address_on_border(highway_map, comp1.path, Dir.LEFT, [(c1_y1, c1_y2)])
                r_x = lane = csm.allocate_a_road_lane(highway_map, road)
                r_y = y
        else: # Dir.UP in address or Dir.DOWN in address:
            if dir_vec[1] > 0:
                # print(f'Criterion 3, con1 starts DOWN')
                road = address[Dir.DOWN]
                # x = int(c1_x1 + c1_x2) / 2
                x = csm.allocate_an_address_on_border(highway_map, comp1.path, Dir.DOWN, [(c1_x1, c1_x2)])
                y = c1_y2
                r_x = x
                r_y = lane = csm.allocate_a_road_lane(highway_map, road)
            else:
                # print(f'Criterion 3, con1 starts UP')
                road = address[Dir.UP]
                # x = int(c1_x1 + c1_x2) / 2
                x = csm.allocate_an_address_on_border(highway_map, comp1.path, Dir.UP, [(c1_x1, c1_x2)])
                y = c1_y1
                r_x = x
                r_y = lane = csm.allocate_a_road_lane(highway_map, road)

        prev_road1 = (road, lane)
        road_points1.append((x, y))        
        last_coord1 = (r_x, r_y)
        road_points1.append(last_coord1)        
        print_html_comment_indent(f' {comp1.name}: use road = {road}', indent+1)        

        for index, comp in enumerate(reversed(tree1)):
            if comp == common:
                break
            print_html_comment_indent(f' {comp.name}: down comp {index} = {comp}')
            address = highway_map["addresses"][comp.path]
            #get the next closest ways
            print_html_comment_indent(f' {comp.name}: address map = {address}', indent+1)
            if Dir.LEFT in address or Dir.RIGHT in address:
                if dir_vec[0] > 0:
                    print_html_comment_indent(f'  RIGHT')
                    road = address[Dir.RIGHT]
                    if csm.is_last_road(highway_map, prev_road1[0]):
                        x = lane = csm.allocate_a_road_lane(highway_map, road) #get_horizontal_center_of_road(highway_map, road)
                        y = last_coord1[1]
                        r_x = None # Not needed
                        r_y = None # Not needed
                        print_html_comment_indent(f'   is_last_road')
                    else:
                        x = last_coord1[0]
                        y = csm.get_vertical_end(highway_map, road, dir_vec[0])
                        r_x = lane = csm.allocate_a_road_lane(highway_map, road)
                        r_y = x
                        print_html_comment_indent(f'   ')
                else: # Dir.LEFT
                    print_html_comment_indent(f'  LEFT')
                    road = address[Dir.LEFT]
                    if csm.is_first_road(prev_road1[0]):
                        x = lane = csm.allocate_a_road_lane(highway_map, road)
                        y = last_coord1[1]
                        r_x = None # Not needed
                        r_y = None # Not needed
                        print_html_comment_indent(f'   is_first_road')
                    else:
                        x = last_coord1[0]
                        y = csm.get_vertical_end(highway_map, road, dir_vec[0])
                        r_x = lane = csm.allocate_a_road_lane(highway_map, road)
                        r_y = x
                        print_html_comment_indent(f'   ')
            else: # Dir.UP in address or Dir.DOWN in address:
                if dir_vec[1] > 0:
                    print_html_comment_indent(f'  DOWN')
                    road = address[Dir.DOWN]
                    if csm.is_last_road(highway_map, prev_road1[0]):
                        x = last_coord1[0]
                        y = lane = csm.allocate_a_road_lane(highway_map, road)
                        r_x = None # Not needed
                        r_y = None # Not needed
                        print_html_comment_indent(f'   is_last_road')
                    else:
                        x = csm.get_horizontal_end(highway_map, road, dir_vec[0])
                        y = last_coord1[1]
                        r_x = x
                        r_y = lane = csm.allocate_a_road_lane(highway_map, road)
                        print_html_comment_indent(f'   ')
                else: # Dir.UP
                    print_html_comment_indent(f'  UP')
                    road = address[Dir.UP]
                    if csm.is_first_road(prev_road1[0]):
                        x = last_coord1[0]
                        y = lane = csm.allocate_a_road_lane(highway_map, road)
                        r_x = None # Not needed
                        r_y = None # Not needed
                    else:
                        x = csm.get_horizontal_end(highway_map, road, dir_vec[0])
                        y = last_coord1[1]
                        r_x = x
                        r_y = lane = csm.allocate_a_road_lane(highway_map, road)
                        print_html_comment_indent(f'   ')
                    
            prev_road1 = (road, lane)
            last_coord1 = (x, y)
            road_points1.append(last_coord1)        
            if r_x != None and r_y != None:
                last_coord1 = (r_x, r_y)
                road_points1.append(last_coord1)        
            print_html_comment_indent(f' {comp.name}: use road = {road}', indent+1)


        print_html_comment_indent(f'------------------------------------------')
        print_html_comment_indent(f'Routing comp2 = {comp2.name}')
        dir_vec = normalize_vector((last_coord1[0] - c2_x1, last_coord1[1] - c2_y1)) # Make new assumption base the comp end up
        # go down the hierarchy of the second comp to find a road belonging the component common to both ends
        # Create a sequence of pairs (road, offset) for each road in the hierarhy down tree
        #   This list of paits must be in reverse order to have a single polyline
        road_points2 = []
        address = highway_map["addresses"][comp2.path]
        # get the initial closest road of comp2
        print_html_comment_indent(f' {comp2.name}: address map = {address}', indent+1)
        if Dir.LEFT in address or Dir.RIGHT in address:
            if dir_vec[0] > 0: # Use inverted dir, because comp2 is inverse direction
                road = address[Dir.RIGHT]
                x = c2_x2
                # y = int(c2_y1 + c2_y2) / 2
                y = csm.allocate_an_address_on_border(highway_map, comp2.path, Dir.RIGHT, [(c2_y1, c2_y2)])
                r_x = lane = csm.allocate_a_road_lane(highway_map, road, prev_road1)
                r_y = y
            else:
                road = address[Dir.LEFT]
                x = c2_x1
                # y = int(c2_y1 + c2_y2) / 2
                y = csm.allocate_an_address_on_border(highway_map, comp2.path, Dir.LEFT, [(c2_y1, c2_y2)])
                r_x = lane = csm.allocate_a_road_lane(highway_map, road, prev_road1)
                r_y = y
        else: # Dir.UP in address or Dir.DOWN in address:
            if dir_vec[1] > 0: # Use inverted dir, because comp2 is inverse direction
                road = address[Dir.DOWN]
                # x = int(c2_x1 + c2_x2) / 2
                x = csm.allocate_an_address_on_border(highway_map, comp2.path, Dir.DOWN, [(c2_x1, c2_x2)])
                y = c2_y2
                r_x = x
                r_y = lane = csm.allocate_a_road_lane(highway_map, road, prev_road1)
            else:
                road = address[Dir.UP]
                # x = int(c2_x1 + c2_x2) / 2
                x = csm.allocate_an_address_on_border(highway_map, comp2.path, Dir.UP, [(c2_x1, c2_x2)])
                y = c2_y1
                r_x = x
                r_y = lane = csm.allocate_a_road_lane(highway_map, road, prev_road1)

        prev_road2 = (road, lane)
        last_coord2 = (x, y)
        print_html_comment_indent(f' last_coord2 = {last_coord2}')
        road_points2.insert(0, last_coord2) # For the second list, is the reverse order, up the hierarchy tree
        last_coord2 = (r_x, r_y)
        print_html_comment_indent(f' last_coord2 = {last_coord2}')
        road_points2.insert(0, last_coord2)    
        print_html_comment_indent(f' {comp2.name}: use road = {road}', indent+1)        
        for index, comp in enumerate(reversed(tree2)):
            if comp == common:
                break
            print_html_comment_indent(f' {comp.name}: down comp {index} = {comp}')
            address = highway_map["addresses"][comp.path]
            #get the next closest ways
            print_html_comment_indent(f' {comp.name}: address map = {address}', indent+1)
            if Dir.LEFT in address or Dir.RIGHT in address:
                if dir_vec[0] > 0: # Use inverted dir, because comp2 is inverse direction
                    print_html_comment_indent(f'  RIGHT')
                    road = address[Dir.RIGHT]
                    if csm.is_last_road(highway_map, prev_road2[0]):
                        print_html_comment_indent(f'   is_last_road')

                        x = lane = csm.allocate_a_road_lane(highway_map, road, prev_road1)
                        y = last_coord2[1]
                        r_x = None # Not needed
                        r_y = None # Not needed
                    else:
                        x = last_coord2[0]
                        y = csm.get_road_vertical_end(highway_map, road, dir_vec[0])
                        r_x = lane = csm.allocate_a_road_lane(highway_map, road, prev_road1)
                        r_y = y
                else:
                    print_html_comment_indent(f'  LEFT')
                    road = address[Dir.LEFT]
                    if csm.is_first_road(prev_road2[0]):
                        x = lane = csm.allocate_a_road_lane(highway_map, road, prev_road1)
                        y = last_coord2[1]
                        r_x = None # Not needed
                        r_y = None # Not needed
                    else:
                        x = last_coord2[0]
                        y = csm.get_road_vertical_end(highway_map, road, dir_vec[0])
                        r_x = lane = csm.allocate_a_road_lane(highway_map, road), prev_road1
                        r_y = y
            else: # Dir.UP in address or Dir.DOWN in address:
                if dir_vec[1] > 0: # Use inverted dir, because comp2 is inverse direction
                    print_html_comment_indent(f'  DOWN')
                    road = address[Dir.DOWN]
                    if csm.is_last_road(highway_map, prev_road2[0]):
                        print_html_comment_indent(f'   is_last_road')

                        x = last_coord2[0]
                        y = lane = csm.allocate_a_road_lane(highway_map, road, prev_road1)
                        r_x = None # Not needed
                        r_y = None # Not needed
                    else:
                        print_html_comment_indent(f'   NOT is_last_road')
                        
                        x = csm.get_road_horizontal_end(highway_map, road, dir_vec[0])
                        y = last_coord2[1]
                        r_x = x
                        r_y = lane = csm.allocate_a_road_lane(highway_map, road, prev_road1)                        
                else:
                    print_html_comment_indent(f'  UP')
                    road = address[Dir.UP]
                    if csm.is_first_road(prev_road2[0]):
                        x = last_coord2[0]
                        y = lane = csm.allocate_a_road_lane(highway_map, road, prev_road1)
                        r_x = None # Not needed
                        r_y = None # Not needed
                    else:
                        x = csm.get_road_horizontal_end(highway_map, road, dir_vec[0])
                        y = last_coord2[1]
                        r_x = x
                        r_y = lane = csm.allocate_a_road_lane(highway_map, road, prev_road1)

            prev_road2 = (road, lane)
            last_coord2 = (x, y)
            road_points2.insert(0, last_coord2) # For the second list, is the reverse order, up the hierarchy tree
            if r_x != None and r_y != None:
                last_coord2 = (r_x, r_y)
                road_points2.insert(0, last_coord2)  # For the second list, is the reverse order, up the hierarchy tree   

            print_html_comment_indent(f' {comp.name}: use road = {road}', indent+1)
                
        print_html_comment_indent(f'------------------------------------------')
        # In the end, connect the last road parts that connects all together
        road_points_center = [] # TODO TBD


        #  At this point, both sides of the connections are at the same final architecture
        if prev_road1[0] == prev_road2[0]: # If they are at the same road
            road_points_center = [last_coord1, last_coord2]
        else: # If they are NOT in the same road
            if highway_map["roads"]["orientations"][prev_road2[0]] == DirType.HORIZONTAL:
                dist_to_end_1 = csm.get_closest_horizontal_dist_to_end(highway_map, prev_road1[0], last_coord1[0])
                dist_to_end_2 = csm.get_closest_horizontal_dist_to_end(highway_map, prev_road2[0], last_coord2[0])
                if abs(dist_to_end_1) < abs(dist_to_end_2): # road of comp1 is the master
                    x1 = csm.get_road_horizontal_end(highway_map, prev_road1[0], dist_to_end_1)
                else: # road of comp2 is the master
                    x1 = csm.get_road_horizontal_end(highway_map, prev_road1[0], dist_to_end_2)
                y1 = last_coord1[1]
                x2 = x1
                y2 = last_coord2[1]
            
            else: # If DirType.VERTICAL
                dist_to_end_1 = csm.get_closest_vertical_dist_to_end(highway_map, prev_road1[0], last_coord1[1])
                dist_to_end_2 = csm.get_closest_vertical_dist_to_end(highway_map, prev_road2[0], last_coord2[1])
                if abs(dist_to_end_1) < abs(dist_to_end_2): # road of comp1 is the master
                    y1 = csm.get_road_vertical_end(highway_map, prev_road1[0], dist_to_end_1)
                else: # road of comp2 is the master
                    y1 = csm.get_road_vertical_end(highway_map, prev_road1[0], dist_to_end_2)
                x1 = last_coord1[0]
                y2 = y1
                x2 = last_coord2[0]
            
            road_points_center = [(x1, y1), (x2, y2)]

        
        print_html_comment_indent(f'------------------------------------------')
        road_points = road_points1 + road_points_center + road_points2
        
        for point in road_points:
            print_html_comment_indent(f'  point = {point}')
        conn_str = print_poly_conn(road_points, name)

        # conn_str = print_poly_conn(road_points1, name)
        # conn_str += print_poly_conn(road_points_center, name)
        # conn_str += print_poly_conn(road_points2, name)
            
    print(conn_str)

    return {name:conn_str}
    

def route_svg_comonnection(arch: pt.PlantumlArchitecture, name: str, obj: pt.PlantumlConnection, highway_map: dict, indent=0):
    print_html_comment_indent(f"route_svg_comonnection: {name} {obj.name} {obj.path}", indent) # false
    res = {}
    # Actualy a connection obj may have multiple single connections.
    # This is a list of pairs of componnents refs 
    single_connection_list = []
    if isinstance(obj.comp1, list):
        for idx, item in enumerate(obj.comp1):
            comp1 = item.ref
            comp2 = obj.comp2.ref
            single_connection_list.append((f"{name}:{idx}", comp1, comp2))
    elif isinstance(obj.comp2, list):
        for idx, item in enumerate(obj.comp2):
            comp2 = item.ref
            comp1 = obj.comp1.ref
            single_connection_list.append((f"{name}:{idx}", comp1, comp2))
    else:
            comp1 = obj.comp1.ref
            comp2 = obj.comp2.ref
            single_connection_list.append((f"{name}", comp1, comp2))
    for comp in single_connection_list:
        res.update(route_single_comonnection(arch, comp[0], comp[1], comp[2], highway_map, indent+1))
        
    return res

def get_rects_if_components_between_common_horizontal_lanes(highway_map, comp1, comp2, tree1, tree2, indent):
    """
    This function does two things, it test if the components are between two common roads (same row in some point in the hierarchy), and if yes then return the vertical range (in absolute svg coordinates) of the common areas of both componnents.  If not, returns None
    """
    # print_html_comment_indent(f'  are_components_between_common_horizontal_lanes', indent+1)

    address1 = highway_map["addresses"][comp1.path]
    # print_html_comment_indent(f'    comp1.path={comp1.path}', indent+1)
    for index, item in enumerate(reversed(tree1)):
        # print_html_comment_indent(f' {comp1.name}: tree {index} = {item}')
        if item in tree2:
            break
        # print_html_comment_indent(f'     item.path={item.path}', indent+1)
        address1 = highway_map["addresses"][item.path]
        
    address2 = highway_map["addresses"][comp2.path]
    # print_html_comment_indent(f'    comp2.path={comp2.path}', indent+1)
    for index, item in enumerate(reversed(tree2)):
        # print_html_comment_indent(f' {comp1.name}: tree {index} = {item}')
        if item in tree1:
            break
        # print_html_comment_indent(f'     item.path={item.path}', indent+1)
        address2 = highway_map["addresses"][item.path]
        
    if Dir.UP in address1 and Dir.DOWN in address1 and Dir.UP in address2 and Dir.DOWN in address2: 
        # print_html_comment_indent(f'    They have UP and DOWN', indent+1)
        # print_html_comment_indent(f'     Up 1 = {address1[Dir.UP]}', indent+1)
        # print_html_comment_indent(f'     Up 2 = {address2[Dir.UP]}', indent+1)
        # print_html_comment_indent(f'     Down 1 = {address1[Dir.DOWN]}', indent+1)
        # print_html_comment_indent(f'     Down 2 = {address2[Dir.DOWN]}', indent+1)
        if address1[Dir.UP] == address2[Dir.UP] and  address1[Dir.DOWN] == address2[Dir.DOWN]:
            # print_html_comment_indent(f'     RETURN TRUE', indent+1)
            road1 = address1[Dir.UP]
            road2 = address1[Dir.DOWN]

            rect1 = highway_map["roads"]["rects"][road1]   
            rect2 = highway_map["roads"]["rects"][road2]   
            y1 = rect1[1] + rect1[3]
            y2 = rect2[1]
            return (y1, y2)
  
    return None

def get_rects_if_components_between_common_vertical_lanes(highway_map, comp1, comp2, tree1, tree2, indent):
    """
    This function does two things, it test if the components are between two common roads (same column in some point in the hierarchy), and if yes then return the horizontal range (in absolute svg coordinates) of the common areas of both componnents.  If not, returns None
    """

    address1 = highway_map["addresses"][comp1.path]
    for index, item in enumerate(reversed(tree1)):
        # print_html_comment_indent(f' {comp1.name}: tree {index} = {item}')
        if item in tree2:
            break
        address1 = highway_map["addresses"][item.path]
        
    address2 = highway_map["addresses"][comp2.path]
    for index, item in enumerate(reversed(tree2)):
        # print_html_comment_indent(f' {comp1.name}: tree {index} = {item}')
        if item in tree1:
            break
        address2 = highway_map["addresses"][item.path]
 
    if Dir.LEFT in address1 and Dir.RIGHT in address1 and Dir.LEFT in address2 and Dir.RIGHT in address2:
        if address1[Dir.LEFT] == address2[Dir.LEFT] and  address1[Dir.RIGHT] == address2[Dir.RIGHT]:
            road1 = address1[Dir.LEFT]
            road2 = address1[Dir.RIGHT]

            rect1 = highway_map["roads"]["rects"][road1]   
            rect2 = highway_map["roads"]["rects"][road2]   
            x1 = rect1[0] + rect1[2]
            x2 = rect2[0]
            return (x1, x2)

    return None

