import os
import socket
import subprocess
import sys


def find_free_port(start: int = 8501, tries: int = 50) -> int:
    """Return the first free TCP port at or above `start`."""
    for port in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:  # nothing is listening
                return port
    raise RuntimeError(f"No free port found between {start} and {start + tries - 1}.")


def run_tool(port: int = 8501, open_browser: bool = True) -> None:
    """Start the Streamlit app (tool.py) from Python."""
    tool_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tool.py")
    port = find_free_port(port)
    print(f"Starting the tool at http://localhost:{port}")
    cmd = [
        sys.executable, "-m", "streamlit", "run", tool_path,
        "--server.port", str(port),
        "--server.headless", "false" if open_browser else "true",
    ]
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run_tool()