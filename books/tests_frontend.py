import os
from time import sleep
import unittest
import re

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command, CommandError
from django.urls import reverse_lazy


from django.contrib.auth.models import User

from books.models import Author

class PathagarBook(StaticLiveServerTestCase):
    ADMIN_USER = 'admin'
    ADMIN_PASS = 'pass'

    AUTHOR = "Anonymous"

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(2)

        self.adminuser = User.objects.create_user(self.ADMIN_USER, 'admin@test.com', self.ADMIN_PASS)
        self.adminuser.save()
        self.adminuser.is_staff = True
        self.adminuser.save()

        anonymous = Author(a_author=self.AUTHOR)
        anonymous.save()

    def tearDown(self):
        sleep(5)
        self.driver.close()

    def wait_url(self, url, timeout=5, regex=False):
        while timeout > 0:
            timeout -= 0.1
            if regex and re.match(url, self.driver.current_url):
                return
            elif url == self.driver.current_url:
                return
            sleep(0.1)
        raise TimeoutException("URL %s not reached (current URL: %s)" % (url, self.driver.current_url))

    def test_03_login(self):
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

        # sleep(1)
        self.wait_url(url)

        self.assertEqual(url, drv.current_url)

        # sleep(1)

        elem = drv.find_elements_by_xpath("//*[contains(text(), 'Add Book')]")[0]
        elem.send_keys(Keys.RETURN)

        fullpath = os.path.abspath("./examples/The Dunwich Horror.epub")
        self.assertTrue(os.path.isfile(fullpath))

        elem = drv.find_element_by_id("id_book_file")
        elem.send_keys(fullpath)

        elem = drv.find_element_by_id("id_a_title")
        elem.send_keys("The Dunwich Horror")

        elem = drv.find_element_by_id("id_a_author")
        elem.send_keys(self.AUTHOR)

        elem = drv.find_element_by_id("id_tags")
        elem.send_keys("selenium")

        elem = drv.find_element_by_id("id_a_summary")
        elem.send_keys("A little summary")

        elem = drv.find_element_by_xpath("//input[@value='Add']")
        elem.send_keys(Keys.RETURN)

        self.wait_url(r'^http://[a-zA-Z0-9:]+/book/\d+/view$', regex=True)


        latest_url = str(self.live_server_url) + str(reverse_lazy("latest"))
        drv.get(latest_url)
        self.wait_url(latest_url)

        elem = drv.find_elements_by_css_selector("h1.bookname > a")
        self.assertEqual(elem[0].text, "The Dunwich Horror")

        # Launch a simple search (from books)
        for term, results in [("xxxxxxx", []), ("Dunwich", ["The Dunwich Horror"])]:
            print(term)
            elem = drv.find_element_by_id("search")
            elem.clear()
            elem.send_keys(term)
            elem.submit()

            self.wait_url(r'.*?q=' + term, regex=True)

            founds = drv.find_elements_by_css_selector("h1.bookname > a")
            self.assertEqual(len(founds), len(results))
            if results:
                names = [x.text for x in founds]
                self.assertEqual(names, results)
