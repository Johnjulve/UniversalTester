"""
Cross-platform Desktop Application (GUI) for UniversalTester (testx).
Runs on Windows and Linux using standard library Tkinter/TTK.
"""
import os
import sys
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Dict, Any, List

from core.service import TesterService
from core.models import RunRequest, RunResult
from core.events import ProgressEvent
from gui.worker import AsyncTestRunner
from cli.interactive import load_config

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class UniversalTesterApp:
    """Master Desktop GUI Window for UniversalTester."""

    def __init__(self, root: tk.Tk, service: Optional[TesterService] = None):
        self.root = root
        self.service = service or TesterService()
        self.runner = AsyncTestRunner(self.service)
        self.event_queue: queue.Queue = queue.Queue()
        self.config = load_config(_ROOT_DIR)

        self.root.title("UniversalTester (testx) — Quality & Benchmark Engine")
        self.root.geometry("980x640")
        self.root.minsize(780, 520)

        self.project_path_var = tk.StringVar(value=os.getcwd())
        self.status_var = tk.StringVar(value="Ready")
        self.step_var = tk.StringVar(value="Select a testing capability to begin.")

        self._setup_styles()
        self._build_ui()
        self._refresh_capabilities()
        self._poll_queue()

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

    def _build_ui(self):
        # 1. Top Project Bar
        top_frame = ttk.Frame(self.root, padding="10 10 10 5")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Project:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 6))

        proj_entry = ttk.Entry(top_frame, textvariable=self.project_path_var, font=("Segoe UI", 9))
        proj_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        ttk.Button(top_frame, text="Browse...", command=self._browse_directory).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(top_frame, text="Refresh", command=self._refresh_capabilities).pack(side=tk.LEFT)

        # 2. Main Paned Content Area
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left Sidebar: Capabilities (dynamic)
        left_frame = ttk.LabelFrame(paned, text=" Testing Capabilities ", padding="10")
        paned.add(left_frame, weight=1)

        self.cap_buttons_frame = ttk.Frame(left_frame)
        self.cap_buttons_frame.pack(fill=tk.BOTH, expand=True)

        # Right Area: Execution Dashboard & Live Log
        right_frame = ttk.LabelFrame(paned, text=" Execution Dashboard ", padding="10")
        paned.add(right_frame, weight=3)

        # Status & Progress Header
        header_frame = ttk.Frame(right_frame)
        header_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(header_frame, text="Status:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        self.status_label = ttk.Label(header_frame, textvariable=self.status_var, font=("Segoe UI", 10))
        self.status_label.pack(side=tk.LEFT, padx=(0, 16))

        self.cancel_btn = ttk.Button(header_frame, text="Cancel Run", state=tk.DISABLED, command=self._cancel_run)
        self.cancel_btn.pack(side=tk.RIGHT)

        ttk.Label(right_frame, textvariable=self.step_var, font=("Segoe UI", 9)).pack(fill=tk.X, pady=(0, 4))

        self.progress_bar = ttk.Progressbar(right_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))

        # Live Console Text Area
        console_frame = ttk.Frame(right_frame)
        console_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(console_frame, wrap=tk.WORD, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(console_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def _browse_directory(self):
        selected = filedialog.askdirectory(initialdir=self.project_path_var.get())
        if selected:
            self.project_path_var.set(selected)
            self._refresh_capabilities()

    def _refresh_capabilities(self):
        for widget in self.cap_buttons_frame.winfo_children():
            widget.destroy()

        proj_path = self.project_path_var.get()
        caps = self.service.list_capabilities(proj_path)

        for cap in caps:
            cap_id = cap["id"]
            name = cap["name"]
            is_avail = cap.get("available", True)
            btn_text = f"Pillar {cap.get('pillar', '')}: {name}" if cap.get('pillar') not in ('ALL', 'SYS') else name
            if not is_avail:
                btn_text += " [N/A]"

            btn = ttk.Button(
                self.cap_buttons_frame,
                text=btn_text,
                command=lambda cid=cap_id: self._trigger_run(cid),
                state=tk.NORMAL if is_avail else tk.DISABLED
            )
            btn.pack(fill=tk.X, pady=3)

    def _trigger_run(self, capability: str):
        if self.runner.is_running():
            return

        self.status_var.set("RUNNING...")
        self.step_var.set(f"Executing {capability}...")
        self.progress_bar['value'] = 0
        self.cancel_btn.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.insert(tk.END, f"▶ Starting workload: {capability}\n\n")

        req = RunRequest(
            capability=capability,
            project_path=self.project_path_var.get(),
            options={"concurrent_users": 200}
        )

        def on_event(evt: ProgressEvent):
            self.event_queue.put(("event", evt))

        def on_complete(res: RunResult):
            self.event_queue.put(("result", res))

        self.runner.start_run(req, on_event=on_event, on_complete=on_complete)

    def _cancel_run(self):
        self.runner.cancel()
        self.step_var.set("Cancellation requested...")

    def _poll_queue(self):
        try:
            while True:
                msg_type, payload = self.event_queue.get_nowait()
                if msg_type == "event":
                    evt: ProgressEvent = payload
                    if evt.percent >= 0:
                        self.progress_bar['value'] = evt.percent
                    self.step_var.set(f"[{evt.step}] {evt.message}")
                    if evt.message:
                        self.log_text.insert(tk.END, f"{evt.message}\n")
                        self.log_text.see(tk.END)
                elif msg_type == "result":
                    res: RunResult = payload
                    self.cancel_btn.config(state=tk.DISABLED)
                    self.status_var.set(f"✔ {res.status}" if res.is_success else f"✖ {res.status}")
                    self.progress_bar['value'] = 100
                    summary = f"\n────────────────────────────────────────\nRun ID: {res.run_id} | Status: {res.status} | Duration: {res.duration_s}s\n"
                    if res.metrics:
                        summary += f"Metrics: {res.metrics}\n"
                    self.log_text.insert(tk.END, summary)
                    self.log_text.see(tk.END)
        except queue.Empty:
            pass

        self.root.after(50, self._poll_queue)


def main() -> int:
    """Launch the UniversalTester Desktop GUI."""
    root = tk.Tk()
    app = UniversalTesterApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
