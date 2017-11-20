from hashlib import md5
import os
from time import sleep
from urllib.parse import quote_plus
from urllib.request import urlopen
import re

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import TimeoutException

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse_lazy
from django.contrib.auth.models import User

from books.models import Author, TagGroup


class PathagarBook(StaticLiveServerTestCase):
    ADMIN_USER = 'admin'
    ADMIN_PASS = 'pass'

    AUTHOR = "Anonymous"

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(2)

        self.adminuser = User.objects.create_user(self.ADMIN_USER,
                                                  'admin@test.com',
                                                  self.ADMIN_PASS)
        self.adminuser.save()
        self.adminuser.is_staff = True
        self.adminuser.save()

        # create anonymous author
        anonymous = Author(a_author=self.AUTHOR)
        anonymous.save()

        # create tag group
        group = TagGroup(name="myth", slug="myth")
        group.save()
        self.taggroups = ['lovecraft', 'cthulhu']
        group.tags.add(*self.taggroups)

    def tearDown(self):
        self.driver.close()

    def wait_url(self, url, timeout=5, regex=False):
        while timeout > 0:
            timeout -= 0.1
            if regex and re.match(url, self.driver.current_url):
                return
            elif url == self.driver.current_url:
                return
            sleep(0.1)
        raise TimeoutException("URL %s not reached (current URL: %s)" %
                               (url, self.driver.current_url))

    def remove_search_options(self):
        drv = self.driver
        # remove search options
        action = webdriver.ActionChains(drv)
        elem = drv.find_element_by_id("search")
        action.move_to_element(elem).perform()
        for key in ("search-author", "search-title"):
            chk = drv.find_element_by_id(key)
            if chk.get_attribute("checked"):
                chk.click()

    def book_search(self, args, option=None):
        drv = self.driver

        self.remove_search_options()

        for term, results in args:
            elem = drv.find_element_by_id("search")

            if option:
                # simulate a mouse hover
                action = webdriver.ActionChains(drv)
                action.move_to_element(elem).perform()

                chk = drv.find_element_by_id(option)
                if not chk.get_attribute('checked'):
                    chk.click()

            elem.clear()
            elem.send_keys(term)
            elem.submit()

            suffix = ''
            if option:
                suffix = '&%s=on' % option
            self.wait_url(r'.*?q=' + quote_plus(term) + suffix, regex=True)

            founds = drv.find_elements_by_css_selector("h1.bookname > a")
            self.assertEqual(len(founds), len(results))
            if results:
                names = [x.text for x in founds]
                self.assertEqual(names, results,
                    msg="Expected %s, found %s" % (str(results), str(names)))

    def author_search(self, args, option=None):
        drv = self.driver

        self.remove_search_options()

        for term, results in args:
            elem = drv.find_element_by_id("search")

            if option:
                # simulate a mouse hover
                action = webdriver.ActionChains(drv)
                action.move_to_element(elem).perform()

                chk = drv.find_element_by_id(option)
                if not chk.get_attribute('checked'):
                    chk.click()

            elem.clear()
            elem.send_keys(term)
            elem.submit()

            suffix = ''
            if option:
                suffix = '&%s=on' % option
            self.wait_url(r'.*?q=' + quote_plus(term) + suffix, regex=True)

            founds = drv.find_elements_by_css_selector(
                "h2.authorname > a > span")
            self.assertEqual(len(founds), len(results), msg="Failed to found %s" % term)
            if results:
                names = [x.text for x in founds]
                self.assertEqual(names, results,
                    msg="Expected %s, found %s" % (str(results), str(names)))

    def test_scenario_with_login(self):
        drv = self.driver
        drv.get(self.live_server_url)

        url = drv.current_url

        self.assertIn("Welcome to the Pathagar", drv.title)
        elem = drv.find_elements_by_xpath("//*[contains(text(), 'Log In')]")[0]
        elem.send_keys(Keys.RETURN)

        elem = drv.find_element_by_id("id_username")
        elem.send_keys(self.ADMIN_USER)
        elem = drv.find_element_by_id("id_password")
        elem.send_keys(self.ADMIN_PASS)
        elem.send_keys(Keys.RETURN)

        self.wait_url(url)

        self.assertEqual(url, drv.current_url)

        elem = drv.find_elements_by_xpath(
            "//*[contains(text(), 'Add Book')]")[0]
        elem.send_keys(Keys.RETURN)

        fullpath = os.path.abspath("./examples/valid/The Dunwich Horror.epub")
        md5file = md5(open(fullpath, 'rb').read()).hexdigest()
        self.assertTrue(os.path.isfile(fullpath))

        elem = drv.find_element_by_id("id_book_file")
        elem.send_keys(fullpath)

        elem = drv.find_element_by_id("id_a_title")
        elem.send_keys("The Dunwich Horror")

        elem = drv.find_element_by_id("id_a_author")
        elem.send_keys(self.AUTHOR)

        elem = drv.find_element_by_id("id_tags")
        tags = ["lovecraft", "horror", "Cthulhu"]
        elem.send_keys(" ".join(tags))
        # force tags to lowercase due to settings.TAGGIT_CASE_INSENSITIVE
        tags = [x.lower() for x in tags]

        elem = drv.find_element_by_id("id_a_summary")
        elem.send_keys("A little summary")

        elem = drv.find_element_by_xpath("//input[@value='Add']")
        elem.send_keys(Keys.RETURN)

        self.wait_url(r'^http://[a-zA-Z0-9:]+/book/\d+/view$', regex=True)

        # simulate a download
        elem = drv.find_elements_by_css_selector("a.download")
        link = elem[0].get_attribute('href')
        data = urlopen(link).read()
        md5download = md5(data).hexdigest()

        # check MD5
        self.assertEqual(md5download, md5file)

        # tags on detail book
        elem = drv.find_element_by_id("tags")
        elems = elem.find_elements_by_css_selector("a.button")
        items = [ x.text for x in elems ]
        self.assertEqual(sorted(items), sorted(tags))

        # book edit
        book_edit = str(self.live_server_url) + str(reverse_lazy("book_edit", kwargs={'pk': 1}))
        drv.get(book_edit)
        self.wait_url(book_edit)

        elem = drv.find_element_by_id("id_a_title")
        self.assertEqual(elem.get_attribute('value'), "The Dunwich Horror")

        elem = Select(drv.find_element_by_id("id_a_author"))
        self.assertEqual(elem.first_selected_option.text, self.AUTHOR)

        elem = drv.find_element_by_id("id_tags")
        items = [x.strip() for x in elem.get_attribute('value').split(',')]
        self.assertEqual(sorted(items), sorted(tags))

        elem = drv.find_element_by_id("id_a_summary")
        self.assertEqual(elem.get_attribute('value'), "A little summary")

        # check book is available in latest url
        latest_url = str(self.live_server_url) + str(reverse_lazy("latest"))
        drv.get(latest_url)
        self.wait_url(latest_url)

        elem = drv.find_elements_by_css_selector("h1.bookname > a")
        self.assertEqual(elem[0].text, "The Dunwich Horror")

        # check books list with invalid page number
        latest_url = str(self.live_server_url) + str(reverse_lazy("latest")) + "?page=9999"
        drv.get(latest_url)
        self.wait_url(latest_url)

        # check author list with invalid page number
        latest_url = str(self.live_server_url) + str(reverse_lazy("by_author")) + "?page=9999"
        drv.get(latest_url)
        self.wait_url(latest_url)

        latest_url = str(self.live_server_url) + str(reverse_lazy("latest"))
        drv.get(latest_url)
        self.wait_url(latest_url)

        # Search books
        self.book_search(
            [("xxxxxxx", []), ("Dunwich", ["The Dunwich Horror"]), ])

        self.book_search(
            [("title:Dunwich", ["The Dunwich Horror"]),
             ("author:" + self.AUTHOR, ["The Dunwich Horror"]),
             ("summary:little", ["The Dunwich Horror"]), ])

        self.book_search([("author:" + self.AUTHOR, ["The Dunwich Horror"]),
                          ("title:dunwich", ["The Dunwich Horror"]),
                          ("title:necronomicon", []),
                          ("summary:little", ["The Dunwich Horror"]),
                          ("lang:en", []),
                          ("publisher:xxxxxx", []),
                          ("identifier:50133", []), ],
                         option='search-all')

        self.book_search([("horror", ["The Dunwich Horror"]),
                          ("necronomicon1", [])],
                         option='search-title')

        self.book_search([(self.AUTHOR, ["The Dunwich Horror"]),
                          ("Arthur", [])],
                         option='search-author')

        # Search authors
        author_url = str(self.live_server_url) + str(reverse_lazy("by_author"))
        drv.get(author_url)
        self.wait_url(author_url)

        self.author_search([(self.AUTHOR[0:4], [self.AUTHOR]),
                            ("Dunwich", [self.AUTHOR]),
                            ('xxx', []), ])

        self.author_search(
            [("title:Dunwich", [self.AUTHOR]),
             ("author:" + self.AUTHOR[0:5], [self.AUTHOR]),
             ("summary:little", [self.AUTHOR]),
             ("lang:fr", []), ])

        self.author_search([("author:" + self.AUTHOR, [self.AUTHOR]),
                            ("title:dunwich", [self.AUTHOR]),
                            ("title:necronomicon", []),
                            ("summary:little", [self.AUTHOR])],
                           option='search-all')

        self.author_search([("horror", [self.AUTHOR]),
                            ("necronomicon1", [])],
                           option='search-title')

        self.author_search([(self.AUTHOR[0:5], [self.AUTHOR]),
                            ("Arthur", [])],
                           option='search-author')

        # Tags
        tags_url = str(self.live_server_url) + str(reverse_lazy("tags"))
        drv.get(tags_url)
        self.wait_url(tags_url)

        elem = drv.find_element_by_id("tags")
        elems = elem.find_elements_by_css_selector("a.button")
        items = [ x.text for x in elems ]
        links = [ x.get_attribute('href') for x in elems ]
        self.assertEqual(sorted(items), sorted(tags))

        # check now that book is available from each tags
        for link in links:
            drv.get(link)
            self.wait_url(link)

            elem = drv.find_elements_by_css_selector("h1.bookname > a")
            self.assertEqual(elem[0].text, "The Dunwich Horror")

        # Tags Groups
        tags_url = str(self.live_server_url) + str(reverse_lazy("tags"))
        drv.get(tags_url)
        self.wait_url(tags_url)

        elem = drv.find_element_by_id("taggroups")
        elems = elem.find_elements_by_css_selector("a.button")
        items = [ x.text for x in elems ]
        links = [ x.get_attribute('href') for x in elems ]
        self.assertEqual(sorted(items), ["myth"])

        # check now that tag is available from taggroup
        for link in links:
            drv.get(link)
            self.wait_url(link)

            elem = drv.find_element_by_id("tags")
            elems = elem.find_elements_by_css_selector("a.button")
            items = [ x.text for x in elems ]
            links = [ x.get_attribute('href') for x in elems ]
            self.assertEqual(sorted(items), sorted(self.taggroups))
