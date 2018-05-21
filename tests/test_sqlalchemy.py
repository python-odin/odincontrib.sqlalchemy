import pytest

from datetime import datetime
from odin import StringField, Mapping
from odin.utils import getmeta
from odin.registration import cache
from sqlalchemy import Column, String, Text, Table, Integer, DateTime, MetaData
from sqlalchemy.ext.declarative import declarative_base

from odincontrib.sqlalchemy import field_factory, table_resource_factory, register_model_base, ModelResource

Base = declarative_base()
register_model_base(Base)


@pytest.mark.parametrize('column, expected, expected_attrs', (
    (Column(String, primary_key=True), StringField, dict(key=True, null=False)),
    (Column(String(256), nullable=True), StringField, dict(null=True, max_length=256)),
    (Column(Text), StringField, dict(null=True)),
))
def test_field_factory(column, expected, expected_attrs):
    actual = field_factory(column)

    assert isinstance(actual, expected)
    for attr, value in expected_attrs.items():
        assert getattr(actual, attr) == value


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
    @pytest.fixture(autouse=True)
    def clear_resources(self):
        """
        Ensure a cached version of a resource is not re-used.
        """
        cache.resources.clear()
        cache.mappings.clear()
        yield
        cache.resources.clear()
        cache.mappings.clear()

    def test_from_table(self):
        actual = table_resource_factory(test_table)

        assert issubclass(actual, ModelResource)
        assert actual.__name__ == 'ModelATest'

    def test_from_declarative(self):
        actual = table_resource_factory(ModelTest, module='tests')

        assert issubclass(actual, ModelResource)
        assert actual.__name__ == 'ModelTest'

    def test_get_mappings(self):
        actual, actual_from, actual_to = table_resource_factory(ModelTest, module='tests', return_mappings=True)

        assert issubclass(actual, ModelResource)
        assert issubclass(actual_from, Mapping)
        assert issubclass(actual_to, Mapping)

    def test_exclude_fields(self):
        actual = table_resource_factory(ModelTest, module='tests', exclude_fields='name')

        assert not hasattr(actual, 'name')

    def test_additional_fields(self):
        actual = table_resource_factory(ModelTest, module='tests', additional_fields={
            'foo': StringField(),
        })

        assert 'foo' in getmeta(actual).field_map

    def test_not_a_table(self):
        with pytest.raises(TypeError):
            table_resource_factory("eek")

    def test_wrong_args(self):
        with pytest.raises(ValueError):
            table_resource_factory(test_table, return_mappings=True)

    def test_to_model(self):
        resource = table_resource_factory(ModelTest, resource_type_name="ResourceTest",
                                          generate_mappings=True)

        target = resource(id=1, name='Foo', created=datetime(2020, 10, 10))

        actual = target.to_model()

        assert isinstance(actual, ModelTest)
        assert actual.id == 1
        assert actual.name == 'Foo'
        assert actual.created == datetime(2020, 10, 10)
