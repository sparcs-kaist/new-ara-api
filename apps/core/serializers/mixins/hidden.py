import typing

from rest_framework import serializers


class HiddenSerializerMixin(metaclass=serializers.SerializerMetaclass):
    CAN_OVERRIDE_REASONS = []

    def get_is_mine(self, obj) -> bool:
        return self.context["request"].user == obj.created_by

    def get_is_hidden(self, obj) -> bool:
        return not self.visible_verdict(obj)

    def get_why_hidden(self, obj) -> typing.List[str]:
        _, _, reasons = self.hidden_info(obj)
        return [reason.value for reason in reasons]

    def get_can_override_hidden(self, obj) -> typing.Optional[bool]:
        hidden, can_override, _ = self.hidden_info(obj)
        if not hidden:
            return
        return can_override

    def visible_verdict(self, obj):
        hidden, can_override, _ = self.hidden_info(obj)
        return not hidden or (can_override and self.requested_override_hidden)

    @property
    def requested_override_hidden(self):
        return (
            "override_hidden" in self.context
            and self.context["override_hidden"] is True
        )

    def hidden_info(self, obj) -> typing.Tuple[bool, bool, typing.List]:
        user = self.context["request"].user
        reasons = obj.hidden_reasons(user)
        cannot_override_reasons = [
            reason for reason in reasons if reason not in self.CAN_OVERRIDE_REASONS
        ]
        can_override = len(cannot_override_reasons) == 0
        return len(reasons) > 0, can_override, reasons


class HiddenSerializerFieldMixin(metaclass=serializers.SerializerMetaclass):
    is_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    why_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    can_override_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
