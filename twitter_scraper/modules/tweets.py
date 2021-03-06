import re
from requests_html import HTMLSession, HTML
from datetime import datetime
from urllib.parse import quote
from lxml.etree import ParserError
from .exceptions import ProfileUnavailable
from .headers import get_headers


def get_tweets(query, pages=1, proxies=None):
    """Gets tweets for a given user, via the Twitter frontend API."""

    after_part = (
        f"include_available_features=1&include_entities=1&include_new_items_bar=true"
    )
    if query.startswith("#"):
        query = quote(query)
        url = f"https://twitter.com/i/search/timeline?f=tweets&vertical=default&q={query}&src=tyah&reset_error_state=false&"
    else:
        url = f"https://twitter.com/i/profiles/show/{query}/timeline/tweets?"
    url += after_part
    headers = get_headers(query)
    session = HTMLSession()

    def gen_tweets(pages):
        r = session.get(url, headers=headers, proxies=proxies)

        while pages > 0:
            try:
                html = HTML(
                    html=r.json()["items_html"], url="bunk", default_encoding="utf-8"
                )
            except KeyError:
                raise ProfileUnavailable()
            except ParserError:
                break

            comma = ","
            dot = "."
            tweets = []
            for tweet, profile in zip(
                html.find(".stream-item"), html.find(".js-profile-popup-actionable")
            ):
                # 10~11 html elements have `.stream-item` class and also their `data-item-type` is `tweet`
                # but their content doesn't look like a tweet's content
                try:
                    text = tweet.find(".tweet-text")[0].full_text
                except IndexError:  # issue #50
                    continue

                tweet_id = tweet.attrs["data-item-id"]

                tweet_url = profile.attrs["data-permalink-path"]

                username = profile.attrs["data-screen-name"]

                user_id = profile.attrs["data-user-id"]

                is_pinned = bool(tweet.find("div.pinned"))

                time = datetime.fromtimestamp(
                    int(tweet.find("._timestamp")[0].attrs["data-time-ms"]) / 1000.0
                )

                interactions = [x.text for x in tweet.find(".ProfileTweet-actionCount")]

                replies = int(
                    interactions[0].split(" ")[0].replace(comma, "").replace(dot, "")
                    or interactions[3]
                )

                retweets = int(
                    interactions[1].split(" ")[0].replace(comma, "").replace(dot, "")
                    or interactions[4]
                    or interactions[5]
                )

                likes = int(
                    interactions[2].split(" ")[0].replace(comma, "").replace(dot, "")
                    or interactions[6]
                    or interactions[7]
                )

                hashtags = [
                    hashtag_node.full_text
                    for hashtag_node in tweet.find(".twitter-hashtag")
                ]

                urls = [
                    url_node.attrs["data-expanded-url"]
                    for url_node in (
                        tweet.find("a.twitter-timeline-link:not(.u-hidden)")
                        + tweet.find(
                            "[class='js-tweet-text-container'] a[data-expanded-url]"
                        )
                    )
                ]
                urls = list(set(urls))  # delete duplicated elements

                photos = [
                    photo_node.attrs["data-image-url"]
                    for photo_node in tweet.find(".AdaptiveMedia-photoContainer")
                ]

                is_retweet = (
                    True
                    if tweet.find(".js-stream-tweet")[0].attrs.get(
                        "data-retweet-id", None
                    )
                    else False
                )

                videos = []
                video_nodes = tweet.find(".PlayableMedia-player")
                for node in video_nodes:
                    styles = node.attrs["style"].split()
                    for style in styles:
                        if style.startswith("background"):
                            tmp = style.split("/")[-1]
                            video_id = (
                                tmp[: tmp.index(".jpg")]
                                if ".jpg" in tmp
                                else tmp[: tmp.index(".png")]
                                if ".png" in tmp
                                else None
                            )
                            videos.append({"id": video_id})

                tweets.append(
                    {
                        "tweetId": tweet_id,
                        "tweetUrl": tweet_url,
                        "username": username,
                        "userId": user_id,
                        "isRetweet": is_retweet,
                        "isPinned": is_pinned,
                        "time": time,
                        "text": text,
                        "replies": replies,
                        "retweets": retweets,
                        "likes": likes,
                        "entries": {
                            "hashtags": hashtags,
                            "urls": urls,
                            "photos": photos,
                            "videos": videos,
                        },
                    }
                )

            last_tweet = html.find(".stream-item")[-1].attrs["data-item-id"]

            for tweet in tweets:
                tweet["text"] = re.sub(r"(\S)http", r"\g<1> http", tweet["text"], 1)
                tweet["text"] = re.sub(
                    r"(\S)pic\.twitter", r"\g<1> pic.twitter", tweet["text"], 1
                )
                yield tweet

            r = session.get(url, params={"max_position": last_tweet}, headers=headers)
            pages += -1

    yield from gen_tweets(pages)
