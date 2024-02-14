import sys
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QTableView, QVBoxLayout, QWidget, QDialog, \
     QMessageBox, QComboBox, QStyledItemDelegate, QHBoxLayout, QListView
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from PyQt5 import QtCore, QtWidgets


class filmsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Фильмы")
        self.setGeometry(300, 180, 900, 700)

        # Создаем модель таблицы и связываем ее с виджетом QTableView
        self.model = QSqlTableModel(self)
        self.model.setTable("Films")
        self.model.setEditStrategy(QSqlTableModel.OnFieldChange)  # Сохранять изменения сразу после редактирования поля
        self.model.select()

        self.tableView = QTableView()
        self.tableView.setModel(self.model)
        self.tableView.hideColumn(0)

        # Создаем кнопки "Добавить" и "Удалить" в окне таблицы
        self.addButton = QPushButton("+", self)
        self.deleteButton = QPushButton("-", self)

        # Создаем вертикальный контейнер и добавляем в него кнопки и виджет таблицы
        layout = QVBoxLayout()

        layout.addWidget(self.tableView)
        layout.addWidget(self.addButton)
        layout.addWidget(self.deleteButton)

        self.setLayout(layout)

        # Подключаем сигналы кнопок к соответствующим методам
        self.addButton.clicked.connect(self.add_row)
        self.deleteButton.clicked.connect(self.delete_row)

    def add_row(self):
        rowCount = self.model.rowCount()
        self.model.insertRow(rowCount)


    def delete_row(self):
        # Получаем индексы выбранных строк
        indexes = self.tableView.selectedIndexes()

        if indexes:
            # Запрашиваем подтверждение удаления
            confirm = QMessageBox.question(self, "Подтверждение", "Вы уверены, что хотите удалить выбранные строки?",
                                           QMessageBox.Yes | QMessageBox.No)

            if confirm == QMessageBox.Yes:
                rows = sorted(set(index.row() for index in indexes), reverse=True)
                # Удаляем выбранные строки из модели начиная с конца, чтобы индексы не нарушились
                for row in rows:
                    self.model.removeRow(row)

                if not self.model.submitAll():
                    QMessageBox.warning(
                        self, "Ошибка", "Не удалось удалить строки: " + self.model.lastError().text())
                    self.model.revertAll()  # Откатим изменения
                else:
                    self.model.select()  # Обновляем модель для отображения изменений в интерфейсе
        else:
            QMessageBox.warning(self, "Внимание", "Вы не выбрали строки для удаления.")

    def closeEvent(self, event):
        if self.model.isDirty():
            # Есть несохраненные изменения
            reply = QMessageBox.question(self, 'Подтверждение закрытия',
                                         "Есть несохраненные изменения. Хотите сохранить их перед выходом?",
                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if reply == QMessageBox.Save:
                # Пытаемся сохранить изменения
                if not self.model.submitAll():
                    QMessageBox.warning(self, "Ошибка сохранения",
                                        "Не удалось сохранить изменения: " + self.model.lastError().text())
                    # Возвращаем пользователя в приложение, чтобы он мог исправить ошибки
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                # Пользователь отменяет выход
                event.ignore()
                return
        # Если пользователь выбрал "Discard" или изменений нет, выходим нормально
        event.accept()

class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, Films, parent=None):
        super().__init__(parent)
        self.Films = Films

    def createEditor(self, parent, option, index):
        comboBox = QComboBox(parent)
        for Film in self.Films:
            comboBox.addItem(Film)
        return comboBox

    def setEditorData(self, editor, index):
        Film = index.data()
        comboBoxIndex = editor.findText(Film)
        if comboBoxIndex >= 0:
            editor.setCurrentIndex(comboBoxIndex)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText())


class RaspisanieWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Расписание")
        self.setGeometry(300, 180, 900, 700)
        self.model = QSqlTableModel(self)
        self.model.setTable("Raspisanie")
        self.model.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.model.select()

        # Получаем список фильмов из базы данных
        Films = self.get_films_from_db()

        # Создаем делегат с полученным списком фильмов
        delegate = ComboBoxDelegate(Films, self)
        self.tableView = QTableView()
        self.tableView.setModel(self.model)
        self.tableView.verticalHeader().setVisible(False)

        # Создаем виджет списка дат
        self.dateListView = QListView()
        self.dateListView.setFixedWidth(60)
        self.dateListView.setSpacing(6)  # Устанавливаем фиксированную ширину для списка дат

        # Создаем модель для списка дат и добавляем даты
        date_model = QStandardItemModel()
        date_model.appendRow(QStandardItem(''))
        current_date = QDate.currentDate()
        for i in range(8):
            date = current_date.addDays(i)
            date_str = date.toString("dd.MM")
            item = QStandardItem(date_str)
            date_model.appendRow(item)

        self.dateListView.setModel(date_model)
        # Применяем стиль CSS к элементам списка дат
        self.dateListView.setStyleSheet("QListView::item { border-bottom: 1px solid white; }")

        # Применяем ComboBoxDelegate ко всем столбцам модели
        for column in range(self.model.columnCount()):
            self.tableView.setItemDelegateForColumn(column, delegate)

        layout = QHBoxLayout()
        layout.addWidget(self.dateListView)
        layout.addWidget(self.tableView)
        self.setLayout(layout)

    def get_films_from_db(self):
        # Создаем SQL запрос
        query = QSqlQuery("SELECT название_фильма FROM Films")
        Films = []
        while query.next():
            Films.append(query.value(0))
        return Films

class HomeWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Главная")
        self.setGeometry(300, 180, 900, 700)

        # Создаем модель таблицы и связываем ее с виджетом QTableView
        self.model = QSqlTableModel(self)
        self.model.setTable("Raspisanie")
        self.model.select()

        self.tableView = QTableView()
        self.tableView.setModel(self.model)
        self.tableView.clicked.connect(self.onTableClicked)

        self.tableView.verticalHeader().setVisible(False)

        # Создаем виджет списка дат
        self.dateListView = QListView()
        self.dateListView.setFixedWidth(60)
        self.dateListView.setSpacing(6) # Устанавливаем фиксированную ширину для списка дат

        # Создаем модель для списка дат и добавляем даты
        date_model = QStandardItemModel()
        date_model.appendRow(QStandardItem(''))
        current_date = QDate.currentDate()
        for i in range(8):
            date = current_date.addDays(i)
            date_str = date.toString("dd.MM")
            item = QStandardItem(date_str)
            date_model.appendRow(item)

        self.dateListView.setModel(date_model)
        # Применяем стиль CSS к элементам списка дат
        self.dateListView.setStyleSheet("QListView::item { border-bottom: 1px solid white; }")

        # Создаем горизонтальный контейнер и добавляем в него виджеты
        layout = QHBoxLayout()
        layout.addWidget(self.dateListView)
        layout.addWidget(self.tableView)
        self.setLayout(layout)

    def getSelectedId(self):
        indexes = self.tableView.selectedIndexes()
        if indexes:
            row = indexes[0].row()
            column = indexes[0].column()
            cell_index = self.model.index(row, column)
            cell_id = self.model.data(cell_index)
            cell_number = row * self.model.columnCount() + column + 1
            return cell_id, cell_number
        return None, None

    def handleButtonClicked(self, button_number):  # Слот для обработки нажатия кнопки
        print("Button Number:", button_number)


    def getFilmId(self, film_name):
        query = QSqlQuery()
        query.prepare("SELECT id_film FROM Films WHERE название_фильма = :film_name")
        query.bindValue(":film_name", film_name)
        if query.exec_() and query.next():
            film_id = query.value(0)
            return film_id
        else:
            print("Error retrieving film id:", query.lastError().text())
            return None

    def onTableClicked(self):
        selected_cell, cell_number = self.getSelectedId()
        if selected_cell:
            print("Selected Cell ID:", selected_cell)
            print("Cell Number:", cell_number)
            film_id = self.getFilmId(selected_cell)
            self.new_window = RulesWindow(self, selected_cell, cell_number, film_id)
            self.new_window.buttonClicked.connect(self.handleButtonClicked)  # Подключение сигнала
            self.new_window.show()
            self.updateFilmCell(cell_number, film_id)  # Добавлен аргумент film_id
            self.close()

    def updateFilmCell(self, cell_number, film_id):
        query = QSqlQuery()
        query.prepare("INSERT OR REPLACE INTO film_cell (id_cell, id_film) VALUES (:cell_number, :id_film)")
        query.bindValue(":cell_number", cell_number)
        query.bindValue(":id_film", film_id)
        if query.exec_():
            print("Cell number and film id inserted into film_cell table:", cell_number, film_id)
        else:
            print("Error inserting cell number and film id into film_cell table:", query.lastError().text())


class RulesWindow(QtWidgets.QWidget):
    buttonClicked = QtCore.pyqtSignal(int)

    def __init__(self, homewindow, selected_cell, cell_number, film_id):
        super().__init__()
        self.homewindow = homewindow
        self.selected_cell = selected_cell
        self.cell_number = cell_number
        self.film_id = film_id
        self.updated = False  # Флаг для отслеживания обновления столбца seats
        self.initUI()

    def initUI(self):
        self.setGeometry(350, 100, 760, 800)
        self.setStyleSheet("background-color: grey; ")

        # Создаем вертикальный лэйаут для всех рядов кнопок и надписей
        v_layout = QtWidgets.QVBoxLayout()
        v_layout.setSpacing(20)  # Устанавливаем интервал между рядами

        label_names = ["ряд 1", "ряд 2", "ряд 3", "ряд 4", "ряд 5", "ряд 6"]

        self.button = QtWidgets.QPushButton(self.selected_cell + ' / выход', self)
        self.button.setStyleSheet("background-color: white; color: black")
        self.button.clicked.connect(self.openHomewindow)
        v_layout.addWidget(self.button)

        for label_name in label_names:
            v_layout.addWidget(QtWidgets.QLabel("", self))  # Пустой виджет для создания интервала между рядами

            h_layout = QtWidgets.QHBoxLayout()  # Создаем горизонтальный layout

            label = QtWidgets.QLabel(label_name, self)
            label.setStyleSheet("color: white; font-weight: bold;")
            h_layout.addWidget(label)

            # Получаем текущий список кнопок из столбца seats в таблице film_cell
            current_buttons = self.getFilmCellButtons()

            for button_number in range(1, 13):
                button = QtWidgets.QPushButton(str((label_names.index(label_name) * 12) + button_number), self)
                button.setFixedSize(40, 40)
                if (label_names.index(label_name) * 12) + button_number in current_buttons:
                    button.setStyleSheet("background-color: red; ")
                else:
                    button.setStyleSheet("background-color: white; ")
                button.clicked.connect(self.handleButtonClicked)
                h_layout.addWidget(button)

            v_layout.addLayout(h_layout)

        self.setLayout(v_layout)



    def getFilmCellButtons(self):
        query = QSqlQuery()
        query.prepare("SELECT seats FROM film_cell WHERE id_cell = :cell_number")
        query.bindValue(":cell_number", self.cell_number)
        if query.exec_() and query.next():
            seats_str = query.value(0)
            if seats_str:
                return list(map(int, seats_str.split(',')))
        return []

    def handleButtonClicked(self):
        button = self.sender()
        button_number = int(button.text())
        self.buttonClicked.emit(button_number)
        if button.styleSheet() == "background-color: white; ":
            button.setStyleSheet("background-color: red;")  # Изменяем стиль кнопки
        else:
            button.setStyleSheet("background-color: white;")  # Изменяем стиль кнопки

        # Получаем текущий список кнопок из столбца seats в таблице film_cell
        current_buttons = self.getFilmCellButtons()

        if button_number in current_buttons:
            # Кнопка уже нажата, поэтому удаляем ее из списка и меняем цвет на белый
            current_buttons.remove(button_number)
            button.setStyleSheet("background-color: white;")
        else:
            # Кнопка не нажата, поэтому добавляем ее в список
            current_buttons.append(button_number)

        # Обновляем столбец seats в таблице film_cell
        self.updateFilmCellButtons(current_buttons)

    def updateFilmCellButtons(self, buttons):
        seats_str = ','.join(map(str, buttons))
        query = QSqlQuery()
        query.prepare("UPDATE film_cell SET seats = :seats WHERE id_cell = :cell_number")
        query.bindValue(":seats", seats_str)
        query.bindValue(":cell_number", self.cell_number)
        if query.exec_():
            print("Buttons updated in film_cell table:", seats_str)
        else:
            print("Error updating buttons in film_cell table:", query.lastError().text())

    def openHomewindow(self):
        self.homewindow.show()
        self.close()

    def closeEvent(self, event):
        if not self.updated:
            # Получаем текущий список кнопок из столбца seats в таблице film_cell
            current_buttons = self.getFilmCellButtons()

            # Проверяем, какие кнопки горят красным и отсутствуют в текущем списке
            red_buttons = [button for button in self.findChildren(QtWidgets.QPushButton) if
                           button.palette().button().color().name() == "#ff0000"]
            new_buttons = [button for button in red_buttons if int(button.text()) not in current_buttons]

            # Добавляем новые кнопки в текущий список
            current_buttons.extend(int(button.text()) for button in new_buttons)

            # Обновляем столбец seats в таблице film_cell
            self.updateFilmCellButtons(current_buttons)

            self.updated = True

        self.close()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Главное окно")
        self.setGeometry(160, 500, 1060, 920)

        # Создаем кнопки для открытия окон с таблицами
        self.button1 = QPushButton("Фильмы", self)
        self.button2 = QPushButton("Расписание", self)
        self.button3 = QPushButton("Главная", self)

        # Устанавливаем положение и размер кнопок
        self.button1.setGeometry(10, 100, 120, 80)
        self.button2.setGeometry(10, 190, 120, 80)
        self.button3.setGeometry(10, 10, 120, 80)

        # Подключаем сигналы кнопок к соответствующим методам
        self.button1.clicked.connect(self.open_films_table)
        self.button2.clicked.connect(self.open_raspisanie_table)
        self.button3.clicked.connect(self.open_home_table)

    def open_films_table(self):
        filmWindow = filmsWindow(self)
        filmWindow.exec()

    def open_raspisanie_table(self):
        raspWindow = RaspisanieWindow(self)
        raspWindow.exec()

    def open_home_table(self):
        homWindow = HomeWindow(self)
        homWindow.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Подключаемся к базе данных
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName("Kinoteatr.db")
    if not db.open():
        print("Не удалось подключиться к базе данных.")
        sys.exit(1)

    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
