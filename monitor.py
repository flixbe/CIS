import os
import sys
import time
import subprocess
import re
import argparse
import socket
import SocketServer

import helpers

def poll():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dispatcher-server",
                        help="dispatcher host:port, by default it uses localhost:8888",
                        default="localhost:8888",
                        action="store")
    parser.add_argument("repository",
                        metavar="REPOSITORY",
                        type=str,
                        help="path to the repository this will observe")
    args = parser.parse_args()
    dispatcher_host, dispatcher_port = args.dispatcher_server.split(":")

    while True:
        try:
            subprocess.check_output(["./scripts/update.sh", args.repository])
        except subprocess.CalledProcessError as e:
            raise Exception ("Can't update and check repository. Reason: %s" % e.output)

        if os.path.isfile(".commit_hash"):
            try:
                response = helpers.communicate(dispatcher_host,
                                               int(dispatcher_port),
                                               "status")
            except socket.error as e:
                raise Exception("Can't communicate with dispatcher server: %s" % e)

            if response == "OK":
                commit = ""
                with open(".commit_hash", "r") as f:
                    commit = f.readline()
                response = helpers.communicate(dispatcher_host,
                                               int(dispatcher_port),
                                               "dispatch:%s" % commit)
                if response != "OK":
                    raise Exception("Could not dispatch the test: %s" % response)
                print "Dispatched!"
            else:
                raise Exception("Could not dispatch the test: %s" % response)
        time.sleep(5)


if __name__ == "__main__":
    poll()