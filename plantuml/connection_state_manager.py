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
        return x1, y1, x2, y2
    return None, None, None, None

def get_road_down_end(highway_map: dict, road: str) -> int:
    road_rect = highway_map["roads"]["rects"][road]
    return road_rect[1] + road_rect[3] - int(road_rect[2]/2)

def get_road_up_end(highway_map: dict, road: str) -> int:
    road_rect = highway_map["roads"]["rects"][road]
    return road_rect[1] + int(road_rect[2]/2)

def get_road_right_end(highway_map: dict, road: str) -> int:
    road_rect = highway_map["roads"]["rects"][road]
    return road_rect[0] + road_rect[2] - int(road_rect[3]/2)

def get_road_left_end(highway_map: dict, road: str) -> int:
    road_rect = highway_map["roads"]["rects"][road]
    return road_rect[0] + int(road_rect[3]/2)

def is_first_road(road: str):
    words = road.split()
    if words[2] == "0":
        return True
    return False

def is_last_road(highway_map: dict, road: str):
    if road in highway_map["final"]:
        return True
    return False

def get_road_horizontal_end(highway_map: dict, road: str, target_dir: int) -> int:
    return get_road_right_end(highway_map, road) if target_dir > 0 else get_road_left_end(highway_map, road)

def get_road_vertical_end(highway_map: dict, road: str, target_dir: int) -> int:
    return get_road_down_end(highway_map, road) if target_dir > 0 else get_road_up_end(highway_map, road)


def get_closest_horizontal_dist_to_end(highway_map: dict, road: str, target_offset: int) -> int:
    road_rect = highway_map["roads"]["rects"][road]
    
    if target_offset - road_rect[0] < (road_rect[0] + road_rect[2]) - target_offset:
        return road_rect[0] - target_offset
    else:
        return (road_rect[0] + road_rect[2]) - target_offset

def get_closest_vertical_dist_to_end(highway_map: dict, road: str, target_offset: int) -> int:
    road_rect = highway_map["roads"]["rects"][road]
    
    if target_offset - road_rect[1] < (road_rect[1] + road_rect[3]) - target_offset:
        return road_rect[1] - target_offset
    else:
        return (road_rect[1] + road_rect[3]) - target_offset

def is_border_offset_available(highway_map: dict, comp_path: str, face: Dir, offset: int) -> bool:
    # print(f' is_border_offset_available of {comp_path} for offset={offset}')

    if comp_path in highway_map["addresses"]:
        allocarions = highway_map["addresses"][comp_path]["allocarions"]
        if face in allocarions:
            if offset in allocarions[face]:
                return False
    else:
        highway_map["addresses"][comp_path] = {"allocarions": {Dir.LEFT:[], Dir.RIGHT:[], Dir.UP:[], Dir.DOWN:[]}}
    return True
    
def allocate_the_border_offset(highway_map: dict, comp_path: str, face: Dir, offset: int):
    # print(f' allocate_the_border_offset of {comp_path} for offset={offset}')

    if not comp_path in highway_map["addresses"]:
        highway_map["addresses"][comp_path] = {"allocarions": {Dir.LEFT:[], Dir.RIGHT:[], Dir.UP:[], Dir.DOWN:[]}}

    highway_map["addresses"][comp_path]["allocarions"][face].append(offset)
    
def allocate_an_address_on_border(highway_map: dict, comp_path: str, face: Dir, ranges: list[tuple[int, int]], range_for_checking = None) -> int|None:
    """
    Automatically allocates a lane in a road. Multiple lanes are used to avoi passing one connection over other.
    highway_map: map generated by do_svg_architecture.recurrent_layout_sizing. All coordinates are in pixels in the svg context.
    comp_path: The path string returned by the component.
    face: The face of the rectangle on the screen.
    ranges: is a sequence of faces positions (from init to end) where the allocation is allowed by the caller of this function. It can be one single range covering the entire side of a rectangle or multiple parts where a direct sight to the next component is possible.
    return: a position along the border face of the retangle.
    """
    # print(f'allocate_an_address_on_border of {comp_path} for ranges={ranges}')
    for free_range in ranges:
        if free_range[1] - free_range[0] > 5: # Do not use too short ranges

            delta = int((free_range[1]-free_range[0])/2) # I want the perpendicular direction
            offset = int(free_range[0] + delta)
        
            step = 10
            # init_off = int(free_range[0] + (free_range[1]-free_range[0])/3)
            if free_range[1] - free_range[0] < (2 * step):
                step = 3
            for init in [0, 5, 2, 8]: # Keep trying with different interlacing 
                # Do the allocation first around the meddle till the end
                for curr_shift in range (init, delta, step):
                    curr_offset = offset + curr_shift
                    if is_border_offset_available(highway_map, comp_path, face, curr_offset) and is_offroad_lane_available(highway_map, curr_offset, range_for_checking):
                        allocate_the_border_offset(highway_map, comp_path, face, curr_offset)
                        return curr_offset
                    curr_offset = offset - curr_shift
                    if is_border_offset_available(highway_map, comp_path, face, curr_offset) and is_offroad_lane_available(highway_map, curr_offset, range_for_checking):
                        allocate_the_border_offset(highway_map, comp_path, face, curr_offset)
                        return curr_offset
            # # Other try the init
            # for offset in range (init_off, int(free_range[0]), -step):
                # if is_border_offset_available(highway_map, comp_path, face, offset) and is_offroad_lane_available(highway_map, offset, range_for_checking):
                    # allocate_the_border_offset(highway_map, comp_path, face, offset)
                    # return offset
    
    if len(ranges) > 0:
        ranges[0][0] # No allocation because is full, re-use something else shared
    
    return None # No allocation, re-use something else shared

# def get_horizontal_center_of_road(highway_map: dict, road: str) -> int:
    # # road_rect = [road_x, road_y, road_w, road_h] with absolute coord inside the svg area
    # road_rect = highway_map["roads"]["rects"][road]
    # return road_rect[0] + int(road_rect[2]/2)
    
# def get_vertical_center_of_road(highway_map: dict, road: str) -> int:
    # road_rect = highway_map["roads"]["rects"][road]
    # res = road_rect[1] + int(road_rect[3]/2)
    # print_html_comment_indent(f'    get_vertical_center_of_road res = {res} for rtoad = {road}')
    # return res
    
def is_road_lane_available(highway_map: dict, road_name: str, lane: int) -> bool:
    # print(f' is_road_lane_available of {road_name} for lane={lane}')
    local_roads_map = highway_map["roads"]
    # if road_name in local_roads_map:
    allocations = local_roads_map["allocations"][road_name]
    if lane in allocations:
        # print(f'  FALSE', allocations)
        return False

    # print(f'  FALSE')
    return True
    
def allocate_the_road_lane(highway_map: dict, road_name: str, lane: int):
    # print(f' allocate_the_road_lane of {road_name} for lane={lane}')

    local_roads_map = highway_map["roads"]
    # if road_name in local_roads_map:
    allocations = local_roads_map["allocations"][road_name]
    if not lane in allocations:
        print(f'        Do allocation of lane={lane} in road={road_name}')
        allocations.append(lane)

def deallocate_a_road_lane(highway_map: dict, road_name: str, lane: int):
    # print(f' deallocate_a_road_lanethe lane={lane} from {road_name} ')

    local_roads_map = highway_map["roads"]
    # if road_name in local_roads_map:
    allocations = local_roads_map["allocations"][road_name]
    if lane in allocations:
        # print(f'  FALSE', allocations)
        allocations.remove(lane)

def allocate_a_road_lane(highway_map: dict, road: str, do_alloc: bool = True, prev_allocation: tuple[str, int]|None = None) -> int:
    """
    Automatically allocates a lane in a road. Multiple lanes are used to avoi passing one connection over other.
    
    highway_map: map generated by do_svg_architecture.recurrent_layout_sizing. All coordinates are in pixels in the svg context.
    road: The name of the road to alloc a lane.
    do_alloc: True = really execute an allocation. If False, just get a road lane without allocating it.
    prev_allocation: A previous allocation of this road/lane (e.g. by comp 1). Usualy this is used to pass the last allocation from comp1, if it matches this road for comp2, there is no need to alloc a new one.
    
    return: the lane, which is an absolute position perpendicular to the deirection of the road.
    """
    print(f'allocate_a_road_lane road={road}, prev_allocation={prev_allocation}')
    local_roads_map = highway_map["roads"]
    rect = local_roads_map["rects"][road]
    orientation = local_roads_map["orientations"][road]
    print(f' road rect={rect}')
    
    if prev_allocation != None and road == prev_allocation[0]:
        return prev_allocation[1]

    if orientation == DirType.VERTICAL:
        delta = int(rect[2]/2) # I want the perpendicular direction
        offset = int(rect[0] + delta)
    else:
        delta = int(rect[3]/2)
        offset = int(rect[1] + delta)

    print(f' delta={delta}, offset={offset}')

    for init in [0, 5, 2, 8]: # Keep trying with different interlacing 
        print(f'   init={init}')
        for relative_lane in range (init, delta, 10):
            print(f'     relative_lane={relative_lane}')
            lane = offset + relative_lane
            print(f'      lane={lane} going up')
            if is_road_lane_available(highway_map, road, lane):
                allocate_the_road_lane(highway_map, road, lane) if do_alloc == True else None
                print(f'        Get this')
                return lane
            lane = offset - relative_lane
            print(f'      lane={lane} going down')
            if is_road_lane_available(highway_map, road, lane):
                allocate_the_road_lane(highway_map, road, lane) if do_alloc == True else None
                print(f'        Get this')
                return lane

    # if orientation == DirType.VERTICAL:
        # init = int(rect[0] + 5)  # I want the perpendicular direction
        # end = int(rect[0] + rect[2])
    # else:
        # init = int(rect[1] + 5)
        # end = int(rect[1] + rect[3])

    # for lane in range (init, end, 10):
        # if is_road_lane_available(highway_map, road, lane):
            # allocate_the_road_lane(highway_map, road, lane)
            # return lane

    # if orientation == DirType.VERTICAL: # I want the transversal
        # init = rect[0] + 1
    # else:
        # init = rect[1] + 1
        
    # for lane in range (init, end, 10):
        # if is_road_lane_available(highway_map, road, lane):
            # allocate_the_road_lane(highway_map, road, lane)
            # return lane

    return init # No allocation, re-use something else shared

def is_free_offroad_horizontal_lane(highway_map, lane_line):

    def is_horizontal_overlapping(lane_line, lane):
        if lane_line[1] != lane_line[3] or lane_line[1] != lane[1] or lane_line[1] != lane[3]:
            return False
        # Check if they overlap
        return lane_line[3] >= lane[1] and lane[3] >= lane_line[1]
    # print(f' is_free_offroad_horizontal_lane for {lane_line}')
    
    if (lane_line[0] > lane_line[2]): # Ensure right order
        lane_line[0], lane_line[2] = lane_line[2], lane_line[0]

    local_roads_map = highway_map["roads"]
    # if road_name in local_roads_map:

    if not "offroad_horizontal_lane" in local_roads_map["allocations"]:
        local_roads_map["allocations"]["offroad_horizontal_lane"] = []
        
    for lane in local_roads_map["allocations"]["offroad_horizontal_lane"]:
        if is_horizontal_overlapping(lane_line, lane):
            # print(f'   It is NOT free')

            return False

    # print(f'   It is free')
    return True
    
def is_free_offroad_vertical_lane(highway_map, lane_line):

    def is_vertical_overlapping(lane_line, lane):
        if lane_line[0] != lane_line[2] or lane_line[0] != lane[0] or lane_line[0] != lane[2]:
            return False
        # Check if they overlap
        return lane_line[2] >= lane[0] and lane[2] >= lane_line[0]

    # print(f' is_free_offroad_vertical_lane for {lane_line}')

    if (lane_line[1] > lane_line[3]): # Ensure right order
        lane_line[1], lane_line[3] = lane_line[3], lane_line[1]

    local_roads_map = highway_map["roads"]
    # if road_name in local_roads_map:

    if not "offroad_vertical_lane" in local_roads_map["allocations"]:
        local_roads_map["allocations"]["offroad_vertical_lane"] = []
    
    for lane in local_roads_map["allocations"]["offroad_vertical_lane"]:
        if is_vertical_overlapping(lane_line, lane):
            print(f'   It is NOT free')
            return False

    # print(f'    offroad_vertical_lane = {local_roads_map["allocations"]["offroad_vertical_lane"]}')

    # print(f'   It is free')
    return True

def allocate_offroad_horizontal_lane(highway_map, lane_line):
    # print(f' allocate_offroad_horizontal_lane for {lane_line}')
    
    if (lane_line[0] > lane_line[2]): # Ensure right order
        lane_line[0], lane_line[2] = lane_line[2], lane_line[0]

    local_roads_map = highway_map["roads"]
    # if road_name in local_roads_map:
    
    if not "offroad_horizontal_lane" in local_roads_map["allocations"]:
        local_roads_map["allocations"]["offroad_horizontal_lane"] = []
    
    local_roads_map["allocations"]["offroad_horizontal_lane"].append(lane_line)

def allocate_offroad_vertical_lane(highway_map, lane_line):
    # print(f' allocate_offroad_vertical_lane for {lane_line}')

    if (lane_line[1] > lane_line[3]): # Ensure right order
        lane_line[1], lane_line[3] = lane_line[3], lane_line[1]

    local_roads_map = highway_map["roads"]
    # if road_name in local_roads_map:
    
    if not "offroad_vertical_lane" in local_roads_map["allocations"]:
        local_roads_map["allocations"]["offroad_vertical_lane"] = []
    
    local_roads_map["allocations"]["offroad_vertical_lane"].append(lane_line)

def is_offroad_lane_available(highway_map: dict, offset: int, range_for_checking: None | list[int|None, int|None, int|None, int|None]):
    if range_for_checking != None and isinstance(range_for_checking, list) and len(range_for_checking) == 4:

        # print(f" is_offroad_lane_available offset={offset} range_for_checking={range_for_checking}")
        
        # Replace the missing axis (None axis) with offset and test.
        if range_for_checking[0] == None and range_for_checking[2] == None:
            range_for_checking[0] = offset
            range_for_checking[2] = offset
            return is_free_offroad_vertical_lane(highway_map, range_for_checking)
        elif range_for_checking[1] == None and range_for_checking[3] == None:
            range_for_checking[1] = offset
            range_for_checking[3] = offset
            return is_free_offroad_horizontal_lane(highway_map, range_for_checking)

    return True # Default