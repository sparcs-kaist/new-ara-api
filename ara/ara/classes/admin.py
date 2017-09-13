from django.contrib import admin


class MetaDataModelAdmin(admin.ModelAdmin):
    readonly_fields = (
        'created_at',
        'updated_at',
        'deleted_at',
    )
