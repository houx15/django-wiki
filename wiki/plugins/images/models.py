from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import ugettext_lazy as _

import settings

from wiki.models.pluginbase import RevisionPlugin, RevisionPluginRevision

if not "sorl.thumbnail" in django_settings.INSTALLED_APPS:
    raise ImproperlyConfigured('wiki.plugins.images: needs sorl.thumbnail in INSTALLED_APPS')

def upload_path(instance, filename):
    from os import path
    # Has to match original extension filename
        
    upload_path = settings.IMAGE_PATH
    upload_path = upload_path.replace('%aid', str(instance.plugin.image.article.id))
    if settings.IMAGE_PATH_OBSCURIFY:
        import random, hashlib
        m=hashlib.md5(str(random.randint(0,100000000000000)))
        upload_path = path.join(upload_path, m.hexdigest())
    return path.join(upload_path, filename)

class Image(RevisionPlugin):
    
    # The plugin system is so awesome that the inheritor doesn't need to do
    # anything! :D
    
    def can_write(self, **kwargs):
        user = kwargs.get('user', None)
        if not settings.ANONYMOUS and (not user or user.is_anonymous()):
            return False
        return RevisionPlugin.can_write(self, **kwargs)

    class Meta:
        verbose_name = _(u'image')
        verbose_name_plural = _(u'images')
        app_label = settings.APP_LABEL
    
    def __unicode__(self):
        title = (_(u'Image: %s') % self.current_revision.imagerevision.get_filename()) if self.current_revision else _(u'Current revision not set!!')
        return unicode(title)

class ImageRevision(RevisionPluginRevision):
    
    image = models.ImageField(upload_to=upload_path,
                              max_length=2000, height_field='height',
                              width_field='width', blank=True, null=True)
    
    width = models.SmallIntegerField(default=0)
    height = models.SmallIntegerField(default=0)
    
    def get_filename(self):
        if self.image:
            return self.image.path.split('/')[-1]
    
    def get_size(self):
        """Used to retrieve the file size and not cause exceptions."""
        try:
            return self.image.size
        except ValueError:
            return None
    
    def inherit_predecessor(self, image):
        """
        Inherit certain properties from predecessor because it's very
        convenient. Remember to always call this method before 
        setting properties :)"""
        predecessor = image.current_revision.imagerevision
        self.plugin = predecessor.plugin
        try:
            self.image = predecessor.image
        except OSError:
            self.image = None
        self.width = predecessor.width
        self.height = predecessor.height
        self.deleted = predecessor.deleted
        self.locked = predecessor.locked

    class Meta:
        verbose_name = _(u'image revision')
        verbose_name_plural = _(u'image revisions')
        app_label = settings.APP_LABEL
        ordering = ('-created',)
