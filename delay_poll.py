"""Text notifier of Caltrain delays

Version: 0.1

Polls twitter for most recent 100 tweets using the search term: 'caltrain'.

Filters out tweets that:
  - Are not recent (within the last 30 minutes)
  - Are retweets
  - Do not contain words pertaining to delays

Currently outputs counts of recent tweets and recent delayed tweets,
and the relevant tweets to a log file that is time stamped.  Collecting
data until a proper threshold for alerts can be determined.

"""
import codecs
import json
import os
import re
import time
import urllib2

from datetime import date, timedelta, datetime

LOG_OUTPUT_DIR = 'tweet_logs/'
DELAYED_KEYWORDS = ['late', 'delayed', 'delay', 'delays']
THIRTY_MINUTES_IN_SEC = 30 * 60
FIFTEEN_MINUTES_IN_SEC = 15 * 60

def _doesTweetContainKeywords(tweet, keywords):
  """Checks the tweet against a list of keywords.
  """
  tweet_word_list = re.findall(r'\w+', tweet)
  return any([tweet_word for tweet_word in tweet_word_list
              if tweet_word in keywords])

def _isRetweet(tweet):
  """Checks if the first word in a tweet is 'rt', indicating a
  retweet.
  """
  tweet_word_list = re.findall(r'\w+', tweet)
  return tweet_word_list[0] == 'rt'

def _parseDate(tweet_date):
  """Parses a tweet time stamp into a datetime object.
  Date comes in as: "Tue, 15 May 2012 18:05:44 +0000"
  """
  tweet_date = tweet_date.split(' ')
  tweet_date = ' '.join(tweet_date[:-1])
  return datetime.strptime(tweet_date, '%a, %d %b %Y %H:%M:%S')

def _isTweetInValidTimeRange(tweet, time_range):
  """Given a tweet JSON object, check the creation
  date and see if it falls within a recency time window of X seconds.
  """
  DAYS_IN_SECONDS = 24 * 60 * 60
  current_date = datetime.utcnow()
  tweet_date = _parseDate(tweet['created_at'])
  date_diff = current_date - tweet_date
  time_difference = date_diff.days * DAYS_IN_SECONDS
  time_difference += date_diff.seconds
  return time_difference <= time_range

def _writeOutData(recent_tweet_counts, delayed_tweet_counts, delayed_tweets):
  """Write out the total tweet counts, delayed tweet counts, and actual
  delayed tweets.
  """
  log_file_name = LOG_OUTPUT_DIR + 'delays_%s' % (int(time.time()))
  print "Writing out to %s" % log_file_name
  f = codecs.open(log_file_name, "wb", "utf8")
  f.write("Total tweets count: %s\n" % recent_tweet_counts)
  f.write("Delay tweets count: %s\n" % delayed_tweet_counts)
  for tweet in delayed_tweets:
    f.write(tweet)
    f.write("\n")
  f.close()

def pollTwitterForDelays(last_poll_tweet_id = -1):
  """Polls twitter for search results, filters the results and writes it
  out to logs.
  """
  url = 'http://search.twitter.com/search.json?q=caltrain&rpp=100&page=1&result_type=recent'
  response = urllib2.urlopen(url).read()
  output = json.loads(response)
  twitter_results = output['results']

  # Check the most recent tweet id of the last time we polled twitter,
  # if the tweet id hasn't changed, don't bother parsing data.
  most_recent_tweet_id = output['max_id']
  if most_recent_tweet_id == last_poll_tweet_id:
    print "No updates."
    return most_recent_tweet_id

  recent_tweet_counts = 0
  delayed_tweet_counts = 0
  delayed_tweets = []

  for tweet in twitter_results:
    tweet_text = tweet['text'].lower()
    is_tweeted_recently = \
        _isTweetInValidTimeRange(tweet, THIRTY_MINUTES_IN_SEC)
    recent_tweet_counts += 1 if is_tweeted_recently else 0
    if _doesTweetContainKeywords(tweet_text, DELAYED_KEYWORDS):
      if not _isRetweet(tweet_text) and is_tweeted_recently:
        delayed_tweet_counts += 1
        delayed_tweets.append('%s AT %s' % (tweet_text,tweet['created_at']))

  if delayed_tweet_counts:
    print "Found some delay tweets."
    _writeOutData(recent_tweet_counts, delayed_tweet_counts, delayed_tweets)
  return most_recent_tweet_id


most_recent_tweet_id = -1
while(1):
  print "Polling twitter...."
  most_recent_tweet_id = pollTwitterForDelays(most_recent_tweet_id)
  print "...Done polling."
  time.sleep(FIFTEEN_MINUTES_IN_SEC)

