"""
Einstellungsdialog für die Ollama-Anbindung.

Erlaubt das Setzen von Host/Port sowie das Laden der auf dem Host
verfügbaren Modelle per Hot-Reload (/api/tags), analog zum
Pandora-Ökosystem der bestehenden Projekte.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QDialogButtonBox,
)

from ollama_client import OllamaModelsThread


class OllamaSettingsDialog(QDialog):
    def __init__(self, host: str, model: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ollama-Einstellungen")
        self.setMinimumWidth(420)
        self._models_thread = None

        self.host_input = QLineEdit(host)
        self.host_input.setPlaceholderText("http://localhost:11434")

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItem(model)
        self.model_combo.setCurrentText(model)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)

        reload_btn = QPushButton("Modelle aktualisieren")
        reload_btn.clicked.connect(self.reload_models)

        form = QFormLayout()
        form.addRow("Ollama Host:", self.host_input)

        model_row = QHBoxLayout()
        model_row.addWidget(self.model_combo, stretch=1)
        model_row.addWidget(reload_btn)
        form.addRow("Modell:", model_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.status_label)
        layout.addWidget(buttons)

    def reload_models(self):
        host = self.host_input.text().strip() or "http://localhost:11434"
        self.status_label.setText("Frage Modelle ab ...")
        self._models_thread = OllamaModelsThread(host)
        self._models_thread.models_ready.connect(self._on_models_ready)
        self._models_thread.error.connect(self._on_models_error)
        self._models_thread.start()

    def _on_models_ready(self, names):
        current = self.model_combo.currentText()
        self.model_combo.clear()
        self.model_combo.addItems(names)
        if current:
            self.model_combo.setCurrentText(current)
        self.status_label.setText(f"{len(names)} Modell(e) gefunden.")

    def _on_models_error(self, message):
        self.status_label.setText(message)

    def values(self):
        return self.host_input.text().strip(), self.model_combo.currentText().strip()
