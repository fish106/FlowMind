from typing import Any, Optional

from pydantic import BaseModel, Field

from core.domain.task_example import SerializableTaskExample
from core.domain.task_variant import SerializableTaskVariant
from core.utils.hash import compute_obj_hash


class CreateExampleRequest(BaseModel):
    task_input: dict[str, Any] = Field(..., description="the input of the task. Must match the input schema")
    task_output: dict[str, Any] = Field(..., description="the output of the task. Must match the output schema")

    from_task_run_id: Optional[str] = None
    in_training_set: Optional[bool] = None

    from_correction: Optional[bool] = Field(
        default=None,
        description="whether the example comes from a correction, "
        "i-e whether the LLM made a mistake in the original task run",
    )

    def build(self, task_variant: SerializableTaskVariant) -> SerializableTaskExample:
        task_variant.enforce(self.task_input, self.task_output)
        return SerializableTaskExample(
            id="",  # will be generated by the storage
            task_id=task_variant.task_id,
            task_schema_id=task_variant.task_schema_id,
            task_input=self.task_input,
            task_input_hash=compute_obj_hash(self.task_input),
            task_output=self.task_output,
            task_output_hash=compute_obj_hash(self.task_output),
            from_task_run_id=self.from_task_run_id,
            in_training_set=self.in_training_set or False,
            from_correction=self.from_correction,
        )
