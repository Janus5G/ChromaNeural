"""Application-owned presentation only. No global locale or protocol changes."""
from pathlib import Path
import json
import os
import re
import string
import tempfile
import time
import weakref

RESOURCE_DIR = Path(__file__).resolve().parents[1] / "locales"
REGISTRY_PATH = RESOURCE_DIR.parent / "locale-registry.json"

def load_registry(path=REGISTRY_PATH):
    """Read the shared, data-only registration used by Python and Windows."""
    with Path(path).open("rb") as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise ValueError("Locale registry exceeds limit")
    value = json.loads(raw)
    if not isinstance(value, dict) or set(value) != {"version", "locales"} or type(value["version"]) is not int or value["version"] != 1:
        raise ValueError("Invalid locale registry")
    entries = value["locales"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("Empty locale registry")
    identifiers, names = set(), set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"id", "name", "number"}:
            raise ValueError("Invalid locale registration")
        identifier, name, number = entry["id"], entry["name"], entry["number"]
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", identifier) or identifier.casefold() in identifiers:
            raise ValueError("Invalid or duplicate locale identifier")
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError("Invalid or duplicate locale display name")
        if not isinstance(number, dict) or set(number) != {"decimal", "group", "primary", "secondary"}:
            raise ValueError("Invalid number format")
        if any(not isinstance(number[key], str) or len(number[key]) != 1 for key in ("decimal", "group")) or number["decimal"] == number["group"]:
            raise ValueError("Invalid number separators")
        if any(type(number[key]) is not int or not 1 <= number[key] <= 9 for key in ("primary", "secondary")):
            raise ValueError("Invalid number grouping")
        identifiers.add(identifier.casefold())
        names.add(name)
    if "en" not in [entry["id"] for entry in entries]:
        raise ValueError("English fallback registration is required")
    return tuple(entries)

REGISTRY = load_registry()
LOCALES = tuple(entry["id"] for entry in REGISTRY)
NAMES = tuple(entry["name"] for entry in REGISTRY)
NUMBER_FORMATS = {entry["id"]: entry["number"] for entry in REGISTRY}
NEUTRAL = "Message unavailable."
FORMATTER = string.Formatter()

def fields(text):
    names = set()
    for _, field, spec, conversion in FORMATTER.parse(text):
        if field is not None:
            if not re.fullmatch(r"[a-z][a-z0-9_]*", field) or spec or conversion:
                raise ValueError("Unsafe message format")
            names.add(field)
    return names

def catalog(locale, directory=RESOURCE_DIR):
    with (Path(directory) / (locale + ".json")).open("rb") as stream:
        raw = stream.read(524289)
    if len(raw) > 524288:
        raise ValueError("Locale resource exceeds limit")
    value = json.loads(raw)
    if not isinstance(value, dict) or any(not isinstance(k, str) or not isinstance(v, str) or not v for k, v in value.items()):
        raise ValueError("Invalid locale resource")
    for text in value.values():
        fields(text)
    return value

class LanguagePreference:
    """Separate bounded file in Settings.directory; read is side-effect free."""
    def __init__(self, directory):
        self.directory = Path(directory)
        self.path = self.directory / "ui-language.json"
        self.locale = "en"
        self.error = False
        try:
            with self.path.open("rb") as stream:
                raw = stream.read(1025)
            if len(raw) > 1024:
                raise ValueError("Language preference exceeds limit")
            value = json.loads(raw)
            if not isinstance(value, dict) or set(value) != {"version", "locale"} or type(value["version"]) is not int or value["version"] != 1 or value["locale"] not in LOCALES:
                raise ValueError("Unsupported language preference")
            self.locale = value["locale"]
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError):
            self.error = True

    def save(self, locale):
        if locale not in LOCALES:
            raise ValueError("Unsupported locale")
        # Re-read before explicit save, including files modified since startup.
        current = LanguagePreference(self.directory)
        if current.error and self.path.exists():
            backup = self.directory / ("ui-language.invalid." + str(time.time_ns()) + ".json")
            with self.path.open("rb") as source, backup.open("xb") as dest:
                while chunk := source.read(65536):
                    dest.write(chunk)
                dest.flush()
                os.fsync(dest.fileno())
        fd, temp = tempfile.mkstemp(prefix=".ui-language-", dir=self.directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                json.dump({"version": 1, "locale": locale}, stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, self.path)
            self.locale = locale
            self.error = False
        finally:
            if os.path.exists(temp):
                os.unlink(temp)

class Message:
    """Lazy owned text; user data is never scanned or used as a format string."""
    def __init__(self, render):
        self.render = render
    def __str__(self):
        return self.render()
    def __add__(self, other):
        return Message(lambda: str(self) + str(other))
    def __radd__(self, other):
        return Message(lambda: str(other) + str(self))

class LocaleContext:
    def __init__(self, locale="en", directory=RESOURCE_DIR):
        self.directory = directory
        self.english = catalog("en", directory)
        self.messages = self.english
        self.locale = "en"
        self.findings = set()
        self._bindings = {}
        self._listeners = weakref.WeakKeyDictionary()
        self.set(locale)

    def text(self, key, **values):
        canonical = self.english.get(key)
        if canonical is None:
            self.findings.add("missing:" + key)
            return NEUTRAL
        template = self.messages.get(key, canonical)
        try:
            if fields(template) != fields(canonical) or set(values) != fields(canonical):
                raise ValueError("Message placeholders differ")
            # str() preserves supplied data literally; formatting is not recursive.
            return template.format_map({k: str(v) for k, v in values.items()})
        except (ValueError, KeyError):
            self.findings.add("format:" + key)
            return NEUTRAL

    def msg(self, key, **values):
        return Message(lambda: self.text(key, **values))

    def set(self, locale):
        selected = locale if locale in LOCALES else "en"
        try:
            messages = catalog(selected, self.directory) if selected != "en" else self.english
        except (OSError, ValueError):
            messages = self.english
            self.findings.add("resource:" + selected)
        self.locale, self.messages = selected, messages
        for owner, entries in list(self._bindings.values()):
            if hasattr(owner, "winfo_exists") and not owner.winfo_exists():
                continue
            for setter, message in list(entries.values()):
                setter(str(message))
        for owner, callback in list(self._listeners.items()):
            if owner.winfo_exists():
                callback()
        return self.locale

    def listen(self, owner, callback):
        self._listeners[owner] = callback

    def bind(self, owner, slot, setter, value):
        entries = self._bindings.setdefault(id(owner), (owner, {}))[1]
        if isinstance(value, Message):
            entries[slot] = (setter, value)
        else:
            entries.pop(slot, None)
        setter(str(value))

    def forget(self, owner):
        self._bindings.pop(id(owner), None)
        self._listeners.pop(owner, None)

    def option(self, widget, value, option="text"):
        if id(widget) not in self._bindings:
            widget.bind("<Destroy>", lambda event: self.forget(widget) if event.widget is widget else None, add="+")
        self.bind(widget, option, lambda text: widget.configure(**{option: text}), value)
        return widget

    def title(self, window, value):
        self.bind(window, "title", window.title, value)

    def widget(self, factory, *args, **kwargs):
        value = kwargs.pop("text", "")
        widget = factory(*args, **kwargs)
        self.option(widget, value)
        return widget

    def variable(self, master, value=""):
        import tkinter as tk
        context = self
        class DisplayVar(tk.StringVar):
            def set(self, value):
                context.bind(self, "value", lambda text: tk.StringVar.set(self, text), value)
        variable = DisplayVar(master)
        variable.set(value)
        return variable

    def number(self, value, digits=6):
        if value is None:
            return "—"
        text = f"{value:,.{digits}f}"
        if digits:
            text = text.rstrip("0").rstrip(".")
        format = NUMBER_FORMATS[self.locale]
        sign = "-" if text.startswith("-") else ""
        whole, dot, decimal = text.lstrip("-").replace(",", "").partition(".")
        tail = whole[-format["primary"]:]
        whole = whole[:-format["primary"]]
        groups = []
        while whole:
            groups.insert(0, whole[-format["secondary"]:])
            whole = whole[:-format["secondary"]]
        return sign + format["group"].join(groups + [tail]) + (format["decimal"] + decimal if dot else "")

    def bytes(self, value):
        if value is None:
            return "—"
        for divisor, unit in ((1048576, " MiB"), (1024, " KiB")):
            if value >= divisor:
                return self.number(value / divisor) + unit
        return self.number(value, 0) + " B"

def packaged_version():
    path = Path(__file__).resolve().parents[2] / "VERSION"
    return path.read_text(encoding="utf-8").strip() if path.is_file() else "—"

def language_from_argv(argv):
    # Parse only the optional override, without Settings or state writes.
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--language", choices=LOCALES)
    return parser.parse_known_args(argv)[0].language

def argument_parser(context, **kwargs):
    """Localize help prose while leaving argument/choice/JSON contracts intact."""
    import argparse
    class HelpParser(argparse.ArgumentParser):
        def __init__(self, *args, **options):
            super().__init__(*args, **options)
            self._positionals.title = context.text("cli.positionals")
            self._optionals.title = context.text("cli.options")
            for action in self._actions:
                if isinstance(action, argparse._HelpAction):
                    action.help = context.text("cli.help")
        def _get_formatter(self):
            formatter = super()._get_formatter()
            original = formatter.add_usage
            formatter.add_usage = lambda usage, actions, groups, prefix=None: original(
                usage, actions, groups, context.text("cli.usage") if prefix is None else prefix)
            return formatter
    return HelpParser(**kwargs)
