"""
Global Settings Dialog for OPC UA Certificate Manager.

This module provides a dialog for configuring global application settings:
- Theme (Dark/Light mode)
- Language (English/Spanish)
- Default certificate export format
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from src.utils.config import load_config, save_config
from src.utils.i18n import _, Translator, get_translator, set_language


class SettingsDialog:
    """
    Global settings dialog window.
    
    Allows users to configure:
    - Application theme (Dark/Light mode)
    - Language (English/Spanish, extensible)
    - Default certificate export format
    """
    
    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        on_settings_changed: Optional[Callable] = None,
    ) -> None:
        """
        Create and show the settings dialog.
        
        Args:
            parent: Parent window.
            on_settings_changed: Callback when settings are saved.
        """
        self.parent = parent
        self.on_settings_changed = on_settings_changed
        self.config = load_config()
        self._ = get_translator()
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(_("settings.dialog.title", "Global Settings"))
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 400) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Build the settings dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text=_("settings.dialog.title", "Global Settings"),
            font=("Segoe UI", 14, "bold"),
        )
        title_label.pack(pady=(0, 20))
        
        # Appearance section
        appearance_frame = ttk.LabelFrame(
            main_frame,
            text=_("settings.appearance", "Appearance"),
            padding=10,
        )
        appearance_frame.pack(fill="x", pady=(0, 10))
        
        # Theme selection
        ttk.Label(
            appearance_frame,
            text=_("settings.theme", "Theme:"),
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.theme_var = tk.StringVar(
            value=self.config.get("theme", "light")
        )
        theme_combo = ttk.Combobox(
            appearance_frame,
            textvariable=self.theme_var,
            values=["light", "dark"],
            state="readonly",
            width=25,
        )
        theme_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Language section
        language_frame = ttk.LabelFrame(
            main_frame,
            text=_("settings.language", "Language"),
            padding=10,
        )
        language_frame.pack(fill="x", pady=(0, 10))
        
        # Language selection
        ttk.Label(
            language_frame,
            text=_("settings.language.select", "Language:"),
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.language_var = tk.StringVar(
            value=self.config.get("language", "en")
        )
        
        # Get available languages
        translator = get_translator()
        languages = translator.get_available_languages()
        lang_values = [f"{lang['code']} - {lang['name']}" for lang in languages]
        
        language_combo = ttk.Combobox(
            language_frame,
            textvariable=self.language_var,
            values=lang_values,
            state="readonly",
            width=25,
        )
        language_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Set current language as selected
        current_lang = self.config.get("language", "en")
        current_display = f"{current_lang} - {translator.get(f'lang.{current_lang}', current_lang.upper())}"
        self.language_var.set(current_display)
        
        # Export section
        export_frame = ttk.LabelFrame(
            main_frame,
            text=_("settings.export", "Certificate Export"),
            padding=10,
        )
        export_frame.pack(fill="x", pady=(0, 10))
        
        # Export format selection
        ttk.Label(
            export_frame,
            text=_("settings.export.format", "Default Format:"),
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.export_format_var = tk.StringVar(
            value=self.config.get("default_export_format", "PEM")
        )
        export_formats = [
            "PEM (.pem)",
            "DER (.cer)",
            "PEM (.cer)",
            "DER (.crt)",
            "PEM (.crt)",
        ]
        export_combo = ttk.Combobox(
            export_frame,
            textvariable=self.export_format_var,
            values=export_formats,
            state="readonly",
            width=25,
        )
        export_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        save_btn = ttk.Button(
            button_frame,
            text=_("settings.save", "Save"),
            command=self._on_save,
        )
        save_btn.pack(side="right", padx=5)
        
        cancel_btn = ttk.Button(
            button_frame,
            text=_("settings.cancel", "Cancel"),
            command=self.dialog.destroy,
        )
        cancel_btn.pack(side="right", padx=5)
    
    def _on_save(self) -> None:
        """Handle save button click."""
        # Validate and save settings
        try:
            # Update config
            self.config["theme"] = self.theme_var.get()
            
            # Extract language code from display string
            lang_display = self.language_var.get()
            lang_code = lang_display.split(" - ")[0] if " - " in lang_display else "en"
            self.config["language"] = lang_code
            
            # Extract format from display string
            format_display = self.export_format_var.get()
            format_code = format_display.split(" ")[0]  # "PEM" or "DER"
            self.config["default_export_format"] = format_code
            
            # Save to file
            save_config(self.config)
            
            # Apply language change
            set_language(lang_code)
            
            # Notify callback
            if self.on_settings_changed:
                self.on_settings_changed({
                    "theme": self.theme_var.get(),
                    "language": lang_code,
                    "export_format": format_code,
                })
            
            # Show success message
            messagebox.showinfo(
                _("settings.saved", "Settings Saved"),
                _("settings.saved.message", "Settings have been saved successfully.\n\nLanguage change will take effect on next restart."),
                parent=self.dialog,
            )
            
            # Close dialog
            self.dialog.destroy()
        
        except Exception as e:
            messagebox.showerror(
                _("settings.error", "Error"),
                f"{_('settings.error.save', 'Error saving settings:')}\n\n{str(e)}",
                parent=self.dialog,
            )


def show_settings_dialog(
    parent: tk.Tk | tk.Toplevel,
    on_settings_changed: Optional[Callable] = None,
) -> None:
    """
    Show the global settings dialog.
    
    Args:
        parent: Parent window.
        on_settings_changed: Callback when settings are saved.
    """
    dialog = SettingsDialog(parent, on_settings_changed)