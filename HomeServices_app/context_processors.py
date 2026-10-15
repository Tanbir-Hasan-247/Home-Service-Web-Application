from .models import Notification, users, workers

def notification_context(request):
    """
    Context processor that supplies unread notifications, the latest notifications,
    and the profile picture URL for the currently logged in user across all templates.
    """
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        latest_notifs = Notification.objects.filter(user=request.user).order_by('-created_at')[:8]

        profile_pic_url = None
        if request.user.is_staff:
            worker = workers.objects.filter(admin=request.user).first()
            if worker and worker.get_profile_pic_url:
                profile_pic_url = worker.get_profile_pic_url

        if not profile_pic_url:
            cust = users.objects.filter(admin=request.user).first()
            if cust and cust.get_profile_pic_url:
                profile_pic_url = cust.get_profile_pic_url

        return {
            'unread_notifications_count': unread_count,
            'user_notifications': latest_notifs,
            'current_profile_pic_url': profile_pic_url,
        }
    return {
        'unread_notifications_count': 0,
        'user_notifications': [],
        'current_profile_pic_url': None,
    }
