import pyschema
from abc import ABCMeta, abstractmethod


class Expression(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def render():
        pass

    def __repr__(self):
        return self.render("default")


class Symbol(Expression):
    def __init__(self, name, namespace=None):
        self.name = name
        self.namespace = namespace

    def render(self, syntax):
        if self.namespace:
            return "{}.{}".format(self.namespace, self.name)
        return self.name


class Multiplication(Expression):
    def __init__(self, left, right):
        super(Multiplication, self).__init__()
        self.left = left
        self.right = right

    def render(self, syntax):
        return "({}) * ({})".format(
            self.left.render(syntax),
            self.right.render(syntax)
        )


class EqualityCheck(Expression):
    def __init__(self, left, right):
        super(EqualityCheck, self).__init__()
        self.left = left
        self.right = right

    def render(self, syntax):
        if syntax == "sql":
            return "({}) = ({})".format(
                self.left.render(syntax),
                self.right.render(syntax)
            )
        return "({}) == ({})".format(
            self.left.render(syntax),
            self.right.render(syntax)
        )


class BooleanValued(Expression):
    def __init__(self, proxy):
        self.proxy = proxy

    def render(self, syntax):
        return self.proxy.render(syntax)

    def __repr__(self):
        return "BooleanValued: " + super(BooleanValued, self).__repr__()

    @classmethod
    def mixin(self, cls):
        "Use as decorator for class to get this property"
        class Wrapper(IntegerValued):
            def __new__(wrappercls, *args, **kwargs):
                return BooleanValued(cls(*args, **kwargs))
        return Wrapper


class IntegerValued(Expression):
    def __init__(self, proxy):
        self.proxy = proxy

    def convert_compatible(self, other):
        if isinstance(other, int):
            return IntegerConstant(other)
        elif isinstance(other, IntegerValued):
            return other
        assert False

    def mul(self, other, reverse):
        other = self.convert_compatible(other)
        if reverse:
            left, right = other, self
        else:
            left, right = self, other
        return IntegerValued(Multiplication(left, right))

    def __mul__(self, other):
        return self.mul(other, reverse=False)

    def __rmul__(self, other):
        return self.mul(other, reverse=True)

    def eq(self, other, reverse):
        other = self.convert_compatible(other)
        if reverse:
            left, right = other, self
        else:
            left, right = self, other
        return BooleanValued(EqualityCheck(left, right))

    def __eq__(self, other):
        return self.eq(other, reverse=False)

    def __req__(self, other):
        return self.eq(other, reverse=True)

    def render(self, syntax):
        return self.proxy.render(syntax)

    def __repr__(self):
        return "IntegerValued: " + super(IntegerValued, self).__repr__()

    @classmethod
    def mixin(self, cls):
        "Use as decorator for class to get this property"
        class Wrapper(IntegerValued):
            def __new__(wrappercls, *args, **kwargs):
                return IntegerValued(cls(*args, **kwargs))
        return Wrapper


@IntegerValued.mixin
class IntegerConstant(Expression):
    def __init__(self, value):
        self.value = value

    def render(self, syntax):
        return str(self.value)


# convenience wrappers
@IntegerValued.mixin
class IntegerSymbol(Symbol):
    pass


SYMBOLMAP = {
    pyschema.Integer: IntegerSymbol
}


class Selection(object):
    def __init__(self, table, expression):
        self.table = table
        self.expression = expression

    def sql(self):
        return "SELECT * FROM {table._name} WHERE {expr}".format(
            table=self.table,
            expr=self.expression.render("sql")
        )


class Table(dict):
    def __init__(self, schema, ref_name):
        self._name = ref_name
        self._fields = {}

        for field_name, field in schema._fields.items():
            symcls = SYMBOLMAP.get(type(field))
            symcls(ref_name, ref_name)
            self._fields[field_name] = symcls(ref_name + "." + field_name)

    def __getattr__(self, name):
        return self._fields[name]

    def __getitem__(self, expression):
        if isinstance(expression, Expression):
            return Selection(self, expression)


if __name__ == "__main__":
    class Foo(pyschema.Record):
        i = pyschema.Integer()

    mytable = Table(Foo, "mytable")
    other = Table(Foo, "other")
    print 5 * mytable.i == mytable.i
    print mytable[mytable.i == other.i * 2].sql()
