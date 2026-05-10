from django.contrib import admin
from .models import users, workers, Country, State, City, ServiceCatogarys, ServiceRequests, Response, Feedback

# This customizes how the 'workers' model appears in the admin panel
@admin.register(workers)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'designation', 'city', 'acc_activation', 'avalability_status')
    list_filter = ('acc_activation', 'avalability_status', 'designation', 'city')
    search_fields = ('admin__first_name', 'admin__last_name', 'admin__email', 'designation')
    list_editable = ('acc_activation', 'avalability_status')

    def get_full_name(self, obj):
        return obj.admin.get_full_name()
    get_full_name.short_description = 'Worker Name'

# This customizes how the 'users' (customers) model appears
@admin.register(users)
class UserAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'contact_number', 'get_email')
    search_fields = ('admin__first_name', 'admin__last_name', 'admin__email')

    def get_full_name(self, obj):
        return obj.admin.get_full_name()
    get_full_name.short_description = 'Customer Name'
    
    def get_email(self, obj):
        return obj.admin.email
    get_email.short_description = 'Email'

# This customizes the 'ServiceRequests' model view
@admin.register(ServiceRequests)
class ServiceRequestsAdmin(admin.ModelAdmin):
    list_display = ('service', 'user', 'city', 'status', 'dateofrequest')
    list_filter = ('status', 'service', 'city')
    search_fields = ('user__admin__first_name', 'service__Name')

# This customizes the 'Response' model view
@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('requests', 'assigned_worker', 'Date', 'status')
    list_filter = ('status',)
    search_fields = ('requests__service__Name', 'assigned_worker__admin__first_name')

# This customizes the 'Feedback' model view
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('User', 'Employ', 'Rating', 'Date')
    list_filter = ('Rating',)
    search_fields = ('User__username', 'Employ__admin__first_name')

# Registering other models with default settings
admin.site.register(Country)
admin.site.register(State)
admin.site.register(City)
admin.site.register(ServiceCatogarys)