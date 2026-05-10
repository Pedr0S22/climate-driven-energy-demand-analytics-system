from PyQt6 import QtCore, QtGui, QtWidgets

class Sidebar(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        self.setStyleSheet("""
            QFrame {
                background-color: #EAEAEF;
                border-right: 3px solid black;
                border-bottom-left-radius: 5px;
            }
        """)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 20, 0, 20)
        self.layout.setSpacing(0)
        
        # Dictionary to store sections and their children
        self.sections = {}
        # Track if a section is expanded
        self.section_expanded = {}

    def add_menu_header(self, text):
        """Adds a clickable section header that toggles children visibility."""
        btn = QtWidgets.QPushButton(text)
        btn.setFixedHeight(50)
        font = QtGui.QFont("Tw Cen MT Condensed", 22, QtGui.QFont.Weight.Bold)
        btn.setFont(font)
        btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #000180;
                text-align: left;
                padding-left: 20px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: rgba(0, 1, 128, 0.05);
            }
        """)
        
        self.layout.addWidget(btn)
        self.sections[text] = []
        self.section_expanded[text] = False
        
        btn.clicked.connect(lambda: self.toggle_section(text))
        return btn

    def add_menu_item(self, text, active=False, indent=False, header_parent=None):
        """Adds a navigation item. If header_parent is provided, it belongs to that section."""
        container = QtWidgets.QWidget()
        container.setFixedHeight(50)
        item_layout = QtWidgets.QHBoxLayout(container)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(10)

        # Active Indicator Bar
        indicator = QtWidgets.QFrame()
        indicator.setFixedWidth(8)
        if active:
            indicator.setStyleSheet("background-color: #000180; border: none;")
        else:
            indicator.setStyleSheet("background-color: transparent; border: none;")
        item_layout.addWidget(indicator)

        # Button
        btn = QtWidgets.QPushButton(text)
        font_size = 20 if indent else 22
        font = QtGui.QFont("Tw Cen MT Condensed", font_size)
        if active:
            font.setBold(True)
        btn.setFont(font)
        
        color = "#000180" if active else "#262626"
        left_padding = 40 if indent else 5
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {color};
                text-align: left;
                padding-left: {left_padding}px;
            }}
            QPushButton:hover {{
                color: #000180;
                text-decoration: underline;
            }}
        """)
        btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        item_layout.addWidget(btn)
        
        self.layout.addWidget(container)
        
        # Section Logic
        if header_parent and header_parent in self.sections:
            self.sections[header_parent].append(container)
            
            # If this item is active, expand the parent section
            if active:
                self.section_expanded[header_parent] = True
            
            # Set visibility based on section state
            container.setVisible(self.section_expanded[header_parent])
        
        return btn

    def toggle_section(self, header_text):
        """Toggles visibility of all items in a section."""
        if header_text in self.sections:
            # Toggle state
            is_visible = not self.section_expanded[header_text]
            self.section_expanded[header_text] = is_visible
            
            # Apply visibility to all children
            for item in self.sections[header_text]:
                item.setVisible(is_visible)
