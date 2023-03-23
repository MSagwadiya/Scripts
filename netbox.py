#!/usr/bin/env python
import os
import json
import pynetbox
import subprocess
import requests

URL = 'https://netbox8.ndc.aptportfolio.com'
TOKEN = '3b9cd39db5c5fa04b3557cb426c984564b1cf17e'
FILTER_TAGS = ['AWX']
headers = {
    'Accept': 'application/json ; indent=4',
    'Authorization': 'Token %s' % (TOKEN),
}
device_url = URL + '/api/dcim/devices'
devices = []

# Get all devices from NetBox
def get_data(api_url):
    out = []
    while api_url:
        api_output = requests.get(api_url, headers=headers, verify=False)
        api_output_data = api_output.json()

        if isinstance(api_output_data, dict) and "results" in api_output_data:
            out += api_output_data["results"]
            api_url = api_output_data["next"]
    return out

hosts_list = get_data(device_url)

# Filter out inactive devices
for i in hosts_list:
    if FILTER_TAGS:
      tag_list = []
      if i['tags']:
          for tag_item in i['tags']:
               tag_list.append(tag_item['name'])
      if any(item in FILTER_TAGS for item in tag_list):
            if i['status']:
                if i['status']['label'] == 'Active':
                    devices.append(i)
ansible_hosts = []
ansible_env = os.environ.copy()
ansible_env["ANSIBLE_CACHE_PLUGIN"] = "memory"

# Update CPU information for each active device
for device in devices:
    if device['display_name']:
        cmd = "ansible -i %s, %s  -m gather_facts | grep ansible_processor_vcpus | awk '{{print $2}}' | tr -d \,"
        fact = subprocess.check_output(cmd % (device['display_name'], device['display_name']), shell=True, env=ansible_env)
        print(fact)
        nb = pynetbox.api(url=URL, token=TOKEN)
        nb.http_session.verify = False
        device_id = nb.dcim.devices.get(name=device['display_name'])
        device_data = {'custom_fields': {'CPU': fact.decode('utf-8')}}
        result = device_id.update({
            'id': device_id.id,
            'custom_fields': device_data['custom_fields']
        })
        print(device_id.name)
