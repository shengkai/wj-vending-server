# -*- coding: utf-8 -*-
import socket
import threading
import select
import struct
import sys
import Queue
import time


clients = {}
recv_queues = {}
# send_queues = {}
inputs = []
outputs = []


def compose_command(action, box_id, data):
    cmd = '\x24' + '\x80' + '\x0c'
    if action == 'open':
        cmd += '\x01'
    elif action == 'check':
        cmd += '\x02'
    else:
        raise Exception("No action.")

    cmd += chr(box_id)
    cmd += '\xff\xff\x00\x00\x00'

    crc_code = get_crc(cmd)

    cmd += crc_code
    cmd += '\x21'

    return cmd


def get_crc(byte_data):
    crc = None
    for byte in bytearray(byte_data):
        if crc is None:
            crc = byte
        else:
            crc ^= byte

    return chr(crc)


def byte_pbyte(data):
    # check if there are multiple bytes
    if len(str(data)) > 1:
        # make list all bytes given
        msg = list(data)
        # mark which item is being converted
        s = 0
        for u in msg:
            # convert byte to ascii, then encode ascii to get byte number
            u = str(u).encode("hex")
            # make byte printable by canceling \x
            u = str(u)
            # apply coverted byte to byte list
            msg[s] = u
            s = s + 1
        msg = " ".join(msg)
    else:
        msg = data
        # convert byte to ascii, then encode ascii to get byte number
        msg = str(msg).encode("hex")
        # make byte printable by canceling \x
        msg = str(msg)
    # return printable byte
    return msg


def listener():
    ip_port = ('0.0.0.0', 6000)
    iot = socket.socket()
    iot.setblocking(False)
    iot.bind(ip_port)
    iot.listen(50)
    inputs.append(iot)
    print('IoT server started...')

    while inputs:
        readable, writable, exceptional = select.select(inputs, outputs, inputs)
        for s in readable:
            if s is iot:
                conn, client_address = s.accept()
                print(str(client_address) + " connected.")
                conn.setblocking(False)
                conn.send(compose_command('check', 1, []))
                inputs.append(conn)
            else:
                try:
                    data = s.recv(1024)
                    print(byte_pbyte(data))
                    if len(data) > 5 and data[0] == '\xf0':
                        if data[4] == '\xff':
                            # A readable client socket has data
                            print(sys.stderr, 'received "%s" from %s' % (data, s.getpeername()))
                            client_id = ord(data[5])
                            print('Client id %d is online.' % client_id)
                            clients[client_id] = s
                            # send_queues[s] = Queue.Queue()
                            recv_queues[s] = Queue.Queue()
                        # message_queues[s].put(data)
                        # Add output channel for response
                        # if s not in outputs:
                        #	outputs.append(s)
                        else:
                            client_id = data[3]
                            recv_queues[s].put(data)
                except Exception as ex:
                    # Interpret empty result as closed connection
                    print(ex)
                    # Stop listening for input on the connection
                    if s in outputs:
                        outputs.remove(s)
                    inputs.remove(s)
                    s.close()

                    # Remove message queue
                    keys = [x[0] for x in clients.items() if s is x[1]]
                    if len(keys) == 1:
                        del clients[keys[0]]
                    # if s in send_queues:
                    #     del send_queues[s]
                    if s in recv_queues:
                        del recv_queues[s]

        # for s in writable:
        #	try:
        #		next_msg = send_queues[s].get_nowait()
        #	except Queue.Empty:
        #		# No messages waiting so stop checking for writability.
        #		print('output queue for', s.getpeername(), 'is empty')
        #		outputs.remove(s)
        #	else:
        #		print( 'sending "%s" to %s' % (next_msg, s.getpeername()))
        #		s.send(next_msg)

        # Handle "exceptional conditions"
        for s in exceptional:
            print('Handling exceptional condition for', s.getpeername())
            # Stop listening for input on the connection
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()

            # Remove message queue
            keys = [x[0] for x in clients.items() if s in x[1]]
            if len(keys) == 1:
                clients.pop(keys)
            # del send_queues[s]
            del recv_queues[s]


server_thread = threading.Thread(target=listener)
server_thread.daemon = True
server_thread.start()


def socket_heart():
    while True:
        print('Live clients: ' + str(clients.keys()))
        for s in clients:
            clients[s].send('\x00')
        time.sleep(10)


heart_thread = threading.Thread(target=socket_heart)
heart_thread.daemon = True
heart_thread.start()


def clean_received_data(client_id):
    if client_id not in clients:
        raise Exception("This client is not logged in.")

    sock = clients[client_id]
    while not recv_queues[sock].empty():
        recv_queues[sock].get()


def send_command(client_id, command):
    if client_id not in clients:
        raise Exception("This client is not logged in.")

    sock = clients[client_id]
    print('Sending command: ' + byte_pbyte(command))
    sock.send(command)


# send_queues[sock].put(commstr)
# outputs.append(sock)

def receive_message(client_id):
    if client_id not in clients:
        raise Exception("This client is not logged in.")

    sock = clients[client_id]
    message = recv_queues[sock].get()
    return message


def show_clients():
    return clients.keys()