# coding: utf-8
from __future__ import absolute_import
from __future__ import unicode_literals

import datetime
import unittest
import json

import fs
import parameterized
import requests
import six

import instalooter.cli
from instalooter._cli.constants import USAGE
from instalooter._cli import time as timeutils

from .utils import mock
from .utils.method_names import firstparam


# @mock.patch('instalooter.looter.requests.Session', lambda: TestCLI.session)
class TestCLI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.session = requests.Session()

    @classmethod
    def tearDownClass(cls):
        cls.session.close()

    def setUp(self):
        self.destfs = fs.open_fs("temp://")
        self.tmpdir = self.destfs.getsyspath("/")

    def tearDown(self):
        self.destfs.close()

    def test_user(self):
        r = instalooter.cli.main(["user", "mysteryjets", self.tmpdir, "-q", '-n', '10'])
        self.assertEqual(r, 0)
        self.assertEqual(len(self.destfs.listdir('/')), 10)

    def test_single_post(self):
        r = instalooter.cli.main(["post", "BFB6znLg5s1", self.tmpdir, "-q"])
        self.assertEqual(r, 0)
        self.assertTrue(self.destfs.exists("1243533605591030581.jpg"))

    def test_dump_json(self):
        r = instalooter.cli.main(["post", "BIqZ8L8AHmH", self.tmpdir, '-q', '-d'])
        self.assertEqual(r, 0)

        self.assertTrue(self.destfs.exists("1308972728853756295.json"))
        self.assertTrue(self.destfs.exists("1308972728853756295.jpg"))

        with self.destfs.open("1308972728853756295.json") as fp:
            json_metadata = json.load(fp)

        self.assertEqual("1308972728853756295", json_metadata["id"])
        self.assertEqual("BIqZ8L8AHmH", json_metadata["shortcode"])

    def test_dump_only(self):
        r = instalooter.cli.main(["post", "BIqZ8L8AHmH", self.tmpdir, '-q', '-D'])
        self.assertEqual(r, 0)

        self.assertTrue(self.destfs.exists("1308972728853756295.json"))
        self.assertFalse(self.destfs.exists("1308972728853756295.jpg"))

        with self.destfs.open("1308972728853756295.json") as fp:
            json_metadata = json.load(fp)

        self.assertEqual("1308972728853756295", json_metadata["id"])
        self.assertEqual("BIqZ8L8AHmH", json_metadata["shortcode"])

    def test_usage(self):
        handle = six.moves.StringIO()
        instalooter.cli.main(["--usage"], stream=handle)
        self.assertEqual(handle.getvalue().strip(), USAGE.strip())

    @unittest.expectedFailure
    def test_single_post_from_url(self):
        url = "https://www.instagram.com/p/BFB6znLg5s1/"
        instalooter.cli.main(["post", url, self.tmpdir, "-q"])
        self.assertIn("1243533605591030581.jpg", os.listdir(self.tmpdir))


class TestTimeUtils(unittest.TestCase):

    @parameterized.parameterized.expand([
        (":", (None, None)),
        ("2017-03-12:", (datetime.date(2017, 3, 12), None)),
        (":2016-08-04", (None, datetime.date(2016, 8, 4))),
        ("2017-03-01:2017-02-01", (datetime.date(2017, 3, 1), datetime.date(2017, 2, 1))),
    ], testcase_func_name=firstparam)
    def test_get_times_from_cli(self, token, expected):
        self.assertEqual(timeutils.get_times_from_cli(token), expected)

    @parameterized.parameterized.expand([
        ("thisday", 0, 0),
        ("thisweek", 7, 7),
        ("thismonth", 28, 31),
        ("thisyear", 365, 366),
    ], testcase_func_name=firstparam)
    def test_get_times_from_cli_keywords(self, token, inf, sup):
        start, stop = timeutils.get_times_from_cli(token)
        self.assertGreaterEqual(start - stop, datetime.timedelta(inf))
        self.assertLessEqual(start - stop, datetime.timedelta(sup))
        self.assertEqual(start, datetime.date.today())

    @parameterized.parameterized.expand([
        ["x"],
        ["x:y"],
        ["x:y:z"],
    ], testcase_func_name=firstparam)
    def test_get_times_from_cli_bad_format(self, token):
        self.assertRaises(ValueError, timeutils.get_times_from_cli, token)
