import socket
import platform


def get_network_host():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)

    # windows doesn't support 0.0.0.0
    if platform.system() == "Windows":
        return ip_address
    else:
        return "0.0.0.0"
