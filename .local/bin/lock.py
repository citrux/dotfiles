#!/usr/bin/env python

# based on gtk4-layer-shell lockscreen example (https://github.com/wmww/gtk4-layer-shell/tree/main)
# and pamela for user auth via pam (https://github.com/jupyterhub/pamela)

from ctypes import CDLL

CDLL("libgtk4-layer-shell.so")

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4SessionLock", "1.0")

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Gtk4SessionLock as SessionLock

import os
import pwd
import sys
from datetime import datetime, timedelta
import threading
from ctypes import (
    CDLL,
    CFUNCTYPE,
    POINTER,
    Structure,
    byref,
    c_char,
    c_char_p,
    c_int,
    c_uint,
    c_void_p,
    cast,
    pointer,
    sizeof,
)
from ctypes.util import find_library

# Python 3 bytes/unicode compat
unicode = str
raw_input = input


def _bytes_to_str(s, encoding="utf8"):
    return s.decode(encoding)


def _cast_bytes(s, encoding="utf8"):
    if isinstance(s, unicode):
        return s.encode(encoding)
    return s


LIBPAM = CDLL(find_library("pam"))
LIBC = CDLL(find_library("c"))

CALLOC = LIBC.calloc
CALLOC.restype = c_void_p
CALLOC.argtypes = [c_uint, c_uint]

STRDUP = LIBC.strdup
STRDUP.argstypes = [c_char_p]
STRDUP.restype = POINTER(c_char)  # NOT c_char_p !!!!

# Various constants
PAM_PROMPT_ECHO_OFF = 1
PAM_PROMPT_ECHO_ON = 2
PAM_ERROR_MSG = 3
PAM_TEXT_INFO = 4

# These constants are libpam-specific
PAM_ESTABLISH_CRED = 0x0002
PAM_DELETE_CRED = 0x0004
PAM_REINITIALIZE_CRED = 0x0008
PAM_REFRESH_CRED = 0x0010

# constants for PAM_ variables for pam_set_item()
PAM_SERVICE = 1
PAM_USER = 2
PAM_TTY = 3
PAM_RHOST = 4
PAM_RUSER = 8

# PAM error codes
PAM_SUCCESS = 0
PAM_BAD_ITEM = 29


class PamHandle(Structure):
    """wrapper class for pam_handle_t"""

    _fields_ = [("handle", c_void_p)]

    def __init__(self):
        Structure.__init__(self)
        self.handle = 0

    def get_item(self, item_type, encoding="utf-8"):
        voidPointer = c_void_p()
        retval = PAM_GET_ITEM(self, item_type, byref(voidPointer))
        if retval == PAM_BAD_ITEM:
            return None
        if retval != PAM_SUCCESS:
            raise PAMError(errno=retval)

        s = cast(voidPointer, c_char_p)
        if s.value is None:
            return None
        return _bytes_to_str(s.value, encoding)

    def set_item(self, item_type, item, encoding="utf-8"):
        retval = PAM_SET_ITEM(self, item_type, item.encode(encoding))
        if retval != PAM_SUCCESS:
            raise PAMError(errno=retval)

    def get_env(self, var, encoding="utf-8"):
        ret = PAM_GETENV(self, var.encode(encoding))
        if ret is None:
            raise PAMError()
        else:
            return ret.decode(encoding)

    def put_env(self, k, v, encoding="utf-8"):
        retval = PAM_PUTENV(self, (f"{k}={v}").encode(encoding))
        if retval != PAM_SUCCESS:
            raise PAMError(errno=retval)

    def del_env(self, k, encoding="utf-8"):
        retval = PAM_PUTENV(self, k.encode(encoding))
        if retval != PAM_SUCCESS:
            raise PAMError(errno=retval)

    def get_envlist(self, encoding="utf-8"):
        ret = PAM_GETENVLIST(self)
        if ret is None:
            raise PAMError()

        parsed = {}
        for i in PAM_GETENVLIST(self):
            if i:
                k, v = i.decode(encoding).split("=", 1)
                parsed[k] = v
            else:
                break
        return parsed

    def open_session(self):
        retval = PAM_OPEN_SESSION(self, 0)
        if retval != PAM_SUCCESS:
            raise PAMError(errno=retval)

    def close_session(self):
        retval = PAM_CLOSE_SESSION(self, 0)
        if retval != PAM_SUCCESS:
            raise PAMError(errno=retval)


PAM_STRERROR = LIBPAM.pam_strerror
PAM_STRERROR.restype = c_char_p
PAM_STRERROR.argtypes = [PamHandle, c_int]


def pam_strerror(handle, errno):
    """Wrap bytes-only PAM_STRERROR in native str"""
    return _bytes_to_str(PAM_STRERROR(handle, errno))


class PAMError(Exception):
    errno = None
    message = ""

    def __init__(self, message="", errno=None):
        self.errno = errno
        if message:
            self.message = message
        else:
            if errno is None:
                self.message = "Unknown"
            else:
                self.message = pam_strerror(PamHandle(), errno)

    def __repr__(self):
        en = "" if self.errno is None else " %i" % self.errno
        return f"<PAM Error{en}: '{self.message}'>"

    def __str__(self):
        en = "" if self.errno is None else " %i" % self.errno
        return f"[PAM Error{en}] {self.message}"


class PamMessage(Structure):
    """wrapper class for pam_message structure"""

    _fields_ = [
        ("msg_style", c_int),
        ("msg", POINTER(c_char)),
    ]

    def __repr__(self):
        return "<PamMessage %i '%s'>" % (self.msg_style, _bytes_to_str(self.msg))


class PamResponse(Structure):
    """wrapper class for pam_response structure"""

    _fields_ = [
        ("resp", POINTER(c_char)),
        ("resp_retcode", c_int),
    ]

    def __repr__(self):
        return "<PamResponse %i '%s'>" % (self.resp_retcode, _bytes_to_str(self.resp))


CONV_FUNC = CFUNCTYPE(
    c_int, c_int, POINTER(POINTER(PamMessage)), POINTER(POINTER(PamResponse)), c_void_p
)


class PamConv(Structure):
    """wrapper class for pam_conv structure"""

    _fields_ = [("conv", CONV_FUNC), ("appdata_ptr", c_void_p)]


PAM_START = LIBPAM.pam_start
PAM_START.restype = c_int
PAM_START.argtypes = [c_char_p, c_char_p, POINTER(PamConv), POINTER(PamHandle)]

PAM_END = LIBPAM.pam_end
PAM_END.restype = c_int
PAM_END.argtypes = [PamHandle, c_int]

PAM_AUTHENTICATE = LIBPAM.pam_authenticate
PAM_AUTHENTICATE.restype = c_int
PAM_AUTHENTICATE.argtypes = [PamHandle, c_int]

PAM_OPEN_SESSION = LIBPAM.pam_open_session
PAM_OPEN_SESSION.restype = c_int
PAM_OPEN_SESSION.argtypes = [PamHandle, c_int]

PAM_CLOSE_SESSION = LIBPAM.pam_close_session
PAM_CLOSE_SESSION.restype = c_int
PAM_CLOSE_SESSION.argtypes = [PamHandle, c_int]

PAM_ACCT_MGMT = LIBPAM.pam_acct_mgmt
PAM_ACCT_MGMT.restype = c_int
PAM_ACCT_MGMT.argtypes = [PamHandle, c_int]

PAM_CHAUTHTOK = LIBPAM.pam_chauthtok
PAM_CHAUTHTOK.restype = c_int
PAM_CHAUTHTOK.argtypes = [PamHandle, c_int]

PAM_SETCRED = LIBPAM.pam_setcred
PAM_SETCRED.restype = c_int
PAM_SETCRED.argtypes = [PamHandle, c_int]

PAM_GETENV = LIBPAM.pam_getenv
PAM_GETENV.restype = c_char_p
PAM_GETENV.argtypes = [PamHandle, c_char_p]

PAM_GETENVLIST = LIBPAM.pam_getenvlist
PAM_GETENVLIST.restype = POINTER(c_char_p)
PAM_GETENVLIST.argtypes = [PamHandle]

PAM_PUTENV = LIBPAM.pam_putenv
PAM_PUTENV.restype = c_int
PAM_PUTENV.argtypes = [PamHandle, c_char_p]

PAM_SET_ITEM = LIBPAM.pam_set_item
PAM_SET_ITEM.restype = c_int
PAM_SET_ITEM.argtypes = [PamHandle, c_int, c_char_p]

PAM_GET_ITEM = LIBPAM.pam_get_item
PAM_GET_ITEM.restype = c_int
PAM_GET_ITEM.argtypes = [PamHandle, c_int, POINTER(c_void_p)]


@CONV_FUNC
def default_conv(n_messages, messages, p_response, app_data):
    addr = CALLOC(n_messages, sizeof(PamResponse))
    p_response[0] = cast(addr, POINTER(PamResponse))
    if not sys.stdin.isatty():
        return 0
    for i in range(n_messages):
        msg = messages[i].contents
        style = msg.msg_style
        msg_string = _bytes_to_str(cast(msg.msg, c_char_p).value)
        if style == PAM_TEXT_INFO:
            # back from POINTER(c_char) to c_char_p
            print(msg_string)
        elif style == PAM_ERROR_MSG:
            print(msg_string, file=sys.stderr)
        elif style in (PAM_PROMPT_ECHO_ON, PAM_PROMPT_ECHO_OFF):
            if style == PAM_PROMPT_ECHO_ON:
                read_pw = raw_input
            else:
                read_pw = getpass.getpass

            pw_copy = STRDUP(_cast_bytes(read_pw(msg_string)))
            p_response.contents[i].resp = pw_copy
            p_response.contents[i].resp_retcode = 0
        else:
            print(repr(messages[i].contents))
    return 0


def new_simple_password_conv(passwords, encoding):
    passwords = [_cast_bytes(password, encoding) for password in passwords]
    passwords.reverse()

    @CONV_FUNC
    def conv_func(n_messages, messages, p_response, app_data):
        """Simple conversation function that responds to any
        prompt where the echo is off with the supplied password"""
        # Create an array of n_messages response objects
        addr = CALLOC(n_messages, sizeof(PamResponse))
        p_response[0] = cast(addr, POINTER(PamResponse))
        for i in range(n_messages):
            if messages[i].contents.msg_style == PAM_PROMPT_ECHO_OFF:
                if not passwords:
                    return 1
                pw_copy = STRDUP(passwords.pop())
                p_response.contents[i].resp = pw_copy
                p_response.contents[i].resp_retcode = 0
        return 0

    return conv_func


def pam_start(service, username, conv_func=default_conv, encoding="utf8"):
    service = _cast_bytes(service, encoding)
    username = _cast_bytes(username, encoding)

    handle = PamHandle()
    conv = pointer(PamConv(conv_func, 0))
    retval = PAM_START(service, username, conv, pointer(handle))

    if retval != 0:
        PAM_END(handle, retval)
        raise PAMError(errno=retval)

    return handle


def pam_end(handle, retval=0):
    e = PAM_END(handle, retval)
    if retval == 0 and e == 0:
        return
    if retval == 0:
        retval = e
    raise PAMError(errno=retval)


def authenticate(
    username,
    password=None,
    service="login",
    encoding="utf-8",
    resetcred=PAM_REINITIALIZE_CRED,
    close=True,
    check=True,
):
    """Returns None if the given username and password authenticate for the
    given service.  Raises PAMError otherwise

    ``username``: the username to authenticate

    ``password``: the password in plain text. It can also be an iterable of
                  passwords when using multifactor authentication.
                  Defaults to None to use PAM's conversation interface

    ``service``: the PAM service to authenticate against.
                 Defaults to 'login'

    The above parameters can be strings or bytes.  If they are strings,
    they will be encoded using the encoding given by:

    ``encoding``: the encoding to use for the above parameters if they
                  are given as strings.  Defaults to 'utf-8'

    ``resetcred``: Use the pam_setcred() function to
                   reinitialize the credentials.
                   Defaults to 'PAM_REINITIALIZE_CRED'.

    ``check``: If True (default) Check that account is valid with PAM_ACCT_MGMT.
               added in 1.2.

    ``close``: If True (default) the transaction will be closed after
                   authentication; if False the (open) PamHandle instance
                   will be returned.
    """

    if password is None:
        conv_func = default_conv
    else:
        if isinstance(password, str):
            password = (password,)
        conv_func = new_simple_password_conv(password, encoding)

    handle = pam_start(service, username, conv_func=conv_func, encoding=encoding)

    retval = PAM_AUTHENTICATE(handle, 0)
    if retval == 0 and check:
        retval = PAM_ACCT_MGMT(handle, 0)

    # Re-initialize credentials (for Kerberos users, etc)
    # Don't check return code of pam_setcred(), it shouldn't matter
    # if this fails
    if retval == 0 and resetcred:
        PAM_SETCRED(handle, resetcred)

    if close:
        return pam_end(handle, retval)
    elif retval != 0:
        raise PAMError(errno=retval)
    else:
        return handle



class ScreenLock:
    def __init__(self):
        self.grace_ends_at = datetime.now() + timedelta(seconds=15)
        self.lock_instance = SessionLock.Instance.new()
        self.lock_instance.connect("locked", self._on_locked)
        self.lock_instance.connect("unlocked", self._on_unlocked)
        self.lock_instance.connect("failed", self._on_failed)

    def _on_locked(self, lock_instance):
        pass
        # print("Locked!")

    def _on_unlocked(self, lock_instance):
        # print("Unlocked!")
        app.quit()

    def _on_failed(self, lock_instance):
        print("Failed to lock :(")
        app.quit()

    def _authenticate(self, entry):
        GLib.idle_add(self.spinner.start)
        try:
            username = pwd.getpwuid(os.getuid()).pw_name
            authenticate(username, entry.props.text)
            GLib.idle_add(self.lock_instance.unlock)
        except PAMError as e:
            GLib.idle_add(self.label.set_label, e.message)
        GLib.idle_add(self.spinner.stop)

    def _on_unlock_clicked(self, entry):
        threading.Thread(target=self._authenticate, args=(entry,)).start()

    def _on_mouse_motion(self, *args):
        if datetime.now() < self.grace_ends_at:
            self.lock_instance.unlock()

    def _on_key_press(self, *args):
        if datetime.now() < self.grace_ends_at:
            self.lock_instance.unlock()

    def _create_lock_window(self, monitor):
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_string("""
                                      picture {
                                          filter: blur(8px);
                                      }

                                      entry.password {
                                          background: rgba(0,0,0,0.5);
                                      }
                                      """)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        window = Gtk.Window(application=app)

        mouse_controller = Gtk.EventControllerMotion()
        mouse_controller.connect('motion', self._on_mouse_motion)
        keyboard_controller = Gtk.EventControllerKey()
        keyboard_controller.connect('key_pressed', self._on_key_press)
        keyboard_controller.props.propagation_phase = Gtk.PropagationPhase.CAPTURE
        window.add_controller(mouse_controller)
        window.add_controller(keyboard_controller)

        overlay = Gtk.Overlay()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)

        picture = Gtk.Picture()
        picture.set_filename("/home/citrux/Pictures/wallpaper.jpg")
        picture.set_content_fit(Gtk.ContentFit.COVER)

        overlay.add_overlay(picture)
        overlay.add_overlay(box)
        window.set_child(overlay)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.append(hbox)

        self.entry = Gtk.PasswordEntry()
        self.entry.props.show_peek_icon = True
        self.entry.props.placeholder_text = "Enter Password"
        self.entry.set_size_request(250, -1)
        self.entry.connect("activate", self._on_unlock_clicked)
        hbox.append(self.entry)

        self.spinner = Gtk.Spinner()
        hbox.append(self.spinner)

        self.label = Gtk.Label()
        box.append(self.label)

        self.lock_instance.assign_window_to_monitor(window, monitor)
        window.present()

    def lock(self):
        if not self.lock_instance.lock():
            # Failure has already been handled in on_failed()
            return

        display = Gdk.Display.get_default()

        for monitor in display.get_monitors():
            self._create_lock_window(monitor)


app = Gtk.Application(application_id="com.github.wmww.gtk4-layer-shell.py-session-lock")
lock = ScreenLock()


def on_activate(app):
    lock.lock()


app.connect("activate", on_activate)
app.run(None)
