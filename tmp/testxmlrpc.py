import xmlrpclib

hmDaemon = None
hmDaemonURL = "http://127.0.0.1:7000"

arguments = []
arguments.append("fhuici")
arguments.append("password")
arguments.append("fhuici@dummy.com")
arguments.append("computer9")
arguments.append("status")
requestName = "power"

hmDaemon = xmlrpclib.Server(hmDaemonURL, None, None, 0, 1)
print hmDaemon.processRequest(requestName, arguments)

