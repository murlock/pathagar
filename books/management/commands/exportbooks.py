# Copyright (C) 2010, One Laptop Per Child
# Copyright (C) 2017, Michael Bonfils
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
import shutil
import sys
from optparse import make_option

from books.models import Book, Status

logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.DEBUG)

class Command(BaseCommand):
    help = "Dump collection in directory (CSV)"
    args = 'Directory Path'

    def add_arguments(self, parser):
        parser.add_argument('--copy',
                            action='store_true',
                            dest='copy_file',
                            default=False,
                            help='Copy book')
        parser.add_argument('filepath',
                            help='PATH')


    def _handle_csv(self, csvpath, *args, **options):
        """
        Export books into directory with CSV catalog
        WARN: does not handle tags

        """

        csvfile = open(csvpath, "w")
        outputdir = os.path.basename(csvpath)
        do_copy = options.get('copy_file')

        writer = csv.writer(csvfile)

        for book in Book.objects.all(): #[0:5]:
            path = book.book_file.path
            if do_copy:
                shutil.copy(path, outputdir)
                path = os.path.basename(path)

            entry = [path, book.a_title, book.a_author.a_author, book.a_summary]
            writer.writerow(entry)
        csvfile.close()


    def handle(self, filepath, *args, **options):
        self._handle_csv(filepath, *args, **options)

