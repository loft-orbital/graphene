import re
from uuid import uuid4

from graphql import graphql

from ..connection import Connection, ConnectionField
from ..id_type import BaseGlobalIDType, SimpleGlobalIDType, UUIDGlobalIDType
from ..node import Node
from ...types import Int, ObjectType, Schema, String


class TestUUIDGlobalID:
    def setup(self):
        self.user_list = [
            {"id": uuid4(), "name": "First"},
            {"id": uuid4(), "name": "Second"},
            {"id": uuid4(), "name": "Third"},
            {"id": uuid4(), "name": "Fourth"},
        ]
        self.users = {user["id"]: user for user in self.user_list}

        class CustomNode(Node):
            class Meta:
                global_id_type = UUIDGlobalIDType

        class User(ObjectType):
            class Meta:
                interfaces = [CustomNode]

            name = String()

            @classmethod
            def get_node(cls, _type, _id):
                return self.users[_id]

        class RootQuery(ObjectType):
            user = CustomNode.Field(User)

        self.schema = Schema(query=RootQuery, types=[User])

    def test_str_schema_correct(self):
        """
        Check that the schema has the expected and custom node interface and user type and that they both use UUIDs
        """
        parsed = re.findall(r"(.+) \{\n\s*([\w\W]*?)\n\}", str(self.schema))
        types = [t for t, f in parsed]
        fields = [f for t, f in parsed]
        custom_node_interface = "interface CustomNode"
        assert custom_node_interface in types
        assert "id: UUID!" == fields[types.index(custom_node_interface)]
        user_type = "type User implements CustomNode"
        assert user_type in types
        assert "id: UUID!\n  name: String" == fields[types.index(user_type)]

    def test_get_by_id(self):
        query = """query userById($id: UUID!) {
            user(id: $id) {
                id
                name
            }
        }"""
        # UUID need to be converted to string for serialization
        result = graphql(self.schema, query, variable_values={"id": str(self.user_list[0]["id"])})
        assert not result.errors
        assert result.data["user"]["id"] == str(self.user_list[0]["id"])
        assert result.data["user"]["name"] == self.user_list[0]["name"]


class TestSimpleGlobalID:
    def setup(self):
        self.user_list = [
            {"id": "my global primary key in clear 1", "name": "First"},
            {"id": "my global primary key in clear 2", "name": "Second"},
            {"id": "my global primary key in clear 3", "name": "Third"},
            {"id": "my global primary key in clear 4", "name": "Fourth"},
        ]
        self.users = {user["id"]: user for user in self.user_list}

        class CustomNode(Node):
            class Meta:
                global_id_type = SimpleGlobalIDType

        class User(ObjectType):
            class Meta:
                interfaces = [CustomNode]

            name = String()

            @classmethod
            def get_node(cls, _type, _id):
                return self.users[_id]

        class RootQuery(ObjectType):
            user = CustomNode.Field(User)

        self.schema = Schema(query=RootQuery, types=[User])

    def test_str_schema_correct(self):
        """
        Check that the schema has the expected and custom node interface and user type and that they both use UUIDs
        """
        parsed = re.findall(r"(.+) \{\n\s*([\w\W]*?)\n\}", str(self.schema))
        types = [t for t, f in parsed]
        fields = [f for t, f in parsed]
        custom_node_interface = "interface CustomNode"
        assert custom_node_interface in types
        assert "id: ID!" == fields[types.index(custom_node_interface)]
        user_type = "type User implements CustomNode"
        assert user_type in types
        assert "id: ID!\n  name: String" == fields[types.index(user_type)]

    def test_get_by_id(self):
        query = """query {
            user(id: "my global primary key in clear 3") {
                id
                name
            }
        }"""
        result = graphql(self.schema, query)
        assert not result.errors
        assert result.data["user"]["id"] == self.user_list[2]["id"]
        assert result.data["user"]["name"] == self.user_list[2]["name"]


class TestCustomGlobalID:
    def setup(self):
        self.user_list = [
            {"id": 1, "name": "First"},
            {"id": 2, "name": "Second"},
            {"id": 3, "name": "Third"},
            {"id": 4, "name": "Fourth"},
        ]
        self.users = {user["id"]: user for user in self.user_list}

        class CustomGlobalIDType(BaseGlobalIDType):
            """
            Global id that is simply and integer in clear.
            """

            graphene_type = Int

            @classmethod
            def resolve_global_id(cls, info, global_id):
                _type = info.return_type.graphene_type._meta.name
                return _type, global_id

            @classmethod
            def to_global_id(cls, _type, _id):
                return _id

        class CustomNode(Node):
            class Meta:
                global_id_type = CustomGlobalIDType

        class User(ObjectType):
            class Meta:
                interfaces = [CustomNode]

            name = String()

            @classmethod
            def get_node(cls, _type, _id):
                return self.users[_id]

        class RootQuery(ObjectType):
            user = CustomNode.Field(User)

        self.schema = Schema(query=RootQuery, types=[User])

    def test_str_schema_correct(self):
        """
        Check that the schema has the expected and custom node interface and user type and that they both use UUIDs
        """
        parsed = re.findall(r"(.+) \{\n\s*([\w\W]*?)\n\}", str(self.schema))
        types = [t for t, f in parsed]
        fields = [f for t, f in parsed]
        custom_node_interface = "interface CustomNode"
        assert custom_node_interface in types
        assert "id: Int!" == fields[types.index(custom_node_interface)]
        user_type = "type User implements CustomNode"
        assert user_type in types
        assert "id: Int!\n  name: String" == fields[types.index(user_type)]

    def test_get_by_id(self):
        query = """query {
            user(id: 2) {
                id
                name
            }
        }"""
        result = graphql(self.schema, query)
        assert not result.errors
        assert result.data["user"]["id"] == self.user_list[1]["id"]
        assert result.data["user"]["name"] == self.user_list[1]["name"]
