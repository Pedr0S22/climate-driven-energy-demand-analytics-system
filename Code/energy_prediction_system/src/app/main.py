import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow 

def main():
    # o motor do PyQt)
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    
    #loop do programa 
    sys.exit(app.exec())

if __name__ == "__main__":
    main()