# coding: utf-8

from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

from .models import Post, Topic

from pdp.utils.templatetags.emarkdown import emarkdown


class LastPostsFeedRSS(Feed):
    title = u'Posts sur Progdupeupl'
    link = '/forums/'
    description = u'Les derniers messages parus sur le forum de Progdupeupl.'

    def items(self):
        return Post.objects\
            .order_by('-pubdate')[:5]

    def item_title(self, item):
        return u'{}, message #{}'.format(item.topic.title, item.pk)

    def item_description(self, item):
        # TODO: Use cached Markdown when implemented
        return emarkdown(item.text)

    def item_author_name(self, item):
        return item.author.username

    def item_author_link(self, item):
        return item.author.get_absolute_url()

    def item_link(self, item):
        return item.get_absolute_url()


class LastPostsFeedATOM(LastPostsFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastPostsFeedRSS.description


class LastTopicsFeedRSS(Feed):
    title = u'Sujets sur Progdupeupl'
    link = '/forums/'
    description = u'Les derniers sujets créés sur le forum de Progdupeupl.'

    def items(self):
        return Topic.objects\
            .order_by('-pubdate')[:5]

    def item_title(self, item):
        return u'{} dans {}'.format(item.title, item.forum.title)

    def item_description(self, item):
        return item.subtitle

    def item_author_name(self, item):
        return item.author.username

    def item_author_link(self, item):
        return item.author.get_absolute_url()

    def item_link(self, item):
        return item.get_absolute_url()


class LastTopicsFeedATOM(LastTopicsFeedRSS):
    feed_type = Atom1Feed
    subtitle = LastTopicsFeedRSS.description