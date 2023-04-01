import paho.mqtt.client as mqtt
import json
import uuid
from datetime import datetime
from random import uniform
import time
import math

# Define constants
MQTT_BROKER = "192.168.0.223" # "192.168.0.121"  # Change this to your MQTT broker address
MQTT_PORT = 1883
#VEHICLE_ID = "vehicle/1234/status"  # Change this to the desired vehicle ID
OPTITRACK_ID = 12
DTS_ID = "Duckie06"

def generate_mock_data(dt):
    radius = 1
    x = 5 + math.sin(dt)*radius
    y = 5 + math.cos(dt)*radius

    data = {
        "type": "status_vehicle",
        "data": {
            "id": str(12),
            "name": "My Vehicle",
            "timestamp": datetime.now().isoformat(),
            "coordinates": {
                "x": x,
                "y": y,
                "yaw": uniform(0, 360), # grad vs rad?
                "x_abs": uniform(0, N_TILES_X * TILE_LENGTH_MM),
                "y_abs": uniform(0, N_TILES_Y * TILE_WIDTH_MM)
            }
        }
    }
    return json.dumps(data)

id_table = {
    "13": "Duckie06",
    "4": "db01"
}

zone_enabled = False
obstacle_center = (1.5,8.5)

def check_if_close_to_school(pos):
    print(f"Zone Enabled: {zone_enabled}")
    if not zone_enabled:
        return "out_of_zone"
    print(pos)
    distance = math.sqrt((obstacle_center[0] - pos[0])**2 + (obstacle_center[1] - pos[1])**2)
    if distance < 1.5:
        print("zone detected")
        return "in_zone"
    return "out_of_zone"

def check_zone(id, pos):
    data = {"type": "zone",
         "data": {
             "value": check_if_close_to_school(pos)
         }
     }
    client.publish(f"vehicle/{id}/back", to_back_format(data))

def from_echo_format(data):
    data = json.loads(data)
    return json.loads(data["data"])

def to_back_format(data):
    msg = {
        "data": json.dumps(data)
    }
    return json.dumps(msg)

def remap_obstacle(topic, data):
    data = from_echo_format(data)
    client.publish("vehicle/13/obstruction", json.dumps(data))

def reponde_to_service_change(topic, data):
    global zone_enabled
    if "status" not in topic:
        return
    data = json.loads(data)["data"]
    print(data)
    if data["message"] == "built_service":
        print("enable zone")
        zone_enabled = True
    else:
        print("disable zone")
        zone_enabled = False


def forward_optitrack(data):
    #print("optitrack")
    data = json.loads(data)
    id = str(data["data"]["id"])
    if id not in id_table:
        return
    other_id = id_table[id]
    pos = (data["data"]["coordinates"]["x"],data["data"]["coordinates"]["y"])
    check_zone(other_id, pos)
    client.publish(f"vehicle/{other_id}/back", to_back_format(data))
    print(id)


def on_message(client, userdata, msg):
    print(msg.topic)
    if "vehicle" in msg.topic:
        if "status" in msg.topic:
            forward_optitrack(msg.payload.decode())
        elif "obstacle" in msg.topic:
            remap_obstacle(msg.topic, msg.payload.decode())
    elif "service" in msg.topic:
        reponde_to_service_change(msg.topic, msg.payload.decode())
    else:
        data = msg.payload.decode()
        print("Got a message: " + data)


# Define callback function to handle MQTT connection
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("vehicle/+/status")
    client.subscribe("vehicle/+/obstacle")
    client.subscribe("service/+/status")

# Define MQTT client and connect to broker
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT)

client.loop_forever()
# Publish mock data every 1 seconds
while True:
    print("Publishing mock data...")
    #client.publish(VEHICLE_ID, generate_mock_data(time.time()))
    print("Done...")
    time.sleep(1)

if __name__ == "__main__":
    print("start")