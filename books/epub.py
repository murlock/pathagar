# Copyright 2009 One Laptop Per Child
# Author: Sayamindu Dasgupta <sayamindu@laptop.org>
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

import zipfile
import tempfile
import os
from lxml import etree
import shutil

from books import epubinfo


class Epub(object):
    def __init__(self, _file):
        """
        _file: can be either a path to a file (a string) or a file-like object.
        """
        self._file = _file
        self._zobject = None
        self._opfpath = None
        self._ncxpath = None
        self._basepath = None

        self._verify()

        self._get_opf()
        self._get_ncx()

        opffile = self._zobject.open(self._opfpath)
        self._info = epubinfo.EpubInfo(opffile)

    def __del__(self):
        self.close()

    def _get_opf(self):
        containerfile = self._zobject.open('META-INF/container.xml')

        tree = etree.parse(containerfile)
        root = tree.getroot()

        for element in root.iterfind('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile'):
            if element.get('media-type') == 'application/oebps-package+xml':
                self._opfpath = element.get('full-path')

        if self._opfpath.rpartition('/')[0]:
            self._basepath = self._opfpath.rpartition('/')[0] + '/'
        else:
            self._basepath = ''

        containerfile.close()

    def _get_ncx(self):
        opffile = self._zobject.open(self._opfpath)

        tree = etree.parse(opffile)
        root = tree.getroot()

        spine = root.find('.//{http://www.idpf.org/2007/opf}spine')
        tocid = spine.get('toc')

        for element in root.iterfind('.//{http://www.idpf.org/2007/opf}item'):
            if element.get('id') == tocid:
                self._ncxpath = self._basepath + element.get('href')

        opffile.close()

    def _verify(self):
        '''
        Method to crudely check to verify that what we
        are dealing with is a epub file or not
        '''
        if isinstance(self._file, str):
            self._file = os.path.abspath(self._file)
            if not os.path.exists(self._file):
                raise FileNotFoundError("No such file: %s" % self._file)

        self._zobject = zipfile.ZipFile(self._file)
        # force a testzip to ensure that Zip is valid
        # it was done by extraction step before
        self._zobject.testzip()

        if not 'mimetype' in self._zobject.namelist():
            raise ValueError("Invalid EPUB file, mimetype is not available")

        mtypefile = self._zobject.open('mimetype')
        mimetype = mtypefile.readline().decode('utf-8')

        # Some files seem to have trailing characters
        if not mimetype.startswith('application/epub+zip'):
            raise ValueError("EPUB file has invalid mimetype: %s" % mimetype)

    def get_info(self):
        '''
        Returns a EpubInfo object for the open Epub file
        '''
        return self._info

    def get_cover_image(self):
        '''
        Returns a tuple file like object, name extension
        '''
        if self._info.cover_image is None:
            return None, None
        names = self._zobject.namelist()
        img = self._info.cover_image
        ext = os.path.splitext(img)[1]
        assert not img.startswith('/')
        for subdir in [self._basepath, '']:
            path = os.path.join(subdir, img)
            if path in names:
                return self._zobject.open(path), ext
        return None, None

    def close(self):
        '''
        Cleans up (closes open zip files and deletes uncompressed content of Epub.
        Please call this when a file is being closed or during application exit.
        '''
        if self._zobject:
            self._zobject.close()
        self._zobject = None
