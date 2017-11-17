# Copyright (C) 2010, One Laptop Per Child
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.core.files import File

from django.db import transaction
from django.db.utils import IntegrityError

import csv
import json
import logging
import os
import sys
from optparse import make_option

from books.models import Author, Book, Status, sha256_sum

logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.DEBUG)


def resolve_path(inputdir, book):
    # check if file is located in same directory as input file
    if not os.path.exists(book):
        # check if file is located in same directory as CSV
        book = os.path.join(inputdir, book)
    return book


class Command(BaseCommand):
    help = "Adds a book collection (via a CSV file)"
    args = 'Absolute path to CSV file'

    def add_arguments(self, parser):
        parser.add_argument('--json',
                            action='store_true',
                            dest='is_json_format',
                            default=False,
                            help='The file is in JSON format')
        parser.add_argument('filepath',
                            help='PATH')

    def _handle_csv(self, csvpath):
        """
        Store books from a file in CSV format.
        WARN: does not handle tags

        """

        csvfile = open(csvpath)
        # Sniffer fais to detect a CSV created with DictWriter with default Dialect (excel) !
        # dialect = csv.Sniffer().sniff(csvfile.read(32000))
        # csvfile.seek(0)
        dialect = 'excel'
        reader = csv.reader(csvfile)  # , dialect)

        # TODO: Figure out if this is a valid CSV file

        status_published = Status.objects.get(status='Published')

        inputdir = os.path.dirname(csvpath)

        for row in reader:
            if len(row) < 4:
                raise CommandError("Invalid CSV file, not enought fields")
            path = row[0]
            title = row[1]
            author = row[2]
            summary = row[3]

            path = resolve_path(inputdir, path)

            if not os.path.exists(path):
                print("FILE NOT FOUND '%s'" % path)
                continue

            sha = sha256_sum(open(path, "rb"))
            f = open(path, 'rb')

            a_author = Author.objects.get_or_create(a_author=author)[0]
            book = Book(a_title=title, a_author=a_author, file_sha256sum=sha,
                        a_summary=summary, a_status=status_published)
            try:
                book.book_file.save(os.path.basename(path), File(f))
                book.validate_unique()
                with transaction.atomic():
                    book.save()
            except IntegrityError as e:
                print("EXCEPTION SAVING FILE '%s': %s" % (
                    path, str(e)))

    def _handle_json(self, jsonpath):
        """
        Store books from a file in JSON format.

        """
        jsonfile = open(jsonpath)
        data_list = json.loads(jsonfile.read())

        status_published = Status.objects.get(status='Published')
        stats = dict(total=0, errors=0, skipped=0, imported=0)
        inputdir = os.path.dirname(jsonpath)

        for d in data_list:
            stats['total'] += 1
            logger.debug('read item %s' % json.dumps(d))

            # Skip unless there is book content
            if 'book_path' not in d:
                stats['skipped'] += 1
                logger.warn('No "book_path" field')
                continue

            book_path = resolve_path(inputdir, d['book_path'])
            del d['book_path']

            # Skip unless there is book content
            if not os.path.exists(book_path):
                stats['skipped'] += 1
                logger.warn('Book file not available %s' % (book_path))
                continue

            # Get a Django File from the given path:
            d['file_sha256sum'] = sha256_sum(open(book_path, "rb"))
            f = open(book_path, 'rb')

            if 'cover_path' in d:
                cover_path = resolve_path(inputdir, d['cover_path'])
                if os.path.exists(cover_path):
                    f_cover = open(cover_path, 'rb')
                    d['cover_img'] = File(f_cover)
                del d['cover_path']

            if 'a_status' in d:
                d['a_status'] = Status.objects.get(status=d['a_status'])
            else:
                d['a_status'] = status_published

            a_author = d.get('a_author', 'Anonymous')
            d['a_author'] = Author.objects.get_or_create(a_author=a_author)[0]

            d.setdefault('a_title', os.path.splitext(os.path.basename(book_path))[0])

            tags = d.pop('tags', [])

            book = Book(**d)
            try:
                book.book_file.save(os.path.basename(book_path), File(f))
                book.validate_unique()  # Throws ValidationError if not unique

                with transaction.atomic():
                    book.save()  # must save item to generate Book.id before creating tags
                    [book.tags.add(tag) for tag in tags if tag]
                    book.save()  # save again after tags are generated
                    stats['imported'] += 1
            except ValidationError as e:
                stats['skipped'] += 1
                logger.info('Book already imported, skipping title="%s"' % book.a_title)
            except Exception as e:
                stats['errors'] += 1
                # Likely a bug
                logger.warn('Error adding book title="%s": %s' % (
                    book.a_title, str(e)))

        logger.info("addbooks complete total=%(total)d imported=%(imported)d skipped=%(skipped)d errors=%(errors)d" % stats)

    def handle(self, *args, **options):
        filepath = options.get('filepath')
        if not os.path.exists(filepath):
            raise CommandError("%r is not a valid path" % filepath)

        filepath = os.path.abspath(filepath)
        if options['is_json_format']:
            self._handle_json(filepath)
        else:
            self._handle_csv(filepath)
