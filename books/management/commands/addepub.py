from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.db.utils import IntegrityError

import os

from books.models import Language, Book, Status, Author, sha256_sum
from books.epub import Epub
from books.langlist import langs


def get_epubs(path):
    """Returns a list of EPUB(s)"""
    epub_list = []

    for root, dirs, files in os.walk(path):
        for name in files:
            if name.lower().endswith('.epub'):
                epub_list.append(os.path.join(root, name))

    return epub_list


class Command(BaseCommand):
    help = "Adds a book or a collection (via a directory containing EPUB files)"
    args = 'Absolute path to directory of EPUB files or EPUB file'

    def add_arguments(self, parser):
        parser.add_argument('--ignore-error',
                            action='store_true',
                            dest='ignore_error',
                            default=False,
                            help='Continue after error')
        parser.add_argument('--ignore-tags',
                            action='store_true',
                            dest='ignore_tags',
                            default=False,
                            help='Ignore tags from EPUB file')
        parser.add_argument('path', help='PATH')

    def handle(self, *args, **options):
        dirpath = options.get('path')
        dirpath = os.path.expanduser(os.path.expandvars(dirpath))
        if not os.path.exists(dirpath):
            raise CommandError("%r is not a valid path" % dirpath)

        if os.path.isdir(dirpath):
            names = get_epubs(dirpath)
        elif os.path.isfile(dirpath):
            names = [dirpath]
        else:
            raise CommandError("%r is not a valid path" % dirpath)

        for name in names:
            info = None
            try:
                e = Epub(name)
                info = e.get_info()
                e.close()
            except Exception as e:
                self.stdout.write(self.style.WARNING("The book {0} is not a valid epub filewas not saved: {1}".format(
                    os.path.basename(name), str(e))))
                if not options['ignore_error']:
                    raise CommandError(e)
                continue
            lang = Language.objects.filter(code=info.language)
            if not lang:
                for data in langs:
                    if data[0] == info.language:
                        lang = Language()
                        lang.label = data[1]
                        lang.save()
                        break
            else:
                lang = lang[0]

            #XXX: Hacks below
            info.title = info.title or os.path.splitext(os.path.basename(name))[0]
            info.summary = info.summary or ''
            info.creator = info.creator or 'Anonymous'
            info.rights = info.rights or ''
            info.date = info.date or ''
            if not info.identifier:
                info.identifier = {}
            if not info.identifier.get('value'):
                info.identifier['value'] = ''

            f = open(name, "rb")
            sha = sha256_sum(open(name, "rb"))
            pub_status = Status.objects.get(status='Published')
            author = Author.objects.get_or_create(a_author=info.creator)[0]
            book = Book(a_title=info.title,
                        a_author=author, a_summary=info.summary,
                        file_sha256sum=sha, a_rights=info.rights,
                        dc_identifier=info.identifier['value'].strip('urn:uuid:'),
                        dc_issued=info.date,
                        a_status=pub_status, mimetype="application/epub+zip")
            try:
                book.book_file.save(os.path.basename(name), File(f))
                book.validate_unique()
                book.save()
                if not options['ignore_tags']:
                    book.tags.add(*info.subject)
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING("The book {0} was not saved: {1}".format(book.book_file, str(e))))
                if not options['ignore_error']:
                    raise CommandError(e)
