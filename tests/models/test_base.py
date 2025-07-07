"""
Tests for base model functionality.
"""

from datetime import datetime
from typing import ClassVar

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field

from app.models.base import BaseModel


# Create a test model that inherits from BaseModel
class BaseTestModel(BaseModel, table=True):
    """Test model for testing BaseModel functionality."""

    __tablename__: ClassVar[str] = "test_models"

    name: str = Field(nullable=False)
    description: str = Field(default="")
    value: int = Field(default=0)


@pytest.mark.models
@pytest.mark.asyncio
async def test_base_model_creation(db: AsyncSession):
    """Test basic model creation with BaseModel."""
    # Create a test record
    test_data = {"name": "Test Item", "description": "Test description", "value": 42}

    # Create using the class method
    item = await BaseTestModel.create(db, test_data)

    assert item.id is not None
    assert item.name == "Test Item"
    assert item.description == "Test description"
    assert item.value == 42
    assert item.created_at is not None
    assert item.updated_at is not None
    assert isinstance(item.created_at, datetime)
    assert isinstance(item.updated_at, datetime)


@pytest.mark.models
@pytest.mark.asyncio
async def test_base_model_get_by_id(db: AsyncSession):
    """Test getting a model by ID."""
    # Create a test record first
    test_data = {"name": "Get By ID Test", "value": 123}
    created_item = await BaseTestModel.create(db, test_data)

    # Get the item by ID
    retrieved_item = await BaseTestModel.get_by_id(db, created_item.id)

    assert retrieved_item is not None
    assert retrieved_item.id == created_item.id
    assert retrieved_item.name == "Get By ID Test"
    assert retrieved_item.value == 123


@pytest.mark.models
@pytest.mark.asyncio
async def test_base_model_get_by_id_not_found(db: AsyncSession):
    """Test getting a non-existent model by ID."""
    # Try to get a non-existent item
    result = await BaseTestModel.get_by_id(db, 99999)

    assert result is None


@pytest.mark.models
@pytest.mark.asyncio
async def test_base_model_get_all(db: AsyncSession):
    """Test getting all models with pagination."""
    # Create multiple test records
    test_items = []
    for i in range(5):
        test_data = {"name": f"Item {i}", "value": i * 10}
        item = await BaseTestModel.create(db, test_data)
        test_items.append(item)

    # Get all items
    all_items = await BaseTestModel.get_all(db)

    # Should have at least our test items
    assert len(all_items) >= 5

    # Test pagination
    paginated_items = await BaseTestModel.get_all(db, skip=0, limit=2)
    assert len(paginated_items) == 2

    # Test with skip
    skipped_items = await BaseTestModel.get_all(db, skip=2, limit=2)
    assert len(skipped_items) == 2


@pytest.mark.models
@pytest.mark.asyncio
async def test_base_model_update(db: AsyncSession):
    """Test updating a model."""
    # Create a test record
    test_data = {"name": "Original Name", "value": 100}
    item = await BaseTestModel.create(db, test_data)
    original_updated_at = item.updated_at

    # Wait a tiny bit to ensure updated_at changes
    import asyncio

    await asyncio.sleep(0.01)

    # Update the item
    update_data = {"name": "Updated Name", "value": 200}
    updated_item = await item.update(db, update_data)

    assert updated_item.id == item.id
    assert updated_item.name == "Updated Name"
    assert updated_item.value == 200
    assert updated_item.updated_at > original_updated_at


@pytest.mark.models
@pytest.mark.asyncio
async def test_base_model_update_partial(db: AsyncSession):
    """Test partial update of a model."""
    # Create a test record
    test_data = {"name": "Partial Test", "description": "Original desc", "value": 50}
    item = await BaseTestModel.create(db, test_data)

    # Update only one field
    update_data = {"value": 75}
    updated_item = await item.update(db, update_data)

    # Only the updated field should change
    assert updated_item.name == "Partial Test"  # Unchanged
    assert updated_item.description == "Original desc"  # Unchanged
    assert updated_item.value == 75  # Changed


@pytest.mark.models
@pytest.mark.asyncio
async def test_base_model_delete(db: AsyncSession):
    """Test deleting a model."""
    # Create a test record
    test_data = {"name": "To Be Deleted", "value": 999}
    item = await BaseTestModel.create(db, test_data)
    item_id = item.id

    # Delete the item
    await item.delete(db)

    # Verify it's deleted
    deleted_item = await BaseTestModel.get_by_id(db, item_id)
    assert deleted_item is None


@pytest.mark.models
@pytest.mark.asyncio
async def test_base_model_default_values(db: AsyncSession):
    """Test model creation with default values."""
    # Create with minimal data (using defaults)
    test_data = {"name": "Minimal Item"}
    item = await BaseTestModel.create(db, test_data)

    assert item.name == "Minimal Item"
    assert item.description == ""  # Default value
    assert item.value == 0  # Default value
    assert item.created_at is not None
    assert item.updated_at is not None


@pytest.mark.models
@pytest.mark.asyncio
async def test_base_model_timestamps(db: AsyncSession):
    """Test that timestamps are set correctly."""
    before_creation = datetime.now()

    # Create a test record
    test_data = {"name": "Timestamp Test"}
    item = await BaseTestModel.create(db, test_data)

    after_creation = datetime.now()

    # Check that timestamps are within expected range
    assert before_creation <= item.created_at <= after_creation
    assert before_creation <= item.updated_at <= after_creation

    # Initially, created_at and updated_at should be very close
    time_diff = abs((item.updated_at - item.created_at).total_seconds())
    assert time_diff < 1.0  # Less than 1 second difference


@pytest.mark.models
@pytest.mark.asyncio
async def test_base_model_update_timestamp_changes(db: AsyncSession):
    """Test that updated_at changes when model is updated."""
    # Create a test record
    test_data = {"name": "Timestamp Update Test"}
    item = await BaseTestModel.create(db, test_data)
    original_created_at = item.created_at
    original_updated_at = item.updated_at

    # Wait a bit to ensure timestamp difference
    import asyncio

    await asyncio.sleep(0.01)

    # Update the item
    update_data = {"name": "Updated Timestamp Test"}
    updated_item = await item.update(db, update_data)

    # created_at should remain the same
    assert updated_item.created_at == original_created_at

    # updated_at should be newer
    assert updated_item.updated_at > original_updated_at


@pytest.mark.models
def test_base_model_inheritance():
    """Test that BaseModel can be properly inherited."""
    # Test that our BaseTestModel properly inherits from BaseModel
    assert issubclass(BaseTestModel, BaseModel)

    # Test that required fields are present
    assert hasattr(BaseTestModel, "id")
    assert hasattr(BaseTestModel, "created_at")
    assert hasattr(BaseTestModel, "updated_at")
    assert hasattr(BaseTestModel, "__tablename__")

    # Test that class methods are available
    assert hasattr(BaseTestModel, "get_by_id")
    assert hasattr(BaseTestModel, "get_all")
    assert hasattr(BaseTestModel, "create")

    # Test that instance methods are available
    test_instance = BaseTestModel(name="test")
    assert hasattr(test_instance, "update")
    assert hasattr(test_instance, "delete")


@pytest.mark.models
@pytest.mark.asyncio
async def test_base_model_create_with_empty_dict(db: AsyncSession):
    """Test creating a model with empty data dict."""
    # This should work with default values
    empty_data = {}

    # This will fail because 'name' is required (nullable=False)
    with pytest.raises(
        Exception
    ):  # Could be ValidationError or database constraint error
        await BaseTestModel.create(db, empty_data)
