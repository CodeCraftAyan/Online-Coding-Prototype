from .models import SiteSetting

def site_settings(request):
    try:
        setting = SiteSetting.objects.first()

        if not setting:
            setting = SiteSetting.objects.create()

        return {
            "show_video": setting.show_video,
            "video_triggered_at": setting.video_triggered_at.timestamp() if setting.video_triggered_at else 0
        }

    except Exception as e:
        # 🔥 NEVER break admin or any page
        return {
            "show_video": False,
            "video_triggered_at": 0
        }