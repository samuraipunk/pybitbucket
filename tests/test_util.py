# -*- coding: utf-8 -*-
import json
from os import path

from pybitbucket.util import links_from


class TestUtil(object):
    @classmethod
    def setup_class(cls):
        cls.test_dir, current_file = path.split(path.abspath(__file__))

    def load_example_repository(self):
        example_path = path.join(
            self.test_dir,
            'example_single_repository.json')
        with open(example_path) as f:
            example = json.load(f)
        return example

    def test_first_link(self):
        example = self.load_example_repository()
        links = links_from(example)
        actual_name, actual_url = next(links)
        assert 'watchers' == actual_name

    def test_counting_link(self):
        example = self.load_example_repository()
        links = links_from(example)
        links_list = list(links)
        # Count of the links in the example,
        # not including the clone links.
        assert 7 == len(links_list)
