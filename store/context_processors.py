from .models import Category, SiteSetting


def global_context(request):
    return {
        'site_settings': SiteSetting.load(),
        'global_categories': Category.objects.all(),
    }