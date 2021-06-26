from django.contrib import admin


class MetaDataModelAdmin(admin.ModelAdmin):
    meta_data_fields = (
        'created_at',
        'updated_at',
        'deleted_at',
    )

    def get_readonly_fields(self, request, obj=None) -> list:
        readonly_fields = list(super().get_readonly_fields(request, obj))

        for meta_data_field in self.meta_data_fields:
            if meta_data_field not in readonly_fields:
                readonly_fields.append(meta_data_field)

        return readonly_fields


class MetaDataStackedInline(admin.StackedInline):
    meta_data_fields = (
        'created_at',
        'updated_at',
        'deleted_at',
    )

    def get_readonly_fields(self, request, obj=None) -> list:
        readonly_fields = list(super().get_readonly_fields(request, obj))

        for meta_data_field in self.meta_data_fields:
            if meta_data_field not in readonly_fields:
                readonly_fields.append(meta_data_field)

        return readonly_fields


class MetaDataTabularInline(admin.TabularInline):
    meta_data_fields = (
        'created_at',
        'updated_at',
        'deleted_at',
    )

    def get_readonly_fields(self, request, obj=None) -> list:
        readonly_fields = list(super().get_readonly_fields(request, obj))

        for meta_data_field in self.meta_data_fields:
            if meta_data_field not in readonly_fields:
                readonly_fields.append(meta_data_field)

        return readonly_fields
