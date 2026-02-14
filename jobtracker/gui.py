"""Windows desktop GUI for the job tracker."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from typing import Optional

import customtkinter as ctk
from tkcalendar import DateEntry, Calendar

from . import database


def _show_date_picker(parent, entry: ctk.CTkEntry, position_widget=None, on_select=None) -> None:
    """Show a calendar popup near the given widget; on date selection, set the entry and optionally call on_select."""
    popup = ctk.CTkToplevel(parent)
    popup.title("Select Date")
    popup.geometry("280x250")
    if position_widget:
        parent.update_idletasks()
        wx = position_widget.winfo_rootx()
        wy = position_widget.winfo_rooty() + position_widget.winfo_height() + 4
        popup.geometry(f"280x250+{wx}+{wy}")
    popup.transient(parent)
    popup.grab_set()
    popup.focus_force()
    cal_frame = ctk.CTkFrame(popup, fg_color="transparent")
    cal_frame.pack(fill="both", expand=True, padx=10, pady=10)
    cal = Calendar(cal_frame, date_pattern="y-mm-dd")
    cal.pack()
    def on_ok():
        sel = cal.selection_get()
        if sel:
            entry.delete(0, "end")
            entry.insert(0, sel.strftime("%Y-%m-%d"))
        popup.grab_release()
        popup.destroy()
        if on_select:
            on_select()
    ctk.CTkButton(popup, text="OK", command=on_ok, width=80).pack(pady=(0, 10))

# Appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class JobFormDialog(ctk.CTkToplevel):
    """Modal dialog for adding or editing a job."""

    def __init__(
        self,
        parent,
        title: str,
        job: Optional[dict] = None,
        on_save=None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.title(title)
        self.on_save = on_save
        self.job = job
        self.result = None

        self.geometry("500x640")
        self.resizable(True, True)

        # Make modal
        self.transient(parent)
        self.grab_set()
        self.focus_force()

        self._build_ui()
        if job:
            self._load_job()

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        # Company
        ctk.CTkLabel(scroll, text="Company").pack(anchor="w", **pad)
        self.company_var = ctk.StringVar()
        ctk.CTkEntry(scroll, textvariable=self.company_var, width=400).pack(fill="x", **pad)

        # Position
        ctk.CTkLabel(scroll, text="Position").pack(anchor="w", **pad)
        self.position_var = ctk.StringVar()
        ctk.CTkEntry(scroll, textvariable=self.position_var, width=400).pack(fill="x", **pad)

        # Status
        ctk.CTkLabel(scroll, text="Status").pack(anchor="w", **pad)
        self.status_var = ctk.StringVar(value="applied")
        status_combo = ctk.CTkComboBox(
            scroll,
            values=database.STATUSES,
            variable=self.status_var,
            width=200,
        )
        status_combo.pack(anchor="w", **pad)

        # Applied date
        ctk.CTkLabel(scroll, text="Applied Date").pack(anchor="w", **pad)
        date_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        date_frame.pack(anchor="w", **pad)
        self.date_entry = DateEntry(date_frame, width=14, date_pattern="y-mm-d")
        self.date_entry.pack(side="left")

        # Location
        ctk.CTkLabel(scroll, text="Location").pack(anchor="w", **pad)
        self.location_var = ctk.StringVar()
        ctk.CTkEntry(scroll, textvariable=self.location_var, width=400).pack(fill="x", **pad)

        # Salary
        ctk.CTkLabel(scroll, text="Salary").pack(anchor="w", **pad)
        self.salary_var = ctk.StringVar()
        ctk.CTkEntry(scroll, textvariable=self.salary_var, width=200).pack(anchor="w", **pad)

        # URL
        ctk.CTkLabel(scroll, text="Job URL").pack(anchor="w", **pad)
        self.url_var = ctk.StringVar()
        ctk.CTkEntry(scroll, textvariable=self.url_var, width=400).pack(fill="x", **pad)

        # Job Description
        ctk.CTkLabel(scroll, text="Job Description").pack(anchor="w", **pad)
        self.description_text = ctk.CTkTextbox(scroll, height=100, width=400)
        self.description_text.pack(fill="x", **pad)

        # Notes
        ctk.CTkLabel(scroll, text="Notes").pack(anchor="w", **pad)
        self.notes_text = ctk.CTkTextbox(scroll, height=80, width=400)
        self.notes_text.pack(fill="x", **pad)

        # Buttons (fixed at bottom)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkButton(btn_frame, text="Save", command=self._on_save, width=100).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="Cancel", command=self._on_cancel, width=100, fg_color="gray").pack(side="left")

    def _load_job(self):
        if not self.job:
            return
        self.company_var.set(self.job.get("company", ""))
        self.position_var.set(self.job.get("position", ""))
        self.status_var.set(self.job.get("status", "applied"))
        ad = self.job.get("applied_date")
        if ad:
            try:
                d = datetime.strptime(ad, "%Y-%m-%d").date()
                self.date_entry.set_date(d)
            except (ValueError, TypeError):
                pass
        self.location_var.set(self.job.get("location", "") or "")
        self.salary_var.set(self.job.get("salary", "") or "")
        self.url_var.set(self.job.get("url", "") or "")
        self.description_text.delete("1.0", "end")
        self.description_text.insert("1.0", self.job.get("description", "") or "")
        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", self.job.get("notes", "") or "")

    def _get_values(self) -> dict:
        return {
            "company": self.company_var.get().strip(),
            "position": self.position_var.get().strip(),
            "status": self.status_var.get(),
            "applied_date": self.date_entry.get_date().strftime("%Y-%m-%d") if self.date_entry.get_date() else None,
            "location": self.location_var.get().strip() or None,
            "salary": self.salary_var.get().strip() or None,
            "url": self.url_var.get().strip() or None,
            "description": self.description_text.get("1.0", "end").strip() or None,
            "notes": self.notes_text.get("1.0", "end").strip() or None,
        }

    def _on_save(self):
        vals = self._get_values()
        if not vals["company"] or not vals["position"]:
            messagebox.showerror("Validation", "Company and Position are required.")
            return
        self.result = vals
        if self.on_save:
            self.on_save(vals)
        self.grab_release()
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.grab_release()
        self.destroy()


class JobDetailDialog(ctk.CTkToplevel):
    """Dialog showing full job details."""

    def __init__(self, parent, job: dict, on_edit=None, on_delete=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.title(f"Job #{job['id']}")
        self.job = job
        self.on_edit = on_edit
        self.on_delete = on_delete

        self.geometry("450x500")
        self._build_ui()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=(24, 10))

        inner = ctk.CTkFrame(scroll, fg_color="transparent")
        inner.pack(fill="both", expand=True)

        fields = [
            ("Company", self.job.get("company")),
            ("Position", self.job.get("position")),
            ("Status", self.job.get("status")),
            ("Applied", self.job.get("applied_date")),
            ("Location", self.job.get("location")),
            ("Salary", self.job.get("salary")),
            ("URL", self.job.get("url")),
        ]
        for label, value in fields:
            if value:
                ctk.CTkLabel(inner, text=f"{label}:", font=("", 12, "bold")).pack(anchor="w", pady=(8, 2))
                ctk.CTkLabel(inner, text=str(value), anchor="w", justify="left").pack(anchor="w", padx=(0, 0), pady=(0, 4))
                if label == "URL" and value.startswith("http"):
                    pass

        description = self.job.get("description")
        if description:
            ctk.CTkLabel(inner, text="Job Description:", font=("", 12, "bold")).pack(anchor="w", pady=(8, 2))
            desc_lbl = ctk.CTkLabel(inner, text=description, anchor="w", justify="left", wraplength=380)
            desc_lbl.pack(anchor="w", pady=(0, 4))

        notes = self.job.get("notes")
        if notes:
            ctk.CTkLabel(inner, text="Notes:", font=("", 12, "bold")).pack(anchor="w", pady=(8, 2))
            notes_lbl = ctk.CTkLabel(inner, text=notes, anchor="w", justify="left", wraplength=380)
            notes_lbl.pack(anchor="w", pady=(0, 4))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 20))
        if self.on_edit:
            ctk.CTkButton(btn_frame, text="Edit", command=self._edit, width=80).pack(side="left", padx=(0, 10))
        if self.on_delete:
            ctk.CTkButton(
                btn_frame,
                text="Delete",
                command=self._delete,
                width=80,
                fg_color="#c0392b",
                hover_color="#a93226",
            ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="Close", command=self.destroy, width=80).pack(side="right")

    def _edit(self):
        self.destroy()
        if self.on_edit:
            self.on_edit(self.job)

    def _delete(self):
        if messagebox.askyesno("Confirm Delete", f"Delete job at {self.job.get('company')}?"):
            if self.on_delete:
                self.on_delete(self.job["id"])
            self.destroy()


class JobTrackerApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("Job Tracker")
        self.geometry("900x550")
        self.minsize(700, 400)
        # CustomTkinter resets state on init; set before mainloop to start maximized
        self._state_before_windows_set_titlebar_color = "zoomed"

        database.init_db()

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        self.tabview = ctk.CTkTabview(self, width=800)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        self.tabview.add("Job Tracking")
        self.tabview.add("Settings")
        self.tabview.set("Job Tracking")

        # Job Tracking tab content
        job_tab = self.tabview.tab("Job Tracking")
        top = ctk.CTkFrame(job_tab, fg_color="transparent")
        top.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(top, text="Job Tracker", font=("", 24, "bold")).pack(side="left")

        self.stats_label = ctk.CTkLabel(top, text="", font=("", 12))
        self.stats_label.pack(side="left", padx=(30, 0))

        # Toolbar
        toolbar = ctk.CTkFrame(job_tab, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkButton(toolbar, text="+ Add Job", command=self._add_job, width=100).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            toolbar,
            text="Delete",
            command=self._delete_selected,
            width=80,
            fg_color="#c0392b",
            hover_color="#a93226",
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(toolbar, text="Refresh", command=self._refresh_list, width=80).pack(side="left")
        ctk.CTkLabel(toolbar, text="Change status:").pack(side="left", padx=(20, 5))
        self.change_status_combo = ctk.CTkComboBox(
            toolbar,
            values=database.STATUSES,
            width=120,
            state="disabled",
            command=self._on_change_status,
        )
        self.change_status_combo.pack(side="left", padx=(0, 0))

        # Filters
        filter_frame = ctk.CTkFrame(job_tab, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(filter_frame, text="Company:").pack(side="left", padx=(0, 5))
        self.filter_company = ctk.CTkEntry(filter_frame, width=120, placeholder_text="Filter...")
        self.filter_company.pack(side="left", padx=(0, 15))
        self.filter_company.bind("<KeyRelease>", lambda e: self._on_filter())
        ctk.CTkLabel(filter_frame, text="Position:").pack(side="left", padx=(0, 5))
        self.filter_position = ctk.CTkEntry(filter_frame, width=120, placeholder_text="Filter...")
        self.filter_position.pack(side="left", padx=(0, 15))
        self.filter_position.bind("<KeyRelease>", lambda e: self._on_filter())
        ctk.CTkLabel(filter_frame, text="Status:").pack(side="left", padx=(0, 5))
        self.filter_status = ctk.CTkComboBox(
            filter_frame,
            values=["all"] + database.STATUSES,
            width=100,
            command=lambda _: self._on_filter(),
        )
        self.filter_status.set("all")
        self.filter_status.pack(side="left", padx=(0, 15))
        ctk.CTkLabel(filter_frame, text="Date from:").pack(side="left", padx=(0, 5))
        df_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        df_frame.pack(side="left", padx=(0, 15))
        self.filter_date_from = ctk.CTkEntry(df_frame, width=100, placeholder_text="YYYY-MM-DD")
        self.filter_date_from.pack(side="left")
        self.filter_date_from.bind("<KeyRelease>", lambda e: self._on_filter())
        self.filter_date_from.bind("<Button-1>", lambda e: _show_date_picker(self, self.filter_date_from, self.filter_date_from, self._on_filter))
        self._cal_btn_from = ctk.CTkButton(df_frame, text="📅", width=36, command=lambda: _show_date_picker(self, self.filter_date_from, self._cal_btn_from, self._on_filter))
        self._cal_btn_from.pack(side="left", padx=(5, 0))
        ctk.CTkLabel(filter_frame, text="Date to:").pack(side="left", padx=(0, 5))
        dt_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        dt_frame.pack(side="left", padx=(0, 15))
        self.filter_date_to = ctk.CTkEntry(dt_frame, width=100, placeholder_text="YYYY-MM-DD")
        self.filter_date_to.pack(side="left")
        self.filter_date_to.bind("<KeyRelease>", lambda e: self._on_filter())
        self.filter_date_to.bind("<Button-1>", lambda e: _show_date_picker(self, self.filter_date_to, self.filter_date_to, self._on_filter))
        self._cal_btn_to = ctk.CTkButton(dt_frame, text="📅", width=36, command=lambda: _show_date_picker(self, self.filter_date_to, self._cal_btn_to, self._on_filter))
        self._cal_btn_to.pack(side="left", padx=(5, 0))
        ctk.CTkButton(filter_frame, text="Clear", command=self._clear_filters, width=60, fg_color="gray").pack(side="left", padx=(10, 0))

        # Table frame - use tkinter Treeview for grid
        table_frame = ctk.CTkFrame(job_tab, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        columns = ("id", "company", "position", "status", "applied_date", "location")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15, selectmode="browse")
        self.tree.heading("id", text="ID")
        self.tree.heading("company", text="Company")
        self.tree.heading("position", text="Position")
        self.tree.heading("status", text="Status")
        self.tree.heading("applied_date", text="Applied")
        self.tree.heading("location", text="Location")

        self.tree.column("id", width=50)
        self.tree.column("company", width=180)
        self.tree.column("position", width=200)
        self.tree.column("status", width=100)
        self.tree.column("applied_date", width=100)
        self.tree.column("location", width=150)

        scrollbar = ttk.Scrollbar(table_frame)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.tree.yview)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self._on_row_double_click)
        self.tree.bind("<Return>", self._on_row_double_click)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._on_selection_change())

        # Style for dark theme
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            rowheight=28,
        )
        style.configure("Treeview.Heading", background="#1f538d", foreground="white")
        style.map("Treeview", background=[("selected", "#1f538d")])
        style.map("Treeview.Heading", background=[("active", "#2a6bb5")])

        # Settings tab content
        self._build_settings_tab()

    def _build_settings_tab(self):
        settings_tab = self.tabview.tab("Settings")
        inner = ctk.CTkFrame(settings_tab, fg_color="transparent")
        inner.pack(fill="both", expand=True)

        ctk.CTkLabel(inner, text="Settings", font=("", 22, "bold")).pack(anchor="w", pady=(0, 20))

        # Appearance
        ctk.CTkLabel(inner, text="Appearance", font=("", 14, "bold")).pack(anchor="w", pady=(10, 5))
        theme_frame = ctk.CTkFrame(inner, fg_color="transparent")
        theme_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(theme_frame, text="Theme:").pack(side="left", padx=(0, 10))
        self.theme_combo = ctk.CTkComboBox(
            theme_frame,
            values=["Dark", "Light", "System"],
            width=120,
            command=self._on_theme_change,
        )
        current = ctk.get_appearance_mode()
        self.theme_combo.set("Dark" if current == "Dark" else "Light" if current == "Light" else "System")
        self.theme_combo.pack(side="left")

        # Database info
        ctk.CTkLabel(inner, text="Data", font=("", 14, "bold")).pack(anchor="w", pady=(20, 5))
        db_path = str(database.DATABASE_PATH)
        ctk.CTkLabel(inner, text=f"Database: {db_path}", font=("", 11), anchor="w").pack(anchor="w")

    def _on_theme_change(self, value: str):
        mode = value.lower()
        ctk.set_appearance_mode(mode)

    def _get_filters(self) -> dict:
        status = self.filter_status.get()
        return {
            "status_filter": None if status == "all" else status,
            "company": self.filter_company.get() or None,
            "position": self.filter_position.get() or None,
            "date_from": self.filter_date_from.get() or None,
            "date_to": self.filter_date_to.get() or None,
        }

    def _clear_filters(self):
        self.filter_company.delete(0, "end")
        self.filter_position.delete(0, "end")
        self.filter_status.set("all")
        self.filter_date_from.delete(0, "end")
        self.filter_date_to.delete(0, "end")
        self._refresh_list()

    def _on_filter(self, _=None):
        self._refresh_list()

    def _refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        filters = self._get_filters()
        jobs = database.get_all_jobs(**filters)
        for j in jobs:
            self.tree.insert(
                "",
                "end",
                iid=str(j["id"]),
                values=(
                    j["id"],
                    j["company"],
                    j["position"],
                    j["status"],
                    j.get("applied_date") or "",
                    j.get("location") or "",
                ),
            )
            self._update_stats()
        self._on_selection_change()

    def _update_stats(self):
        stats = database.get_stats()
        total = sum(stats.values())
        parts = [f"{s}: {c}" for s, c in stats.items()]
        self.stats_label.configure(text=f"Total: {total}  |  " + "  |  ".join(parts))

    def _get_selected_id(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(self.tree.item(sel[0])["values"][0])
        except (IndexError, ValueError):
            return None

    def _on_selection_change(self):
        """Update the change-status dropdown when selection changes."""
        job_id = self._get_selected_id()
        if job_id:
            job = database.get_job(job_id)
            if job:
                self.change_status_combo.configure(state="normal")
                self.change_status_combo.set(job.get("status", "applied"))
                return
        self.change_status_combo.configure(state="disabled")
        self.change_status_combo.set("")

    def _on_change_status(self, new_status: str):
        """Update the selected job's status."""
        job_id = self._get_selected_id()
        if job_id and new_status:
            database.update_job(job_id, status=new_status)
            self._refresh_list()
            self._on_selection_change()

    def _on_row_double_click(self, event=None):
        job_id = self._get_selected_id()
        if job_id:
            job = database.get_job(job_id)
            if job:
                JobDetailDialog(
                    self,
                    job,
                    on_edit=self._edit_job,
                    on_delete=self._delete_job,
                )

    def _add_job(self):
        def on_save(vals):
            database.add_job(
                company=vals["company"],
                position=vals["position"],
                status=vals["status"],
                applied_date=vals["applied_date"],
                salary=vals["salary"],
                location=vals["location"],
                url=vals["url"],
                description=vals.get("description"),
                notes=vals.get("notes"),
            )
            self._refresh_list()

        dlg = JobFormDialog(self, "Add Job", job=None, on_save=on_save)
        dlg.wait_window()

    def _edit_job(self, job: dict):
        def on_save(vals):
            database.update_job(
                job["id"],
                company=vals["company"],
                position=vals["position"],
                status=vals["status"],
                applied_date=vals["applied_date"],
                location=vals["location"],
                salary=vals["salary"],
                url=vals["url"],
                description=vals.get("description"),
                notes=vals.get("notes"),
            )
            self._refresh_list()

        JobFormDialog(self, f"Edit Job #{job['id']}", job=job, on_save=on_save)

    def _delete_selected(self):
        """Delete the currently selected job from the list."""
        job_id = self._get_selected_id()
        if not job_id:
            messagebox.showinfo("Delete", "Select a job to delete.")
            return
        job = database.get_job(job_id)
        if job and messagebox.askyesno("Confirm Delete", f"Delete {job.get('position')} at {job.get('company')}?"):
            database.delete_job(job_id)
            self._refresh_list()

    def _delete_job(self, job_id: int):
        database.delete_job(job_id)
        self._refresh_list()


def run_gui():
    """Launch the GUI application."""
    app = JobTrackerApp()
    app.update_idletasks()
    # Start full screen; use geometry fallback if zoom fails
    try:
        app.state("zoomed")
    except Exception:
        pass
    if app.state() != "zoomed":
        w = app.winfo_screenwidth()
        h = app.winfo_screenheight()
        app.geometry(f"{w}x{h}+0+0")
    app.mainloop()
