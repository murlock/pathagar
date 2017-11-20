import os
from time import sleep

from django.test import TestCase
from django.core.management import call_command, CommandError

from books.epub import Epub
from books.models import Book


class AddBooksTest(TestCase):
    def test_addbooks_csv_valid(self):
        args = ["examples/valid/books.csv"]
        opts = {}
        call_command('addbooks', *args, **opts)

        """
        FIXME: check number and contents of DB
        nb_book = len(Book.objects.all())
        self.assertEqual(nb_book, 2)
        """

    def test_addbooks_json_valid(self):
        args = ["examples/valid/books.json"]
        opts = {'is_json_format': 1}
        call_command('addbooks', *args, **opts)

        """
        FIXME: check number and contents of DB
        nb_book = len(Book.objects.all())
        self.assertEqual(nb_book, 2)
        """

    def test_addbooks_invalid_path(self):
        args = ['addbooks', "examples/books_not_available.csv"]
        self.assertRaises(CommandError,
                          call_command, *args)

    def test_addbooks_invalid_csv(self):
        args = ['addbooks', 'examples/invalid/invalid.csv']
        self.assertRaises(CommandError,
                          call_command, *args)

    def test_exportbooks(self):
        args = ["export.csv"]
        opts = {}
        call_command('exportbooks', *args, **opts)

    def test_exportbooks_addbooks(self):
        if not os.path.exists("exports/"):
            os.mkdir("exports/")

        args = ["exports/export.csv"]
        opts = {"copy_file": 1}
        call_command('exportbooks', *args, **opts)

