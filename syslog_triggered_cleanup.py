import logging
import socketserver
import mab_cleanup
from netaddr import *
from threading import Thread


def delete_mac(mac: str, cleanup_groups: list):
    endpoint_id, endpoint_group_id = mab_cleanup.get_endpoint_by_mac(mac)
    print(f"Endpoint ID for MAC {mac} is: {endpoint_id}, Group ID is: {endpoint_group_id}")
    if cleanup_groups == [] or endpoint_group_id in cleanup_groups:
        mab_cleanup.delete_endpoint(endpoint_id)
    else:
        print(f"Group {endpoint_group_id} is not in the cleanup group list. Ignoring.")


HOST, PORT = "0.0.0.0", 514

logging.basicConfig(level=logging.INFO, format='%(message)s', datefmt='')

class SyslogUDPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = bytes.decode(self.request[0].strip())
        socket = self.request[1]
        #print( "\n%s : " % self.client_address[0], str(data),"\n")
        if "Accounting stop request" in data and not "NAS-Port-Type=Virtual" in data:
            mac = data[data.find("UserName=")+9:data.find("UserName=")+26]
            mac = mac.replace("-",":")
            print(f"Received account stop for {mac}")
            try:
                EUI(mac)
            except:
                print(f"{mac} is not a MAC address, probably not a MAB endpoint.")
                mac = ""
            if mac != "":
                t = Thread(target=delete_mac, args=(mac, cleanup_groups))
                t.start()
            

if __name__ == "__main__":
    cleanup_groups = mab_cleanup.get_ise_cleanup_groups()
    if cleanup_groups == "ERROR" or cleanup_groups == []:
        print("No filter found - cleaning all endpoint groups.")
        cleanup_groups = []
    try:
        server = socketserver.UDPServer((HOST,PORT), SyslogUDPHandler)
        server.serve_forever(poll_interval=0.5)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        print ("Crtl+C Pressed. Shutting down.")