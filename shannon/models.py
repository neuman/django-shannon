from django.db import models
import uuid
import os
import logging

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.exception import S3ResponseError
import urllib2

from django.conf import settings
from django.dispatch import receiver
import youtube_dl

import glob
from PIL import Image

MEDIA_TYPE_CHOICES = (
    ('V', 'Video'),
    ('A', 'Audio'),
    ('I', 'Image'),
    ('D', 'Document'),
    ('U', 'Unknown')
)

MEDIUM_CHOICES = (
    ('TXT', 'Text'),
    ('VID', 'Video'),
    ('AUD', 'Audio'),
    ('IMG', 'Image'),
    ('MUL', 'Multimedia'),
    ('DAT', 'Data'),
)

EXTENSIONS = {
    "TXT":['txt','md'],
    "VID":['avi', 'm4v', 'mov', 'mp4', 'mpeg', 'mpg', 'vob', 'wmv'],
    "AUD":['aac', 'aiff', 'm4a', 'mp3', 'wav', 'wma'],
    "IMG":['gif', 'jpeg', 'jpg', 'png'],
    "MUL":[],
    "DAT":['csv','json'],
}

CONVERSION_STATUS = (
    ('U', 'Unconverted'),
    ('Q', 'In Conversion Queue'),
    ('I', 'In Progress'),
    ('C', 'Converted'),
    ('E', 'Error'),
)

VIDEO_EXTENSIONS = [
    'avi',
    'm4v',
    'mov',
    'mp4',
    'mpeg',
    'mpg',
    'vob',
    'wmv',
    'mkv',
]
AUDIO_EXTENSIONS = [
    'aac',
    'aiff',
    'm4a',
    'mp3',
    'wav',
    'wma',
]
IMAGE_EXTENSIONS = [
    'gif',
    'jpeg',
    'jpg',
    'png',
]
DOCUMENT_EXTENSIONS = [
    'doc',
    'docx',
    'mus',
    'pdf',
    'ppt',
    'pptx',
    'rtf',
    'sib',
    'txt',
    'xls',
    'xlsx',
]

ALL_EXTS = VIDEO_EXTENSIONS + AUDIO_EXTENSIONS + IMAGE_EXTENSIONS +\
    DOCUMENT_EXTENSIONS

def get_unique_file_name(filename):
    blocks = filename.split('.')
    ext = blocks[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return filename

def get_file_path(instance, filename):
    blocks = filename.split('.')
    ext = blocks[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    instance.title = blocks[0]
    return os.path.join('uploads/', get_unique_file_name(filename))

def get_file_extension(filename, extension=None):
    #return string_in.__getslice__(string_in.__len__()-3, string_in.__len__()).lower()
    i = filename.rfind(".")
    return filename.__getslice__(i+1, filename.__len__()).lower()

def get_file_name(filename, extension=None):
    #return string_in.__getslice__(string_in.__len__()-3, string_in.__len__()).lower()
    i = filename.rfind(".")
    return filename.__getslice__(0, i).lower()

def upload_to_s3(filename):
    conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket = conn.create_bucket(settings.AWS_STORAGE_BUCKET_NAME)
    new_extension = get_file_extension(filename)
    k = Key(bucket)
    k.name = str(uuid.uuid4())+"."+new_extension
    k.set_contents_from_filename(filename)
    return k

def create_media_from_s3_key(s3_key):
    m = Media()
    m.set_internal_file_s3_key(s3_key)
    m.assumed_extension = get_file_extension(s3_key)
    m.medium = get_medium(m.assumed_extension)
    #m.title = m.get_file_name()
    return m

def get_file_extension(string_in):
    #return string_in.__getslice__(string_in.__len__()-3, string_in.__len__()).lower()
    i = string_in.rfind(".")
    return string_in.__getslice__(i+1, string_in.__len__()).lower()

def get_medium(extension_in):
    for medium in EXTENSIONS:
        for extension in EXTENSIONS[medium]:
            if extension == extension_in:
                return medium


class Media(models.Model):
    original_url = models.CharField(max_length=500, null=True, blank=True)
    original_file_url = models.TextField(default='', null=True, blank=True)
    internal_file_url = models.TextField(default='/', null=True, blank=True)
    normalized_file_url = models.TextField(default='', null=True, blank=True)
    original_thumbnail_file_url = models.TextField(default='', null=True, blank=True)
    original_file = models.FileField(upload_to=get_file_path, null=True, blank=True)
    internal_file = models.FileField(upload_to='', null=True, blank=True)
    title = models.CharField(max_length=500, null=True, blank=True)
    assumed_extension = models.CharField(max_length=50, default="")
    medium = models.CharField(max_length=3, choices=MEDIUM_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=1, choices=CONVERSION_STATUS, null=True, blank=True)
    blurb = models.TextField(default='', null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True

    def __str__(self):
        if (self.title != "") and (self.title != None):
            return self.title
        else:
            return "Couldn't Find Media Name"

    def get_status(self):
        return self.status

    def get_file_url(self):
        try:
            return self.internal_file.url
        except ValueError:
            return None

    def refresh_original_file(self):
        #stream directly to s3 without saving to local filesystem
        request = urllib2.Request(self.original_url)
        response = urllib2.urlopen(request)
        conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.create_bucket(settings.AWS_STORAGE_BUCKET_NAME)
        k = Key(bucket)
        k.name = str(uuid.uuid4())+"."+self.assumed_extension
        k.set_contents_from_string(response.read(), {'Content-Type' : response.info().gettype()})
        k.set_canned_acl('public-read')
        self.set_original_file_s3_key(k.name)
        self.save()

    def refresh_original_file_from_youtube(self):
        y = youtube_dl.YoutubeDL()
        i = y.extract_info(self.original_url)
        new_filename = y.prepare_filename(i)
        k = upload_to_s3(new_filename)
        k.set_canned_acl('public-read')
        self.set_original_file_s3_key(k.name)
        self.save()
        os.remove(new_filename)

    def refresh_original_image_convert_to_jpg(self):
        #download the file to local
        hexy = uuid.uuid4()
        temp_filename = str(hexy)+"."+self.assumed_extension
        new_filename = str(hexy)+"."+"jpg"

        temp_file = urllib2.urlopen(self.original_url)
        data = temp_file.read()
        with open(temp_filename, "wb") as code:
            code.write(data)
        #convert it to jpg
        for infile in glob.glob(temp_filename):
            file, ext = os.path.splitext(infile)
            im = Image.open(infile).convert("RGB")
            im.save(file + ".jpg")

        k = upload_to_s3(new_filename)
        k.set_canned_acl('public-read')
        self.set_internal_file_s3_key(k.name)
        self.save()
        os.remove(new_filename)

    size = 256, 256
    def refresh_original_image_as_thumbnail(self):
        #download the file to local
        hexy = uuid.uuid4()
        temp_filename = str(hexy)+"."+self.assumed_extension
        new_filename = str(hexy)+"."+"jpg"

        temp_file = urllib2.urlopen(self.original_url)
        data = temp_file.read()
        with open(temp_filename, "wb") as code:
            code.write(data)
        #convert it to jpg
        for infile in glob.glob(temp_filename):
            file, ext = os.path.splitext(infile)
            im = Image.open(infile).convert("RGB")

            im.thumbnail(self.size, Image.ANTIALIAS)
            im.save(file + ".jpg")

        k = upload_to_s3(new_filename)
        k.set_canned_acl('public-read')
        self.set_internal_file_s3_key(k.name)
        self.save()
        os.remove(new_filename)

    def set_original_file_s3_key(self, key):
        self.internal_file.name = key
        self.save()

    def set_internal_file_s3_key(self, key):
        self.internal_file.name = key
        self.save()

    def get_original_s3_key(self):
        return self.original_file.name.lstrip('/')

    def get_internal_s3_key(self):
        return self.internal_file.name.lstrip('/')

    def get_content(self):
        return self.original_file._get_file().read()
        #avoid pulling from s3 constantly
        if not self.noodles.__contains__('content'):
            self.noodles.__setitem__('content',self.original_file._get_file().read())
        return self.noodles['content']

    def get_content_data_values(self):
        content = self.get_content()
        content = json.loads(content)

        try:
            value_name = content['y_name']
        except Exception as e:
            value_name = 'value'
        output = [point[value_name] for point in content['data']]
        return output

    def get_content_data_labels(self):
        content = self.get_content()
        content = json.loads(content)
        try:
            label_name = content['x_name']
        except Exception as e:
            label_name = 'label'
        output = [point[label_name] for point in content['data']]
        return output

    def get_file_name(self):
        return self.name

    def get_file_extension(self):
        #return string_in.__getslice__(string_in.__len__()-3, string_in.__len__()).lower()
        i = self.get_file_url().rfind(".")
        return string_in.__getslice__(i+1, string_in.__len__()).lower()

    def get_medium(self):
        for medium in cm.EXTENSIONS:
            for extension in cm.EXTENSIONS[medium]:
                if extension == self.get_file_extension():
                    return medium

    def is_file_nonzero(self):
        if self.file.size > 0:
                    return True
        return False

    def get_post(self):
        return get_media_post(self)

    #for celery
    @property
    def noext(self):
        return os.path.splitext(self.s3_key)[0]

    @property
    def basename(self):
        return os.path.splitext(os.path.basename(self.s3_key))[0]

    @property
    def fileext(self):
        return os.path.splitext(self.s3_key)[1][1:]

    def reprocess(self):
        self.update(set__status='U', set__s3_key=self.original_s3_key)
        from ddesk.tasks import get_info
        get_info.apply_async(args=[str(self.id)])

    def set_complete(self):
        self.status = 'C'
        self.save()
        #get applications
        for application in self.get_applications():
            app_media = application.get_medias_proxy()
            if app_media.count() == app_media.filter(status='C').count():
                application.update(set__in_progress=False)
                # Immediate notifications have been suppressed until now since
                # media was being converted, so update all reviewers that
                # have immediate update frequency
                application.notify_reviewers()


@receiver(models.signals.pre_delete, sender=Media)
def remove_file_from_s3(sender, instance, using, **kwargs):
    instance.internal_file.delete(save=False)

def check_key_exists(key):
    conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket = conn.create_bucket(settings.AWS_STORAGE_BUCKET_NAME)
    objs = list(bucket.objects.filter(Prefix=key))
    if len(objs) > 0 and objs[0].key == key:
        return True
    else:
        return False

def delete_key(rel_path, bucket_name):
    conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket = conn.create_bucket(bucket_name)
    for key in bucket.list(prefix=rel_path):
        key.delete()

def check_key_exists(rel_path, bucket_name):
    conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket = conn.create_bucket(bucket_name)
    exists = False
    try:
        # A hackish way of testing if the rel_path is a folder vs a file
        is_dir = rel_path[-1] == '/'
        if is_dir:
            keyresult = bucket.get_all_keys(prefix=rel_path)
            if len(keyresult) > 0:
                exists = True
            else:
                exists = False
        else:
            key = Key(bucket, rel_path)
            exists = key.exists()
    except S3ResponseError:
        log.exception("Trouble checking existence of S3 key '%s'", rel_path)
        return False
    if rel_path[0] == '/':
        raise
    return exists


#detect media type at savetime
from django.db.models.signals import post_save

@receiver(post_save, sender=Media)
def media_post_save_handler(sender, **kwargs):
    pass