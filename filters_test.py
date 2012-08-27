import random
import unittest
import filters

class TestDelayPoll(unittest.TestCase):
  def testFilterSanitizeTweets(self):
    tweets = [{'text' : 'FOO'}, {'text' : 'BAR'}]
    tweets = filters.filterSanitizeTweets(tweets)
    self.assertEqual(tweets,
        [{'text' : 'foo'}, {'text' : 'bar'}])

  def testFilterRetweets(self):
    tweets = [{'text' : 'rt foo'}, {'text' : 'bar'}]
    tweets = filters.filterRetweets(tweets)
    self.assertEqual(tweets, [{'text' : 'bar'}])

  def testFilterKeepDelayedTweets(self):
    tweets = [{'text' : 'foo delay'}, {'text' : 'bar'}]
    tweets = filters.filterKeepDelayedTweets(tweets)
    self.assertEqual(tweets, [{'text' : 'foo delay'}])

if __name__ == '__main__':
    unittest.main()
