import logging
import os
import sys

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))  # src/app
src_dir = os.path.dirname(current_dir)  # src

# adicionar a pasta src ao caminho de procura do Python
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from app.ui.main_window import MainWindow  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402


def main():
    logger.info("Starting Frontend Application...")
    # o motor do PyQt)
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # loop do programa
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
