from lxml import etree

from django.test import TestCase, Client
from django.core.management import call_command, CommandError
from django.urls import reverse_lazy

from books.epub import Epub
from books.models import Book, Author, TagGroup


class OpfsTest(TestCase):
    def setUp(self):
        nb_book = len(Book.objects.all())
        self.assertEqual(nb_book, 0)

        args = ["examples/valid/The Dunwich Horror.epub"]
        opts = {}
        call_command('addepub', *args, **opts)

        # append tags to book
        book = Book.objects.get(pk=1)
        book.tags.add("horror")

        # create a taggroup
        group = TagGroup(name='lovecraft', slug='lovecraft')
        group.save()
        group.tags.add("horror")


    def test_simple_opds_feed(self):
        c = Client()

        for opds in ('latest_feed', 'root_feed', 'by_author_feed',
                     'by_title_feed', 'most_downloaded_feed',
                     'tags_listgroups', 'tags_feed'):
            d = c.get(reverse_lazy(opds))
            parser = etree.fromstring(d.content)

    def test_with_parameters(self):
        c = Client()

        # by author
        d = c.get(reverse_lazy('by_title_author_feed',
            kwargs=dict(author_id=1)))
        parser = etree.fromstring(d.content)

        # by tag_feed_atom, with unknow tag
        d = c.get(reverse_lazy('by_tag_feed',
            kwargs={'tag': 'xxxx'}))
        self.assertEqual(d.status_code, 404)

        # by tag_feed_atom, with known tag
        d = c.get(reverse_lazy('by_tag_feed',
            kwargs={'tag': 'horror'}))
        parser = etree.fromstring(d.content)

        d = c.get(reverse_lazy('tag_groups_feed', kwargs={'group_slug': 'lovecraft'}))
        parser = etree.fromstring(d.content)
