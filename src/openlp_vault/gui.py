import datetime
import json
import logging
import os
import socket
import sys
import tempfile
import time
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .auth import (
    AuthenticationCancelledError,
    authenticate,
    default_token_path,
    has_reusable_token,
)
from .backup import cleanup_backup_file, create_backup, upload_backup
from .config import load_config, save_config
from . import __version__
from .discovery import find_openlp_installation
from .legal import (
    CONTACT_EMAIL,
    COPYRIGHT_NOTICE,
    MAINTAINING_COMMUNITY,
    PROJECT_URL,
    read_legal_document,
)
from .restore import apply_backup, delete_backup, download_backup, list_backups
from .utils import format_drive_timestamp
from .i18n import _, detect_language, ngettext

LOG = logging.getLogger("openlp_vault.gui")

OAUTH_TIMEOUT_SECONDS = 120
DRIVE_SETUP_URL = (
    "https://github.com/ucbtrigales/openlp-vault/blob/main/docs/"
    f"{detect_language()}/drive_setup.md"
)
DRIVE_STATUS_COLORS = {
    "connected": {"background": "#d1e7dd", "foreground": "#0f5132"},
    "pending": {"background": "#cff4fc", "foreground": "#055160"},
    "disconnected": {"background": "#fff3cd", "foreground": "#664d03"},
}


def _asset_path(filename):
    """Locate a bundled GUI asset in source and frozen applications."""
    package_asset = Path(__file__).resolve().with_name("assets") / filename
    if package_asset.is_file():
        return package_asset

    # PyInstaller extracts one-file applications below ``sys._MEIPASS``. The
    # fallback also supports older bundles where data was placed at the root.
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        bundle_root = Path(bundle_root)
        for candidate in (
            bundle_root / "openlp_vault" / "assets" / filename,
            bundle_root / "assets" / filename,
            bundle_root / filename,
        ):
            if candidate.is_file():
                return candidate

    return package_asset


class OpenLPVaultGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OpenLP Vault")
        self.geometry("500x400")
        self.resizable(True, True)

        logo_path = _asset_path("openlp-vault-logo.png")
        try:
            self._application_logo_image = tk.PhotoImage(file=str(logo_path))
            self.iconphoto(True, self._application_logo_image)
        except (OSError, tk.TclError):
            self._application_logo_image = None
            LOG.warning("No se pudo cargar el icono de OpenLP Vault", exc_info=True)

        self.drive_service = None
        self.drive_user_email = None
        self.backups = []
        self.credentials_path = tk.StringVar(value="credentials.json")
        discovered_source = find_openlp_installation()
        self.source_path = tk.StringVar(
            value=str(discovered_source) if discovered_source is not None else ""
        )
        self.drive_folder_name = tk.StringVar(value="OpenLP Vault")

        self._load_config()
        self.startup_state = self._detect_startup_state()
        self._build_ui()
        if self._needs_first_run_setup():
            self.after_idle(lambda: self._open_configuration(first_run=True))
        else:
            self._refresh_backups(silent=True)

    def _detect_startup_state(self):
        """Detecta configuración, credenciales locales y sesión OAuth guardada."""
        credentials_path = Path(self.credentials_path.get()).expanduser()
        return {
            "has_config": bool(load_config()),
            "has_credentials_file": credentials_path.is_file(),
            "has_reusable_token": has_reusable_token(),
        }

    def _needs_first_run_setup(self):
        """Devuelve True cuando todavía no hay una sesión OAuth reutilizable."""
        return not self.startup_state["has_reusable_token"]

    def _validate_configuration_settings(self):
        credentials_path = Path(self.credentials_path.get()).expanduser()
        if not credentials_path.is_file():
            raise ValueError(_("Select an existing credentials.json file."))
        try:
            credentials_data = json.loads(credentials_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(_("The credentials file does not contain valid JSON.")) from exc

        oauth_client = credentials_data.get("installed") or credentials_data.get("web")
        if not isinstance(oauth_client, dict) or not oauth_client.get("client_id") or not oauth_client.get("client_secret"):
            raise ValueError(_("The file does not contain valid OAuth credentials."))

        source_path = Path(self.source_path.get()).expanduser()
        if not source_path.is_dir():
            raise ValueError(_("Select an existing OpenLP data directory."))

        folder_name = self.drive_folder_name.get().strip()
        if not folder_name:
            raise ValueError(_("Enter a name for the Google Drive folder."))

        return credentials_path, source_path, folder_name

    def _get_drive_user_email(self, drive_service):
        try:
            about = drive_service.about().get(fields="user(emailAddress)").execute()
        except Exception:
            LOG.warning("No se pudo obtener el email de la cuenta de Drive", exc_info=True)
            return None
        return about.get("user", {}).get("emailAddress")

    def _connected_drive_status(self):
        if self.drive_user_email:
            return _("Google Drive is connected.\nAccount: {email}").format(
                email=self.drive_user_email
            )
        return _("Google Drive is already connected.")

    def _set_drive_status(self, status_var, message, state="disconnected"):
        status_var.set(message)
        status_bar = getattr(self, "_configuration_status_bar", None)
        if status_bar is not None and status_bar.winfo_exists():
            status_bar.configure(**DRIVE_STATUS_COLORS[state])

    def _start_configuration_authentication(
        self, dialog, status_var, connect_button, disconnect_button, save_button, close_button
    ):
        try:
            credentials_path, source_path, folder_name = self._validate_configuration_settings()
        except ValueError as exc:
            self._set_drive_status(status_var, str(exc), "disconnected")
            messagebox.showwarning(_("Incomplete configuration"), str(exc), parent=dialog)
            return

        self.credentials_path.set(str(credentials_path))
        self.source_path.set(str(source_path))
        self.drive_folder_name.set(folder_name)
        save_config({
            "credentials_path": str(credentials_path),
            "source_path": str(source_path),
            "drive_folder_name": folder_name,
        })

        self._configuration_auth_sequence = getattr(self, "_configuration_auth_sequence", 0) + 1
        attempt_id = self._configuration_auth_sequence
        cancel_event = threading.Event()
        self._active_configuration_auth_attempt = attempt_id
        self._configuration_auth_cancel_event = cancel_event
        self._configuration_authenticating = True

        connect_button.configure(
            text=_("❌  Cancel connection"),
            state="normal",
            command=lambda: self._cancel_configuration_authentication(
                attempt_id, status_var, connect_button, disconnect_button, save_button, close_button
            ),
        )
        disconnect_button.configure(state="disabled")
        save_button.configure(state="disabled")
        close_button.configure(state="disabled")
        deadline = time.monotonic() + OAUTH_TIMEOUT_SECONDS
        self._update_auth_countdown(attempt_id, deadline, status_var)

        def _authenticate_and_verify():
            try:
                drive_service, _credentials = authenticate(
                    client_secrets_file=credentials_path,
                    oauth_timeout_seconds=OAUTH_TIMEOUT_SECONDS,
                    cancel_event=cancel_event,
                )
                backups = list_backups(drive_service)
                drive_user_email = self._get_drive_user_email(drive_service)
            except Exception as exc:
                self.after(0, lambda error=exc: self._finish_configuration_authentication(
                    attempt_id, dialog, status_var, connect_button, disconnect_button,
                    save_button, close_button, error=error
                ))
                return
            self.after(0, lambda: self._finish_configuration_authentication(
                attempt_id, dialog, status_var, connect_button, disconnect_button,
                save_button, close_button, drive_service=drive_service, backups=backups,
                drive_user_email=drive_user_email
            ))

        threading.Thread(target=_authenticate_and_verify, daemon=True).start()

    def _update_auth_countdown(self, attempt_id, deadline, status_var):
        if getattr(self, "_active_configuration_auth_attempt", None) != attempt_id:
            return
        remaining = max(0, int(deadline - time.monotonic()) + 1)
        minutes, seconds = divmod(remaining, 60)
        self._set_drive_status(
            status_var,
            _("Waiting for authorization in the browser… ({minutes:02d}:{seconds:02d}). "
              "You can cancel the connection.").format(minutes=minutes, seconds=seconds),
            "pending",
        )
        if remaining > 0:
            self.after(1000, lambda: self._update_auth_countdown(attempt_id, deadline, status_var))

    def _restore_connection_controls(
        self, status_var, connect_button, disconnect_button, save_button, close_button, message
    ):
        self._configuration_authenticating = False
        self._active_configuration_auth_attempt = None
        self._configuration_auth_cancel_event = None
        self._set_drive_status(status_var, message, "disconnected")
        connect_button.configure(text=_("🔗  Connect to Google Drive"), state="normal")
        disconnect_button.configure(state="normal" if has_reusable_token() else "disabled")
        save_button.configure(state="normal")
        close_button.configure(state="normal")

    def _cancel_configuration_authentication(
        self, attempt_id, status_var, connect_button, disconnect_button, save_button, close_button
    ):
        if getattr(self, "_active_configuration_auth_attempt", None) != attempt_id:
            return
        cancel_event = getattr(self, "_configuration_auth_cancel_event", None)
        if cancel_event is not None:
            cancel_event.set()
        self._restore_connection_controls(
            status_var, connect_button, disconnect_button, save_button, close_button,
            _("Authentication cancelled. You can try again.")
        )
        connect_button.configure(
            command=lambda: self._start_configuration_authentication(
                self._configuration_dialog, status_var, connect_button,
                disconnect_button, save_button, close_button
            )
        )
        self._append_log(_("Google Drive authentication cancelled."))

    def _finish_configuration_authentication(
        self, attempt_id, dialog, status_var, connect_button, disconnect_button,
        save_button, close_button, drive_service=None, backups=None, drive_user_email=None, error=None,
    ):
        if getattr(self, "_active_configuration_auth_attempt", None) != attempt_id:
            return

        if error is not None:
            if isinstance(error, AuthenticationCancelledError):
                message = _("Authentication cancelled. You can try again.")
            elif "timed out" in str(error).lower():
                message = _("Authorization expired after 2 minutes. You can try again.")
            else:
                message = _("Could not connect to Google Drive: {error}").format(error=error)
            self._restore_connection_controls(
                status_var, connect_button, disconnect_button, save_button, close_button, message
            )
            connect_button.configure(
                command=lambda: self._start_configuration_authentication(
                    dialog, status_var, connect_button, disconnect_button, save_button, close_button
                )
            )
            if not isinstance(error, AuthenticationCancelledError):
                messagebox.showerror(_("Connection error"), message, parent=dialog)
            return

        self._configuration_authenticating = False
        self._active_configuration_auth_attempt = None
        self._configuration_auth_cancel_event = None
        self.drive_service = drive_service
        self.drive_user_email = drive_user_email
        self.backups = backups or []
        self.startup_state = self._detect_startup_state()
        self._set_drive_status(
            status_var, self._connected_drive_status(), "connected"
        )
        connect_button.configure(text=_("✅  Google Drive connected"), state="disabled")
        disconnect_button.configure(state="normal")
        save_button.configure(state="normal")
        close_button.configure(state="normal")
        self._append_log(_("Google Drive connected successfully."))
        messagebox.showinfo(
            _("Connection complete"),
            _("Google Drive connected successfully and is ready to store backups."),
            parent=dialog,
        )

    def _disconnect_google_drive(self, dialog, status_var, connect_button, disconnect_button):
        confirmed = messagebox.askyesno(
            _("Disconnect Google Drive"),
            _("Remove the Google Drive authorization stored on this computer?"),
            parent=dialog,
        )
        if not confirmed:
            return

        try:
            default_token_path().unlink(missing_ok=True)
        except OSError as exc:
            messagebox.showerror(
                _("Disconnection error"),
                _("Could not remove the saved authorization: {error}").format(error=exc),
                parent=dialog,
            )
            return

        self.drive_service = None
        self.drive_user_email = None
        self.backups = []
        self.startup_state = self._detect_startup_state()
        self._set_drive_status(
            status_var, _("Google Drive has not been connected yet."), "disconnected"
        )
        connect_button.configure(text=_("🔗  Connect to Google Drive"), state="normal")
        disconnect_button.configure(state="disabled")
        self._append_log(_("Google Drive disconnected; the local token was removed."))

    def _close_configuration(self, dialog):
        if getattr(self, "_configuration_authenticating", False):
            messagebox.showwarning(
                _("Authentication in progress"),
                _("Wait for authentication to finish before closing this window."),
                parent=dialog,
            )
            return
        dialog.destroy()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=18)
        main_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        if sys.platform in {"darwin", "win32"}:
            style.theme_use("clam")
        style.configure("Bold.TButton", font=(None, 10, "bold"))
        style.configure("ActionDialog.TButton", font=(None, 11))
        style.configure("ActionDialogBold.TButton", font=(None, 11, "bold"))
        style.configure("Footer.TLabel", font=(None, 9), foreground="#6c757d")

        heading_frame = ttk.Frame(main_frame)
        heading_frame.pack(pady=(0, 12))
        if self._application_logo_image is not None:
            scale_factor = max(
                1, (self._application_logo_image.width() + 63) // 64
            )
            self._main_logo_image = self._application_logo_image.subsample(
                scale_factor
            )
            ttk.Label(heading_frame, image=self._main_logo_image).pack(
                side="left", padx=(0, 10)
            )
        ttk.Label(
            heading_frame, text="OpenLP Vault", font=("TkDefaultFont", 20, "bold")
        ).pack(side="left")

        ttk.Button(main_frame, text=_("⬆️  Create and upload a backup"), command=self._open_backup_dialog).pack(fill="x", pady=8)
        ttk.Button(main_frame, text=_("⬇️  Download and restore a backup"), command=self._open_restore_dialog).pack(fill="x", pady=8)
        ttk.Button(main_frame, text=_("⚙️  Settings"), command=self._open_configuration).pack(fill="x", pady=12)

        self.log_text = tk.Text(main_frame, height=8, wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=False, pady=(0, 8))

    def _append_log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _authenticate(self):
        self._append_log(_("Authenticating with Google Drive..."))
        try:
            drive_service, _credentials = authenticate(
                client_secrets_file=self.credentials_path.get()
            )
            self.drive_service = drive_service
            self.drive_user_email = self._get_drive_user_email(drive_service)
            self._refresh_backups()
        except Exception as exc:
            LOG.exception("Error de autenticación")
            messagebox.showerror(_("Error"), _("Could not authenticate: {error}").format(error=exc), parent=self)
            self._append_log(_("Error: {error}").format(error=exc))

    def _open_backup_dialog(self):
        default_name = self._default_backup_filename()
        backup_name_var = tk.StringVar(value=default_name)

        dialog = tk.Toplevel(self)
        dialog.title(_("Create and upload backup"))
        dialog.geometry("700x190")
        dialog.resizable(True, True)

        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=_("ZIP file name:")).pack(anchor="w", pady=(0, 8))
        ttk.Entry(frame, textvariable=backup_name_var).pack(fill="x", pady=(0, 8))
        drive_available = self.drive_service is not None
        availability_message = (
            _("The file will be uploaded to Google Drive.")
            if drive_available
            else _("Google Drive is not connected; only a local backup can be created.")
        )
        ttk.Label(frame, text=availability_message).pack(anchor="w", pady=(0, 12))

        button_frame = ttk.Frame(frame)
        button_frame.pack(side="bottom", fill="x", pady=(12, 0))
        for column in range(3):
            button_frame.columnconfigure(column, weight=1, uniform="backup_actions")

        upload_button = ttk.Button(
            button_frame,
            text=_("⬆️  Create and upload"),
            command=lambda: self._backup(backup_name_var.get(), dialog),
            style="ActionDialogBold.TButton",
            state="normal" if drive_available else "disabled",
        )
        upload_button.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ttk.Button(
            button_frame,
            text=_("💾  Create local backup"),
            command=lambda: self._create_local_backup(backup_name_var.get(), dialog),
            style="ActionDialog.TButton",
            state="normal",
        ).grid(row=0, column=1, sticky="nsew", padx=6)
        ttk.Button(
            button_frame,
            text=_("❌  Cancel"),
            command=dialog.destroy,
            style="ActionDialog.TButton",
        ).grid(row=0, column=2, sticky="nsew", padx=(6, 0))

    def _default_backup_filename(self):
        hostname = socket.gethostname().replace(" ", "_")
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        return f"openlp_backup_{hostname}_{timestamp}"

    def _backup(self, zip_name=None, dialog=None):
        if dialog:
            dialog.destroy()

        self._append_log(_("Starting backup..."))
        source = self.source_path.get() or find_openlp_installation()
        if not source:
            messagebox.showwarning(_("Warning"), _("The OpenLP installation was not found. Set its path in Settings."), parent=self)
            return

        if not self.source_path.get():
            self.source_path.set(str(source))
            self._append_log(_("OpenLP path detected automatically: {source}").format(source=source))

        try:
            self._ensure_authenticated()
        except RuntimeError as exc:
            self._append_log(str(exc))
            return

        # Crear diálogo modal de progreso
        progress = tk.Toplevel(self)
        progress.title(_("Creating and uploading backup"))
        progress.resizable(True, True)
        progress.transient(self)
        progress.grab_set()

        p_frame = ttk.Frame(progress, padding=12)
        p_frame.pack(fill="both", expand=True)
        ttk.Label(p_frame, text=_("Please wait — creating and uploading the backup...")).pack(anchor="center", pady=(4, 8))
        pb = ttk.Progressbar(p_frame, mode="indeterminate", length=360)
        pb.pack(pady=(0, 8))
        pb.start(12)

        def _do_backup():
            try:
                self._append_log(_("Creating the backup..."))
                backup_path = create_backup(source, zip_name=zip_name)
                self._append_log(_("Backup file created: {path}").format(path=backup_path))
                folder_name = self.drive_folder_name.get() or "OpenLP Vault"
                self._append_log(_("Uploading the backup..."))
                metadata = upload_backup(backup_path, self.drive_service, folder_name=folder_name)
                self._append_log(_("Backup uploaded: {name} (id={id})").format(name=metadata.get("name"), id=metadata.get("id")))

                def _on_success():
                    try:
                        pb.stop()
                    finally:
                        progress.grab_release()
                        progress.destroy()
                    cleanup_backup_file(backup_path)
                    self._refresh_backups()
                    messagebox.showinfo(_("Success"), _("Backup created and uploaded successfully."), parent=self)

                self.after(0, _on_success)
            except Exception as exc:
                LOG.exception("Error al crear/subir respaldo")

                def _on_error():
                    try:
                        pb.stop()
                    finally:
                        try:
                            progress.grab_release()
                        except Exception:
                            pass
                        progress.destroy()
                    messagebox.showerror(_("Error"), _("Could not create or upload the backup: {error}").format(error=exc), parent=self)
                    self._append_log(_("Error: {error}").format(error=exc))

                self.after(0, _on_error)

        thread = threading.Thread(target=_do_backup, daemon=True)
        thread.start()

    def _create_local_backup(self, zip_name=None, dialog=None):
        if dialog:
            dialog.destroy()

        self._append_log(_("Starting local backup creation..."))
        source = self.source_path.get() or find_openlp_installation()
        if not source:
            messagebox.showwarning(_("Warning"), _("The OpenLP installation was not found. Set its path in Settings."), parent=self)
            return

        if not self.source_path.get():
            self.source_path.set(str(source))
            self._append_log(_("OpenLP path detected automatically: {source}").format(source=source))

        # Crear diálogo modal de progreso para creación local
        progress = tk.Toplevel(self)
        progress.title(_("Creating local backup"))
        progress.resizable(True, True)
        progress.transient(self)
        progress.grab_set()

        p_frame = ttk.Frame(progress, padding=12)
        p_frame.pack(fill="both", expand=True)
        ttk.Label(p_frame, text=_("Please wait — creating local backup...")).pack(anchor="center", pady=(4, 8))
        pb = ttk.Progressbar(p_frame, mode="indeterminate", length=360)
        pb.pack(pady=(0, 8))
        pb.start(12)

        def _do_local():
            try:
                self._append_log(_("Creating local backup..."))
                backup_path = create_backup(source, zip_name=zip_name)
                self._append_log(_("Backup file created: {path}").format(path=backup_path))

                def _on_success():
                    try:
                        pb.stop()
                    finally:
                        progress.grab_release()
                        progress.destroy()
                    messagebox.showinfo(_("Success"), _("Local backup created: {path}").format(path=backup_path), parent=self)

                self.after(0, _on_success)
            except Exception as exc:
                LOG.exception("Error al crear respaldo local")

                def _on_error():
                    try:
                        pb.stop()
                    finally:
                        try:
                            progress.grab_release()
                        except Exception:
                            pass
                        progress.destroy()
                    messagebox.showerror(_("Error"), _("Could not create the local backup: {error}").format(error=exc), parent=self)
                    self._append_log(_("Error: {error}").format(error=exc))

                self.after(0, _on_error)

        thread = threading.Thread(target=_do_local, daemon=True)
        thread.start()

    def _open_restore_dialog(self):
        if self.drive_service is None:
            messagebox.showwarning(
                _("Google Drive not connected"),
                _("No Google Drive connection has been established. Open Settings to connect it."),
                parent=self,
            )
            return

        progress = tk.Toplevel(self)
        progress.title(_("Refreshing backups"))
        progress.resizable(True, True)
        progress.transient(self)
        progress.grab_set()
        progress.protocol("WM_DELETE_WINDOW", lambda: None)

        progress_frame = ttk.Frame(progress, padding=16)
        progress_frame.pack(fill="both", expand=True)
        ttk.Label(
            progress_frame,
            text=_("Checking available backups in Google Drive…"),
        ).pack(pady=(0, 10))
        progress_bar = ttk.Progressbar(progress_frame, mode="indeterminate", length=380)
        progress_bar.pack(fill="x")
        progress_bar.start(12)

        def _finish_loading():
            progress_bar.stop()
            try:
                progress.grab_release()
            except Exception:
                pass
            progress.destroy()

        def _load_backups():
            try:
                backups = list_backups(self.drive_service)
            except Exception as exc:
                def _on_error(error=exc):
                    _finish_loading()
                    self.backups = []
                    LOG.error(
                        "No se pudo actualizar la lista de respaldos",
                        exc_info=(type(error), error, error.__traceback__),
                    )
                    messagebox.showerror(
                        _("Error retrieving backups"),
                        _("Could not refresh the backup list: {error}").format(error=error),
                        parent=self,
                    )

                self.after(0, _on_error)
                return

            def _on_success():
                _finish_loading()
                self.backups = backups
                if not backups:
                    messagebox.showwarning(
                        _("Warning"), _("No backups are available."), parent=self
                    )
                    return
                self._show_restore_dialog()

            self.after(0, _on_success)

        threading.Thread(target=_load_backups, daemon=True).start()

    def _show_restore_dialog(self):
        sorted_backups = sorted(
            self.backups, key=lambda item: item.get("createdTime", ""), reverse=True
        )
        dialog = tk.Toplevel(self)
        dialog.title(_("Download and restore a backup"))
        dialog.geometry("820x480")
        dialog.resizable(True, True)

        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text=_("Select the backup to restore:"),
            font=("TkDefaultFont", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        listbox = tk.Listbox(frame, height=12, width=92)
        listbox.pack(fill="both", expand=True, padx=2)
        for item in sorted_backups:
            created = format_drive_timestamp(item.get("createdTime", ""))
            listbox.insert("end", f"{item.get('name')} — {created}")
        listbox.selection_set(0)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=(12, 0), padx=2)
        for column in range(3):
            button_frame.columnconfigure(column, weight=1, uniform="restore_actions")

        ttk.Button(
            button_frame,
            text=_("⬇️  Download and restore"),
            command=lambda: self._restore_selected(listbox, dialog),
            style="ActionDialogBold.TButton",
        ).grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ttk.Button(
            button_frame,
            text=_("🗑️  Delete"),
            command=lambda: self._delete_selected(listbox, dialog),
            style="ActionDialog.TButton",
        ).grid(row=0, column=1, sticky="nsew", padx=6)
        ttk.Button(
            button_frame,
            text=_("❌  Cancel"),
            command=dialog.destroy,
            style="ActionDialog.TButton",
        ).grid(row=0, column=2, sticky="nsew", padx=(6, 0))

    def _restore_selected(self, listbox, dialog):
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning(_("Warning"), _("Select a backup to restore."), parent=dialog)
            return
        sorted_backups = self._get_sorted_backups()
        backup = sorted_backups[selection[0]]
        destination = self.source_path.get() or find_openlp_installation()
        if not destination:
            messagebox.showwarning(_("Warning"), _("The OpenLP destination was not found. Set its path in Settings."), parent=self)
            return
        # Pedir confirmación antes de restaurar
        parent = dialog
        parent.attributes("-topmost", True)
        confirmed = messagebox.askyesno(
            _("Confirm restore"),
            _("Download and restore {name}? The OpenLP installation at {destination} will be overwritten.").format(name=backup.get("name"), destination=destination),
            parent=parent,
        )
        parent.attributes("-topmost", False)
        if not confirmed:
            return
        dialog.destroy()
        self._restore_backup(backup)

    def _delete_selected(self, listbox, parent):
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning(_("Warning"), _("Select a backup to delete."), parent=parent)
            return
        sorted_backups = self._get_sorted_backups()
        backup = sorted_backups[selection[0]]
        parent.attributes("-topmost", True)
        confirmed = messagebox.askyesno(_("Confirm deletion"), _("Delete backup {name}?").format(name=backup.get("name")), parent=parent)
        parent.attributes("-topmost", False)
        if not confirmed:
            return

        try:
            delete_backup(backup.get('id'), self.drive_service)
            self._append_log(_("Backup deleted: {name}").format(name=backup.get("name")))
            self._refresh_backups()
            listbox.delete(selection[0])
            messagebox.showinfo(_("Success"), _("Backup deleted successfully."), parent=parent)
        except Exception as exc:
            LOG.exception("Error al eliminar respaldo")
            messagebox.showerror(_("Error"), _("Could not delete the backup: {error}").format(error=exc), parent=parent)
            self._append_log(_("Error: {error}").format(error=exc))

    def _get_sorted_backups(self):
        return sorted(self.backups, key=lambda item: item.get("createdTime", ""), reverse=True)

    def _restore_backup(self, backup):
        self._append_log(_("Restoring backup {name}...").format(name=backup.get("name")))
        destination = self.source_path.get() or find_openlp_installation()
        if not destination:
            messagebox.showwarning(_("Warning"), _("The OpenLP destination was not found."), parent=self)
            return

        # Crear diálogo modal de progreso
        progress = tk.Toplevel(self)
        progress.title(_("Downloading and restoring backup"))
        progress.resizable(True, True)
        progress.transient(self)
        progress.grab_set()

        p_frame = ttk.Frame(progress, padding=12)
        p_frame.pack(fill="both", expand=True)
        ttk.Label(p_frame, text=_("Please wait — downloading and applying the backup...")).pack(anchor="center", pady=(4, 8))
        pb = ttk.Progressbar(p_frame, mode="indeterminate", length=360)
        pb.pack(pady=(0, 8))
        pb.start(12)

        def _do_restore():
            try:
                archive_path = Path(tempfile.mkdtemp(prefix="openlp_restore_")) / f"{backup.get('id')}.zip"
                self._append_log(_("Downloading backup {id}...").format(id=backup.get("id")))
                download_backup(backup.get('id'), self.drive_service, archive_path)
                self._append_log(_("Applying backup to {destination}...").format(destination=destination))
                apply_backup(archive_path, destination)
                self._append_log(_("Restore complete."))

                def _on_success():
                    try:
                        pb.stop()
                    finally:
                        progress.grab_release()
                        progress.destroy()
                    cleanup_backup_file(archive_path)
                    messagebox.showinfo(_("Success"), _("Restore completed successfully."), parent=self)

                self.after(0, _on_success)
            except Exception as exc:
                LOG.exception("Error al restaurar respaldo")

                def _on_error():
                    try:
                        pb.stop()
                    finally:
                        try:
                            progress.grab_release()
                        except Exception:
                            pass
                        progress.destroy()
                    messagebox.showerror(_("Error"), _("Could not restore the backup: {error}").format(error=exc), parent=self)
                    self._append_log(_("Error: {error}").format(error=exc))

                self.after(0, _on_error)

        thread = threading.Thread(target=_do_restore, daemon=True)
        thread.start()

    def _refresh_backups(self, silent=False):
        if not silent:
            self._append_log(_("Checking backups in Drive..."))
        try:
            self._ensure_authenticated()
            self.backups = list_backups(self.drive_service)
            if not silent:
                self._append_log(ngettext("{count} backup found.", "{count} backups found.", len(self.backups)).format(count=len(self.backups)))
        except Exception:
            self.backups = []
            if not silent:
                self._append_log(_("Not authenticated yet, or backups could not be listed."))

    def _show_legal_document(self, name, title, parent):
        try:
            content = read_legal_document(name)
        except (OSError, ValueError) as exc:
            messagebox.showerror(
                _("Error"),
                _("Could not open {name}: {error}").format(name=name, error=exc),
                parent=parent,
            )
            return

        viewer = tk.Toplevel(parent)
        viewer.title(title)
        viewer.geometry("780x560")
        viewer.minsize(560, 360)
        viewer.transient(parent)

        frame = ttk.Frame(viewer, padding=12)
        frame.pack(fill="both", expand=True)
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        text = tk.Text(
            text_frame,
            wrap="word",
            state="normal",
            yscrollcommand=scrollbar.set,
            padx=8,
            pady=8,
        )
        text.insert("1.0", content)
        text.configure(state="disabled")
        text.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=text.yview)
        ttk.Button(frame, text=_("Close"), command=viewer.destroy, width=14).pack(
            anchor="e", pady=(10, 0)
        )

    def _open_about_dialog(self, parent=None):
        owner = parent or self
        existing_dialog = getattr(self, "_about_dialog", None)
        if existing_dialog is not None and existing_dialog.winfo_exists():
            existing_dialog.deiconify()
            existing_dialog.lift()
            existing_dialog.focus_set()
            return

        dialog = tk.Toplevel(owner)
        self._about_dialog = dialog
        dialog.bind(
            "<Destroy>",
            lambda event: setattr(self, "_about_dialog", None)
            if event.widget is dialog
            else None,
        )
        dialog.title(_("About OpenLP Vault"))
        dialog.geometry("620x410")
        dialog.resizable(True, True)
        dialog.transient(owner)

        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill="both", expand=True)
        heading_frame = ttk.Frame(frame)
        heading_frame.pack(fill="x", pady=(0, 12))
        logo_path = _asset_path("openlp-vault-logo.png")
        try:
            logo_image = tk.PhotoImage(file=str(logo_path))
            scale_factor = max(1, (logo_image.width() + 79) // 80)
            self._about_logo_image = logo_image.subsample(scale_factor)
            ttk.Label(heading_frame, image=self._about_logo_image).pack(
                side="left", padx=(0, 14)
            )
        except (OSError, tk.TclError):
            LOG.warning("No se pudo cargar el logo de OpenLP Vault", exc_info=True)
        ttk.Label(
            heading_frame,
            text=f"OpenLP Vault {__version__}",
            font=("TkDefaultFont", 16, "bold"),
        ).pack(side="left")
        ttk.Label(frame, text=COPYRIGHT_NOTICE).pack(anchor="w")

        background = ttk.Style().lookup("TFrame", "background") or self.cget("background")
        email_label = tk.Label(
            frame,
            text=CONTACT_EMAIL,
            foreground="#0563c1",
            background=background,
            cursor="hand2",
            font=("TkDefaultFont", 10, "underline"),
        )
        email_label.pack(anchor="w", pady=(2, 12))
        email_label.bind(
            "<Button-1>",
            lambda _event: webbrowser.open(f"mailto:{CONTACT_EMAIL}"),
        )

        ttk.Label(
            frame,
            text=_(
                "Free software licensed under GNU GPL version 3 or later "
                "(GPL-3.0-or-later)."
            ),
            wraplength=580,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))
        ttk.Label(
            frame,
            text=_("Maintained by the community of {community}.").format(
                community=MAINTAINING_COMMUNITY
            ),
            wraplength=580,
            justify="left",
        ).pack(anchor="w")
        ttk.Label(
            frame,
            text=_("Contributors retain copyright in their contributions."),
            wraplength=580,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        project_label = tk.Label(
            frame,
            text=PROJECT_URL,
            foreground="#0563c1",
            background=background,
            cursor="hand2",
            font=("TkDefaultFont", 10, "underline"),
        )
        project_label.pack(anchor="w", pady=(0, 14))
        project_label.bind(
            "<Button-1>", lambda _event: webbrowser.open_new_tab(PROJECT_URL)
        )

        buttons = ttk.Frame(frame)
        buttons.pack(side="bottom", fill="x")
        ttk.Button(
            buttons,
            text=_("View license"),
            command=lambda: self._show_legal_document(
                "LICENSE", _("GNU General Public License"), dialog
            ),
        ).pack(side="left")
        ttk.Button(
            buttons,
            text=_("View legal notice"),
            command=lambda: self._show_legal_document(
                "NOTICE", _("Legal notice"), dialog
            ),
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            buttons, text=_("Close"), command=dialog.destroy, width=14
        ).pack(side="right")

        dialog.focus_set()

    def _open_configuration(self, first_run=False):
        existing_dialog = getattr(self, "_configuration_dialog", None)
        if existing_dialog is not None and existing_dialog.winfo_exists():
            existing_dialog.deiconify()
            existing_dialog.lift()
            existing_dialog.focus_set()
            return

        dialog = tk.Toplevel(self)
        self._configuration_dialog = dialog
        dialog.bind(
            "<Destroy>",
            lambda event: setattr(self, "_configuration_dialog", None) if event.widget is dialog else None,
        )
        dialog.title(_("Settings"))
        dialog.geometry("800x480")
        dialog.resizable(True, True)
        dialog.transient(self)
        self._configuration_authenticating = False
        self._active_configuration_auth_attempt = None
        self._configuration_auth_cancel_event = None

        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill="both", expand=True)

        heading = _("Set up OpenLP Vault") if first_run else _("Settings")
        ttk.Label(
            frame, text=heading, font=("TkDefaultFont", 14, "bold")
        ).pack(anchor="w", pady=(0, 8))
        if first_run:
            ttk.Label(
                frame,
                text=_("Complete these fields and connect Google Drive to store and restore backups."),
                wraplength=760,
                justify="left",
            ).pack(anchor="w", pady=(0, 10))

        ttk.Label(
            frame,
            text=_("Credentials file path (credentials.json):"),
        ).pack(anchor="w", pady=(6, 0))
        credentials_row = ttk.Frame(frame)
        credentials_row.pack(fill="x", pady=2)
        ttk.Entry(credentials_row, textvariable=self.credentials_path).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(
            credentials_row,
            text=_("Browse…"),
            command=lambda: self._choose_credentials(dialog),
        ).pack(side="right", padx=(8, 0))

        frame_background = ttk.Style().lookup("TFrame", "background") or self.cget("background")
        credentials_help_label = tk.Label(
            frame,
            text=_("How do I get the credentials file?"),
            foreground="#0563c1",
            background=frame_background,
            cursor="hand2",
            font=("TkDefaultFont", 10, "underline"),
        )
        credentials_help_label.pack(anchor="w", pady=(0, 8))
        credentials_help_label.bind(
            "<Button-1>",
            lambda _event: webbrowser.open_new_tab(DRIVE_SETUP_URL),
        )

        connection_available = self.drive_service is not None or has_reusable_token()
        if self.drive_service is not None:
            initial_status = self._connected_drive_status()
            initial_status_state = "connected"
        elif connection_available:
            initial_status = _("A saved authorization is available. You can verify the connection.")
            initial_status_state = "pending"
        else:
            initial_status = _("Google Drive has not been connected yet.")
            initial_status_state = "disconnected"
        status_var = tk.StringVar(value=initial_status)

        connection_frame = ttk.Frame(frame)
        connection_frame.pack(fill="x", pady=(14, 12))
        connection_frame.columnconfigure(0, weight=1)
        connection_frame.columnconfigure(1, weight=0, minsize=280)
        connection_frame.rowconfigure(0, weight=1)

        status_colors = DRIVE_STATUS_COLORS[initial_status_state]
        status_bar = tk.Label(
            connection_frame,
            textvariable=status_var,
            anchor="w",
            justify="left",
            wraplength=480,
            height=2,
            padx=10,
            pady=7,
            background=status_colors["background"],
            foreground=status_colors["foreground"],
        )
        status_bar.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._configuration_status_bar = status_bar

        drive_buttons_frame = ttk.Frame(connection_frame)
        drive_buttons_frame.grid(row=0, column=1, sticky="nsew")
        drive_buttons_frame.columnconfigure(0, weight=1)

        connect_button = ttk.Button(
            drive_buttons_frame,
            text=_("✅  Google Drive connected") if self.drive_service is not None else _("🔗  Connect to Google Drive"),
            style="Bold.TButton",
            width=30,
        )
        connect_button.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        disconnect_button = ttk.Button(
            drive_buttons_frame,
            text=_("🔌  Disconnect Google Drive"),
            command=lambda: self._disconnect_google_drive(
                dialog, status_var, connect_button, disconnect_button
            ),
            state="normal" if connection_available else "disabled",
            width=30,
        )
        disconnect_button.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        ttk.Label(frame, text=_("Drive folder name:")).pack(anchor="w", pady=(8, 0))
        ttk.Entry(frame, textvariable=self.drive_folder_name).pack(fill="x", pady=2)

        ttk.Label(frame, text=_("OpenLP data directory:")).pack(anchor="w", pady=(8, 0))
        source_row = ttk.Frame(frame)
        source_row.pack(fill="x", pady=2)
        ttk.Entry(source_row, textvariable=self.source_path).pack(side="left", fill="x", expand=True)
        ttk.Button(
            source_row,
            text=_("Browse…"),
            command=lambda: self._choose_source(dialog),
        ).pack(side="right", padx=(8, 0))

        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=(12, 8))

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=(0, 4))
        button_frame.columnconfigure(1, weight=1)
        about_label = tk.Label(
            button_frame,
            text=f"OpenLP Vault {__version__}",
            foreground="#0563c1",
            background=frame_background,
            cursor="hand2",
            font=("TkDefaultFont", 9, "underline"),
        )
        about_label.grid(row=0, column=0, sticky="w")
        about_label.bind(
            "<Button-1>", lambda _event: self._open_about_dialog(dialog)
        )
        save_button = ttk.Button(
            button_frame,
            text=_("OK"),
            command=lambda: self._save_configuration(dialog),
            style="Bold.TButton",
            width=14,
        )
        save_button.grid(row=0, column=2, padx=(0, 8))
        close_button = ttk.Button(
            button_frame,
            text=_("Cancel"),
            command=lambda: self._close_configuration(dialog),
            width=14,
        )
        close_button.grid(row=0, column=3)

        connect_button.configure(
            command=lambda: self._start_configuration_authentication(
                dialog, status_var, connect_button, disconnect_button, save_button, close_button
            ),
            state="disabled" if self.drive_service is not None else "normal",
        )

        dialog.protocol("WM_DELETE_WINDOW", lambda: self._close_configuration(dialog))

        dialog.update_idletasks()
        required_height = dialog.winfo_reqheight()
        dialog.minsize(800, required_height)
        if dialog.winfo_height() < required_height:
            dialog.geometry(f"800x{required_height}")

        dialog.grab_set()
        dialog.focus_set()

    def _choose_credentials(self, parent=None):
        path = filedialog.askopenfilename(title=_("Select credentials.json"), filetypes=[("JSON", "*.json")], parent=parent or self)
        if path:
            self.credentials_path.set(path)

    def _choose_source(self, parent=None):
        path = filedialog.askdirectory(title=_("Select OpenLP directory"), parent=parent or self)
        if path:
            self.source_path.set(path)

    # snapshot_dir selection removed

    def _load_config(self):
        config = load_config()
        if not config:
            return

        self.credentials_path.set(config.get("credentials_path", self.credentials_path.get()))
        self.source_path.set(config.get("source_path", self.source_path.get()))
        self.drive_folder_name.set(config.get("drive_folder_name", self.drive_folder_name.get()))

    def _save_configuration(self, dialog=None):
        if getattr(self, "_configuration_authenticating", False):
            messagebox.showwarning(
                _("Authentication in progress"),
                _("Wait for authentication to finish before saving."),
                parent=dialog or self,
            )
            return

        config = {
            "credentials_path": self.credentials_path.get(),
            "source_path": self.source_path.get(),
            "drive_folder_name": self.drive_folder_name.get(),
        }
        save_config(config)
        self.startup_state = self._detect_startup_state()
        self._append_log(_("Settings saved."))
        if dialog:
            dialog.destroy()

    def _ensure_authenticated(self):
        if self.drive_service is not None:
            return
        if not has_reusable_token():
            self._open_configuration(first_run=True)
            raise RuntimeError(_("Google Drive is not connected. Complete the Google Drive setup."))

        self._authenticate()
        if self.drive_service is None:
            raise RuntimeError(_("Could not connect to Google Drive."))


def main():
    app = OpenLPVaultGUI()
    app.mainloop()
