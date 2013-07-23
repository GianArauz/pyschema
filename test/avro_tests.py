import unittest
from pyschema import Record
from pyschema.types import Boolean, Integer, Float, Blob, Text, Enum, List
from pyschema.contrib import avro
from pprint import pprint
import simplejson as json


class SomeAvroRecord(Record):
    a = Text()
    b = Integer()
    c = Blob()
    d = Boolean()
    e = Float()
    f = Enum([
        "FOO", "bar"
    ])
    g = List(Text())


hand_crafted_schema_dict = {
    "type": "record",
    "name": "SomeAvroRecord",
    "fields": [
        {"name": "a", "type": "string"},
        {"name": "b", "type": "long"},
        {"name": "c", "type": "bytes"},
        {"name": "d", "type": "boolean"},
        {"name": "e", "type": "double"},
        {"name": "f", "type": "enum", "symbols": ["FOO", "bar"]},
        {"name": "g", "type": "array", "items": "string"},
    ]
}


class TestAvro(unittest.TestCase):
    def recursive_compare(self, node1, node2):
        if isinstance(node1, dict):
            for k, v1 in node1.iteritems():
                v2 = node2[k]
                self.recursive_compare(v1, v2)
        elif isinstance(node1, list):
            for i, v1 in enumerate(node1):
                v2 = node2[i]
                self.recursive_compare(v1, v2)
        else:
            self.assertEquals(node1, node2)

    def test_avro_schema(self):
        schema = avro.get_schema_dict(SomeAvroRecord)
        pprint(schema)
        fields = schema["fields"]
        names = tuple(x["name"] for x in fields)
        self.assertEquals(
            names,
            ("a", "b", "c", "d", "e", "f", "g")
        )
        self.assertEquals(schema["type"], "record")
        self.assertEquals(schema["name"], "SomeAvroRecord")

    def test_roundtrip(self):
        schema_string = avro.get_schema_string(SomeAvroRecord)
        schema_dict = json.loads(schema_string)
        self.recursive_compare(schema_dict, hand_crafted_schema_dict)
        self.recursive_compare(hand_crafted_schema_dict, schema_dict)
