import boto3
import json
import os
import base64
import jwt
import time
import urllib2
import logging
import calendar
import random
import Queue
import threading


RUN_INSTANCE_URL = 'https://ppriuj7e7i.execute-api.us-east-1.amazonaws.com/dev/SandboxRunInstance'

def encodeJwt(payload, secret, algorithm='HS256'):
  return jwt.encode(payload, secret, algorithm=algorithm)

logging.getLogger().setLevel(logging.DEBUG)

queue = Queue.Queue()


class ThreadLaunch(threading.Thread):
  """Threaded Sandbox Launch"""
  def __init__(self, queue):
    threading.Thread.__init__(self)
    self.queue = queue
 
  def run(self):
    while True:
      #grabs jwt from queue
      jwttext = self.queue.get()

      data = {
        "usecase": "legis-graph"
      }
      
      try:
        req = urllib2.Request(url=RUN_INSTANCE_URL, data=json.dumps(data))
        req.add_header('Authorization', jwttext)
        req.add_header('Cache-Control', 'max-age=0')
        r = urllib2.urlopen(req)
        print(r.read())
      except urllib2.HTTPError, e:
        print('HTTPError = ' + str(e.code))
        print(e.read())
   
      #signals to queue job is done
      self.queue.task_done()

start = time.time()

def main():
  #spawn a pool of threads, and pass them queue instance 
  for i in range(5):
    t = ThreadLaunch(queue)
    t.setDaemon(True)
    t.start()

  for i in range(1000):
    iteration = i
    currentTime = int(calendar.timegm(time.gmtime()))
    rand = random.randint(1, 1000000)
  
    print('Beginning iteration: %s' % (rand))
  
    payload = {
      "email": "ryan@ryguy.com",
      "email_verified": True,
      "iss": "https://devrel-test.auth0.com/",
      "sub": "generated|%s|%s" % (rand, iteration),
      "aud": "CK4MU2kBWYkDXdWcKs5mj0GbgzEDfifL",
      "exp": currentTime + 60*60*24,
      "iat": currentTime 
    }
  
    jwttext= encodeJwt(payload, 'T8VM3OWmK4Xfq3sNCw-YeiBPssMbn-XwgTKVXhRahpqfhZeZnqVzj1_TtbCva0li')
    queue.put(jwttext)

  queue.join()

  print("Finished processing")

main()
print "Elapsed Time: %s" % (time.time() - start)
