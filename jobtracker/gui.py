"""Windows desktop GUI for the job tracker."""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
from typing import Optional
import threading

import customtkinter as ctk
from tkcalendar import DateEntry, Calendar

from . import database
from . import resume_builder
from . import profile_manager


def _export_success_dialog(parent, path: str) -> None:
    """Show export confirmation with Open Path and Open File buttons."""
    dlg = ctk.CTkToplevel(parent)
    dlg.title("Exported")
    dlg.geometry("420x180")
    dlg.transient(parent)
    dlg.grab_set()

    ctk.CTkLabel(dlg, text="Resume saved to:", font=("", 12, "bold")).pack(anchor="w", padx=20, pady=(20, 6))
    path_lbl = ctk.CTkLabel(dlg, text=path, anchor="w", justify="left", wraplength=380)
    path_lbl.pack(anchor="w", padx=20, pady=(0, 16))

    btn_frame = ctk.CTkFrame(dlg, fg_color="transparent")
    btn_frame.pack(fill="x", padx=20, pady=(0, 20))
    ctk.CTkButton(btn_frame, text="Open Path", command=lambda: _open_path(path), width=100).pack(side="left", padx=(0, 10))
    ctk.CTkButton(btn_frame, text="Open File", command=lambda: _open_file(path), width=100).pack(side="left", padx=(0, 10))
    ctk.CTkButton(btn_frame, text="Close", command=dlg.destroy, width=80).pack(side="left")


def _open_path(path: str) -> None:
    """Open the folder containing the file in Explorer."""
    dirpath = os.path.dirname(path)
    if dirpath and os.path.exists(dirpath):
        os.startfile(dirpath)


def _open_file(path: str) -> None:
    """Open the file with default application."""
    if path and os.path.exists(path):
        os.startfile(path)


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
        ctk.CTkButton(btn_frame, text="Generate & Export to Word", command=self._generate_and_export_resume, width=180).pack(side="left", padx=(0, 10))
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

    def _generate_and_export_resume(self):
        """Generate tailored resume from form data and export as Word."""
        company = self.company_var.get().strip()
        position = self.position_var.get().strip()
        description = self.description_text.get("1.0", "end").strip() or None
        if not company or not position:
            messagebox.showerror("Validation", "Company and Position are required.")
            return
        if not description:
            messagebox.showwarning("Job Description", "Add the job description for better tailoring.")

        progress = ctk.CTkToplevel(self)
        progress.title("Generating Resume...")
        progress.geometry("320x80")
        progress.transient(self)
        progress.grab_set()
        ctk.CTkLabel(progress, text="Generating tailored resume...").pack(pady=20, padx=20)
        progress.update()

        result_holder = []

        def do_build():
            text, err = resume_builder.build_tailored_resume(
                job_company=company,
                job_position=position,
                job_description=description,
                base_resume=resume_builder.get_base_resume(),
            )
            result_holder.append((text, err))
            self.after(0, lambda: _finish(progress, result_holder))

        def _finish(win, holder):
            try:
                win.grab_release()
                win.destroy()
            except Exception:
                pass
            if not holder:
                return
            text, err = holder[0]
            if err:
                messagebox.showerror("Resume Builder", err)
                return
            if not text:
                messagebox.showwarning("Resume Builder", "No content generated.")
                return
            # Save as .docx
            default_name = f"Resume_{company}_{position}".replace(" ", "_").replace("/", "-")[:50] + ".docx"
            path = filedialog.asksaveasfilename(
                title="Export Resume",
                defaultextension=".docx",
                filetypes=[("Word Document", "*.docx"), ("All", "*.*")],
                initialfile=default_name,
            )
            if path:
                ok, export_err = resume_builder.export_to_docx(text, path)
                if ok:
                    _export_success_dialog(self, path)
                else:
                    messagebox.showerror("Export Failed", export_err or "Could not save file.")

        threading.Thread(target=do_build, daemon=True).start()


class JobDetailDialog(ctk.CTkToplevel):
    """Dialog showing full job details."""

    def __init__(self, parent, job: dict, on_edit=None, on_delete=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.title(f"Job #{job['id']}")
        self.job = job
        self.on_edit = on_edit
        self.on_delete = on_delete

        self.geometry("500x600")
        self._build_ui()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=(24, 10))

        inner = ctk.CTkFrame(scroll, fg_color="transparent")
        inner.pack(fill="both", expand=True)

        COPY_ICON = "\U0001F4CB"  # 📋 clipboard icon

        border_color = "#444" if ctk.get_appearance_mode() in ("Dark", None) else "#bbb"
        def _section(title: str = None, copy_command=None):
            """Create a section frame with border. If copy_command given, add icon button at top."""
            frame = ctk.CTkFrame(inner, fg_color="transparent", corner_radius=4, border_width=1, border_color=border_color)
            frame.pack(fill="x", pady=(0, 12))
            if title or copy_command:
                header = ctk.CTkFrame(frame, fg_color="transparent")
                header.pack(fill="x", padx=10, pady=(10, 6))
                if title:
                    ctk.CTkLabel(header, text=title, font=("", 12, "bold")).pack(side="left")
                if copy_command:
                    ctk.CTkButton(
                        header, text=COPY_ICON, command=copy_command, width=32, fg_color="transparent"
                    ).pack(side="right", padx=(8, 0))
            return frame

        # Basic info section
        info_section = _section("Job Details")
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
                row = ctk.CTkFrame(info_section, fg_color="transparent")
                row.pack(anchor="w", padx=10, pady=(8, 2))
                if label == "URL":
                    ctk.CTkButton(
                        row, text=COPY_ICON, command=self._copy_url, width=32, fg_color="transparent"
                    ).pack(side="left", padx=(0, 6))
                ctk.CTkLabel(row, text=f"{label}:", font=("", 12, "bold")).pack(side="left", padx=(0, 6))
                ctk.CTkLabel(row, text=str(value), anchor="w", justify="left").pack(side="left", fill="x", expand=True)
        ctk.CTkFrame(info_section, height=4, fg_color="transparent").pack(anchor="w")

        # Job Description section
        description = self.job.get("description")
        if description:
            desc_section = _section("Job Description", copy_command=self._copy_description)
            desc_lbl = ctk.CTkLabel(desc_section, text=description, anchor="w", justify="left", wraplength=400)
            desc_lbl.pack(anchor="w", padx=10, pady=(0, 10))

        # Notes section
        notes = self.job.get("notes")
        if notes:
            notes_section = _section("Notes")
            notes_lbl = ctk.CTkLabel(notes_section, text=notes, anchor="w", justify="left", wraplength=400)
            notes_lbl.pack(anchor="w", padx=10, pady=(0, 10))

        # Tailored Resume section
        resume_section = _section("Tailored Resume", copy_command=self._copy_resume)
        self.resume_textbox = ctk.CTkTextbox(resume_section, height=200, width=400)
        self.resume_textbox.pack(anchor="w", padx=10, pady=(0, 8))
        tailored_resume = self.job.get("tailored_resume")
        if tailored_resume:
            self.resume_textbox.insert("1.0", tailored_resume)
        self.resume_textbox.configure(state="disabled")
        resume_btn_row = ctk.CTkFrame(resume_section, fg_color="transparent")
        resume_btn_row.pack(anchor="w", padx=10, pady=(0, 10))
        ctk.CTkButton(resume_btn_row, text="Export to Word", command=self._export_resume, width=120).pack(side="left")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 20))
        ctk.CTkButton(btn_frame, text="Build Tailored Resume", command=self._build_resume, width=140).pack(side="left", padx=(0, 10))
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

    def _build_resume(self):
        """Build tailored resume for this job using OpenAI."""
        progress = ctk.CTkToplevel(self)
        progress.title("Building Resume...")
        progress.geometry("300x80")
        progress.transient(self)
        progress.grab_set()
        ctk.CTkLabel(progress, text="Generating tailored resume...").pack(pady=20, padx=20)
        progress.update()

        result_holder = []

        def do_build():
            text, err = resume_builder.build_tailored_resume(
                job_company=self.job.get("company", ""),
                job_position=self.job.get("position", ""),
                job_description=self.job.get("description"),
                base_resume=resume_builder.get_base_resume(),
            )
            result_holder.append((text, err))
            self.after(0, lambda: _finish(progress, result_holder))

        def _finish(win, holder):
            try:
                win.grab_release()
                win.destroy()
            except Exception:
                pass
            if holder:
                text, err = holder[0]
                if err:
                    messagebox.showerror("Resume Builder", err)
                elif text:
                    self._save_resume_and_refresh(text)
                else:
                    messagebox.showwarning("Resume Builder", "No content generated.")

        threading.Thread(target=do_build, daemon=True).start()

    def _save_resume_and_refresh(self, text: str):
        """Save tailored resume text to job and refresh display."""
        job_id = self.job.get("id")
        if job_id:
            database.update_job(job_id, tailored_resume=text)
        self.job["tailored_resume"] = text
        self.resume_textbox.configure(state="normal")
        self.resume_textbox.delete("1.0", "end")
        self.resume_textbox.insert("1.0", text)
        self.resume_textbox.configure(state="disabled")

    def _copy_url(self):
        url = self.job.get("url")
        if url:
            self.clipboard_clear()
            self.clipboard_append(url)

    def _copy_description(self):
        description = self.job.get("description")
        if description:
            self.clipboard_clear()
            self.clipboard_append(description)

    def _copy_resume(self):
        text = self.job.get("tailored_resume")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)

    def _export_resume(self):
        text = self.job.get("tailored_resume")
        if not text:
            messagebox.showinfo("Resume", "No tailored resume to export.")
            return
        default_name = f"Resume_{self.job.get('company', 'Job')}_{self.job.get('position', 'Application')}".replace(" ", "_").replace("/", "-")[:50] + ".docx"
        path = filedialog.asksaveasfilename(
            title="Export Resume",
            defaultextension=".docx",
            filetypes=[("Word Document", "*.docx"), ("All", "*.*")],
            initialfile=default_name,
        )
        if path:
            ok, err = resume_builder.export_to_docx(text, path)
            if ok:
                _export_success_dialog(self, path)
            else:
                messagebox.showerror("Export Failed", err or "Could not save file.")


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
        _tab_bg = ("gray95", "gray17")  # theme-aware: light, dark
        job_tab = self.tabview.tab("Job Tracking")
        job_tab.configure(fg_color=_tab_bg)
        top = ctk.CTkFrame(job_tab, fg_color=_tab_bg)
        top.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(top, text="Job Tracker", font=("", 24, "bold")).pack(side="left")

        self.stats_label = ctk.CTkLabel(top, text="", font=("", 12))
        self.stats_label.pack(side="left", padx=(30, 0))
        
        # Profile selector on Job Tracking page
        profile_selector_frame = ctk.CTkFrame(top, fg_color=_tab_bg)
        profile_selector_frame.pack(side="right")
        ctk.CTkLabel(profile_selector_frame, text="Profile:", font=("", 11)).pack(side="left", padx=(0, 5))
        self.job_tab_profile_combo = ctk.CTkComboBox(
            profile_selector_frame,
            values=profile_manager.list_profiles(),
            width=120,
            command=self._on_profile_change,
        )
        current_profile = profile_manager.get_current_profile()
        if current_profile:
            self.job_tab_profile_combo.set(current_profile)
        self.job_tab_profile_combo.pack(side="left")

        # Toolbar
        toolbar = ctk.CTkFrame(job_tab, fg_color=_tab_bg)
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

        # Filters - horizontally scrollable
        _tab_bg = ("gray95", "gray17")  # theme-aware: light, dark
        filter_container = ctk.CTkFrame(job_tab, fg_color=_tab_bg)
        filter_container.pack(fill="x", padx=20, pady=(0, 10))
        filter_frame = ctk.CTkScrollableFrame(
            filter_container, fg_color=_tab_bg, orientation="horizontal", height=50
        )
        filter_frame.pack(fill="x")
        ctk.CTkLabel(filter_frame, text="Company:").pack(side="left", padx=(0, 5))
        self.filter_company = ctk.CTkEntry(filter_frame, width=120, placeholder_text="Filter...")
        self.filter_company.pack(side="left", padx=(0, 15))
        self.filter_company.bind("<KeyRelease>", lambda e: self._on_filter())
        ctk.CTkLabel(filter_frame, text="Position:").pack(side="left", padx=(0, 5))
        self.filter_position = ctk.CTkEntry(filter_frame, width=120, placeholder_text="Filter...")
        self.filter_position.pack(side="left", padx=(0, 15))
        self.filter_position.bind("<KeyRelease>", lambda e: self._on_filter())
        ctk.CTkLabel(filter_frame, text="Description:").pack(side="left", padx=(0, 5))
        self.filter_description = ctk.CTkEntry(filter_frame, width=120, placeholder_text="Filter...")
        self.filter_description.pack(side="left", padx=(0, 15))
        self.filter_description.bind("<KeyRelease>", lambda e: self._on_filter())
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
        df_frame = ctk.CTkFrame(filter_frame, fg_color=_tab_bg)
        df_frame.pack(side="left", padx=(0, 15))
        self.filter_date_from = ctk.CTkEntry(df_frame, width=100, placeholder_text="YYYY-MM-DD")
        self.filter_date_from.pack(side="left")
        self.filter_date_from.bind("<KeyRelease>", lambda e: self._on_filter())
        self.filter_date_from.bind("<Button-1>", lambda e: _show_date_picker(self, self.filter_date_from, self.filter_date_from, self._on_filter))
        self._cal_btn_from = ctk.CTkButton(df_frame, text="📅", width=36, command=lambda: _show_date_picker(self, self.filter_date_from, self._cal_btn_from, self._on_filter))
        self._cal_btn_from.pack(side="left", padx=(5, 0))
        ctk.CTkLabel(filter_frame, text="Date to:").pack(side="left", padx=(0, 5))
        dt_frame = ctk.CTkFrame(filter_frame, fg_color=_tab_bg)
        dt_frame.pack(side="left", padx=(0, 15))
        self.filter_date_to = ctk.CTkEntry(dt_frame, width=100, placeholder_text="YYYY-MM-DD")
        self.filter_date_to.pack(side="left")
        self.filter_date_to.bind("<KeyRelease>", lambda e: self._on_filter())
        self.filter_date_to.bind("<Button-1>", lambda e: _show_date_picker(self, self.filter_date_to, self.filter_date_to, self._on_filter))
        self._cal_btn_to = ctk.CTkButton(dt_frame, text="📅", width=36, command=lambda: _show_date_picker(self, self.filter_date_to, self._cal_btn_to, self._on_filter))
        self._cal_btn_to.pack(side="left", padx=(5, 0))
        ctk.CTkButton(filter_frame, text="Clear", command=self._clear_filters, width=60, fg_color="gray").pack(side="left", padx=(10, 0))

        # Table frame - use tkinter Treeview for grid
        table_frame = ctk.CTkFrame(job_tab, fg_color=_tab_bg)
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

        self._apply_treeview_theme()

        # Settings tab content
        self._build_settings_tab()

    def _build_settings_tab(self):
        _tab_bg = ("gray95", "gray17")  # theme-aware: light, dark
        settings_tab = self.tabview.tab("Settings")
        settings_tab.configure(fg_color=_tab_bg)
        scroll = ctk.CTkScrollableFrame(settings_tab, fg_color=_tab_bg)
        scroll.pack(fill="both", expand=True)
        inner = ctk.CTkFrame(scroll, fg_color=_tab_bg)
        inner.pack(fill="both", expand=True)

        ctk.CTkLabel(inner, text="Settings", font=("", 22, "bold")).pack(anchor="w", pady=(0, 20))

        # Appearance
        ctk.CTkLabel(inner, text="Appearance", font=("", 14, "bold")).pack(anchor="w", pady=(10, 5))
        theme_frame = ctk.CTkFrame(inner, fg_color=_tab_bg)
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

        # OpenAI / Resume builder
        ctk.CTkLabel(inner, text="Resume Builder (OpenAI)", font=("", 14, "bold")).pack(anchor="w", pady=(20, 5))
        ctk.CTkLabel(inner, text="API Key:", font=("", 11)).pack(anchor="w", pady=(5, 2))
        self.api_key_entry = ctk.CTkEntry(inner, width=400, placeholder_text="sk-...", show="*")
        self.api_key_entry.pack(anchor="w", pady=(0, 5))
        if resume_builder.get_api_key():
            self.api_key_entry.insert(0, resume_builder.get_api_key())
        ctk.CTkLabel(inner, text="Model:", font=("", 11)).pack(anchor="w", pady=(10, 2))
        model_values = [
            "gpt-5.2",
            "gpt-5.1",
            "gpt-5",
            "gpt-5-mini",
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1-mini",
            "o1",
        ]
        self.model_combo = ctk.CTkComboBox(inner, values=model_values, width=200)
        self.model_combo.pack(anchor="w", pady=(0, 5))
        saved_model = resume_builder.get_model()
        self.model_combo.set(saved_model if saved_model in model_values else "gpt-4o-mini")
        ctk.CTkLabel(inner, text="Base Resume (your resume text to tailor):", font=("", 11)).pack(anchor="w", pady=(10, 2))
        resume_btn_frame = ctk.CTkFrame(inner, fg_color=_tab_bg)
        resume_btn_frame.pack(anchor="w", pady=(0, 5))
        ctk.CTkButton(resume_btn_frame, text="Upload .docx / .pdf", command=self._upload_resume, width=140).pack(side="left", padx=(0, 10))
        ctk.CTkButton(resume_btn_frame, text="Save", command=self._save_resume_settings, width=80).pack(side="left")
        self.base_resume_text = ctk.CTkTextbox(inner, height=120, width=500)
        self.base_resume_text.pack(anchor="w", pady=(0, 5))
        if resume_builder.get_base_resume():
            self.base_resume_text.insert("1.0", resume_builder.get_base_resume())

        # Profile management
        ctk.CTkLabel(inner, text="Profile", font=("", 14, "bold")).pack(anchor="w", pady=(20, 5))
        profile_frame = ctk.CTkFrame(inner, fg_color=_tab_bg)
        profile_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(profile_frame, text="Current Profile:").pack(side="left", padx=(0, 10))
        self.profile_combo = ctk.CTkComboBox(
            profile_frame,
            values=profile_manager.list_profiles(),
            width=150,
            command=self._on_profile_change,
        )
        current_profile = profile_manager.get_current_profile()
        if current_profile:
            self.profile_combo.set(current_profile)
        self.profile_combo.pack(side="left", padx=(0, 10))
        ctk.CTkButton(profile_frame, text="New Profile", command=self._create_profile, width=100).pack(side="left", padx=(0, 5))
        ctk.CTkButton(profile_frame, text="Rename", command=self._rename_profile, width=80).pack(side="left", padx=(0, 5))
        ctk.CTkButton(profile_frame, text="Delete", command=self._delete_profile, width=80, fg_color="#c0392b", hover_color="#a93226").pack(side="left")

        # Database info
        ctk.CTkLabel(inner, text="Data", font=("", 14, "bold")).pack(anchor="w", pady=(20, 5))
        db_path = str(database.get_database_path())
        self.db_path_label = ctk.CTkLabel(inner, text=f"Database: {db_path}", font=("", 11), anchor="w")
        self.db_path_label.pack(anchor="w")

    def _upload_resume(self):
        path = filedialog.askopenfilename(
            title="Select Resume",
            filetypes=[("Resume files", "*.pdf *.docx"), ("PDF", "*.pdf"), ("Word", "*.docx"), ("All", "*.*")],
        )
        if path:
            text, err = resume_builder.extract_text_from_file(path)
            if err:
                messagebox.showerror("Upload Failed", err)
            elif text:
                self.base_resume_text.delete("1.0", "end")
                self.base_resume_text.insert("1.0", text)
                messagebox.showinfo("Uploaded", "Resume text extracted. Click Save to keep it.")
            else:
                messagebox.showwarning("Upload", "No text found in file.")

    def _save_resume_settings(self):
        resume_builder.save_api_key(self.api_key_entry.get().strip())
        resume_builder.save_model(self.model_combo.get().strip())
        resume_builder.save_base_resume(self.base_resume_text.get("1.0", "end").strip())
        messagebox.showinfo("Saved", "Resume builder settings saved.")

    def _apply_treeview_theme(self):
        """Apply Treeview styles - white cell background, theme-aware heading."""
        cell_bg, cell_fg = "#ffffff", "#1a1a1a"
        heading_bg, heading_active, selected = "#1f538d", "#2a6bb5", "#1f538d"
        for st in database.STATUSES:
            for suffix in ("_0", "_1"):
                self.tree.tag_configure(f"{st}{suffix}", background=cell_bg, foreground=cell_fg)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=cell_bg,
            foreground=cell_fg,
            fieldbackground=cell_bg,
            rowheight=28,
        )
        style.configure("Treeview.Heading", background=heading_bg, foreground="white")
        style.map("Treeview", background=[("selected", selected)])
        style.map("Treeview.Heading", background=[("active", heading_active)])

    def _on_theme_change(self, value: str):
        display = value if value in ("Dark", "Light", "System") else value.capitalize()
        ctk.set_appearance_mode(display.lower())
        resume_builder.save_theme(display)
        self._apply_treeview_theme()

    def _reload_settings(self):
        """Reload settings from current profile's config."""
        # Reload API key
        self.api_key_entry.delete(0, "end")
        api_key = resume_builder.get_api_key()
        if api_key:
            self.api_key_entry.insert(0, api_key)
        # Reload model
        saved_model = resume_builder.get_model()
        model_values = self.model_combo.cget("values")
        self.model_combo.set(saved_model if saved_model in model_values else "gpt-4o-mini")
        # Reload base resume
        self.base_resume_text.delete("1.0", "end")
        base_resume = resume_builder.get_base_resume()
        if base_resume:
            self.base_resume_text.insert("1.0", base_resume)
        # Update database path display
        if hasattr(self, "db_path_label"):
            db_path = str(database.get_database_path())
            self.db_path_label.configure(text=f"Database: {db_path}")

    def _on_profile_change(self, profile_name: str):
        """Switch to a different profile and refresh data."""
        if profile_name:
            profile_manager.set_current_profile(profile_name)
            # Re-initialize database for new profile
            database.init_db()
            # Refresh job list
            self._refresh_list()
            # Reload settings for new profile
            self._reload_settings()
            # Update both profile combos
            profiles = profile_manager.list_profiles()
            self.profile_combo.configure(values=profiles)
            self.profile_combo.set(profile_name)
            if hasattr(self, "job_tab_profile_combo"):
                self.job_tab_profile_combo.configure(values=profiles)
                self.job_tab_profile_combo.set(profile_name)

    def _create_profile(self):
        """Create a new profile."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("New Profile")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Profile Name:", font=("", 12)).pack(anchor="w", padx=20, pady=(20, 5))
        name_entry = ctk.CTkEntry(dialog, width=350)
        name_entry.pack(padx=20, pady=(0, 20))
        name_entry.focus()
        
        def on_ok():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Profile name cannot be empty.")
                return
            if profile_manager.create_profile(name):
                profile_manager.set_current_profile(name)
                database.init_db()
                profiles = profile_manager.list_profiles()
                self.profile_combo.configure(values=profiles)
                self.profile_combo.set(name)
                if hasattr(self, "job_tab_profile_combo"):
                    self.job_tab_profile_combo.configure(values=profiles)
                    self.job_tab_profile_combo.set(name)
                self._refresh_list()
                self._reload_settings()
                dialog.destroy()
                messagebox.showinfo("Created", f"Profile '{name}' created and activated.")
            else:
                messagebox.showerror("Error", f"Profile '{name}' already exists.")
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkButton(btn_frame, text="Create", command=on_ok, width=100).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy, width=100, fg_color="gray").pack(side="left")
        name_entry.bind("<Return>", lambda e: on_ok())

    def _rename_profile(self):
        """Rename the current profile."""
        current = profile_manager.get_current_profile()
        if not current:
            messagebox.showinfo("No Profile", "No profile selected.")
            return
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Rename Profile")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="New Profile Name:", font=("", 12)).pack(anchor="w", padx=20, pady=(20, 5))
        name_entry = ctk.CTkEntry(dialog, width=350)
        name_entry.pack(padx=20, pady=(0, 20))
        name_entry.insert(0, current)
        name_entry.select_range(0, "end")
        name_entry.focus()
        
        def on_ok():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showerror("Error", "Profile name cannot be empty.")
                return
            if new_name == current:
                dialog.destroy()
                return
            if profile_manager.rename_profile(current, new_name):
                profiles = profile_manager.list_profiles()
                self.profile_combo.configure(values=profiles)
                self.profile_combo.set(new_name)
                if hasattr(self, "job_tab_profile_combo"):
                    self.job_tab_profile_combo.configure(values=profiles)
                    self.job_tab_profile_combo.set(new_name)
                dialog.destroy()
                messagebox.showinfo("Renamed", f"Profile renamed to '{new_name}'.\nPlease restart the application for changes to take effect.")
            else:
                messagebox.showerror("Error", f"Profile '{new_name}' already exists or rename failed.")
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkButton(btn_frame, text="Rename", command=on_ok, width=100).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy, width=100, fg_color="gray").pack(side="left")
        name_entry.bind("<Return>", lambda e: on_ok())

    def _delete_profile(self):
        """Delete the current profile."""
        current = profile_manager.get_current_profile()
        if not current:
            messagebox.showinfo("No Profile", "No profile selected.")
            return
        profiles = profile_manager.list_profiles()
        if len(profiles) <= 1:
            messagebox.showwarning("Cannot Delete", "Cannot delete the last profile.")
            return
        if messagebox.askyesno("Confirm Delete", f"Delete profile '{current}'?\n\nThis will permanently delete all jobs and settings for this profile."):
            if profile_manager.delete_profile(current):
                new_current = profile_manager.get_current_profile()
                profiles = profile_manager.list_profiles()
                self.profile_combo.configure(values=profiles)
                if hasattr(self, "job_tab_profile_combo"):
                    self.job_tab_profile_combo.configure(values=profiles)
                if new_current:
                    self.profile_combo.set(new_current)
                    if hasattr(self, "job_tab_profile_combo"):
                        self.job_tab_profile_combo.set(new_current)
                    database.init_db()
                    self._refresh_list()
                    self._reload_settings()
                messagebox.showinfo("Deleted", f"Profile '{current}' deleted.")
            else:
                messagebox.showerror("Error", "Failed to delete profile.")

    def _get_filters(self) -> dict:
        status = self.filter_status.get()
        return {
            "status_filter": None if status == "all" else status,
            "company": self.filter_company.get() or None,
            "position": self.filter_position.get() or None,
            "description": self.filter_description.get() or None,
            "date_from": self.filter_date_from.get() or None,
            "date_to": self.filter_date_to.get() or None,
        }

    def _clear_filters(self):
        self.filter_company.delete(0, "end")
        self.filter_position.delete(0, "end")
        self.filter_description.delete(0, "end")
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
        for idx, j in enumerate(jobs):
            status = j.get("status") or "applied"
            self.tree.insert(
                "",
                "end",
                iid=str(j["id"]),
                values=(
                    j["id"],
                    j["company"],
                    j["position"],
                    status,
                    j.get("applied_date") or "",
                    j.get("location") or "",
                ),
                tags=(f"{status}_{idx % 2}",),
            )
        self._update_stats(len(jobs))
        self._on_selection_change()

    def _update_stats(self, filtered_count: int = 0):
        stats = database.get_stats()
        total = sum(stats.values())
        parts = [f"{s}: {c}" for s, c in stats.items()]
        filtered_text = f"{filtered_count} job{'s' if filtered_count != 1 else ''}  |  "
        self.stats_label.configure(text=filtered_text + f"Total: {total}  |  " + "  |  ".join(parts))

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


def _show_profile_selection() -> str | None:
    """Show profile selection dialog. Returns selected profile name or None."""
    profiles = profile_manager.list_profiles()
    current = profile_manager.get_current_profile()
    
    if not profiles:
        # No profiles exist - create default
        profile_manager.create_profile("Default")
        profile_manager.set_current_profile("Default")
        return "Default"
    
    if current and current in profiles:
        return current
    
    # Show selection dialog
    root = ctk.CTk()
    root.title("Select Profile")
    root.geometry("400x250")
    root.withdraw()  # Hide until ready
    
    selected_profile = [None]
    
    def on_select():
        selected_profile[0] = profile_combo.get()
        if selected_profile[0]:
            profile_manager.set_current_profile(selected_profile[0])
        root.destroy()
    
    def on_new():
        name = new_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Profile name cannot be empty.")
            return
        if profile_manager.create_profile(name):
            profile_combo.configure(values=profile_manager.list_profiles())
            profile_combo.set(name)
            messagebox.showinfo("Created", f"Profile '{name}' created.")
        else:
            messagebox.showerror("Error", f"Profile '{name}' already exists.")
    
    inner = ctk.CTkFrame(root, fg_color="transparent")
    inner.pack(fill="both", expand=True, padx=20, pady=20)
    
    ctk.CTkLabel(inner, text="Select Profile", font=("", 18, "bold")).pack(anchor="w", pady=(0, 10))
    ctk.CTkLabel(inner, text="Each profile has its own jobs and settings.", font=("", 11)).pack(anchor="w", pady=(0, 15))
    
    profile_combo = ctk.CTkComboBox(inner, values=profiles, width=350)
    profile_combo.pack(fill="x", pady=(0, 15))
    if profiles:
        profile_combo.set(profiles[0])
    
    ctk.CTkLabel(inner, text="Or create new:", font=("", 11)).pack(anchor="w", pady=(0, 5))
    new_frame = ctk.CTkFrame(inner, fg_color="transparent")
    new_frame.pack(fill="x", pady=(0, 15))
    new_entry = ctk.CTkEntry(new_frame, width=250, placeholder_text="Profile name...")
    new_entry.pack(side="left", padx=(0, 10))
    ctk.CTkButton(new_frame, text="Create", command=on_new, width=90).pack(side="left")
    
    btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
    btn_frame.pack(fill="x")
    ctk.CTkButton(btn_frame, text="Select", command=on_select, width=100).pack(side="right", padx=(10, 0))
    
    def on_closing():
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.deiconify()
    root.mainloop()
    return selected_profile[0] if selected_profile[0] else (profiles[0] if profiles else None)


def run_gui():
    """Launch the GUI application."""
    # Ensure a profile is selected
    profile = _show_profile_selection()
    if not profile:
        # Fallback: use first profile or create default
        profiles = profile_manager.list_profiles()
        if profiles:
            profile = profiles[0]
            profile_manager.set_current_profile(profile)
        else:
            profile_manager.create_profile("Default")
            profile_manager.set_current_profile("Default")
            profile = "Default"
    
    # Initialize database for the selected profile
    database.init_db()
    
    saved_theme = resume_builder.get_theme()
    ctk.set_appearance_mode(saved_theme.lower())
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
