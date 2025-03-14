from datetime import datetime, timedelta

import pytest
from bson.tz_util import utc

from core.storage.mongo.models.task_variant import TaskVariantDocument
from core.storage.mongo.mongo_storage import MongoStorage
from core.storage.mongo.mongo_storage_test import TASK_ID, _task_variant  # pyright: ignore [reportPrivateUsage]
from core.storage.mongo.mongo_types import AsyncCollection
from core.storage.mongo.partials.task_variants import MongoTaskVariantsStorage
from core.storage.mongo.utils import dump_model


@pytest.fixture(scope="function")
def task_variants_storage(storage: MongoStorage, task_variants_col: AsyncCollection) -> MongoTaskVariantsStorage:
    return storage.task_variants


@pytest.fixture(scope="function")
async def inserted_variants(task_variants_col: AsyncCollection):
    task_variants = [
        _task_variant(),
        _task_variant(schema_id=2),
        _task_variant(tenant="tenant_2"),  # same slug, different tenant
        _task_variant(slug="slug_2"),  # same tenant, different slug
    ]

    await task_variants_col.insert_many([dump_model(task_variant) for task_variant in task_variants])
    return task_variants


class TestUpdateTask:
    async def test_is_public(
        self,
        task_variants_storage: MongoTaskVariantsStorage,
        task_variants_col: AsyncCollection,
        inserted_variants: list[TaskVariantDocument],
    ):
        assert await task_variants_col.count_documents({"is_public": True}) == 0

        await task_variants_storage.update_task(TASK_ID, is_public=True)

        public_tasks = [a async for a in task_variants_col.find({"is_public": True})]
        assert len(public_tasks) == 2
        assert {a.id for a in inserted_variants[:2]} == {a["_id"] for a in public_tasks}

    async def test_name(
        self,
        task_variants_storage: MongoTaskVariantsStorage,
        task_variants_col: AsyncCollection,
        inserted_variants: list[TaskVariantDocument],
    ):
        await task_variants_storage.update_task(TASK_ID, name="new_name")

        new_name_tasks = [a async for a in task_variants_col.find({"name": "new_name"})]
        assert len(new_name_tasks) == 2
        assert {a.id for a in inserted_variants[:2]} == {a["_id"] for a in new_name_tasks}


class TestGetLatestSchemaTaskVariant:
    async def test_get_latest_schema_task_variant(
        self,
        task_variants_storage: MongoTaskVariantsStorage,
        task_variants_col: AsyncCollection,
    ):
        # Create task variants with different schema_ids and created_at times
        base_time = datetime(year=2024, month=1, day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=utc)
        variants = [
            _task_variant(schema_id=1, created_at=base_time),
            _task_variant(schema_id=2, created_at=base_time + timedelta(minutes=1)),
            _task_variant(schema_id=2, created_at=base_time + timedelta(minutes=2)),
            _task_variant(schema_id=3, created_at=base_time),
            _task_variant(schema_id=3, created_at=base_time + timedelta(minutes=3)),
        ]

        await task_variants_col.insert_many([dump_model(variant) for variant in variants])

        # Test getting the latest schema task variant
        latest_variant = await task_variants_storage.get_latest_task_variant(TASK_ID)
        assert latest_variant is not None
        assert latest_variant.task_schema_id == 3
        assert latest_variant.created_at == base_time + timedelta(minutes=3)

        other_variant = await task_variants_storage.get_latest_task_variant(TASK_ID, schema_id=2)
        assert other_variant is not None
        assert other_variant.task_schema_id == 2
        assert other_variant.created_at == base_time + timedelta(minutes=2)

    async def test_get_latest_schema_task_variant_no_variants(
        self,
        task_variants_storage: MongoTaskVariantsStorage,
        task_variants_col: AsyncCollection,
    ):
        # Test when there are no variants for the given task_id
        result = await task_variants_storage.get_latest_task_variant("non_existent_task_id")
        assert result is None
