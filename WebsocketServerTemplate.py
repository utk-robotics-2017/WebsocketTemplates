#Imports
import sys
import random
import signal
import time

import tornado.ioloop
import tornado.websocket

#We're going to store the clients
clients = set()
clientId = 0

#Port for the websocket to be hosted on
port = 9002
pin = random.randint(0, 99999)

def log(wsId, message):
    print("{}\tClient {:2d}\t{}".format(time.strftime("%H:%M:%S", time.localtime()), wsId, message))

class Server(tornado.websocket.WebSocketHandler):
    #Accept cross origin requests
    def check_origin(self, origin):
        return True

    #Client connected
    def open(self):
        global clients, clientId

        self.id = clientId
        clientId += 1
        clients.add(self)

        self.verified = False

        log(self.id, "connected with ip: " + self.request.remote_ip)

    #Client sent a message
    def on_message(self, message):
        if not self.verified:
            #Try to read the message as a pin number
            try:
                clientPin = int(message)
            except ValueError:
                self.write_message("Invalid Pin")
                log(self.id, "entered an invalid pin: " + message)
                return

            #Check pin
            if clientPin == pin:
                self.verified = True
                self.write_message("Verified")
                log(self.id, "entered correct pin")
            else:
                self.write_message("WrongPin")
                log(self.id, "entered wrong pin")

        else:
            #If message starts with the command, run the code
            cmd = "PostMessage"
            if message[:len(cmd)] == cmd:
                #Additional data will be in "message[len(cmd):]"
                #Messages can be sent to this client using "self.write_message(str)"

                #Messages can be sent to all clients by iterating over "clients" and calling "write_message(str)" on each one
                for client in clients:
                    client.write_message("PrintMessage" + "Client %d: %s" % (self.id, message[len(cmd):]))
                return

    #Client disconnected
    def on_close(self):
        clients.remove(self)
        log(self.id, "disconnected")

#Catch ctrl+c
def sigInt_handler(signum, frame):
    print(" Closing Server")

    #Close each client's connection
    while clients:
        client = next(iter(clients))
        client.close(reason="Server Closing")
        client.on_close()

    #Close the websocket port
    tornado.ioloop.IOLoop.current().stop()
    print("Server is closed")
    sys.exit(0)

if __name__ == "__main__":
    app = tornado.web.Application([(r"/", Server)])
    app.listen(port)
    signal.signal(signal.SIGINT, sigInt_handler)
    print("Pin: {:05d}".format(pin))
    tornado.ioloop.IOLoop.current().start()
