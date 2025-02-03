from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QDoubleSpinBox,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QListWidget,
    QLabel,
    QTextEdit,
)
from typing import Dict, List, Optional
import asyncio
from crawler import SpecificationCrawler, SpecData


class SpecificationConflictDialog(QDialog):
    def __init__(
        self, field_name: str, values: List[float], urls: List[str], parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle(f"Choose {field_name} value")
        layout = QVBoxLayout()

        label = QLabel(f"Multiple values found for {field_name}. Please choose one:")
        layout.addWidget(label)

        self.list_widget = QListWidget()
        for value, url in zip(values, urls):
            self.list_widget.addItem(f"{value} (from {url})")
        layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_selected_value(self) -> Optional[float]:
        if not self.list_widget.currentItem():
            return None
        text = self.list_widget.currentItem().text()
        return float(text.split(" ")[0])


class SpeakerPropertiesDialog(QDialog):
    def __init__(
        self,
        speaker_name: str,
        sensitivity: Optional[float] = None,
        impedance: Optional[float] = None,
        weight: Optional[float] = None,
        height: Optional[float] = None,
        width: Optional[float] = None,
        depth: Optional[float] = None,
        parent=None,
        test_mode=False,
    ):
        super().__init__(parent)
        self.speaker_name = speaker_name
        self.test_mode = test_mode

        self.setWindowTitle(f"Speaker Properties - {speaker_name}")
        self.setModal(True)

        # Create layout
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Create spinboxes for each property
        self.sensitivity = QDoubleSpinBox()
        self.sensitivity.setRange(50, 200)
        self.sensitivity.setSuffix(" dB")
        if sensitivity is not None:
            self.sensitivity.setValue(sensitivity)

        self.impedance = QDoubleSpinBox()
        self.impedance.setRange(1, 100)
        self.impedance.setSuffix(" Ω")
        if impedance is not None:
            self.impedance.setValue(impedance)

        self.weight = QDoubleSpinBox()
        self.weight.setRange(0, 1000)
        self.weight.setSuffix(" kg")
        if weight is not None:
            self.weight.setValue(weight)

        self.height = QDoubleSpinBox()
        self.height.setRange(0, 10000)
        self.height.setSuffix(" mm")
        if height is not None:
            self.height.setValue(height)

        self.width = QDoubleSpinBox()
        self.width.setRange(0, 10000)
        self.width.setSuffix(" mm")
        if width is not None:
            self.width.setValue(width)

        self.depth = QDoubleSpinBox()
        self.depth.setRange(0, 10000)
        self.depth.setSuffix(" mm")
        if depth is not None:
            self.depth.setValue(depth)

        # Add fields to form layout
        form_layout.addRow("Sensitivity:", self.sensitivity)
        form_layout.addRow("Impedance:", self.impedance)
        form_layout.addRow("Weight:", self.weight)
        form_layout.addRow("Height:", self.height)
        form_layout.addRow("Width:", self.width)
        form_layout.addRow("Depth:", self.depth)

        main_layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()

        get_spec_btn = QPushButton("Get Specification")
        get_spec_btn.clicked.connect(self.handle_search_specifications)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(get_spec_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        main_layout.addLayout(button_layout)

        # Create log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(100)
        self.log_text.setPlaceholderText("Operation logs will appear here...")
        main_layout.addWidget(self.log_text)

        self.setLayout(main_layout)

    async def search_specifications(self):
        """Search for speaker specifications and parse results"""
        if not self.speaker_name:
            if not self.test_mode:
                QMessageBox.warning(self, "Warning", "No speaker name provided")
            return

        try:
            crawler = SpecificationCrawler()

            # Search for specifications
            search_query = f"{self.speaker_name} speaker specifications technical data"
            self.log_message(f"Searching for: {search_query}")
            results = await crawler.search_web(search_query)

            if not results:
                self.log_message("No search results found")
                if not self.test_mode:
                    QMessageBox.warning(self, "Warning", "No results found")
                return

            # Get content from top 3 results and extract specifications
            specs = []
            self.log_message(f"\nAnalyzing top {min(3, len(results))} search results:")
            for i, result in enumerate(results[:3], 1):
                self.log_message(f"\n{i}. Fetching content from: {result}")
                content = await crawler.fetch_url_content(result)
                if content:
                    self.log_message("Content retrieved successfully")
                    spec_data = crawler.extract_specifications(content, result)
                    self.log_message("Extracted specifications:")
                    for field in [
                        "sensitivity",
                        "impedance",
                        "weight",
                        "height",
                        "width",
                        "depth",
                    ]:
                        value = getattr(spec_data, field)
                        if value is not None:
                            self.log_message(f"  - {field}: {value}")
                    specs.append(spec_data)
                else:
                    self.log_message("Failed to retrieve content")

            # Merge specifications and handle conflicts
            merged_specs = self.merge_specifications(specs)
            self.log_message("\nProcessing merged specifications:")

            # Update values, asking user to resolve conflicts
            for field, values in merged_specs.items():
                if len(values) == 1:
                    # Single value found, use it directly
                    value, url = values[0]
                    getattr(self, field).setValue(value)
                    self.log_message(f"Setting {field} = {value} (from {url})")
                elif len(values) > 1:
                    # Multiple values found, ask user to choose
                    self.log_message(f"\nMultiple values found for {field}:")
                    for val, url in values:
                        self.log_message(f"  - {val} (from {url})")

                    dialog = SpecificationConflictDialog(
                        field, [v[0] for v in values], [v[1] for v in values], self
                    )
                    if dialog.exec() == QDialog.Accepted:
                        chosen_value = dialog.get_selected_value()
                        if chosen_value is not None:
                            getattr(self, field).setValue(chosen_value)
                            self.log_message(f"User selected {field} = {chosen_value}")

        except Exception as e:
            error_msg = f"Failed to fetch specifications: {str(e)}"
            self.log_message(f"\nError: {error_msg}")
            if not self.test_mode:
                QMessageBox.warning(self, "Error", error_msg)

    def merge_specifications(
        self, specs: List[SpecData]
    ) -> Dict[str, List[tuple[float, str]]]:
        """Merge specifications from multiple sources, grouping conflicting values"""
        merged = {}
        fields = ["sensitivity", "impedance", "weight", "height", "width", "depth"]

        for field in fields:
            values = [
                (getattr(spec, field), spec.source_url)
                for spec in specs
                if getattr(spec, field) is not None
            ]
            if values:
                merged[field] = values

        return merged

    def log_message(self, message: str):
        """Add a message to the log text area"""
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def handle_search_specifications(self):
        """Synchronous wrapper for search_specifications"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If no event loop exists, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self.search_specifications())
        except Exception as e:
            if not self.test_mode:
                QMessageBox.warning(
                    self, "Error", f"Failed to fetch specifications: {str(e)}"
                )

    def get_properties(self):
        """Get the speaker properties as a dictionary"""
        return {
            "sensitivity": self.sensitivity.value() or None,
            "impedance": self.impedance.value() or None,
            "weight": self.weight.value() or None,
            "height": self.height.value() or None,
            "width": self.width.value() or None,
            "depth": self.depth.value() or None,
        }
