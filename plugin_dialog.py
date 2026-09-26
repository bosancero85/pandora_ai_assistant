"""
Plugin-Verwaltungsdialog.

Zeigt alle im Plugin-Ordner gefundenen Plugins mit Checkbox
(aktiv/inaktiv) sowie einem Hot-Reload-Button, der die Plugin-Dateien
neu einliest, ohne die Anwendung neu zu starten.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QDialogButtonBox,
)


class PluginManagerDialog(QDialog):
    def __init__(self, plugin_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plugin-Verwaltung")
        self.setMinimumSize(480, 360)
        self.plugin_manager = plugin_manager

        self.info_label = QLabel(
            "Plugins aus dem Ordner 'plugins/'. Häkchen setzen/entfernen, "
            "um eine Aktion zu (de)aktivieren."
        )
        self.info_label.setWordWrap(True)

        self.list_widget = QListWidget()
        self.list_widget.itemChanged.connect(self._on_item_changed)

        reload_btn = QPushButton("🔄  Plugins neu laden (Hot-Reload)")
        reload_btn.clicked.connect(self.reload_plugins)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        close_btn = buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_btn:
            close_btn.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self.info_label)
        layout.addWidget(self.list_widget, stretch=1)
        layout.addWidget(reload_btn)
        layout.addWidget(self.status_label)
        layout.addWidget(buttons)

        self.refresh_list()

    # ------------------------------------------------------------------
    def refresh_list(self):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for action, plugin in sorted(self.plugin_manager.plugins.items()):
            item = QListWidgetItem(f"{action} – {plugin.description}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked
                if self.plugin_manager.is_enabled(action)
                else Qt.CheckState.Unchecked
            )
            item.setData(Qt.ItemDataRole.UserRole, action)
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)

    def _on_item_changed(self, item: QListWidgetItem):
        action = item.data(Qt.ItemDataRole.UserRole)
        enabled = item.checkState() == Qt.CheckState.Checked
        self.plugin_manager.set_enabled(action, enabled)

    def reload_plugins(self):
        errors = self.plugin_manager.discover()
        self.refresh_list()
        if errors:
            self.status_label.setText("Fehler beim Laden:\n" + "\n".join(errors))
        else:
            count = len(self.plugin_manager.plugins)
            self.status_label.setText(f"{count} Plugin(s) erfolgreich geladen.")
