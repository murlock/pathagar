import os
import zipfile

from django.test import TestCase
from django.core.management import call_command, CommandError

from books.epub import Epub
from books.models import Book


class EpubTest(TestCase):
    def test_simple_import(self):
        epub = Epub("examples/valid/The Dunwich Horror.epub")
        info = epub.get_info()
        self.assertEqual(info.title, "The Dunwich Horror")
        self.assertEqual(info.creator, "H. P. Lovecraft")
        self.assertEqual(info.language, "en")
        epub.close()

    def test_tags(self):
        epub = Epub("examples/valid/Five Plays.epub")
        info = epub.get_info()
        self.assertEqual(info.subject, ['English drama'])
        epub.close()

    def test_epub_not_found(self):
        self.assertRaises(FileNotFoundError,
                          Epub, 'examples/invalid/not-found.epub')

    def test_not_a_zip_file(self):
        self.assertRaises(zipfile.BadZipFile,
                          Epub, "examples/invalid/not-a-zifile.epub")

    def test_not_mimetype(self):
        self.assertRaises(ValueError,
                          Epub, "examples/invalid/missing-mimetype.epub")

    def test_invalid_mimetype(self):
        self.assertRaises(ValueError,
                          Epub, "examples/invalid/invalid-mimetype.epub")

class AddEpubTest(TestCase):
    def test_01_import_commandline(self):
        nb_book = len(Book.objects.all())
        self.assertEqual(nb_book, 0)

        args = ["examples/valid/The Dunwich Horror.epub"]
        opts = {}
        call_command('addepub', *args, **opts)

        nb_book = len(Book.objects.all())
        self.assertEqual(nb_book, 1)

        book = Book.objects.get(pk=1)
        self.assertEqual(str(book.a_author), "H. P. Lovecraft")
        self.assertEqual(str(book.a_title), "The Dunwich Horror")

        args = ["examples/valid/Five Plays.epub"]
        call_command('addepub', *args, **opts)

        book = Book.objects.get(pk=2)
        self.assertEqual(str(book.a_author), "Lord Dunsany")
        self.assertEqual(str(book.a_title), "Five Plays")
        tags = [str(x) for x in book.tags.all()]
        self.assertEqual(tags, ['English drama'])

    def test_02_import_duplicated(self):
        # try to import duplicated epub
        args = ["examples/valid/The Dunwich Horror.epub"]
        opts = {}
        call_command('addepub', *args, **opts)
        self.assertRaises(CommandError, call_command,
                          ('addepub'), opts)

    def test_invalid_path(self):
        args = ["examples/invalid/not-found.epub"]
        opts = {}
        self.assertRaises(CommandError, call_command,
                          ('addepub'), opts)

    def test_invalid_zip(self):
        args = ["examples/invalid/not-a-zipfile.epub"]
        opts = {}
        self.assertRaises(CommandError, call_command,
                          ('addepub'), opts)

    def test_ignore_error(self):
        args = ["examples/invalid/"]
        opts = {"ignore_error": 1}
        call_command('addepub', *args, **opts)

