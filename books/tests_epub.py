import os

from django.test import TestCase
from django.core.management import call_command, CommandError

from books.epub import Epub
from books.models import Book


class EpubTest(TestCase):
    def test_simple_import(self):
        epub = Epub("examples/The Dunwich Horror.epub")
        info = epub.get_info()
        self.assertEqual(info.title, "The Dunwich Horror")
        self.assertEqual(info.creator, "H. P. Lovecraft")
        epub.close()

    def test_remove_temporary_dir(self):
        basedir = ''
        if True:
            epub = Epub("examples/The Dunwich Horror.epub")
            basedir = epub.get_basedir()
            del epub
        self.assertFalse(os.path.exists(basedir))

    def test_tags(self):
        epub = Epub("examples/Five Plays.epub")
        info = epub.get_info()
        self.assertEqual(info.subject, ['English drama'])
        epub.close()


class AddEpubTest(TestCase):
    def test_01_import_commandline(self):
        nb_book = len(Book.objects.all())
        self.assertEqual(nb_book, 0)

        args = ["examples/The Dunwich Horror.epub"]
        opts = {}
        call_command('addepub', *args, **opts)

        nb_book = len(Book.objects.all())
        self.assertEqual(nb_book, 1)

        book = Book.objects.get(pk=1)
        self.assertEqual(str(book.a_author), "H. P. Lovecraft")
        self.assertEqual(str(book.a_title), "The Dunwich Horror")

        args = ["examples/Five Plays.epub"]
        call_command('addepub', *args, **opts)

        book = Book.objects.get(pk=2)
        self.assertEqual(str(book.a_author), "Lord Dunsany")
        self.assertEqual(str(book.a_title), "Five Plays")
        tags = [str(x) for x in book.tags.all()]
        self.assertEqual(tags, ['English drama'])

    def test_02_import_duplicated(self):
        # try to import duplicated epub
        args = ["examples/The Dunwich Horror.epub"]
        opts = {}
        call_command('addepub', *args, **opts)
        self.assertRaises(CommandError, call_command,
                          ('addepub'), opts)
