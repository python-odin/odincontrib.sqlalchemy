import inspect

import sys

import odin
from sqlalchemy import types as sql_types, Column, Table

from odin import registration
from odin import fields
from odin.mapping import FieldResolverBase, mapping_factory


class SqlAlchemyFieldResolver(FieldResolverBase):
    """
    Field resolver for SQLAlchemy declarative Models
    """
    def get_field_dict(self):
        return {col.name: col for col in self.obj.__table__.columns}


def register_model_base(base):
    """
    Register a model base class with the Odin field resolver.

    :param base: Base class generated by :py:meth:`sqlalchemy.ext.declarative.declarative_base`

    """
    assert hasattr(base, 'metadata'), "base does not appear to be a valid SQL Alchemy table base."

    registration.register_field_resolver(SqlAlchemyFieldResolver, base)


BASE_ATTR_MAP = {

}

SQL_TYPE_MAP = [
    (sql_types.String, fields.StringField, {}),
    (sql_types.Integer, fields.IntegerField, {}),
    (sql_types.Numeric, fields.FloatField, {}),
    (sql_types.Boolean, fields.BooleanField, {}),
    (sql_types.Date, fields.DateField, {}),
    (sql_types.Time, fields.TimeField, {}),
    (sql_types.DateTime, fields.DateTimeField, {}),
    (sql_types.Enum, fields.StringField, {}),
]


def field_factory(column):
    # type: (Column) -> fields.BaseField
    """
    Generate an equivalent resource field from a SQLAlchemy column definition.
    """
    for sql_type, field, attrs in SQL_TYPE_MAP:
        if isinstance(column.type, sql_type):
            field_kwargs = {
                'null': column.nullable,
                'key': column.primary_key,
            }
            return field(**field_kwargs)


class ModelResource(odin.Resource):
    """
    Resource with some extra model specific fields.
    """
    def to_model(self):
        """
        Map this resource to corresponding model.
        """
        mapping = registration.get_mapping(self, self.__model__)
        return mapping.apply(self)


def table_resource_factory(table, module=None, base_resource=ModelResource, resource_mixins=None, exclude_fields=None,
                           generate_mappings=False, return_mappings=False, additional_fields=None,
                           resource_type_name=None, reverse_exclude_fields=None):
    """

    :param table:
    :param module:
    :param base_resource:
    :param resource_mixins:
    :param exclude_fields:
    :param generate_mappings:
    :param return_mappings:
    :param additional_fields:
    :param resource_type_name:
    :param reverse_exclude_fields:
    :return:
    """
    model = None
    if not isinstance(table, Table):
        if hasattr(table, '__table__') and isinstance(table.__table__, Table):
            model = table
            table = table.__table__
        else:
            raise TypeError("table is not a Table instance")
    else:
        if generate_mappings or return_mappings:
            raise ValueError("Mappings can only be generated for declarative tables.")

    # Determine the calling module
    if module is None:
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0]).__name__
    elif not isinstance(module, str):
        module = module.__name__

    # Set defaults
    resource_mixins = resource_mixins or []
    bases = tuple(resource_mixins + [base_resource])
    exclude_fields = exclude_fields or []
    generate_mappings = generate_mappings or return_mappings  # Need to be generated if expected to be returned
    resource_type_name = resource_type_name or str(table.name)
    reverse_exclude_fields = reverse_exclude_fields or []

    attrs = {
        '__module__': module,
        '__table__': table,
        '__model__': model,
    }

    # Map columns to fields
    for col in table.columns:
        if col.name in exclude_fields:
            continue

        field = field_factory(col)
        if field:
            attrs[col.name] = field

    # Add any additional fields.
    if additional_fields:
        attrs.update(additional_fields)

    # Create
    resource_type = type(resource_type_name, bases, attrs)

    # Generate mappings
    if generate_mappings:
        forward_mapping, reverse_mapping = mapping_factory(
            model, resource_type, reverse_exclude_fields=reverse_exclude_fields
        )
        if return_mappings:
            return resource_type, forward_mapping, reverse_mapping

    return resource_type
