from typing import Any, Generic, Type, TypeVar

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Model

from ara.domain.ara_entity import AraEntity, AraEntityCreateInput

T = TypeVar("T", bound=Model)


class AraDjangoInfra(Generic[T]):
    def __init__(self, model: Type[T]) -> None:
        self.model = model

    def get_by_id(self, id: Any, *, is_select_for_update: bool = False) -> T:
        """
        Generic function for simple get by id queries.

        Args:
            id (Any):
                Not sure of the id type. It could be hash Id or int.
                TODO(hyuk): check for the all models.
            is_select_for_update (bool):
                Set True if get queryset for update purpose. Defaults to False.

        """
        if is_select_for_update:
            return self.model.objects.select_for_update().get(id=id)
        return self.model.objects.get(id=id)

    def get_filtered_objects(
        self,
        *,
        columns: list[str] | None = None,
        conditions: dict[str, Any],
        is_select_for_update: bool = False,
    ) -> list[T | dict[str, Any]]:
        """
        Generic function for simple queries.
        Should not be used for complex & specific purpose queries.

        Args:
            columns (List[str] | None):
                List of column names to fetch. Get all columns if None. Default None.
            conditions (Dict[str, Any]):
                Dictionary of field names and their corresponding values to filter by.
            is_select_for_update (bool):
                Set True if get queryset for update purpose. Defaults to False.

        Returns:
            List[T | Dict[str, Any]]:
                A list containing the matching object,
                with only the specified columns if `columns` is not None.

        Example:
            # Get all rows with id=1 and only fetch 'id' and 'name' fields
            query1 = get_filtered_queryset(
                columns=['id', 'name'],
                conditions={'id': 1}
            )

            # Get the first 10 rows with rating>=4.0 and order by created_at descending
            query2 = get_filtered_queryset(
                columns=['id', 'name', 'rating', 'created_at'],
                conditions={'rating__gte': 4.0}
            ).order_by('-created_at').limit(10)

        Raises:
            ValidationError: If conditions parameter is empty or invalid.
        """
        if not conditions:
            raise ValidationError("conditions parameter is required")

        try:
            if is_select_for_update:
                queryset = self.model.objects.select_for_update()
            else:
                queryset = self.model.objects

            queryset = queryset.filter(**conditions)

            if columns is not None:
                queryset = queryset.values(*columns)

            return list(queryset)

        except ValidationError:
            raise ValidationError("invalid conditions parameter")

    def create_manual(self, **kwargs) -> T:
        return self.model.objects.create(**kwargs)

    def update_or_create(self, **kwargs) -> tuple[T, bool]:
        return self.model.objects.update_or_create(**kwargs)

    def get_by(self, **kwargs) -> T | None:
        """Returns repository model instance if exists.

        :param kwargs: keyword arguments of fields
        :raises MultipleObjectsXxx: when multiple rows exist
        :return: None or model instance if exists.
        """
        try:
            return self.model.objects.get(**kwargs)
        except ObjectDoesNotExist:
            return None

    def _to_model(self, entity: AraEntity) -> Model:
        raise NotImplementedError()

    @staticmethod
    def convert_model_to_entity(model: T) -> AraEntity:
        raise NotImplementedError()

    def _convert_entity_to_model(self, entity: AraEntity) -> Model:
        raise NotImplementedError()

    def _convert_create_input_to_model(self, create_input: AraEntityCreateInput) -> T:
        raise NotImplementedError()

    def bulk_update_entity(self, entities: list[AraEntity]):
        if len(entities) == 0:
            return

        model_instances = [self._convert_entity_to_model(entity) for entity in entities]

        unique_updated_fields = list(
            {field for entity in entities for field in entity.updated_fields}
        )
        if len(unique_updated_fields) == 0:
            return

        self.model.objects.bulk_update(model_instances, unique_updated_fields)

    def bulk_update(self, instances: list[T], fields: list[str]):
        return self.model.objects.bulk_update(instances, fields)

    def bulk_create(self, inputs: list[AraEntityCreateInput]) -> list[AraEntity]:
        instances = [self._convert_create_input_to_model(input) for input in inputs]
        created_instances = self.model.objects.bulk_create(instances)
        entities = [
            self.convert_model_to_entity(created_instance)
            for created_instance in created_instances
        ]
        return entities

    def save_entity(self, entity: AraEntity):
        model = self._convert_entity_to_model(entity)
        model.save()
        return entity
