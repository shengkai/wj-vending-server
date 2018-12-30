# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
# import serial
import json
import time
import socket_server
import sys


@csrf_exempt
def send_command(req):
    if req.method == 'POST':
        logfile = file("command.log", "a")
        logfile.write(req.POST['txt'])
        logfile.write('\n')
        logfile.close()

        json_data = json.loads(req.POST['txt'])
        secret = json_data['secret'] if 'secret' in json_data else ""
        action = json_data['action'] if 'action' in json_data else ""
        mac_address = int(json_data['mac_address'] if 'mac_address' in json_data else 0)
        box_id = int(json_data['box'] if 'box' in json_data else 0)
        data = json_data['data'] if 'data' in json_data else ""

        try:
            command = socket_server.compose_command(action, box_id, data)
            socket_server.clean_received_data(mac_address)
            print(command.encode('hex'))
            socket_server.send_command(mac_address, command)
            time.sleep(1)

        except Exception as ex:
            print sys.exc_info()
            return render_to_response('send_command.html', {'uf': str(ex)})

        return_data = socket_server.receive_message(mac_address).encode('hex')

        return HttpResponse(return_data)
    else:
        pass

    return render_to_response('send_command.html', {'uf': ''})


@csrf_exempt
def show_status(req):
    clients = socket_server.show_clients()
    return render_to_response('status.html', {'clients': clients})