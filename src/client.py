#!/usr/bin/env python3

import socket
import time
import select
import logging
import struct

from google.protobuf.internal.encoder import _VarintEncoder
from google.protobuf.internal.decoder import _DecodeVarint
import erl_playground_pb2

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 9900        # The port used by the server

def encode_varint(value):
    """ Encode an int as a protobuf varint """
    data = []
    _VarintEncoder()(data.append, value, False)
    return b''.join(data)


def decode_varint(data):
    """ Decode a protobuf varint to an int """
    return _DecodeVarint(data, 0)[0]


def send_message(conn, msg):
    """ Send a message, prefixed with its size, to a TPC/IP socket """
    data = msg.SerializeToString()
    size = encode_varint(len(data))
    conn.sendall(b'\x00'+size+data)


def recv_message(conn):
    """ Receive a message, prefixed with its size, from a TCP/IP socket """
    # Receive the message size
    bitsize = conn.recv(2)
    size=struct.unpack("!i", b'\x00\x00'+bitsize)[0]
    # Receive the message data
    data = conn.recv(size)
    # Decode the message
    msg = erl_playground_pb2.envelope()
    msg.ParseFromString(data)
    message = msg.uncompressed_data.server_message_data.message
    return message

def check_messages_from_server():
    ready = select.select([s], [], [], 0.0)
    if ready[0]:
        response = recv_message(s)
        server_log(response)
    return "no_messages"

def create_session(username, s):
    logging.debug('Sending create-session msg with username \"%s\"' % username)
    env = erl_playground_pb2.envelope()
    env.uncompressed_data.type = 1
    env.uncompressed_data.create_session_data.username = username
    send_message(s, env)

def send_user_request(msg, s):
    logging.debug('Sending user_request msg with message \"%s\"' % msg)
    env = erl_playground_pb2.envelope()
    env.uncompressed_data.type = 3
    env.uncompressed_data.user_request_data.message = msg
    send_message(s, env)

def server_log(msg):
    msgList = msg.split('~n')
    for m in msgList:
        NORMAL = '\033[0m'
        COLOR = '\033[92m'
        logging.info('[{color}SERVER{normal}]: {message}'.format(color=COLOR, normal=NORMAL, message=m))
    print(">>> ", end='', flush=True)

import sys
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%H:%M:%S')
# Open a TCP/IP socket
while True:
    try:#moved this line here
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.setblocking(0)

            # Send a connection request
            username = input('Insert username\n>>> ')
            create_session(username, s)

            logging.info('Connection established. Insert \'quit\' to exit.')

            user_input = ''
            while user_input != 'quit':
                check_messages_from_server()
                incoming = select.select([sys.stdin],[],[],0.0)[0]
                if len(incoming) > 0:
                    user_input = sys.stdin.readline()
                    if user_input[-1:] == '\n':
                        user_input = user_input[:-1]
                    if user_input == 'quit':
                        break
                    send_user_request(user_input, s)
                time.sleep(0.1)
        break
    except socket.error:
        print("Connection Failed, Retrying..")
        time.sleep(1)
