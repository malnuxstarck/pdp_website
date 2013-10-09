# coding: utf-8
import os, time
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.dispatch import receiver


class UserGallery(models.Model):
    class Meta:
        verbose_name = "Galleries de l'utilisateur"
        verbose_name_plural = "Galleries de l'utilisateur"

    user = models.ForeignKey(User, verbose_name=('Membre'))
    gallery = models.ForeignKey('Gallery', verbose_name=('Gallerie'))
    MODE_CHOICES = (
        ('R', 'Lecture'),
        ('W', 'Ecriture')
    )
    mode = models.CharField(max_length=1,choices=MODE_CHOICES, default='R')

    def __unicode__(self):
        '''Textual form of an User Gallery'''
        return u'Gallerie "{0}" envoye par {1}'.format(self.gallery,
                                                        self.user)
    def is_write(self):
        return self.mode == 'W'
    
    def is_read(self):
        return self.mode == 'R'
    
    def get_images(self):
        return Image.objects.all()\
            .filter(gallery=self.gallery)\
            .order_by('update')

    def get_gallery(self, user):
        return Gallery.objects.all()\
            .filter(pk=self.gallery.pk)

class Image(models.Model):
    class Meta:
        verbose_name = "Image"
        verbose_name_plural = "Images"

    gallery = models.ForeignKey('Gallery', verbose_name=('Gallerie'))
    title = models.CharField('Titre', max_length=80)
    slug = models.SlugField(max_length=80)
    physical= models.ImageField(upload_to="gallery/%Y/%m/%d")
    legend = models.CharField('Légende', max_length=80)
    pubdate = models.DateTimeField('Date de création', auto_now_add=True)
    update = models.DateTimeField('Date de modification', null=True, blank=True)

    def __unicode__(self):
        '''Textual form of an Image'''
        return self.title
        
    def get_absolute_url(self):
        return '{0}/{1}/{2}/{3}/{4}'.format(IMAGES_URL,time.strptime(self.pubdate,'%Y'),time.strptime(self.pubdate,'%m'),time.strptime(self.pubdate,'%d'), self.physical)

    def get_extension(self):
        return os.path.splitext(self.nom_physique)[1]
    
# These two auto-delete files from filesystem when they are unneeded:
@receiver(models.signals.post_delete, sender=Image)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """Deletes image from filesystem
    when corresponding object is deleted.
    """
    if instance.physical:
        if os.path.isfile(instance.physical.path):
            os.remove(instance.physical.path)

class Gallery(models.Model):
    class Meta:
        verbose_name = "Gallerie"
        verbose_name_plural = "Galleries"

    title= models.CharField('Titre', max_length=80)
    subtitle = models.CharField('Sous titre', max_length=200)
    slug = models.SlugField(max_length=80)
    pubdate = models.DateTimeField('Date de création', auto_now_add=True)
    update = models.DateTimeField('Date de modification', null=True, blank=True)

    def __unicode__(self):
        '''Textual form of an Gallery'''
        return self.title
    
    def get_absolute_url(self):
        return '/gallerie/{0}/{1}'.format(self.pk, self.slug)

    def get_users(self):
        return UserGallery.objects.all()\
            .filter(gallery=self)

    def get_images(self):
        return Image.objects.all()\
            .filter(gallery=self)\
            .order_by('pubdate')

    def get_last_image(self):
        return Image.objects.all()\
            .filter(gallery=self)\
            .order_by('-pubdate')[0]
