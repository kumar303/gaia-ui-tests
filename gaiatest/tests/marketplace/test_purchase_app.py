# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import tempfile
import time

from gaiatest import GaiaTestCase
from marionette.keys import Keys

class TestPurchaseApp(GaiaTestCase):

    #MKT_NAME = 'localhost'
    #MKT_URL = 'http://localhost:8002/manifest.webapp'
    MKT_NAME = 'Marketplace Dev'
    MKT_URL = 'https://marketplace-dev.allizom.org/manifest.webapp'
    MKT_INSTALLED = False
    APP_NAME = 'Private Yacht'
    APP_INSTALLED = False

    _loading_fragment_locator = ('css selector', 'div.loading-fragment')

    # Marketplace search on home page
    _search_locator = ('id', 'search-q')

    # Marketplace search results area and a specific result item
    _search_results_area_locator = ('id', 'search-results')
    _search_result_locator = ('css selector', '#search-results li.item')

    # Marketplace result app name, author, and install button
    _app_name_locator = ('xpath', '//h3')
    _install_button = ('css selector', '.button.product')

    # System app confirmation button to confirm installing an app
    _yes_button_locator = ('id', 'app-install-install-button')

    # Label identifier for all homescreen apps
    _app_icon_locator = ('xpath', "//li[@class='icon']//span[text()='%s']" % APP_NAME)
    _homescreen_iframe_locator = ('css selector', 'div.homescreen iframe')

    # App install popup
    _yes_button_locator = ('id', 'app-install-install-button')
    _notification_banner_locator = ('id', 'system-banner')

    def setUp(self):
        GaiaTestCase.setUp(self)

        if self.wifi:
            self.data_layer.enable_wifi()
            self.data_layer.connect_to_wifi(self.testvars['wifi'])

        apps = set(a['manifest']['name'] for a in self.apps.get_installed())
        if self.MKT_NAME not in apps:
            self.install_mkt_dev()

        # launch the app
        self.app = self.apps.launch(self.MKT_NAME)

    def setUpDevice(self):
        # Push payment test settings to the device.
        # This is a temporary workaround until prefs land in:
        # https://bugzilla.mozilla.org/show_bug.cgi?id=855143
        self.device.stop_b2g()
        try:
            dest = '/data/local/user.js'
            mgr = self.device.manager
            src = []
            if mgr.fileExists(dest):
                for line in mgr.catFile(dest).splitlines():
                    src.append(line)
            with open(os.path.join(os.path.dirname(__file__),
                                   'payment-prefs.js')) as f:
                for line in f.readlines():
                    if line not in src:
                        src.append(line.strip())
            with tempfile.NamedTemporaryFile() as f:
                f.write('\n'.join(src))
                f.flush()
                mgr.pushFile(f.name, dest)
        finally:
            self.device.start_b2g()

    def install_mkt_dev(self):
        self.marionette.switch_to_frame()
        self.marionette.execute_script(
            'navigator.mozApps.install("%s")' % self.MKT_URL)

        # click YES on the installation dialog and wait for icon displayed
        self.wait_for_element_displayed(*self._yes_button_locator)
        yes = self.marionette.find_element(*self._yes_button_locator)
        self.marionette.tap(yes)

        # wait for the app to be installed and the notification banner to be available
        self.wait_for_element_displayed(*self._notification_banner_locator)

        self.MKT_INSTALLED = True

    def test_search_and_install_app(self):
        # select to search for an app

        self.wait_for_element_not_displayed(*self._loading_fragment_locator)

        search_box = self.marionette.find_element(*self._search_locator)

        if not search_box.is_displayed():
            # Scroll a little to make the search box appear
            self.marionette.execute_script('window.scrollTo(0, 10)')

        # search for the app
        search_box.send_keys(self.APP_NAME)
        search_box.send_keys(Keys.RETURN)

        # validate the first result is the app
        self.wait_for_element_displayed(*self._search_results_area_locator)
        results = self.marionette.find_elements(*self._search_result_locator)
        self.assertGreater(len(results), 0, 'no results found')
        app_name = results[0].find_element(*self._app_name_locator)
        self.assertEquals(app_name.text, self.APP_NAME, 'First app has wrong name')

        # Find and click the purchase button to the install the web app
        purchase_button = results[0].find_element(*self._install_button)
        self.assertEquals(purchase_button.text, '$0.99', 'incorrect button label')

        # TODO: Fix this. The tap only rarely works.
        self.marionette.tap(purchase_button)
        print 'click the sign in button now!!!'
        time.sleep(5)

        self._login_to_persona(self.testvars['marketplace']['username'],
                               self.testvars['marketplace']['password'])

        # Confirm the installation of the web app
        self.marionette.switch_to_frame()

        self.wait_for_element_displayed(*self._yes_button_locator)
        yes_button = self.marionette.find_element(*self._yes_button_locator)
        self.marionette.tap(yes_button)
        self.wait_for_element_not_displayed(*self._yes_button_locator)

        self.APP_INSTALLED = True

        homescreen_frame = self.marionette.find_element(*self._homescreen_iframe_locator)
        self.marionette.switch_to_frame(homescreen_frame)

        # Wait for app's icon to appear on the homescreen
        self.wait_for_element_present(*self._app_icon_locator)

    def _login_to_persona(self, username, password):

        _persona_frame_locator = ('css selector', "iframe")

        # Trusty UI on home screen
        _tui_container_locator = ('id', 'trustedui-frame-container')

        # Persona dialog
        _waiting_locator = ('css selector', 'body.waiting')
        _email_input_locator = ('id', 'authentication_email')
        _password_input_locator = ('id', 'authentication_password')
        _next_button_locator = ('css selector', 'button.start')
        _returning_button_locator = ('css selector', 'button.returning')
        _sign_in_button_locator = ('id', 'signInButton')
        _this_session_only_button_locator = ('id', 'this_is_not_my_computer')
        # I also tried:
        # _this_session_only_button_locator = ('css selector', '#your_computer_content li:nth-child(2)')

        # Switch to top level frame then Persona frame
        self.marionette.switch_to_frame()
        self.wait_for_element_present(*_tui_container_locator)
        trustyUI = self.marionette.find_element(*_tui_container_locator)
        self.wait_for_condition(lambda m: trustyUI.find_element(*_persona_frame_locator))
        personaDialog = trustyUI.find_element(*_persona_frame_locator)
        self.marionette.switch_to_frame(personaDialog)

        # Wait for the loading to complete
        self.wait_for_element_not_present(*_waiting_locator)

        if self.marionette.find_element(*_email_input_locator).is_displayed():
            # Persona has no memory of your details ie after device flash
            email_field = self.marionette.find_element(*_email_input_locator)
            email_field.send_keys(username)
            email_field.send_keys(Keys.RETURN)

            self.wait_for_element_displayed(*_password_input_locator)
            password_field = self.marionette.find_element(*_password_input_locator)
            password_field.send_keys(password)

            self.wait_for_element_displayed(*_returning_button_locator)
            # only click() works
            # self.marionette.tap(self.marionette.find_element(*_returning_button_locator))
            self.marionette.find_element(*_returning_button_locator).click()

        else:
            # Persona remembers your username and password
            self.marionette.tap(self.marionette.find_element(*_sign_in_button_locator))

            # Sometimes it prompts for "Remember Me?"
            # If it does, tell it to remember you for this session only
            # TODO: Find out actual logic behind when it prompts or not
            try:
                print 'click the This Session Only button now (if you see it)!!!'
                time.sleep(5)
                this_session_only_button = self.marionette.find_element(*_this_session_only_button_locator)
                # TODO: neither of the next two lines work
                self.marionette.tap(this_session_only_button)
                this_session_only_button.click()
            except:
                pass

    def tearDown(self):

        if self.MKT_INSTALLED:
            self.apps.uninstall(self.MKT_NAME)

        if self.APP_INSTALLED:
            self.apps.uninstall(self.APP_NAME)

        GaiaTestCase.tearDown(self)
