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
        data = req.POST
        json_string = json.dumps(req.POST)
        print(json_string)
        logfile = file("command.log", "a")
        logfile.write(json_string)
        logfile.write('\n')
        logfile.close()

        secret = data['secret'] if 'secret' in data else ""
        action = data['action'] if 'action' in data else ""
        mac_address = data['mac_address'] if 'mac_address' in data else ""
        box_id = int(data['box'] if 'box' in data else 0)
        extra = data['data'] if 'data' in data else ""

        try:
            command = socket_server.compose_command(action, box_id, extra)
            socket_server.clean_received_data(mac_address)
            socket_server.send_command(mac_address, command)
        except Exception as ex:
            print sys.exc_info()
            return render_to_response('send_command.html', {'uf': str(ex)})

        return_data = socket_server.receive_message(mac_address)

        if return_data is not None and len(return_data) > 0:
            print('Received: ' + socket_server.byte_humanized(return_data))
            return HttpResponse('success')

        return HttpResponse('fail')
    else:
        pass

    return render_to_response('send_command.html', {'uf': ''})


@csrf_exempt
def show_status(req):
    clients = socket_server.show_clients()
    return render_to_response('status.html', {'clients': clients})