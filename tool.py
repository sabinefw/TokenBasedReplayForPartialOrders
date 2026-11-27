"""
Streamlit front end for token-based replay conformance checking on partially
ordered logs.

Wraps `do_conformance_checking_for_partially_ordered_log` from
https://github.com/sabinefw/TokenBasedReplayForPartialOrders  (module: user_interface)

Run with:   streamlit run tool.py
"""

import inspect
import logging
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src.TokenBasedReplayForPartialOrders.structures.partially_ordered_log_conformance_result import (
    LevelType,
    PartiallyOrderedLogConformanceResult,
    PersistationType,
)
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
LOGGER = logging.getLogger(__name__)

# The XES limit mirrors .streamlit/config.toml. The PNML limit is intentionally
# much smaller because workflow nets do not require large uploads.
MAX_LOG_UPLOAD_SIZE_MB = 1024
MAX_NET_UPLOAD_SIZE_MB = 1


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

def with_wrap(widget, *args, **kwargs):
    """Call a Streamlit widget so that a long label breaks into several lines instead of being cut off."""
    try:
        return widget(*args, wrap=True, **kwargs)
    except TypeError:  # older Streamlit versions do not have the wrap option (they wrap anyway)
        return widget(*args, **kwargs)

# Custom labels for the boolean inputs: {parameter name of the function: text shown in the app}
CUSTOM_LABELS = {
    "only_use_heuristics": "Use \"Fast\" Algorithm (bounds only)",
    "include_runs_with_invalid_labels": "Include traces with invalid labels",
    "add_initial_and_start_events": "Add start and end events",
}

# ---------------------------------------------------------------------------
# Browser uploads and downloads
# ---------------------------------------------------------------------------
def clear_results():
    """Discard the previous result when either uploaded input file changes."""
    for key in ("result", "result_error", "result_object"):
        st.session_state.pop(key, None)


def store_uploaded_file(upload, directory: str, filename: str) -> str:
    """Write an upload under a server-controlled name and return its path."""
    destination = Path(directory, filename)
    with destination.open("wb") as target:
        target.write(upload.getbuffer())
    return str(destination)


# Formats for downloading the result: {name shown in the app: (PersistationType, file extension, MIME type)}
SAVE_FORMATS = {
    "CSV": (PersistationType.CSV, ".csv", "text/csv"),
    "XML": (PersistationType.XML, ".xml", "application/xml"),
}

# Explanation of the saved files, shown in the help box of the "Save result" section (Markdown).
SAVE_HELP = {
    "CSV": """
**One table, one line per result**
- The **first line** is the total result for the whole log: ID `Total`, column "Total result" = `True`.
- Then follows **one line per trace**: ID = trace ID, column "Total result" = `False`.

**Columns**
- ID, Total result
- Minimum / Average / Maximum fitness value (for a precise result all three are equal; the average of a trace is the mean of its minimum and maximum)
- Produced tokens, Consumed tokens
- Missing tokens (max / min), Remaining tokens (max / min)
- Places decided with forward heuristic, with backward heuristic
- Places decided with other method: the larger of the places decided by the flow algorithm and the places only estimated

The file is UTF-8 encoded and comma-separated, with a decimal point. Values are saved with full precision, independent of the decimal digits shown in the app.
""",
    "XML": """
**Nested structure**
- The root element `PartiallyOrderedLogConformanceResult` contains the element `TotalResult` (attribute `isPreciseResult`) with the result for the whole log.
- Nested below it, `RunResults` contains one `RunResult` element per trace (attribute `id` = trace ID).

**Content of `TotalResult` and of every `RunResult`**
- `minimumFitnessValue`, `averageFitnessValue`, `maximumFitnessValue` (for a precise result all three are equal; the average of a trace is the mean of its minimum and maximum)
- `producedTokens`, `consumedTokens`
- `missingTokensMax`, `missingTokensMin`, `remainingTokensMax`, `remainingTokensMin`
- `placesDecidedForwardHeuristic`, `placesDecidedBackwardHeuristic`
- `placesDecidedOtherMethod`: places decided by the flow algorithm if its usage was activated in the parameter; otherwise the places only estimated, 

The file is UTF-8 encoded. Values are saved with full precision, independent of the decimal digits shown in the app.
""",

}
# ---------------------------------------------------------------------------
# Result handling
# ---------------------------------------------------------------------------
def result_as_bytes(result: PartiallyOrderedLogConformanceResult, persist_type: PersistationType,
                    extension: str) -> bytes:
    """Persist a result briefly, then return it for a browser download."""
    descriptor, filename = tempfile.mkstemp(suffix=extension, prefix="po-track-result-")
    os.close(descriptor)
    path = Path(filename)
    try:
        result.persist_result(str(path), persist_type)
        return path.read_bytes()
    finally:
        path.unlink(missing_ok=True)


def extract_conformance_values(result: PartiallyOrderedLogConformanceResult):
    if result is None:
        raise ValueError("None is not a valid input.")

    return {
        "lower": result.lower_bound_conformance,
        "upper": result.upper_bound_conformance,
        "level": result.conformance_level,
        "is_precise": result.is_precise_result,
        "produced": result.produced_tokens,
        "consumed": result.consumed_tokens,
        "missing_min": result.missing_tokens_min,
        "missing_max": result.missing_tokens_max,
        "remaining_min": result.remaining_tokens_min,
        "remaining_max": result.remaining_tokens_max,
        "places_forward": result.number_places_decided_forward_heuristic,
        "places_backward": result.number_places_decided_backward_heuristic,
        "places_flow": result.number_places_decided_flow_network,
        "places_estimated": result.number_places_only_estimated,
        "number_non_conforming_runs" : result.get_number_of_non_conforming_runs(),
        "number_all_runs" : result.get_number_of_runs_in_log(),
    }

# ---------------------------------------------------------------------------
# Workflow net visualization (pm4py)
# ---------------------------------------------------------------------------
def net_to_dot(path: str) -> str:
    """
    Read a PNML file with pm4py and return the Graphviz DOT source of its
    visualization.
    """
    import pm4py
    from pm4py.visualization.petri_net import visualizer as pn_visualizer

    net, initial_marking, final_marking = pm4py.read_pnml(path)
    gviz = pn_visualizer.apply(net, initial_marking, final_marking)
    return gviz.source


# ---------------------------------------------------------------------------
# Worst runs: table and visualization of a run
# ---------------------------------------------------------------------------
LEVEL_OPTIONS = {
    "Minimum fitness value": LevelType.LOWER_BOUND,
    "Maximum fitness value": LevelType.UPPER_BOUND,
}


def event_text(event) -> str:
    """Text shown for an event (a node of the run) in the visualization: its label."""
    return str(event.label.activity_description)


MISSING_ACTIVITY_PREFIX = "INVALID LABEL"


def count_missing_activities(run) -> int:
    """Number of events of the run whose label text starts with MISSING ACTIVITY."""
    return sum(1 for event in run.partial_order if event_text(event).startswith(MISSING_ACTIVITY_PREFIX))


def right_aligned(column_class, label, **kwargs):
    """Column configuration with right-aligned cells (older Streamlit versions without that option: default)."""
    try:
        return column_class(label, alignment="right", **kwargs)
    except TypeError:
        return column_class(label, **kwargs)


def format_range(minimum, maximum) -> str:
    return str(minimum) if minimum == maximum else f"{minimum} - {maximum}"


def build_run_figure(run):
    """
    Draw the partial order of a run (a NetworkX graph) and return a matplotlib figure.

    Long labels are wrapped into several lines. The layout is computed in points from the real size of
    the label boxes, so that boxes never overlap, however long the labels are.
    """
    import textwrap

    import networkx as nx
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    FONT_SIZE = 10
    WRAP_WIDTH = 24  # maximal number of characters per line of a label
    BOX_PADDING = 8.0  # extra space (points) around the text inside a box
    GAP_X = 70.0  # horizontal space (points) between two layers, room for the arrows
    GAP_Y = 16.0  # vertical space (points) between two boxes of the same layer
    MARGIN = 20.0  # space (points) around the whole picture

    graph = run.partial_order
    if graph.number_of_nodes() == 0:
        raise ValueError("The run has no events.")

    # Edges implied by transitivity are hidden, which makes the picture much easier to read.
    try:
        graph = nx.transitive_reduction(graph)
    except Exception:  # noqa: BLE001  (e.g. graph is not acyclic: draw it as it is)
        pass

    original_texts = {node: event_text(node) for node in graph.nodes}
    wrapped_texts = {node: textwrap.fill(text, width=WRAP_WIDTH) for node, text in original_texts.items()}

    # Measure the size of every label box (in points).
    measuring_fig = Figure()
    FigureCanvasAgg(measuring_fig)
    renderer = measuring_fig.canvas.get_renderer()
    box_size = {}
    for node, text in wrapped_texts.items():
        item = measuring_fig.text(0, 0, text, fontsize=FONT_SIZE)
        extent = item.get_window_extent(renderer)
        box_size[node] = (extent.width * 72.0 / measuring_fig.dpi + BOX_PADDING,
                          extent.height * 72.0 / measuring_fig.dpi + BOX_PADDING)
        item.remove()

    # Layers = topological generations (left to right). Not acyclic: one single layer.
    try:
        layers = [list(generation) for generation in nx.topological_generations(graph)]
    except nx.NetworkXUnfeasible:
        layers = [list(graph.nodes)]

    layer_width = [max(box_size[node][0] for node in layer) for layer in layers]
    layer_height = [sum(box_size[node][1] for node in layer) + GAP_Y * (len(layer) - 1) for layer in layers]
    total_width = sum(layer_width) + GAP_X * (len(layers) - 1) + 2 * MARGIN
    total_height = max(layer_height) + 2 * MARGIN

    # Positions in points: every layer is a column whose boxes are stacked vertically and centered.
    pos = {}
    x_left = MARGIN
    for layer, width, height in zip(layers, layer_width, layer_height):
        y_top = total_height / 2 + height / 2
        for node in layer:
            pos[node] = (x_left + width / 2, y_top - box_size[node][1] / 2)
            y_top -= box_size[node][1] + GAP_Y
        x_left += width + GAP_X

    fig = Figure(figsize=(total_width / 72.0, total_height / 72.0))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, total_width)
    ax.set_ylim(0, total_height)
    ax.set_axis_off()

    text_items = nx.draw_networkx_labels(graph, pos, labels=wrapped_texts, ax=ax, font_size=FONT_SIZE,
                                         bbox=dict(boxstyle="round,pad=0.35", fc="#e8f0fe", ec="#5b7db1"))
    for node, text_item in text_items.items():
        if original_texts[node].startswith(MISSING_ACTIVITY_PREFIX):
            text_item.set_color("red")
    # Every arrow starts and ends exactly at the border of the two label boxes (patchA / patchB),
    # so the arrow heads are never hidden behind a box, however long the label is.
    # The arrows are drawn after the labels (zorder 4 > 3), because the boxes only get their final
    # position when the labels are drawn.
    for source, target in graph.edges:
        ax.annotate("", xy=pos[target], xytext=pos[source], zorder=4,
                    arrowprops=dict(arrowstyle="-|>", color="#666666", mutation_scale=14,
                                    shrinkA=1, shrinkB=1,
                                    patchA=text_items[source].get_bbox_patch(),
                                    patchB=text_items[target].get_bbox_patch()))
    return fig


#

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Token-Based Replay for Partial Orders", layout="wide")
st.markdown(
    """
    <style>
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] *,
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
        overflow-wrap: break-word;
    }
    [data-testid="stWidgetLabel"] p { white-space: normal; overflow-wrap: break-word; }
    [data-testid="stMainBlockContainer"] { padding-top: 0.25rem !important; }
    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] * {
        font-size: 1rem !important;
    }
    /* Keep both upload controls compact and the same height before and after an upload. */
    [data-testid="stFileUploaderDropzone"] {
        height: 3rem !important;
        min-height: 3rem !important;
        padding: 0.25rem 0.5rem !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] { display: none !important; }
    [data-testid="stFileUploaderFile"] {
        min-height: 3rem !important;
        margin: 0 !important;
        padding: 0.25rem 0.5rem !important;
        border-radius: 0.5rem;
        background: rgba(151, 166, 195, 0.15);
    }
    /* Once a file is present, its native file row replaces the upload box. */
    [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"])
        [data-testid="stFileUploaderDropzone"] { display: none !important; }
    [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"])
        section + div { margin-top: 0 !important; }
    [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"])
        [data-testid="stFileUploaderFile"] { box-sizing: border-box; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("Token-based Replay Fitness for Partially Ordered Event Logs")

try:
    conformance_fn = load_function()
except Exception:  # noqa: BLE001
    LOGGER.exception("Application initialization failed")
    st.error("The application could not be initialized. Please try again later.")
    st.stop()

bool_params = get_bool_parameters(conformance_fn)
leading = get_leading_positional_params(conformance_fn, 2)

left, right = st.columns([1, 3], gap="large")

with left:
    st.subheader("Input")

    net_upload = st.file_uploader(
        "Upload workflow net (.pnml)", type=["pnml"], key="net_upload",
        max_upload_size=MAX_NET_UPLOAD_SIZE_MB, on_change=clear_results,
    )
    log_upload = st.file_uploader(
        "Upload event log (.xes)", type=["xes"], key="log_upload",
        max_upload_size=MAX_LOG_UPLOAD_SIZE_MB, on_change=clear_results,
    )

    bool_values = {}
    for name, default in bool_params:
        bool_values[name] = with_wrap(st.checkbox, CUSTOM_LABELS.get(name, pretty(name)), value=default, key=f"bool_{name}")

    calculate = st.button("Calculate", type="primary", use_container_width=True)

    # ----- results, directly below the input menu on the left -----
    if calculate:
        errors = []
        if log_upload is None:
            errors.append("Please upload an event log in XES format.")
        if net_upload is None:
            errors.append("Please upload a reference workflow net in PNML format.")

        if errors:
            for msg in errors:
                st.error(msg)
        else:
            st.session_state.pop("result", None)
            st.session_state.pop("result_error", None)
            st.session_state.pop("result_object", None)
            try:
                with st.spinner("Calculating conformance..."):
                    with tempfile.TemporaryDirectory(prefix="po-track-upload-") as upload_dir:
                        log_path = store_uploaded_file(log_upload, upload_dir, "event-log.xes")
                        net_path = store_uploaded_file(net_upload, upload_dir, "workflow-net.pnml")
                        result = conformance_fn(log_path, net_path, **bool_values)
                st.session_state["result"] = extract_conformance_values(result)
                st.session_state["result_object"] = result
            except Exception:  # noqa: BLE001
                LOGGER.exception("Conformance calculation failed")
                st.session_state["result_error"] = (
                    "The calculation could not be completed. Please verify that the uploaded "
                    "files are valid and compatible."
                )

    # Filled below after the calculation result is available. Keeping this
    # container in the left column decouples it from the trace list on the right.
    result_container = st.container()

with right:
    st.subheader("Reference workflow net")

    if net_upload is None:
        st.info("Upload a workflow net (.pnml) to see its visualization here.")
    else:
        try:
            with tempfile.TemporaryDirectory(prefix="po-track-net-") as net_dir:
                net_file = store_uploaded_file(net_upload, net_dir, "workflow-net.pnml")
                dot_source = net_to_dot(net_file)
            st.graphviz_chart(dot_source, use_container_width=True)
        except Exception:  # noqa: BLE001
            LOGGER.exception("Workflow-net visualization failed")
            st.error("The uploaded workflow net could not be read or visualized.")

    if net_upload is not None:
        st.markdown("<div style='height: 1cm'></div>", unsafe_allow_html=True)

    # Filled below after the calculation result is available. Keeping this
    # container here decouples the right column from the height of the result.
    nonconforming_container = st.container()

with result_container:
    res = st.session_state.get("result")
    error_details = st.session_state.get("result_error")
    if error_details:
        st.subheader("Result")
        st.error(error_details)
    elif res:
        st.subheader("Result")

        digits = 4
        if res["is_precise"]:
            st.metric("Fitness value", f"{res['level']:.{digits}f}")
        else:
            st.metric("Minimum fitness value", f"{res['lower']:.{digits}f}")
            st.metric("Maximum fitness value", f"{res['upper']:.{digits}f}")
        st.metric("Number of non-conforming traces: ", f"{res['number_non_conforming_runs']} / {res['number_all_runs']}")

        with st.expander("Download result"):
            save_format = st.selectbox("File format", list(SAVE_FORMATS), key="save_format")
            save_type, save_extension, mime_type = SAVE_FORMATS[save_format]
            with st.popover("What does the saved file contain?", use_container_width=True):
                st.markdown(SAVE_HELP[save_format])
            try:
                download_data = result_as_bytes(
                    st.session_state["result_object"], save_type, save_extension
                )
            except Exception:  # noqa: BLE001
                LOGGER.exception("Preparing result download failed")
                st.error("The result could not be prepared for download.")
            else:
                st.download_button(
                    "Download result", data=download_data,
                    file_name=f"po-track-result{save_extension}", mime=mime_type,
                    key="download_result", use_container_width=True,
                )

        # ----- token information -----
        st.markdown("&nbsp;")
        if res["is_precise"]:
            missing_text = f"{res['missing_min']}"
            remaining_text = f"{res['remaining_min']}"
        else:
            missing_text = f"{res['missing_min']} - {res['missing_max']}"
            remaining_text = f"{res['remaining_min']} - {res['remaining_max']}"
        st.markdown(
            f"**Produced tokens:** {res['produced']}  \n"
            f"**Consumed tokens:** {res['consumed']}  \n"
            f"**Missing tokens:** {missing_text}  \n"
            f"**Remaining tokens:** {remaining_text}"
        )

        # ----- how the places were decided -----
        st.markdown("&nbsp;")
        place_lines = [
            f"**Places decided by forward heuristic:** {res['places_forward']}",
            f"**Places decided by backward heuristic:** {res['places_backward']}",
        ]
        if not bool_values["only_use_heuristics"]:
            place_lines.append(f"**Places decided by flow algorithm:** {res['places_flow']}")
        else:
            place_lines.append(f"**Places only estimated:** {res['places_estimated']}")
        st.markdown("  \n".join(place_lines))

with nonconforming_container:
    result_object = st.session_state.get("result_object")
    current_result = st.session_state.get("result")
    if current_result and result_object is not None:
        st.subheader("Non-conforming traces")

        control_left, control_right = st.columns(2)
        if current_result["is_precise"]:
            level_type = LevelType.MIDDLE  # lower bound = upper bound, so the choice would make no difference
        else:
            with control_right:
                level_name = st.selectbox("Rank traces by", list(LEVEL_OPTIONS), key="worst_runs_level")
            level_type = LEVEL_OPTIONS[level_name]

        # All runs that are not perfect, worst first. Its length is the maximal number of runs one can select.
        try:
            all_worst_runs = result_object.find_runs_with_worst_conformance_values(
                len(result_object.run_to_conformance_result), level_type)
        except Exception:  # noqa: BLE001
            all_worst_runs = None
            LOGGER.exception("Determining the worst runs failed")
            st.error("The non-conforming traces could not be determined.")

        worst_runs = None
        if all_worst_runs is not None and all_worst_runs:
            maximal_number_runs = len(all_worst_runs)
            # Keep the stored selection valid if the maximum got smaller (e.g. after changing the ranking).
            st.session_state.setdefault("worst_runs_count", min(5, maximal_number_runs))
            if st.session_state["worst_runs_count"] > maximal_number_runs:
                st.session_state["worst_runs_count"] = maximal_number_runs
            with control_left:
                number_runs = st.number_input(
                    "Include max. number of non-conforming traces in list", min_value=1, max_value=maximal_number_runs, step=1, key="worst_runs_count",
                    help=f"At most {maximal_number_runs}: the number of runs with a fitness value below 1.")
            worst_runs = all_worst_runs[:int(number_runs)]
        elif all_worst_runs is not None:
            worst_runs = []

        if worst_runs is not None:
            if not worst_runs:
                st.info("There are no runs with a fitness value below 1.")
            else:
                plot_area = st.container()  # reserved above the table, filled below once the selected row is known
                digits_runs = 4
                rows = []
                for rank, entry in enumerate(worst_runs, start=1):
                    run_result = entry.conformance_result
                    row = {
                        "Rank": rank,
                        "Trace ID": entry.run.name_foreign_source,
                        "Events": len(entry.run.partial_order),
                        "Invalid activity labels": count_missing_activities(entry.run),
                    }
                    if current_result["is_precise"]:
                        row["Fitness value"] = run_result.conformance_level_min
                    else:
                        row["Minimum fitness value"] = run_result.conformance_level_min
                        row["Maximum fitness value"] = run_result.conformance_level_max
                    row["Missing tokens"] = format_range(run_result.missing_token_min, run_result.missing_token_max)
                    row["Remaining tokens"] = format_range(run_result.remaining_token_min, run_result.remaining_token_max)
                    rows.append(row)

                runs_table = pd.DataFrame(rows)
                number_format = f"%.{digits_runs}f"
                formatted_columns = ("Fitness value", "Minimum fitness value", "Average fitness value", "Maximum fitness value")
                column_config = {
                    name: (right_aligned(st.column_config.NumberColumn, name, format=number_format)
                           if name in formatted_columns
                           else right_aligned(st.column_config.Column, name))
                    for name in runs_table.columns
                }
                table_event = st.dataframe(
                    runs_table,
                    hide_index=True,
                    use_container_width=True,
                    column_config=column_config,
                    on_select="rerun",
                    selection_mode="single-row",
                    key="worst_runs_table",
                )
                selected_rows = table_event.selection.rows
                selected = selected_rows[0] if selected_rows else 0
                if selected >= len(worst_runs):
                    selected = 0

                selected_run = worst_runs[selected].run
                with plot_area:
                    st.caption(f"Trace {selected + 1}: {selected_run.name_foreign_source} "
                               f"({len(selected_run.partial_order)} events). Select a row in the table below to show another trace.")
                    try:
                        st.pyplot(build_run_figure(selected_run), use_container_width=True)
                    except Exception:  # noqa: BLE001
                        LOGGER.exception("Trace visualization failed")
                        st.error("The selected trace could not be visualized.")
