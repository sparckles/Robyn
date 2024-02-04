import socket
import platform


def get_network_host():
    # windows doesn't support 0.0.0.0
    if platform.system() == "Windows":
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    else:
        return "0.0.0.0"
