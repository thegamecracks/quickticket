import pytest


# https://pytest-django.readthedocs.io/en/latest/database.html
@pytest.mark.django_db
def test_case(example_fixture: str):
    assert example_fixture == "Hello world!"
