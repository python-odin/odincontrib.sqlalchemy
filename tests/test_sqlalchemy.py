import pytest

from sqlalchemy import Column, String, Text, Table, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

from odin import StringField, Resource

from odincontrib.sqlalchemy import field_factory, table_resource_factory, register_model_base

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


# test_table = Table(
#     Column(Integer, name='id', primary_key=True),
#     Column(String(256), name='name'),
#     Column(DateTime(), name='created'),
# )
#

class ModelTest(Base):
    __tablename__ = 'ModelTest'

    id = Column(Integer, primary_key=True)
    name = Column(String(256))
    created = Column(DateTime)


class TestTableResourceFactory(object):
    # def test_from_table(self):
    #     actual = table_resource_factory(test_table)
    #
    #     assert isinstance(actual, Resource)

    def test_from_declarative(self):
        actual = table_resource_factory(ModelTest)

        assert issubclass(actual, Resource)
