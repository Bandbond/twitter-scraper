from requests_html import HTMLSession, HTML
from .exceptions import ProfileUnavailable
from .headers import get_headers


class Profile:
    """
        Parse twitter profile and split informations into class as attribute.

        Attributes:
            - name
            - username
            - birthday
            - location
            - biography
            - website
            - profile_photo
            - banner_photo
            - likes_count
            - tweets_count
            - followers_count
            - following_count
            - is_verified
            - is_private
            - user_id
    """

    count = 'li[class*="--{}"] span[data-count]'

    def __init__(self, username):
        self.session = HTMLSession()
        page = self.session.get(
            f"https://twitter.com/{username}", headers=get_headers(username)
        )
        self.username = username
        self.html = HTML(html=page.text, url="bunk", default_encoding="utf-8")
        if self.html.html == '{"message":"This user does not exist."}':
            raise ProfileUnavailable()

    def _count(self, name):
        try:
            return int(
                self.html.find(f'li[class*="--{name}"] span[data-count]')[0].attrs[
                    "data-count"
                ]
            )
        except Exception:
            pass

    @property
    def is_private(self):
        return len(self.html.find(".ProfileHeaderCard-badges .Icon--protected")) > 0

    @property
    def is_verified(self):
        return len(self.html.find(".ProfileHeaderCard-badges .Icon--verified")) > 0

    @property
    def location(self):
        return self.html.find(".ProfileHeaderCard-locationText")[0].text or None

    @property
    def birthday(self):
        return (
            self.tml.find(".ProfileHeaderCard-birthdateText")[0].text.replace(
                "Born ", ""
            )
            or None
        )

    @property
    def profile_photo(self):
        return self.html.find(".ProfileAvatar-image")[0].attrs["src"]

    @property
    def banner_photo(self):
        try:
            return self.html.find(".ProfileCanopy-headerBg img")[0].attrs["src"]
        except KeyError:
            pass

    @property
    def page_title(self):
        return self.html.find("title")[0].text

    @property
    def name(self):
        return self.page_title[: self.page_title.find("(")].strip()

    @property
    def user_id(self):
        return self.html.find(".ProfileNav")[0].attrs["data-user-id"]

    @property
    def biography(self):
        return self.html.find(".ProfileHeaderCard-bio")[0].text

    @property
    def website(self):
        return self.html.find(".ProfileHeaderCard-urlText")[0].text or None

    @property
    def tweets_count(self):
        return self._count("tweets")

    @property
    def following_count(self):
        return self._count("following")

    @property
    def followers_count(self):
        return self._count("followers")

    @property
    def likes_count(self):
        return self._count("favorites")

    def to_dict(self):
        return dict(
            name=self.name,
            username=self.username,
            birthday=self.birthday,
            biography=self.biography,
            location=self.location,
            website=self.website,
            profile_photo=self.profile_photo,
            banner_photo=self.banner_photo,
            likes_count=self.likes_count,
            tweets_count=self.tweets_count,
            followers_count=self.followers_count,
            following_count=self.following_count,
            is_verified=self.is_verified,
            is_private=self.is_private,
            user_id=self.user_id,
        )

    def __dir__(self):
        return [
            "name",
            "username",
            "birthday",
            "location",
            "biography",
            "website",
            "profile_photo",
            "banner_photo",
            "likes_count",
            "tweets_count",
            "followers_count",
            "following_count",
            "is_verified",
            "is_private",
            "user_id",
        ]

    def __repr__(self):
        return f"<profile {self.username}@twitter>"
