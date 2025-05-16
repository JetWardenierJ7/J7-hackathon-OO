"""This module defines the Data schemas used by the API"""

from marshmallow import Schema, fields


class DefaultResponseSchema(Schema):
    """Schema for a default API response"""

    message = fields.Str()


class LoginReponseSchema(Schema):
    """Schema for the login reponse"""

    access_token = fields.Str()


class UserSchema(Schema):
    """The schema for defining a User"""

    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(
        required=True, load_only=True
    )  # load only - Always for password
    name = fields.Str()
    surname = fields.Str()
    status = fields.Bool()
    mailings = fields.Bool()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    role = fields.Str()
    ip_address = fields.Str(load_only=True)
    timezone = fields.Str(load_only=True)
    display_name = fields.Str()


class UserUpdateSchema(Schema):
    """The schema used for updating a User"""

    name = fields.Str()
    surname = fields.Str()
    mailings = fields.Bool()
    updated_at = fields.DateTime(dump_only=True)


class UserPasswordSchema(Schema):
    """The schema used for updating a password for a User"""

    new_password = fields.Str()
    new_password_confirmation = fields.Str()


class UserCreatedSchema(Schema):
    """The schema used for creating a User"""

    user_id = fields.Int()


class PlainDocumentSchema(Schema):
    """Schema that represents a `Chunk` in a `Document`"""

    chunk_id = fields.Str(required=True)
    document_id = fields.Str(required=True)
    document_title = fields.Str()
    content_text = fields.Str()
    extension = fields.Str()
    position = fields.Int()
    lastmodified = fields.Str()
    published = fields.Str()
    publisher = fields.Str()
    source = fields.Str()
    type_primary = fields.Str()
    type_secondary = fields.Str()
    summary = fields.Str()
    url = fields.Str()
    summary = fields.Str()

class SearchDocumentsSchema(Schema): 
    search_string = fields.Str()
    search_from = fields.Str()
    search_until = fields.Str()
    publisher = fields.List(fields.Str())
    type_primary = fields.List(fields.Str())


class DefaultInputSchema(Schema): 
    """Schema for a default input"""
    input = fields.Str()

class DefaultOutputSchema(Schema): 
    """Schema for a default input"""
    output = fields.Str()

class SearchObjectsSchema(Schema): 
    date = fields.Str()
    documents = fields.List(fields.Nested(PlainDocumentSchema()))

class filterTypePrimarySchema(Schema): 
    type_primary = fields.Str()
    amount_of_docs = fields.Int()

class filterTypeSecondarySchema(Schema): 
    type_secondary = fields.Str()
    amount_of_docs = fields.Int()

class filterPublishersSchema(Schema): 
    publisher = fields.Str()
    amount_of_docs = fields.Int()

class SearchObjectFilterSchema(Schema): 
    type_primary = fields.List(fields.Nested(filterTypePrimarySchema()))
    type_secondary = fields.List(fields.Nested(filterTypeSecondarySchema()))
    publishers = fields.List(fields.Nested(filterPublishersSchema()))


class SearchResultsSchema(Schema): 
    timeline = fields.List(fields.Nested(SearchObjectsSchema()))
    filters = fields.Nested(SearchObjectFilterSchema())
class ChatInputSchema(Schema):
    """Schema for a chat input"""
    question = fields.Str()
