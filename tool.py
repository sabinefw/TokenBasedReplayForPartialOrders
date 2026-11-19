"""
Streamlit front end for token-based replay conformance checking on partially
ordered logs.

Wraps `do_conformance_checking_for_partially_ordered_log` from
https://github.com/sabinefw/TokenBasedReplayForPartialOrders  (module: user_interface)

Run with:   streamlit run tool.py
"""

import inspect
import json
import os
import subprocess
import sys

import streamlit as st

from src.TokenBasedReplayForPartialOrders.structures.partially_ordered_log_conformance_result import PartiallyOrderedLogConformanceResult
from src.TokenBasedReplayForPartialOrders.user_interface import do_conformance_checking_for_partially_ordered_log as conf_alg_fn

# ---------------------------------------------------------------------------
# CONFIGURATION - adjust if your folder layout differs
# ---------------------------------------------------------------------------
# Folder that contains user_interface.py (the repo's "src" folder).
# Default: src next to this file.
# You can also set the environment variable TBR_SRC.
HERE = os.path.dirname(os.path.abspath(__file__))
REPO_SRC = os.environ.get(
    "TBR_SRC", os.path.join(HERE, "src", "TokenBasedReplayForPartialOrders")
)
for p in (REPO_SRC, os.path.dirname(REPO_SRC)):
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

FUNCTION_NAME = "do_conformance_checking_for_partially_ordered_log"


# ---------------------------------------------------------------------------
# Import the function
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_function():
    fn = conf_alg_fn
    return fn


def get_bool_parameters(fn):
    """Return [(name, default)] for all parameters whose default is a bool."""
    params = inspect.signature(fn).parameters.values()
    return [(p.name, p.default) for p in params if isinstance(p.default, bool)]


def get_leading_positional_params(fn, n=2):
    params = [
        p
        for p in inspect.signature(fn).parameters.values()
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]
    return params[:n]


def pretty(name):
    return name.replace("_", " ").capitalize()


# ---------------------------------------------------------------------------
# Native file dialog ("explorer view")
# ---------------------------------------------------------------------------
# The dialog is opened in a separate Python process, because tkinter does not
# work reliably inside Streamlit's script threads. This only works when the app
# runs on your own computer (the dialog appears on the machine running Streamlit).
_DIALOG_SCRIPT = """
import json, sys
import tkinter as tk
from tkinter import filedialog
title, filetypes, initialdir = json.loads(sys.argv[1])
root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)
path = filedialog.askopenfilename(
    title=title,
    filetypes=[tuple(ft) for ft in filetypes],
    initialdir=initialdir or None,
)
root.destroy()
print(path)
"""


def _browse_callback(key, title, filetypes):
    """Button callback: open the file dialog and store the chosen path."""
    current = st.session_state.get(key, "").strip()
    initialdir = os.path.dirname(current) if current and os.path.exists(os.path.dirname(current)) else ""
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _DIALOG_SCRIPT, json.dumps([title, filetypes, initialdir])],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "File dialog failed.")
        chosen = proc.stdout.strip()
        if chosen:  # empty string = dialog cancelled
            st.session_state[key] = chosen
        st.session_state.pop("browse_error", None)
    except Exception as e:  # noqa: BLE001
        st.session_state["browse_error"] = (
            f"Could not open a file dialog ({e}). You can still type or paste the path. "
            "On Linux you may need to install tkinter (e.g. `sudo apt install python3-tk`)."
        )


def path_input(label, key, placeholder, dialog_title, filetypes):
    """Text field for a path with a 'Browse...' button that opens an explorer."""
    text_col, button_col = st.columns([5, 2], vertical_alignment="bottom")
    with text_col:
        value = st.text_input(label, key=key, placeholder=placeholder)
    with button_col:
        st.button(
            "Browse...",
            key=f"{key}_browse",
            on_click=_browse_callback,
            args=(key, dialog_title, filetypes),
            use_container_width=True,
        )
    return value

# ---------------------------------------------------------------------------
# Result handling
# ---------------------------------------------------------------------------
def extract_lower_and_upper_bound_and_conformance_level(result: PartiallyOrderedLogConformanceResult):
    if result is None:
        raise ValueError("None is not a valid input.")

    return result.lower_bound_conformance, result.upper_bound_conformance, result.conformance_level


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Token-Based Replay for Partial Orders", layout="wide")
st.title("Token-Replay-Based conformance norm for partially ordered logs")

try:
    conformance_fn = load_function()
except Exception as e:  # noqa: BLE001
    st.error(
        f"Could not import `{FUNCTION_NAME}` from `user_interface`.\n\n"
        f"Looked in: `{REPO_SRC}`\n\n"
        "Clone the repository next to this file, or set the environment variable "
        "`TBR_SRC` to the folder containing `user_interface.py`."
    )
    st.exception(e)
    st.stop()

bool_params = get_bool_parameters(conformance_fn)
leading = get_leading_positional_params(conformance_fn, 2)

left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("Input")

    log_path = path_input("Event log path (.xes)", key="log_path", placeholder="C:/data/log.xes",
                          dialog_title="Select event log",
                          filetypes=[["XES event logs", "*.xes"], ["All files", "*.*"]])
    net_path = path_input("Workflow net path (.pnml)", key="net_path", placeholder="C:/data/net.pnml",
                          dialog_title="Select workflow net",
                          filetypes=[["PNML Petri nets", "*.pnml"], ["All files", "*.*"]])
    if st.session_state.get("browse_error"):
        st.warning(st.session_state["browse_error"])

    bool_values = {}
    for name, default in bool_params:
        bool_values[name] = st.checkbox(pretty(name), value=default, key=f"bool_{name}")

    calculate = st.button("Calculate", type="primary", use_container_width=True)

    # ----- results, directly below the input menu on the left -----
    if calculate:
        errors = []
        if not log_path.strip():
            errors.append("Please enter the path of the event log.")
        elif not os.path.isfile(log_path.strip()):
            errors.append(f"Event log file not found: {log_path}")
        if not net_path.strip():
            errors.append("Please enter the path of the workflow net.")
        elif not os.path.isfile(net_path.strip()):
            errors.append(f"Workflow net file not found: {net_path}")

        if errors:
            for msg in errors:
                st.error(msg)
        else:
            try:
                with st.spinner("Calculating conformance..."):
                    result = conformance_fn(
                        log_path.strip(), net_path.strip(), **bool_values
                    )
                lower, upper, conformance_level = extract_lower_and_upper_bound_and_conformance_level(result)
                st.session_state["result"] = {
                    "lower": lower,
                    "upper": upper,
                    "raw": conformance_level,
                }
            except Exception as e:  # noqa: BLE001
                st.session_state.pop("result", None)
                st.error("The calculation failed.")
                st.exception(e)

    res = st.session_state.get("result")
    if res:
        st.subheader("Result")
        conformance_value = (res["lower"] + res["upper"]) / 2
        st.metric("Lower bound", f"{res['lower']:.4f}")
        st.metric("Upper bound", f"{res['upper']:.4f}")
        st.metric("Conformance value", f"{conformance_value:.4f}")
        with st.expander("Raw return value of the function"):
            st.code(res["raw"])

with right:
    with st.expander("Function details (read from the code)", expanded=False):
        st.write(f"`{FUNCTION_NAME}{inspect.signature(conformance_fn)}`")
        st.write(
            "First two parameters used for the paths: "
            + ", ".join(f"`{p.name}`" for p in leading)
        )
        st.write(
            "Boolean parameters: "
            + (", ".join(f"`{n}` (default {d})" for n, d in bool_params) or "none found")
        )