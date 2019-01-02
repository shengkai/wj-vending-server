# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
# import serial
import json
import time
from . import socket_server
import sys


@csrf_exempt
def send_command(req):
    if req.method == 'POST':
        data = req.POST
        # print(json_string)

        secret = data['secret'] if 'secret' in data else ""
        action = data['action'] if 'action' in data else ""
        mac_address = data['mac_address'] if 'mac_address' in data else ""
        box_id = int(data['box'] if 'box' in data else 0)
        extra = data['data'] if 'data' in data else ""

        try:
            command = socket_server.compose_command(action, box_id)
            socket_server.clean_received_data(mac_address)
            logfile = open("command.log", "a")
            logfile.write(
                'Sending ' + action + ' command to ' + mac_address + ':' + str(box_id)
                + ' HEX: ' + socket_server.byte_humanized(command) + '\n')
            logfile.close()
            socket_server.send_command(mac_address, command)
        except Exception as ex:
            print(sys.exc_info())
            return render_to_response('send_command.html', {'uf': str(ex)})

        return_data = socket_server.receive_message(mac_address)

        if action == 'open':
            if return_data is not None and len(return_data) > 0:
                print('Received: ' + socket_server.byte_humanized(return_data))
                if return_data[3] < 0x05:
                    return HttpResponse('success')

            return HttpResponse('fail')
        elif action == 'check':
            if return_data is not None and len(return_data) > 0:
                print('Received: ' + socket_server.byte_humanized(return_data))
                if return_data[3] < 0x05:
                    return HttpResponse('open')
                elif return_data[3] >= 0x05:
                    return HttpResponse('error')
                else:
                    return HttpResponse('close')

        return HttpResponse('fail')
    else:
        pass

    return render_to_response('send_command.html', {'uf': ''})


@csrf_exempt
def show_status(req):
    clients = socket_server.show_clients()
    return render_to_response('status.html', {'clients': clients})