from rest_framework import serializers


class MetaDataModelSerializer(serializers.ModelSerializer):
    def get_extra_kwargs(self):
        read_only_fields = list(getattr(self.Meta, "read_only_fields", []))

        for meta_data_field in ("created_at", "updated_at", "deleted_at"):
            if meta_data_field not in read_only_fields:
                read_only_fields.append(meta_data_field)

        setattr(self.Meta, "read_only_fields", tuple(read_only_fields))

        return super().get_extra_kwargs()
