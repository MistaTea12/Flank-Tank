import socket
from _thread import *
import sys

currentPlayer = 0
server = socket.gethostname()
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    print("SERVER ERROR:",str(e))

s.listen(2)
print("[SERVER STARTED] Waiting for a connection....")

def read_pos(str):
    str = str.split(",")
    return int(str[0]), int(str[1])


def make_pos(tup):
    return str(tup[0]) + "," + str(tup[1])

pos = [(100,100),(500,500)]

def threaded_client(conn, player):
    global currentPlayer
    conn.send(str.encode(make_pos(pos[player])))
    join = "Welcome to the server Player " + str(currentPlayer)
    conn.send(bytes(join,"utf-8"))
    conn.send(bytes("\nCurrent location is: " + str(pos[player]),"utf-8"))
    reply = ""
    while True:
        try:
            data = read_pos(conn.recv(2048).decode())
            pos[player] = data

            if not data:
                print("DISCONNECTED")
                break
            else:
                if player == 0:
                    reply = pos[1] #send position of other player
                else:
                    reply = pos[0] #send position of other player

                print("Received: ", data)
                print("Sending : ", reply)

            conn.sendall(str.encode(make_pos(reply)))
        except Exception as e:
            print(e)
            break

    print("Lost connection")
    conn.close()
    currentPlayer -= 1


while True:
    clientsocket, address = s.accept()
    print(f"Connection from {address} has been established.")

    start_new_thread(threaded_client, (clientsocket, currentPlayer))
    currentPlayer += 1