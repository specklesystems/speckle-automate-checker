"""Helper module for a speckle object tree flattening."""

from collections.abc import Iterable
from typing import Optional, Tuple, List

from specklepy.objects import Base
from specklepy.objects.other import Instance, Transform


def speckle_print(log_string: str = "banana") -> None:

    print("\033[92m" + str(log_string) + "\033[0m")


def flatten_base(base: Base) -> Iterable[Base]:
    """Flatten a base object into an iterable of bases."""
    elements = getattr(base, "elements", getattr(base, "@elements", None))
    if elements is not None:
        for element in elements:
            yield from flatten_base(element)
    yield base


def flatten_base_thorough(base: Base, parent_type: str = None) -> Iterable[Base]:
    """Take a base and flatten it to an iterable of bases.

    Args:
        base: The base object to flatten.
        parent_type: The type of the parent object, if any.

    Yields:
        Base: A flattened base object.
    """
    if isinstance(base, Base):
        base["parent_type"] = parent_type

    elements = getattr(base, "elements", getattr(base, "@elements", None))
    if elements:
        try:
            for element in elements:
                # Recursively yield flattened elements of the child
                yield from flatten_base_thorough(element, base.speckle_type)
        except KeyError:
            pass
    elif hasattr(base, "@Lines"):
        categories = base.get_dynamic_member_names()

        # could be old revit
        try:
            for category in categories:
                print(category)
                if category.startswith("@"):
                    category_object: Base = getattr(base, category)[0]
                    yield from flatten_base_thorough(
                        category_object, category_object.speckle_type
                    )

        except KeyError:
            pass

    yield base


def extract_base_and_transform(
    base: Base,
    inherited_instance_id: Optional[str] = None,
    transform_list: Optional[List[Transform]] = None,
) -> Tuple[Base, str, Optional[List[Transform]]]:
    """
    Traverses Speckle object hierarchies to yield `Base` objects and their transformations.
    Tailored to Speckle's AEC data structures, it covers the newer hierarchical structures
    with Collections and also  with patterns found in older Revit specific data.

    Parameters:
    - base (Base): The starting point `Base` object for traversal.
    - inherited_instance_id (str, optional): The inherited identifier for `Base` objects without a unique ID.
    - transform_list (List[Transform], optional): Accumulated list of transformations from parent to child objects.

    Yields:
    - tuple: A `Base` object, its identifier, and a list of applicable `Transform` objects or None.

    The id of the `Base` object is either the inherited identifier for a definition from an instance
    or the one defined in the object.
    """
    # Derive the identifier for the current `Base` object, defaulting to an inherited one if needed.
    current_id = getattr(base, "id", inherited_instance_id)
    transform_list = transform_list or []

    if isinstance(base, Instance):
        # Append transformation data and dive into the definition of `Instance` objects.
        if base.transform:
            transform_list.append(base.transform)
        if base.definition:
            yield from extract_base_and_transform(
                base.definition, current_id, transform_list.copy()
            )
    else:
        # Initial yield for the current `Base` object.
        yield base, current_id, transform_list

        # Process 'elements' and '@elements', typical containers for `Base` objects in AEC models.
        elements_attr = getattr(base, "elements", []) or getattr(base, "@elements", [])
        for element in elements_attr:
            if isinstance(element, Base):
                # Recurse into each `Base` object within 'elements' or '@elements'.
                yield from extract_base_and_transform(
                    element, current_id, transform_list.copy()
                )

        # Recursively process '@'-prefixed properties that are Base objects with 'elements'.
        # This is a common pattern in older Speckle data models, such as those used for Revit commits.
        for attr_name in dir(base):
            if attr_name.startswith("@"):
                attr_value = getattr(base, attr_name)
                # If the attribute is a Base object containing 'elements', recurse into it.
                if isinstance(attr_value, Base) and hasattr(attr_value, "elements"):
                    yield from extract_base_and_transform(
                        attr_value, current_id, transform_list.copy()
                    )
