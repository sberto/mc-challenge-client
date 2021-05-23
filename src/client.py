#!/usr/bin/env python3

import socket
import time
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
    size = encode_varint(len(data)+8)
    conn.sendall(size)
    conn.sendall(data)


def recv_message(conn):
    """ Receive a message, prefixed with its size, from a TCP/IP socket """
    # Receive the size of the message data
    data = b''
    while True:
        try:
            data += conn.recv(8)
            size = decode_varint(data)
            break
        except IndexError:
            pass
    # Receive the message data
    data = conn.recv(16384)
    # Decode the message
    msg = erl_playground_pb2.server_message()
    msg.ParseFromString(data)
    return msg

# Open a TCP/IP socket
rpc_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
rpc_conn.connect((HOST, PORT))

# Send a connection request
env = erl_playground_pb2.envelope()
env.uncompressed_data.type = 1
env.uncompressed_data.create_session_data.username = 'Jeb'
send_message(rpc_conn, env)


# Receive the connection response
response = recv_message(rpc_conn)
print(response)
# bla = response.uncompressed_data.server_message_data.message
# rpc_conn.recv(16384)