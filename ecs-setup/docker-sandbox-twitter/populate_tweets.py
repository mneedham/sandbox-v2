#!/usr/bin/python 
import oauth2 as oauth
import urllib
import os
import json
import time
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import Cursor
import tweepy
import datetime
from neo4j.v1 import GraphDatabase, basic_auth
from retrying import retry
from Queue import Queue
from threading import Thread, Lock

connectionMutex = Lock()

# Twitter key/secret as a result of registering application
TWITTER_CONSUMER_KEY = os.environ["TWITTER_CONSUMER_KEY"]
TWITTER_CONSUMER_SECRET = os.environ["TWITTER_CONSUMER_SECRET"]

# Twitter key/secret as a result of registering application
TWITTER_USER_KEY = os.environ["TWITTER_USER_KEY"]
TWITTER_USER_SECRET = os.environ["TWITTER_USER_SECRET"]

TWITTER_SCREEN_NAME = None

# Neo4j configuration
NEO4J_HOST = os.environ["NEO4J_HOST"]
NEO4J_AUTH = os.environ["NEO4J_AUTH"]
NEO4J_SESSION = None
CONNECT_NEO4J_RETRIES = 1
#CONNECT_NEO4J_RETRIES = 10
CONNECT_NEO4J_WAIT_SECS = 3

def get_db_creds():
  global NEO4J_AUTH
  return {'user': (NEO4J_AUTH.split("/"))[0],
          'password': (NEO4J_AUTH.split("/"))[1]}

creds = get_db_creds()
driver = GraphDatabase.driver("bolt://%s" % (NEO4J_HOST), auth=basic_auth(creds['user'], creds['password']), encrypted=False)

@retry(stop_max_attempt_number=CONNECT_NEO4J_RETRIES, wait_fixed=(CONNECT_NEO4J_WAIT_SECS * 1000))
def get_db_session():
  global driver, NEO4J_SESSION
  connectionMutex.acquire()
  try:
    if not NEO4J_SESSION:
      NEO4J_SESSION = driver.session()
  finally:
    connectionMutex.release()
  return NEO4J_SESSION

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(time.mktime(obj.timetuple()))

        return json.JSONEncoder.default(self, obj)

class StdOutListener(StreamListener):
    """ A listener handles tweets that are received from the stream.
    This is a basic listener that just prints received tweets to stdout.
    """
    def on_status(self, status):
      statusQ.put(status)
      #print json.dumps(status._json, indent=2, cls=MyEncoder)

    def on_error(self, status_code):
      print "Error: %s" % status_code


# Queues to hold items retrieved from twitter, to be put into DB
statusQ = Queue()
friendQ = Queue()
followerQ = Queue()

##
## Workers to take tweets/friends off queues and put them into DB
##
def status_worker():
  while True:
    item = statusQ.get()
    process_status(item)
    statusQ.task_done()

def friend_worker():
  while True:
    item = friendQ.get()
    process_friend(item)
    friendQ.task_done()

def follower_worker():
  while True:
    item = followerQ.get()
    process_follower(item)
    followerQ.task_done()

##
## Main threads to retrieve data from twitter and put them in Queues
##
def status_get_worker():
  for status in Cursor(api.user_timeline).items(1000):
    statusQ.put(status)

def friend_get_worker():
  for friend in limit_handled(Cursor(api.friends).items()):
    friendQ.put(friend)

def follower_get_worker():
  for follower in limit_handled(Cursor(api.followers).items()):
    followerQ.put(follower)

##
## Threads to pull data off queues and put them into DB
##
statusT = Thread(target=status_worker)
statusT.daemon = True
statusT.start()

friendT = Thread(target=friend_worker)
friendT.daemon = True
friendT.start()

followerT = Thread(target=follower_worker)
followerT.daemon = True
followerT.start()

##
## Handlers to put data into DB
##
def process_status(status):
    query = """
    UNWIND {tweet} AS t

    WITH t
    ORDER BY t.id

    WITH t,
         t.entities AS e,
         t.user AS u,
         t.retweeted_status AS retweet

    MERGE (tweet:Tweet {id:t.id})
    SET tweet.id_str = t.id_str, 
        tweet.text = t.text,
        tweet.created_at = t.created_at,
        tweet.favorites = t.favorite_count,
        tweet.import_method = 'user'

    MERGE (user:User {screen_name:u.screen_name})
    SET user.name = u.name,
        user.location = u.location,
        user.followers = u.followers_count,
        user.following = u.friends_count,
        user.statuses = u.statusus_count,
        user.profile_image_url = u.profile_image_url

    MERGE (user)-[:POSTS]->(tweet)

    MERGE (source:Source {name:REPLACE(SPLIT(t.source, ">")[1], "</a", "")})
    MERGE (tweet)-[:USING]->(source)

    FOREACH (h IN e.hashtags |
      MERGE (tag:Hashtag {name:LOWER(h.text)})
      MERGE (tag)<-[:TAGS]-(tweet)
    )
    """

    session = get_db_session()
    results = session.run(query, parameters={"tweet": status._json})
    for record in results:
      print(record)

def add_main_user(user):
    global TWITTER_SCREEN_NAME
    query = """
    UNWIND {user} AS u
     WITH u

     MERGE (user:User:Me {screen_name:u.screen_name})
     SET user.name = u.name,
         user.location = u.location,
         user.followers = u.followers_count,
         user.following = u.friends_count,
         user.statuses = u.statusus_count,
         user.url = u.url,
         user.profile_image_url = u.profile_image_url
    """

    session = get_db_session()
    results = session.run(query, parameters={"user": user._json, "screen_name": TWITTER_SCREEN_NAME})
    for record in results:
      print(record)

def process_friend(friend):
    global TWITTER_SCREEN_NAME
    query = """
    UNWIND {user} AS u
     WITH u

     MERGE (user:User {screen_name:u.screen_name})
     SET user.name = u.name,
         user.location = u.location,
         user.followers = u.followers_count,
         user.following = u.friends_count,
         user.statuses = u.statusus_count,
         user.url = u.url,
         user.profile_image_url = u.profile_image_url

     MERGE (mainUser:User {screen_name:{screen_name}})
         MERGE (mainUser)-[:FOLLOWS]->(user)
    """

    session = get_db_session()
    results = session.run(query, parameters={"user": friend._json, "screen_name": TWITTER_SCREEN_NAME})
    for record in results:
      print(record)

def process_follower(follower):
    global TWITTER_SCREEN_NAME
    query = """
    UNWIND {user} AS u
     WITH u

     MERGE (user:User {screen_name:u.screen_name})
     SET user.name = u.name,
         user.location = u.location,
         user.followers = u.followers_count,
         user.following = u.followers_count,
         user.statuses = u.statusus_count,
         user.url = u.url,
         user.profile_image_url = u.profile_image_url

     MERGE (mainUser:User {screen_name:{screen_name}})
         MERGE (mainUser)-[:FOLLOWS]->(user)
    """

    session = get_db_session()
    results = session.run(query, parameters={"user": follower._json, "screen_name": TWITTER_SCREEN_NAME})
    for record in results:
      print(record)

# Sleeps if encountering a rate limit error
def limit_handled(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            print("Sleeping 15 mins")
            time.sleep(15 * 60)

#def make_api_request(url, method='GET', headers={}):
#  token = oauth.Token(key=TWITTER_USER_KEY, secret=TWITTER_USER_SECRET)
#  consumer = oauth.Consumer(key=TWITTER_CONSUMER_KEY, secret=TWITTER_CONSUMER_SECRET)
#  client = oauth.Client(consumer, token)
#  return client.request(url, method, headers=headers)

# Configuring tweepy
auth = OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_USER_KEY, TWITTER_USER_SECRET)
api = tweepy.API(auth)

user = api.verify_credentials()
TWITTER_SCREEN_NAME = user.screen_name
add_main_user(user)


#stream.filter(track=TRACK_TERMS, follow=[str(i) for i in FOLLOW_PEOPLE], async=False)

##
## Start threads to retrieve historical twitter data and put into queue
##
statusGT = Thread(target=status_get_worker)
statusGT.daemon = True
statusGT.start()

friendGT = Thread(target=friend_get_worker)
friendGT.daemon = True
friendGT.start()

followerGT = Thread(target=follower_get_worker)
followerGT.daemon = True
followerGT.start()

  
# Start streaming data
l = StdOutListener()
TRACK_TERMS = ['neo4j', 'API']
FOLLOW_PEOPLE = [95401]
stream = Stream(auth, l)
stream.userstream(async=True, track=TRACK_TERMS, replies='all')

while True:
  print("Status: %s" % statusQ.qsize())
  print("Friend: %s" % friendQ.qsize())
  print("Follower: %s" % followerQ.qsize())
  time.sleep(15)
