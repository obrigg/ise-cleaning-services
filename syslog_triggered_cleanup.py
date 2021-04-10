import logging
import socketserver
import mab_cleanup
from netaddr import *


def delete_mac(mac: str):
    endpoint_id = mab_cleanup.get_endpoint_by_mac(mac)
    print(f"Endpoint ID for MAC {mac} is: {endpoint_id}")
    mab_cleanup.delete_endpoint(endpoint_id)


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
                delete_mac(mac)
            

if __name__ == "__main__":
    try:
        server = socketserver.UDPServer((HOST,PORT), SyslogUDPHandler)
        server.serve_forever(poll_interval=0.5)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        print ("Crtl+C Pressed. Shutting down.")