import os
import requests
import json
import xmltodict
from time import time
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


######           User Inputs        ######
list_of_group_names = [ "AAA-Vouchers",
                        "BBB-Vouchers",
                        "Vitorcam-IPCamera",
                        "PartnerTV-Android-Streamer"
                    ]

######   Setting up the environment ######
ise_user = os.environ.get('ISE_USER', "admin")
ise_password = os.environ.get('ISE_PASSWORD', "")
base_url = "https://" + os.environ.get('ISE_IP', "") + ":9060/ers/config/"

auth = HTTPBasicAuth(ise_user, ise_password)
headers = {"Content-Type": "application/json",
           "Accept": "application/json"}


def get_ise_group_id(group_name: str):
    '''
    This function will return the ISE group id a given group name.
    '''
    print(f"Fetching for ISE for endpoint group {group_name}...")
    url = base_url + "endpointgroup/name/" + group_name
    response = requests.get(url=url, auth=auth, headers=headers, verify=False)
    if response.status_code == 200:
        group_id = response.json()['EndPointGroup']['id']
        print(f"ISE endpoint group {group_name}, id: {group_id}")
        return(group_id)
    else:
        print(f"ERROR: Group {group_name} was not found")
        return("ERROR")


def get_endpoints_by_group_id(groupId: str):
    if groupId == "":
        url = base_url + "endpoint?size=10"
    else:
        url = base_url + f"endpoint?size=100&filter=groupId.EQ.{groupId}"
    isFinished = False
    list_of_endpoints = []
    while not isFinished:
        response = requests.get(url=url, headers=headers, auth=auth, verify=False)
        if response.status_code != 200:
            print(f"An error has occurred: {response.json()}")
        else:
            endpoints = response.json()['SearchResult']['resources']
            if len(endpoints) > 0:
                list_of_endpoints += endpoints
            if 'nextPage' not in response.json()['SearchResult'].keys():
                isFinished = True
            else:
                url = response.json()['SearchResult']['nextPage']['href']
    if len(list_of_endpoints) > 0:
        return(list_of_endpoints)


def check_ise_auth_status(mac_address: str):
    url = "https://" + os.environ.get('ISE_IP', "") + \
        "/admin/API/mnt/Session/MACAddress/" + mac_address
    response = requests.get(url=url, auth=auth, verify=False)
    if response.status_code != 200:
        print(f"An error has occurred: {response.text()}")
        return("ERROR")
    else:
        status = xmltodict.parse(response.text)
        return(status['sessionParameters']['acct_status_type'])
    

def delete_endpoint(endpoint_id: str):
    url = base_url + "endpoint/" + endpoint_id
    response = requests.delete(url=url, auth=auth, headers=headers, verify=False)
    if response.status_code != 204:
        print(f"Error deleting endpoint {endpoint_id}: {response.text}")

# Translate group names to group IDs
list_of_group_ids = []
for group_name in list_of_group_names:
    groupId = get_ise_group_id(group_name)
    list_of_group_ids.append(groupId)
# Gather all relevant endpoints
list_of_endpoints = []
for groupId in list_of_group_ids:
    endpoints = get_endpoints_by_group_id(groupId)
    if endpoints != None:
        list_of_endpoints += endpoints
print(f"Received a total of {len(list_of_endpoints)} endpoints.")

for endpoint in list_of_endpoints:
    #print(endpoint)
    status = check_ise_auth_status(endpoint['name'])
    if status == "Stop":
        print(f"Deleting endpoint {endpoint['name']}")
        delete_endpoint(endpoint['id'])