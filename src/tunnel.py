from time import sleep

from sshtunnel import SSHTunnelForwarder
import requests

remote_user = 'pi'
remote_host = '192.168.0.32'
remote_port = 22
local_host = '127.0.0.1'
local_port = 5000

server = SSHTunnelForwarder(
   (remote_host, remote_port),
   ssh_username=remote_user,
   ssh_password='password',
   remote_bind_address=(local_host, local_port),
   local_bind_address=(local_host, local_port),
)

server.start()

for i in range(0, 10):
   r = requests.get('http://127.0.0.1:5000').content
   sleep(0.2)
   print(r)

server.stop()