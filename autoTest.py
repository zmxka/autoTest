import paho.mqtt.client as mqtt
import math
import threading
import time
import requests
from queue import Queue
from functools import reduce

def ship_info():
	while True:
		time.sleep(1)
		client.publish(topic,get_payload(lng, lat, state, yaw, task_id))
def app_info(msg):
	cmd = str(msg.payload)[2:-2].split(';')
	if(cmd[0] == '$A'):
		global task_id
		task_id = '\"'+cmd[1]+'\"'
		print(task_id)
		switchCommands[cmd[0]](cmd[1], lng, lat)
	else:
		switchCommands[str(msg.payload)[2:-1]]()

def on_connect(client, userdata, flag, rc):
	print('mqtt连接')
	client.subscribe('APP2SHIP/'+ship_Id)
	th1 = threading.Thread(target = ship_info, name='ship_info')
	th1.setDaemon(True)
	th1.start()

def on_message(client, userdata, msg):
	th2 = threading.Thread(target = app_info, name = 'app_cmd',args=(msg,))
	th2.setDaemon(True)
	th2.start()
	
def get_payload(lng, lat, state, yaw, task_id):
	return '{"ship_number": 0, "pd_rematime": 12388, "ship_id": 0, "pd_current": 185, "speed": 1.5,'\
				'"index": 0, "temperature": "1,1,1", "err": 0, "yaw": %f, "route_id": %s, "pd_percent": 80,'\
				'"lng": %f, "lat": %f, "state": %d}' %(yaw, task_id, lng, lat, state)

def start_task (task_id, Lng, Lat):
	global lng, lat, yaw, state
	global is_back, is_stop, is_pause
	res = requests.post('http://orca-tech.cn:7777/orcatech/mobile/route/select', json = {"id": task_id})
	data = res.json()
	route = data['data']['route'].split('|')
	if len(route) == 2:
		route = list(map(lambda x: x[0:-1].split(';'), route))
		route = reduce(lambda x,y: x+y,route)
		route = list(map(lambda x: x.split(';'), route))
		route = reduce(lambda x,y: x+y, route)
		route = list(map(lambda x: x.split(','), route))
		route = list(map(lambda x: list(map(float, x)), route))
		route.insert(0,[Lng,Lat])
	else:
		route = list(map(lambda x: x.split(';'), route))
		route = reduce(lambda x,y: x+y, route)
		route = list(map(lambda x: x.split(','), route[0:-1]))
		route = list(map(lambda x: list(map(float, x)), route))
		route.insert(0,[Lng,Lat])
	for i in range(1,len(route)):
		if(is_stop == 1):
			state == 0
			break
		while True:
			time.sleep(1)
			if(is_stop == 1):
				break
			elif(is_pause == 1):
				state = -1
				continue
			else:
				state = 1
			lng = lng + (route[i][0] - route[i-1][0])/20
			lat = lat + (route[i][1] - route[i-1][1])/20
			yaw = ship_angle(route[i-1][0], route[i-1][1], route[i][0], route[i][1])
			if abs(route[i][0] - lng) < abs(route[i][0] - route[i-1][0])/50 or abs(route[i][1] - lat) < abs(route[i][1] - route[i-1][1])/50:
				break
	if(is_stop == 1):
		is_stop =0
	else:
		state = -3
   
def ship_angle(x1, y1, x2, y2):
	angle = 0.0
	dx = x2 - x1
	dy = y2 - y1
	ds = math.sqrt(pow(dx,2)+pow(dy,2))
	if(dx > 0 and dy >0):
		angle = math.asin(dx/ds)
	elif (dx > 0 and dy < 0):
		angle = -math.asin(dx/ds) + math.pi
	elif (dx < 0 and dy < 0):
		angle = -math.asin(dx/ds) + math.pi
	elif (dx < 0 and dy > 0 ):
		angle = math.asin(dx/ds) + 2 * math.pi
	return math.degrees(angle)

def pause_task():
	global is_pause
	is_pause = 1

def continue_task():
	global is_pause
	is_pause = 0

def stop_task():
	global is_stop,state
	is_stop = 1
	print(state)
	if(state == -3):
		state = 0
		is_stop =0

def back_task():
	global is_back
	is_back = 1

switchCommands = {
	'$A': start_task,
	'$B;0#' : pause_task,
	'$B;1#': continue_task,
	'$B;2#': stop_task,
	'$C;#': back_task,
}

ship_Id = input()
lng = 108.898545
lat = 34.247700
state = 0
yaw = 0
task_id = '0'
is_pause = 0
is_stop = 0
is_back = 0
topic = 'SHIP2APP/' + ship_Id +'/BASIC'
client = mqtt.Client('zhou', True ,None)
client.on_connect = on_connect
client.on_message = on_message
client.connect('zmxka.com', 11883, 60)
client.loop_forever()