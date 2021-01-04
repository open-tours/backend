from django_cleanup.signals import cleanup_pre_delete
from easy_thumbnails.files import get_thumbnailer
from easy_thumbnails.signal_handlers import generate_aliases_global
from easy_thumbnails.signals import saved_file

# connect easy_thumbnails
saved_file.connect(generate_aliases_global)


# delete easy_thumbnails images on
def easy_thumbnails_delete(**kwargs):
    thumbnailer = get_thumbnailer(kwargs["file"])
    thumbnailer.delete_thumbnails()


cleanup_pre_delete.connect(easy_thumbnails_delete)
