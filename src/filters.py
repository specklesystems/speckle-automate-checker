from specklepy.objects.base import Base

from src.rules import PropertyRules


def filter_objects_by_category(speckle_objects: list[Base], category_input: str) -> tuple[list[Base], list[Base]]:
    """Filters objects by category value and test.

    This function takes a list of Speckle objects, filters out the objects
    with a matching category value and satisfies the test, and returns
    both the matching and non-matching objects.

    Args:
        speckle_objects (List[Base]): The list of Speckle objects to filter.
        category_input (str): The category value to match against.

    Returns:
        Tuple[List[Base], List[Base]]: A tuple containing two lists:
                                        - The first list contains objects with matching category and test.
                                        - The second list contains objects without matching category or test.
    """
    matching_objects = []
    non_matching_objects = []

    for obj in speckle_objects:
        if PropertyRules.is_category(obj, category_input):
            matching_objects.append(obj)
        else:
            non_matching_objects.append(obj)

    return matching_objects, non_matching_objects
