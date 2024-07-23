import sys
import os
import time
import threading
import urllib.parse
import traceback
import requests
import pyodbc
import uuid
import webbrowser
from opcua import Client, ua
from datetime import datetime
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QDate, QMutex, QTime
from PyQt5.QtGui import QPixmap, QIcon, QFont, QColor
from PyQt5.QtWidgets import QTimeEdit, QDateEdit, QSplashScreen, QButtonGroup, QStyledItemDelegate, QInputDialog, QVBoxLayout, QGroupBox, QSpacerItem, QSizePolicy, QFormLayout, QDialogButtonBox, QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QDialog, QHeaderView, QLabel, QLineEdit, QComboBox, QRadioButton, QMessageBox

# Define the connection parameters with default values
server = ""
database = ""
username = ""
password = ""
ip = ""
url = ""
user = "Automate"
passw = "Automate123"
encoded_username = urllib.parse.quote(user)
encoded_password = urllib.parse.quote(passw)

DEFAULT_PARAMS = {
    "server": "192.168.0.183",
    "database": "RecipeDB",
    "username": "PC_SERVER_MIX1",
    "password": "PASSWORD01",
    "ip": "192.168.0.4",
    "url": "192.168.0.183/ReportServer"
}

try:
    with open("init.txt", "r") as init_file:
        for line in init_file:
            parts = line.strip().split(" = ", 1)
            if len(parts) == 2:
                key, value = parts
                if key in globals():
                    globals()[key] = value
except FileNotFoundError:
    # If init.txt doesn't exist, create it with default values from DEFAULT_PARAMS
    with open("init.txt", "w") as init_file:
        for key, value in DEFAULT_PARAMS.items():
            init_file.write(f"{key} = {value}\n")

class SplashScreen(QSplashScreen):
    def __init__(self):
        pixmap = QPixmap("sscreen.jpg")  # Load the image file
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

class ConnectionForm(QDialog):
    def __init__(self):
        super().__init__()

        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.setWindowTitle("Config. Connessione")
        layout = QVBoxLayout(self)

        self.params = {
            "server": QLineEdit(server),
            "database": QLineEdit(database),
            "username": QLineEdit(username),
            "password": QLineEdit(password),
            "ip": QLineEdit(ip),
            "url": QLineEdit(url)
        }

        for param, line_edit in self.params.items():
            layout.addWidget(QLabel(f"{param.capitalize()}:"))
            layout.addWidget(line_edit)

        save_button = QPushButton("Salva")
        save_button.clicked.connect(self.save_parameters)
        layout.addWidget(save_button)

        self.load_parameters()

    def load_parameters(self):
        if os.path.exists("init.txt"):
            try:
                with open("init.txt", "r") as file:
                    lines = file.readlines()
                    for line in lines:
                        parts = line.strip().split(" = ", 1)
                        if len(parts) == 2:
                            param, value = parts
                            if param in self.params:
                                if not value:
                                    value = DEFAULT_PARAMS[param]  # Use default if value is empty
                                self.params[param].setText(value)
                                globals()[param] = value  # Update global variable
            except FileNotFoundError:
                pass
        else:
            with open("init.txt", "w") as file:
                for key, value in DEFAULT_PARAMS.items():
                    file.write(f"{key} = {value}\n")
                    self.params[key].setText(value)
                    globals()[key] = value  # Update global variable

    def save_parameters(self):
        with open("init.txt", "w") as file:
            for param, line_edit in self.params.items():
                value = line_edit.text()
                file.write(f"{param} = {value}\n")
                globals()[param] = value  # Update global variable

        QMessageBox.information(self, "Successo", "Parametri salvati con successo.")
        self.close()  # Close the dialog

def get_db_connection():
    conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    conn = pyodbc.connect(conn_str)
    return conn

#--------------------------------------------------------------------BEGIN OF LOGIN GLOBAL CLASSES

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Froneri Recipe Manager - Login")
        self.setWindowFlag(Qt.Window)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        icon_path = "icon.ico"
        self.setWindowIcon(QIcon(icon_path))
        self.setFixedSize(380, 300)  # Increased size of the dialog
        #self.refresh_thread = None

        main_layout = QVBoxLayout(self)

        # Status indicators and labels
        #status_layout = QHBoxLayout()
        #self.database_status_label = QLabel(self)
        #self.plc_status_label = QLabel(self)
        #self.rep_status_label = QLabel(self)
        
        # Status icons
        #self.green_pixmap = QPixmap(15, 15)
        #self.green_pixmap.fill(Qt.green)
        #self.red_pixmap = QPixmap(15, 15)
        #self.red_pixmap.fill(Qt.red)

        # Initial status (red as default)
        #self.database_status_label.setPixmap(self.red_pixmap)
        #self.plc_status_label.setPixmap(self.red_pixmap)
        #self.rep_status_label.setPixmap(self.red_pixmap)

        # Adding image
        image_label = QLabel(self)
        pixmap = QPixmap("Froneri_logo.png").scaled(200, 57)
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(image_label)
        # Status bar (simulated)
        conn_button_layout = QHBoxLayout()
        config_button = QPushButton("Parametri di Connessione")
        config_button.clicked.connect(self.ConnectionForm)
        #refresh_button = QPushButton("Aggiorna Stato Connessione")
        #refresh_button.clicked.connect(self.RefreshConn)
        conn_button_layout.addWidget(config_button)
        #conn_button_layout.addWidget(refresh_button)

        #status_layout = QHBoxLayout()
        #status_layout.addWidget(self.database_status_label)
        #status_layout.addWidget(QLabel("Database Status"), 1)
        #status_layout.addWidget(self.plc_status_label)
        #status_layout.addWidget(QLabel("PLC Status"), 1)
        #status_layout.addWidget(self.rep_status_label)
        #status_layout.addWidget(QLabel("Report Server Status"), 1)

        main_layout.addLayout(conn_button_layout)
        #main_layout.addLayout(status_layout)

        # Login form layout
        form_layout = QFormLayout()
        self.username_edit = QLineEdit(self)
        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Username:", self.username_edit)
        form_layout.addRow("Password:", self.password_edit)
        main_layout.addLayout(form_layout)

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        try:
            self.buttons.accepted.connect(self.accept)
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"E' successo un errore: {e}")
            return
        self.buttons.rejected.connect(self.reject)
        main_layout.addWidget(self.buttons)

        self.version_lbl = QLabel("Versione 1.7.2 - 20/05/2024")
        main_layout.addWidget(self.version_lbl)

        # Check statuses
        #self.RefreshConn()
        #self.check_sql_server_status()
        #self.check_plc_status()
        #self.check_report_status()

    def get_credentials(self):
        return self.username_edit.text(), self.password_edit.text()
    
    def ConnectionForm(self):
        connection_form_dialog = ConnectionForm()
        connection_form_dialog.exec_()

    def RefreshConn(self):
        if self.refresh_thread is None or not self.refresh_thread.is_alive():
            # Only start a new refresh thread if there is no active thread
            self.refresh_thread = threading.Thread(target=self.perform_refresh)
            self.refresh_thread.start()

    def perform_refresh(self):
        try:
            self.check_sql_server_status()
            self.check_plc_status()
            self.check_report_status()
        except Exception as e:
            print(f"An error occurred during refresh: {e}")

    def check_sql_server_status(self):
        try:
            # Attempt to connect to your SQL server
            conn = get_db_connection()
            conn.close()
            self.database_status_label.setPixmap(self.green_pixmap)
        except pyodbc.Error:
            self.database_status_label.setPixmap(self.red_pixmap)

    def check_plc_status(self):
        try:
            # Connect to the OPC server
            client = Client(f"opc.tcp://{ip}:4840")
            client.session_timeout = 30000
            client.connect()

            # If connection is successful, set status to green
            self.plc_status_label.setPixmap(self.green_pixmap)

            # Disconnect from the OPC server
            client.disconnect()

        except Exception as e:
            #print(f"An error occurred: {e}")
            # If connection fails, set status to red
            self.plc_status_label.setPixmap(self.red_pixmap)

    def check_report_status(self):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                self.rep_status_label.setPixmap(self.green_pixmap)
            else:
                self.rep_status_label.setPixmap(self.red_pixmap)    
        except:
            self.rep_status_label.setPixmap(self.red_pixmap)

    def reject(self):
        sys.exit()

#--------------------------------------------------------------------END OF LOGIN GLOBAL CLASSES
#--------------------------------------------------------------------BEGIN OF INGREDIENT GLOBAL CLASSES
        
class AddEditDialog(QDialog):
    refresh_signal = pyqtSignal()
    def __init__(self, tableWidget, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aggiunge Ingredienti")
        self.resize(400, 400)

        layout = QVBoxLayout()
        radio_layout = QHBoxLayout()

        # Store the reference to the tableWidget
        self.tableWidget = tableWidget

        self.code_label = QLabel("Codice:")
        self.code_edit = QLineEdit()
        layout.addWidget(self.code_label)
        layout.addWidget(self.code_edit)

        self.description_label = QLabel("Descrizione:")
        self.description_edit = QLineEdit()
        layout.addWidget(self.description_label)
        layout.addWidget(self.description_edit)

        self.area_label = QLabel("Area:")
        self.area_combo = QComboBox()
        layout.addWidget(self.area_label)
        layout.addWidget(self.area_combo)

        self.serbatoio_label = QLabel("Serbatoio:")
        self.serbatoio_edit = QComboBox()
        layout.addWidget(self.serbatoio_label)
        layout.addWidget(self.serbatoio_edit)

        self.cserbatoio_label = QLabel("Codice Serbatoio:")
        self.cserbatoio_edit = QComboBox()
        layout.addWidget(self.cserbatoio_label)
        layout.addWidget(self.cserbatoio_edit)

        self.manual_radio = QRadioButton("Manuale")
        self.automatic_radio = QRadioButton("Automatico")
        radio_layout.addWidget(self.automatic_radio)
        radio_layout.addWidget(self.manual_radio)
        layout.addLayout(radio_layout)
        self.type_group = QButtonGroup(self)
        self.type_group.addButton(self.automatic_radio)
        self.type_group.addButton(self.manual_radio)
        self.automatic_radio.setChecked(True)

        self.rework_type_label = QLabel("Tipo Rework:")
        self.rework_type_combo = QComboBox()
        self.rework_type_combo.setCurrentIndex(1)
        layout.addWidget(self.rework_type_label)
        layout.addWidget(self.rework_type_combo)

        self.save_button = QPushButton("Salva")
        self.cancel_button = QPushButton("Anulla")
        layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save_data)
        layout.addWidget(self.cancel_button)
        self.cancel_button.clicked.connect(self.reject)

        self.serbatoio_edit.currentIndexChanged.connect(self.on_serbatoio_changed)
        self.cserbatoio_edit.currentIndexChanged.connect(self.on_cserbatoio_changed)

        self.setLayout(layout)

    def on_serbatoio_changed(self):
        storage_id = self.serbatoio_edit.currentData()  # Get the storage ID associated with the selected storage name
        index = self.cserbatoio_edit.findText(str(storage_id))
        if index >= 0:
            self.cserbatoio_edit.setCurrentIndex(index)

    def on_cserbatoio_changed(self):
        storage_name = self.cserbatoio_edit.currentData()  # Get the storage name associated with the selected storage ID
        index = self.serbatoio_edit.findText(storage_name)
        if index >= 0:
            self.serbatoio_edit.setCurrentIndex(index)

    def populate_fields(self, cursor):
        # Ensure signals are disconnected before reconnecting to prevent multiple connections
        self.serbatoio_edit.currentIndexChanged.disconnect(self.on_serbatoio_changed)
        self.cserbatoio_edit.currentIndexChanged.disconnect(self.on_cserbatoio_changed)
        # Populate area_combo
        cursor.execute('SELECT ia_description FROM dbo.IngredientArea')
        for row in cursor.fetchall():
            self.area_combo.addItem(row[0])

        # Populate rework_type_combo
        cursor.execute('SELECT irt_description FROM dbo.IngredientReworkType')
        for row in cursor.fetchall():
            self.rework_type_combo.addItem(row[0])

        # Populate serbatoio_edit with storage names and associate storage IDs as user data
        cursor.execute('SELECT st_storagename, st_storageid FROM dbo.Storage')
        for row in cursor.fetchall():
            self.serbatoio_edit.addItem(row[0], row[1])

        # Populate cserbatoio_edit with storage IDs as item text and storage names as user data
        cursor.execute('SELECT st_storageid, st_storagename FROM dbo.Storage')
        for row in cursor.fetchall():
            self.cserbatoio_edit.addItem(str(row[0]), row[1])

        self.serbatoio_edit.currentIndexChanged.connect(self.on_serbatoio_changed)
        self.cserbatoio_edit.currentIndexChanged.connect(self.on_cserbatoio_changed)

    def save_data(self):
        code = self.code_edit.text()
        description = self.description_edit.text()
        area = self.area_combo.currentText()
        manual = self.manual_radio.isChecked()
        rework_type = self.rework_type_combo.currentText()
        serb = self.serbatoio_edit.currentText()
        cserb = self.cserbatoio_edit.currentText()

        if not code:
            QMessageBox.warning(self, "Errore", "Il codice non può essere vuoto.")
            return

        # Connect to the database
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)

        try:
            cursor = conn.cursor()

            # Check if the code is already in use --- DUPLICITY CHECK
            cursor.execute("SELECT im_code FROM dbo.IngredientMaster WHERE im_code = ?", code)
            existing_code = cursor.fetchone()

            if existing_code:
                QMessageBox.warning(self, "Errore", "Il codice è già in uso da un altro ingrediente.")
                return  # Stop execution as the code is already in use

            # Convert area and rework_type to their respective IDs
            cursor.execute("SELECT ia_areaid FROM dbo.IngredientArea WHERE ia_description = ?", area)
            area_id = cursor.fetchone()[0]

            cursor.execute("SELECT irt_reworktypeid FROM dbo.IngredientReworkType WHERE irt_description = ?", rework_type)
            rework_type_id = cursor.fetchone()[0]

            # Insert data without specifying im_ingredientid
            insert_sql = """
            INSERT INTO dbo.IngredientMaster (im_ingredientid, im_code, im_description, im_accosid, im_areaid, im_typeid, im_reworktypeid, im_storage, im_storagename) 
            SELECT COALESCE(MAX(im_ingredientid), 0) + 1, ?, ?, NULL, ?, ?, ?, ?, ?
            FROM dbo.IngredientMaster
            """
            cursor.execute(insert_sql, (code, description, area_id, 0 if manual else 1, rework_type_id, cserb, serb))
            conn.commit()

            # Close the database connection
            conn.close()
        except pyodbc.Error as e:
            QMessageBox.critical(self, "Errore Database", f"E' successo un errore: {e}")
            return  # Early exit on error
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"E' successo un errore: {e}")
            return  # Early exit on general errors
        else:
            QMessageBox.information(self, "Successo", "Ingrediente salvato con successo.")
            self.accept()
            self.refresh_signal.emit()

class EditIngredientsDialog(QDialog):
    refresh_signal = pyqtSignal()
    def __init__(self, ingredient_id, parent=None):
        super().__init__(parent)
        self.ingredient_id = ingredient_id
        self.setWindowTitle("Modifica Ingredienti")
        self.setGeometry(100, 100, 800, 800)

        layout = QVBoxLayout(self)
        radio_layout = QHBoxLayout()
        
        self.code_label = QLabel("Codice:")
        self.code_edit = QLineEdit()
        layout.addWidget(self.code_label)
        layout.addWidget(self.code_edit)

        self.description_label = QLabel("Descrizione:")
        self.description_edit = QLineEdit()
        layout.addWidget(self.description_label)
        layout.addWidget(self.description_edit)

        self.area_label = QLabel("Area:")
        self.area_combo = QComboBox()
        layout.addWidget(self.area_label)
        layout.addWidget(self.area_combo)

        self.serbatoio_label = QLabel("Serbatoio:")
        self.serbatoio_edit = QComboBox()
        layout.addWidget(self.serbatoio_label)
        layout.addWidget(self.serbatoio_edit)

        self.cserbatoio_label = QLabel("Codice Serbatoio:")
        self.cserbatoio_edit = QComboBox()
        layout.addWidget(self.cserbatoio_label)
        layout.addWidget(self.cserbatoio_edit)

        self.manual_radio = QRadioButton("Manuale")
        self.automatic_radio = QRadioButton("Automatico")
        radio_layout.addWidget(self.automatic_radio)
        radio_layout.addWidget(self.manual_radio)
        layout.addLayout(radio_layout)
        self.type_group = QButtonGroup(self)
        self.type_group.addButton(self.automatic_radio)
        self.type_group.addButton(self.manual_radio)
        self.automatic_radio.setChecked(True)

        self.rework_type_label = QLabel("Tipo Rework:")
        self.rework_type_combo = QComboBox()
        self.rework_type_combo.setCurrentIndex(1)
        layout.addWidget(self.rework_type_label)
        layout.addWidget(self.rework_type_combo)

        self.save_button = QPushButton("Salva")
        self.cancel_button = QPushButton("Anulla")
        layout.addWidget(self.save_button)
        #self.save_button.clicked.connect(self.save_data)
        layout.addWidget(self.cancel_button)
        self.cancel_button.clicked.connect(self.reject)

        self.serbatoio_edit.currentIndexChanged.connect(self.on_serbatoio_changed)
        self.cserbatoio_edit.currentIndexChanged.connect(self.on_cserbatoio_changed)

        self.setLayout(layout)
        self.populate_options()
        self.populate_fields()

        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT im_code FROM dbo.IngredientMaster WHERE im_code = ?", (self.ingredient_id,))
        originalcode = cursor.fetchone()
        if originalcode:
            originalcode = originalcode[0]
        self.save_button.clicked.connect(lambda: self.save_data(originalcode))

    def populate_fields(self):
        # Connect to the database
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Fetch the ingredient data
            cursor.execute("SELECT * FROM dbo.IngredientMaster WHERE im_code = ?", (self.ingredient_id,))
            ingredient_data = cursor.fetchone()

            if ingredient_data is not None:
                # Populate fields with the ingredient data
                self.code_edit.setText(str(ingredient_data.im_code))
                self.description_edit.setText(ingredient_data.im_description)

                # Populate area combo box
                cursor.execute("SELECT ia_description FROM dbo.IngredientArea WHERE ia_areaid = ?", (ingredient_data.im_areaid,))
                area_description = cursor.fetchone()
                if area_description:
                    self.area_combo.setCurrentText(area_description[0])

                # Populate rework type combo box
                cursor.execute("SELECT irt_description FROM dbo.IngredientReworkType WHERE irt_reworktypeid = ?", (ingredient_data.im_reworktypeid,))
                rework_description = cursor.fetchone()
                if rework_description:
                    self.rework_type_combo.setCurrentText(rework_description[0])

                # Populate serbatoio name and id combo boxes
                self.set_combobox_selection(self.cserbatoio_edit, ingredient_data.im_storage)
                self.set_combobox_selection(self.serbatoio_edit, ingredient_data.im_storagename)

                # Set radio buttons
                self.manual_radio.setChecked(ingredient_data.im_typeid == 0)
                self.automatic_radio.setChecked(ingredient_data.im_typeid != 0)

        except pyodbc.Error as e:
            QMessageBox.critical(self, "Errore Database", f"E' successo un errore: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"E' successo un errore: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    def set_combobox_selection(self, combo_box, value):
        index = combo_box.findText(str(value))
        combo_box.setCurrentIndex(index if index >= 0 else 0)

    def on_serbatoio_changed(self):
        storage_id = self.serbatoio_edit.currentData()  # Get the storage ID associated with the selected storage name
        index = self.cserbatoio_edit.findText(str(storage_id))
        if index >= 0:
            self.cserbatoio_edit.setCurrentIndex(index)

    def on_cserbatoio_changed(self):
        storage_name = self.cserbatoio_edit.currentData()  # Get the storage name associated with the selected storage ID
        index = self.serbatoio_edit.findText(storage_name)
        if index >= 0:
            self.serbatoio_edit.setCurrentIndex(index)

    def populate_options(self):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

        with pyodbc.connect(conn_str) as conn:
            try:
                cursor = conn.cursor()
                # Populate area_combo
                cursor.execute('SELECT ia_description FROM dbo.IngredientArea')
                for row in cursor.fetchall():
                    self.area_combo.addItem(row[0])

                # Populate rework_type_combo
                cursor.execute('SELECT irt_description FROM dbo.IngredientReworkType')
                for row in cursor.fetchall():
                    self.rework_type_combo.addItem(row[0])

                # Populate serbatoio_edit with storage names and associate storage IDs as user data
                cursor.execute('SELECT st_storagename, st_storageid FROM dbo.Storage')
                for row in cursor.fetchall():
                    self.serbatoio_edit.addItem(row[0], userData=row[1])

                # Populate cserbatoio_edit with storage IDs as item text and storage names as user data
                cursor.execute('SELECT st_storageid, st_storagename FROM dbo.Storage')
                for row in cursor.fetchall():
                    self.cserbatoio_edit.addItem(str(row[0]), row[1])

                self.serbatoio_edit.currentIndexChanged.connect(self.on_serbatoio_changed)
                self.cserbatoio_edit.currentIndexChanged.connect(self.on_cserbatoio_changed)

            except pyodbc.Error as e:
                QMessageBox.critical(self, "Errore Database", f"E' successo un errore: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"E' successo un errore: {e}")
    
    def save_data(self, originalcode):
        code = self.code_edit.text()
        description = self.description_edit.text()
        area = self.area_combo.currentText()
        manual = self.manual_radio.isChecked()
        rework_type = self.rework_type_combo.currentText()
        serb = self.serbatoio_edit.currentText()
        selected_storage_id = self.serbatoio_edit.currentData()

        # Connect to the database
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Check if the code is already in use by another ingredient
            cursor.execute("SELECT im_code FROM dbo.IngredientMaster WHERE im_code = ?", originalcode)
            existing_code = cursor.fetchone()

            if existing_code and existing_code[0] != self.ingredient_id:
                QMessageBox.warning(self, "Errore", "Il codice è già in uso da un altro ingrediente.")
                return  # Stop execution as the code is already in use

            # Convert area and rework_type to their respective IDs
            cursor.execute("SELECT ia_areaid FROM dbo.IngredientArea WHERE ia_description = ?", area)
            area_id = cursor.fetchone()[0]

            cursor.execute("SELECT irt_reworktypeid FROM dbo.IngredientReworkType WHERE irt_description = ?", rework_type)
            rework_type_id = cursor.fetchone()[0]

            # Update ingredient data
            update_sql = """
            UPDATE dbo.IngredientMaster
            SET im_code = ?, im_description = ?, im_areaid = ?, im_typeid = ?, im_reworktypeid = ?, im_storage = ?, im_storagename = ?
            WHERE im_code = ?
            """
            cursor.execute(update_sql, (code, description, area_id, 0 if manual else 1, rework_type_id, selected_storage_id, serb, originalcode))
            conn.commit()

            QMessageBox.information(self, "Successo", "Ingrediente modificato con successo.")
            self.accept()
            self.refresh_signal.emit()

        except pyodbc.Error as e:
            QMessageBox.critical(self, "Errore Database", f"E' successo un errore: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Si è verificato un errore: {e}")
        finally:
            if conn:
                conn.close()

#--------------------------------------------------------------------END OF INGREDIENT GLOBAL CLASSES
#--------------------------------------------------------------------BEGIN OF RECIPE GLOBAL CLASSES
                
class EditableDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, role=Qt.DisplayRole)
        editor.setText(str(value))

    def setModelData(self, editor, model, index):
        value = editor.text()
        model.setData(index, value, role=Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class RecipeDialog(QDialog):
    recipeAdded = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuova Ricetta")
        layout = QVBoxLayout(self)

        first_row_layout = QVBoxLayout()
        self.code_label = QLabel("Codice: ", self)
        self.code_edit = QLineEdit(self)
        self.description_label = QLabel("Descrizione: ", self)
        self.description_edit = QLineEdit(self)
        self.line_label = QLabel("Linea: ", self)
        self.line_edit = QComboBox(self)
        self.line_edit.addItems(["B", "C", "D"])

        first_row_layout.addWidget(self.code_label)
        first_row_layout.addWidget(self.code_edit)
        first_row_layout.addWidget(self.description_label)
        first_row_layout.addWidget(self.description_edit)
        first_row_layout.addWidget(self.line_label)
        first_row_layout.addWidget(self.line_edit)

        layout.addLayout(first_row_layout)

        second_section_layout = QHBoxLayout()
        self.pasteurizer_temp_label = QLabel("Temperatura Pastorizatore: ", self)
        self.pasteurizer_temp_edit = QLineEdit("88")
        self.homogenizer_pressure_label = QLabel("Pressione Omogeneizzatore:", self)
        self.homogenizer_pressure_edit = QLineEdit("200")
        self.homogenizer_speed_label = QLabel("Velocità Omogeneizzatore: ", self)
        self.homogenizer_speed_edit = QLineEdit("100")
        self.mix_tank_time_label = QLabel("Blender Holding Time (min): ", self)
        self.mix_tank_time_edit = QLineEdit("20")

        second_section_layout.addWidget(self.pasteurizer_temp_label)
        second_section_layout.addWidget(self.pasteurizer_temp_edit)
        second_section_layout.addWidget(self.homogenizer_pressure_label)
        second_section_layout.addWidget(self.homogenizer_pressure_edit)
        second_section_layout.addWidget(self.homogenizer_speed_label)
        second_section_layout.addWidget(self.homogenizer_speed_edit)
        second_section_layout.addWidget(self.mix_tank_time_label)
        second_section_layout.addWidget(self.mix_tank_time_edit)

        layout.addLayout(second_section_layout)

        self.buttons_layout = QHBoxLayout()
        self.ok_button = QPushButton("Salva", self)
        self.cancel_button = QPushButton("Anulla", self)
        self.buttons_layout.addWidget(self.ok_button)
        self.buttons_layout.addWidget(self.cancel_button)

        self.ok_button.clicked.connect(self.recipe_save_data)
        self.cancel_button.clicked.connect(self.reject)

        layout.addLayout(self.buttons_layout)

    def recipe_save_data(self):
        try:
            code = self.code_edit.text()
            description = self.description_edit.text()
            line = self.line_edit.currentText()
            pastemp = self.pasteurizer_temp_edit.text()
            hopress = self.homogenizer_pressure_edit.text()
            hospeed = self.homogenizer_speed_edit.text()
            mixtime = self.mix_tank_time_edit.text()

            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            cursor.execute("SELECT rm_recipeid FROM dbo.RecipeMaster WHERE rm_recipeid = ?", code)
            existing_code = cursor.fetchone()

            if existing_code:
                QMessageBox.warning(self, "Errore", "Il codice è già in uso da un altra ricetta.")
                return

            insert_sql = """
            INSERT INTO [RecipeDB].[dbo].[RecipeMaster] (rm_recipeid, rm_description, rm_fat, rm_solid, rm_patemperature, rm_pressureid, rm_numingredients, rm_numaccosingredients, rm_lastedit, rm_quantity, rm_stdquantity, rm_holdingtime, rm_line, rm_omospeed, rm_omopress) 
            SELECT ?, ?, 0, 0, ?, 1, 0, 0, GETDATE(), 100, 100, ?, ?, ?, ?
            """
            cursor.execute(insert_sql, (code, description, pastemp, mixtime, line, hospeed, hopress))
            conn.commit()

            conn.close()
            self.recipeAdded.emit()
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Si è verificato un errore: {e}")

class RecipeDialogBase(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

    def create_db_connection(self):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        return pyodbc.connect(conn_str)

    def execute_query(self, query, params=None, fetch=True):
        with self.create_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            if fetch:
                return cursor.fetchall()
            else:
                conn.commit()                                   

class EditRecipeIngredientsDialog(RecipeDialogBase):
    ingredientAdded = pyqtSignal()
    recipeUpdated = pyqtSignal()
    def __init__(self, recipe_id, parent=None):
        super().__init__(parent)
        self.recipe_id = recipe_id  # Store recipe_id as an instance variable
        self.setWindowTitle("Modifica Ricetta/Ingredienti")
        self.setGeometry(100, 100, 1500, 800)

        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Fetch description and line from the database
        cursor.execute("SELECT [rm_description], [rm_line], [rm_patemperature], [rm_holdingtime], [rm_omospeed], [rm_omopress] FROM dbo.RecipeMaster WHERE [rm_recipeid] = ?", (recipe_id))
        row = cursor.fetchone()
        
        self.descr_rec = row[0] if row else "" 
        self.line_rec = row[1] if row else "" 
        self.ptemp_rec = row[2] if row else ""
        self.htime_rec = row[3] if row else ""
        self.omos_rec = row[4] if row else ""
        self.omop_rec = row[5] if row else ""

        conn.close()

        layout = QVBoxLayout(self)
        self.ingredients_table = self.create_ingredients_table(layout)
        self.load_ingredients(self.recipe_id)
        self.ingredientAdded.connect(self.refresh_ingredients)
        self.ingredients_table.itemChanged.connect(self.update_percentage_in_table)
    
    def add_button_clicked(self):
        dialog = AddIngredientDialog(self.recipe_id, parent=self, parent_dialog=self)
        dialog.exec_()

    def modify_ingredient(self):
        selected_row = self.ingredients_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un ingrediente da modificare.")
            return

        ingredient_code = self.ingredients_table.item(selected_row, 3).text()  # Assuming column 3 contains the ingredient code
        current_percentage = self.ingredients_table.item(selected_row, 5).text()  # Assuming column 5 contains the percentage

        self.open_modification_dialog(ingredient_code, current_percentage)

    def update_total_percentage(self, item):
        if item.column() == 5:  # Check if the changed item is in the "Percentuale" column
            total_percentage = 0.0
            for row in range(self.ingredients_table.rowCount()):
                percentage_item = self.ingredients_table.item(row, 5)
                if percentage_item and percentage_item.text():
                    percentage_value = float(percentage_item.text().replace(',', '.'))
                    total_percentage += percentage_value
            formatted_percentage = "{:.3f}".format(total_percentage)
            self.total_percentage_txt.setText(str(formatted_percentage))

    def update_percentage_in_table(self, item):
        if item.column() == 5:  # Check if the changed item is in the "Percentuale" column
            new_percentage = item.text().replace(',', '.')
            selected_row = self.ingredients_table.currentRow()
            if selected_row != -1:  # Ensure a row is selected
                percentage_item = self.ingredients_table.item(selected_row, 5)
                if ',' in new_percentage:
                    QMessageBox.warning(self, "Attenzione", "Inserire valore con punto invece di virgola.")
                    return
                
                if percentage_item is not None:
                    percentage_item.setText(new_percentage)
                    self.save_percentage_to_database(selected_row, new_percentage)
                else:
                    # If for some reason the item doesn't exist, create it and set it
                    percentage_item = QTableWidgetItem(new_percentage)
                    self.ingredients_table.setItem(selected_row, 5, percentage_item)         
    
    def save_percentage_to_database(self, row, new_percentage):
        # Extract the primary key or unique identifier for the row
        recipeid = self.ingredients_table.item(row, 0).text()
        ingrcode = self.ingredients_table.item(row, 2).text()
        # Update the database with the new percentage value
        query = "UPDATE dbo.RecipeIngredients SET ri_percentage = ? WHERE ri_recipeid = ? and ri_ingredientid = ?"
        parameters = (new_percentage, recipeid, ingrcode)
        
        try:
            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                cursor.execute(query, parameters)
                conn.commit()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while updating the database: {str(e)}")

    def create_ingredients_table(self, layout):
        # Create a horizontal layout for input fields
        input_fields_layout = QHBoxLayout()
        input2_fields_layout = QHBoxLayout()
        
        self.recipe_lbl = QLabel("Num. Ricetta:")
        self.recipe_txt = QLineEdit(str(self.recipe_id))
        self.descr_lbl = QLabel("Descrizione:")
        self.descr_txt = QLineEdit(self.descr_rec)
        self.line_lbl = QLabel("Linea:")
        self.line_combo = QComboBox()
        self.line_combo.addItems(["B", "C", "D"])
        if self.line_rec:
            index = self.line_combo.findText(self.line_rec)
            if index != -1:
                self.line_combo.setCurrentIndex(index)

        self.total_percentage_lbl = QLabel("Percentuale Totale:")
        self.total_percentage_txt = QLineEdit()
        self.total_percentage_txt.setReadOnly(True)
        
        # Add input field widgets to the horizontal layout
        input_fields_layout.addWidget(self.recipe_lbl)
        input_fields_layout.addWidget(self.recipe_txt)
        input_fields_layout.addWidget(self.descr_lbl)
        input_fields_layout.addWidget(self.descr_txt)
        input_fields_layout.addWidget(self.line_lbl)
        input_fields_layout.addWidget(self.line_combo)
        input_fields_layout.addWidget(self.total_percentage_lbl)
        input_fields_layout.addWidget(self.total_percentage_txt)

        self.ptemp_lbl = QLabel("Temp. Pastorizzatore:")
        self.ptemp_txt = QLineEdit(str(self.ptemp_rec) if self.ptemp_rec is not None else "")
        self.htime_lbl = QLabel("Holding Time (min.):")
        self.htime_txt = QLineEdit(str(self.htime_rec) if self.htime_rec is not None else "")
        self.omop_lbl = QLabel("Pressione Omo.:")
        self.omop_txt = QLineEdit(str(self.omop_rec) if self.omop_rec is not None else "")
        self.omos_lbl = QLabel("Velocità Omo.:")
        self.omos_txt = QLineEdit(str(self.omos_rec) if self.omos_rec is not None else "")

        input2_fields_layout.addWidget(self.ptemp_lbl)
        input2_fields_layout.addWidget(self.ptemp_txt)
        input2_fields_layout.addWidget(self.htime_lbl)
        input2_fields_layout.addWidget(self.htime_txt)
        input2_fields_layout.addWidget(self.omop_lbl)
        input2_fields_layout.addWidget(self.omop_txt)
        input2_fields_layout.addWidget(self.omos_lbl)
        input2_fields_layout.addWidget(self.omos_txt)
        
        # Add the horizontal input fields layout to the vertical layout
        layout.addLayout(input_fields_layout)
        layout.addLayout(input2_fields_layout)
        self.ingredients_lbl = QLabel("Ingredienti della Ricetta:")
        self.ingredients_table = QTableWidget(self)  # Create and assign the QTableWidget
        self.ingredients_table.setColumnCount(6)
        self.ingredients_table.setHorizontalHeaderLabels(["Ricetta", "Sequenza", "ID", "Codice", "Descrizione", "Percentuale"])
        self.ingredients_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.ingredients_lbl)
        layout.addWidget(self.ingredients_table)

        # Make the "Percentuale" column editable
        self.ingredients_table.setItemDelegateForColumn(5, EditableDelegate(self))

        # Connect the textChanged signal of the "Percentuale" column to update the total percentage
        self.ingredients_table.itemChanged.connect(self.update_total_percentage)
        
        # Create the buttons
        self.add_ingredient_button = QPushButton("Aggiungere Ingrediente", self)
        self.upsq_ingredient_button = QPushButton("Sposta Ingr. Su", self)
        self.dwsq_ingredient_button = QPushButton("Sposta Ingr. Giù", self) #skipper
        self.delete_ingredient_button = QPushButton("Cancella Ingrediente", self)
        self.save_recipe_button = QPushButton("Salva Ricetta", self)

        # Layout for buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.add_ingredient_button)
        buttons_layout.addWidget(self.upsq_ingredient_button)
        buttons_layout.addWidget(self.dwsq_ingredient_button)
        buttons_layout.addWidget(self.delete_ingredient_button)
        buttons_layout.addWidget(self.save_recipe_button)
        layout.addLayout(buttons_layout)

        # Connect buttons to their actions
        self.add_ingredient_button.clicked.connect(self.add_button_clicked)
        self.upsq_ingredient_button.clicked.connect(self.up_selected_schedule)
        self.dwsq_ingredient_button.clicked.connect(self.down_selected_schedule)
        self.delete_ingredient_button.clicked.connect(self.delete_ingredient)
        self.save_recipe_button.clicked.connect(self.save_recipe)

        # Load the ingredients for the recipe
        self.load_ingredients(self.recipe_id)
        return self.ingredients_table

    def refresh_ingredients(self):
        self.load_ingredients(self.recipe_id)

    def load_ingredients(self, recipe_id):
        # Clear the table first
        self.ingredients_table.setRowCount(0)
        
        # Load new data from the database
        query = """SELECT ri.ri_recipeid, ri.ri_sequence, ri.ri_ingredientid, im.im_code,
        im.im_description, ri.ri_percentage 
        FROM RecipeDB.dbo.RecipeIngredients ri
        JOIN RecipeDB.dbo.IngredientMaster im ON ri.ri_ingredientid = im.im_ingredientid
        WHERE ri.ri_recipeid = ? ORDER BY ri.ri_sequence ASC"""
        rows = self.execute_query(query, (recipe_id))
        self.populate_ingredients_table(rows)

    def up_selected_schedule(self):
        selected_row = self.ingredients_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selezione Richiesta", "Selezionare prima un ingredienti per spostare su.")
            return
        
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        rcp_ref_item = self.ingredients_table.item(selected_row, 0)
        seq_ref_item = self.ingredients_table.item(selected_row, 1)
        cod_ref_item = self.ingredients_table.item(selected_row, 2)
        rcp_ref = int(rcp_ref_item.text())
        seq_ref = int(seq_ref_item.text())
        cod_ref = int(cod_ref_item.text())
        seq_new = seq_ref - 1

        query = "SELECT ri_ingredientid FROM dbo.RecipeIngredients WHERE ri_sequence = ? and ri_recipeid = ?"
        cursor.execute(query, (seq_new,rcp_ref))
        cod_pv = cursor.fetchone()
        if cod_pv == None:
            cod_prev = 0
        else:
            cod_prev = int(cod_pv[0])

        if (seq_ref - 1) == 0:
            QMessageBox.warning(self, "Attenzione", "Ingredienti già è alla prima posizione disponibile.")
            return

        reply = QMessageBox.question(self, "Conferma",
                                    f"Sei sicuro di voler spostare l'ingredienti alla posizione {seq_ref - 1}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            seq_prev = seq_new + 1
            update_up = """
            UPDATE dbo.RecipeIngredients
            SET ri_sequence = ?
            WHERE ri_ingredientid = ? and ri_recipeid = ?;
            """
            cursor.execute(update_up, (seq_new, cod_ref, rcp_ref))

            update_down = """
            UPDATE dbo.RecipeIngredients
            SET ri_sequence = ?
            WHERE ri_ingredientid = ? and ri_recipeid = ?;
            """
            cursor.execute(update_down, (seq_prev, cod_prev, rcp_ref))

            conn.commit()
            self.refresh_ingredients()
      
    def down_selected_schedule(self):
        selected_row = self.ingredients_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selezione Richiesta", "Selezionare prima un ingredienti per spostare su.")
            return
        
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        rcp_ref_item = self.ingredients_table.item(selected_row, 0)
        seq_ref_item = self.ingredients_table.item(selected_row, 1)
        cod_ref_item = self.ingredients_table.item(selected_row, 2)
        rcp_ref = int(rcp_ref_item.text())
        seq_ref = int(seq_ref_item.text())
        cod_ref = int(cod_ref_item.text())
        seq_new = seq_ref + 1

        query = "SELECT COUNT(*) FROM dbo.RecipeIngredients WHERE ri_recipeid = ?"
        cursor.execute(query, (rcp_ref))
        rcptotal = cursor.fetchone()[0]

        query = "SELECT ri_ingredientid FROM dbo.RecipeIngredients WHERE ri_sequence = ? and ri_recipeid = ?"
        cursor.execute(query, (seq_new, rcp_ref))
        cod_af = cursor.fetchone()
        if cod_af is None:
            cod_after = 0
        else:
            cod_after = int(cod_af[0])

        if (seq_ref + 1) > rcptotal:
            QMessageBox.warning(self, "Attenzione", "Ingredienti già è all'ultima posizione disponibile.")
            return
        elif seq_ref  == rcptotal:
            QMessageBox.warning(self, "Attenzione", "Ingredienti già è all'ultima posizione disponibile.")
            return

        reply = QMessageBox.question(self, "Conferma",
                                    f"Sei sicuro di voler spostare l'ingredienti alla posizione {seq_ref + 1}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            update_up = """
            UPDATE dbo.RecipeIngredients
            SET ri_sequence = ?
            WHERE ri_ingredientid = ? and ri_recipeid = ?;

            UPDATE dbo.RecipeIngredients
            SET ri_sequence = ?
            WHERE ri_ingredientid = ? and ri_recipeid = ?;
            """
            cursor.execute(update_up, (seq_new, cod_ref, rcp_ref, seq_ref, cod_after, rcp_ref))
            conn.commit()
            self.refresh_ingredients()

    def populate_ingredients_table(self, rows):
        self.ingredients_table.setRowCount(0)
        for row_index, row_data in enumerate(rows):
            self.ingredients_table.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                item = QTableWidgetItem(str(data))
                self.ingredients_table.setItem(row_index, col_index, item)

    def open_modification_dialog(self, ingredient_code, current_percentage):
        dialog = IngredientModificationDialog(
            ingredient_code, 
            current_percentage, 
            on_accept_callback=self.update_ingredient_in_database,  # Pass the callback here
            parent=self
        )
        dialog.exec_()

    def delete_ingredient(self):
        selected_row = self.ingredients_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un ingrediente da cancellare.")
            return
        
        ingredient_id_item = self.ingredients_table.item(selected_row, 2)
        if ingredient_id_item is None:
            QMessageBox.warning(self, "Errore", "Nessun ingrediente trovato per l'item selezionato")
            return

        ingredient_id = ingredient_id_item.text()  # Retrieve the ingredient ID here
        reply = QMessageBox.question(self, "Conferma Cancellazione",
                                    f"Sei sicuro di voler cancellare l'ingrediente di ID {ingredient_id}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            recipe_id = self.ingredients_table.item(selected_row, 0).text()  # Assuming recipe ID is in the 1st column
            sequence = self.ingredients_table.item(selected_row, 1).text()  # Assuming sequence is in the 2nd column

            try:
                conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
                with pyodbc.connect(conn_str) as conn:
                    cursor = conn.cursor()
                    query = "DELETE FROM dbo.RecipeIngredients WHERE ri_recipeid = ? AND ri_sequence = ? AND ri_ingredientid = ?"
                    cursor.execute(query, (recipe_id, sequence, ingredient_id))
                    conn.commit()
                    QMessageBox.information(self, "Successo", "Ingrediente cancellato con successo.")
                    self.refresh_ingredients()  # Make sure to call the method here
            except Exception as e:
                QMessageBox.warning(self, "Cancellazione Fallita", f"Si è verificato un errore: {e}")

    def save_recipe(self):
        # Get the values from the input fields
        new_recipe_id = self.recipe_txt.text()
        new_description = self.descr_txt.text()
        new_line = self.line_combo.currentText()
        new_ptemp = self.ptemp_txt.text()
        new_htime = self.htime_txt.text()
        new_omop = self.omop_txt.text()
        new_omos = self.omos_txt.text()
        total_percentage = float(self.total_percentage_txt.text().replace(',', '.'))
        
        if total_percentage != 100:
            QMessageBox.warning(self, "Attenzione", "Somma della ricetta non raggiunge il 100%. Controllare il percentuale degli ingredienti.")
            return

        try:
            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()

                # If the recipe ID has changed, check if the new ID already exists
                if new_recipe_id != self.recipe_id:
                    cursor.execute("SELECT COUNT(*) FROM dbo.RecipeMaster WHERE rm_recipeid = ?", (new_recipe_id))
                    if cursor.fetchone()[0] > 0:
                        # New recipe ID already exists, show error message and return
                        QMessageBox.warning(self, "Errore", "ID ricetta già esistente. Scegliere un ID ricetta diverso.")
                        return

                # Perform SQL UPDATE operation for RecipeMaster table
                query = "UPDATE dbo.RecipeMaster SET [rm_recipeid] = ?, [rm_description] = ?, [rm_line] = ?, [rm_patemperature] = ?, [rm_holdingtime] = ?, [rm_omospeed] = ?, [rm_omopress] = ? WHERE [rm_recipeid] = ?"
                cursor.execute(query, (new_recipe_id, new_description, new_line, new_ptemp, new_htime, new_omos, new_omop, self.recipe_id))
                conn.commit()

                # Update RecipeIngredients table if recipe ID changed
                if new_recipe_id != self.recipe_id:
                    query = "UPDATE dbo.RecipeIngredients SET [ri_recipeid] = ? WHERE [ri_recipeid] = ?"
                    cursor.execute(query, (new_recipe_id, self.recipe_id))
                    conn.commit()

                # Optionally, update the instance variables if needed
                self.recipe_id = new_recipe_id
                self.descr_rec = new_description
                self.line_rec = new_line
                self.ptemp_rec = new_ptemp
                self.htime_rec = new_htime
                self.omop_rec = new_omop
                self.omos_rec = new_omos

                for row in range(self.ingredients_table.rowCount()):
                    recipe_id = self.ingredients_table.item(row, 0).text()
                    sequence = self.ingredients_table.item(row, 1).text()
                    ingredient_id = self.ingredients_table.item(row, 2).text()
                    new_percentage = self.ingredients_table.item(row, 5).text()

                    # Update statement for the ingredient
                    query = """UPDATE dbo.RecipeIngredients
                            SET [ri_percentage] = ?
                            WHERE [ri_recipeid] = ? AND [ri_sequence] = ? AND [ri_ingredientid] = ?"""

                    # Execute the update for this ingredient
                    cursor.execute(query, (new_percentage, recipe_id, sequence, ingredient_id))

                # Commit all ingredient updates
                conn.commit()

                # Inform the user about the successful update
                QMessageBox.information(self, "Successo", "Ricetta aggiornata con successo.")
                self.recipeUpdated.emit()  # Emit signal indicating recipe update
                self.accept()

        except Exception as e:
            # Handle exceptions for RecipeMaster table update
            QMessageBox.critical(self, "Errore", f"Si è verificato un errore nell'aggiornamento: {str(e)}")
            return

class EditRecipeIngredientsDialogD(RecipeDialogBase):
    ingredientAdded = pyqtSignal()
    recipeUpdated = pyqtSignal()
    def __init__(self, recipe_id, parent=None):
        super().__init__(parent)
        self.recipe_id = recipe_id  # Store recipe_id as an instance variable
        self.setWindowTitle("Modifica Ricetta/Ingredienti")
        self.setGeometry(100, 100, 1500, 800)

        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Fetch description and line from the database
        cursor.execute("SELECT [rm_description], [rm_line], [rm_patemperature], [rm_omopress], [rm_omopress2] FROM dbo.RecipeMaster WHERE [rm_recipeid] = ?", (recipe_id))
        row = cursor.fetchone()
        
        self.descr_rec = row[0] if row else "" 
        self.line_rec = row[1] if row else "" 
        self.ptemp_rec = row[2] if row else ""
        self.omop_rec = row[3] if row else ""
        self.omop2_rec = row[4] if row else ""

        conn.close()

        layout = QVBoxLayout(self)
        self.ingredients_table = self.create_ingredients_table(layout)
        self.load_ingredients(self.recipe_id)
        self.ingredientAdded.connect(self.refresh_ingredients)
        self.ingredients_table.itemChanged.connect(self.update_percentage_in_table)
    
    def add_button_clicked(self):
        dialog = AddIngredientDialog(self.recipe_id, parent=self, parent_dialog=self)
        dialog.exec_()

    def modify_ingredient(self):
        selected_row = self.ingredients_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un ingrediente da modificare.")
            return

        ingredient_code = self.ingredients_table.item(selected_row, 3).text()  # Assuming column 3 contains the ingredient code
        current_percentage = self.ingredients_table.item(selected_row, 5).text()  # Assuming column 5 contains the percentage

        self.open_modification_dialog(ingredient_code, current_percentage)

    def update_total_percentage(self, item):
        if item.column() == 5:  # Check if the changed item is in the "Percentuale" column
            total_percentage = 0.0
            for row in range(self.ingredients_table.rowCount()):
                percentage_item = self.ingredients_table.item(row, 5)
                if percentage_item and percentage_item.text():
                    percentage_value = float(percentage_item.text().replace(',', '.'))
                    total_percentage += percentage_value
            formatted_percentage = "{:.3f}".format(total_percentage)
            self.total_percentage_txt.setText(str(formatted_percentage))

    def update_percentage_in_table(self, item):
        if item.column() == 5:  # Check if the changed item is in the "Percentuale" column
            new_percentage = item.text().replace(',', '.')
            selected_row = self.ingredients_table.currentRow()
            if selected_row != -1:  # Ensure a row is selected
                percentage_item = self.ingredients_table.item(selected_row, 5)
                if ',' in new_percentage:
                    QMessageBox.warning(self, "Attenzione", "Inserire valore con punto invece di virgola.")
                    return
                
                if percentage_item is not None:
                    percentage_item.setText(new_percentage)
                    self.save_percentage_to_database(selected_row, new_percentage)
                else:
                    # If for some reason the item doesn't exist, create it and set it
                    percentage_item = QTableWidgetItem(new_percentage)
                    self.ingredients_table.setItem(selected_row, 5, percentage_item)         
    
    def save_percentage_to_database(self, row, new_percentage):
        # Extract the primary key or unique identifier for the row
        recipeid = self.ingredients_table.item(row, 0).text()
        ingrcode = self.ingredients_table.item(row, 2).text()
        # Update the database with the new percentage value
        query = "UPDATE dbo.RecipeIngredients SET ri_percentage = ? WHERE ri_recipeid = ? and ri_ingredientid = ?"
        parameters = (new_percentage, recipeid, ingrcode)
        
        try:
            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                cursor.execute(query, parameters)
                conn.commit()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while updating the database: {str(e)}")

    def create_ingredients_table(self, layout):
        # Create a horizontal layout for input fields
        input_fields_layout = QHBoxLayout()
        input2_fields_layout = QHBoxLayout()
        
        self.recipe_lbl = QLabel("Num. Ricetta:")
        self.recipe_txt = QLineEdit(str(self.recipe_id))
        self.descr_lbl = QLabel("Descrizione:")
        self.descr_txt = QLineEdit(self.descr_rec)
        self.line_lbl = QLabel("Linea:")
        self.line_combo = QComboBox()
        self.line_combo.addItems(["B", "C", "D"])
        if self.line_rec:
            index = self.line_combo.findText(self.line_rec)
            if index != -1:
                self.line_combo.setCurrentIndex(index)

        self.total_percentage_lbl = QLabel("Percentuale Totale:")
        self.total_percentage_txt = QLineEdit()
        self.total_percentage_txt.setReadOnly(True)
        
        # Add input field widgets to the horizontal layout
        input_fields_layout.addWidget(self.recipe_lbl)
        input_fields_layout.addWidget(self.recipe_txt)
        input_fields_layout.addWidget(self.descr_lbl)
        input_fields_layout.addWidget(self.descr_txt)
        input_fields_layout.addWidget(self.line_lbl)
        input_fields_layout.addWidget(self.line_combo)
        input_fields_layout.addWidget(self.total_percentage_lbl)
        input_fields_layout.addWidget(self.total_percentage_txt)

        self.ptemp_lbl = QLabel("Temp. Pastorizzatore:")
        self.ptemp_txt = QLineEdit(str(self.ptemp_rec) if self.ptemp_rec is not None else "")
        self.omop_lbl = QLabel("Pressione Omo. 1:")
        self.omop_txt = QLineEdit(str(self.omop_rec) if self.omop_rec is not None else "")
        self.omop2_lbl = QLabel("Pressione Omo. 2:")
        self.omop2_txt = QLineEdit(str(self.omop2_rec) if self.omop2_rec is not None else "")

        input2_fields_layout.addWidget(self.ptemp_lbl)
        input2_fields_layout.addWidget(self.ptemp_txt)
        input2_fields_layout.addWidget(self.omop_lbl)
        input2_fields_layout.addWidget(self.omop_txt)
        input2_fields_layout.addWidget(self.omop2_lbl)
        input2_fields_layout.addWidget(self.omop2_txt)
        
        # Add the horizontal input fields layout to the vertical layout
        layout.addLayout(input_fields_layout)
        layout.addLayout(input2_fields_layout)
        self.ingredients_lbl = QLabel("Ingredienti della Ricetta:")
        self.ingredients_table = QTableWidget(self)  # Create and assign the QTableWidget
        self.ingredients_table.setColumnCount(6)
        self.ingredients_table.setHorizontalHeaderLabels(["Ricetta", "Sequenzia", "ID", "Codice", "Descrizione", "Percentuale"])
        self.ingredients_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.ingredients_lbl)
        layout.addWidget(self.ingredients_table)

        # Make the "Percentuale" column editable
        self.ingredients_table.setItemDelegateForColumn(5, EditableDelegate(self))

        # Connect the textChanged signal of the "Percentuale" column to update the total percentage
        self.ingredients_table.itemChanged.connect(self.update_total_percentage)
        
        # Create the buttons
        self.add_ingredient_button = QPushButton("Aggiungere Ingrediente", self)
        #self.modify_ingredient_button = QPushButton("Modifica Ingrediente", self)
        self.delete_ingredient_button = QPushButton("Cancella Ingrediente", self)
        self.save_recipe_button = QPushButton("Salva Ricetta", self)

        # Layout for buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.add_ingredient_button)
        #buttons_layout.addWidget(self.modify_ingredient_button)
        buttons_layout.addWidget(self.delete_ingredient_button)
        buttons_layout.addWidget(self.save_recipe_button)
        layout.addLayout(buttons_layout)

        # Connect buttons to their actions
        self.add_ingredient_button.clicked.connect(self.add_button_clicked)
        #self.modify_ingredient_button.clicked.connect(self.modify_ingredient)
        self.delete_ingredient_button.clicked.connect(self.delete_ingredient)
        self.save_recipe_button.clicked.connect(self.save_recipe)

        # Load the ingredients for the recipe
        self.load_ingredients(self.recipe_id)
        return self.ingredients_table

    def refresh_ingredients(self):
        self.load_ingredients(self.recipe_id)

    def load_ingredients(self, recipe_id):
        # Clear the table first
        self.ingredients_table.setRowCount(0)
        
        # Load new data from the database
        query = """SELECT ri.ri_recipeid, ri.ri_sequence, ri.ri_ingredientid, im.im_code,
        im.im_description, ri.ri_percentage 
        FROM RecipeDB.dbo.RecipeIngredients ri
        JOIN RecipeDB.dbo.IngredientMaster im ON ri.ri_ingredientid = im.im_ingredientid
        WHERE ri.ri_recipeid = ? ORDER BY ri.ri_sequence ASC"""
        rows = self.execute_query(query, (recipe_id))
        self.populate_ingredients_table(rows)

    def up_selected_schedule(self):
        selected_row = self.ingredients_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selezione Richiesta", "Selezionare prima un ingredienti per spostare su.")
            return
        
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        rcp_ref_item = self.ingredients_table.item(selected_row, 0)
        seq_ref_item = self.ingredients_table.item(selected_row, 1)
        cod_ref_item = self.ingredients_table.item(selected_row, 2)
        rcp_ref = int(rcp_ref_item.text())
        seq_ref = int(seq_ref_item.text())
        cod_ref = int(cod_ref_item.text())
        seq_new = seq_ref - 1

        query = "SELECT ri_ingredientid FROM dbo.RecipeIngredients WHERE ri_sequence = ? and ri_recipeid = ?"
        cursor.execute(query, (seq_new,rcp_ref))
        cod_pv = cursor.fetchone()
        if cod_pv == None:
            cod_prev = 0
        else:
            cod_prev = int(cod_pv[0])

        if (seq_ref - 1) == 0:
            QMessageBox.warning(self, "Attenzione", "Ingredienti già è alla prima posizione disponibile.")
            return

        reply = QMessageBox.question(self, "Conferma",
                                    f"Sei sicuro di voler spostare l'ingredienti alla posizione {seq_ref - 1}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            seq_prev = seq_new + 1
            update_up = """
            UPDATE dbo.RecipeIngredients
            SET ri_sequence = ?
            WHERE ri_ingredientid = ? and ri_recipeid = ?;
            """
            cursor.execute(update_up, (seq_new, cod_ref, rcp_ref))

            update_down = """
            UPDATE dbo.RecipeIngredients
            SET ri_sequence = ?
            WHERE ri_ingredientid = ? and ri_recipeid = ?;
            """
            cursor.execute(update_down, (seq_prev, cod_prev, rcp_ref))

            conn.commit()
            self.refresh_ingredients()
      
    def down_selected_schedule(self):
        selected_row = self.ingredients_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selezione Richiesta", "Selezionare prima un ingredienti per spostare su.")
            return
        
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        rcp_ref_item = self.ingredients_table.item(selected_row, 0)
        seq_ref_item = self.ingredients_table.item(selected_row, 1)
        cod_ref_item = self.ingredients_table.item(selected_row, 2)
        rcp_ref = int(rcp_ref_item.text())
        seq_ref = int(seq_ref_item.text())
        cod_ref = int(cod_ref_item.text())
        seq_new = seq_ref + 1

        query = "SELECT COUNT(*) FROM dbo.RecipeIngredients WHERE ri_recipeid = ?"
        cursor.execute(query, (rcp_ref))
        rcptotal = cursor.fetchone()[0]

        query = "SELECT ri_ingredientid FROM dbo.RecipeIngredients WHERE ri_sequence = ? and ri_recipeid = ?"
        cursor.execute(query, (seq_new, rcp_ref))
        cod_af = cursor.fetchone()
        if cod_af is None:
            cod_after = 0
        else:
            cod_after = int(cod_af[0])

        if (seq_ref + 1) > rcptotal:
            QMessageBox.warning(self, "Attenzione", "Ingredienti già è all'ultima posizione disponibile.")
            return
        elif seq_ref  == rcptotal:
            QMessageBox.warning(self, "Attenzione", "Ingredienti già è all'ultima posizione disponibile.")
            return

        reply = QMessageBox.question(self, "Conferma",
                                    f"Sei sicuro di voler spostare l'ingredienti alla posizione {seq_ref + 1}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            update_up = """
            UPDATE dbo.RecipeIngredients
            SET ri_sequence = ?
            WHERE ri_ingredientid = ? and ri_recipeid = ?;

            UPDATE dbo.RecipeIngredients
            SET ri_sequence = ?
            WHERE ri_ingredientid = ? and ri_recipeid = ?;
            """
            cursor.execute(update_up, (seq_new, cod_ref, rcp_ref, seq_ref, cod_after, rcp_ref))
            conn.commit()
            self.refresh_ingredients()

    def populate_ingredients_table(self, rows):
        self.ingredients_table.setRowCount(0)
        for row_index, row_data in enumerate(rows):
            self.ingredients_table.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                item = QTableWidgetItem(str(data))
                self.ingredients_table.setItem(row_index, col_index, item)

    def open_modification_dialog(self, ingredient_code, current_percentage):
        dialog = IngredientModificationDialog(
            ingredient_code, 
            current_percentage, 
            on_accept_callback=self.update_ingredient_in_database,  # Pass the callback here
            parent=self
        )
        dialog.exec_()

    def delete_ingredient(self):
        selected_row = self.ingredients_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un ingrediente da cancellare.")
            return
        
        ingredient_id_item = self.ingredients_table.item(selected_row, 2)
        if ingredient_id_item is None:
            QMessageBox.warning(self, "Errore", "Nessun ingrediente trovato per l'item selezionato")
            return

        ingredient_id = ingredient_id_item.text()  # Retrieve the ingredient ID here
        reply = QMessageBox.question(self, "Conferma Cancellazione",
                                    f"Sei sicuro di voler cancellare l'ingrediente di ID {ingredient_id}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            recipe_id = self.ingredients_table.item(selected_row, 0).text()  # Assuming recipe ID is in the 1st column
            sequence = self.ingredients_table.item(selected_row, 1).text()  # Assuming sequence is in the 2nd column

            try:
                conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
                with pyodbc.connect(conn_str) as conn:
                    cursor = conn.cursor()
                    query = "DELETE FROM dbo.RecipeIngredients WHERE ri_recipeid = ? AND ri_sequence = ? AND ri_ingredientid = ?"
                    cursor.execute(query, (recipe_id, sequence, ingredient_id))
                    conn.commit()
                    QMessageBox.information(self, "Successo", "Ingrediente cancellato con successo.")
                    self.refresh_ingredients()  # Make sure to call the method here
            except Exception as e:
                QMessageBox.warning(self, "Cancellazione Fallita", f"Si è verificato un errore: {e}")

    def save_recipe(self):
        # Get the values from the input fields
        new_recipe_id = self.recipe_txt.text()
        new_description = self.descr_txt.text()
        new_line = self.line_combo.currentText()
        new_ptemp = self.ptemp_txt.text()
        new_omop = self.omop_txt.text()
        new_omop2 = self.omop2_txt.text()
        total_percentage = float(self.total_percentage_txt.text().replace(',', '.'))
        
        if total_percentage != 100:
            QMessageBox.warning(self, "Attenzione", "Somma della ricetta non raggiunge il 100%. Controllare il percentuale degli ingredienti.")
            return

        try:
            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()

                # If the recipe ID has changed, check if the new ID already exists
                if new_recipe_id != self.recipe_id:
                    cursor.execute("SELECT COUNT(*) FROM dbo.RecipeMaster WHERE rm_recipeid = ?", (new_recipe_id))
                    if cursor.fetchone()[0] > 0:
                        # New recipe ID already exists, show error message and return
                        QMessageBox.warning(self, "Errore", "ID ricetta già esistente. Scegliere un ID ricetta diverso.")
                        return

                # Perform SQL UPDATE operation for RecipeMaster table
                query = "UPDATE dbo.RecipeMaster SET [rm_recipeid] = ?, [rm_description] = ?, [rm_line] = ?, [rm_patemperature] = ?, [rm_omopress] = ?, [rm_omopress2] = ? WHERE [rm_recipeid] = ?"
                cursor.execute(query, (new_recipe_id, new_description, new_line, new_ptemp, new_omop, new_omop2, self.recipe_id))
                conn.commit()

                # Update RecipeIngredients table if recipe ID changed
                if new_recipe_id != self.recipe_id:
                    query = "UPDATE dbo.RecipeIngredients SET [ri_recipeid] = ? WHERE [ri_recipeid] = ?"
                    cursor.execute(query, (new_recipe_id, self.recipe_id))
                    conn.commit()

                # Optionally, update the instance variables if needed
                self.recipe_id = new_recipe_id
                self.descr_rec = new_description
                self.line_rec = new_line
                self.ptemp_rec = new_ptemp
                self.omop_rec = new_omop
                self.omop2_rec = new_omop2

                for row in range(self.ingredients_table.rowCount()):
                    recipe_id = self.ingredients_table.item(row, 0).text()
                    sequence = self.ingredients_table.item(row, 1).text()
                    ingredient_id = self.ingredients_table.item(row, 2).text()
                    new_percentage = self.ingredients_table.item(row, 5).text()

                    # Update statement for the ingredient
                    query = """UPDATE dbo.RecipeIngredients
                            SET [ri_percentage] = ?
                            WHERE [ri_recipeid] = ? AND [ri_sequence] = ? AND [ri_ingredientid] = ?"""

                    # Execute the update for this ingredient
                    cursor.execute(query, (new_percentage, recipe_id, sequence, ingredient_id))

                # Commit all ingredient updates
                conn.commit()

                # Inform the user about the successful update
                QMessageBox.information(self, "Successo", "Ricetta aggiornata con successo.")
                self.recipeUpdated.emit()  # Emit signal indicating recipe update
                self.accept()

        except Exception as e:
            # Handle exceptions for RecipeMaster table update
            QMessageBox.critical(self, "Errore", f"Si è verificato un errore nell'aggiornamento: {str(e)}")
            return

class AddIngredientDialog(QDialog):
    ingredientAdded = pyqtSignal()
    def __init__(self, recipe_id, parent=None, database_connection=None, parent_dialog=None):
        super().__init__(parent)
        self.parent_dialog = parent_dialog
        self.recipe_id = recipe_id
        self.setWindowTitle("Aggiungere Ingrediente")
        self.database_connection = database_connection  # Store the database connection
        self.setGeometry(100, 100, 400, 200)  # Replace with appropriate values
        layout = QVBoxLayout(self)
        self.original_ingredient_items = []

        # Filter + Combo box for ingredient selection
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Cerca Codice o Descrizione")
        self.filter_edit.textChanged.connect(self.filter_combo)
        self.ingr_label = QLabel("Ingrediente:")
        self.ingredient_combo = QComboBox()
        layout.addWidget(self.ingr_label)
        layout.addWidget(self.filter_edit)
        layout.addWidget(self.ingredient_combo)

        # Line edit for percentage input
        self.perc_label = QLabel("Percentuale:")
        self.percentage_edit = QLineEdit()
        layout.addWidget(self.perc_label)
        layout.addWidget(self.percentage_edit)

        # Buttons
        self.add_button = QPushButton("Aggiungere")
        self.cancel_button = QPushButton("Annullare")
        layout.addWidget(self.add_button)
        layout.addWidget(self.cancel_button)

        # Set layout and connect buttons
        self.setLayout(layout)
        self.add_button.clicked.connect(lambda: self.add_ingredient(self.recipe_id))
        self.cancel_button.clicked.connect(self.reject)

        # Fetch ingredients from the database
        self.populate_ingredient_combo()

    def populate_ingredient_combo(self):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT CAST(im_ingredientid AS VARCHAR) + ' - ' + im_code + ' - ' + im_description FROM dbo.IngredientMaster")
        for row in cursor.fetchall():
            item_text = row[0]
            self.original_ingredient_items.append(item_text)  # Store original items
            self.ingredient_combo.addItem(item_text)  # Add each mix tank description to the combo box
        conn.close()

    def filter_combo(self):
        filter_text = self.filter_edit.text().lower()  # Convert the filter text to lowercase for case-insensitive matching

        # Clear the combo box before adding filtered items
        self.ingredient_combo.clear()

        # Re-add items based on the filter text from the original items
        for item_text in self.original_ingredient_items:
            # Convert item text to lowercase and check if filter text is in it
            if filter_text in item_text.lower():
                self.ingredient_combo.addItem(item_text)

        # If after filtering no items are found, you might want to handle it (optional)
        if self.ingredient_combo.count() == 0:
            self.ingredient_combo.addItem("No items match your search")

    def load_ingredients(self, recipe_id):
        # Clear the table
        self.ingredients_table.setRowCount(0)

        # Load new data from the database
        query = """SELECT ri.ri_recipeid, ri.ri_sequence, ri.ri_ingredientid, im.im_code,
        im.im_description, ri.ri_percentage 
        FROM RecipeDB.dbo.RecipeIngredients ri
        JOIN RecipeDB.dbo.IngredientMaster im ON ri.ri_ingredientid = im.im_ingredientid
        WHERE ri.ri_recipeid = ? ORDER BY ri.ri_sequence ASC
        """
        rows = self.execute_query(query, (recipe_id,))
        self.populate_ingredients_table(rows)

    def populate_ingredients_table(self, rows):
        for row_index, row_data in enumerate(rows):
            self.ingredients_table.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                item = QTableWidgetItem(str(data))
                self.ingredients_table.setItem(row_index, col_index, item)

    def refresh_ingredients(self):
        self.load_ingredients(self.recipe_id)

    def add_ingredient(self, recipe_id):
        try:
            # Retrieve selected ingredient and percentage values
            ingredient_id_str = self.ingredient_combo.currentText().split(' - ')[0]
            ingredient_id = int(ingredient_id_str)
            percentage = self.percentage_edit.text()
            if ',' in percentage:
                percentage = percentage.replace(',', '.')

            # Define connection string
            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            
            # Establish database connection
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Check if the ingredient_id already exists for the given recipe_id
            cursor.execute("SELECT COUNT(*) FROM dbo.RecipeIngredients WHERE ri_recipeid = ? AND ri_ingredientid = ?", recipe_id, ingredient_id)
            if cursor.fetchone()[0] > 0:
                # Ingredient already exists, show warning
                QMessageBox.warning(self, "Attenzione", "Questo ingrediente esiste già nella ricetta.")
                return
            
            # Determine the ri_sequence as the highest existing sequence for the selected recipe
            cursor.execute("SELECT MAX(ri_sequence) FROM dbo.RecipeIngredients WHERE ri_recipeid = ?", recipe_id)
            max_sequence = cursor.fetchone()[0]
            ri_sequence = max_sequence + 1 if max_sequence is not None else 1
            
            # Insert the new record into RecipeIngredients
            insert_query = """
            INSERT INTO dbo.RecipeIngredients (ri_recipeid, ri_sequence, ri_ingredientid, ri_percentage, ri_stdpercentage)
            VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, (recipe_id, ri_sequence, ingredient_id, percentage, percentage))
            conn.commit()
            
            # Close the dialog
            self.accept()  # Close the dialog
            #QMessageBox.information(self, "Successo", "L'ingrediente è stato inserito.")
            self.parent_dialog.ingredientAdded.emit()
                
        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Si è verificato un errore: {traceback.format_exc()}")
        finally:
            # Ensure the database connection is closed even if an error occurs
            conn.close()

class IngredientModificationDialog(QDialog):
    def __init__(self, ingredient_code, current_percentage, on_accept_callback=None, parent=None):
        super().__init__(parent)
        self.on_accept_callback = on_accept_callback
        self.setWindowTitle("Modifica Ingrediente")

        layout = QVBoxLayout(self)

        # Ingredient Code (read-only if not meant to be edited)
        self.code_lbl = QLabel("Codice Ingrediente:")
        self.code_txt = QLineEdit(ingredient_code)
        self.code_txt.setReadOnly(True)  # Make read-only if the code should not be changed

        # Current Percentage
        self.percentage_lbl = QLabel("Percentuale Attuale:")
        self.percentage_txt = QLineEdit(current_percentage)

        layout.addWidget(self.code_lbl)
        layout.addWidget(self.code_txt)
        layout.addWidget(self.percentage_lbl)
        layout.addWidget(self.percentage_txt)

        # OK and Cancel buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_values(self):
        return self.code_txt.text(), self.percentage_txt.text()
    
    def accept(self):
        if self.on_accept_callback:
            new_percentage = self.percentage_txt.text()
            self.on_accept_callback(new_percentage)
        super().accept()

class DeleteRecipeDialog(QDialog):
    recipeDeleted = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cancella Ricetta")
        self.setGeometry(100, 100, 300, 200)  # Adjust size as needed

        layout = QVBoxLayout(self)

        # Recipe selection combo box
        self.recipe_combo = QComboBox(self)
        layout.addWidget(self.recipe_combo)

        # Delete button
        self.delete_button = QPushButton("Cancella", self)
        layout.addWidget(self.delete_button)

        # Populate the combo box with recipe IDs
        self.populate_recipe_combo()

        # Connect the delete button
        self.delete_button.clicked.connect(self.delete_recipe)

    def populate_recipe_combo(self):
        # Connect to the database
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT rm_recipeid FROM RecipeDB.dbo.RecipeMaster")
        for row in cursor.fetchall():
            self.recipe_combo.addItem(str(row[0]))
        conn.close()

    def delete_recipe(self):
        selected_recipe = self.recipe_combo.currentText()
        reply = QMessageBox.question(self, 'Conferma Cancellamento', 
                                     f"Sei sicuro di voler cancellare la ricetta {selected_recipe}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            query = "DELETE FROM RecipeDB.dbo.RecipeMaster WHERE rm_recipeid = ?"
            cursor.execute(query, (selected_recipe,))
            conn.commit()
            conn.close()
            self.recipeDeleted.emit()
            self.accept()

class CommIngrDialog(QDialog):
    def __init__(self, recipe_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dove viene utilizzato?")
        self.resize(400, 300)

        layout = QVBoxLayout()
        self.setLayout(layout)

        table_widget = QTableWidget()
        table_widget.setColumnCount(2)
        table_widget.setHorizontalHeaderLabels(["ID Ricetta", "Descrizione"])
        table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        for row_index, row_data in enumerate(recipe_data):
            table_widget.insertRow(row_index)
            for col_index, value in enumerate(row_data):
                table_widget.setItem(row_index, col_index, QTableWidgetItem(str(value)))
        
        layout.addWidget(table_widget)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

#--------------------------------------------------------------------END OF RECIPE GLOBAL CLASSES
#--------------------------------------------------------------------BEGIN OF SCHEDULE GLOBAL CLASSES
            
def get_empty_positions():
        client = Client(f"opc.tcp://{ip}:4840")
        client.session_timeout = 30000
        client.connect()
        
        empty_positions = []  # Initialize an empty list to store the empty positions
        
        for next_position in range(1, 11):  # Iterate from slot 1 to slot 10
            nodest = f'ns=3;s="RecipeManagement"."Lista"[{next_position}]."Codice"'
            value = client.get_node(nodest).get_value()
            
            if value == "":
                empty_positions.append(next_position)  # Append empty position to the list
        
        # Disconnect the client outside the loop when done
        client.disconnect()
        
        return empty_positions  # Return the list of empty positions

def monitor_and_update():
    while True:
        try:
            # Connect to the OPC server
            client = Client(f"opc.tcp://{ip}:4840")
            client.session_timeout = 30000
            client.connect()

            # Read OPC tags and monitor changes

            # Update SQL table based on OPC data

            # Disconnect from OPC server
            client.disconnect()

            # Sleep for 15 minutes (900 seconds)
            time.sleep(900)

        except Exception as e:
            # Handle exceptions here, e.g., log errors
            print(f"Error: {str(e)}")

#--------------------------------------------------------------------END OF SCHEDULE GLOBAL CLASSES
#--------------------------------------------------------------------BEGIN OF MAIN FUNCTIONS/HMI
            
class SQLTableWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        splash = SplashScreen()
        splash.show()
        QApplication.processEvents()

        self.authenticated = False

        time.sleep(5)

        while not self.authenticated:
            # Create a login dialog and show it
            splash.close()
            login_dialog = LoginDialog(self)
            if login_dialog.exec_() == QDialog.Accepted:
                username, password = login_dialog.get_credentials()
                self.authenticated = self.authenticate(username, password)
                if not self.authenticated:
                    QMessageBox.warning(self, "Accesso non riuscito", "L'username o password non è corretta")
            else:
                self.close()  # Close the main window if the login dialog is canceled

        # If authentication is successful, proceed with setting up the UI
        self.setup_ui()

    def authenticate(self, username, password):
        return username == "man" and password == "123man"
    
    @pyqtSlot(bool)
    def onToggle(self, checked):
        # This slot is called when the group box is checked or unchecked.
        # You can add logic here if you need to do something when it's toggled.
        self.groupBox.setFlat(not checked)

    @pyqtSlot(bool)
    def onToggleD(self, checked):
        # This slot is called when the group box is checked or unchecked.
        # You can add logic here if you need to do something when it's toggled.
        self.groupDBox.setFlat(not checked)

    def tab_changed(self, index):
        # Check if the newly selected tab is password protected
        tab_name = self.tab_widget.tabText(index)
        if tab_name in self.protected_tabs:
            password, ok = QInputDialog.getText(self, 'Password Richiesta',
                                                f'Inserire password per accedere a {tab_name}:',
                                                QLineEdit.Password)  # Use QLineEdit.Password here
            if ok:
                if self.check_password(password):
                    # If the password is correct, allow the tab change
                    return
                else:
                    # If the password is incorrect, show an error message
                    QMessageBox.warning(self, 'Accesso Negato', 'La password non è corretta.')
            else:
                # If the user clicked "Cancel," do nothing or handle it differently
                pass
            # If the password is incorrect or "Cancel" is clicked, revert to the first tab
            self.tab_widget.setCurrentIndex(0)

        if tab_name == "Ingredienti": #bingo
            self.refresh_table()
        elif tab_name == "Ricette":
            self.r_refresh_table()
        elif tab_name == "Programma":
            self.populate_recipe_combos()
            self.refresh_schedule_list()
        elif tab_name == "Linea D":
            self.populate_recipe_combosD()
            self.refresh_schedule_listD()
        elif tab_name == "Reports":
            self.refresh_report_tab()
        else:
            pass

    def check_password(self, password):
        # Placeholder password check function
        return password == "accos"

    def setup_ui(self):
        # Set up the main window
        self.setWindowTitle("Froneri Recipe Manager - AIMA Powered - by Automate SRL")
        self.setGeometry(100, 100, 1750, 800)
        self.setWindowState(self.windowState() | Qt.WindowFullScreen)
        icon_path = "icon.ico"
        self.setWindowIcon(QIcon(icon_path))

        # Status bar
        status_bar = self.statusBar()
        ## Add QLabel widgets with the corresponding QPixmap icons
        #self.database_status_label = QLabel()
        #self.database_status_label.setPixmap(self.red_pixmap)  # Assuming red_pixmap is defined elsewhere
        #status_bar.addWidget(self.database_status_label)
#
        #self.plc_status_label = QLabel()
        #self.plc_status_label.setPixmap(self.red_pixmap)  # Assuming red_pixmap is defined elsewhere
        #status_bar.addWidget(self.plc_status_label)
#
        #self.rep_status_label = QLabel()
        #self.rep_status_label.setPixmap(self.red_pixmap)  # Assuming red_pixmap is defined elsewhere
        #status_bar.addWidget(self.rep_status_label)
        
        exit_button = QPushButton("Chiude")
        exit_button.clicked.connect(self.close)
        #config_button = QPushButton("Configuration")
        #config_button.clicked.connect(self.configuration_param)
        #status_bar.addPermanentWidget(config_button)
        status_bar.addPermanentWidget(exit_button)

        # Main widget and layout
        main_widget = QWidget()  # This will be the central widget
        main_layout = QVBoxLayout(main_widget)  # Main layout

        # Create a tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)  # Add tab widget to the main layout

#----------------------------------------------------END MAIN HMI TAB------------------------------------------------------------
#---------------------------------------------------INGREDIENT HMI TAB--------------------------------------------------------------
        
        # Create a tab for Ingredients
        ingredients_tab = QWidget()
        #tab_widget.addTab(ingredients_tab, "Ingredienti")
        self.add_edit_dialog = AddEditDialog(self)

        # Create a layout for the Ingredients tab
        ingredients_layout = QVBoxLayout(ingredients_tab)

        # Create a table widget for Ingredients tab
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(7)  # Set the number of columns
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.setSortingEnabled(True)

        # Create a horizontal layout for the table and buttons
        table_and_buttons_layout = QHBoxLayout()
        ingredients_layout.addLayout(table_and_buttons_layout)

        # Add the table widget to the layout
        table_and_buttons_layout.addWidget(self.tableWidget, 1)  # Let the table take up the available space

        # Create a container widget for the buttons
        buttons_container = QWidget()
        buttons_layout = QVBoxLayout(buttons_container)  # Buttons layout
        buttons_layout.setAlignment(Qt.AlignTop)  # Align buttons to the top

        # Create buttons for ADD and DELETE
        add_button = QPushButton("Aggiunge Ingredienti")
        modify_button = QPushButton("Modifica Ingredienti")
        delete_button = QPushButton("Cancella Selezione")
        copy_button = QPushButton("Copia Selezione")
        show_recipes_button = QPushButton("Dove viene utilizzato?")
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Cerca Codice o Descrizione")
        self.filter_edit.textChanged.connect(self.filter_table)

        # Add buttons and filter to the buttons layout
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(modify_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(copy_button)
        buttons_layout.addWidget(show_recipes_button)
        buttons_layout.addWidget(self.filter_edit)

        # Add the buttons container to the layout
        table_and_buttons_layout.addWidget(buttons_container)

        # Connect buttons to their respective functions
        add_button.clicked.connect(self.open_add_dialog)
        modify_button.clicked.connect(self.open_modify_dialog)
        delete_button.clicked.connect(self.open_delete_dialog)
        copy_button.clicked.connect(self.open_copy_dialog)
        show_recipes_button.clicked.connect(self.show_recipes_dialog)

        # Connect to the SQL Server
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)

        # Retrieve data from the database
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                [im_code] as Codice,
                [im_description] as Descrizione,
                aa.ia_description AS [Area],
                CASE WHEN [im_typeid] = 1 THEN 'Automatic' ELSE 'Manual' END as [Auto/Manuale],
                irt.irt_description AS [Tipo Rework],
                [im_storage] as [ID Serbatoio],
                [im_storagename] as [Nome Serbatoio]
            FROM
                [RecipeDB].[dbo].[IngredientMaster] im
            LEFT JOIN
                [dbo].[IngredientArea] aa ON im.im_areaid = aa.ia_areaid
            LEFT JOIN
                [dbo].[IngredientReworkType] irt ON im.im_reworktypeid = irt.irt_reworktypeid
            ORDER BY [im_code] ASC
        """)

        # Get column names
        column_names = [column[0] for column in cursor.description]

        # Set the main widget as the central widget of the window
        self.setCentralWidget(main_widget)
        
        # Set the column count and labels
        self.tableWidget.setColumnCount(len(column_names))
        self.tableWidget.setHorizontalHeaderLabels(column_names)

        # Populate the table with data
        row_index = 0
        for row in cursor.fetchall():
            self.tableWidget.insertRow(row_index)
            for col_index, value in enumerate(row):
                self.tableWidget.setItem(row_index, col_index, QTableWidgetItem(str(value)))
            row_index += 1

        # Close the database connection
        conn.close()
        self.add_edit_dialog.refresh_signal.connect(self.refresh_table)
#-------------------------------------------------END OF INGREDIENT HMI TAB-------------------------------------------
#-----------------------------------------------------RECIPE HMI TAB----------------------------------------------------------

        # Create a tab for Recipes
        recipes_tab = QWidget()
        #tab_widget.addTab(recipes_tab, "Ricette")
        
        # Create a layout for the Recipes tab
        recipes_layout = QVBoxLayout(recipes_tab)
        
        # Create a table widget for Recipes tab
        self.recipesTableWidget = QTableWidget()
        self.recipesTableWidget.setColumnCount(0)  # Initially, no columns
        self.recipesTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.recipesTableWidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.recipesTableWidget.setSelectionMode(QTableWidget.SingleSelection)
        self.recipesTableWidget.setSortingEnabled(True)
        recipes_layout.addWidget(self.recipesTableWidget)
        
        # Create a horizontal layout for the table and buttons
        rtable_and_buttons_layout = QHBoxLayout()
        recipes_layout.addLayout(rtable_and_buttons_layout)
        
        # Add the table widget to the layout
        rtable_and_buttons_layout.addWidget(self.recipesTableWidget, 1)  # Let the table take up the available space

        # Create a container widget for the buttons
        rbuttons_container = QWidget()
        rbuttons_layout = QVBoxLayout(rbuttons_container)  # Buttons layout
        rbuttons_layout.setAlignment(Qt.AlignTop)  # Align buttons to the top

        # Create buttons for ADD and DELETE
        radd_button = QPushButton("Aggiunge Ricetta")
        redit_button = QPushButton("Modifica Ricetta")
        rdelete_button = QPushButton("Cancella Selezione")
        rcopy_button = QPushButton("Copia Selezione")
        self.rfilter_edit = QLineEdit()
        self.rfilter_edit.setPlaceholderText("Cerca Codice o Descrizione")
        self.rfilter_edit.textChanged.connect(self.rfilter_table)

        # Add buttons and filter to the buttons layout
        rbuttons_layout.addWidget(radd_button)
        rbuttons_layout.addWidget(redit_button)
        rbuttons_layout.addWidget(rdelete_button)
        rbuttons_layout.addWidget(rcopy_button)
        rbuttons_layout.addWidget(self.rfilter_edit)

        # Add the buttons container to the layout
        rtable_and_buttons_layout.addWidget(rbuttons_container)

        # Connect buttons to their respective functions
        radd_button.clicked.connect(self.ropen_add_dialog)
        redit_button.clicked.connect(self.open_edit_recipe_ingredients_dialog)
        rdelete_button.clicked.connect(self.open_delete_recipe_dialog)
        rcopy_button.clicked.connect(self.open_copyrecipe_dialog)

        # Connect to the SQL Server
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)

        # Retrieve data from the database
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                [rm_recipeid] as [Codice Ricetta],
                [rm_description] as Descrizione,
                [rm_line] as [Linea di Produzione],
                [rm_patemperature] as [Temp. Pasteur.],
                [rm_holdingtime] as [Holding Time],
                [rm_omopress] as [Pressione Omo.],
                [rm_omospeed] as [Velocità Omo.]
            FROM
                [RecipeDB].[dbo].[RecipeMaster]
            ORDER BY [rm_recipeid] ASC
        """)

        # Get column names
        column_names = [column[0] for column in cursor.description]

        # Set the column count and labels for recipesTableWidget
        self.recipesTableWidget.setColumnCount(len(column_names))
        self.recipesTableWidget.setHorizontalHeaderLabels(column_names)

        # Populate the table with data
        row_index = 0
        for row in cursor.fetchall():
            self.recipesTableWidget.insertRow(row_index)
            for col_index, value in enumerate(row):
                self.recipesTableWidget.setItem(row_index, col_index, QTableWidgetItem(str(value)))
            row_index += 1

        # Close the database connection
        conn.close()

#--------------------------------------------END OF RECIPE HMI---------------------------------------------------
#--------------------------------------------SCHEDULE PROD HMI---------------------------------------------------
        # Create a tab for Scheduling
        schedule_tab = QWidget()
        #tab_widget.addTab(schedule_tab, "Programma")

        # Create a horizontal layout to hold both the form and the table
        horizontal_layout = QVBoxLayout(schedule_tab)

        # Create a layout for the Recipes
        schedule_layout = QVBoxLayout(schedule_tab)
        schedule_container = QWidget()
        schedule_container.setLayout(schedule_layout)
        form_split_layout = QHBoxLayout()
        sch_form_layout = QVBoxLayout()
        rcp_layout = QHBoxLayout()
        qtymixagewtr_layout = QHBoxLayout()
        rwkcol_layout = QHBoxLayout()
        adv_layout = QHBoxLayout()
        ingrlist_layout = QVBoxLayout()
        p04_parameters_layout = QHBoxLayout()
        pasteurizer_parameters_layout = QHBoxLayout()
        pasteurizer_parameters_layout2 = QHBoxLayout()
        pasteurizer_parameters_layout3 = QHBoxLayout()
        blender_parameters_layout = QHBoxLayout()
        blender_parameters_layout2 = QHBoxLayout()
        blender_parameters_layout3 = QHBoxLayout()
        sch_button_layout = QHBoxLayout()
        sch_button_layout.setAlignment(Qt.AlignCenter)
        sch_button_layoutb = QHBoxLayout()
        sch_button_layoutb.setAlignment(Qt.AlignCenter)

        #Line and WO field
        self.workorder_lbl = QLabel("WorkOrder:", self)
        self.workorder_txt = QLineEdit()
        self.line_label = QLabel("Linea:", self)
        self.line_combo = QComboBox()
        self.line_combo.addItems(["B", "C"])
        self.line_combo.currentTextChanged.connect(self.populate_recipe_combos)
        rcp_layout.addWidget(self.workorder_lbl)
        rcp_layout.addWidget(self.workorder_txt)
        rcp_layout.addWidget(self.line_label)
        rcp_layout.addWidget(self.line_combo)
        #Recipe fields
        self.recipe_no_label = QLabel("Cod.Ricetta:", self)
        self.recipe_name_label = QLabel("Nome:", self)
        self.sfilter_edit = QLineEdit()
        self.sfilter_edit.setMinimumWidth(100)
        self.sfilter_edit.setMaximumWidth(250)
        self.sfilter_edit.setPlaceholderText("Cerca Codice")
        self.sfilter_edit.textChanged.connect(self.sfilter_combo)
        self.recipe_no_combo = QComboBox()
        self.recipe_name_combo = QComboBox()
        self.original_recipe_items = []
        self.populate_recipe_combos()
        rcp_layout.addWidget(self.recipe_no_label)
        rcp_layout.addWidget(self.sfilter_edit)
        rcp_layout.addWidget(self.recipe_no_combo)
        rcp_layout.addWidget(self.recipe_name_label)
        rcp_layout.addWidget(self.recipe_name_combo)
        sch_form_layout.addLayout(rcp_layout)
        self.recipe_no_combo.currentIndexChanged.connect(self.on_recipe_no_combo_changed)
        self.recipe_name_combo.currentIndexChanged.connect(self.on_recipe_name_combo_changed)
        self.sfilter_edit.returnPressed.connect(self.load_ingredients)
        #self.recipe_no_combo.currentIndexChanged.connect(self.load_ingredients)
        #Quantity field
        self.quantity_label = QLabel("Quantità:", self)
        self.quantity_field = QLineEdit()
        self.quantity_field.setPlaceholderText("500 - 32000Kg")
        self.quantity_field.textChanged.connect(self.calculate_target_quantities)
        qtymixagewtr_layout.addWidget(self.quantity_label)
        qtymixagewtr_layout.addWidget(self.quantity_field)
        #Mix and Age Tanks Fields
        self.mix_tank_label = QLabel("Blender:",self)
        self.mix_tank_combo = QComboBox()
        self.age_tank_label = QLabel("Serbatoio:",self)
        self.age_tank_combo = QComboBox()
        # Implement functions to populate these combo boxes
        self.populate_mix_tank_combo()
        self.populate_age_tank_combo()
        qtymixagewtr_layout.addWidget(self.mix_tank_label)
        qtymixagewtr_layout.addWidget(self.mix_tank_combo)
        qtymixagewtr_layout.addWidget(self.age_tank_label)
        qtymixagewtr_layout.addWidget(self.age_tank_combo)
        #Water % 
        self.water_percent_label = QLabel("Acqua %:",self)
        self.water_percent_field = QLineEdit()
        self.water_percent_field.setPlaceholderText("0 - 100%")
        qtymixagewtr_layout.addWidget(self.water_percent_label)
        qtymixagewtr_layout.addWidget(self.water_percent_field)
        sch_form_layout.addLayout(qtymixagewtr_layout)
        #Rework Radios
        self.rework_label = QLabel("Rework:",self)
        self.rework_yes_radio = QRadioButton("Yes")
        self.rework_no_radio = QRadioButton("No")
        self.rework_no_radio.setChecked(True)
        rwkcol_layout.addWidget(self.rework_label)
        rwkcol_layout.addWidget(self.rework_yes_radio)
        rwkcol_layout.addWidget(self.rework_no_radio)
        
        #Cooling field
        self.cooling_temp_label = QLabel("Temp. Raffredamento:",self)
        self.cooling_temp_field = QLineEdit()
        self.cooling_temp_field.setPlaceholderText("1 - 20 °C")
        rwkcol_layout.addWidget(self.cooling_temp_label)
        rwkcol_layout.addWidget(self.cooling_temp_field)
        sch_form_layout.addLayout(rwkcol_layout)
        sch_form_layout.addLayout(adv_layout)
        sch_form_layout.setAlignment(Qt.AlignTop)

        #Add buttons to the buttons layout
        self.sch_add_button = QPushButton("Aggiungere alla programmazione")
        sch_reset_button = QPushButton("Resetta Modulo")
        sch_delete_button = QPushButton("Cancella dalla programmazione")
        sch_transfer_button = QPushButton("Trasferire al PLC")
        sch_refresh_button = QPushButton("Aggiorna Lista Programmazione")
        sch_up_button = QPushButton("Sposta WorkOrder su")
        sch_down_button = QPushButton("Sposta WorkOrder giù")
        sch_report_button = QPushButton("Genera Pre-Prod Report")
        sch_button_layout.addWidget(sch_report_button)
        sch_button_layout.addWidget(self.sch_add_button)
        self.sch_add_button.clicked.connect(self.add_to_schedule)
        sch_report_button.clicked.connect(self.generate_plan_report)
        sch_button_layoutb.addWidget(sch_up_button)
        sch_up_button.clicked.connect(self.up_selected_schedule)
        sch_button_layoutb.addWidget(sch_down_button)
        sch_down_button.clicked.connect(self.down_selected_schedule)
        sch_button_layoutb.addWidget(sch_delete_button)
        sch_delete_button.clicked.connect(self.delete_selected_schedule)
        sch_button_layoutb.addWidget(sch_transfer_button)
        sch_transfer_button.clicked.connect(self.transfer_to_plc)
        sch_button_layout.addWidget(sch_refresh_button)
        sch_refresh_button.clicked.connect(self.refresh_schedule_list)

        # Create a group box
        self.groupBox = QGroupBox("Parametri Avanzati")
        self.groupBox.setCheckable(True)
        self.groupBox.setChecked(False) # Start unchecked (collapsed)
        self.groupBox.toggled.connect(self.onToggle) # Connect signal to slot

        # Create sections with parameters
        parameters_layout = QVBoxLayout()
        self.groupBox.setLayout(parameters_layout)
        
        # Section "P04 Parameters"
        self.p04_label1 = QLabel("Tempo Ag. Slow P04:", self)
        self.p04_field1 = QLineEdit("10000.0")
        self.p04_label2 = QLabel("Tempo Ag. Fast P04:", self)
        self.p04_field2 = QLineEdit("10000.0")
        self.p04_label3 = QLabel("Tempo Martelli P04:", self)
        self.p04_field3 = QLineEdit("330000.0")
        p04_parameters_layout.addWidget(self.p04_label1)
        p04_parameters_layout.addWidget(self.p04_field1)
        p04_parameters_layout.addWidget(self.p04_label2)
        p04_parameters_layout.addWidget(self.p04_field2)
        p04_parameters_layout.addWidget(self.p04_label3)
        p04_parameters_layout.addWidget(self.p04_field3)
        
        # Section "Pasteurizer Parameters"
        self.past_label1 = QLabel("Past. Temp.:", self) #su
        self.past_field1 = QLineEdit()
        self.past_field1.setPlaceholderText("88.0")
        self.past_label2 = QLabel("Past. ΔTemp.:", self)
        self.past_field2 = QLineEdit("4.0")
        #self.past_label3 = QLabel("Detraction Temp.:", self)
        #self.past_field3 = QLineEdit("5.0")
        self.past_label4 = QLabel("Abbatt. ΔTemp.:", self)
        self.past_field4 = QLineEdit("3.0")
        adv_layout.addWidget(self.past_label1)
        adv_layout.addWidget(self.past_field1)
        pasteurizer_parameters_layout.addWidget(self.past_label2)
        pasteurizer_parameters_layout.addWidget(self.past_field2)
        #pasteurizer_parameters_layout.addWidget(self.past_label3)
        #pasteurizer_parameters_layout.addWidget(self.past_field3)
        pasteurizer_parameters_layout.addWidget(self.past_label4)
        pasteurizer_parameters_layout.addWidget(self.past_field4)

        self.past_label5 = QLabel("Temp. Fine Prod.:", self)
        self.past_field5 = QLineEdit("30.0")
        self.past_label6 = QLabel("Vol. Fine Prod.:", self)
        self.past_field6 = QLineEdit("300.0")
        self.past_label7 = QLabel("Liv. Acqua BTD:", self)
        self.past_field7 = QLineEdit("42.0")
        self.past_label8 = QLabel("Liv. Purea:", self)
        self.past_field8 = QLineEdit("0.0")
        pasteurizer_parameters_layout2.addWidget(self.past_label5)
        pasteurizer_parameters_layout2.addWidget(self.past_field5)
        pasteurizer_parameters_layout2.addWidget(self.past_label6)
        pasteurizer_parameters_layout2.addWidget(self.past_field6)
        pasteurizer_parameters_layout2.addWidget(self.past_label7)
        pasteurizer_parameters_layout2.addWidget(self.past_field7)
        pasteurizer_parameters_layout2.addWidget(self.past_label8)
        pasteurizer_parameters_layout2.addWidget(self.past_field8)

        self.past_label9 = QLabel("Liv. Omog.:", self)
        self.past_field9 = QLineEdit("300.0")
        self.past_label10 = QLabel("Press. Omo.:", self) #su
        self.past_field10 = QLineEdit()
        self.past_field10.setPlaceholderText("200.0")
        self.past_label11 = QLabel("Press. Omog. 2:", self)
        self.past_field11 = QLineEdit("0.0")
        self.past_label12 = QLabel("Vel. Omog.:", self) #su
        self.past_field12 = QLineEdit()
        self.past_field12.setPlaceholderText("100.0")
        pasteurizer_parameters_layout3.addWidget(self.past_label9)
        pasteurizer_parameters_layout3.addWidget(self.past_field9)
        adv_layout.addWidget(self.past_label10)
        adv_layout.addWidget(self.past_field10)
        pasteurizer_parameters_layout3.addWidget(self.past_label11)
        pasteurizer_parameters_layout3.addWidget(self.past_field11)
        adv_layout.addWidget(self.past_label12)
        adv_layout.addWidget(self.past_field12)
        
        # Section "Blender Parameters"
        self.blen_label1 = QLabel("Temp. Blender:", self)
        self.blen_field1 = QLineEdit("55.0")
        self.blen_label2 = QLabel("ΔTemp. Blender:", self)
        self.blen_field2 = QLineEdit("5.0")
        self.blen_label3 = QLabel("Tempo Maturazzione:", self)
        self.blen_field3 = QLineEdit("0.0")
        blender_parameters_layout.addWidget(self.blen_label1)
        blender_parameters_layout.addWidget(self.blen_field1)
        blender_parameters_layout.addWidget(self.blen_label2)
        blender_parameters_layout.addWidget(self.blen_field2)
        blender_parameters_layout.addWidget(self.blen_label3)
        blender_parameters_layout.addWidget(self.blen_field3)

        self.blen_label4 = QLabel("Holding Time (min.):", self) #su
        self.blen_field4 = QLineEdit()
        self.blen_field4.setPlaceholderText("20")
        self.blen_label5 = QLabel("Pausa Carico Polveri(ms):", self)
        self.blen_field5 = QLineEdit("5000")
        self.blen_label6 = QLabel("Lavoro Carico Polveri(ms):", self)
        self.blen_field6 = QLineEdit("5000")
        adv_layout.addWidget(self.blen_label4)
        adv_layout.addWidget(self.blen_field4)
        blender_parameters_layout2.addWidget(self.blen_label5)
        blender_parameters_layout2.addWidget(self.blen_field5)
        blender_parameters_layout2.addWidget(self.blen_label6)
        blender_parameters_layout2.addWidget(self.blen_field6)

        self.blen_label7 = QLabel("Vel. Agitatore Z:", self) #traduzione
        self.blen_field7 = QLineEdit("0.0")
        self.blen_label8 = QLabel("Vel. Agitatore G:", self)
        self.blen_field8 = QLineEdit("0.0")
        self.blen_label9 = QLabel("Vel. Agitatore M:", self)
        self.blen_field9 = QLineEdit("0.0")
        blender_parameters_layout3.addWidget(self.blen_label7)
        blender_parameters_layout3.addWidget(self.blen_field7)
        blender_parameters_layout3.addWidget(self.blen_label8)
        blender_parameters_layout3.addWidget(self.blen_field8)
        blender_parameters_layout3.addWidget(self.blen_label9)
        blender_parameters_layout3.addWidget(self.blen_field9)
        
        # Button to toggle edit mode
        edit_button = QLabel("Parametri fissi di produzioni - Non cambiare")

        # Add the edit button to the layout
        parameters_layout.addWidget(edit_button)
        
        # Add sections to the main parameters layout
        parameters_layout.addLayout(p04_parameters_layout)
        parameters_layout.addLayout(pasteurizer_parameters_layout)
        parameters_layout.addLayout(pasteurizer_parameters_layout2)
        parameters_layout.addLayout(pasteurizer_parameters_layout3)
        parameters_layout.addLayout(blender_parameters_layout)
        parameters_layout.addLayout(blender_parameters_layout2)
        parameters_layout.addLayout(blender_parameters_layout3)

        #Split form from Table and Buttons
        spacer = QSpacerItem(20, 50, QSizePolicy.Minimum, QSizePolicy.Fixed)
        sch_form_layout.addSpacerItem(spacer)
        sch_form_layout.addWidget(self.groupBox)
        #sch_form_layout.addLayout(parameters_layout)
        form_split_layout.addLayout(sch_form_layout)
        
        # Ingredient table
        self.ingredients_table_label = QLabel("Lista Ingredienti:",self)
        self.ingredients_table = QTableWidget()
        self.ingredients_table.setMinimumWidth(900)
        self.ingredients_table.setColumnCount(6)  # Assuming 5 columns
        self.ingredients_table.setHorizontalHeaderLabels(["Ricetta", "Tipo", "Codice", "Descrizione", "%", "Quantità(Kg)"])
        self.ingredients_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ingredients_table.horizontalHeader().setSectionResizeMode(5,QHeaderView.Stretch)
        self.ingredients_table.resizeColumnsToContents()
        ingrlist_layout.addWidget(self.ingredients_table_label)
        ingrlist_layout.addWidget(self.ingredients_table)
        form_split_layout.addLayout(ingrlist_layout)
        schedule_layout.addLayout(form_split_layout)
        schedule_layout.addLayout(sch_button_layout)
                                 
        # Scheduled WO Table
        schedule_table_label = QLabel("Lista Programmazione:", self)
        self.schedule_table = QTableWidget()
        schedule_table_layout = QVBoxLayout()
        self.schedule_table.resizeColumnsToContents()
        schedule_layout.addWidget(schedule_table_label)
        schedule_layout.addWidget(self.schedule_table)
        schedule_layout.addLayout(sch_button_layoutb)
        
        # Add the form layout and the table to the horizontal layout
        horizontal_layout.addWidget(schedule_container)
        horizontal_layout.addLayout(schedule_table_layout)

        # Set the main layout of the tab to be the horizontal layout
        schedule_tab.setLayout(schedule_layout)
        self.populate_schedule_table()

#--------------------------------------------END OF SCHEDULE HMI----------------------------------------------------
#--------------------------------------------SCHEDULE PROD LINEA D HMI---------------------------------------------------
        # Create a tab for Scheduling
        scheduleD_tab = QWidget()
        #tab_widget.addTab(schedule_tab, "Programma")

        # Create a horizontal layout to hold both the form and the table
        horizontalD_layout = QVBoxLayout(scheduleD_tab)

        # Create a layout for the Recipes
        scheduleD_layout = QVBoxLayout(scheduleD_tab)
        scheduleD_container = QWidget()
        scheduleD_container.setLayout(scheduleD_layout)
        formD_split_layout = QHBoxLayout()
        schD_form_layout = QVBoxLayout()
        rcpD_layout = QHBoxLayout()
        qtymixagewtrD_layout = QHBoxLayout()
        rwkcolD_layout = QHBoxLayout()
        advD_layout = QHBoxLayout()
        ingrlistD_layout = QVBoxLayout()
        p04D_parameters_layout = QHBoxLayout()
        pasteurizerD_parameters_layout = QHBoxLayout()
        pasteurizerD_parameters_layout2 = QHBoxLayout()
        pasteurizerD_parameters_layout3 = QHBoxLayout()
        blenderD_parameters_layout = QHBoxLayout()
        blenderD_parameters_layout2 = QHBoxLayout()
        blenderD_parameters_layout3 = QHBoxLayout()
        schD_button_layout = QHBoxLayout()
        schD_button_layout.setAlignment(Qt.AlignCenter)
        schD_button_layoutb = QHBoxLayout()
        schD_button_layoutb.setAlignment(Qt.AlignCenter)

        #Line and WO field
        self.workorderD_lbl = QLabel("WorkOrder:", self)
        self.workorderD_txt = QLineEdit()
        self.lineD_label = QLabel("Linea:", self)
        self.lineD_combo = QComboBox()
        self.lineD_combo.addItems(["D"])
        self.lineD_combo.currentTextChanged.connect(self.populate_recipe_combosD)
        rcpD_layout.addWidget(self.workorderD_lbl)
        rcpD_layout.addWidget(self.workorderD_txt)
        rcpD_layout.addWidget(self.lineD_label)
        rcpD_layout.addWidget(self.lineD_combo)
        #Recipe fields
        self.recipeD_no_label = QLabel("Cod.Ricetta:", self)
        self.recipeD_name_label = QLabel("Nome:", self)
        self.sfilterD_edit = QLineEdit()
        self.sfilterD_edit.setMinimumWidth(100)
        self.sfilterD_edit.setMaximumWidth(250)
        self.sfilterD_edit.setPlaceholderText("Cerca Codice")
        self.sfilterD_edit.textChanged.connect(self.sfilter_comboD)
        self.recipeD_no_combo = QComboBox()
        self.recipeD_name_combo = QComboBox()
        self.originalD_recipe_items = []
        self.populate_recipe_combosD()
        rcpD_layout.addWidget(self.recipeD_no_label)
        rcpD_layout.addWidget(self.sfilterD_edit)
        rcpD_layout.addWidget(self.recipeD_no_combo)
        rcpD_layout.addWidget(self.recipeD_name_label)
        rcpD_layout.addWidget(self.recipeD_name_combo)
        schD_form_layout.addLayout(rcpD_layout)
        self.recipeD_no_combo.currentIndexChanged.connect(self.on_recipe_no_combo_changedD)
        self.recipeD_name_combo.currentIndexChanged.connect(self.on_recipe_name_combo_changedD)
        self.sfilterD_edit.returnPressed.connect(self.load_ingredientsD)
        #self.recipe_no_combo.currentIndexChanged.connect(self.load_ingredients)
        #Quantity field
        self.quantityD_label = QLabel("Quantità:", self)
        self.quantityD_field = QLineEdit()
        self.quantityD_field.setPlaceholderText("500 - 32000Kg")
        self.quantityD_field.textChanged.connect(self.calculate_target_quantitiesD)
        qtymixagewtrD_layout.addWidget(self.quantityD_label)
        qtymixagewtrD_layout.addWidget(self.quantityD_field)
        #Quantity Sotto Batch field
        self.quantitysbD_label = QLabel("Qtà Sotto Batch:", self)
        self.quantitysbD_field = QLineEdit()
        self.quantitysbD_field.setPlaceholderText("500 - 32000Kg")
        qtymixagewtrD_layout.addWidget(self.quantitysbD_label)
        qtymixagewtrD_layout.addWidget(self.quantitysbD_field)
        #Mix and Age Tanks Fields
        self.mixD_tank_label = QLabel("Blender:",self)
        self.mixD_tank_combo = QComboBox()
        self.ageD_tank_label = QLabel("Serbatoio:",self)
        self.ageD_tank_combo = QComboBox()
        # Implement functions to populate these combo boxes
        self.populate_mix_tank_comboD()
        self.populate_age_tank_comboD()
        qtymixagewtrD_layout.addWidget(self.mixD_tank_label)
        qtymixagewtrD_layout.addWidget(self.mixD_tank_combo)
        qtymixagewtrD_layout.addWidget(self.ageD_tank_label)
        qtymixagewtrD_layout.addWidget(self.ageD_tank_combo)
        schD_form_layout.addLayout(qtymixagewtrD_layout)
        
        #Water % 
        self.waterD_percent_label = QLabel("Acqua %:",self)
        self.waterD_percent_field = QLineEdit()
        self.waterD_percent_field.setPlaceholderText("0 - 100%")
        rwkcolD_layout.addWidget(self.waterD_percent_label)
        rwkcolD_layout.addWidget(self.waterD_percent_field)
        #Cooling field
        self.coolingD_temp_label = QLabel("Temp. Raffredamento:",self)
        self.coolingD_temp_field = QLineEdit()
        self.coolingD_temp_field.setPlaceholderText("1 - 20 °C")
        rwkcolD_layout.addWidget(self.coolingD_temp_label)
        rwkcolD_layout.addWidget(self.coolingD_temp_field)
        schD_form_layout.addLayout(rwkcolD_layout)
        schD_form_layout.addLayout(advD_layout)
        schD_form_layout.setAlignment(Qt.AlignTop)

        #Add buttons to the buttons layout
        self.schD_add_button = QPushButton("Aggiungere alla programmazione")
        sch_reset_button = QPushButton("Resetta Modulo")
        schD_delete_button = QPushButton("Cancella dalla programmazione")
        schD_transfer_button = QPushButton("Trasferire al PLC")
        schD_refresh_button = QPushButton("Aggiorna Lista Programmazione")
        schD_up_button = QPushButton("Sposta WorkOrder su")
        schD_down_button = QPushButton("Sposta WorkOrder giù")
        schD_report_button = QPushButton("Genera Pre-Prod Report")
        schD_button_layout.addWidget(schD_report_button)
        schD_button_layout.addWidget(self.schD_add_button)
        self.schD_add_button.clicked.connect(self.add_to_scheduleD)
        schD_report_button.clicked.connect(self.generate_plan_reportD)
        schD_button_layoutb.addWidget(schD_up_button)
        schD_up_button.clicked.connect(self.up_selected_scheduleD)
        schD_button_layoutb.addWidget(schD_down_button)
        schD_down_button.clicked.connect(self.down_selected_scheduleD)
        schD_button_layoutb.addWidget(schD_delete_button)
        schD_delete_button.clicked.connect(self.delete_selected_scheduleD)
        schD_button_layoutb.addWidget(schD_transfer_button)
        schD_transfer_button.clicked.connect(self.transfer_to_plcD)
        schD_button_layout.addWidget(schD_refresh_button)
        schD_refresh_button.clicked.connect(self.refresh_schedule_listD)

        # Create a group box
        self.groupDBox = QGroupBox("Parametri Avanzati")
        self.groupDBox.setCheckable(True)
        self.groupDBox.setChecked(False) # Start unchecked (collapsed)
        self.groupDBox.toggled.connect(self.onToggle) # Connect signal to slot

        # Create sections with parameters
        parametersD_layout = QVBoxLayout()
        self.groupDBox.setLayout(parametersD_layout)
        
        # Section "Pasteurizer Parameters"
        self.pastD_label1 = QLabel("Past. Temp.:", self) #su
        self.pastD_field1 = QLineEdit("88.0")
        advD_layout.addWidget(self.pastD_label1)
        advD_layout.addWidget(self.pastD_field1)
        self.pastD_label10 = QLabel("Press. Omog. 1:", self) #su
        self.pastD_field10 = QLineEdit("150.0")
        self.pastD_label11 = QLabel("Press. Omog. 2:", self) #su
        self.pastD_field11 = QLineEdit("30.0")
        advD_layout.addWidget(self.pastD_label10)
        advD_layout.addWidget(self.pastD_field10)
        advD_layout.addWidget(self.pastD_label11)
        advD_layout.addWidget(self.pastD_field11)

        self.blenD_label1 = QLabel("Temp. Blender:", self)
        self.blenD_field1 = QLineEdit("55.0")
        blenderD_parameters_layout2.addWidget(self.blenD_label1)
        blenderD_parameters_layout2.addWidget(self.blenD_field1)
        self.pastD_label8 = QLabel("Liv. Purea:", self)
        self.pastD_field8 = QLineEdit("1000.0")
        blenderD_parameters_layout2.addWidget(self.pastD_label8)
        blenderD_parameters_layout2.addWidget(self.pastD_field8)

        # Button to toggle edit mode
        editD_button = QLabel("Parametri fissi di produzioni - Non cambiare")

        # Add the edit button to the layout
        parametersD_layout.addWidget(editD_button)

        parametersD_layout.addLayout(blenderD_parameters_layout2)
        parametersD_layout.addLayout(blenderD_parameters_layout3)

        self.blenD_label10 = QLabel("Tempo Agit.(s):", self) #su
        self.blenD_field10 = QLineEdit("300")
        self.blenD_label4 = QLabel("HoldingTime(min):", self) #su
        self.blenD_field4 = QLineEdit("20")
        blenderD_parameters_layout2.addWidget(self.blenD_label4)
        blenderD_parameters_layout2.addWidget(self.blenD_field4)
        blenderD_parameters_layout2.addWidget(self.blenD_label10)
        blenderD_parameters_layout2.addWidget(self.blenD_field10)

        self.blenD_label7 = QLabel("Vel. Ag. Zuc:", self)
        self.blenD_field7 = QLineEdit("100.0")
        self.blenD_label8 = QLabel("Vel. Ag. Glu:", self)
        self.blenD_field8 = QLineEdit("100.0")
        self.blenD_label9 = QLabel("Vel. Ag. Man:", self)
        self.blenD_field9 = QLineEdit("100.0")
        blenderD_parameters_layout3.addWidget(self.blenD_label7)
        blenderD_parameters_layout3.addWidget(self.blenD_field7)
        blenderD_parameters_layout3.addWidget(self.blenD_label8)
        blenderD_parameters_layout3.addWidget(self.blenD_field8)
        blenderD_parameters_layout3.addWidget(self.blenD_label9)
        blenderD_parameters_layout3.addWidget(self.blenD_field9)
        
        # Add sections to the main parameters layout
        schD_form_layout.addLayout(p04D_parameters_layout)
        schD_form_layout.addLayout(pasteurizerD_parameters_layout)
        schD_form_layout.addLayout(pasteurizerD_parameters_layout2)
        schD_form_layout.addLayout(pasteurizerD_parameters_layout3)
        schD_form_layout.addLayout(blenderD_parameters_layout)
        schD_form_layout.addLayout(blenderD_parameters_layout2)
        schD_form_layout.addLayout(blenderD_parameters_layout3)

        #Split form from Table and Buttons
        spacerD = QSpacerItem(20, 50, QSizePolicy.Minimum, QSizePolicy.Fixed)
        schD_form_layout.addSpacerItem(spacerD)
        #sch_form_layout.addLayout(parameters_layout)
        schD_form_layout.addWidget(self.groupDBox)
        formD_split_layout.addLayout(schD_form_layout)
        
        # Ingredient table
        self.ingredientsD_table_label = QLabel("Lista Ingredienti:",self)
        self.ingredientsD_table = QTableWidget()
        self.ingredientsD_table.setMinimumWidth(900)
        self.ingredientsD_table.setColumnCount(6)  # Assuming 5 columns
        self.ingredientsD_table.setHorizontalHeaderLabels(["Ricetta", "Tipo", "Codice", "Descrizione", "%", "Quantità(Kg)"])
        self.ingredientsD_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ingredientsD_table.horizontalHeader().setSectionResizeMode(5,QHeaderView.Stretch)
        self.ingredientsD_table.resizeColumnsToContents()
        ingrlistD_layout.addWidget(self.ingredientsD_table_label)
        ingrlistD_layout.addWidget(self.ingredientsD_table)
        formD_split_layout.addLayout(ingrlistD_layout)
        scheduleD_layout.addLayout(formD_split_layout)
        scheduleD_layout.addLayout(schD_button_layout)
                                 
        # Scheduled WO Table
        scheduleD_table_label = QLabel("Lista Programmazione:", self)
        self.scheduleD_table = QTableWidget()
        scheduleD_table_layout = QVBoxLayout()
        self.scheduleD_table.resizeColumnsToContents()
        scheduleD_layout.addWidget(scheduleD_table_label)
        scheduleD_layout.addWidget(self.scheduleD_table)
        scheduleD_layout.addLayout(schD_button_layoutb)
        
        # Add the form layout and the table to the horizontal layout
        horizontalD_layout.addWidget(scheduleD_container)
        horizontalD_layout.addLayout(scheduleD_table_layout)

        # Set the main layout of the tab to be the horizontal layout
        scheduleD_tab.setLayout(scheduleD_layout)
        self.populate_schedule_tableD()

#--------------------------------------------END OF SCHEDULE LINEA DHMI----------------------------------------------------
#--------------------------------------------BEGIN OF REPORT HMI----------------------------------------------------
        # Create a tab for Reports
        report_tab = QWidget()

        # Create a horizontal layout to hold both the form and the table
        rep_h_layout = QHBoxLayout(report_tab)
        rep_table_layout = QVBoxLayout()

        # Scheduled WO Table
        report_label = QLabel("Lista WorkOrders:", self)
        self.report_table = QTableWidget()
        self.report_table.setMinimumWidth(1320)
        self.report_table.setSortingEnabled(True)
        self.report_table.setColumnCount(12)  # Adjust this according to your table's column count
        self.report_table.setHorizontalHeaderLabels(
            ["Linea", "Batch", "WorkOrder", "Ricetta", "Descrizione", "Quantità", 
             "Pasteurizatore", "Serbatoio", "Blender", "Programmato", "Aggiornato", "Completato"]
        )
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Add the label and table widget to rep_h_layout
        rep_table_layout.addWidget(report_label)
        rep_table_layout.addWidget(self.report_table)

        # Create a QVBoxLayout to hold the buttons
        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignTop)

        # Filter
        self.worder_label = QLabel("Filtro WorkOrder:")
        self.filter_rep = QLineEdit()
        self.filter_rep.textChanged.connect(self.filter_report)
        self.picker_label = QLabel("Filtro Data:")
        self.date_picker = QDateEdit(self)
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.time_label = QLabel("Filtro Ora:")
        self.time_picker = QComboBox(self)
        button_layout.addWidget(self.worder_label)
        button_layout.addWidget(self.filter_rep)
        button_layout.addWidget(self.picker_label)
        button_layout.addWidget(self.date_picker)
        button_layout.addWidget(self.time_label)
        button_layout.addWidget(self.time_picker)

        # Buttons Set
        end_report_button = QPushButton("Genera Post-Prod")
        sch_past_button = QPushButton("Genera Pastorizzatore")
        rep_refresh_button = QPushButton("Aggiorna Lista WorkOrder")
        sch_report_button = QPushButton("Genera Pre-Prod")
        bulkend_button = QPushButton("Genera Post-Prod Giorno")
        bulkpast_button = QPushButton("Genera Pastor. Giorno")
        button_layout.addWidget(sch_report_button)
        sch_report_button.clicked.connect(self.generate_plan_report2)
        button_layout.addWidget(end_report_button)
        end_report_button.clicked.connect(self.generate_end_report)
        button_layout.addWidget(sch_past_button)
        sch_past_button.clicked.connect(self.generate_past_report)
        button_layout.addWidget(rep_refresh_button)
        rep_refresh_button.clicked.connect(self.refresh_report_tab)
        button_layout.addWidget(bulkend_button)
        bulkend_button.clicked.connect(self.generate_bulkend_report)
        button_layout.addWidget(bulkpast_button)
        bulkpast_button.clicked.connect(self.generate_bulkpast_report)

        self.date_picker.dateChanged.connect(self.on_date_changed)
        self.time_picker.currentTextChanged.connect(self.on_time_changed)

        # Add the button layout to rep_h_layout
        rep_h_layout.addLayout(rep_table_layout)
        rep_h_layout.addLayout(button_layout)

        report_tab.setLayout(rep_h_layout)
        
        # Populate the report table and time picker on first open
        self.populate_report_table(QDate.currentDate().toString('yyyy-MM-dd') + '%')
        self.populate_time_picker()

#--------------------------------------------END OF REPORT HMI---------------------------------------------------- 
#----------------------------------------ORGANIZE AND PROTECT TABS------------------------------------------------ 

        self.tab_widget.addTab(schedule_tab, "Programma")
        self.tab_widget.addTab(scheduleD_tab, "Linea D")
        self.tab_widget.addTab(report_tab, "Reports")
        self.tab_widget.addTab(ingredients_tab, "Ingredienti")
        self.tab_widget.addTab(recipes_tab, "Ricette")

        # Connect the tab change event to check for password
        self.tab_widget.currentChanged.connect(self.tab_changed)

        # Protected tabs indexes
        self.protected_tabs = {
            #"Ingredienti": 2,
            "Ricette": 3
        }

#--------------------------------------------------------------------END OF MAIN FUNCTIONS/HMI
#--------------------------------------------------------------------BEGIN OF INGREDIENTS FUNCTIONS/HMI   
    
    def filter_table(self, text):
        for row in range(self.tableWidget.rowCount()):
            # Get the items from column 0 and column 1 of the current row
            item0 = self.tableWidget.item(row, 0)
            item1 = self.tableWidget.item(row, 1)
            
            # Check if the items are not None and if the text matches any of them
            is_match = False
            if item0 is not None and text.lower() in item0.text().lower():
                is_match = True
            if item1 is not None and text.lower() in item1.text().lower():
                is_match = True
            
            # Hide the row if there is no match
            self.tableWidget.setRowHidden(row, not is_match)

    def refresh_table(self):
        # Clear the existing data in the table widget -- checkpoint
        self.tableWidget.clearContents()

        # Connect to the SQL Server
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Retrieve data from the database (similar to your initial data retrieval code)
        cursor.execute("""
            SELECT
                [im_code] as Codice,
                [im_description] as Descrizione,
                aa.ia_description AS [Area],
                CASE WHEN [im_typeid] = 1 THEN 'Automatic' ELSE 'Manual' END as [Auto/Manuale],
                irt.irt_description AS [Tipo Rework],
                [im_storage] as [ID Serbatoio],
                [im_storagename] as [Nome Serbatoio]
            FROM
                [RecipeDB].[dbo].[IngredientMaster] im
            LEFT JOIN
                [dbo].[IngredientArea] aa ON im.im_areaid = aa.ia_areaid
            LEFT JOIN
                [dbo].[IngredientReworkType] irt ON im.im_reworktypeid = irt.irt_reworktypeid
            ORDER BY [im_code] ASC
        """)

        # Get column names (similar to your initial code)
        column_names = [column[0] for column in cursor.description]

        # Set the column count and labels for recipesTableWidget
        self.tableWidget.setColumnCount(len(column_names))
        self.tableWidget.setHorizontalHeaderLabels(column_names)

        # Populate the table with data (similar to your initial code)
        row_index = 0
        for row in cursor.fetchall():
            self.tableWidget.insertRow(row_index)  
            for col_index, value in enumerate(row):
                self.tableWidget.setItem(row_index, col_index, QTableWidgetItem(str(value)))  
            row_index += 1

        # Close the database connection
        conn.close()

    def open_add_dialog(self):
        dialog = AddEditDialog(self)
        dialog.setWindowTitle("Add Ingredient")
        dialog.refresh_signal.connect(self.refresh_table)
    
        # Connect to the database
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
    
        # Populate combo boxes
        dialog.populate_fields(cursor)
        if dialog.exec_() == QDialog.Accepted:
            # Handle the data entered in the Edit dialog and update it in the database
            code = dialog.code_edit.text()
            description = dialog.description_edit.text()
            area = dialog.area_combo.currentText()
            manual = dialog.manual_radio.isChecked()
            rework_type = dialog.rework_type_combo.currentText()

    def open_modify_dialog(self):
        selected_rows = self.tableWidget.selectionModel().selectedRows()
        if selected_rows:
            # Assuming the recipe ID is in the first column
            ingr_id = selected_rows[0].data()
            dialog = EditIngredientsDialog(ingr_id, self)
            dialog.refresh_signal.connect(self.refresh_table)
            dialog.exec_()
        else:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un ingrediente da editare.")

    def open_delete_dialog(self):
        selected_row = self.tableWidget.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un ingrediente da cancellare.")
            return
    
        # Assuming the Ingredient ID (im_ingredientid) is in a specific column, e.g., column 0
        ingredient_id_item = self.tableWidget.item(selected_row, 0)
        if ingredient_id_item is None:
            QMessageBox.warning(self, "Errore", "Nessun ingrediente trovato per l'item selezionato")
            return
    
        ingredient_id = ingredient_id_item.text()
    
        reply = QMessageBox.question(self, "Conferma Cancellazione",
                                     f"Sei sicuro di voler cancellare l'ingrediente di ID {ingredient_id}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            self.delete_ingredient_from_db(ingredient_id)
            self.refresh_table()
    
    def delete_ingredient_from_db(self, ingredient_id):
        try:
            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
        
                delete_query = "DELETE FROM dbo.IngredientMaster WHERE im_code = ?"
                cursor.execute(delete_query, ingredient_id)  # Pass ingredient_id directly as a string
        
                conn.commit()
        
                QMessageBox.information(self, "Successo", "Ingrediente cancellato con successo.")
        except Exception as e:
            QMessageBox.warning(self, "Cancellazione Fallita", f"Si è verificato un errore: {e}")

    def open_copy_dialog(self):
        ingredient_row = self.tableWidget.currentRow()
        if ingredient_row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un ingrediente da copiare.")
            return
    
        try:
            # Fetch the code from the selected row, assuming 'im_code' is in column 0
            original_code = self.tableWidget.item(ingredient_row, 0).text()
    
            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
    
            # Fetch the description and other values from the selected row in the table
            original_code = self.tableWidget.item(ingredient_row, 0).text()
            original_description = self.tableWidget.item(ingredient_row, 1).text()
            new_description = "COPIA " + original_description
    
            # Insert the new row using a subquery to get the next im_ingredientid
            insert_query = """
            INSERT INTO dbo.IngredientMaster (im_ingredientid, im_code, im_description, im_accosid, im_areaid, im_typeid, im_reworktypeid, im_storage, im_storagename) 
            VALUES ((SELECT MAX(im_ingredientid) + 1 FROM dbo.IngredientMaster), 
                    1, 
                    ?, 
                    (SELECT im_accosid FROM dbo.IngredientMaster WHERE im_code = ?), 
                    (SELECT im_areaid FROM dbo.IngredientMaster WHERE im_code = ?), 
                    (SELECT im_typeid FROM dbo.IngredientMaster WHERE im_code = ?), 
                    (SELECT im_reworktypeid FROM dbo.IngredientMaster WHERE im_code = ?),
                    (SELECT im_storage FROM dbo.IngredientMaster WHERE im_code = ?),
                    (SELECT im_storagename FROM dbo.IngredientMaster WHERE im_code = ?));
            """
            cursor.execute(insert_query, (new_description, original_code, original_code, original_code, original_code, original_code, original_code))
    
            conn.commit()
            conn.close()

            self.refresh_table()
            QMessageBox.information(self, "Successo", "Ingrediente copiado con successo.")
            
        except Exception as e:
            QMessageBox.warning(self, "Copia Falita", f"Si è verificato un errore: {e}")

    def show_recipes_dialog(self):
        selected_row = self.tableWidget.currentRow()
        if selected_row < 0:
            return

        selected_code = self.tableWidget.item(selected_row, 0).text()
        
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                rm.rm_recipeid, rm.rm_description
            FROM
                dbo.RecipeMaster rm
            JOIN
                dbo.RecipeIngredients ri ON ri.ri_recipeid = rm.rm_recipeid
            WHERE
                ri.ri_code = ?
        """, selected_code)
        
        recipe_data = cursor.fetchall()
        conn.close()
        
        if recipe_data:
            dialog = CommIngrDialog(recipe_data, self)
            dialog.exec_()
        else:
            QMessageBox.warning(self, "Non trovato!", "Nessuna ricetta contiene questo ingrediente.")

#--------------------------------------------------------------------END OF INGREDIENTS FUNCTIONS/HMI
#--------------------------------------------------------------------BEGIN OF RECIPES FUNCTIONS/HMI

    def rfilter_table(self, text):
        for row in range(self.recipesTableWidget.rowCount()):
            # Get the items from column 0 and column 1 of the current row
            item0 = self.recipesTableWidget.item(row, 0)
            item1 = self.recipesTableWidget.item(row, 1)
            
            # Check if the items are not None and if the text matches any of them
            is_match = False
            if item0 is not None and text.lower() in item0.text().lower():
                is_match = True
            if item1 is not None and text.lower() in item1.text().lower():
                is_match = True
            
            # Hide the row if there is no match
            self.recipesTableWidget.setRowHidden(row, not is_match)
            
    def ropen_add_dialog(self):
        dialog = RecipeDialog(self)
        dialog.recipeAdded.connect(self.r_refresh_table)
        dialog.exec_()

    def open_edit_recipe_ingredients_dialog(self):
        selected_rows = self.recipesTableWidget.selectionModel().selectedRows()
        if selected_rows:
            first_selected_row = selected_rows[0]
            # Retrieve the line number from column 3 (index 2)
            lineno = self.recipesTableWidget.model().data(first_selected_row.sibling(first_selected_row.row(), 2))
            recipe_id = first_selected_row.data()  # Assuming recipe_id is in the first column

            if lineno == "D":
                dialog = EditRecipeIngredientsDialogD(recipe_id, self)
                dialog.recipeUpdated.connect(self.r_refresh_table)
                dialog.exec_()
            elif lineno == "B" or lineno == "C":
                dialog = EditRecipeIngredientsDialog(recipe_id, self)
                dialog.recipeUpdated.connect(self.r_refresh_table)
                dialog.exec_()
            else:
                QMessageBox.warning(self, "Attenzione", "Seleziona prima una ricetta da editare.")
        else:
            QMessageBox.warning(self, "Attenzione", "Nessuna ricetta selezionata.")

    def open_delete_recipe_dialog(self):
        selected_row = self.recipesTableWidget.currentRow()  # Make sure to reference the correct table widget
        if selected_row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima una ricetta da cancellare.")
            return
    
        recipe_id_item = self.recipesTableWidget.item(selected_row, 0)  # Again, reference the correct table widget
        if recipe_id_item is None:
            QMessageBox.warning(self, "Errore", "Nessuna ricetta trovata per l'item selezionato")
            return
    
        recipe_id = int(recipe_id_item.text())  # Convert to int
    
        reply = QMessageBox.question(self, "Conferma Cancellazione",
                                     f"Sei sicuro di voler cancellare la ricetta di ID {recipe_id}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            self.delete_recipe_from_db(recipe_id)
            self.r_refresh_table()
    
    def delete_recipe_from_db(self, recipe_id):
        try:
            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # Start a transaction
            conn.autocommit = False

            # First, delete the related ingredients to maintain referential integrity
            query_ingredients = "DELETE FROM dbo.RecipeIngredients WHERE ri_recipeid = ?"
            cursor.execute(query_ingredients, (recipe_id))
            
            # Then, delete the recipe itself
            delete_query_master = "DELETE FROM dbo.RecipeMaster WHERE rm_recipeid = ?"
            cursor.execute(delete_query_master, (recipe_id))
            
            # Commit the transaction
            conn.commit()
            
            QMessageBox.information(self, "Successo", "Ricetta cancellata con successo.")

        except Exception as e:
            # If an error occurs, rollback the transaction
            conn.rollback()
            QMessageBox.warning(self, "Cancellazione Falita", f"Si è verificato un errore: {e}")
        
        finally:
            # Close the connection
            if conn:
                conn.close()

    def r_refresh_table(self):
        # Clear the existing data in the table widget
        self.recipesTableWidget.clearContents()

        # Connect to the SQL Server
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Retrieve data from the database (similar to your initial data retrieval code)
        cursor.execute("""
            SELECT
                [rm_recipeid] as [Codice Ricetta],
                [rm_description] as Descrizione,
                [rm_line] as [Linea di Produzione],
                [rm_patemperature] as [Temp. Pasteur.],
                [rm_holdingtime] as [Holding Time],
                [rm_omopress] as [Pressione Omo.],
                [rm_omospeed] as [Velocità Omo.]
            FROM
                [RecipeDB].[dbo].[RecipeMaster]
            ORDER BY [rm_recipeid] ASC
        """)

        # Get column names (similar to your initial code)
        column_names = [column[0] for column in cursor.description]

        # Set the column count and labels for recipesTableWidget
        self.recipesTableWidget.setColumnCount(len(column_names))
        self.recipesTableWidget.setHorizontalHeaderLabels(column_names)

        # Populate the table with data (similar to your initial code)
        row_index = 0
        for row in cursor.fetchall():
            self.recipesTableWidget.insertRow(row_index)  # Corrected to self.recipesTableWidget
            for col_index, value in enumerate(row):
                self.recipesTableWidget.setItem(row_index, col_index, QTableWidgetItem(str(value)))  # Corrected to self.recipesTableWidget
            row_index += 1

        # Close the database connection
        conn.close()

    def open_copyrecipe_dialog(self):
        recipe_row = self.recipesTableWidget.currentRow()
        if recipe_row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima una ricetta da copiare.")
            return
    
        try:   
            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
    
            # Fetch the description and other values from the selected row in the table
            original_rcode = self.recipesTableWidget.item(recipe_row, 0).text()
            original_rdescription = self.recipesTableWidget.item(recipe_row, 1).text()
            new_rdescription = "COPIA " + original_rdescription
    
            # Insert the new row using a subquery to get the next im_ingredientid
            insert_query = """
            INSERT INTO dbo.RecipeMaster (rm_recipeid, rm_description, rm_fat, rm_solid, rm_patemperature, 
                                          rm_pressureid,rm_numingredients,rm_numaccosingredients,rm_lastedit,
                                          rm_quantity,rm_stdquantity,rm_holdingtime,rm_line,rm_omospeed,rm_omopress) 
            VALUES (1, 
                    ?, 
                    (SELECT rm_fat FROM dbo.RecipeMaster WHERE rm_recipeid = ?),
                    (SELECT rm_solid FROM dbo.RecipeMaster WHERE rm_recipeid = ?),
                    (SELECT rm_patemperature FROM dbo.RecipeMaster WHERE rm_recipeid = ?),
                    (SELECT rm_pressureid FROM dbo.RecipeMaster WHERE rm_recipeid = ?),
                    (SELECT rm_numingredients FROM dbo.RecipeMaster WHERE rm_recipeid = ?),
                    (SELECT rm_numaccosingredients FROM dbo.RecipeMaster WHERE rm_recipeid = ?),
                    GETDATE(),
                    (SELECT rm_quantity FROM dbo.RecipeMaster WHERE rm_recipeid = ?),
                    (SELECT rm_stdquantity FROM dbo.RecipeMaster WHERE rm_recipeid = ?),
                    (SELECT rm_holdingtime FROM dbo.RecipeMaster WHERE rm_recipeid = ?),
                    (SELECT rm_line FROM dbo.RecipeMaster WHERE rm_recipeid = ?),
                    (SELECT rm_omospeed FROM dbo.RecipeMaster WHERE rm_recipeid = ?),
                    (SELECT rm_omopress FROM dbo.RecipeMaster WHERE rm_recipeid = ?));
            """
            cursor.execute(insert_query, (new_rdescription, original_rcode, original_rcode, original_rcode, original_rcode, 
                                          original_rcode, original_rcode, original_rcode, original_rcode, original_rcode, original_rcode, 
                                          original_rcode, original_rcode))
            
            #cursor.execute("SELECT MAX(rm_recipeid) FROM dbo.RecipeMaster")
            new_rcode = 1 #cursor.fetchone()[0]
            
            insert_query2 = """
            INSERT INTO dbo.RecipeIngredients (ri_recipeid, ri_sequence, ri_ingredientid, ri_percentage, ri_stdpercentage, ri_code)
            SELECT ?, ri_sequence, ri_ingredientid, ri_percentage, ri_stdpercentage, ri_code
            FROM dbo.RecipeIngredients
            WHERE ri_recipeid = ?;
            """
            cursor.execute(insert_query2, (new_rcode, original_rcode))

            conn.commit()
            conn.close()

            self.r_refresh_table()
            QMessageBox.information(self, "Successo", "Ricetta copiata con successo.")
            
        except Exception as e:
            QMessageBox.warning(self, "Copia Falita", f"Si è verificato un errore: {e}")

#--------------------------------------------------------------------END OF RECIPE FUNCTIONS/HMI
#--------------------------------------------------------------------BEGIN OF SCHEDULE FUNCTIONS/HMI

    def populate_recipe_combos(self):
        self.recipe_no_combo.clear()
        self.recipe_name_combo.clear()
        self.original_recipe_items.clear()
        line_combo_text = self.line_combo.currentText()
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        if line_combo_text == "C":
            cursor.execute("SELECT rm_recipeid, rm_description FROM RecipeDB.dbo.RecipeMaster WHERE rm_line = 'B' OR rm_line = 'C'")
        elif line_combo_text == "B":
            cursor.execute("SELECT rm_recipeid, rm_description FROM RecipeDB.dbo.RecipeMaster WHERE rm_line = 'B'")
        elif line_combo_text == "D":
            cursor.execute("SELECT rm_recipeid, rm_description FROM RecipeDB.dbo.RecipeMaster WHERE rm_line = 'D'")
        #elif line_combo_text == "A":
        #    cursor.execute("SELECT rm_recipeid, rm_description FROM RecipeDB.dbo.RecipeMaster WHERE rm_line = 'A'")
        else:
            cursor.execute("SELECT rm_recipeid, rm_description FROM RecipeDB.dbo.RecipeMaster")
        for recipe_id, recipe_name in cursor:
            self.recipe_no_combo.addItem(str(recipe_id), recipe_id)
            self.recipe_name_combo.addItem(recipe_name)
            self.original_recipe_items.append((str(recipe_id), recipe_name))
        conn.close

    def on_recipe_no_combo_changed(self):
        selected_index = self.recipe_no_combo.currentIndex()
        self.recipe_name_combo.setCurrentIndex(selected_index)
        selected_recipe_id = self.recipe_no_combo.currentData()
        #self.load_ingredients()

        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        try:
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                query = "SELECT rm_patemperature, rm_holdingtime, rm_omospeed, rm_omopress FROM RecipeDB.dbo.RecipeMaster WHERE rm_recipeid = ?"
                cursor.execute(query, selected_recipe_id)

                result = cursor.fetchone()

                if result:
                    self.past_field1.setText(str(result[0]))
                    self.past_field10.setText(str(result[3]))
                    self.past_field12.setText(str(result[2]))
                    self.blen_field4.setText(str(result[1]))
                else:
                    self.reset_fields()

        except pyodbc.Error as e:
            print(f"Database error: {e}")
            self.reset_fields()

    def reset_fields(self):
        self.past_field1.setText("88")
        self.past_field10.setText("200")
        self.past_field12.setText("100")
        self.blen_field4.setText("20")
    
    def on_recipe_name_combo_changed(self):
        selected_index = self.recipe_name_combo.currentIndex()
        self.recipe_no_combo.setCurrentIndex(selected_index)
        #self.load_ingredients()

    def sfilter_combo(self):
        filter_text = self.sfilter_edit.text().lower()
        
        # Clear both combo boxes
        self.recipe_no_combo.clear()
        self.recipe_name_combo.clear()

        # Filter and add items based on the original items list
        for recipe_id, recipe_name in self.original_recipe_items:
            if filter_text in recipe_id.lower() or filter_text in recipe_name.lower():
                self.recipe_no_combo.addItem(recipe_id)
                self.recipe_name_combo.addItem(recipe_name)

        # Connect the combo box signals after adding items
        self.recipe_no_combo.currentIndexChanged.connect(self.on_recipe_no_combo_changed)
        self.recipe_name_combo.currentIndexChanged.connect(self.on_recipe_name_combo_changed)

    def populate_mix_tank_combo(self):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT mtm_description FROM RecipeDB.dbo.MixTankMaster")
        for row in cursor.fetchall():
            self.mix_tank_combo.addItem(row[0])  # Add each mix tank description to the combo box
        conn.close()
    
    def populate_age_tank_combo(self):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT atm_description FROM RecipeDB.dbo.AgeTankMaster")
        for row in cursor.fetchall():
            self.age_tank_combo.addItem(row[0])  # Add each age tank description to the combo box
        conn.close()

    def load_ingredients(self):
        selected_recipe_id = self.recipe_no_combo.currentText()
        quantity = 1
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = """
            SELECT ri.ri_recipeid, ia.ia_description, im.im_code, im.im_description, CAST(ri.ri_percentage AS DECIMAL(9,3)) as '%', CAST((ri.ri_percentage * ?) AS DECIMAL(9,3)) as Target
            FROM RecipeDB.dbo.RecipeIngredients ri
            JOIN RecipeDB.dbo.IngredientMaster im ON ri.ri_ingredientid = im.im_ingredientid
            JOIN RecipeDB.dbo.IngredientArea ia ON ia.ia_areaid = im.im_areaid
            WHERE ri.ri_recipeid = ?
            ORDER BY ri.ri_sequence ASC
        """
        cursor.execute(query, (quantity,selected_recipe_id))
        self.populate_ingredients_table(cursor)
        self.ingredients_table.resizeColumnsToContents()
        self.ingredients_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ingredients_table.horizontalHeader().setSectionResizeMode(5,QHeaderView.Stretch)
        conn.close()

    def populate_ingredients_table(self, cursor):
        self.ingredients_table.setRowCount(0)
        for row_index, row_data in enumerate(cursor):
            self.ingredients_table.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                if col_index in [5, 6]:
                    formatted_number = "{:.3f}".format(data)
                    item = QTableWidgetItem(formatted_number)
                else:
                    item = QTableWidgetItem(str(data))    
                self.ingredients_table.setItem(row_index, col_index, item)

    def populate_schedule_table(self):
        # Get the database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute('''SELECT [sc_line] as Line
        	  ,[sc_position] as Seq
              ,[sc_batchid] as WorkOrder
              ,[sc_status] as Status
              ,[sc_recipeid] as Ricetta
              ,[sc_quantity] as Quantità
              ,[sc_pasteuriserid] as Pastorizzatore
              ,[mtm].[mtm_description] as Blender
              ,[atm].[atm_description] as Serbatoio
              ,[sc_scheduled] as StampScheduled
              ,[sc_transferred] as StampTransfer
              ,[sc_completed] as StampComplete
              ,[UniID] as UIdentifier
          FROM [RecipeDB].[dbo].[Schedule] AS [sch]
          INNER JOIN
                [dbo].[MixTankMaster] AS [mtm] ON [sch].[sc_mixtankid] = [mtm].[mtm_tankid]
          INNER JOIN
                [dbo].[AgeTankMaster] AS [atm] ON [sch].[sc_agetankid] = [atm].[atm_tankid]
            WHERE sc_line != 'D'
            ORDER BY [sc_position] ASC''')
        
        # Fetch all the results
        results = cursor.fetchall()
        
        # Determine the number of rows and columns
        number_of_rows = len(results)
        if number_of_rows > 0:
            number_of_columns = len(results[0])
            self.schedule_table.setColumnCount(number_of_columns)
            self.schedule_table.setRowCount(number_of_rows)
            
            # Set the headers if needed
            headers = [description[0] for description in cursor.description]
            self.schedule_table.setHorizontalHeaderLabels(headers)
            header = self.schedule_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)
            self.schedule_table.resizeColumnsToContents()
            
            # Populate the table
            for row_number, row_data in enumerate(results):
                for column_number, data in enumerate(row_data):
                    self.schedule_table.setItem(row_number, column_number, QTableWidgetItem(str(data)))
        
        # Close the cursor and connection
        cursor.close()
        conn.close

    def refresh_schedule_list(self):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        cursor.execute('''SELECT [sc_line] as Line
                    ,[sc_position] as Seq
                    ,[sc_batchid] as WorkOrder
                    ,[sc_status] as Status
                    ,[sc_recipeid] as Ricetta
                    ,[sc_quantity] as Quantità
                    ,[sc_pasteuriserid] as Pastorizzatore
                    ,[mtm].[mtm_description] as Blender
                    ,[atm].[atm_description] as Serbatoio 
                    ,[sc_scheduled] as StampScheduled
                    ,[sc_transferred] as StampTransfer
                    ,[sc_completed] as StampComplete
                    ,[UniID] as UIdentifier
                FROM [RecipeDB].[dbo].[Schedule] AS [sch]
                INNER JOIN
                        [dbo].[MixTankMaster] AS [mtm] ON [sch].[sc_mixtankid] = [mtm].[mtm_tankid]
                INNER JOIN
                        [dbo].[AgeTankMaster] AS [atm] ON [sch].[sc_agetankid] = [atm].[atm_tankid]
                    WHERE sc_line != 'D'
                    ORDER BY [sc_position] ASC''')

        # Fetch all the results
        results = cursor.fetchall()

        # Determine the number of rows and columns
        number_of_rows = len(results)
        number_of_columns = len(results[0]) if number_of_rows > 0 else 0

        # Set the horizontal header labels
        headers = [description[0] for description in cursor.description]
        self.schedule_table.setColumnCount(number_of_columns)
        self.schedule_table.setRowCount(number_of_rows)
        self.schedule_table.setHorizontalHeaderLabels(headers)
        self.schedule_table.resizeColumnsToContents()

        # Set the column resize mode to Stretch
        header = self.schedule_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Populate the table if there are rows
        if number_of_rows > 0:
            for row_number, row_data in enumerate(results):
                for column_number, data in enumerate(row_data):
                    self.schedule_table.setItem(row_number, column_number, QTableWidgetItem(str(data)))

        # Close the cursor and connection
        cursor.close()
        conn.close()

    def calculate_target_quantities(self):
        quantity = self.quantity_field.text()
        if not quantity or not quantity.isdigit():
            quantity = 0
            #QMessageBox.warning(self, "Errore", "Inserisci prima una quantità valida.")
            #return
        
        selected_recipe_id = self.recipe_no_combo.currentText()
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = """
            SELECT ri.ri_recipeid, ia.ia_description, im.im_code, im.im_description, CAST(ri.ri_percentage AS DECIMAL(9,3)) as '%', CAST((ri.ri_percentage * CAST(? AS DECIMAL(9,3))) / 100 AS DECIMAL(10, 2)) as Target
            FROM RecipeDB.dbo.RecipeIngredients ri
            JOIN RecipeDB.dbo.IngredientMaster im ON ri.ri_ingredientid = im.im_ingredientid
            JOIN RecipeDB.dbo.IngredientArea ia ON ia.ia_areaid = im.im_areaid
            WHERE ri.ri_recipeid = ?
            ORDER BY ri.ri_sequence ASC
        """
        cursor.execute(query, (quantity,selected_recipe_id))
        self.populate_ingredients_table(cursor)
        self.ingredients_table.resizeColumnsToContents()
        self.ingredients_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ingredients_table.horizontalHeader().setSectionResizeMode(5,QHeaderView.Stretch)
        conn.close()
        
    def get_selected_ingredients(self):
        selected_ingredients = []
        for row in range(self.ingredients_table.rowCount()):
            # Initialize ingredient_data with default values
            ingredient_data = {
                "recipe_id": "",
                "ingredient_type": "",
                "ingredient_id": "",
                "description": "",
                "standard_percentage": "",
                "total_qty": ""
            }
            for col, key in enumerate(ingredient_data.keys()):
                item = self.ingredients_table.item(row, col)
                if item is not None:
                    ingredient_data[key] = item.text()
            selected_ingredients.append(ingredient_data)
        return selected_ingredients  
        
    def add_to_schedule(self):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Step 1a: Collect values from the UI
        line = self.line_combo.currentText()
        recipe_no = self.recipe_no_combo.currentText()
        recipe_desc = self.recipe_name_combo.currentText()
        quantity = self.quantity_field.text()
        mix_tank_description = self.mix_tank_combo.currentText()
        sc_mixtankid = self.get_mixtankid(mix_tank_description)
        age_tank_description = self.age_tank_combo.currentText()
        sc_agetankid = self.get_agetankid(age_tank_description)
        water_percent = self.water_percent_field.text()
        cooling_temp = self.cooling_temp_field.text()
        rework = 1 if self.rework_yes_radio.isChecked() else 0

        # Step 1b: Collect values from the Static UI
        ats = self.p04_field1.text()
        atf = self.p04_field2.text()
        hmt = self.p04_field3.text()
        ptm = self.past_field1.text()
        pdt = self.past_field2.text() #su
        dtm = cooling_temp
        ddt = self.past_field4.text()
        ept = self.past_field5.text()
        elv = self.past_field6.text()
        bwl = self.past_field7.text()
        puv = self.past_field8.text()
        hov = self.past_field9.text()
        hp1 = self.past_field10.text() #su
        hp2 = self.past_field11.text()
        hos = self.past_field12.text() #su
        mtp = self.blen_field1.text()
        mdt = self.blen_field2.text()
        agt = self.blen_field3.text()
        try:
            hot = int(self.blen_field4.text()) * 60000
        except ValueError:
            hot = None
        spl = self.blen_field5.text()
        wpl = self.blen_field6.text()
        azs = self.blen_field7.text()
        ags = self.blen_field8.text()
        ams = self.blen_field9.text()
    
        # Step 2: Generate sc_batchid
        sc_batchid = self.workorder_txt.text()

        if not all([sc_batchid, line, recipe_no, recipe_desc, quantity, mix_tank_description, age_tank_description, water_percent, cooling_temp, ptm, hp1, hot]):
            QMessageBox.warning(self, "Attenzione", "Inserire tutti i valori prima di aggiungere alla programmazione.")
            return
    
        # Step 3: Calculate sc_position
        try:
            cur_position = self.get_next_position()
            cursor.execute("SELECT [sc_position] FROM [RecipeDB].[dbo].[Schedule]")
            avai_positions = [row[0] for row in cursor.fetchall()]
            next_position = next((pos for pos in cur_position if pos not in avai_positions), None)
            if next_position is not None:
                sc_position = next_position  # Use the current position if it's available
            else:
                QMessageBox.information(self, "Attenzione", "Nessuna posizione disponibile nella coda del Software PLC. Aspettare la liberazione di un posto o cancellare alcuna WorkOrder del Software PLC Supervisorio.")
                return
        except Exception as e:
            error_details = traceback.format_exc()
            QMessageBox.warning(self, "Attenzione", f"La connessione verso PLC per ottenere la posizione non è andata a buon fine. {e},{error_details}")
            return
        #sc_position = 1 #tooth

        workorder = 999999

        # Step 4: Determine sc_pasteuriserid based on line
        pasteuriserid_mapping = {"B": 2, "C": 3, "D": 4}
        sc_pasteuriserid = pasteuriserid_mapping.get(line, 0)
    
        # Step 5: Get sc_actfat and sc_actsolid from RecipeMaster
        sc_actfat, sc_actsolid = self.get_fat_and_solid_values(recipe_no)

        #Get the Ingredients for Schedule
        selected_ingredients = self.get_selected_ingredients()

        #Generate unique identifier
        uniid = str(uuid.uuid4())
    
        # Step 6: Prepare and execute the SQL insert statement
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        try:
            cursor = conn.cursor()
            insert_sql = """
            INSERT INTO dbo.Schedule (
                sc_batchid, sc_line, sc_position, sc_status, sc_recipeid, sc_quantity,
                sc_pasteuriserid, sc_mixtankid, sc_agetankid, sc_autowaterpc, 
                sc_tanktemperature, sc_recovery, sc_colour, sc_actfat, sc_actsolid, 
                sc_reworkqty, sc_reworkfat, sc_reworksolid, sc_transferred, 
                sc_completed, sc_adjusted, sc_waterbatch, sc_scheduled, UniID
            ) VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?, 0, 0, NULL, NULL, 0, 0, GETDATE(), ?)
            """
        
            cursor.execute(insert_sql, (
                sc_batchid, line, sc_position, recipe_no, quantity,
                sc_pasteuriserid, sc_mixtankid, sc_agetankid, water_percent, 
                cooling_temp, sc_actfat, sc_actsolid, rework, uniid
            ))

            insert_sql = """
            INSERT INTO dbo.SchedulePayload (
                SequenceID,WorkOrderID,RecipeID,RecipeName,TotalQty,BatchNumber,PasteurizerID,AgeTankID,IsRework,WaterAutoVol,PTempPast,PTempBreak,
                PPressOmo,PSpeedOmo,PDeltaTPast,PDeltaTBreak,PTempProdEnd,PLiterOmo,PLiterLoadEnd,PLevelWater,BMixTankID,BTempMix,BHoldingTime,
                BDeltaTMix,BPowderLoadPause,BPowderLoadWork,AgitatorTimeSlowP04,AgitatorTimeFastP04,HammerTimeP04,lineid,linename,UniID
            ) VALUES (
                ISNULL((SELECT MAX(SequenceID) FROM dbo.SchedulePayload), 0) + 1,
                ?,
                ?, ?, ?, ?, 
                (SELECT p_description FROM dbo.Pasteurisers WHERE p_line = CAST(? AS VARCHAR)), 
                (SELECT atm_tankid FROM dbo.AgeTankMaster WHERE atm_description = CAST(? AS VARCHAR)),
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                (SELECT mtm_tankid FROM dbo.MixTankMaster WHERE mtm_description = CAST(? AS VARCHAR)), 
                ?, ?, ?, ?, ?, ?, ?, ?,
                (SELECT p_pasteuriserid FROM dbo.Pasteurisers WHERE p_line = CAST(? AS VARCHAR)),
                (SELECT p_line FROM dbo.Pasteurisers WHERE p_line = CAST(? AS VARCHAR)),
                ?
                )
            """
        
            cursor.execute(insert_sql, (
                workorder, recipe_no, recipe_desc, quantity, sc_batchid, line, age_tank_description, rework, water_percent, ptm, dtm,
                hp1, hos, pdt, ddt, ept, hov, elv, bwl, mix_tank_description, mtp, hot,
                mdt, spl, wpl, ats, atf, hmt, line, line, uniid
            ))

            for ingredient in selected_ingredients:
                recipe_id = ingredient["recipe_id"]
                ingredient_type = ingredient["ingredient_type"]
                ingredient_id = ingredient["ingredient_id"]
                description = ingredient["description"]
                standard_percentage = ingredient["standard_percentage"]
                total_qty = ingredient["total_qty"]
                ingr_active = "True" 

                insert_ingredient_sql = """
                INSERT INTO dbo.SchedulePayloadIngrd (BatchNumber, RecipeID, 
                                                    IngrSeqID, 
                                                    IngrID, 
                                                    IngrDesc, 
                                                    IngrTypeID, 
                                                    IngrTypeDesc, StdPercentage, TotalQty, 
                                                    IngrStorage, 
                                                    IngrStorageName, 
                                                    IngrActive, UniID)
                VALUES (?, ?, 
                (SELECT ri_sequence FROM dbo.RecipeIngredients WHERE ri_code = CAST(? AS VARCHAR) and ri_recipeid = CAST(? AS VARCHAR)), 
                (SELECT im_ingredientid FROM dbo.IngredientMaster WHERE im_code = CAST(? AS VARCHAR)), 
                ?,
                (SELECT ia_areaid FROM dbo.IngredientArea WHERE ia_description = CAST(? AS VARCHAR)),
                ?, ?, ?, 
                (SELECT im_storage FROM dbo.IngredientMaster WHERE im_description = CAST(? AS VARCHAR)), 
                (SELECT im_storagename FROM dbo.IngredientMaster WHERE im_description = CAST(? AS VARCHAR)),
                ?,?)
                """
                cursor.execute(insert_ingredient_sql, (sc_batchid,recipe_id,ingredient_id,recipe_id,ingredient_id,description,ingredient_type,ingredient_type,standard_percentage,total_qty, description, description, ingr_active, uniid))
                
                #insert_query = """
                #    INSERT INTO dbo.Reports (LineID,SequenceID,WorkOrderID,RecipeID,RecipeName,RecTotalQty,BatchNumber,PasteurizerID,
                #    AgeTankID,MixTankID,IngrSeqID,IngrDesc,IngrTypeID,IngrTypeDesc,IngrStorage,IngrStorageName,
                #    StdPercentage,TotalQty,EffectiveQty,Variance,TimeInserted,TimeUpdated,TimeCompleted,UniID,IngrID,IngrCode) 
                #    VALUES ((SELECT p_pasteuriserid FROM dbo.Pasteurisers WHERE p_line = CAST(? AS VARCHAR)), ?, ?, ?, ?, ?, ?, (SELECT p_description FROM dbo.Pasteurisers WHERE p_line = CAST(? AS VARCHAR)), 
                #    (SELECT atm_tankid FROM dbo.AgeTankMaster WHERE atm_description = CAST(? AS VARCHAR)), 
                #    (SELECT mtm_tankid FROM dbo.MixTankMaster WHERE mtm_description = CAST(? AS VARCHAR)), 
                #    (SELECT ri_sequence FROM dbo.RecipeIngredients WHERE ri_code = CAST(? AS VARCHAR) and ri_recipeid = CAST(? AS VARCHAR)),
                #    ?, 
                #    (SELECT ia_areaid FROM dbo.IngredientArea WHERE ia_description = CAST(? AS VARCHAR)), 
                #    ?, 
                #    (SELECT im_storage FROM dbo.IngredientMaster WHERE im_description = CAST(? AS VARCHAR)), 
                #    (SELECT im_storagename FROM dbo.IngredientMaster WHERE im_description = CAST(? AS VARCHAR)), 
                #    ?, ?, 
                #    NULL, NULL, GETDATE(), GETDATE(), NULL,?,(SELECT im_ingredientid FROM RecipeDB.dbo.IngredientMaster WHERE im_code = ?),?)
                #    """
                ## Execute the insert query for each row in ingr_rows
                #cursor.execute(insert_query, (line, sc_position, workorder, recipe_id, recipe_desc, quantity, sc_batchid, line,
                #                                age_tank_description, mix_tank_description, ingredient_id, recipe_id, description, ingredient_type, ingredient_type,
                #                                description, description, standard_percentage, total_qty, uniid, ingredient_id, ingredient_id))
                        
            conn.commit()
            
            #QMessageBox.information(self, "Successo", "WorkOrder inserita con successo alla programmazione.")
            self.refresh_schedule_list() #bobbin
            self.ingredients_table.setRowCount(0)
            self.workorder_txt.clear()
            self.sfilter_edit.clear()
            self.recipe_no_combo.setCurrentIndex(-1)
            self.recipe_name_combo.setCurrentIndex(-1)
            self.line_combo.setCurrentIndex(-1)
            self.quantity_field.clear()
            self.mix_tank_combo.setCurrentIndex(-1)
            self.age_tank_combo.setCurrentIndex(-1)
            self.water_percent_field.clear()
            self.cooling_temp_field.clear()
            
        except Exception as e:
            error_details = traceback.format_exc()
            QMessageBox.warning(self, "Errore", f"Si è verificato un errore: {e},{error_details}")
            return
        finally: #tooth
            conn.close

    def get_next_position(self):
        client = Client(f"opc.tcp://{ip}:4840")
        client.session_timeout = 30000
        client.connect()

        next_positions = []
        for next_position in range(1, 11):
            nodest = f'ns=3;s="RecipeManagement"."Lista"[{next_position}]."Codice"'
            value = client.get_node(nodest).get_value()

            if value == "":
                next_positions.append(next_position)

        client.disconnect()

        return next_positions

    def get_fat_and_solid_values(self, recipe_id):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
    
        # SQL query to retrieve rm_fat and rm_solid values
        query = "SELECT rm_fat, rm_solid FROM RecipeDB.dbo.RecipeMaster WHERE rm_recipeid = ?"
        cursor.execute(query, (recipe_id,))
    
        result = cursor.fetchone()
        sc_actfat, sc_actsolid = result if result else (0, 0)
    
        cursor.close()
        conn.close()
    
        return sc_actfat, sc_actsolid

    def get_mixtankid(self, mix_tank_description):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
    
        query = "SELECT mtm_tankid FROM RecipeDB.dbo.MixTankMaster WHERE mtm_description = ?"
        cursor.execute(query, (mix_tank_description,))
    
        result = cursor.fetchone()
        sc_mixtankid = result[0] if result else None
    
        cursor.close()
        conn.close()
    
        return sc_mixtankid

    def get_agetankid(self, age_tank_description):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
    
        query = "SELECT atm_tankid FROM RecipeDB.dbo.AgeTankMaster WHERE atm_description = ?"
        cursor.execute(query, (age_tank_description,))
    
        result = cursor.fetchone()
        sc_agetankid = result[0] if result else None
    
        cursor.close()
        conn.close()
    
        return sc_agetankid

    def delete_selected_schedule(self):
        selected_row = self.schedule_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima una WorkOrder da cancellare.")
            return
    
        # Assuming the Work Order (sc_batchid) is in a specific column, e.g., column 0
        work_order_item = self.schedule_table.item(selected_row, 2)
        uniid = self.schedule_table.item(selected_row, 12)
        if work_order_item is None:
            QMessageBox.warning(self, "Errore", "Nessuna WorkOrder trovata per la selezione.")
            return
    
        work_order = work_order_item.text()
        uniqueid = uniid.text()
    
        reply = QMessageBox.question(self, "Conferma Cancellazione", 
                                     f"Sei sicuro di voler cancellare WorkOrder ID {work_order}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            self.delete_schedule_from_db(uniqueid)
            self.refresh_schedule_list()

    def delete_schedule_from_db(self, uniqueid):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
    
        sch = "DELETE FROM RecipeDB.dbo.Schedule WHERE UniID = ?"
        cursor.execute(sch, (uniqueid))
        conn.commit()
        schpl = "DELETE FROM RecipeDB.dbo.SchedulePayload WHERE UniID = ?"
        cursor.execute(schpl, (uniqueid))
        conn.commit()
        schpli = "DELETE FROM RecipeDB.dbo.SchedulePayloadIngrd WHERE UniID = ?"
        cursor.execute(schpli, (uniqueid))
        conn.commit()
    
        cursor.close()
        conn.close()

    def up_selected_schedule(self):
        selected_row = self.schedule_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selezione Richiesta", "Selezionare prima una WorkOrder per spostare su.")
            return
        seq_ref_item = self.schedule_table.item(selected_row, 1)
        batch_ref_item = self.schedule_table.item(selected_row, 2)

        seq_ref = int(seq_ref_item.text())
        batch_ref = int(batch_ref_item.text())

        empty_pos = get_empty_positions()

        if seq_ref - 1 not in empty_pos:
            QMessageBox.warning(self, "Attenzione", "WorkOrder già è alla prima posizione disponibile.")
            return
        elif seq_ref == 1:
            QMessageBox.warning(self, "Attenzione", "WorkOrder già è alla prima posizione della lista.")
            return

        reply = QMessageBox.question(self, "Conferma",
                                    f"Sei sicuro di voler spostare la WorkOrder alla posizione {seq_ref - 1}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            seq_new = seq_ref - 1
            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            update_up = """
            UPDATE dbo.Schedule
            SET sc_position = ?
            WHERE sc_position = ?;

            UPDATE dbo.SchedulePayload
            SET SequenceID = ?
            WHERE SequenceID = ?;

            UPDATE dbo.Schedule
            SET sc_position = ?
            WHERE sc_batchid = ?;

            UPDATE dbo.SchedulePayload
            SET SequenceID = ?
            WHERE BatchNumber = ?;
            """
            cursor.execute(update_up, (seq_ref, seq_new, seq_ref, seq_new, seq_new, batch_ref, seq_new, batch_ref))
            conn.commit()
            self.refresh_schedule_list()
      
    def down_selected_schedule(self):
        selected_row = self.schedule_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selezione Richiesta", "Selezionare prima una WorkOrder per spostare giù.")
            return
        seq_ref_item = self.schedule_table.item(selected_row, 1)
        batch_ref_item = self.schedule_table.item(selected_row, 2)

        seq_ref = int(seq_ref_item.text())
        batch_ref = int(batch_ref_item.text())

        empty_pos = get_empty_positions()

        if seq_ref + 1 not in empty_pos:
            QMessageBox.warning(self, "Attenzione", "WorkOrder già è all'ultima posizione disponibile.")
            return
        elif seq_ref == 10:
            QMessageBox.warning(self, "Attenzione", "WorkOrder già è all'ultima posizione dalla lista.")
            return

        reply = QMessageBox.question(self, "Conferma",
                                    f"Sei sicuro di voler spostare la WorkOrder alla posizione {seq_ref + 1}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            seq_new = seq_ref + 1
            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            update_up = """
            UPDATE dbo.Schedule
            SET sc_position = ?
            WHERE sc_position = ?;

            UPDATE dbo.SchedulePayload
            SET SequenceID = ?
            WHERE SequenceID = ?;

            UPDATE dbo.Schedule
            SET sc_position = ?
            WHERE sc_batchid = ?;

            UPDATE dbo.SchedulePayload
            SET SequenceID = ?
            WHERE BatchNumber = ?;
            """
            cursor.execute(update_up, (seq_ref, seq_new, seq_ref, seq_new, seq_new, batch_ref, seq_new, batch_ref))
            conn.commit()
            self.refresh_schedule_list()

    def get_stampid(self):
        try:
            ctime = datetime.now()
            ftime = int(ctime.strftime("%y%m%d") + "01")
            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            conn = pyodbc.connect(conn_str)
            query = "SELECT TOP 1 WorkOrderID FROM RecipeDB.dbo.Reports ORDER BY WorkOrderID DESC"
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            lastDB = result[0] if result else 0

            laststamp = max(lastDB, ftime)

            if laststamp >= int(ftime):
                workorder = laststamp +1
            else:
                workorder = int(ftime) +1
                
            #client.disconnect()
            return workorder
        
        except Exception as e:
            error_details = traceback.format_exc()

    def transfer_to_plc(self):
        ctime = datetime.now()
        ftime = int(ctime.strftime("%y%m%d") + "01")
        workorder = None
        selected_rows = self.schedule_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "Selezione Richiesta", "Seleziona almeno una WorkOrder da trasferire.")
            return

        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        uniids_to_delete = []

        try:
            # OPC UA operations: Connect to the OPC UA client once before the loop
            client = Client(f"opc.tcp://{ip}:4840")
            client.session_timeout = 30000
            client.connect()

            for selected_row_index in selected_rows:
                selected_row = selected_row_index.row()

                try:
                    # Step 1: Get the unique identifier from the selected row
                    sequence_id = self.schedule_table.item(int(selected_row), 1).text()
                    uniid = self.schedule_table.item(int(selected_row), 12).text()
                    uniids_to_delete.append(uniid)
                    
                    # Step 2: Fetch data from the SQL table using the unique identifier
                    with pyodbc.connect(conn_str) as conn:
                        cursor = conn.cursor()
                        
                        cursor.execute("SELECT TOP 1 WorkOrderID FROM RecipeDB.dbo.Reports ORDER BY WorkOrderID DESC")
                        result = cursor.fetchone()
                        
                        lastDB = result[0] if result else 0
                        laststamp = max(lastDB, ftime)
                        workorder = laststamp + 1 if laststamp >= ftime else ftime + 1

                        cursor.execute("UPDATE [RecipeDB].[dbo].[SchedulePayload] SET WorkOrderID = ? WHERE UniID = ?", workorder, uniid)
                        conn.commit()
                    
                        cursor.execute("SELECT * FROM [RecipeDB].[dbo].[SchedulePayload] WHERE UniID = ?", uniid)
                        payload_rows = cursor.fetchall()

                        cursor.execute("SELECT [BatchNumber],[RecipeID],[IngrSeqID],[IngrID],[IngrDesc],[IngrTypeID],[IngrTypeDesc],[StdPercentage],[TotalQty],[IngrStorage],[IngrStorageName],[IngrActive],[UniID],ROW_NUMBER() OVER (PARTITION BY [IngrTypeID] ORDER BY [IngrSeqID] ASC) AS [payload_seq] FROM [RecipeDB].[dbo].[SchedulePayloadIngrd] WHERE UniID = ?", uniid)
                        ingr_rows = cursor.fetchall()

                    datatags = {
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Codice"': {'Name': 'RecipeID', 'DataType': 'String'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."StampID"': {'Name': 'WorkOrderID', 'DataType': 'Int32'},#in case error 080424 and remove also [WorkOrderID] from cursor above 
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Descrizione"': {'Name': 'RecipeName', 'DataType': 'String'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."qTotale"': {'Name': 'TotalQty', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."WorkOrder"': {'Name': 'BatchNumber', 'DataType': 'String'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."IndirizzoPastorizzazione"': {'Name': 'PasteurizerID', 'DataType': 'String'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Selezione"."N_Serbatoio"': {'Name': 'AgeTankID', 'DataType': 'Int16'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Rework"': {'Name': 'IsRework', 'DataType': 'Boolean'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."pAcqua"': {'Name': 'WaterAutoVol', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Pastorizzatore"."T_Pastorizzazione"': {'Name': 'PTempPast', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Pastorizzatore"."T_Abbattimento"': {'Name': 'PTempBreak', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Pastorizzatore"."P_Omogeneizzatore1"': {'Name': 'PPressOmo', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Pastorizzatore"."V_Omogeneizzatore"': {'Name': 'PSpeedOmo', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Pastorizzatore"."DT_Pastorizzatore"': {'Name': 'PDeltaTPast', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Pastorizzatore"."DT_Abbattimento"': {'Name': 'PDeltaTBreak', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Pastorizzatore"."T_FineProduzione"': {'Name': 'PTempProdEnd', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Pastorizzatore"."L_Omogeneizzatore"': {'Name': 'PLiterOmo', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Pastorizzatore"."L_FineScarico"': {'Name': 'PLiterLoadEnd', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Pastorizzatore"."LIV_AcquaBTD"': {'Name': 'PLevelWater', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Blender"."Scelta"': {'Name': 'BMixTankID', 'DataType': 'Int16'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Blender"."T_Miscela"': {'Name': 'BTempMix', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Blender"."HoldingTime"': {'Name': 'BHoldingTime', 'DataType': 'Int32'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Blender"."DT_Miscela"': {'Name': 'BDeltaTMix', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Blender"."PausaCaricoPolveri"': {'Name': 'BPowderLoadPause', 'DataType': 'Int32'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Blender"."LavoroCaricoPolveri"': {'Name': 'BPowderLoadWork', 'DataType': 'Int32'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."TempoAgitatoreSlowP04"': {'Name': 'AgitatorTimeSlowP04', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."TempoAgitatoreFastP04"': {'Name': 'AgitatorTimeFastP04', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."TempoMartelliP04"': {'Name': 'HammerTimeP04', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Selezione"."N_Linea"': {'Name': 'lineid', 'DataType': 'Int16'},
                    }

                    tag_mappings = {
                        1: {  # liquidi
                            'Attivo' : {'Name': 'IngrActive', 'DataType': 'Boolean'},
                            'NomeProdotto': {'Name': 'IngrDesc', 'DataType': 'String'},
                            'Famiglia': {'Name': 'IngrStorage', 'DataType': 'Int16'},
                            'Quantità': {'Name': 'TotalQty', 'DataType': 'Float'},
                            'Percentuale': {'Name': 'StdPercentage', 'DataType': 'Float'},
                            # Add other variables for this type
                        },
                        2: {  # polveri
                            'Attivo' : {'Name': 'IngrActive', 'DataType': 'Boolean'},
                            'NomeProdotto': {'Name': 'IngrDesc', 'DataType': 'String'},
                            'SerbatoioP': {'Name': 'IngrStorage', 'DataType': 'Int16'},
                            'KgDaCaricare': {'Name': 'TotalQty', 'DataType': 'Float'},
                            'Percentuale': {'Name': 'StdPercentage', 'DataType': 'Float'},
                            # Add other variables for this type
                        },
                        3: {  # aromi
                            'Attivo' : {'Name': 'IngrActive', 'DataType': 'Boolean'},
                            'NomeProdotto': {'Name': 'IngrDesc', 'DataType': 'String'},
                            'KgDaCaricare': {'Name': 'TotalQty', 'DataType': 'Float'},
                            'Percentuale': {'Name': 'StdPercentage', 'DataType': 'Float'},
                            # Add other variables for this type
                        },
                        4: {  # semilav
                            'Attivo' : {'Name': 'IngrActive', 'DataType': 'Boolean'},
                            'NomeProdotto': {'Name': 'IngrDesc', 'DataType': 'String'},
                            'Quantità': {'Name': 'TotalQty', 'DataType': 'Float'},
                            'Percentuale': {'Name': 'StdPercentage', 'DataType': 'Float'},
                            # Add other variables for this type
                        },
                        6: {  # latte
                            'Attivo' : {'Name': 'IngrActive', 'DataType': 'Boolean'},
                            'NomeProdotto': {'Name': 'IngrDesc', 'DataType': 'String'},
                            'Famiglia': {'Name': 'IngrStorage', 'DataType': 'String'},
                            'Quantità': {'Name': 'TotalQty', 'DataType': 'Float'},
                            'Percentuale': {'Name': 'StdPercentage', 'DataType': 'Float'},
                            # Add other variables for this type
                        },
                        7: {  # zucchero
                            'Attivo' : {'Name': 'IngrActive', 'DataType': 'Boolean'},
                            'NomeProdotto': {'Name': 'IngrDesc', 'DataType': 'String'},
                            'SerbatoioP': {'Name': 'IngrStorage', 'DataType': 'Int16'},
                            'KgDaCaricare': {'Name': 'TotalQty', 'DataType': 'Float'},
                            'Percentuale': {'Name': 'StdPercentage', 'DataType': 'Float'},
                            # Add other variables for this type
                        },
                        8: {  # acqua
                            'Attivo' : {'Name': 'IngrActive', 'DataType': 'Boolean'},
                            'NomeProdotto': {'Name': 'IngrDesc', 'DataType': 'String'},
                            'Famiglia': {'Name': 'IngrStorage', 'DataType': 'Int16'},
                            'Quantità': {'Name': 'TotalQty', 'DataType': 'Float'},
                            'Percentuale': {'Name': 'StdPercentage', 'DataType': 'Float'},
                            # Add other variables for this type
                        }
                    }

                    ingr_seq_ids = [row.payload_seq for row in ingr_rows]

                    def get_tags_by_ingrtype(sequence_id, ingr_type_id, ingr_type_desc, ingr_storage, payload_seq, row):
                        base_tags = tag_mappings.get(ingr_type_id, {})
                        result = {}

                        for tag_suffix, tag_info in base_tags.items():
                            if hasattr(row, tag_info['Name']):
                                value = getattr(row, tag_info['Name'])
                                if tag_info['Name'] == 'IngrActive':
                                    value = bool(getattr(row, tag_info['Name']))

                                # Constructing tag string based on conditions
                                if "Liquidi" in ingr_type_desc and ingr_storage != 8:
                                    tag = f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Liquidi1"[{payload_seq}]."{".".join(tag_suffix.split())}"'
                                elif ingr_storage == 8:
                                    tag = f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Liquidi2"[1]."{".".join(tag_suffix.split())}"'
                                elif ingr_type_desc in ["Acqua", "Latte"]:
                                    tag = f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."{ingr_type_desc}"."{".".join(tag_suffix.split())}"'
                                elif ingr_storage == 99 and ingr_type_desc in ["Zucchero"]:
                                    tag = f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Zucchero"."{".".join(tag_suffix.split())}"'
                                else:
                                    tag = f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."{ingr_type_desc}"[{payload_seq}]."{".".join(tag_suffix.split())}"'

                                # Storing the value in the result dictionary with the constructed tag as the key
                                result[tag] = value

                        # The result dictionary is returned with all the tags and their corresponding values
                        return result

                    ingr_tags = []

                    for row in ingr_rows:
                        ingr_type_id = row.IngrTypeID
                        ingr_type_desc = row.IngrTypeDesc
                        ingr_storage = row.IngrStorage
                        payload_seq = row.payload_seq
                        tags = get_tags_by_ingrtype(sequence_id, ingr_type_id, ingr_type_desc, ingr_storage, payload_seq, row)
                        ingr_tags.append(tags)

                    def get_ua_variant_type(value):
                        if isinstance(value, bool):
                            return ua.VariantType.Boolean
                        elif isinstance(value, int):
                            return ua.VariantType.Int16
                        elif isinstance(value, float):
                            return ua.VariantType.Float
                        else:
                            return ua.VariantType.String

                    # Transfer data tags
                    for tag, column_info in datatags.items():
                        column_name = column_info['Name']
                        if hasattr(payload_rows[0], column_name):
                            value = getattr(payload_rows[0], column_name)
                            variant_type_str = column_info['DataType']

                            if variant_type_str == 'String':
                                value = str(value)
                            elif variant_type_str == 'Int16':
                                try:
                                    value = int(value)  # Ensure the value is an integer
                                except ValueError as e:
                                    error_details = traceback.format_exc()
                                    QMessageBox.warning(self, "Trasferimento Falito", f"Si è verificato un errore: {tag},{e},{error_details}")
                                    continue

                            # Set the node value
                            try:
                                variant_type_enum = getattr(ua.VariantType, variant_type_str)
                                data_value = ua.DataValue(ua.Variant(value, variant_type_enum))
                                node = client.get_node(tag)
                                node.set_value(data_value)
                            except Exception as e:
                                error_details = traceback.format_exc()
                                QMessageBox.warning(self, "Trasferimento Falito", f"Si è verificato un errore: {tag},{e},{error_details}")

                    # Transfer ingredient tags
                    for tag_dict in ingr_tags:
                        for tag, value in tag_dict.items():
                            try:
                                # Determine the correct UA Variant Type
                                variant_type = get_ua_variant_type(value)
                                data_value = ua.DataValue(ua.Variant(value, variant_type))
                                node = client.get_node(tag)
                                node.set_value(data_value)
                            except Exception as e:
                                error_details = traceback.format_exc()
                                QMessageBox.warning(self, "Trasferimento Falito", f"Si è verificato un errore: {tag},{e},{error_details}")

                    # Get the data from payload_rows before the loop, assuming all ingredients share the same values
                    payload_row = payload_rows[0]
                    LineID = payload_row.lineid
                    SequenceID = payload_row.SequenceID
                    WorkOrderID = payload_row.WorkOrderID
                    RecipeID = payload_row.RecipeID
                    RecipeName = payload_row.RecipeName
                    RecTotalQty = payload_row.TotalQty
                    BatchNumber = payload_row.BatchNumber
                    PasteurizerID = payload_row.PasteurizerID
                    AgeTankID = payload_row.AgeTankID
                    MixTankID = payload_row.BMixTankID
                    UniID = payload_row.UniID

                    # Open the connection once before the loop
                    with pyodbc.connect(conn_str) as conn:
                        cursor = conn.cursor()

                        # Execute the update once, outside the loop for ingr_rows
                        update_query = """
                        UPDATE [RecipeDB].[dbo].[Schedule]
                        SET [sc_status] = 1, [sc_transferred] = GETDATE()
                        WHERE [UniID] = ?
                        """
                        cursor.execute(update_query, UniID)

                        # Iterate over each ingredient row
                        for row in ingr_rows:
                            IngrSeqID = row.IngrSeqID
                            IngrDesc = row.IngrDesc
                            IngrTypeID = row.IngrTypeID
                            IngrTypeDesc = row.IngrTypeDesc
                            IngrStorage = row.IngrStorage
                            IngrStorageName = row.IngrStorageName
                            IngrID = row.IngrID
                            StdPercentage = row.StdPercentage
                            TotalQty = row.TotalQty

                            insert_query = """
                            INSERT INTO dbo.Reports (LineID,SequenceID,WorkOrderID,RecipeID,RecipeName,RecTotalQty,BatchNumber,
                            PasteurizerID,AgeTankID,MixTankID,IngrSeqID,IngrDesc,IngrTypeID,IngrTypeDesc,IngrStorage,IngrStorageName,
                            StdPercentage,TotalQty,EffectiveQty,Variance,TimeInserted,TimeUpdated,TimeCompleted,UniID,IngrID,IngrCode) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, GETDATE(), GETDATE(), NULL,?,?,(SELECT im_code FROM RecipeDB.dbo.IngredientMaster WHERE im_ingredientid = ?))
                            """
                            # Execute the insert query for each row in ingr_rows
                            cursor.execute(insert_query, (LineID, SequenceID, WorkOrderID, RecipeID, RecipeName, RecTotalQty, BatchNumber,
                                                        PasteurizerID, AgeTankID, MixTankID, IngrSeqID, IngrDesc, IngrTypeID, IngrTypeDesc,
                                                        IngrStorage, IngrStorageName, StdPercentage, TotalQty, UniID, IngrID, IngrID))

                        cursor.execute("DELETE FROM RecipeDB.dbo.SchedulePayload WHERE UniID = ?", uniid)
                        cursor.execute("DELETE FROM RecipeDB.dbo.SchedulePayloadIngrd WHERE UniID = ?", uniid)
                        conn.commit()

                    QMessageBox.information(self, "Successo", "WorkOrder trasferita al PLC con successo.")

                except Exception as e:
                    error_details = traceback.format_exc()
                    QMessageBox.warning(self, "Trasferimento Falito", f"Si è verificato un errore: {e},{error_details}")

            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                for uniid in uniids_to_delete:
                    cursor.execute("DELETE FROM RecipeDB.dbo.Schedule WHERE UniID = ?", uniid)
                    conn.commit()

            self.refresh_schedule_list()
            client.disconnect()  # Disconnect the OPC UA client once after the loop

        except Exception as e:
            error_details = traceback.format_exc()
            QMessageBox.warning(self, "Trasferimento Falito", f"Si è verificato un errore: {e},{error_details}")

#--------------------------------------------------------------------END OF SCHEDULE FUNCTIONS/HMI
#--------------------------------------------------------------------BEGIN OF SCHEDULE LINEA D FUNCTIONS/HMI

    def populate_recipe_combosD(self):
        self.recipeD_no_combo.clear()
        self.recipeD_name_combo.clear()
        self.originalD_recipe_items.clear()
        lineD_combo_text = self.line_combo.currentText()
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT rm_recipeid, rm_description FROM RecipeDB.dbo.RecipeMaster WHERE rm_line = 'D'")
        for recipe_id, recipe_name in cursor:
            self.recipeD_no_combo.addItem(str(recipe_id), recipe_id)
            self.recipeD_name_combo.addItem(recipe_name)
            self.originalD_recipe_items.append((str(recipe_id), recipe_name))
        conn.close

    def on_recipe_no_combo_changedD(self):
        selected_index = self.recipeD_no_combo.currentIndex()
        self.recipeD_name_combo.setCurrentIndex(selected_index)
        #self.load_ingredients()

        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        query = "SELECT rm_patemperature, rm_holdingtime, rm_omospeed, rm_omopress FROM RecipeDB.dbo.RecipeMaster WHERE rm_recipeid = ?"
        cursor.execute(query, (selected_index))
        
        result = cursor.fetchone()

        cursor.close()
        conn.close()
    
    def on_recipe_name_combo_changedD(self):
        selected_index = self.recipeD_name_combo.currentIndex()
        self.recipeD_no_combo.setCurrentIndex(selected_index)
        selected_recipe_id = self.recipeD_no_combo.currentData()
        #self.load_ingredients()

        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        try:
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                query = "SELECT rm_patemperature, rm_omopress, rm_omopress2 FROM RecipeDB.dbo.RecipeMaster WHERE rm_recipeid = ?"
                cursor.execute(query, selected_recipe_id)

                result = cursor.fetchone()

                if result:
                    self.pastD_field1.setText(str(result[0]))
                    self.pastD_field10.setText(str(result[1]))
                    self.pastD_field11.setText(str(result[2]))
                else:
                    self.reset_fieldsD()

        except pyodbc.Error as e:
            print(f"Database error: {e}")
            self.reset_fieldsD()
        #self.load_ingredients()

    def reset_fieldsD(self):
        self.past_field1.setText("88")
        self.past_field10.setText("150")
        self.past_field11.setText("30")

    def sfilter_comboD(self):
        filter_text = self.sfilterD_edit.text().lower()
        
        # Clear both combo boxes
        self.recipeD_no_combo.clear()
        self.recipeD_name_combo.clear()

        # Filter and add items based on the original items list
        for recipe_id, recipe_name in self.originalD_recipe_items:
            if filter_text in recipe_id.lower() or filter_text in recipe_name.lower():
                self.recipeD_no_combo.addItem(recipe_id)
                self.recipeD_name_combo.addItem(recipe_name)

        # Connect the combo box signals after adding items
        self.recipeD_no_combo.currentIndexChanged.connect(self.on_recipe_no_combo_changedD)
        self.recipeD_name_combo.currentIndexChanged.connect(self.on_recipe_name_combo_changedD)

    def populate_mix_tank_comboD(self):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT mtm_description FROM RecipeDB.dbo.MixTankMaster")
        for row in cursor.fetchall():
            self.mixD_tank_combo.addItem(row[0])  # Add each mix tank description to the combo box
        conn.close()
    
    def populate_age_tank_comboD(self):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT atm_description FROM RecipeDB.dbo.AgeTankMaster WHERE atm_line = 'D'")
        for row in cursor.fetchall():
            self.ageD_tank_combo.addItem(row[0])  # Add each age tank description to the combo box
        conn.close()

    def load_ingredientsD(self):
        selected_recipe_id = self.recipeD_no_combo.currentText()
        quantity = 1
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = """
            SELECT ri.ri_recipeid, ia.ia_description, im.im_code, im.im_description, CAST(ri.ri_percentage AS DECIMAL(9,3)) as '%', CAST((ri.ri_percentage * ?) AS DECIMAL(9,3)) as Target
            FROM RecipeDB.dbo.RecipeIngredients ri
            JOIN RecipeDB.dbo.IngredientMaster im ON ri.ri_ingredientid = im.im_ingredientid
            JOIN RecipeDB.dbo.IngredientArea ia ON ia.ia_areaid = im.im_areaid
            WHERE ri.ri_recipeid = ?
            ORDER BY ri.ri_sequence ASC
        """
        cursor.execute(query, (quantity,selected_recipe_id))
        self.populate_ingredients_tableD(cursor)
        self.ingredientsD_table.resizeColumnsToContents()
        self.ingredientsD_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ingredientsD_table.horizontalHeader().setSectionResizeMode(5,QHeaderView.Stretch)
        conn.close()

    def populate_ingredients_tableD(self, cursor):
        self.ingredientsD_table.setRowCount(0)
        for row_index, row_data in enumerate(cursor):
            self.ingredientsD_table.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                if col_index in [5, 6]:
                    formatted_number = "{:.3f}".format(data)
                    item = QTableWidgetItem(formatted_number)
                else:
                    item = QTableWidgetItem(str(data))    
                self.ingredientsD_table.setItem(row_index, col_index, item)

    def populate_schedule_tableD(self):
        # Get the database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute('''SELECT [sc_line] as Line
        	  ,[sc_position] as Seq
              ,[sc_batchid] as WorkOrder
              ,[sc_status] as Status
              ,[sc_recipeid] as Ricetta
              ,[sc_quantity] as Quantità
              ,[sc_pasteuriserid] as Pastorizzatore
              ,[mtm].[mtm_description] as Blender
              ,[atm].[atm_description] as Serbatoio
              ,[sc_scheduled] as StampScheduled
              ,[sc_transferred] as StampTransfer
              ,[sc_completed] as StampComplete
              ,[UniID] as UIdentifier
          FROM [RecipeDB].[dbo].[Schedule] AS [sch]
          INNER JOIN
                [dbo].[MixTankMaster] AS [mtm] ON [sch].[sc_mixtankid] = [mtm].[mtm_tankid]
          INNER JOIN
                [dbo].[AgeTankMaster] AS [atm] ON [sch].[sc_agetankid] = [atm].[atm_tankid]
            WHERE sc_line = 'D'
            ORDER BY [sc_position] ASC''')
        
        # Fetch all the results
        results = cursor.fetchall()
        
        # Determine the number of rows and columns
        number_of_rows = len(results)
        if number_of_rows > 0:
            number_of_columns = len(results[0])
            self.scheduleD_table.setColumnCount(number_of_columns)
            self.scheduleD_table.setRowCount(number_of_rows)
            
            # Set the headers if needed
            headers = [description[0] for description in cursor.description]
            self.scheduleD_table.setHorizontalHeaderLabels(headers)
            header = self.scheduleD_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)
            self.scheduleD_table.resizeColumnsToContents()
            
            # Populate the table
            for row_number, row_data in enumerate(results):
                for column_number, data in enumerate(row_data):
                    self.scheduleD_table.setItem(row_number, column_number, QTableWidgetItem(str(data)))
        
        # Close the cursor and connection
        cursor.close()
        conn.close

    def refresh_schedule_listD(self):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        cursor.execute('''SELECT [sc_line] as Line
                    ,[sc_position] as Seq
                    ,[sc_batchid] as WorkOrder
                    ,[sc_status] as Status
                    ,[sc_recipeid] as Ricetta
                    ,[sc_quantity] as Quantità
                    ,[sc_pasteuriserid] as Pastorizzatore
                    ,[mtm].[mtm_description] as Blender
                    ,[atm].[atm_description] as Serbatoio 
                    ,[sc_scheduled] as StampScheduled
                    ,[sc_transferred] as StampTransfer
                    ,[sc_completed] as StampComplete
                    ,[UniID] as UIdentifier
                FROM [RecipeDB].[dbo].[Schedule] AS [sch]
                INNER JOIN
                        [dbo].[MixTankMaster] AS [mtm] ON [sch].[sc_mixtankid] = [mtm].[mtm_tankid]
                INNER JOIN
                        [dbo].[AgeTankMaster] AS [atm] ON [sch].[sc_agetankid] = [atm].[atm_tankid]
                    WHERE sc_line = 'D'
                    ORDER BY [sc_position] ASC''')

        # Fetch all the results
        results = cursor.fetchall()

        # Determine the number of rows and columns
        number_of_rows = len(results)
        number_of_columns = len(results[0]) if number_of_rows > 0 else 0

        # Set the horizontal header labels
        headers = [description[0] for description in cursor.description]
        self.scheduleD_table.setColumnCount(number_of_columns)
        self.scheduleD_table.setRowCount(number_of_rows)
        self.scheduleD_table.setHorizontalHeaderLabels(headers)
        self.scheduleD_table.resizeColumnsToContents()

        # Set the column resize mode to Stretch
        header = self.scheduleD_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Populate the table if there are rows
        if number_of_rows > 0:
            for row_number, row_data in enumerate(results):
                for column_number, data in enumerate(row_data):
                    self.scheduleD_table.setItem(row_number, column_number, QTableWidgetItem(str(data)))

        # Close the cursor and connection
        cursor.close()
        conn.close()

    def calculate_target_quantitiesD(self):
        quantity = self.quantityD_field.text()
        #if not quantity or not quantity.isdigit():
        #    QMessageBox.warning(self, "Errore", "Inserisci prima una quantità valida.")
        #    return
        
        selected_recipe_id = self.recipeD_no_combo.currentText()
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = """
            SELECT ri.ri_recipeid, ia.ia_description, im.im_code, im.im_description, CAST(ri.ri_percentage AS DECIMAL(9,3)) as '%', CAST((ri.ri_percentage * CAST(? AS DECIMAL(9,3))) / 100 AS DECIMAL(10, 2)) as Target
            FROM RecipeDB.dbo.RecipeIngredients ri
            JOIN RecipeDB.dbo.IngredientMaster im ON ri.ri_ingredientid = im.im_ingredientid
            JOIN RecipeDB.dbo.IngredientArea ia ON ia.ia_areaid = im.im_areaid
            WHERE ri.ri_recipeid = ?
            ORDER BY ri.ri_sequence ASC
        """
        cursor.execute(query, (quantity,selected_recipe_id))
        self.populate_ingredients_tableD(cursor)
        self.ingredientsD_table.resizeColumnsToContents()
        self.ingredientsD_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ingredientsD_table.horizontalHeader().setSectionResizeMode(5,QHeaderView.Stretch)
        conn.close()
        
    def get_selected_ingredientsD(self):
        selected_ingredients = []
        for row in range(self.ingredientsD_table.rowCount()):
            # Initialize ingredient_data with default values
            ingredientD_data = {
                "recipe_id": "",
                "ingredient_type": "",
                "ingredient_id": "",
                "description": "",
                "standard_percentage": "",
                "total_qty": ""
            }
            for col, key in enumerate(ingredientD_data.keys()):
                item = self.ingredientsD_table.item(row, col)
                if item is not None:
                    ingredientD_data[key] = item.text()
            selected_ingredients.append(ingredientD_data)
        return selected_ingredients  
        
    def add_to_scheduleD(self):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Step 1a: Collect values from the UI
        line = self.lineD_combo.currentText()
        recipe_no = self.recipeD_no_combo.currentText()
        recipe_desc = self.recipeD_name_combo.currentText()
        quantity = self.quantityD_field.text()
        qtysb = self.quantitysbD_field.text()
        mix_tank_description = self.mixD_tank_combo.currentText()
        sc_mixtankid = self.get_mixtankidD(mix_tank_description)
        age_tank_description = self.ageD_tank_combo.currentText()
        sc_agetankid = self.get_agetankidD(age_tank_description)
        water_percent = self.waterD_percent_field.text()
        cooling_temp = self.coolingD_temp_field.text()
        ptm = self.pastD_field1.text()
        dtm = cooling_temp
        hp1 = self.pastD_field10.text()
        hp2 = self.pastD_field11.text()
        try:
            hot = int(self.blenD_field4.text()) * 60000
        except ValueError:
            hot = None
        puv = self.pastD_field8.text()
        azs = self.blenD_field7.text()
        ags = self.blenD_field8.text()
        ams = self.blenD_field9.text()
        btm = self.blenD_field10.text()
        mtp = self.blenD_field1.text()     
        rework = hos= pdt= ddt= ept= hov= elv= bwl= mdt= spl= wpl= ats= atf = hmt =0  
    
        # Step 2: Generate sc_batchid
        sc_batchid = self.workorderD_txt.text()

        if not all([sc_batchid, line, recipe_no, recipe_desc, quantity, qtysb, mix_tank_description, age_tank_description, water_percent, cooling_temp, ptm, hp1, hp2, hot, puv, azs, ags, ams, mtp]):
            QMessageBox.warning(self, "Attenzione", "Inserire tutti i valori prima di aggiungere alla programmazione.")
            return
    
        # Step 3: Calculate sc_position
        try:
            cur_position = self.get_next_positionD()
            cursor.execute("SELECT [sc_position] FROM [RecipeDB].[dbo].[Schedule]")
            avai_positions = [row[0] for row in cursor.fetchall()]
            next_position = next((pos for pos in cur_position if pos not in avai_positions), None)
            if next_position is not None:
                sc_position = next_position  # Use the current position if it's available
            else:
                QMessageBox.information(self, "Attenzione", "Nessuna posizione disponibile nella coda del Software PLC. Aspettare la liberazione di un posto o cancellare alcuna WorkOrder del Software PLC Supervisorio.")
                return
        except Exception as e:
            error_details = traceback.format_exc()
            QMessageBox.warning(self, "Attenzione", f"La connessione verso PLC per ottenere la posizione non è andata a buon fine. {e},{error_details}")
            return
        #sc_position = 1 #tooth

        workorder = 999999

        # Step 4: Determine sc_pasteuriserid based on line
        pasteuriserid_mapping = {"B": 2, "C": 3, "D": 4}
        sc_pasteuriserid = pasteuriserid_mapping.get(line, 0)
    
        # Step 5: Get sc_actfat and sc_actsolid from RecipeMaster
        sc_actfat, sc_actsolid = self.get_fat_and_solid_valuesD(recipe_no)

        #Get the Ingredients for Schedule
        selected_ingredients = self.get_selected_ingredientsD()

        #Generate unique identifier
        uniid = str(uuid.uuid4())
    
        # Step 6: Prepare and execute the SQL insert statement
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        try:
            cursor = conn.cursor()
            insert_sql = """
            INSERT INTO dbo.Schedule (
                sc_batchid, sc_line, sc_position, sc_status, sc_recipeid, sc_quantity,
                sc_pasteuriserid, sc_mixtankid, sc_agetankid, sc_autowaterpc, 
                sc_tanktemperature, sc_recovery, sc_colour, sc_actfat, sc_actsolid, 
                sc_reworkqty, sc_reworkfat, sc_reworksolid, sc_transferred, 
                sc_completed, sc_adjusted, sc_waterbatch, sc_scheduled, UniID
            ) VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?, 0, 0, NULL, NULL, 0, 0, GETDATE(), ?)
            """
        
            cursor.execute(insert_sql, (
                sc_batchid, line, sc_position, recipe_no, quantity,
                sc_pasteuriserid, sc_mixtankid, sc_agetankid, water_percent, 
                cooling_temp, sc_actfat, sc_actsolid, rework, uniid
            ))

            insert_sql = """
            INSERT INTO dbo.SchedulePayload (
                SequenceID,WorkOrderID,RecipeID,RecipeName,TotalQty,BatchNumber,PasteurizerID,AgeTankID,IsRework,WaterAutoVol,PTempPast,PTempBreak,
                PPressOmo,PSpeedOmo,PDeltaTPast,PDeltaTBreak,PTempProdEnd,PLiterOmo,PLiterLoadEnd,PLevelWater,BMixTankID,BTempMix,BHoldingTime,
                BDeltaTMix,BPowderLoadPause,BPowderLoadWork,AgitatorTimeSlowP04,AgitatorTimeFastP04,HammerTimeP04,lineid,linename,UniID,QtaStBatch,PPressOmo2,LivIniPurea,VelAgGlu,VelAgMan,VelAgZuc,BTempMat
            ) VALUES (
                ISNULL((SELECT MAX(SequenceID) FROM dbo.SchedulePayload), 0) + 1,
                ?,
                ?, ?, ?, ?, 
                (SELECT p_description FROM dbo.Pasteurisers WHERE p_line = CAST(? AS VARCHAR)), 
                (SELECT atm_tankid FROM dbo.AgeTankMaster WHERE atm_description = CAST(? AS VARCHAR)),
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                (SELECT mtm_tankid FROM dbo.MixTankMaster WHERE mtm_description = CAST(? AS VARCHAR)), 
                ?, ?, ?, ?, ?, ?, ?, ?,
                (SELECT p_pasteuriserid FROM dbo.Pasteurisers WHERE p_line = CAST(? AS VARCHAR)),
                (SELECT p_line FROM dbo.Pasteurisers WHERE p_line = CAST(? AS VARCHAR)),
                ?,?,?,?,?,?,?,?
                )
            """
            
            cursor.execute(insert_sql, (
                workorder, recipe_no, recipe_desc, quantity, sc_batchid, line, age_tank_description, rework, water_percent, ptm, dtm,
                hp1, hos, pdt, ddt, ept, hov, elv, bwl, mix_tank_description, mtp, hot,
                mdt, spl, wpl, ats, atf, hmt, line, line, uniid, qtysb, hp2, puv, azs, ags, ams, btm
            ))

            for ingredient in selected_ingredients:
                recipe_id = ingredient["recipe_id"]
                ingredient_type = ingredient["ingredient_type"]
                ingredient_id = ingredient["ingredient_id"]
                description = ingredient["description"]
                standard_percentage = ingredient["standard_percentage"]
                total_qty = ingredient["total_qty"]
                ingr_active = "True" 

                insert_ingredient_sql = """
                INSERT INTO dbo.SchedulePayloadIngrd (BatchNumber, RecipeID, 
                                                    IngrSeqID, 
                                                    IngrID, 
                                                    IngrDesc, 
                                                    IngrTypeID, 
                                                    IngrTypeDesc, StdPercentage, TotalQty, 
                                                    IngrStorage, 
                                                    IngrStorageName, 
                                                    IngrActive, UniID)
                VALUES (?, ?, 
                (SELECT ri_sequence FROM dbo.RecipeIngredients WHERE ri_code = CAST(? AS VARCHAR) and ri_recipeid = CAST(? AS VARCHAR)), 
                (SELECT im_ingredientid FROM dbo.IngredientMaster WHERE im_code = CAST(? AS VARCHAR)), 
                ?,
                (SELECT ia_areaid FROM dbo.IngredientArea WHERE ia_description = CAST(? AS VARCHAR)),
                ?, ?, ?, 
                (SELECT im_storage FROM dbo.IngredientMaster WHERE im_description = CAST(? AS VARCHAR)), 
                (SELECT im_storagename FROM dbo.IngredientMaster WHERE im_description = CAST(? AS VARCHAR)),
                ?,?)
                """
                cursor.execute(insert_ingredient_sql, (sc_batchid,recipe_id,ingredient_id,recipe_id,ingredient_id,description,ingredient_type,ingredient_type,standard_percentage,total_qty, description, description, ingr_active, uniid))
    
            conn.commit()
            
            #QMessageBox.information(self, "Successo", "WorkOrder inserita con successo alla programmazione.")
            self.refresh_schedule_listD() #bobbin
            self.ingredientsD_table.setRowCount(0)
        except Exception as e:
            error_details = traceback.format_exc()
            QMessageBox.warning(self, "Errore", f"Si è verificato un errore: {e},{error_details}")
            return
        finally: #tooth
            conn.close

    def get_next_positionD(self):
        client = Client(f"opc.tcp://{ip}:4840")
        client.session_timeout = 30000
        client.connect()

        next_positions = []
        for next_position in range(1, 11):
            nodest = f'ns=3;s="RecipeManagement"."Lista"[{next_position}]."Codice"'
            value = client.get_node(nodest).get_value()

            if value == "":
                next_positions.append(next_position)

        client.disconnect()

        return next_positions

    def get_fat_and_solid_valuesD(self, recipe_id):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
    
        # SQL query to retrieve rm_fat and rm_solid values
        query = "SELECT rm_fat, rm_solid FROM RecipeDB.dbo.RecipeMaster WHERE rm_recipeid = ?"
        cursor.execute(query, (recipe_id,))
    
        result = cursor.fetchone()
        sc_actfat, sc_actsolid = result if result else (0, 0)
    
        cursor.close()
        conn.close()
    
        return sc_actfat, sc_actsolid

    def get_mixtankidD(self, mix_tank_description):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
    
        query = "SELECT mtm_tankid FROM RecipeDB.dbo.MixTankMaster WHERE mtm_description = ?"
        cursor.execute(query, (mix_tank_description,))
    
        result = cursor.fetchone()
        sc_mixtankid = result[0] if result else None
    
        cursor.close()
        conn.close()
    
        return sc_mixtankid

    def get_agetankidD(self, age_tank_description):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
    
        query = "SELECT atm_tankid FROM RecipeDB.dbo.AgeTankMaster WHERE atm_description = ?"
        cursor.execute(query, (age_tank_description,))
    
        result = cursor.fetchone()
        sc_agetankid = result[0] if result else None
    
        cursor.close()
        conn.close()
    
        return sc_agetankid

    def delete_selected_scheduleD(self):
        selected_row = self.scheduleD_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima una WorkOrder da cancellare.")
            return
    
        # Assuming the Work Order (sc_batchid) is in a specific column, e.g., column 0
        work_order_item = self.scheduleD_table.item(selected_row, 2)
        uniid = self.scheduleD_table.item(selected_row, 12)
        if work_order_item is None:
            QMessageBox.warning(self, "Errore", "Nessuna WorkOrder trovata per la selezione.")
            return
    
        work_order = work_order_item.text()
        uniqueid = uniid.text()
    
        reply = QMessageBox.question(self, "Conferma Cancellazione", 
                                     f"Sei sicuro di voler cancellare WorkOrder ID {work_order}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            self.delete_schedule_from_dbD(uniqueid)
            self.refresh_schedule_listD()

    def delete_schedule_from_dbD(self, uniqueid):
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
    
        sch = "DELETE FROM RecipeDB.dbo.Schedule WHERE UniID = ?"
        cursor.execute(sch, (uniqueid))
        conn.commit()
        schpl = "DELETE FROM RecipeDB.dbo.SchedulePayload WHERE UniID = ?"
        cursor.execute(schpl, (uniqueid))
        conn.commit()
        schpli = "DELETE FROM RecipeDB.dbo.SchedulePayloadIngrd WHERE UniID = ?"
        cursor.execute(schpli, (uniqueid))
        conn.commit()
    
        cursor.close()
        conn.close()

    def up_selected_scheduleD(self):
        selected_row = self.schedule_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selezione Richiesta", "Selezionare prima una WorkOrder per spostare su.")
            return
        seq_ref_item = self.schedule_table.item(selected_row, 1)
        batch_ref_item = self.schedule_table.item(selected_row, 2)

        seq_ref = int(seq_ref_item.text())
        batch_ref = int(batch_ref_item.text())

        empty_pos = get_empty_positions()

        if seq_ref - 1 not in empty_pos:
            QMessageBox.warning(self, "Attenzione", "WorkOrder già è alla prima posizione disponibile.")
            return
        elif seq_ref == 1:
            QMessageBox.warning(self, "Attenzione", "WorkOrder già è alla prima posizione della lista.")
            return

        reply = QMessageBox.question(self, "Conferma",
                                    f"Sei sicuro di voler spostare la WorkOrder alla posizione {seq_ref - 1}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            seq_new = seq_ref - 1
            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            update_up = """
            UPDATE dbo.Schedule
            SET sc_position = ?
            WHERE sc_position = ?;

            UPDATE dbo.SchedulePayload
            SET SequenceID = ?
            WHERE SequenceID = ?;

            UPDATE dbo.Schedule
            SET sc_position = ?
            WHERE sc_batchid = ?;

            UPDATE dbo.SchedulePayload
            SET SequenceID = ?
            WHERE BatchNumber = ?;
            """
            cursor.execute(update_up, (seq_ref, seq_new, seq_ref, seq_new, seq_new, batch_ref, seq_new, batch_ref))
            conn.commit()
            self.refresh_schedule_listD()
      
    def down_selected_scheduleD(self):
        selected_row = self.scheduleD_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selezione Richiesta", "Selezionare prima una WorkOrder per spostare giù.")
            return
        seq_ref_item = self.scheduleD_table.item(selected_row, 1)
        batch_ref_item = self.scheduleD_table.item(selected_row, 2)

        seq_ref = int(seq_ref_item.text())
        batch_ref = int(batch_ref_item.text())

        empty_pos = get_empty_positions()

        if seq_ref + 1 not in empty_pos:
            QMessageBox.warning(self, "Attenzione", "WorkOrder già è all'ultima posizione disponibile.")
            return
        elif seq_ref == 10:
            QMessageBox.warning(self, "Attenzione", "WorkOrder già è all'ultima posizione dalla lista.")
            return

        reply = QMessageBox.question(self, "Conferma",
                                    f"Sei sicuro di voler spostare la WorkOrder alla posizione {seq_ref + 1}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            seq_new = seq_ref + 1
            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            update_up = """
            UPDATE dbo.Schedule
            SET sc_position = ?
            WHERE sc_position = ?;

            UPDATE dbo.SchedulePayload
            SET SequenceID = ?
            WHERE SequenceID = ?;

            UPDATE dbo.Schedule
            SET sc_position = ?
            WHERE sc_batchid = ?;

            UPDATE dbo.SchedulePayload
            SET SequenceID = ?
            WHERE BatchNumber = ?;
            """
            cursor.execute(update_up, (seq_ref, seq_new, seq_ref, seq_new, seq_new, batch_ref, seq_new, batch_ref))
            conn.commit()
            self.refresh_schedule_listD()

    def transfer_to_plcD(self):
        selected_rows = self.scheduleD_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "Selezione Richiesta", "Seleziona almeno una WorkOrder da trasferire.")
            return

        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        uniids_to_delete = []

        try:
            # OPC UA operations: Connect to the OPC UA client outside the loop
            client = Client(f"opc.tcp://{ip}:4840")
            client.session_timeout = 30000
            client.connect()  # Connect once outside the loop

            for selected_row_index in selected_rows:
                selected_row = selected_row_index.row()

                try:
                    # Step 1: Get the unique identifier from the selected row
                    sequence_id = self.scheduleD_table.item(int(selected_row), 1).text()
                    uniid = self.scheduleD_table.item(int(selected_row), 12).text()
                    uniids_to_delete.append(uniid)

                    # Step 2: Fetch data from the SQL table using the unique identifier
                    conn = pyodbc.connect(conn_str)
                    cursor = conn.cursor()
                    workorder = None
                    ctime = datetime.now()
                    ftime = int(ctime.strftime("%y%m%d") + "01")
                    cursor.execute("SELECT TOP 1 WorkOrderID FROM RecipeDB.dbo.Reports ORDER BY WorkOrderID DESC")
                    result = cursor.fetchone()
                    lastDB = result[0] if result else 0
                    laststamp = max(lastDB, ftime)
                    workorder = laststamp + 1 if laststamp >= ftime else ftime + 1

                    cursor.execute("UPDATE [RecipeDB].[dbo].[SchedulePayload] SET WorkOrderID = ? WHERE UniID = ?", workorder, uniid)
                    conn.commit()
                
                    cursor.execute("SELECT * FROM [RecipeDB].[dbo].[SchedulePayload] WHERE UniID = ?", uniid)
                    payload_rows = cursor.fetchall()

                    cursor.execute("SELECT [BatchNumber],[RecipeID],[IngrSeqID],[IngrID],[IngrDesc],[IngrTypeID],[IngrTypeDesc],[StdPercentage],[TotalQty],[IngrStorage],[IngrStorageName],[IngrActive],[UniID],ROW_NUMBER() OVER (PARTITION BY [IngrTypeID] ORDER BY [IngrSeqID] ASC) AS [payload_seq] FROM [RecipeDB].[dbo].[SchedulePayloadIngrd] WHERE UniID = ?", uniid)
                    ingr_rows = cursor.fetchall()

                    datatags = {
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Codice"': {'Name': 'RecipeID', 'DataType': 'String'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."StampID"': {'Name': 'WorkOrderID', 'DataType': 'Int32'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."WorkOrder"': {'Name': 'BatchNumber', 'DataType': 'String'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Descrizione"': {'Name': 'RecipeName', 'DataType': 'String'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."qTotale"': {'Name': 'TotalQty', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."qSottoBatch"': {'Name': 'QtaStBatch', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."pAcqua"': {'Name': 'WaterAutoVol', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."IndirizzoPastorizzazione"': {'Name': 'PasteurizerID', 'DataType': 'String'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Selezione"."N_Serbatoio"': {'Name': 'AgeTankID', 'DataType': 'Int16'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Blender"."Scelta"': {'Name': 'BMixTankID', 'DataType': 'Int16'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Pastorizzatore"."L_Purea"': {'Name': 'LivIniPurea', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Blender"."VelAgitatoreZ"': {'Name': 'VelAgZuc', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Blender"."VelAgitatoreG"': {'Name': 'VelAgGlu', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Blender"."VelAgitatoreM"': {'Name': 'VelAgMan', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Blender"."HoldingTime"': {'Name': 'BHoldingTime', 'DataType': 'Int32'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Blender"."T_Miscela"': {'Name': 'BTempMix', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Blender"."TempoMaturazione"': {'Name': 'BTempMat', 'DataType': 'Int16'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Pastorizzatore"."T_Pastorizzazione"': {'Name': 'PTempPast', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Pastorizzatore"."T_Abbattimento"': {'Name': 'PTempBreak', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Pastorizzatore"."P_Omogeneizzatore1"': {'Name': 'PPressOmo', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Pastorizzatore"."P_Omogeneizzatore2"': {'Name': 'PPressOmo2', 'DataType': 'Float'},
                        f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Selezione"."N_Linea"': {'Name': 'lineid', 'DataType': 'Int16'},
                    }

                    tag_mappings = {
                        1: {  # liquidi
                            'Attivo': {'Name': 'IngrActive', 'DataType': 'Boolean'},
                            'NomeProdotto': {'Name': 'IngrDesc', 'DataType': 'String'},
                            'Famiglia': {'Name': 'IngrStorage', 'DataType': 'Int16'},
                            'Quantità': {'Name': 'TotalQty', 'DataType': 'Float'},
                            'Percentuale': {'Name': 'StdPercentage', 'DataType': 'Float'},
                        },
                        9: {  # polveri
                            'Attivo': {'Name': 'IngrActive', 'DataType': 'Boolean'},
                            'NomeProdotto': {'Name': 'IngrDesc', 'DataType': 'String'},
                            'Famiglia': {'Name': 'IngrStorage', 'DataType': 'Int16'},
                            'Quantità': {'Name': 'TotalQty', 'DataType': 'Float'},
                            'Percentuale': {'Name': 'StdPercentage', 'DataType': 'Float'},
                        },
                        92: {  # aromi
                            'Attivo': {'Name': 'IngrActive', 'DataType': 'Boolean'},
                            'NomeProdotto': {'Name': 'IngrDesc', 'DataType': 'String'},
                            'KgDaCaricare': {'Name': 'TotalQty', 'DataType': 'Float'},
                            'Percentuale': {'Name': 'StdPercentage', 'DataType': 'Float'},
                        },
                        7: {  # semilav
                            'Attivo': {'Name': 'IngrActive', 'DataType': 'Boolean'},
                            'NomeProdotto': {'Name': 'IngrDesc', 'DataType': 'String'},
                            'Famiglia': {'Name': 'IngrStorage', 'DataType': 'Int16'},
                            'Quantità': {'Name': 'TotalQty', 'DataType': 'Float'},
                            'Percentuale': {'Name': 'StdPercentage', 'DataType': 'Float'},
                        },
                        999: {  # semilav
                            'Attivo': {'Name': 'IngrActive', 'DataType': 'Boolean'},
                            'NomeProdotto': {'Name': 'IngrDesc', 'DataType': 'String'},
                            'KgDaCaricare': {'Name': 'TotalQty', 'DataType': 'Float'},
                            'Percentuale': {'Name': 'StdPercentage', 'DataType': 'Float'},
                        }
                    }

                    def get_tags_by_ingrtype(sequence_id, ingr_attivo, ingr_type_id, ingr_storage, row, i, loop, aromifull):
                        base_tags = tag_mappings.get(ingr_storage, {})
                        result = {}
                        tag = None
                        for tag_suffix, tag_info in base_tags.items():
                            if hasattr(row, tag_info['Name']):
                                value = getattr(row, tag_info['Name'])
                                if tag_info['Name'] == 'IngrActive':
                                    value = bool(getattr(row, tag_info['Name']))

                                # Constructing tag string based on conditions
                                if ingr_storage == 7:
                                    tag = f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Liquidi1"[1]."{".".join(tag_suffix.split())}"'
                                elif ingr_storage == 9:
                                    tag = f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Liquidi1"[2]."{".".join(tag_suffix.split())}"'
                                elif ingr_storage == 1:
                                    tag = f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Acqua"."{".".join(tag_suffix.split())}"'
                                elif ingr_storage == 92:
                                    tag = f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Zucchero"."{".".join(tag_suffix.split())}"'
                                elif ingr_storage not in [1, 7, 92, 9] and not aromifull:
                                    tag = f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."AromiAPV"[{i}]."{".".join(tag_suffix.split())}"'
                                    loop += 1
                                elif ingr_storage not in [1, 7, 92, 9] and aromifull:
                                    if tag_suffix == "KgDaCaricare":
                                        tag_suffix = "Quantità"  # Change the tag_suffix to "Quantità" if it's "KgDaCaricare"
                                    tag = f'ns=3;s="RecipeManagement"."Lista"[{sequence_id}]."Semilavorati"[{i}]."{".".join(tag_suffix.split())}"'
                                    loop += 1

                                # Storing the value in the result dictionary with the constructed tag as the key
                                result[tag] = value

                                if loop == 4:
                                    i += 1
                                    loop = 0

                                if i == 10 and not aromifull:
                                    aromifull = True
                                    i = 1
                                elif i == 6 and aromifull:
                                    break  # Stop once we fill Semilavorati

                        # The result dictionary is returned with all the tags and their corresponding values
                        return result, i, loop, aromifull

                    ingr_tags = []
                    i = 1
                    loop = 0
                    aromifull = False  # Initialize aromifull here
                    for row in ingr_rows:
                        ingr_attivo = row.IngrActive
                        ingr_type_id = row.IngrTypeID
                        ingr_storage = row.IngrStorage
                        tags, i, loop, aromifull = get_tags_by_ingrtype(sequence_id, ingr_attivo, ingr_type_id, ingr_storage, row, i, loop, aromifull)
                        ingr_tags.append(tags)

                    def get_ua_variant_type(value):
                        if isinstance(value, bool):
                            return ua.VariantType.Boolean
                        elif isinstance(value, int):
                            return ua.VariantType.Int16
                        elif isinstance(value, float):
                            return ua.VariantType.Float
                        else:
                            return ua.VariantType.String

                    # Transfer data tags
                    for tag, column_info in datatags.items():
                        column_name = column_info['Name']
                        if hasattr(payload_rows[0], column_name):
                            value = getattr(payload_rows[0], column_name)
                            variant_type_str = column_info['DataType']

                            if variant_type_str == 'String':
                                value = str(value)
                            elif variant_type_str == 'Int16':
                                try:
                                    value = int(value)  # Ensure the value is an integer
                                except ValueError as e:
                                    error_details = traceback.format_exc()  # This will give you the stack trace.
                                    QMessageBox.warning(self, "Trasferimento Falito", f"Si è verificato un errore: {tag},{e},{error_details}")
                                    continue

                            # Set the node value
                            try:
                                variant_type_enum = getattr(ua.VariantType, variant_type_str)
                                data_value = ua.DataValue(ua.Variant(value, variant_type_enum))
                                node = client.get_node(tag)
                                node.set_value(data_value)
                            except Exception as e:
                                error_details = traceback.format_exc()
                                QMessageBox.warning(self, "Trasferimento Falito", f"Si è verificato un errore: {tag},{e},{error_details}")

                    # Transfer ingredient tags
                    for tag_dict in ingr_tags:
                        for tag, value in tag_dict.items():
                            try:
                                # Determine the correct UA Variant Type
                                variant_type = get_ua_variant_type(value)
                                data_value = ua.DataValue(ua.Variant(value, variant_type))
                                node = client.get_node(tag)
                                node.set_value(data_value)
                            except Exception as e:
                                error_details = traceback.format_exc()
                                QMessageBox.warning(self, "Trasferimento Falito", f"Si è verificato un errore: {tag},{e},{error_details}")

                    # Get the data from payload_rows before the loop, assuming all ingredients share the same values
                    payload_row = payload_rows[0]
                    LineID = payload_row.lineid
                    SequenceID = payload_row.SequenceID
                    WorkOrderID = payload_row.WorkOrderID
                    RecipeID = payload_row.RecipeID
                    RecipeName = payload_row.RecipeName
                    RecTotalQty = payload_row.TotalQty
                    BatchNumber = payload_row.BatchNumber
                    PasteurizerID = payload_row.PasteurizerID
                    AgeTankID = payload_row.AgeTankID
                    MixTankID = payload_row.BMixTankID
                    UniID = payload_row.UniID

                    # Open the connection once before the loop
                    with pyodbc.connect(conn_str) as conn:
                        cursor = conn.cursor()

                        # Execute the update once, outside the loop for ingr_rows
                        update_query = """
                        UPDATE [RecipeDB].[dbo].[Schedule]
                        SET [sc_status] = 1, [sc_transferred] = GETDATE()
                        WHERE [UniID] = ?
                        """
                        cursor.execute(update_query, UniID)

                        # Iterate over each ingredient row
                        for row in ingr_rows:
                            IngrSeqID = row.IngrSeqID
                            IngrDesc = row.IngrDesc
                            IngrTypeID = row.IngrTypeID
                            IngrStorage = row.IngrStorage
                            StdPercentage = row.StdPercentage
                            TotalQty = row.TotalQty

                            insert_query = """
                            INSERT INTO dbo.Reports (LineID,SequenceID,WorkOrderID,RecipeID,RecipeName,RecTotalQty,BatchNumber,
                            PasteurizerID,AgeTankID,MixTankID,IngrSeqID,IngrDesc,IngrTypeID,IngrStorage,
                            StdPercentage,TotalQty,EffectiveQty,Variance,TimeInserted,TimeUpdated,TimeCompleted,UniID) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,NULL, NULL, GETDATE(), GETDATE(), NULL,?)
                            """
                            # Execute the insert query for each row in ingr_rows
                            cursor.execute(insert_query, (LineID, SequenceID, WorkOrderID, RecipeID, RecipeName, RecTotalQty, BatchNumber,
                                                        PasteurizerID, AgeTankID, MixTankID, IngrSeqID, IngrDesc, IngrTypeID,
                                                        IngrStorage, StdPercentage, TotalQty, UniID))
                            
                        cursor.execute("DELETE FROM RecipeDB.dbo.SchedulePayload WHERE UniID = ?", uniid)
                        cursor.execute("DELETE FROM RecipeDB.dbo.SchedulePayloadIngrd WHERE UniID = ?", uniid)
                        conn.commit()

                    QMessageBox.information(self, "Successo", "WorkOrder trasferita al PLC con successo.")

                except Exception as e:
                    error_details = traceback.format_exc()
                    QMessageBox.warning(self, "Trasferimento Falito", f"Si è verificato un errore: {e},{error_details}")

            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                for uniid in uniids_to_delete:
                    cursor.execute("DELETE FROM RecipeDB.dbo.Schedule WHERE UniID = ?", uniid)
                    conn.commit()
                    
            self.refresh_schedule_listD()

            client.disconnect()  # Disconnect the OPC UA client once after the loop

        except Exception as e:
            error_details = traceback.format_exc()
            QMessageBox.warning(self, "Trasferimento Falito", f"Si è verificato un errore: {e},{error_details}")

#--------------------------------------------------------------------END OF SCHEDULE LINEA D FUNCTIONS/HMI
#--------------------------------------------------------------------BEGIN OF REPORT FUNCTIONS/HMI

    def filter_report(self, text):
        for row in range(self.report_table.rowCount()):
            item = self.report_table.item(row, 2)  # Get the item from column 2 of the current row
            if item is not None:  # Check if the item is not None
                is_match = text.lower() in item.text().lower()
            else:
                is_match = False  # If the item is None, there is no match
            self.report_table.setRowHidden(row, not is_match)

    def filter_time(self, time_str):
        if time_str == "Show All":
            for row in range(self.report_table.rowCount()):
                self.report_table.setRowHidden(row, False)
            return
        
        time = QTime.fromString(time_str, 'HH:mm:ss')
        for row in range(self.report_table.rowCount()):
            time_item = self.report_table.item(row, 11)  # Assuming column 11 holds the datetime
            if time_item:
                datetime_str = time_item.text()
                row_time = QTime.fromString(datetime_str.split(' ')[1], 'HH:mm:ss')
                self.report_table.setRowHidden(row, time != row_time)

    def on_date_changed(self, date):
        # Convert QDate to a suitable string format
        date_str = date.toString('yyyy-MM-dd')
        self.report_table.clearContents()
        self.report_table.setRowCount(0)
        self.populate_report_table(date_str + '%')
        self.populate_time_picker()

    def on_time_changed(self, time_str):
        self.filter_time(time_str)

    def populate_report_table(self,datepick):
        # Get the database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute('''SELECT 
                        [LineID] as Linea,
                        [WorkOrderID] as Batch,
                        [BatchNumber] as WorkOrder,
                        [RecipeID] as Ricetta,
                        [RecipeName] as Descrizione,
                        [RecTotalQty] as Quantità,
                        [PasteurizerID] as [Pasteurizatore],
                        [AgeTankID] as [Serbatoio], 
                        [MixTankID] as Blender,
                        MAX([TimeInserted]) as Programmato,
                        MAX([TimeUpdated]) as Aggiornato,
                        MAX([TimeCompleted]) as Completato
                    FROM [RecipeDB].[dbo].[Reports]
                    WHERE 
                        TimeCompleted IS NOT NULL 
                        AND TimeCompleted LIKE ?
                    GROUP BY 
                        [LineID],
                        [WorkOrderID],
                        [BatchNumber],
                        [RecipeID],
                        [RecipeName],
                        [RecTotalQty],
                        [PasteurizerID],
                        [AgeTankID],
                        [MixTankID]
                    ORDER BY 
                        MAX([TimeCompleted]) DESC;
                    ''',datepick)
        
        # Fetch all the results
        results = cursor.fetchall()
        
        # Determine the number of rows and columns
        number_of_rows = len(results)
        if number_of_rows > 0:
            number_of_columns = len(results[0])
            self.report_table.setColumnCount(number_of_columns)
            self.report_table.setRowCount(number_of_rows)
            
            # Set the headers if needed
            headers = [description[0] for description in cursor.description]
            self.report_table.setHorizontalHeaderLabels(headers)
            header = self.report_table.horizontalHeader()
            self.report_table.resizeColumnsToContents()
            header.setSectionResizeMode(QHeaderView.Stretch)
            
            # Populate the table
            for row_number, row_data in enumerate(results):
                for column_number, data in enumerate(row_data):
                    self.report_table.setItem(row_number, column_number, QTableWidgetItem(str(data)))
        
        # Close the cursor and connection
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        cursor.close()
        conn.close

    def populate_time_picker(self):
        self.time_picker.clear()
        times = {"Show All"}  # Add "Show All" option
        for row in range(self.report_table.rowCount()):
            datetime_item = self.report_table.item(row, 11)  # Assuming column 11 holds the "Completato" datetime
            if datetime_item:
                datetime_str = datetime_item.text()
                if ' ' in datetime_str:
                    time_str = datetime_str.split(' ')[1]  # Extract the time part
                    times.add(time_str)
        for time_str in sorted(times):
            self.time_picker.addItem(time_str)
        self.time_picker.setCurrentText("Show All") 

    def generate_plan_report(self): #newrep
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Step 1a: Collect values from the UI
        line = self.line_combo.currentText()
        recipe_no = self.recipe_no_combo.currentText()
        recipe_desc = self.recipe_name_combo.currentText()
        quantity = self.quantity_field.text()
        mix_tank_description = self.mix_tank_combo.currentText()
        sc_mixtankid = self.get_mixtankid(mix_tank_description)
        age_tank_description = self.age_tank_combo.currentText()
        sc_agetankid = self.get_agetankid(age_tank_description)
        water_percent = self.water_percent_field.text()
        cooling_temp = self.cooling_temp_field.text()
        rework = 1 if self.rework_yes_radio.isChecked() else 0

        # Step 1b: Collect values from the Static UI
        ats = self.p04_field1.text()
        atf = self.p04_field2.text()
        hmt = self.p04_field3.text()
        ptm = self.past_field1.text()
        pdt = self.past_field2.text() #su
        dtm = cooling_temp
        ddt = self.past_field4.text()
        ept = self.past_field5.text()
        elv = self.past_field6.text()
        bwl = self.past_field7.text()
        puv = self.past_field8.text()
        hov = self.past_field9.text()
        hp1 = self.past_field10.text() #su
        hp2 = self.past_field11.text()
        hos = self.past_field12.text() #su
        mtp = self.blen_field1.text()
        mdt = self.blen_field2.text()
        agt = self.blen_field3.text()
        try:
            hot = int(self.blen_field4.text()) * 60000
        except ValueError:
            hot = None
        spl = self.blen_field5.text()
        wpl = self.blen_field6.text()
        azs = self.blen_field7.text()
        ags = self.blen_field8.text()
        ams = self.blen_field9.text()
    
        # Step 2: Generate sc_batchid
        sc_batchid = self.workorder_txt.text()

        if not all([sc_batchid, line, recipe_no, recipe_desc, quantity, mix_tank_description, age_tank_description, water_percent, cooling_temp, ptm, hp1, hot]):
            QMessageBox.warning(self, "Attenzione", "Inserire tutti i valori prima di aggiungere alla programmazione.")
            return
    
        # Step 3: Calculate sc_position
        sc_position = 1 #tooth

        current_date = datetime.now().strftime("%y%m%d")
        workorder = 999999

        # Step 4: Determine sc_pasteuriserid based on line
        pasteuriserid_mapping = {"B": 2, "C": 3, "D": 4}
        sc_pasteuriserid = pasteuriserid_mapping.get(line, 0)
    
        # Step 5: Get sc_actfat and sc_actsolid from RecipeMaster
        sc_actfat, sc_actsolid = self.get_fat_and_solid_values(recipe_no)

        #Get the Ingredients for Schedule
        selected_ingredients = self.get_selected_ingredients()

        #Generate unique identifier
        uniid = str(uuid.uuid4())
        dateraw = str(datetime.now())
    
        # Step 6: Prepare and execute the SQL insert statement
        try:
            for ingredient in selected_ingredients:
                recipe_id = ingredient["recipe_id"]
                ingredient_type = ingredient["ingredient_type"]
                ingredient_id = ingredient["ingredient_id"]
                description = ingredient["description"]
                standard_percentage = ingredient["standard_percentage"]
                total_qty = ingredient["total_qty"]
                ingr_active = "True" 

                insert_query = """
                    INSERT INTO dbo.Reports (LineID,SequenceID,WorkOrderID,RecipeID,RecipeName,RecTotalQty,BatchNumber,PasteurizerID,
                    AgeTankID,MixTankID,IngrSeqID,IngrDesc,IngrTypeID,IngrTypeDesc,IngrStorage,IngrStorageName,
                    StdPercentage,TotalQty,EffectiveQty,Variance,TimeInserted,TimeUpdated,TimeCompleted,UniID,IngrID,IngrCode) 
                    VALUES ((SELECT p_pasteuriserid FROM dbo.Pasteurisers WHERE p_line = CAST(? AS VARCHAR)), ?, ?, ?, ?, ?, ?, (SELECT p_description FROM dbo.Pasteurisers WHERE p_line = CAST(? AS VARCHAR)), 
                    (SELECT atm_tankid FROM dbo.AgeTankMaster WHERE atm_description = CAST(? AS VARCHAR)), 
                    (SELECT mtm_tankid FROM dbo.MixTankMaster WHERE mtm_description = CAST(? AS VARCHAR)), 
                    (SELECT ri_sequence FROM dbo.RecipeIngredients WHERE ri_code = CAST(? AS VARCHAR) and ri_recipeid = CAST(? AS VARCHAR)),
                    ?, 
                    (SELECT ia_areaid FROM dbo.IngredientArea WHERE ia_description = CAST(? AS VARCHAR)), 
                    ?, 
                    (SELECT im_storage FROM dbo.IngredientMaster WHERE im_description = CAST(? AS VARCHAR)), 
                    (SELECT im_storagename FROM dbo.IngredientMaster WHERE im_description = CAST(? AS VARCHAR)), 
                    ?, ?, 
                    NULL, NULL, GETDATE(), GETDATE(), NULL,?,(SELECT im_ingredientid FROM RecipeDB.dbo.IngredientMaster WHERE im_code = ?),?)
                    """
                # Execute the insert query for each row in ingr_rows
                cursor.execute(insert_query, (line, sc_position, workorder, recipe_id, recipe_desc, quantity, sc_batchid, line,
                                                age_tank_description, mix_tank_description, ingredient_id, recipe_id, description, ingredient_type, ingredient_type,
                                                description, description, standard_percentage, total_qty, uniid, ingredient_id, ingredient_id))
                        
                conn.commit()

            try:
                try:
                    # Use the correct format string that includes the date and time
                    date = datetime.strptime(dateraw, '%Y-%m-%d %H:%M:%S.%f').strftime('%d/%m/%Y')
                except ValueError:
                    try:
                        # If the first parsing fails, try without microseconds
                        date = datetime.strptime(dateraw, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                    except ValueError as e:
                        # Handle the error if it still occurs
                        QMessageBox.critical(self, "Errore", f"Si è verificato un errore:\n{str(e)}")
                        return

                # Construct the report URL with parameters
                report_url = f"http://{encoded_username}:{encoded_password}@{url}/Pages/ReportViewer.aspx?%2fPreProductionReport&rs:Command=Render&Data={date}&WorkOrder={sc_batchid}&RecipeId={recipe_id}&StampID={workorder}"
                
                # Open the report URL in a web browser
                webbrowser.open(report_url)

                time.sleep(30)

                conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()
                query = """DELETE FROM dbo.Reports WHERE WorkOrderID = ? AND RecipeID = ?"""
                cursor.execute(query, (workorder, recipe_id))
                conn.commit()

            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Si è verificato un errore:\n{str(e)}")
                return   
            
        except Exception as e:
            error_details = traceback.format_exc()
            QMessageBox.warning(self, "Errore", f"Si è verificato un errore: {e},{error_details}")
            return
        finally: #tooth
            conn.close

    def generate_plan_reportD(self): #newrep
        conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Step 1a: Collect values from the UI
        line = self.line_combo.currentText()
        recipe_no = self.recipe_no_combo.currentText()
        recipe_desc = self.recipe_name_combo.currentText()
        quantity = self.quantity_field.text()
        mix_tank_description = self.mix_tank_combo.currentText()
        sc_mixtankid = self.get_mixtankid(mix_tank_description)
        age_tank_description = self.age_tank_combo.currentText()
        sc_agetankid = self.get_agetankid(age_tank_description)
        water_percent = self.water_percent_field.text()
        cooling_temp = self.cooling_temp_field.text()
        rework = 1 if self.rework_yes_radio.isChecked() else 0

        # Step 1b: Collect values from the Static UI
        ats = self.p04_field1.text()
        atf = self.p04_field2.text()
        hmt = self.p04_field3.text()
        ptm = self.past_field1.text()
        pdt = self.past_field2.text() #su
        dtm = cooling_temp
        ddt = self.past_field4.text()
        ept = self.past_field5.text()
        elv = self.past_field6.text()
        bwl = self.past_field7.text()
        puv = self.past_field8.text()
        hov = self.past_field9.text()
        hp1 = self.past_field10.text() #su
        hp2 = self.past_field11.text()
        hos = self.past_field12.text() #su
        mtp = self.blen_field1.text()
        mdt = self.blen_field2.text()
        agt = self.blen_field3.text()
        try:
            hot = int(self.blen_field4.text()) * 60000
        except ValueError:
            hot = None
        spl = self.blen_field5.text()
        wpl = self.blen_field6.text()
        azs = self.blen_field7.text()
        ags = self.blen_field8.text()
        ams = self.blen_field9.text()
    
        # Step 2: Generate sc_batchid
        sc_batchid = self.workorder_txt.text()

        if not all([sc_batchid, line, recipe_no, recipe_desc, quantity, mix_tank_description, age_tank_description, water_percent, cooling_temp, ptm, hp1, hot]):
            QMessageBox.warning(self, "Attenzione", "Inserire tutti i valori prima di aggiungere alla programmazione.")
            return
    
        # Step 3: Calculate sc_position
        sc_position = 1 #tooth

        current_date = datetime.now().strftime("%y%m%d")
        workorder = 999999

        # Step 4: Determine sc_pasteuriserid based on line
        pasteuriserid_mapping = {"B": 2, "C": 3, "D": 4}
        sc_pasteuriserid = pasteuriserid_mapping.get(line, 0)
    
        # Step 5: Get sc_actfat and sc_actsolid from RecipeMaster
        sc_actfat, sc_actsolid = self.get_fat_and_solid_values(recipe_no)

        #Get the Ingredients for Schedule
        selected_ingredients = self.get_selected_ingredients()

        #Generate unique identifier
        uniid = str(uuid.uuid4())
        dateraw = str(datetime.now())
    
        # Step 6: Prepare and execute the SQL insert statement
        try:
            for ingredient in selected_ingredients:
                recipe_id = ingredient["recipe_id"]
                ingredient_type = ingredient["ingredient_type"]
                ingredient_id = ingredient["ingredient_id"]
                description = ingredient["description"]
                standard_percentage = ingredient["standard_percentage"]
                total_qty = ingredient["total_qty"]
                ingr_active = "True" 

                insert_query = """
                    INSERT INTO dbo.Reports (LineID,SequenceID,WorkOrderID,RecipeID,RecipeName,RecTotalQty,BatchNumber,PasteurizerID,
                    AgeTankID,MixTankID,IngrSeqID,IngrDesc,IngrTypeID,IngrTypeDesc,IngrStorage,IngrStorageName,
                    StdPercentage,TotalQty,EffectiveQty,Variance,TimeInserted,TimeUpdated,TimeCompleted,UniID,IngrID,IngrCode) 
                    VALUES ((SELECT p_pasteuriserid FROM dbo.Pasteurisers WHERE p_line = CAST(? AS VARCHAR)), ?, ?, ?, ?, ?, ?, (SELECT p_description FROM dbo.Pasteurisers WHERE p_line = CAST(? AS VARCHAR)), 
                    (SELECT atm_tankid FROM dbo.AgeTankMaster WHERE atm_description = CAST(? AS VARCHAR)), 
                    (SELECT mtm_tankid FROM dbo.MixTankMaster WHERE mtm_description = CAST(? AS VARCHAR)), 
                    (SELECT ri_sequence FROM dbo.RecipeIngredients WHERE ri_code = CAST(? AS VARCHAR) and ri_recipeid = CAST(? AS VARCHAR)),
                    ?, 
                    (SELECT ia_areaid FROM dbo.IngredientArea WHERE ia_description = CAST(? AS VARCHAR)), 
                    ?, 
                    (SELECT im_storage FROM dbo.IngredientMaster WHERE im_description = CAST(? AS VARCHAR)), 
                    (SELECT im_storagename FROM dbo.IngredientMaster WHERE im_description = CAST(? AS VARCHAR)), 
                    ?, ?, 
                    NULL, NULL, GETDATE(), GETDATE(), NULL,?,(SELECT im_ingredientid FROM RecipeDB.dbo.IngredientMaster WHERE im_code = ?),?)
                    """
                # Execute the insert query for each row in ingr_rows
                cursor.execute(insert_query, (line, sc_position, workorder, recipe_id, recipe_desc, quantity, sc_batchid, line,
                                                age_tank_description, mix_tank_description, ingredient_id, recipe_id, description, ingredient_type, ingredient_type,
                                                description, description, standard_percentage, total_qty, uniid, ingredient_id, ingredient_id))
                        
                conn.commit()

            try:
                try:
                    # Use the correct format string that includes the date and time
                    date = datetime.strptime(dateraw, '%Y-%m-%d %H:%M:%S.%f').strftime('%d/%m/%Y')
                except ValueError:
                    try:
                        # If the first parsing fails, try without microseconds
                        date = datetime.strptime(dateraw, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                    except ValueError as e:
                        # Handle the error if it still occurs
                        QMessageBox.critical(self, "Errore", f"Si è verificato un errore:\n{str(e)}")
                        return

                # Construct the report URL with parameters
                report_url = f"http://{encoded_username}:{encoded_password}@{url}/Pages/ReportViewer.aspx?%2fPreProductionReport&rs:Command=Render&Data={date}&WorkOrder={sc_batchid}&RecipeId={recipe_id}&StampID={workorder}"
                
                # Open the report URL in a web browser
                webbrowser.open(report_url)

                time.sleep(30)

                conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()
                query = """DELETE FROM dbo.Reports WHERE WorkOrderID = ? AND RecipeID = ?"""
                cursor.execute(query, (workorder, recipe_id))
                conn.commit()

            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Si è verificato un errore:\n{str(e)}")
                return   
            
        except Exception as e:
            error_details = traceback.format_exc()
            QMessageBox.warning(self, "Errore", f"Si è verificato un errore: {e},{error_details}")
            return
        finally: #tooth
            conn.close
                
    def generate_plan_report2(self):
        selected_items = self.report_table.selectedItems()
        recipe = None
        if len(selected_items) > 0:
            first_selected_row = selected_items[0].row()

            dateraw_item = self.report_table.item(first_selected_row, 9)
            stampid_item = self.report_table.item(first_selected_row, 1)
            workorder_item = self.report_table.item(first_selected_row, 2)
            recipe_item = self.report_table.item(first_selected_row, 3)

            if dateraw_item and workorder_item and recipe_item:
                dateraw = dateraw_item.text()
                workorder = workorder_item.text()
                recipe = recipe_item.text()
                stampid = stampid_item.text()

                try:
                    try:
                        # Use the correct format string that includes the date and time
                        date = datetime.strptime(dateraw, '%Y-%m-%d %H:%M:%S.%f').strftime('%d/%m/%Y')
                    except ValueError:
                        try:
                            # If the first parsing fails, try without microseconds
                            date = datetime.strptime(dateraw, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                        except ValueError as e:
                            # Handle the error if it still occurs
                            QMessageBox.critical(self, "Errore", f"Si è verificato un errore:\n{str(e)}")
                            return

                    # Construct the report URL with parameters
                    report_url = f"http://{encoded_username}:{encoded_password}@{url}/Pages/ReportViewer.aspx?%2fPreProductionReport&rs:Command=Render&Data={date}&WorkOrder={workorder}&RecipeId={recipe}&StampID={stampid}"
                    
                    # Open the report URL in a web browser
                    webbrowser.open(report_url)

                except Exception as e:
                    QMessageBox.critical(self, "Errore", f"Si è verificato un errore:\n{str(e)}")
                    return            

    def generate_end_report(self):
        selected_items = self.report_table.selectedItems()
        recipe = None
        if len(selected_items) > 0:
            first_selected_row = selected_items[0].row()

            dateraw_item = self.report_table.item(first_selected_row, 11)
            stampid_item = self.report_table.item(first_selected_row, 1)
            workorder_item = self.report_table.item(first_selected_row, 2)
            recipe_item = self.report_table.item(first_selected_row, 3)

            if dateraw_item and workorder_item and recipe_item:
                dateraw = dateraw_item.text()
                workorder = workorder_item.text()
                recipe = recipe_item.text()
                stampid = stampid_item.text()

                try:
                    try:
                        # Use the correct format string that includes the date and time
                        date = datetime.strptime(dateraw, '%Y-%m-%d %H:%M:%S.%f').strftime('%d/%m/%Y')
                    except ValueError:
                        try:
                            # If the first parsing fails, try without microseconds
                            date = datetime.strptime(dateraw, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                        except ValueError as e:
                            # Handle the error if it still occurs
                            QMessageBox.critical(self, "Errore", f"Si è verificato un errore:\n{str(e)}")
                            return

                    # Construct the report URL with parameters
                    report_url = f"http://{encoded_username}:{encoded_password}@{url}/Pages/ReportViewer.aspx?%2fPostProductionReport&rs:Command=Render&Data={date}&WorkOrder={workorder}&RecipeId={recipe}&StampID={stampid}"

                    # Open the report URL in a web browser
                    webbrowser.open(report_url)

                except Exception as e:
                    QMessageBox.critical(self, "Errore", f"Si è verificato un errore:\n{str(e)}")
                    return

    def generate_past_report(self):
        selected_items = self.report_table.selectedItems()
        recipe = None
        if len(selected_items) > 0:
            first_selected_row = selected_items[0].row()

            dateraw_item = self.report_table.item(first_selected_row, 11)
            stampid_item = self.report_table.item(first_selected_row, 1)
            workorder_item = self.report_table.item(first_selected_row, 2)
            recipe_item = self.report_table.item(first_selected_row, 3)

            if dateraw_item and workorder_item and recipe_item:
                dateraw = dateraw_item.text()
                workorder = workorder_item.text()
                recipe = recipe_item.text()
                stampid = stampid_item.text()

                try:
                    try:
                        # Use the correct format string that includes the date and time
                        date = datetime.strptime(dateraw, '%Y-%m-%d %H:%M:%S.%f').strftime('%d/%m/%Y')
                    except ValueError:
                        try:
                            # If the first parsing fails, try without microseconds
                            date = datetime.strptime(dateraw, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                        except ValueError as e:
                            # Handle the error if it still occurs
                            QMessageBox.critical(self, "Errore", f"Si è verificato un errore:\n{str(e)}")
                            return

                    # Construct the report URL with parameters
                    report_url = f"http://{encoded_username}:{encoded_password}@{url}/Pages/ReportViewer.aspx?%2fPasteurReport&rs:Command=Render&Data={date}&StampID={stampid}&IDRecipe={recipe}"

                    # Open the report URL in a web browser
                    webbrowser.open(report_url)

                except Exception as e:
                    QMessageBox.critical(self, "Errore", f"Si è verificato un errore:\n{str(e)}")
                    return     

    def generate_bulkend_report(self):
        dateraw_item = self.date_picker.date()  # Fetch QDate object from date_picker

        if dateraw_item:
            dateraw = dateraw_item.toString('yyyy-MM-dd')  # Convert QDate to string in the desired format

            try:
                # No need for nested try-except since we are getting only date
                date = datetime.strptime(dateraw, '%Y-%m-%d').strftime('%d/%m/%Y')
                
                # Construct the report URL with parameters
                report_url = f"http://{encoded_username}:{encoded_password}@{url}/Pages/ReportViewer.aspx?%2fBulkPostProductionReport&rs:Command=Render&Data={date}"

                # Open the report URL in a web browser
                webbrowser.open(report_url)

            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Si è verificato un errore:\n{str(e)}")
                return

    def generate_bulkpast_report(self):
        dateraw_item = self.date_picker.date()  # Fetch QDate object from date_picker

        if dateraw_item:
            dateraw = dateraw_item.toString('yyyy-MM-dd')  # Convert QDate to string in the desired format

            try:
                # No need for nested try-except since we are getting only date
                date = datetime.strptime(dateraw, '%Y-%m-%d').strftime('%d/%m/%Y')
                
                # Construct the report URL with parameters
                report_url = f"http://{encoded_username}:{encoded_password}@{url}/Pages/ReportViewer.aspx?%2fBulkPasteurReport&rs:Command=Render&Data={date}"

                # Open the report URL in a web browser
                webbrowser.open(report_url)

            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Si è verificato un errore:\n{str(e)}")
                return 

    def refresh_report_tab(self):
        try:
            conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute('''SELECT 
                                [LineID] as Linea,
                                [WorkOrderID] as Batch,
                                [BatchNumber] as WorkOrder,
                                [RecipeID] as Ricetta,
                                [RecipeName] as Descrizione,
                                [RecTotalQty] as Quantità,
                                [PasteurizerID] as [Pasteurizatore],
                                [AgeTankID] as [Serbatoio], 
                                [MixTankID] as Blender,
                                MAX([TimeInserted]) as Programmato,
                                MAX([TimeUpdated]) as Aggiornato,
                                MAX([TimeCompleted]) as Completato
                            FROM [RecipeDB].[dbo].[Reports]
                            WHERE 
                                TimeCompleted IS NOT NULL 
                                AND [TimeCompleted] >= DATEADD(hour, -24, GETDATE())
                            GROUP BY 
                                [LineID],
                                [WorkOrderID],
                                [BatchNumber],
                                [RecipeID],
                                [RecipeName],
                                [RecTotalQty],
                                [PasteurizerID],
                                [AgeTankID],
                                [MixTankID]
                            ORDER BY 
                                MAX([TimeCompleted]) DESC;
                        ''')
        
            # Fetch all the results
            results = cursor.fetchall()

            # Determine the number of rows and columns
            number_of_rows = len(results)
            if number_of_rows > 0:
                number_of_columns = len(results[0])
                self.report_table.setColumnCount(number_of_columns)
                self.report_table.setRowCount(number_of_rows)
                
                # Set the headers if needed
                headers = [description[0] for description in cursor.description]
                self.report_table.setHorizontalHeaderLabels(headers)

                # Resize columns to fit contents after setting headers
                self.report_table.resizeColumnsToContents()

                header = self.report_table.horizontalHeader()

                # Populate the table
                for row_number, row_data in enumerate(results):
                    for column_number, data in enumerate(row_data):
                        self.report_table.setItem(row_number, column_number, QTableWidgetItem(str(data)))
            
            #header.setSectionResizeMode(QHeaderView.Stretch)
            self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            cursor.close()
            conn.close

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Si è verificato un errore:\n{str(e)}")
            return

#--------------------------------------------------------------------END OF REPORT FUNCTIONS/HMI
#--------------------------------------------------------------------SYSTEM CALLOUTS

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icon.ico'))

    # Get the screen size for dynamic font sizing
    screen = app.primaryScreen()
    rect = screen.availableGeometry()
    screenHeight = rect.height()

    # Calculate font size as a percentage of the screen height
    fontSize = screenHeight * 0.012
    minimum_font_size = 6  # Set a minimum font size
    calculated_font_size = max(int(fontSize), minimum_font_size)

    # Set the application font size dynamically
    font = QFont()
    font.setPointSize(calculated_font_size)
    app.setFont(font)

    # Continue with the rest of your application setup
    window = SQLTableWindow()
    window.showMaximized()

    sys.exit(app.exec_())