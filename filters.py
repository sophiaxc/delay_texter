import re
from datetime import date, timedelta, datetime

THIRTY_MINUTES_IN_SEC = 30 * 60
DELAYED_KEYWORDS = ['late', 'delayed', 'delay', 'delays']

def filterSanitizeTweets(tweets):
  for tweet in tweets:
    tweet['text'] = tweet['text'].lower()
  return tweets

def filterOldTweets(tweets):
  def _parseDate(tweet_date):
    """Parses a tweet time stamp into a datetime object.
    Date comes in as: "Tue, 15 May 2012 18:05:44 +0000"
    """
    tweet_date = tweet_date.split(' ')
    tweet_date = ' '.join(tweet_date[:-1])
    return datetime.strptime(tweet_date, '%a, %d %b %Y %H:%M:%S')

  def _isTweetRecent(tweet, time_range):
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

  return [tweet for tweet in tweets if _isTweetRecent(tweet,
    THIRTY_MINUTES_IN_SEC)]

def filterRetweets(tweets):
  """Checks if the first word in a tweet is 'rt', indicating a
  retweet.
  """
  def _isRetweet(tweet):
    tweet_text = tweet['text']
    tweet_word_list = re.findall(r'\w+', tweet_text)
    return tweet_word_list[0] == 'rt'

  return [tweet for tweet in tweets if not _isRetweet(tweet)]

def filterKeepDelayedTweets(tweets):
  def _doesTweetContainKeywords(tweet, keywords):
    """Checks the tweet against a list of keywords.
    """
    tweet_text = tweet['text']
    tweet_word_list = re.findall(r'\w+', tweet_text)
    return any([tweet_word for tweet_word in tweet_word_list
                if tweet_word in keywords])

  return [tweet for tweet in tweets
      if _doesTweetContainKeywords(tweet, DELAYED_KEYWORDS)]
