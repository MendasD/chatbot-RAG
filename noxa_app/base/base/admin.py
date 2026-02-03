from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

admin.site.register(CustomUser, UserAdmin)
admin.site.register(Topic)
admin.site.register(Tag)
admin.site.register(Publication)
admin.site.register(Collection)
admin.site.register(CollectionPublication)
admin.site.register(Message)
admin.site.register(Notification)
admin.site.register(Discussion)
admin.site.register(SearchHistory)
admin.site.register(SearchSuggestion)
admin.site.register(Specialization)
admin.site.register(Classes)
admin.site.register(Courses)
admin.site.register(Subjects)
