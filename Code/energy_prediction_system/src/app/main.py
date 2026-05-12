import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__)) # src/app
src_dir = os.path.dirname(current_dir) # src

# adicionar a pasta src ao caminho de procura do Python
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from PyQt6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def main():
    # o motor do PyQt)
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # loop do programa
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
