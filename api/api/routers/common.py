import logging
import os
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

from core.domain.errors import BadRequestError
from core.domain.task_group_properties import TaskGroupProperties
from core.domain.version_environment import VersionEnvironment
from core.domain.version_reference import VersionReference as DomainVersionReference

_logger = logging.getLogger(__name__)

INCLUDE_PRIVATE_ROUTES = os.getenv("ENV_NAME", "") != "prod"
PRIVATE_TAGS = ["Private"]

PRIVATE_KWARGS: Any = {"include_in_schema": INCLUDE_PRIVATE_ROUTES, "tags": PRIVATE_TAGS}


class DeprecatedVersionReference(BaseModel):
    """Refer to an existing group or create a new one with the given properties.
    Only one of id, iteration or properties must be provided"""

    id: Optional[str] = Field(description="The id of an existing group", default=None)
    iteration: Optional[int] = Field(description="An iteration for an existing group.", default=None)
    properties: Optional[TaskGroupProperties] = Field(
        description="The properties to evaluate the task schema with. A group will be created if needed",
        default=None,
    )
    alias: Optional[str] = Field(description="An alias for the group", default=None)

    is_external: Optional[bool] = Field(
        description="Whether the group is external, i-e not created by internal runners",
        default=None,
    )

    @model_validator(mode="after")
    def post_validate(self):
        if self.id:
            # We log to make sure we catch casese
            _logger.error("id is deprecated, use version iteration or alias instead")
            raise ValueError("id is deprecated, use version iteration or alias instead")

        count = sum(1 for x in [self.iteration, self.properties, self.alias] if x)
        if count != 1:
            raise ValueError("Exactly one of id, iteration, alias or properties must be provided")
        return self

    def to_domain(self):
        if self.properties:
            return DomainVersionReference(properties=self.properties)

        if self.iteration:
            return DomainVersionReference(version=self.iteration)

        if self.alias:
            if not self.alias.startswith("environment="):
                raise BadRequestError("alias must start with environment=", capture=True)
            try:
                env = VersionEnvironment(self.alias.removeprefix("environment="))
                return DomainVersionReference(version=env)
            except ValueError:
                raise BadRequestError("not a valid environment", capture=True)

        raise BadRequestError("not a valid group reference", capture=True)
