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
import time
import urllib2
import deploy_settings

import filters

from twilio.rest import TwilioRestClient

FIFTEEN_MINUTES_IN_SEC = 15 * 60

TWILIO_CLIENT = TwilioRestClient(deploy_settings.ACCOUNT_SID,
                                 deploy_settings.AUTH_TOKEN)

def _writeOutData(valid_tweets, delayed_tweets):
  """Write out the total tweet counts, delayed tweet counts, and actual
  delayed tweets.
  """
  if not delayed_tweets:
    return
  log_file_name = 'delays_%s' % (int(time.time()))
  log_path = os.path.join(deploy_settings.LOG_OUTPUT_DIR, log_file_name)
  print "Writing out to %s" % log_file_name
  f = codecs.open(log_file_name, "wb", "utf8")
  f.write("Total tweets count: %s\n" % len(valid_tweets))
  f.write("Delay tweets count: %s\n" % len(delayed_tweets))
  for tweet in delayed_tweets:
    tweet_details = '%s AT %s' % (tweet['text'], tweet['created_at'])
    f.write(tweet_details)
    f.write("\n")
  f.close()

def _getNotification(valid_tweets, delayed_tweets):
  valid_tweet_count = len(valid_tweets)
  delayed_tweet_count = len(delayed_tweets)
  delayed_tweet_percentage = int(100 * delayed_tweet_count/valid_tweet_count)
  return ("There have been %s caltrain tweets in the past half hour,"
          " and %s%% are about delays.") % (valid_tweet_count,
                                            delayed_tweet_percentage)

def _shouldNotify(recent_tweet_counts, delayed_tweet_counts):
  delayed_tweet_percentage = int(100 * delayed_tweet_counts/recent_tweet_counts)
  return recent_tweet_counts >= deploy_settings.MINIMUM_NUM_TWEETS and \
         delayed_tweet_percentage >= deploy_settings.DELAY_PERCENTAGE

def _sendTextMessages(subscriptions, message):
  for number in subscriptions:
    sms_text = TWILIO_CLIENT.sms.messages.create(to=number,
        from_=deploy_settings.TWILIO_NUMBER, body=message)

def _hasNewUpdates(last_poll_tweet_id, output):
  return output['max_id'] != last_poll_tweet_id

def pollTwitterForDelays(last_poll_tweet_id=-1, subscriptions=[]):
  """Polls twitter for search results, filters the results and writes it
  out to logs.
  """
  try:
    response = urllib2.urlopen(deploy_settings.TWEET_QUERY).read()
    output = json.loads(response)
    twitter_results = output['results']
  except:
    return last_poll_tweet_id

  # Check the most recent tweet id of the last time we polled twitter,
  # if the tweet id hasn't changed, don't bother parsing data.
  if not _hasNewUpdates(last_poll_tweet_id, output):
    print "No updates."
    return last_poll_tweet_id

  should_send, message = _processTwitterResults(twitter_results)
  if should_send:
    print "Sending %s texts..." % len(subscriptions)
    _sendTextMessages(subscriptions, message)

  return most_recent_tweet_id

def _processTwitterResults(tweets):
  """Processes and filters tweets to determine if a text should be sent.
  """
  tweet_filters = [filters.filterSanitizeTweets,
                   filters.filterOldTweets,
                   filters.filterRetweets]

  for tweet_filter in tweet_filters:
    tweets = tweet_filter(tweets)

  delayed_tweets = filters.filterKeepDelayedTweets(tweets)

  _writeOutData(tweets, delayed_tweets)
  message = _getNotification(tweets, delayed_tweets)
  should_notify = _shouldNotify(len(tweets), len(delayed_tweets))
  return should_notify, message

def getSubscriptions():
  subscriptions = []
  f = open(deploy_settings.SUBSCRIPTIONS_FILENAME, "r")
  loaded_json = json.load(f)
  for entry in loaded_json['subscriptions']:
    subscriptions.append(entry['number'])
  return subscriptions

if __name__ == '__main__':
  most_recent_tweet_id = -1
  while(1):
    subscriptions = getSubscriptions()
    print "Polling twitter...."
    most_recent_tweet_id = pollTwitterForDelays(most_recent_tweet_id,
                                                subscriptions)
    print "...Done polling."
    time.sleep(FIFTEEN_MINUTES_IN_SEC)
