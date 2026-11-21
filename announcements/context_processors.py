
from .models import Announcement


def latest_announcements(request):
    return {
        'latest_announcements': Announcement.objects.filter(is_active=True)[:3]
    }