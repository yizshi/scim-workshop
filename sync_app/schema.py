#!/usr/bin/env python
import json
import jsonschema
from typing import Iterable, OrderedDict, Optional, TypeAlias, Mapping, List, TypeVar
from dataclasses import dataclass, asdict
from sync_app.scim.resource import Resource, ResourceWithMeta, ResourceMeta

COMMON_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:Common"
SCHEMAS_RESOUCE_TYPE = "Schema"
SCHEMAS_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:Schema"

@dataclass
class Attributes:
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[bool] = None
    mutability: Optional[str] = None
    returned: Optional[str] = None
    uniqueness: Optional[str] = None
    required: Optional[bool] = False
    multiValued: Optional[bool] = False
    caseExact: Optional[bool] = False
    subAttributes: Optional[List["Attributes"]] = None
    referenceTypes: Optional[List[str]] = None
    canonicalValues: Optional[List[str]] = None

class JSONSchema:
    schema: Mapping
    id: str

    @staticmethod
    def load(path: str, schemaValidator: Optional["JSONSchema"] = None) -> "JSONSchema":
        with open(path, "r") as fh:
            return JSONSchema(json.load(fh), schemaValidator)

    def __init__(self, schema: Mapping, schemaValidator: Optional["JSONSchema"] = None):
        assert "$id" in schema, "All schemas must have a $id entry for identification"
        assert (
            "$schema" in schema
        ), "All schemas must have a validating schema in $schema"

        if schemaValidator:
            schemaValidator.validate(schema)

        self.schema = schema
        self.id = schema["$id"]
        self.validatingSchema = schema["$schema"]

    def validate(self, instance: Mapping) -> bool:
        jsonschema.validate(instance, self.schema)
        # No exception means the schema is valid
        return True


IdToSchema: TypeAlias = Mapping[str, JSONSchema]


class SchemaNotFoundInValidator(Exception):
    pass


class ResourceMissingSchemas(Exception):
    pass


@dataclass
class ValidatorResult:
    valid: bool
    errors: Iterable[jsonschema.ValidationError]


class ResourceValidator:
    schemas: IdToSchema

    @staticmethod
    def load(paths: Iterable[str]) -> "ResourceValidator":
        schemas = []
        for path in paths:
            with open(path, "r") as fh:
                schemas.append(JSONSchema(json.load(fh)))

        return ResourceValidator(schemas)

    def __init__(self, schemas: Iterable[JSONSchema]):
        self.schemas = {schema.id: schema for schema in schemas}
        self.validate_schemas()

    def validate_schemas(self) -> ValidatorResult:
        errors: List[jsonschema.ValidationError] = []
        for schema in self.schemas.values():
            validating_schema = schema.validatingSchema
            if validating_schema not in self.schemas:
                raise SchemaNotFoundInValidator(
                    "While processing schema could not find this validating schema: {schema}".format(
                        schema=schema.validatingSchema
                    )
                )
            else:
                try:
                    self.schemas[validating_schema].validate(schema.schema)
                except jsonschema.ValidationError as e:
                    errors.append(e)

        return ValidatorResult(len(errors) == 0, errors)

    def validate(self, resource: Mapping) -> ValidatorResult:
        errors: List[jsonschema.ValidationError] = []

        if "schemas" not in resource:
            raise ResourceMissingSchemas()

        schemas_to_check = resource["schemas"]

        if COMMON_SCHEMA in self.schemas:
            # The common schema is always added if it's present in the validator
            schemas_to_check = schemas_to_check + [COMMON_SCHEMA]

        for schemaId in schemas_to_check:
            schema_to_check = self.schemas.get(schemaId, None)
            if schema_to_check is None:
                raise SchemaNotFoundInValidator(
                    "While processing {meta!r}".format(meta=resource["meta"])
                )
            try:
                schema_to_check.validate(resource)
            except jsonschema.ValidationError as e:
                errors.append(e)

        return ValidatorResult(len(errors) == 0, errors)


class Schemas(ResourceWithMeta):
    name: str
    description: Optional[str] = None
    attributes: Optional[Iterable[Attributes]] = None
    sub_attributes: Optional[Iterable[Iterable[Attributes]]] = None

    def __init__(
        self,
        meta: ResourceMeta,
        name: str,
        description: Optional[str] = None,
        attributes: Optional[Iterable[Attributes]] = None,
        sub_attributes: Optional[Iterable[Iterable[Attributes]]] = None,
    ):
        super().__init__([SCHEMAS_SCHEMA], meta, name)
        self.name = name
        self.description = description
        self.attributes = attributes
        self.sub_attributes = sub_attributes

    @staticmethod
    def from_dict(resource: Mapping) -> "Schemas":
        assert resource["meta"]["resourceType"] == SCHEMAS_RESOUCE_TYPE

        if "attributes" in resource:
            attributes = [Attributes(**a) for a in resource["attributes"]]
        else:
            attributes = []

        for attribute in attributes:
            if attribute.subAttributes:
                sub_attributes = [Attributes(**sa) for sa in attribute.subAttributes]

        return Schemas(
            meta=ResourceMeta(**resource["meta"]),
            name=resource["name"],
            description=resource.get("description", None),
            attributes=attributes,
            sub_attributes=sub_attributes,
        )

    def to_dict(self):
        resource_common = super().to_dict()
        result = {
            **resource_common,
            "name": self.name,
        }
        if self.description is not None:
            result.update({"description": self.description})
        if self.attributes is not None:
            result.update({"attributes": [asdict(a) for a in self.attributes]})
        if self.sub_attributes is not None:
            result.update({"sub_attributes": [asdict(sa) for sa in self.sub_attributes]})

        return result