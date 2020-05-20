from unittest.mock import MagicMock, call
from contextlib import contextmanager
from functools import partial

import pytest

from featurevis import mixins


@contextmanager
def does_not_raise():
    yield


@pytest.fixture
def key():
    return MagicMock(name="key")


@pytest.fixture
def model():
    return MagicMock(name="Model")


class TestMEIMethodMixin:
    @pytest.fixture
    def generate_mei(self, mei_method, dataloaders, model, seed):
        return partial(mei_method().generate_mei, dataloaders, model, dict(key="key"), seed)

    @pytest.fixture
    def mei_method(self, insert1, magic_and, import_func):
        mei_method = mixins.MEIMethodMixin
        mei_method.insert1 = insert1
        mei_method.__and__ = magic_and
        mei_method.import_func = import_func
        return mei_method

    @pytest.fixture
    def dataloaders(self):
        return MagicMock(name="dataloaders")

    @pytest.fixture
    def seed(self):
        return 42

    @pytest.fixture
    def insert1(self):
        return MagicMock()

    @pytest.fixture
    def magic_and(self):
        magic_and = MagicMock()
        magic_and.return_value.fetch1.return_value = "method_fn", "method_config"
        return magic_and

    @pytest.fixture
    def import_func(self, method_fn):
        return MagicMock(return_value=method_fn)

    @pytest.fixture
    def method_fn(self):
        return MagicMock(return_value=("mei", "score", "output"))

    def test_that_method_is_correctly_inserted(self, mei_method, insert1):
        method_config = MagicMock(name="method_config")
        mei_method().add_method("method_fn", method_config)
        insert1.assert_called_once_with(
            dict(
                method_fn="method_fn",
                method_hash="d41d8cd98f00b204e9800998ecf8427e",
                method_config=method_config,
                method_comment="",
            )
        )

    def test_that_method_is_correctly_fetched(self, generate_mei, magic_and):
        generate_mei()
        magic_and.assert_called_once_with(dict(key="key"))
        magic_and.return_value.fetch1.assert_called_once_with("method_fn", "method_config")

    def test_if_method_function_is_correctly_imported(self, generate_mei, import_func):
        generate_mei()
        import_func.assert_called_once_with("method_fn")

    def test_if_method_function_is_correctly_called(self, generate_mei, model, dataloaders, seed, method_fn):
        generate_mei()
        method_fn.assert_called_once_with(dataloaders, model, "method_config", seed)

    def test_if_returned_mei_entity_is_correct(self, generate_mei):
        mei_entity = generate_mei()
        assert mei_entity == dict(key="key", mei="mei", score="score", output="output")


class TestMEITemplateMixin:
    @pytest.fixture
    def mei_template(
        self, trained_model_table, selector_table, method_table, seed_table, insert1, save, model_loader_class
    ):
        mei_template = mixins.MEITemplateMixin
        mei_template.trained_model_table = trained_model_table
        mei_template.selector_table = selector_table
        mei_template.method_table = method_table
        mei_template.seed_table = seed_table
        mei_template.insert1 = insert1
        mei_template.save = save
        mei_template.model_loader_class = model_loader_class
        get_temp_dir = MagicMock()
        get_temp_dir.return_value.__enter__.return_value = "/temp_dir"
        mei_template.get_temp_dir = get_temp_dir
        mei_template._create_random_filename = MagicMock(side_effect=["filename1", "filename2"])
        return mei_template

    @pytest.fixture
    def trained_model_table(self):
        return MagicMock()

    @pytest.fixture
    def selector_table(self):
        selector_table = MagicMock()
        selector_table.return_value.get_output_selected_model.return_value = "output_selected_model"
        return selector_table

    @pytest.fixture
    def method_table(self):
        method_table = MagicMock()
        method_table.return_value.generate_mei.return_value = dict(mei="mei", output="output")
        return method_table

    @pytest.fixture
    def seed_table(self):
        seed_table = MagicMock()
        seed_table.return_value.__and__.return_value.fetch1.return_value = "seed"
        return seed_table

    @pytest.fixture
    def insert1(self):
        return MagicMock()

    @pytest.fixture
    def save(self):
        return MagicMock()

    @pytest.fixture
    def model_loader_class(self, model_loader):
        return MagicMock(return_value=model_loader)

    @pytest.fixture
    def model_loader(self):
        model_loader = MagicMock()
        model_loader.load.return_value = "dataloaders", "model"
        return model_loader

    def test_if_model_loader_is_correctly_initialized(self, mei_template, trained_model_table, model_loader_class):
        mei_template(cache_size_limit=5)
        model_loader_class.assert_called_once_with(trained_model_table, cache_size_limit=5)

    def test_if_model_is_correctly_loaded(self, key, mei_template, model_loader):
        mei_template().make(key)
        model_loader.load.assert_called_once_with(key=key)

    def test_if_correct_model_output_is_selected(self, key, mei_template, selector_table):
        mei_template().make(key)
        selector_table.return_value.get_output_selected_model.assert_called_once_with("model", key)

    def test_if_seed_is_correctly_fetched(self, key, mei_template, seed_table):
        mei_template().make(key)
        seed_table.return_value.__and__.assert_called_once_with(key)
        seed_table.return_value.__and__.return_value.fetch1.assert_called_once_with("mei_seed")

    def test_if_mei_is_correctly_generated(self, key, mei_template, method_table):
        mei_template().make(key)
        method_table.return_value.generate_mei.assert_called_once_with(
            "dataloaders", "output_selected_model", key, "seed"
        )

    def test_if_mei_is_correctly_saved(self, key, mei_template, save):
        mei_template().make(key)
        assert save.call_count == 2
        save.has_calls(
            call("mei", "/temp_dir/mei_filename1.pth.tar"), call("output", "/temp_dir/output_filename2.pth.tar")
        )

    def test_if_mei_entity_is_correctly_saved(self, key, mei_template, insert1):
        mei_template().make(key)
        insert1.assert_called_once_with(
            dict(mei="/temp_dir/mei_filename1.pth.tar", output="/temp_dir/output_filename2.pth.tar")
        )
