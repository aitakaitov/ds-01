import math
from enum import Enum

GREEN_COLOR_FRACTION = 1 / 3

class NetworkInfo:
    def __init__(self, _id, base_port, node_count, port):
        self.id = _id
        self.port = port
        self.node_count = node_count
        self.base_port = base_port
        self.leader_id = -1
        self.color = None
        self.node_ids = None

        self.round_trip_made = False

        # One to the right if we are not the last node, otherwise the first node
        self.right_neighbour_port = port + 1 if port - base_port != node_count else base_port + 1

        self.right_neighbour_id = -1

    def get_right_neighbour_address(self):
        return f'http://localhost:{self.right_neighbour_port}/message'

    def skip_right_neighbour(self):
        """
        Set the next node in the ring as the right neighbour
        :return:
        """
        self.right_neighbour_port = self.port + 2 if self.port - self.base_port != self.node_count else self.base_port + 1


class BaseRequest:
    def __init__(self, original_id, message_type=None):
        self.original_id = original_id
        self.sender_id = original_id
        self.message_type = message_type


class CollectRequest(BaseRequest):
    def __init__(self, original_id):
        super(CollectRequest, self).__init__(original_id, MessageType.COLLECT_IDS)
        self.ids = [original_id]


class ColorRequest(BaseRequest):
    def __init__(self, original_id, all_node_ids):
        super(ColorRequest, self).__init__(original_id, MessageType.COLORING)
        self.node_color_dict = {}
        self.__determine_coloring(all_node_ids)

    def __determine_coloring(self, all_node_ids):
        node_count = len(all_node_ids)
        green_node_count = math.ceil(node_count * GREEN_COLOR_FRACTION)
        green_nodes = all_node_ids[:green_node_count]
        red_nodes = all_node_ids[green_node_count:]

        for green_node in green_nodes:
            self.node_color_dict[green_node] = Color.GREEN
        for red_node in red_nodes:
            self.node_color_dict[red_node] = Color.RED


class BaseResponse:
    def __init__(self, _id):
        self.id = _id


class Color(Enum):
    RED = 'red',
    GREEN = 'green'


class MessageType(Enum):
    # Health-check ping
    PING = 'ping',
    # Pass node's ID around in the election process
    ELECTION_ROUND = 'election_round'
    # Notify nodes that leader has been elected
    LEADER_ELECTED = 'leader_elected',
    # Collect IDs
    COLLECT_IDS = 'collect_ids',
    # Coloring info
    COLORING = 'coloring',
    # Notify a node that another node is down
    NODE_DOWN = 'node_down'
