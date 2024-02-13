import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QTableView, QVBoxLayout, QWidget, QDialog, \
    QMessageBox, QItemDelegate, QComboBox, QStyledItemDelegate, QHBoxLayout, QLabel
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from PyQt5 import QtCore


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
    def __init__(self, films, parent=None):
        super().__init__(parent)
        self.films = films

    def createEditor(self, parent, option, index):
        comboBox = QComboBox(parent)
        for film in self.films:
            comboBox.addItem(film)
        return comboBox

    def setEditorData(self, editor, index):
        film = index.data()
        comboBoxIndex = editor.findText(film)
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
        films = self.get_films_from_db()

        # Создаем делегат с полученным списком фильмов
        delegate = ComboBoxDelegate(films, self)
        self.tableView = QTableView()
        self.tableView.setModel(self.model)

        # Применяем ComboBoxDelegate ко всем столбцам модели
        for column in range(self.model.columnCount()):
            self.tableView.setItemDelegateForColumn(column, delegate)

        layout = QVBoxLayout()
        layout.addWidget(self.tableView)
        self.setLayout(layout)

    def get_films_from_db(self):
        # Создаем SQL запрос
        query = QSqlQuery("SELECT название_фильма FROM Films")
        films = []
        while query.next():
            films.append(query.value(0))  # предполагается, что названия фильмов хранятся в первом столбце
        return films

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

        # Создаем вертикальный контейнер и добавляем в него виджет таблицы
        layout = QVBoxLayout()
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


class RulesWindow(QWidget):
    buttonClicked = QtCore.pyqtSignal(int)
    def __init__(self, homewindow, selected_cell, cell_number,film_id):
        super().__init__()
        self.homewindow = homewindow
        self.selected_cell = selected_cell
        self.cell_number = cell_number
        self.film_id = film_id
        self.initUI()

    def initUI(self):
        self.setGeometry(350, 100, 760, 800)
        self.setStyleSheet("background-color: grey; ")

        self.button = QPushButton(self.selected_cell, self)
        self.button.setGeometry(80, 10, 590, 30)
        self.button.setStyleSheet("background-color: white; color: black")
        self.button.clicked.connect(self.openHomewindow)

        # Создаем вертикальный лэйаут для всех рядов кнопок и надписей
        v_layout = QVBoxLayout()
        v_layout.setSpacing(20)  # Устанавливаем интервал между рядами

        def handleButtonClicked():
            button = self.sender()
            button_number = int(button.text())
            self.buttonClicked.emit(button_number)
            button.setStyleSheet("background-color: red;")  # Изменяем стиль кнопки

        v_layout = QVBoxLayout()  # Создаем вертикальный layout
        h_layout = QHBoxLayout()  # Создаем горизонтальный layout

        for button_number in range(1, 73):
            button = QPushButton(str(button_number), self)
            button.setFixedSize(40, 40)
            button.setStyleSheet("background-color: white; ")
            button.clicked.connect(handleButtonClicked)
            h_layout.addWidget(button)

            if button_number % 12 == 0:
                v_layout.addLayout(h_layout)
                h_layout = QHBoxLayout()  # Создаем новый горизонтальный layout

        self.setLayout(v_layout)

    def onButtonClicked(self):
        sender = self.sender()
        if sender.styleSheet() == "background-color: white; ":
            sender.setStyleSheet("background-color: red; ")
            self.homewindow.updateFilmCell(self.cell_number, self.film_id)
        else:
            sender.setStyleSheet("background-color: white; ")

    def openHomewindow(self):
        self.homewindow.show()
        self.close()

    def closeEvent(self, event):
        self.openHomewindow()


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
