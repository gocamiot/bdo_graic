from django.contrib import admin
from apps.graic.models import Agent, Graic, Chat

# Register your models here.


class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'llm', 'online', )


admin.site.register(Agent, AgentAdmin)

admin.site.register(Graic)
admin.site.register(Chat)