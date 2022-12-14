import jsonpickle
import random

import os

from flask_cors import CORS
from flask import Flask, request
from utils import *
import threading
import requests
from datetime import datetime

import socket
socket.setdefaulttimeout(5)

PRINT_TO_STD = True
if not PRINT_TO_STD:
    open('output', 'w+', encoding='utf-8').close()

TIMEOUT_SEC = 15
IP_ADDRESS = os.environ['IP_ADDRESS']
NODE_COUNT = os.environ['NUM_NODES']

network_info = NetworkInfo(random.randint(0, 2_000_000_000), IP_ADDRESS, NODE_COUNT)
timers = {}


def create_and_start_timer(func):
    timer = threading.Timer(TIMEOUT_SEC, func)
    timer.start()
    return timer


def send_election_message():
    try:
        log_message(f'Trying to send an election message to the right neighbour')
        send_message(BaseRequest(network_info.id, MessageType.ELECTION_ROUND))
        log_message(f'Reached the right neighbour')

        if not network_info.round_trip_made:
            timers['election_init'] = create_and_start_timer(send_election_message)

    except BaseException:
        log_message(f'Could not contact the neighbour, retry in {TIMEOUT_SEC} seconds')
        timers['election_init'] = create_and_start_timer(send_election_message)


timers['election_init'] = create_and_start_timer(send_election_message)


def send_message(message):
    requests.post(network_info.get_right_neighbour_address(), jsonpickle.encode(message, keys=True))


def forward_message(message):
    try:
        message.sender_id = network_info.id
        send_message(message)
    except BaseException:
        log_message(f'Could not forward message')


def sender_this_node(message):
    return message.original_id == network_info.id


def log_message(string):
    if PRINT_TO_STD:
        print(f'[{datetime.utcnow()}][{network_info.id}]\t{string}', flush=True)
    else:
        with open('output', 'a', encoding='utf-8') as f:
            print(f'[{datetime.utcnow()}][{network_info.id}]\t{string}', file=f, flush=True)


log_message(f'Node {network_info.id} starting up')
log_message(f'\nNode IP: {network_info.ip}\nNeighbour IP: {network_info.right_neighbour_ip}\nNumber of nodes: {network_info.node_count}')

#
# FLASK needs to be at the bottom since we need to do some things before it blocks on the run() call
#


app = Flask(__name__)

@app.route('/message', methods=['POST'])
def process_message():
    data = jsonpickle.decode(request.data, keys=True)

    # simply reply to pings
    if data.message_type == MessageType.PING:
        return f'{network_info.id}', 200

    # if the election is ongoing
    elif data.message_type == MessageType.ELECTION_ROUND:
        # block messages with lower id
        if data.original_id < network_info.id:
            log_message(f'Received election message with lower ID, blocking')
            return f'{network_info.id}', 200
        # this node is the leader
        elif sender_this_node(data):
            timers['election_init'].cancel()
            network_info.round_trip_made = True
            # announce leader
            log_message(f'Election message came back to origin, announcing as leader')
            send_message(BaseRequest(network_info.id, MessageType.LEADER_ELECTED))
            network_info.leader_id = network_info.id

            return f'{network_info.id}', 200
        # forward the message
        else:
            forward_message(data)
            return f'{network_info.id}', 200

    # register the elected leader
    elif data.message_type == MessageType.LEADER_ELECTED:
        timers['election_init'].cancel()
        network_info.round_trip_made = True

        log_message(f'Leader elected message received')
        network_info.leader_id = data.original_id

        # if the message returns back to the leader
        # send a message to collect IDs
        if sender_this_node(data):
            log_message(f'Leader elected message came back to leader')
            log_message(f'Sending collection message')
            send_message(CollectRequest(network_info.id))
        else:
            forward_message(data)

        return f'{network_info.id}', 200

    # round trip ids collect message
    elif data.message_type == MessageType.COLLECT_IDS:
        # if the message came back
        if sender_this_node(data):
            log_message(f'Collection message came back to origin')
            network_info.node_ids = data.ids
            log_message(f'Color set to GREEN')
            log_message(f'Sending coloring request')
            color_request = ColorRequest(network_info.id, network_info.node_ids)
            send_message(color_request)
            pass
        # add node ID and pass message
        else:
            log_message(f'Adding ID to the collection message')
            data.ids.append(network_info.id)
            send_message(data)

        return f'{network_info.id}', 200

    # coloring message
    elif data.message_type == MessageType.COLORING:
        # message came back
        if sender_this_node(data):
            log_message('Coloring request came back to origin')
            log_message('Colors are all set')
            log_message(f'\nNode ID\tColor\n' + '\n'.join(f'{node}\t {color}' for node, color in data.node_color_dict.
                                                         items()))
        # this node is getting colored
        else:
            log_message(f'Setting color to {data.node_color_dict[network_info.id]}')
            network_info.color = data.node_color_dict[network_info.id]
            forward_message(data)

        return f'{network_info.id}', 200


CORS(app)
app.run('0.0.0.0')
