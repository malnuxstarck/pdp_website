# coding: utf-8
#
# This file is part of Progdupeupl.
#
# Progdupeupl is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Progdupeupl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Progdupeupl. If not, see <http://www.gnu.org/licenses/>.

"""Models for forum app."""

from datetime import datetime
from math import ceil

from django.core.urlresolvers import reverse
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify

from pdp.utils import get_current_user
from pdp.utils.cache import template_cache_delete


class Category(models.Model):

    """A category, containing forums."""

    class Meta:
        verbose_name = u'Catégorie'
        verbose_name_plural = u'Catégories'

    title = models.CharField(
        u'Titre',
        max_length=80
    )

    position = models.IntegerField(
        u'Position',
        null=True, blank=True
    )

    slug = models.SlugField(max_length=80)

    def __str__(self):
        """Textual representation of a category.

        Returns:
            string

        """
        return self.title

    def get_absolute_url(self):
        """Get URL to view the category.

        Returns:
            string

        """
        return reverse('pdp.forum.views.cat_details', args=[
            self.slug
        ])

    def get_forums(self):
        """Retreive all forums owned by the category.

        Returns:
            QuerySet on Forum objects

        """
        return Forum.objects.all()\
            .filter(category=self)\
            .order_by('position_in_category')


class Forum(models.Model):

    """A forum, containing topics."""

    class Meta:
        verbose_name = u'Forum'
        verbose_name_plural = u'Forums'

    title = models.CharField(
        u'Titre',
        max_length=80
    )

    subtitle = models.CharField(
        u'Sous-titre',
        max_length=200,
        blank=True
    )

    category = models.ForeignKey(
        Category,
        verbose_name=u'Catégorie'
    )

    position_in_category = models.IntegerField(
        u'Position dans la catégorie',
        null=True, blank=True
    )

    slug = models.SlugField(max_length=80)

    def __str__(self):
        """Textual representation of a forum.

        Returns:
            string

        """
        return self.title

    def get_absolute_url(self):
        """Get URL to view the forum.

        Returns:
            string

        """
        return u'/forums/{0}/{1}/'.format(
            self.category.slug,
            self.slug,
        )

    def get_topic_count(self):
        """Get the number of threads in the forum.

        Returns:
            QuerySet on integer

        """
        return Topic.objects.all().filter(forum__pk=self.pk).count()

    def get_post_count(self):
        """Get the number of posts in the forum.

        Returns:
            QuerySet on integer

        """
        return Post.objects.all().filter(topic__forum=self).count()

    def get_last_message(self):
        """Get the last message on the forum, if any.

        Returns:
            Post object or None

        """
        return Post.objects.all()\
            .filter(topic__forum__pk=self.pk)\
            .order_by('-pubdate').first()

    def is_read(self):
        """Check if this forum was read by current user.

        For convenience for new users, we only mark the forum as unread if the
        user has not read messages posted after the datetime he joined.

        Returns:
            boolean

        """
        user = get_current_user()

        # Though the never_read func will return false for old topics, better
        # filter these old topics here so our topic set is way more compact
        # than a Topic.objects.all() on which we call never_read in for loop.
        topics = Topic.objects.all() \
            .filter(forum=self) \
            .filter(last_message__pubdate__gt=user.date_joined)

        for t in topics:
            if never_read(t):
                return False

        return True


class Topic(models.Model):

    """A thread, containing posts."""

    class Meta:
        verbose_name = u'Sujet'
        verbose_name_plural = u'Sujets'

    title = models.CharField(
        u'Titre',
        max_length=80
    )

    subtitle = models.CharField(
        u'Sous-titre',
        max_length=200,
        blank=True
    )

    forum = models.ForeignKey(
        Forum,
        verbose_name=u'Forum'
    )

    author = models.ForeignKey(
        User,
        verbose_name=u'Auteur',
        related_name='topics'
    )

    last_message = models.ForeignKey(
        'Post',
        null=True,
        related_name='last_message',
        verbose_name=u'Dernier message'
    )

    pubdate = models.DateTimeField(
        u'Date de création',
        auto_now_add=True
    )

    is_solved = models.BooleanField(
        u'Est résolu',
        default=False
    )

    is_locked = models.BooleanField(
        u'Est verrouillé',
        default=False
    )

    is_sticky = models.BooleanField(
        u'Est en post-it',
        default=False
    )

    def __str__(self):
        """Textual representation of a topic.

        Returns:
            string

        """
        return self.title

    def get_absolute_url(self):
        """Get URL to view the topic.

        Returns:
            string

        """
        return reverse('pdp.forum.views.topic', args=[
            self.pk,
            slugify(self.title)
        ])

    def get_post_count(self):
        """Return the number of posts in the topic.

        Returns:
            QuerySet on integer

        """
        return Post.objects.all().filter(topic__pk=self.pk).count()

    def get_answer_count(self):
        """Return the number of answers in the topic.

        Returns:
            Integer

        """
        return self.get_post_count() - 1

    def get_last_answer(self):
        """Gets the last answer in the thread, if any.

        Returns:
            Post object or None

        """
        last_post = Post.objects.all() \
            .filter(topic__pk=self.pk) \
            .order_by('-pubdate') \
            .first()

        # We do not want first post to be considered as an answer.
        if last_post and last_post == self.first_post():
            return None
        else:
            return last_post

    def first_post(self):
        """Return the first post of a topic, written by topic's author.

        Returns:
            Post object or None

        """
        try:
            return Post.objects\
                .filter(topic=self)\
                .order_by('pubdate')[0]
        except IndexError:
            return None

    def last_read_post(self):
        """Return the last post the user has read.

        Returns:
            Post object or None

        """
        user = get_current_user()

        if user is not None:
            # Logged-in user, so he may have a TopicRead instance
            try:
                return TopicRead.objects\
                    .select_related()\
                    .filter(topic=self, user=user)\
                    .latest('post__pubdate').post
            except TopicRead.DoesNotExist:
                return self.first_post()

        # Anonymous user, we return the last post since the first one is
        # available using the topic title link so it would have been redundant.
        resp = self.get_last_answer()
        return resp if resp is not None else self.first_post()

    def is_followed(self, user=None):
        """Check if the topic is currently followed by the user.

        This method uses the TopicFollowed objects.

        Returns:
            boolean

        """
        if user is None:
            user = get_current_user()

        try:
            TopicFollowed.objects.get(topic=self, user=user)
        except TopicFollowed.DoesNotExist:
            return False
        return True

    def antispam(self, user=None):
        """Check if the user is allowed to post in a topic.

        This method uses the SPAM_LIMIT_SECONDS value. If user shouldn't be
        able to post, then antispam is activated and this method returns True.
        Otherwise time elapsed between user's last post and now is enough, and
        the method will return False.

        Returns:
            boolean

        """
        if user is None:
            user = get_current_user()

        last_user_posts = Post.objects\
            .filter(topic=self)\
            .filter(author=user)\
            .order_by('-pubdate')

        if last_user_posts and last_user_posts[0] == self.get_last_answer():
            last_user_post = last_user_posts[0]
            t = timezone.now() - last_user_post.pubdate
            if t.total_seconds() < settings.SPAM_LIMIT_SECONDS:
                return True

        return False

    def never_read(self):
        return never_read(self)


class Post(models.Model):

    """A forum post written by an user."""

    topic = models.ForeignKey(
        Topic,
        verbose_name=u'Sujet'
    )

    author = models.ForeignKey(
        User,
        verbose_name=u'Auteur',
        related_name='posts'
    )

    text = models.TextField(u'Texte')

    pubdate = models.DateTimeField(
        u'Date de publication',
        auto_now_add=True
    )

    update = models.DateTimeField(
        u'Date d\'édition',
        null=True, blank=True
    )

    position_in_topic = models.IntegerField(
        u'Position dans le sujet'
    )

    is_useful = models.BooleanField(
        u'Est utile',
        default=False
    )

    is_moderated = models.BooleanField(
        u'Est modéré',
        default=False
    )
    moderation_time = models.DateTimeField(
        u'Date d\'édition',
        default=datetime.today()
    )
    moderation_text = models.TextField(
        u'Explication de modération',
        default='',
        blank=True
    )
    moderated_by = models.ForeignKey(
        User,
        verbose_name=u'Modérateur',
        null=True
    )

    def __str__(self):
        """Textual representation of a post.

        Returns:
            string

        """
        return u'<Post pour "{0}", #{1}>'.format(self.topic, self.pk)

    def get_absolute_url(self):
        """Get URL to view the post.

        Returns:
            string

        """
        page = int(ceil(
            float(self.position_in_topic) / settings.POSTS_PER_PAGE
        ))

        return '{0}?page={1}#p{2}'\
            .format(self.topic.get_absolute_url(), page, self.pk)

    def is_moderated_visible(self):
        """Should the text of a moderated message be visible?

        We decide that moderated messages remain un-visible for a certain
        amount of time, in order to allow the discussion to cool down.

        Returns:
            boolean

        """
        visible_at = self.moderation_time + settings.MODERATED_REVEAL_DELAY

        return datetime.now() > visible_at


class TopicRead(models.Model):

    """Small model which keeps track of the user viewing topics.

    It remembers the topic he looked and what was the last Post at this time.

    """

    class Meta:
        verbose_name = u'Sujet lu'
        verbose_name_plural = u'Sujets lus'

    topic = models.ForeignKey(Topic)
    post = models.ForeignKey(Post)
    user = models.ForeignKey(User, related_name='topics_read')

    def __str__(self):
        """Textual representation of a TopicRead object.

        Returns:
            string

        """
        return u'<Sujet "{0}" lu par {1}, #{2}>'.format(
            self.topic, self.user, self.post.pk)


class TopicFollowed(models.Model):

    """Small model which keeps track of the topics followed by an user.

    If an instance of this model is stored with an user and topic instance,
    that means that this user is following this topic.

    """

    class Meta:
        verbose_name = u'Sujet suivi'
        verbose_name_plural = u'Sujets suivis'

    topic = models.ForeignKey(Topic)
    user = models.ForeignKey(User, related_name='topics_followed')

    def __str__(self):
        """Textual reprensentation of a TopicFollowed object.

        Returns:
            string

        """
        return u'<Sujet "{0}" suivi par {1}>'.format(
            self.topic.title, self.user.username)


def get_last_topics():
    """Get the 5 very last topics.

    Returns:
        List (or QuerySet?) of Topic objects

    """
    return Topic.objects.all() \
        .order_by('-last_message__pubdate')[:10]


def never_read(topic, user=None):
    """Check if a topic has been read by an user since it last post was added.

    For convenience for new users, topics older than the user's joined
    datetime will be marked as read.

    If no user is provided, this will use the current session user.

    Args:
        topic: Topic to check if has been read
        user: User who may have read the topic

    Returns:
        boolean

    """
    if user is None:
        user = get_current_user()

    if topic.last_message.pubdate < user.date_joined:
        return False

    return TopicRead.objects\
        .filter(post_id=topic.last_message_id, topic=topic, user=user)\
        .count() == 0


def mark_read(topic, user=None):
    """Mark a topic as read for an user.

    If no user is provided, this will use the current session user.

    Args:
        topic: Topic to be marked as read
        user: User who as read the topic

    """

    if user is None:
        user = get_current_user()

    # We update existing TopicRead or create a new one
    req = TopicRead.objects.filter(topic=topic, user=user)
    if req:
        t = req[0]
    else:
        t = TopicRead(topic=topic, user=user)

    t.post = topic.last_message
    t.save()

    # If the topic is followed, we want to update some cached values
    if topic.is_followed(user):
        template_cache_delete('topbar-topics', [user.username])
        if topic in get_last_topics():
            template_cache_delete('home-forums', [user.username])


def follow(topic, user=None):
    """Toggle following of a topic for an user.

    If no user is provided, this will use the current session user.

    Args:
        topic: Topic to be (un)marked as followed
        user: User to toogle the following state for

    Returns:
        New status as boolean : is the user following the topic now?

    """

    # TODO: create follow, unfollow and toggle_follow functions instead of this
    # big one.

    if user is None:
        user = get_current_user()

    ret = None
    try:
        existing = TopicFollowed.objects.get(
            topic=topic, user=user
        )
    except TopicFollowed.DoesNotExist:
        existing = None

    if not existing:
        # Make the user follow the topic
        t = TopicFollowed(
            topic=topic,
            user=user
        )
        t.save()
        ret = True
    else:
        # If user is already following the topic, we make him don't anymore
        existing.delete()
        ret = False
    return ret
