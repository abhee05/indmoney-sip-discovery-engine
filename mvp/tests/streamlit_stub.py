"""A tiny fake `streamlit` module so app.py can be executed in tests without a browser.

Widgets return their defaults unless CLICK / CHOOSE override them; every call is recorded in CALLS.
"""
from __future__ import annotations

import types

CALLS: list[tuple] = []
CLICK: set[str] = set()          # button labels (or keys) that return True
CHOOSE: dict[str, object] = {}   # widget label -> value to return
TEXT: dict[str, str] = {}        # text_input label -> value


class StopApp(Exception):
    pass


class _Block:
    def __getattr__(self, name):
        return getattr(_module, name)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class SessionState(dict):
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError as e:
            raise AttributeError(k) from e

    def __setattr__(self, k, v):
        self[k] = v


def _rec(name):
    def f(*a, **k):
        CALLS.append((name, a, k))
        return _Block()
    return f


def _cache(*dargs, **dkw):
    if dargs and callable(dargs[0]) and not dkw:
        return dargs[0]
    return lambda fn: fn


def columns(spec, **k):
    n = spec if isinstance(spec, int) else len(spec)
    CALLS.append(("columns", (spec,), k))
    return [_Block() for _ in range(n)]


def tabs(labels, **k):
    CALLS.append(("tabs", (labels,), k))
    return [_Block() for _ in labels]


def button(label, key=None, **k):
    CALLS.append(("button", (label,), k))
    return label in CLICK or (key is not None and key in CLICK)


def form_submit_button(label, **k):
    CALLS.append(("form_submit_button", (label,), k))
    return label in CLICK


def _pick(label, options, index=0, **k):
    options = list(options)
    if label in CHOOSE:
        v = CHOOSE[label]
        if callable(v):
            return v(options)
        return v
    if index is None:
        return None
    fmt = k.get("format_func")
    if fmt:
        [fmt(o) for o in options]  # exercise formatters
    return options[index] if options else None


def selectbox(label, options, index=0, **k):
    CALLS.append(("selectbox", (label,), k))
    return _pick(label, options, index, **k)


def radio(label, options, index=0, **k):
    CALLS.append(("radio", (label,), k))
    return _pick(label, options, index, **k)


def text_input(label, value="", **k):
    CALLS.append(("text_input", (label,), k))
    return TEXT.get(label, value)


def number_input(label, min_value=None, max_value=None, value=None, **k):
    CALLS.append(("number_input", (label,), k))
    return CHOOSE.get(label, value)


def slider(label, min_value=None, max_value=None, value=None, **k):
    CALLS.append(("slider", (label,), k))
    return CHOOSE.get(label, value)


def stop():
    raise StopApp()


def spinner(*a, **k):
    return _Block()


def altair_chart(chart, **k):
    CALLS.append(("altair_chart", (), k))
    chart.to_dict()   # validates the chart spec when altair is installed


_module = types.ModuleType("streamlit")
for _name in ["set_page_config", "info", "title", "caption", "subheader", "markdown", "metric", "divider",
              "error", "warning", "success", "dataframe", "download_button", "line_chart", "bar_chart",
              "write", "toast"]:
    setattr(_module, _name, _rec(_name))
for _name, _fn in dict(columns=columns, tabs=tabs, button=button, form_submit_button=form_submit_button,
                        selectbox=selectbox, radio=radio, text_input=text_input, number_input=number_input,
                        slider=slider, stop=stop, spinner=spinner, altair_chart=altair_chart).items():
    setattr(_module, _name, _fn)
_module.container = _rec("container")
_module.expander = _rec("expander")
_module.form = _rec("form")
_module.cache_data = _cache
_module.cache_resource = _cache
_module.session_state = SessionState()
_module.secrets = {}


def reset():
    CALLS.clear()
    CLICK.clear()
    CHOOSE.clear()
    TEXT.clear()


def fresh_session():
    _module.session_state = SessionState()
