#!/usr/bin/python
#
# CDDL HEADER START
#
# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License").
# You may not use this file except in compliance with the License.
#
# You can obtain a copy of the license at usr/src/OPENSOLARIS.LICENSE
# or http://www.opensolaris.org/os/licensing.
# See the License for the specific language governing permissions
# and limitations under the License.
#
# When distributing Covered Code, include this CDDL HEADER in each
# file and include the License file at usr/src/OPENSOLARIS.LICENSE.
# If applicable, add the following below this CDDL HEADER, with the
# fields enclosed by brackets "[]" replaced with your own identifying
# information: Portions Copyright [yyyy] [name of copyright owner]
#
# CDDL HEADER END
#
# Copyright 2010 Sun Microsystems, Inc.  All rights reserved.
# Use is subject to license terms.
#

# Location for themable icons
ICON_LOCATION = "usr/share/package-manager/icons"

import locale
import os
import sys
import gettext
try:
        import gobject
        import gtk
        import pango
except ImportError:
        sys.exit(1)
import pkg.misc as misc
import pkg.gui.misc as gui_misc
import pkg.gui.progress as progress
import pkg.client.api_errors as api_errors
import pkg.gui.installupdate as installupdate
import pkg.gui.enumerations as enumerations
import pkg.gui.repository as repository
import pkg.fmri as fmri
from pkg.client import global_settings
from gettext import ngettext
logger = global_settings.logger
       
debug = False

class Webinstall:
        def __init__(self, image_dir):
                global_settings.client_name = gui_misc.get_wi_name()
                self.image_dir = image_dir
    
                try:
                        self.application_dir = os.environ["PACKAGE_MANAGER_ROOT"]
                except KeyError:
                        self.application_dir = "/"
                misc.setlocale(locale.LC_ALL, "")
                for module in (gettext, gtk.glade):
                        module.bindtextdomain("pkg", os.path.join(
                            self.application_dir,
                            "usr/share/locale"))
                        module.textdomain("pkg")
                gui_misc.init_for_help(self.application_dir)
                self.pub_pkg_list = None
                self.pr = progress.NullProgressTracker()
                self.pub_new_tasks = []
                self.pkg_install_tasks = []
                self.icon_theme = gtk.icon_theme_get_default()
                icon_location = os.path.join(self.application_dir, ICON_LOCATION)
                self.icon_theme.append_search_path(icon_location)
                self.param = None
                self.preferred = None
                self.disabled_pubs = {}
                self.repo_gui = None
                self.first_run = True

                # Webinstall Dialog
                self.gladefile = os.path.join(self.application_dir,
                        "usr/share/package-manager/packagemanager.glade")
                w_xmltree_webinstall = gtk.glade.XML(self.gladefile, "webinstalldialog")
                self.w_webinstall_dialog = \
                        w_xmltree_webinstall.get_widget("webinstalldialog")
                
                self.w_webinstall_proceed = \
                        w_xmltree_webinstall.get_widget("proceed_button")
                self.w_webinstall_cancel = \
                        w_xmltree_webinstall.get_widget("cancel_button")
                self.w_webinstall_close = \
                        w_xmltree_webinstall.get_widget("close_button")
                self.w_webinstall_proceed_label = \
                        w_xmltree_webinstall.get_widget("proceed_new_repo_label")
                self.w_webinstall_toplabel = \
                        w_xmltree_webinstall.get_widget("webinstall_toplabel")
                self.w_webinstall_frame = \
                        w_xmltree_webinstall.get_widget("webinstall_frame")
                self.w_webinstall_image = \
                        w_xmltree_webinstall.get_widget("pkgimage")
                self.window_icon = gui_misc.get_icon(self.icon_theme, 
                    'packagemanager', 48)
                self.w_webinstall_image.set_from_pixbuf(self.window_icon)
                self.w_webinstall_info_label = \
                        w_xmltree_webinstall.get_widget("label19")

                self.w_webinstall_textview = \
                        w_xmltree_webinstall.get_widget("webinstall_textview")  
                infobuffer = self.w_webinstall_textview.get_buffer()
                infobuffer.create_tag("bold", weight=pango.WEIGHT_BOLD)
                infobuffer.create_tag("disabled", foreground="#757575") #Close to DimGrey

                try:
                        dic = \
                            {
                                "on_webinstalldialog_close": \
                                    self.__on_webinstall_dialog_close,
                                "on_cancel_button_clicked": \
                                    self.__on_cancel_button_clicked,
                                "on_help_button_clicked": \
                                    self.__on_help_button_clicked,
                                "on_proceed_button_clicked": \
                                    self.__on_proceed_button_clicked,
                            }
                        w_xmltree_webinstall.signal_autoconnect(dic)


                except AttributeError, error:
                        print _("GUI will not respond to any event! %s. "
                            "Check webinstall.py signals") % error
 
                self.w_webinstall_dialog.set_icon(self.window_icon)
                self.api_o = gui_misc.get_api_object(self.image_dir, self.pr,
                    self.w_webinstall_dialog)
                gui_misc.setup_logging(gui_misc.get_wi_name())
        
        def __output_new_pub_tasks(self, infobuffer, textiter, num_tasks):
                if num_tasks == 0:
                        return
                msg = ngettext(
                    "\n Add New Publisher\n", "\n Add New Publishers\n", num_tasks)
                infobuffer.insert_with_tags_by_name(textiter, msg, "bold")
                self.__output_pub_tasks(infobuffer, textiter, self.pub_new_tasks)

        def __nothing_todo(self, infobuffer, textiter):
                self.w_webinstall_proceed.hide()
                self.w_webinstall_cancel.hide()
                self.w_webinstall_frame.hide()
                self.w_webinstall_toplabel.set_text(
                    _("All specified publishers are already on the system."))
                self.w_webinstall_close.show()
                self.w_webinstall_close.grab_focus()

        @staticmethod
        def __output_pub_tasks(infobuffer, textiter, pub_tasks):
                for pub_info in pub_tasks:
                        if pub_info == None:
                                continue
                        infobuffer.insert_with_tags_by_name(textiter,
                            _("\t%s ") % pub_info.prefix, "bold")
                        repo = pub_info.selected_repository
                        if repo != None:
                                infobuffer.insert(textiter,
                                        _(" (%s)\n") % repo.origins[0].uri)

        def __output_pkg_install_tasks(self, infobuffer, textiter, num_tasks):
                if num_tasks == 0:
                        return                        
                msg = ngettext(
                    "\n Install Package\n", "\n Install Packages\n", num_tasks)
                infobuffer.insert_with_tags_by_name(textiter, msg, "bold")
                for entry in self.pkg_install_tasks:
                        pub_info = entry[0]
                        packages = entry[1]
                        if len(packages) > 0:
                                if self.disabled_pubs and \
                                        pub_info.prefix in self.disabled_pubs:
                                        infobuffer.insert_with_tags_by_name(textiter,
                                            _("\t%s (disabled)\n") % pub_info.prefix,
                                            "bold", "disabled")
                                else:
                                        infobuffer.insert_with_tags_by_name(textiter,
                                            "\t%s\n" % pub_info.prefix, "bold")
                                for pkg in packages:
                                        infobuffer.insert(textiter,
                                            "\t\t%s\n" % fmri.extract_pkg_name(pkg))
                                
        def process_param(self, param=None):
                if param == None or self.api_o == None:
                        self.w_webinstall_proceed.set_sensitive(False)
                        self.w_webinstall_cancel.grab_focus()
                        return
                self.param = param
                self.pub_pkg_list = self.api_parse_publisher_info()
                self.__create_task_lists()        
                infobuffer = self.w_webinstall_textview.get_buffer()
                infobuffer.set_text("")
                
                num_new_pub = len(self.pub_new_tasks)
                num_install_tasks = 0
                for entry in self.pkg_install_tasks:
                        packages = entry[1]
                        num_install_tasks += len(packages)

                self.__set_proceed_label(num_new_pub)
                textiter = infobuffer.get_end_iter()
                if num_new_pub == 0 and num_install_tasks == 0:
                        self.__nothing_todo(infobuffer, textiter)
                        self.w_webinstall_dialog.present()
                        self.w_webinstall_dialog.resize(450, 100)
                        return
                else:
                        gui_misc.change_stockbutton_label(self.w_webinstall_proceed,
                            _("_Proceed"))
                        self.w_webinstall_dialog.show_all()
                        self.w_webinstall_dialog.resize(450, 370)
                        
                self.__output_new_pub_tasks(infobuffer, textiter, num_new_pub)
                self.__output_pkg_install_tasks(infobuffer, textiter, num_install_tasks)

                infobuffer.place_cursor(infobuffer.get_start_iter())
                self.w_webinstall_proceed.grab_focus()
                                
        def __set_proceed_label(self, num_new_pub):
                if num_new_pub == 0:
                        self.w_webinstall_proceed_label.hide()
                else:
                        msg = ngettext(
                            "Click Proceed <b>only</b> if you trust this new "
                                "publisher ",
                            "Click Proceed <b>only</b> if you trust these new "
                                "publishers ",
                            num_new_pub)
                        self.w_webinstall_proceed_label.set_markup(msg)

        def __on_webinstall_dialog_close(self, widget, param=None):
                self.__exit_app()

        def __on_cancel_button_clicked(self, widget):
                self.__exit_app()

        @staticmethod
        def __on_help_button_clicked(widget):
                gui_misc.display_help("webinstall")

        def __exit_app(self, be_name = None):
                gui_misc.shutdown_logging()
                self.w_webinstall_dialog.destroy()
                gtk.main_quit()
                sys.exit(0)
                return

        def __create_task_lists(self):
                pub_new_reg_ssl_tasks = []
                self.pub_new_tasks = []
                self.pkg_install_tasks = []
                for entry in self.pub_pkg_list:
                        pub_info = entry[0]
                        packages = entry[1]
                        if not pub_info:
                                continue

                        repo = pub_info.repositories

                        pub_registered = self.__is_publisher_registered(pub_info.prefix)
                        if pub_registered and packages != None and len(packages) > 0 and \
                                self.__check_publisher_disabled(pub_info.prefix):
                                self.disabled_pubs[pub_info.prefix] = True

                        if not pub_registered:
                                if len(repo) > 0 and repo[0].origins[0] != None and \
                                    repo[0].origins[0].scheme == "https":
                                        #TBD: check for registration uri as well as scheme
                                        #    repo.registration_uri.uri != None:
                                        pub_new_reg_ssl_tasks.append(pub_info)
                                else:
                                        self.pub_new_tasks.append(pub_info)
                        if packages != None and len(packages) > 0:
                                self.pkg_install_tasks.append((pub_info, packages))
                self.pub_new_tasks = pub_new_reg_ssl_tasks + self.pub_new_tasks
                if len(self.pub_new_tasks) > 0 or len(self.disabled_pubs) > 0 and \
                        self.repo_gui == None:
                        self.repo_gui = repository.Repository(self, self.image_dir,
                            webinstall_new=True, main_window = self.w_webinstall_dialog)
                            
        def __check_publisher_disabled(self, name):
                try:
                        if self.api_o == None:
                                return
                        try:
                                pub = self.api_o.get_publisher(name)
                                if pub != None and pub.disabled:
                                        return True
                        except api_errors.UnknownPublisher:
                                return False
                except api_errors.PublisherError, ex:
                        gobject.idle_add(gui_misc.error_occurred,
                            self.w_webinstall_dialog,
                            str(ex),
                            _("Publisher Error"))
                except api_errors.ApiException, ex:
                        gobject.idle_add(gui_misc.error_occurred, 
                            self.w_webinstall_dialog, 
                            str(ex), _("Web Installer Error"))
                return False

        def __disabled_pubs_info(self, disabled_pubs):
                if len(disabled_pubs) == 0:
                        return
                num = len(disabled_pubs)       
                msg = ngettext(
                    "The following publisher is disabled:\n",
                    "The following publishers are disabled:\n", num)
                        
                for pub in disabled_pubs:
                        msg += _("\t<b>%s</b>\n") % pub
                        
                msg += ngettext(
                    "\nClicking OK will enable the publisher before proceeding with "
                    "install. On completion it will be disabled again.",
                    "\nClicking OK will enable the publishers before proceeding with "
                    "install.\nOn completion they will be disabled again.",
                    num)
                        
                msgbox = gtk.MessageDialog(
                    parent = self.w_webinstall_dialog,
                    buttons = gtk.BUTTONS_OK_CANCEL,
                    flags = gtk.DIALOG_MODAL, type = gtk.MESSAGE_INFO,
                    message_format = None)
                msgbox.set_markup(msg)
                title = ngettext("Disabled Publisher", "Disabled Publishers", 
                    len(disabled_pubs))
                msgbox.set_title(title)
                msgbox.set_default_response(gtk.RESPONSE_OK)               
                
                response = msgbox.run()
                if response == gtk.RESPONSE_OK:
                        gobject.idle_add(self.__proceed)
                msgbox.destroy()
                return

        def __is_publisher_registered(self, name):
                try:
                        if self.api_o != None and self.api_o.has_publisher(name):
                                return True
                except api_errors.PublisherError, ex:
                        gobject.idle_add(gui_misc.error_occurred, 
                            self.w_webinstall_dialog, 
                            str(ex), _("Publisher Error"))
                except api_errors.ApiException, ex:
                        gobject.idle_add(gui_misc.error_occurred, 
                            self.w_webinstall_dialog, 
                            str(ex), _("Web Installer Error"))
                return False

        def __on_proceed_button_clicked(self, widget):
                if not self.first_run:
                        try:
                                self.api_o.reset()
                        except api_errors.ApiException, ex:
                                gobject.idle_add(gui_misc.error_occurred, 
                                    self.w_webinstall_dialog, 
                                    str(ex), _("Web Installer Error"))
                                return
                        self.pub_pkg_list = self.api_parse_publisher_info()
                        self.__create_task_lists()
                else:
                        self.first_run = False
                if self.disabled_pubs and len(self.disabled_pubs) > 0:
                        self.__disabled_pubs_info(self.disabled_pubs)
                else:
                        self.__proceed()

        def __proceed(self):
                if len(self.disabled_pubs) > 0 and self.repo_gui:
                        self.repo_gui.webinstall_enable_disable_pubs(
                            self.w_webinstall_dialog, self.disabled_pubs, True)
                        return
                if len(self.pub_new_tasks) > 0:
                        self.__add_new_pub()
                        return
                if len(self.pkg_install_tasks) > 0:
                        self.__install_pkgs()
                        return
                        
        def __add_new_pub(self):
                if len(self.pub_new_tasks) == 0:
                        return
                pub = self.pub_new_tasks[0]
                if debug:
                        print("Add New Publisher:\n\tName: %s" % pub.prefix)
                        repo = pub.selected_repository
                        print("\tURL: %s" % repo.origins[0].uri)

                repo = pub.selected_repository
                if repo and len(repo.origins) > 0 and self.repo_gui:
                        self.repo_gui.webinstall_new_pub(self.w_webinstall_dialog, pub)
                else:
                        msg = _("Failed to add %s.\n") % pub
                        msg += _("No URI specified")
                        gui_misc.error_occurred( 
                                    self.w_webinstall_dialog,
                                    msg, _("Publisher Error"))

        # Publisher Callback
        # invoked at end of adding a publisher and enabling/disabling a set of publishers
        def reload_packages(self, added_pub=True):
                if len(self.pub_new_tasks) > 0:
                        if added_pub:
                                self.pub_new_tasks.pop(0)
                        if len(self.pub_new_tasks) > 0:
                                self.__add_new_pub()
                                return

                if len(self.pkg_install_tasks) > 0:
                        self.api_o = gui_misc.get_api_object(self.image_dir, self.pr,
                            self.w_webinstall_dialog)
                        self.__install_pkgs()
                else:
                        self.__exit_app()
                
        def __install_pkgs(self):
                if len(self.pkg_install_tasks) == 0:
                        return
                # Handle all packages from all pubs as single install action
                try:
                        pref_pub = self.api_o.get_preferred_publisher()
                except api_errors.PublisherError, ex:
                        gobject.idle_add(gui_misc.error_occurred,
                            self.w_webinstall_dialog,
                            str(ex),
                            _("Publisher Error"))
                        return
                except api_errors.ApiException, ex:
                        gobject.idle_add(gui_misc.error_occurred,
                            self.w_webinstall_dialog,
                            str(ex), _("Web Installer Error"))
                        return
                self.preferred = pref_pub.prefix
                all_package_stems = []        
                for pkg_installs in self.pkg_install_tasks:
                        pub_info = pkg_installs[0]
                        packages = pkg_installs[1]
                        pub_pkg_stems = self.process_pkg_stems(pub_info, packages)
                        for pkg in pub_pkg_stems:
                                all_package_stems.append(pkg)
                if debug:
                        print "Install Packages: %s" % all_package_stems
                
                installupdate.InstallUpdate(all_package_stems, self, self.image_dir, 
                    action = enumerations.INSTALL_UPDATE,
                    parent_name = _("Package Manager"),
                    main_window = self.w_webinstall_dialog,
                    web_install = True)

        def process_pkg_stems(self, pub_info, packages):
                if not self.__is_publisher_registered(pub_info.prefix):
                        return []
                if pub_info.prefix == self.preferred:
                        pkg_stem = "pkg:/"
                else:
                        pkg_stem = "pkg://" + pub_info.prefix + "/"
                packages_with_stem = []
                for pkg in packages:
                        if pkg.startswith(pkg_stem):
                                packages_with_stem.append(pkg)
                        else:
                                packages_with_stem.append(pkg_stem + pkg)
                return packages_with_stem
       
        # Install Callback - invoked at end of installing packages
        def update_package_list(self, update_list):
                if update_list == None:
                        return
                self.pkg_install_tasks = []
                if len(self.disabled_pubs) > 0 and self.repo_gui:
                        gobject.idle_add(self.repo_gui.webinstall_enable_disable_pubs,
                            self.w_webinstall_dialog, self.disabled_pubs, False)
                        return
                self.__exit_app()

        def api_parse_publisher_info(self):
                '''<path to mimetype file|origin_url>
                   returns list of publisher and package list tuples'''
                try:
                        return self.api_o.parse_p5i(location=self.param)
                except api_errors.ApiException, ex:
                        self.w_webinstall_proceed.set_sensitive(False)
                        gui_misc.error_occurred( 
                            self.w_webinstall_dialog,
                            str(ex), _("Web Installer Error"))
                        sys.exit(1)
                        return None
