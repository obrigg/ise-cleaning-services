import os
import requests
import json
import xmltodict
from time import time
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


######   Setting up the environment ######
ise_user = os.environ.get('ISE_USER', "admin")
ise_password = os.environ.get('ISE_PASSWORD', "")
base_url = "https://" + os.environ.get('ISE_IP', "") + ":9060/ers/config/"

auth = HTTPBasicAuth(ise_user, ise_password)
headers = {"Content-Type": "application/json",
           "Accept": "application/json"}


def get_ise_cleanup_groups():
    '''
    This function will search ISE for endpoint groups that include the
    tag #cleanup in their description for the cleanup process.
    It will return a list of group IDs.
    '''
    print("Fetching ISE's endpoint groups...")
    url = base_url + "endpointgroup?size=100"
    response = requests.get(url=url, auth=auth, headers=headers, verify=False)
    if response.status_code == 200:
        cleanup_groups = []
        groups = response.json()['SearchResult']['resources']
        for group in groups:
            if "#cleanup" in group['description'].lower():
                print(f"Endpoint group {group['name']} will be cleaned up")
                cleanup_groups.append(group['id'])
        return(cleanup_groups)
    else:
        print(f"ERROR: {response.text}")
        return("ERROR")


def get_endpoints_by_group_id(groupId: str):
    if groupId == "":
        url = base_url + "endpoint?size=100"
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


def get_endpoint_by_mac(mac: str):
    url = base_url + f"endpoint?size=100&filter=mac.EQ.{mac}"
    response = requests.get(url=url, headers=headers, auth=auth, verify=False)
    if response.status_code != 200:
        print(f"An error has occurred: {response.json()}")
    else:
        endpoint_id = response.json()['SearchResult']['resources'][0]['id']
        return(endpoint_id)


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
    else:
        print(f"Successfully deleted {endpoint_id}")

if __name__ == "__main__":
    # Gather relevant cleanup groups
    cleanup_groups = get_ise_cleanup_groups()
    # Gather all relevant endpoints
    list_of_endpoints = []
    for groupId in cleanup_groups:
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