from rest_framework import viewsets


class ActionAPIViewSet(viewsets.GenericViewSet):
    def get_permissions(self):
        if hasattr(self, 'action') and hasattr(self, 'action_permission_classes'):
            if self.action in self.action_permission_classes.keys():
                return [permission() for permission in self.action_permission_classes[self.action]]

        return super(ActionAPIViewSet, self).get_permissions()

    def get_serializer_class(self):
        if hasattr(self, 'action') and hasattr(self, 'action_serializer_class'):
            if self.action in self.action_serializer_class.keys():
                return self.action_serializer_class[self.action]

        return super(ActionAPIViewSet, self).get_serializer_class()
