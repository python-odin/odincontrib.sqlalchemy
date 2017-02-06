from odin import registration
from odin.mapping import FieldResolverBase


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
