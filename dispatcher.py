import os
import re
import time
import socket
import SocketServer
import threading
import argparse

import helpers


def dispatch_tests(server, commit_hash):
    while True:
        print "Trying to dispatch to runners"
        for runner in server.runners:
            response = helpers.communicate(runner["host"],
                                           int(runner["port"]),
                                           "runtest:%s" % commid_id)
            if response == "OK":
                print "Adding hash %s" % commit_hash
                server.dispatched_commits[commit_hash] = runner
                if commit_hash in server.pending_commits:
                    server.pending_commits.remove(commit_hash)
                return
        time.sleep(2)


class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    runners = []
    dead = False
    dispatched_commits = {}
    pending_commits = []


class DispatcherHandler(SocketServer.BaseRequestHandler):
    command_re = re.compile(r"(\w+)(:.+)*")
    BUF_SIZE = 1024

    def handle(self):
        self.data = self.request.recv(self.BUF_SIZE).strip()
        command_groups = self.command_re.match(self.data)
        if not command_groups:
            self.request.sendall("Invalid command!")
            return
        command = command_groups.group(1)
        if command == "status":
            print "In status"
            self.request.sendall("OK")
        elif command == "register":
            print "Register"
            address = command_groups.group(2)
            host, port = re.findall(r":(\w*)", address)
            runner = {"host": host, "port":port}
            self.server.runners.append(runner)
            self.request.sendall("OK")
        elif command == "dispatch":
            print "Going to dispatch"
            commit_hash = command_groups.group(2)[1:]
            if not self.server.runners:
                self.request.sendall("No runners are registered")
            else:
                self.request.sendall("OK")
                dispatch_tests(self.server, commit_hash)
        elif command == "results":
            print "Got test results"
            results = command_groups.group(2)[1:]
            results = results.split(":")
            commit_hash = results[0]
            length_message = int(results[1])
            remaining_buffer = self.BUF_SIZE - (len(command) + len(commit_hash) + len(results[1]) + 3)
            if length_message > remaining_buffer:
                self.data += self.request.recv(length_message - remaining_buffer).strip()
            del self.server.dispatched_commits[commit_hash]
            if not os.path.exists("results"):
                os.makedirs("results")
            with open("results/%s" % commit_hash, "w") as f:
                data = self.data.split(":")[3:]
                data = "\n".join(data)
                f.write(data)
            self.request.sendall("OK")
        else:
            self.request.sendall("Invalid command")


def serve():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",
                        help="dispatcher's host, by default it uses localhost",
                        default="localhost",
                        action="store")
    parser.add_argument("--port",
                        help="dispatcher's port, by default it uses 8888",
                        default=8888,
                        action="store")
    args = parser.parse_args()

    server = ThreadingTCPServer((args.host, int(args.port)), DispatcherHandler)
    print 'serving on %s:%s' % (args.host, int(args.port))

    def runner_checker(server):
        def manage_commit_lists(runner):
            for commit, assigned_runner in server.dispatched_commits.iteritems():
                if assigned_runner == runner:
                    del server.dispatched_commits[commit]
                    server.pending_commits.append(commit)
                    break
            server.runners.remove(runner)

        while not server.dead:
            time.sleep(1)
            for runner in server.runners:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    response = helpers.communicate(runner["host"], int(runner["port"]), "ping")
                    if response != "pong":
                        print "removing runner %s" % runner
                        manage_commit_lists(runner)
                except socket.error as e:
                    manage_commit_lists(runner)

    def redistribute(server):
        while not server.dead:
            for commit in server.pending_commits:
                print "Running redistribute"
                print server.pending_commits
                dispatch_tests(server, commit)
                time.sleep(5)
            
    runner_heartbeat = threading.Thread(target=runner_checker, args=(server,))
    redistributor = threading.Thread(target=redistribute, args=(server,))
    try:
        runner_heartbeat.start()
        redistributor.start()
        server.serve_forever()
    except (KeyboardInterrupt, Exception):
        server.dead = True
        runner_heartbeat.join()
        redistributor.join()


if __name__ == "__main__":
    serve()