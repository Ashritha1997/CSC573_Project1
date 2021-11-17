import pickle
import threading
import socket
import re

# Key is peer hostname. Value is peer upload port
peer_list = {}
# Key is RFC Number. Value is a list of dictionaries {"PEER HOST": hostname, "RFC TITLE": rfc title}
rfc_list = {}


def format_response_add(response_code, data):
    version = "P2P-CI/1.0"
    lines = data.split("\n")
    peer_host = re.sub(r"HOST: ", "", lines[1])
    peer_upload = re.sub(r"PORT: ", "", lines[2])
    rfc_number = int(re.search(r"RFC (\d+)", lines[0]).group(1))
    rfc_title = re.sub(r"TITLE: ", "", lines[3])
    message = version + " " + response_code[0] + " " + response_code[1] + "\n" \
              + "RFC {} ".format(rfc_number) + rfc_title + " " + peer_host + " " + peer_upload
    return message


def format_response_list(response_code):
    global rfc_list
    global peer_list
    message = "P2P-CI/1.0 " + response_code[0] + " " + response_code[1] + "\n"
    for rfc_number, rfc_info in rfc_list.items():
        for peer in rfc_info:
            message += "RFC {} ".format(rfc_number) + peer["RFC TITLE"] + " " + peer["PEER HOST"] + " " + peer_list[
                peer["PEER HOST"]] + "\n"
    return message


def format_response_lookup(data):
    global rfc_list
    global peer_list
    message = "P2P-CI/1.0 "
    lines = data.split("\n")
    # RFC Number is in the zero line
    # RFC Title is in the 3rd line
    rfc_number = int(re.search(r"RFC (\d+)", lines[0]).group(1))
    rfc_title = re.sub(r"TITLE: ", "", lines[3])
    if rfc_number in rfc_list.keys():
        message += "200 " + "OK " + "\n"
        for peer in rfc_list[rfc_number]:
            message += "RFC {} ".format(rfc_number) + peer["RFC TITLE"] + " " + peer["PEER HOST"] + " " + peer_list[
                peer["PEER HOST"]] + "\n"
        return message

    else:
        message += "404 " + "Not Found"
        return message

def add_peer(data):
    global peer_list
    lines = data.split("\n")
    # Hostname of the client is on line 1
    # Port Number that the client is using for the upload process is on line 2
    peer_host = re.sub(r"HOST: ", "", lines[1])
    peer_upload = re.sub(r"PORT: ", "", lines[2])
    peer_list[peer_host] = peer_upload


def add_rfc(data):
    global rfc_list
    lines = data.split("\n")
    # RFC Number is in the zero line
    # RFC Title is in the 3rd line
    rfc_number = int(re.search(r"RFC (\d+)", lines[0]).group(1))
    rfc_title = re.sub(r"TITLE: ", "", lines[3])
    peer_host = re.sub(r"HOST: ", "", lines[1])
    if rfc_number in rfc_list.keys():
        rfc_list[rfc_number].append({"PEER HOST": peer_host, "RFC TITLE": rfc_title})
    else:
        rfc_list[rfc_number] = [{"PEER HOST": peer_host, "RFC TITLE": rfc_title}]


def client_thread(clientSocket, clientAddress, lock):
    global peer_list
    global rfc_list
    while True:
        raw_data = clientSocket.recv(1024)
        data = raw_data.decode()
        first_line = data.split("\n")[0]
        if re.search(r"ADD", first_line):
            lock.acquire()
            add_peer(data)
            add_rfc(data)
            print(peer_list)
            print(rfc_list)
            lock.release()
            response = format_response_add(("200", "OK"), data)
            clientSocket.send(response.encode())
        elif re.search(r"LIST", first_line):
            lock.acquire()
            print(peer_list)
            print(rfc_list)
            response = format_response_list(("200", "OK"))
            lock.release()
            clientSocket.send(response.encode())
        elif re.search(r"LOOKUP", first_line):
            lock.acquire()
            response = format_response_lookup(data)
            lock.release()
            clientSocket.send(response.encode())


def main():
    # Entry point for server.py
    serverPort = 7734
    serverName = "127.0.0.1"
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind((serverName, serverPort))
    serverSocket.listen()
    lock = threading.Lock()
    while True:
        clientSocket, clientAddress = serverSocket.accept()
        threading.Thread(target=client_thread, args=(clientSocket, clientAddress, lock)).start()


main()
