import pytest
from datetime import datetime

from sqlalchemy import Column, String, Text, Table, Integer, DateTime, MetaData
from sqlalchemy.ext.declarative import declarative_base

from odin import StringField, Resource, Mapping

from odincontrib.sqlalchemy import field_factory, table_resource_factory, register_model_base, ModelResource

Base = declarative_base()
register_model_base(Base)


@pytest.mark.parametrize('column, expected, expected_attrs', (
    (Column(String), StringField, {}),
    (Column(String(256)), StringField, {}),
    (Column(Text), StringField, {}),
))
def test_field_factory(column, expected, expected_attrs):
    actual = field_factory(column)
    assert isinstance(actual, expected)


test_table = Table(
    'ModelATest', MetaData(),
    Column(Integer, name='id', primary_key=True),
    Column(String(256), name='name'),
    Column(DateTime(), name='created'),
)


class ModelTest(Base):
    __tablename__ = 'ModelBTest'

    id = Column(Integer, primary_key=True)
    name = Column(String(256))
    created = Column(DateTime)


class TestTableResourceFactory(object):
    def test_from_table(self):
        actual = table_resource_factory(test_table)

        assert issubclass(actual, ModelResource)
        assert actual.__name__ == 'ModelATest'

    def test_from_declarative(self):
        actual = table_resource_factory(ModelTest)

        assert issubclass(actual, ModelResource)
        assert actual.__name__ == 'ModelBTest'

    def test_get_mappings(self):
        actual, actual_from, actual_to = table_resource_factory(ModelTest, return_mappings=True)

        assert issubclass(actual, ModelResource)
        assert issubclass(actual_from, Mapping)
        assert issubclass(actual_to, Mapping)

    def test_exclude_fields(self):
        actual = table_resource_factory(ModelTest, exclude_fields='name')

        assert not hasattr(actual, 'name')

    def test_not_a_table(self):
        with pytest.raises(TypeError):
            table_resource_factory("eek")

    def test_wrong_args(self):
        with pytest.raises(ValueError):
            table_resource_factory(test_table, return_mappings=True)

    def test_to_model(self):
        Resource = table_resource_factory(ModelTest)

        target = Resource(id=1, name='Foo', created=datetime(2020, 10, 10))

        actual = target.to_model()

        assert isinstance(actual, ModelTest)
        assert actual.id == 1
        assert actual.name == 'Foo'
        assert actual.created == datetime(2020, 10, 10)
