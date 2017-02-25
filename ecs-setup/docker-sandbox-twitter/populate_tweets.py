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
import sys
import traceback
import logging

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
#CONNECT_NEO4J_RETRIES = 1
CONNECT_NEO4J_RETRIES = 10
CONNECT_NEO4J_WAIT_SECS = 3

def get_db_creds():
  global NEO4J_AUTH
  return {'user': (NEO4J_AUTH.split("/"))[0],
          'password': (NEO4J_AUTH.split("/"))[1]}

creds = get_db_creds()
driver = GraphDatabase.driver("bolt://%s" % (NEO4J_HOST), auth=basic_auth(creds['user'], creds['password']), encrypted=False)

@retry(stop_max_attempt_number=CONNECT_NEO4J_RETRIES, wait_fixed=(CONNECT_NEO4J_WAIT_SECS * 1000))
def get_db_session():
  return driver.session()

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

    def on_error(self, status_code):
      print "Error: %s" % status_code


# Queues to hold items retrieved from twitter, to be put into DB
statusQ = Queue()
friendQ = Queue()
followerQ = Queue()
followerIDQ = Queue()
friendIDQ = Queue()
fofGetQ = Queue()
fofQ = Queue()

##
## Workers to take tweets/friends off queues and put them into DB
##
def status_worker():
  while True:
    item = statusQ.get()
    try:
      process_status(item)
    except Exception as err:
      traceback.print_exc(file=sys.stdout) 
    finally:
      statusQ.task_done()

def friend_worker():
  global TWITTER_SCREEN_NAME
  while True:
    item = friendQ.get()
    try:
      process_friend(item, TWITTER_SCREEN_NAME)
    except Exception as err:
      traceback.print_exc(file=sys.stdout) 
    finally:
      friendQ.task_done()

# process batch of 100 IDs from Queue
@retry(stop_max_attempt_number=10, wait_fixed=(15 * 1000))
def follower_id_worker():
  while True:
    lookup_ids = followerIDQ.get()
    try:
      for user in api.lookup_users(lookup_ids):
        followerQ.put(user)
    except Exception as err:
      traceback.print_exc(file=sys.stdout) 
    finally:
      followerIDQ.task_done()

# process batch of 100 IDs from Queue
@retry(stop_max_attempt_number=10, wait_fixed=(15 * 1000))
def friend_id_worker():
  while True:
    lookup_ids = friendIDQ.get()
    try:
      for user in api.lookup_users(lookup_ids):
        friendQ.put(user)
    except Exception as err:
      traceback.print_exc(file=sys.stdout) 
    finally:
      friendIDQ.task_done()

def follower_worker():
  global TWITTER_SCREEN_NAME
  while True:
    item = followerQ.get()
    try:
      process_follower(item, TWITTER_SCREEN_NAME)
    except Exception as err:
      traceback.print_exc(file=sys.stdout) 
    finally:
      followerQ.task_done()

def index_worker():
  with get_db_session() as session:
    session.run("CREATE CONSTRAINT ON (t:Tweet) ASSERT t.id IS UNIQUE;").consume()
    session.run("CREATE CONSTRAINT ON (u:User) ASSERT u.screen_name IS UNIQUE;").consume()
    session.run("CREATE CONSTRAINT ON (h:Hashtag) ASSERT h.name IS UNIQUE;").consume()
    session.run("CREATE CONSTRAINT ON (l:Link) ASSERT l.url IS UNIQUE;").consume()
    session.run("CREATE CONSTRAINT ON (s:Source) ASSERT s.name IS UNIQUE;").consume()

##
## Main threads to retrieve data from twitter and put them in Queues
##
@retry(stop_max_attempt_number=10, wait_fixed=(15 * 1000))
def status_get_worker():
  for status in limit_handled(Cursor(api.user_timeline).items(5000)):
    statusQ.put(status)

@retry(stop_max_attempt_number=10, wait_fixed=(15 * 1000))
def mentions_get_worker():
  for status in limit_handled(Cursor(api.mentions_timeline).items(5000)):
    statusQ.put(status)

@retry(stop_max_attempt_number=10, wait_fixed=(15 * 1000))
def friend_get_worker():
  friend_ids = []
  for friend in limit_handled(Cursor(api.friends_ids).items()):
    friend_ids.append(friend)
  start_point = 0
  lookup_ids = friend_ids[ start_point : (start_point + 100) ]
  while len(lookup_ids) > 0:
    friendIDQ.put(lookup_ids)
    start_point = start_point + 100
    lookup_ids = friend_ids[ start_point : (start_point + 100) ]

@retry(stop_max_attempt_number=1, wait_fixed=(15 * 1000))
def follower_get_worker():
  follower_ids = []
  for follower in limit_handled(Cursor(api.followers_ids).items()):
    follower_ids.append(follower)
  start_point = 0
  lookup_ids = follower_ids[ start_point : (start_point + 100) ]
  while len(lookup_ids) > 0:
    followerIDQ.put(lookup_ids)
    start_point = start_point + 100
    lookup_ids = follower_ids[ start_point : (start_point + 100) ]

##
## Threads to pull data off queues and put them into DB
##
statusT = Thread(target=status_worker)
statusT.daemon = True
statusT.start()

friendIDT = Thread(target=friend_id_worker)
friendIDT.daemon = True
friendIDT.start()

friendT = Thread(target=friend_worker)
friendT.daemon = True
friendT.start()

followerIDT = Thread(target=follower_id_worker)
followerIDT.daemon = True
followerIDT.start()

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

    FOREACH (u IN e.urls |
      MERGE (url:Link {url:u.expanded_url})
      MERGE (tweet)-[:CONTAINS]->(url)
    )

    FOREACH (m IN e.user_mentions |
      MERGE (mentioned:User {screen_name:m.screen_name})
      ON CREATE SET mentioned.name = m.name
      MERGE (tweet)-[:MENTIONS]->(mentioned)
    )

    FOREACH (r IN [r IN [t.in_reply_to_status_id] WHERE r IS NOT NULL] |
      MERGE (reply_tweet:Tweet {id:r})
      MERGE (tweet)-[:REPLY_TO]->(reply_tweet)
    )

    FOREACH (retweet_id IN [x IN [retweet.id] WHERE x IS NOT NULL] |
      MERGE (retweet_tweet:Tweet {id:retweet_id})
      MERGE (tweet)-[:RETWEETS]->(retweet_tweet)
    )

    """

    with get_db_session() as session:
      session.run(query, parameters={"tweet": status._json}).consume()

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

    with get_db_session() as session:
      session.run(query, parameters={"user":user._json, "screen_name":TWITTER_SCREEN_NAME}).consume()

def process_friend(friend, friendOfScreenName):
    global TWITTER_SCREEN_NAME
    query = """
    UNWIND {user} AS u
     WITH u

     MERGE (user:User {screen_name:u.screen_name})
     SET user.name = u.name,
         user.location = u.location,
         user.followers = u.followers_count,
         user.following = u.friends_count,
         user.statuses = u.statuses_count,
         user.url = u.url,
         user.profile_image_url = u.profile_image_url

     MERGE (mainUser:User {screen_name:{screen_name}})
         MERGE (mainUser)-[:FOLLOWS]->(user)
    """

    with get_db_session() as session:
      session.run(query, parameters={"user": friend._json, "screen_name": friendOfScreenName}).consume()

def process_follower(follower, followerOfScreenName):
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
         MERGE (mainUser)<-[:FOLLOWS]-(user)
    """

    with get_db_session() as session:
      session.run(query, parameters={"user": follower._json, "screen_name": followerOfScreenName}).consume()

# Sleeps if encountering a rate limit error
def limit_handled(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            print("Sleeping 15 mins")
            time.sleep(15 * 60)


# Configuring tweepy
auth = OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_USER_KEY, TWITTER_USER_SECRET)
api = tweepy.API(auth)

user = api.verify_credentials()
TWITTER_SCREEN_NAME = user.screen_name
add_main_user(user)

indexGT = Thread(target=index_worker)
indexGT.daemon = True
indexGT.start()
indexGT.join()

#stream.filter(track=TRACK_TERMS, follow=[str(i) for i in FOLLOW_PEOPLE], async=False)

##
## Start threads to retrieve historical twitter data and put into queue
##
statusGT = Thread(target=status_get_worker)
statusGT.daemon = True
statusGT.start()

mentionsGT = Thread(target=mentions_get_worker)
mentionsGT.daemon = True
mentionsGT.start()

friendGT = Thread(target=friend_get_worker)
friendGT.daemon = True
friendGT.start()

followerGT = Thread(target=follower_get_worker)
followerGT.daemon = True
followerGT.start()

  
# Start streaming data
l = StdOutListener()
TRACK_TERMS = ['neo4j']
stream = Stream(auth, l)
stream.userstream(async=True, track=TRACK_TERMS, replies='all')

while True:
  time.sleep(15)
  print("Status: %s" % statusQ.qsize())
  print("Friend ID: %s" % friendIDQ.qsize())
  print("Follower ID: %s" % followerIDQ.qsize())
  print("") 
  print("Friend: %s" % friendQ.qsize())
  print("Follower: %s" % followerQ.qsize())
  time.sleep(105)
