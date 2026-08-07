import datetime
import logging
import os
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .auth import authenticate
from .backup import cleanup_backup_file, create_backup, upload_backup
from .config import load_config, save_config
from . import __version__
from .discovery import find_openlp_installation
from .restore import apply_backup, delete_backup, download_backup, list_backups
from .utils import format_drive_timestamp

LOG = logging.getLogger("openlp_vault.gui")


class OpenLPVaultGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OpenLP Vault")
        self.geometry("620x500")
        self.resizable(False, False)

        self.drive_service = None
        self.backups = []
        self.credentials_path = tk.StringVar(value="credentials.json")
        self.source_path = tk.StringVar(value=find_openlp_installation() or "")
        self.drive_folder_name = tk.StringVar(value="OpenLP Vault")

        self._load_config()
        self._build_ui()
        self._refresh_backups(silent=True)

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=18)
        main_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("TButton", font=(None, 11), padding=(14, 9))
        style.configure("Bold.TButton", font=(None, 11, "bold"), padding=(14, 9))

        ttk.Label(main_frame, text="OpenLP Vault", font=(None, 20, "bold")).pack(pady=(0, 12))

        ttk.Button(main_frame, text="⬆️  Crear y subir un respaldo", command=self._open_backup_dialog).pack(fill="x", pady=8)
        ttk.Button(main_frame, text="⬇️  Descargar y restaurar un respaldo", command=self._open_restore_dialog).pack(fill="x", pady=8)
        ttk.Button(main_frame, text="⚙️  Configuración", command=self._open_configuration).pack(fill="x", pady=12)

        self.log_text = tk.Text(main_frame, height=8, wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=False, pady=(0, 8))

    def _append_log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _authenticate(self):
        self._append_log("Autenticando en Google Drive...")
        try:
            drive_service, _ = authenticate(client_secrets_file=self.credentials_path.get())
            self.drive_service = drive_service
            self._refresh_backups()
        except Exception as exc:
            LOG.exception("Error de autenticación")
            messagebox.showerror("Error", f"No se pudo autenticar: {exc}", parent=self)
            self._append_log(f"Error: {exc}")

    def _open_backup_dialog(self):
        default_name = self._default_backup_filename()
        backup_name_var = tk.StringVar(value=default_name)

        dialog = tk.Toplevel(self)
        dialog.title("Crear y subir respaldo")
        dialog.geometry("760x250")
        dialog.resizable(False, False)

        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Nombre del archivo ZIP:").pack(anchor="w", pady=(0, 8))
        ttk.Entry(frame, textvariable=backup_name_var, width=60).pack(anchor="w", pady=(0, 8))
        ttk.Label(frame, text="El archivo se subirá a Google Drive.").pack(anchor="w", pady=(0, 12))

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=10)
        ttk.Button(button_frame, text="❌  Cancelar", command=dialog.destroy, width=16).pack(side="right")
        ttk.Button(button_frame, text="💾  Crear (no subir)", command=lambda: self._create_local_backup(backup_name_var.get(), dialog), width=20).pack(side="right", padx=8)
        ttk.Button(button_frame, text="⬆️  Crear y subir", command=lambda: self._backup(backup_name_var.get(), dialog), style="Bold.TButton", width=20).pack(side="right", padx=12)

    def _default_backup_filename(self):
        hostname = os.uname().nodename.replace(" ", "_")
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        return f"openlp_backup_{hostname}_{timestamp}"

    def _backup(self, zip_name=None, dialog=None):
        if dialog:
            dialog.destroy()

        self._append_log("Iniciando respaldo...")
        source = self.source_path.get() or find_openlp_installation()
        if not source:
            messagebox.showwarning("Advertencia", "No se encontró la instalación de OpenLP. Configure la ruta en la ventana de configuración.", parent=self)
            return

        if not self.source_path.get():
            self.source_path.set(source)
            self._append_log(f"Ruta de OpenLP detectada automáticamente: {source}")

        # Crear diálogo modal de progreso
        progress = tk.Toplevel(self)
        progress.title("Creando y subiendo respaldo")
        progress.resizable(False, False)
        progress.transient(self)
        progress.grab_set()

        p_frame = ttk.Frame(progress, padding=12)
        p_frame.pack(fill="both", expand=True)
        ttk.Label(p_frame, text="Por favor espere — creando y subiendo el respaldo...").pack(anchor="center", pady=(4, 8))
        pb = ttk.Progressbar(p_frame, mode="indeterminate", length=360)
        pb.pack(pady=(0, 8))
        pb.start(12)

        def _do_backup():
            try:
                self._append_log(f"Creando el respaldo...")
                backup_path = create_backup(source, zip_name=zip_name)
                self._append_log(f"Archivo de respaldo creado: {backup_path}")
                # Asegurar autenticación (puede abrir diálogo)
                try:
                    self._ensure_authenticated()
                except Exception:
                    # _ensure_authenticated may raise after showing auth UI; re-raise to be handled below
                    raise
                folder_name = self.drive_folder_name.get() or "OpenLP Vault"
                self._append_log(f"Subiendo el respaldo...")
                metadata = upload_backup(backup_path, self.drive_service, folder_name=folder_name)
                self._append_log(f"Respaldo subido: {metadata.get('name')} (id={metadata.get('id')})")

                def _on_success():
                    try:
                        pb.stop()
                    finally:
                        progress.grab_release()
                        progress.destroy()
                    cleanup_backup_file(backup_path)
                    self._refresh_backups()
                    messagebox.showinfo("Éxito", "Respaldo creado y subido correctamente.", parent=self)

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
                    messagebox.showerror("Error", f"No se pudo crear o subir el respaldo: {exc}", parent=self)
                    self._append_log(f"Error: {exc}")

                self.after(0, _on_error)

        thread = threading.Thread(target=_do_backup, daemon=True)
        thread.start()

    def _create_local_backup(self, zip_name=None, dialog=None):
        if dialog:
            dialog.destroy()

        self._append_log("Iniciando creación local de respaldo...")
        source = self.source_path.get() or find_openlp_installation()
        if not source:
            messagebox.showwarning("Advertencia", "No se encontró la instalación de OpenLP. Configure la ruta en la ventana de configuración.", parent=self)
            return

        if not self.source_path.get():
            self.source_path.set(source)
            self._append_log(f"Ruta de OpenLP detectada automáticamente: {source}")

        # Crear diálogo modal de progreso para creación local
        progress = tk.Toplevel(self)
        progress.title("Creando respaldo local")
        progress.resizable(False, False)
        progress.transient(self)
        progress.grab_set()

        p_frame = ttk.Frame(progress, padding=12)
        p_frame.pack(fill="both", expand=True)
        ttk.Label(p_frame, text="Por favor espere — creando respaldo local...").pack(anchor="center", pady=(4, 8))
        pb = ttk.Progressbar(p_frame, mode="indeterminate", length=360)
        pb.pack(pady=(0, 8))
        pb.start(12)

        def _do_local():
            try:
                self._append_log("Creando respaldo local...")
                backup_path = create_backup(source, zip_name=zip_name)
                self._append_log(f"Archivo de respaldo creado: {backup_path}")

                def _on_success():
                    try:
                        pb.stop()
                    finally:
                        progress.grab_release()
                        progress.destroy()
                    messagebox.showinfo("Éxito", f"Respaldo local creado: {backup_path}", parent=self)

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
                    messagebox.showerror("Error", f"No se pudo crear el respaldo local: {exc}", parent=self)
                    self._append_log(f"Error: {exc}")

                self.after(0, _on_error)

        thread = threading.Thread(target=_do_local, daemon=True)
        thread.start()

    def _open_restore_dialog(self):
        if not self.backups:
            self._refresh_backups()
        if not self.backups:
            messagebox.showwarning("Advertencia", "No hay respaldos disponibles.", parent=self)
            return

        sorted_backups = sorted(self.backups, key=lambda item: item.get("createdTime", ""), reverse=True)
        dialog = tk.Toplevel(self)
        dialog.title("Descargar y restaurar un respaldo")
        dialog.geometry("980x560")
        dialog.resizable(False, False)

        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Seleccione el respaldo a restaurar:", font=(None, 12, "bold")).pack(anchor="w", pady=(0, 8))

        listbox = tk.Listbox(frame, height=12, width=92)
        listbox.pack(fill="both", expand=True, padx=2)
        for item in sorted_backups:
            created = format_drive_timestamp(item.get("createdTime", ""))
            listbox.insert("end", f"{item.get('name')} — {created}")
        listbox.selection_set(0)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=10, padx=2)
        ttk.Button(button_frame, text="❌  Cancelar", command=dialog.destroy, width=16).pack(side="right")
        ttk.Button(button_frame, text="🔄  Actualizar", command=lambda: self._refresh_restore_list(listbox), width=16).pack(side="right", padx=10)
        ttk.Button(button_frame, text="🗑️  Eliminar", command=lambda: self._delete_selected(listbox, dialog), width=16).pack(side="right", padx=10)
        ttk.Button(button_frame, text="⬇️  Descargar y restaurar", command=lambda: self._restore_selected(listbox, dialog), style="Bold.TButton", width=28).pack(side="right", padx=10)

    def _restore_selected(self, listbox, dialog):
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un respaldo para restaurar.", parent=dialog)
            return
        sorted_backups = self._get_sorted_backups()
        backup = sorted_backups[selection[0]]
        destination = self.source_path.get() or find_openlp_installation()
        if not destination:
            messagebox.showwarning("Advertencia", "No se encontró el destino de OpenLP. Configure la ruta en Configuración.", parent=self)
            return
        # Pedir confirmación antes de restaurar
        parent = dialog
        parent.attributes("-topmost", True)
        confirmed = messagebox.askyesno(
            "Confirmar restauración",
            f"¿Descargar y restaurar el respaldo {backup.get('name')}? Se sobrescribirá la instalación de OpenLP en {destination}.",
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
            messagebox.showwarning("Advertencia", "Seleccione un respaldo para eliminar.", parent=parent)
            return
        sorted_backups = self._get_sorted_backups()
        backup = sorted_backups[selection[0]]
        parent.attributes("-topmost", True)
        confirmed = messagebox.askyesno("Confirmar eliminación", f"¿Eliminar el respaldo {backup.get('name')}?", parent=parent)
        parent.attributes("-topmost", False)
        if not confirmed:
            return

        try:
            delete_backup(backup.get('id'), self.drive_service)
            self._append_log(f"Respaldo eliminado: {backup.get('name')}")
            self._refresh_backups()
            listbox.delete(selection[0])
            messagebox.showinfo("Éxito", "Respaldo eliminado correctamente.", parent=parent)
        except Exception as exc:
            LOG.exception("Error al eliminar respaldo")
            messagebox.showerror("Error", f"No se pudo eliminar el respaldo: {exc}", parent=parent)
            self._append_log(f"Error: {exc}")

    def _get_sorted_backups(self):
        return sorted(self.backups, key=lambda item: item.get("createdTime", ""), reverse=True)

    def _restore_backup(self, backup):
        self._append_log(f"Restaurando respaldo {backup.get('name')}...")
        destination = self.source_path.get() or find_openlp_installation()
        if not destination:
            messagebox.showwarning("Advertencia", "No se encontró el destino de OpenLP.", parent=self)
            return

        # Crear diálogo modal de progreso
        progress = tk.Toplevel(self)
        progress.title("Descargando y restaurando respaldo")
        progress.resizable(False, False)
        progress.transient(self)
        progress.grab_set()

        p_frame = ttk.Frame(progress, padding=12)
        p_frame.pack(fill="both", expand=True)
        ttk.Label(p_frame, text="Por favor espere — descargando y aplicando el respaldo...").pack(anchor="center", pady=(4, 8))
        pb = ttk.Progressbar(p_frame, mode="indeterminate", length=360)
        pb.pack(pady=(0, 8))
        pb.start(12)

        def _do_restore():
            try:
                archive_path = Path(tempfile.mkdtemp(prefix="openlp_restore_")) / f"{backup.get('id')}.zip"
                self._append_log(f"Descargando respaldo {backup.get('id')}...")
                download_backup(backup.get('id'), self.drive_service, archive_path)
                self._append_log(f"Aplicando respaldo a {destination}...")
                apply_backup(archive_path, destination)
                self._append_log("Restauración completada.")

                def _on_success():
                    try:
                        pb.stop()
                    finally:
                        progress.grab_release()
                        progress.destroy()
                    cleanup_backup_file(archive_path)
                    messagebox.showinfo("Éxito", "Restauración finalizada correctamente.", parent=self)

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
                    messagebox.showerror("Error", f"No se pudo restaurar el respaldo: {exc}", parent=self)
                    self._append_log(f"Error: {exc}")

                self.after(0, _on_error)

        thread = threading.Thread(target=_do_restore, daemon=True)
        thread.start()

    def _refresh_backups(self, silent=False):
        if not silent:
            self._append_log("Consultando respaldos en Drive...")
        try:
            self._ensure_authenticated()
            self.backups = list_backups(self.drive_service)
            if not silent:
                self._append_log(f"{len(self.backups)} respaldos encontrados.")
        except Exception:
            if not silent:
                self._append_log("No autenticado aún o no se pudieron listar respaldos.")

    def _open_configuration(self):
        dialog = tk.Toplevel(self)
        dialog.title("Configuración")
        dialog.geometry("720x500")
        dialog.resizable(False, False)

        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Configuración", font=(None, 14, "bold")).pack(anchor="w", pady=(0, 10))

        ttk.Label(frame, text="Ruta del archivo de credenciales (credentials.json):").pack(anchor="w", pady=(6, 0))
        ttk.Entry(frame, textvariable=self.credentials_path, width=80).pack(anchor="w", pady=2)
        ttk.Button(frame, text="Seleccionar...", command=lambda: self._choose_credentials(dialog), width=18).pack(anchor="w", pady=2)

        ttk.Label(frame, text="Directorio de datos de OpenLP:").pack(anchor="w", pady=(12, 0))
        ttk.Entry(frame, textvariable=self.source_path, width=80).pack(anchor="w", pady=2)
        ttk.Button(frame, text="Seleccionar...", command=lambda: self._choose_source(dialog), width=18).pack(anchor="w", pady=2)

        ttk.Label(frame, text="Nombre de carpeta en Drive:").pack(anchor="w", pady=(12, 0))
        ttk.Entry(frame, textvariable=self.drive_folder_name, width=80).pack(anchor="w", pady=2)

        # snapshot_dir option removed

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=16)
        ttk.Label(button_frame, text=f"OpenLP Vault versión {__version__}", font=(None, 10, "bold")).pack(side="left")
        ttk.Button(button_frame, text="❌  Cancelar", command=dialog.destroy, width=16).pack(side="right")
        ttk.Button(button_frame, text="✅  Aceptar", command=lambda: self._save_configuration(dialog), width=18, style="Bold.TButton").pack(side="right", padx=10)

    def _choose_credentials(self, parent=None):
        path = filedialog.askopenfilename(title="Seleccionar credentials.json", filetypes=[("JSON", "*.json")], parent=parent or self)
        if path:
            self.credentials_path.set(path)

    def _choose_source(self, parent=None):
        path = filedialog.askdirectory(title="Seleccionar directorio OpenLP", parent=parent or self)
        if path:
            self.source_path.set(path)

    # snapshot_dir selection removed

    def _refresh_restore_list(self, listbox):
        self._refresh_backups()
        listbox.delete(0, "end")
        sorted_backups = sorted(self.backups, key=lambda item: item.get("createdTime", ""), reverse=True)
        for item in sorted_backups:
            created = format_drive_timestamp(item.get("createdTime", ""))
            listbox.insert("end", f"{item.get('name')} — {created}")
        if sorted_backups:
            listbox.selection_set(0)
        else:
            messagebox.showinfo("Información", "No se encontraron respaldos.", parent=self)

    def _load_config(self):
        config = load_config()
        if not config:
            return

        self.credentials_path.set(config.get("credentials_path", self.credentials_path.get()))
        self.source_path.set(config.get("source_path", self.source_path.get()))
        self.drive_folder_name.set(config.get("drive_folder_name", self.drive_folder_name.get()))

    def _save_configuration(self, dialog=None):
        config = {
            "credentials_path": self.credentials_path.get(),
            "source_path": self.source_path.get(),
            "drive_folder_name": self.drive_folder_name.get(),
        }
        save_config(config)
        self._append_log("Configuración guardada.")
        if dialog:
            dialog.destroy()
        messagebox.showinfo("Configuración", "Configuración guardada correctamente.", parent=self)

    def _ensure_authenticated(self):
        if self.drive_service is None:
            self._authenticate()
        if self.drive_service is None:
            raise RuntimeError("Servicio de Drive no disponible. Autentique primero.")


def main():
    app = OpenLPVaultGUI()
    app.mainloop()
