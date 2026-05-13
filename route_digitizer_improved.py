"""
ROUTE DIGITIZER - ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ
С разделением маяков и сигналов по направлениям, но общими станциями и ограничениями
"""
import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QFileDialog,
                             QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QSpinBox, QComboBox, QMessageBox, QTabWidget, QLineEdit,
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                             QCheckBox)
from PyQt5.QtGui import QPixmap, QColor, QPen, QFont, QPolygon
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsTextItem

class RouteDigitizer(QMainWindow):
    def __init__(self):
        super().__init__()
        # Данные
        self.beacons_even = []
        self.beacons_odd = []
        self.signals_even = []
        self.signals_odd = []
        self.stations = []
        self.speed_limits = []
        
        self.image_path = None
        self.zoom_level = 1.0
        self.current_direction = 'even'
        self.last_mouse_pos = QPoint(0, 0)
        self.pixmap_item = None
        
        # Цвета
        self.color_even = QColor(100, 150, 255)
        self.color_odd = QColor(255, 100, 100)
        
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Route Digitizer - Оцифровка маршрута')
        self.setGeometry(50, 50, 1600, 900)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QHBoxLayout(central_widget)
        
        # ===== ЛЕВАЯ ЧАСТЬ - КАРТА =====
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("QGraphicsView { background-color: #1a1a1a; }")
        self.view.mousePressEvent = self.on_map_click
        self.view.mouseMoveEvent = self.on_mouse_move
        main_layout.addWidget(self.view, 7)
        
        # ===== ПРАВАЯ ЧАСТЬ - КОНТРОЛЫ =====
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # Кнопка загрузки
        load_button = QPushButton('📁 Загрузить карту')
        load_button.setStyleSheet("QPushButton { background-color: #2d5a2d; font-weight: bold; padding: 10px; color: white; }")
        load_button.clicked.connect(self.load_image)
        right_layout.addWidget(load_button)
        
        right_layout.addWidget(QLabel('═' * 40))
        
        # Направление
        direction_layout = QHBoxLayout()
        direction_layout.addWidget(QLabel("Направление:"))
        
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(['🔵 ЧЁТНОЕ', '🔴 НЕЧЁТНОЕ'])
        self.direction_combo.currentIndexChanged.connect(self.change_direction)
        direction_layout.addWidget(self.direction_combo)
        
        right_layout.addLayout(direction_layout)
        
        # Вкладки
        self.tabs = QTabWidget()
        
        # TAB 1: МАЯКИ
        beacon_widget = QWidget()
        beacon_layout = QVBoxLayout()
        
        beacon_layout.addWidget(QLabel("Км:"))
        self.km_spin = QSpinBox()
        self.km_spin.setRange(1, 26)
        self.km_spin.setValue(1)
        beacon_layout.addWidget(self.km_spin)
        
        beacon_layout.addWidget(QLabel("ПК:"))
        self.pk_spin = QSpinBox()
        self.pk_spin.setRange(1, 10)
        self.pk_spin.setValue(1)
        beacon_layout.addWidget(self.pk_spin)
        
        beacon_layout.addWidget(QLabel("─" * 40))
        
        add_btn = QPushButton('✚ Добавить')
        add_btn.setStyleSheet("QPushButton { background-color: #3d6d3d; padding: 8px; color: white; }")
        add_btn.clicked.connect(self.add_beacon)
        beacon_layout.addWidget(add_btn)
        
        undo_btn = QPushButton('↶ Отмена (Z)')
        undo_btn.setStyleSheet("QPushButton { background-color: #5a3d3d; padding: 6px; color: white; }")
        undo_btn.clicked.connect(self.undo_beacon)
        beacon_layout.addWidget(undo_btn)
        
        self.beacon_list_label = QLabel("Маяков: 0")
        self.beacon_list_label.setStyleSheet("QLabel { font-size: 8px; color: #888; }")
        beacon_layout.addWidget(self.beacon_list_label)
        
        # Таблица маяков
        self.beacons_table = QTableWidget()
        self.beacons_table.setColumnCount(4)
        self.beacons_table.setHorizontalHeaderLabels(["Км", "ПК", "Направление", ""])
        self.beacons_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.beacons_table.setColumnWidth(3, 30)
        self.beacons_table.verticalHeader().setVisible(False)
        self.beacons_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.beacons_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.beacons_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.beacons_table.setFixedHeight(150)
        beacon_layout.addWidget(self.beacons_table)
        
        beacon_layout.addStretch()
        beacon_widget.setLayout(beacon_layout)
        self.tabs.addTab(beacon_widget, "🗺️ МАЯКИ")
        
        # TAB 2: СВЕТОФОРЫ
        signal_widget = QWidget()
        signal_layout = QVBoxLayout()
        
        signal_layout.addWidget(QLabel("Имя:"))
        self.signal_name = QLineEdit()
        self.signal_name.setPlaceholderText("М21, Ч1, Н3")
        signal_layout.addWidget(self.signal_name)
        
        signal_layout.addWidget(QLabel("Метры:"))
        self.signal_meters = QSpinBox()
        self.signal_meters.setRange(0, 26700)
        self.signal_meters.setSingleStep(50)
        signal_layout.addWidget(self.signal_meters)
        
        # Новое: два состояния для светофора
        signal_layout.addWidget(QLabel("Состояние по умолчанию:"))
        self.signal_default_state = QComboBox()
        self.signal_default_state.addItems([
            "Один зелёный огонь",
            "Один жёлтый огонь",
            "Один красный огонь",
            "Два жёлтых огня",
            "Два жёлтых огня, верхний мигающий",
            "Один жёлтый мигающий огонь",
            "Один красный огонь(м)",
            "Один лунно-белый огонь(М)",
            "Один синий огонь(М)"
        ])
        signal_layout.addWidget(self.signal_default_state)
        
        signal_layout.addWidget(QLabel("Ручное переключение:"))
        self.signal_manual_state = QComboBox()
        self.signal_manual_state.addItems([
            "Один зелёный огонь",
            "Один жёлтый огонь",
            "Один красный огонь",
            "Два жёлтых огня",
            "Два жёлтых огня, верхний мигающий",
            "Один жёлтый мигающий огонь",
            "Один красный огонь(м)",
            "Один лунно-белый огонь(М)",
            "Один синий огонь(М)",
            "Нет ручного переключения"
        ])
        signal_layout.addWidget(self.signal_manual_state)
        
        signal_layout.addWidget(QLabel("─" * 40))
        
        sig_add_btn = QPushButton('✚ Добавить')
        sig_add_btn.setStyleSheet("QPushButton { background-color: #5a5a2d; padding: 8px; color: white; }")
        sig_add_btn.clicked.connect(self.add_signal)
        signal_layout.addWidget(sig_add_btn)
        
        self.signal_list_label = QLabel("Сигналов: 0")
        self.signal_list_label.setStyleSheet("QLabel { font-size: 8px; color: #888; }")
        signal_layout.addWidget(self.signal_list_label)
        
        # Таблица сигналов
        self.signals_table = QTableWidget()
        self.signals_table.setColumnCount(5)
        self.signals_table.setHorizontalHeaderLabels(["Имя", "Метры", "По умолчанию", "Ручное", ""])
        self.signals_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.signals_table.setColumnWidth(4, 30)
        self.signals_table.verticalHeader().setVisible(False)
        self.signals_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.signals_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.signals_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.signals_table.setFixedHeight(150)
        signal_layout.addWidget(self.signals_table)
        
        signal_layout.addStretch()
        signal_widget.setLayout(signal_layout)
        self.tabs.addTab(signal_widget, "🚦 СИГНАЛЫ")
        
        # TAB 3: ОГРАНИЧЕНИЯ СКОРОСТИ
        speed_widget = QWidget()
        speed_layout = QVBoxLayout()
        
        speed_layout.addWidget(QLabel("От метров:"))
        self.speed_from_meters = QSpinBox()
        self.speed_from_meters.setRange(0, 26700)
        self.speed_from_meters.setSingleStep(50)
        speed_layout.addWidget(self.speed_from_meters)
        
        speed_layout.addWidget(QLabel("До метров:"))
        self.speed_to_meters = QSpinBox()
        self.speed_to_meters.setRange(0, 26700)
        self.speed_to_meters.setSingleStep(50)
        speed_layout.addWidget(self.speed_to_meters)
        
        speed_layout.addWidget(QLabel("Ограничение (км/ч):"))
        self.speed_limit = QSpinBox()
        self.speed_limit.setRange(10, 160)
        self.speed_limit.setValue(60)
        speed_layout.addWidget(self.speed_limit)
        
        speed_layout.addWidget(QLabel("─" * 40))
        
        speed_add_btn = QPushButton('✚ Добавить ограничение')
        speed_add_btn.setStyleSheet("QPushButton { background-color: #2d4a5a; padding: 8px; color: white; }")
        speed_add_btn.clicked.connect(self.add_speed_limit)
        speed_layout.addWidget(speed_add_btn)
        
        self.speed_list_label = QLabel("Ограничений: 0")
        self.speed_list_label.setStyleSheet("QLabel { font-size: 8px; color: #888; }")
        speed_layout.addWidget(self.speed_list_label)
        
        # Таблица ограничений
        self.speed_limits_table = QTableWidget()
        self.speed_limits_table.setColumnCount(4)
        self.speed_limits_table.setHorizontalHeaderLabels(["От метров", "До метров", "Ограничение", ""])
        self.speed_limits_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.speed_limits_table.setColumnWidth(3, 30)
        self.speed_limits_table.verticalHeader().setVisible(False)
        self.speed_limits_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.speed_limits_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.speed_limits_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.speed_limits_table.setFixedHeight(150)
        speed_layout.addWidget(self.speed_limits_table)
        
        speed_layout.addStretch()
        speed_widget.setLayout(speed_layout)
        self.tabs.addTab(speed_widget, "⚠️ ОГРАНИЧЕНИЯ")
        
        # TAB 4: СТАНЦИИ
        station_widget = QWidget()
        station_layout = QVBoxLayout()
        
        station_layout.addWidget(QLabel("Название:"))
        self.station_name = QLineEdit()
        station_layout.addWidget(self.station_name)
        
        station_layout.addWidget(QLabel("От метров:"))
        self.station_from_meters = QSpinBox()
        self.station_from_meters.setRange(0, 26700)
        self.station_from_meters.setSingleStep(50)
        station_layout.addWidget(self.station_from_meters)
        
        station_layout.addWidget(QLabel("До метров:"))
        self.station_to_meters = QSpinBox()
        self.station_to_meters.setRange(0, 26700)
        self.station_to_meters.setSingleStep(50)
        station_layout.addWidget(self.station_to_meters)
        
        station_layout.addWidget(QLabel("─" * 40))
        
        st_add_btn = QPushButton('✚ Добавить')
        st_add_btn.setStyleSheet("QPushButton { background-color: #2d5a2d; padding: 8px; color: white; }")
        st_add_btn.clicked.connect(self.add_station)
        station_layout.addWidget(st_add_btn)
        
        self.station_list_label = QLabel("Станций: 0")
        self.station_list_label.setStyleSheet("QLabel { font-size: 8px; color: #888; }")
        station_layout.addWidget(self.station_list_label)
        
        # Таблица станций
        self.stations_table = QTableWidget()
        self.stations_table.setColumnCount(4)
        self.stations_table.setHorizontalHeaderLabels(["Название", "От метров", "До метров", ""])
        self.stations_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.stations_table.setColumnWidth(3, 30)
        self.stations_table.verticalHeader().setVisible(False)
        self.stations_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.stations_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.stations_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.stations_table.setFixedHeight(150)
        station_layout.addWidget(self.stations_table)
        
        station_layout.addStretch()
        station_widget.setLayout(station_layout)
        self.tabs.addTab(station_widget, "🚉 СТАНЦИИ")
        
        right_layout.addWidget(self.tabs)
        
        # Информация
        right_layout.addWidget(QLabel('═' * 40))
        
        self.coord_label = QLabel('X: 0 | Y: 0')
        self.coord_label.setStyleSheet("QLabel { font-weight: bold; color: #0ff; }")
        right_layout.addWidget(self.coord_label)
        
        self.status_label = QLabel('Маяков: 0 | Сигналов: 0 | Станций: 0')
        self.status_label.setStyleSheet("QLabel { font-weight: bold; color: #0f0; }")
        right_layout.addWidget(self.status_label)
        
        # Видимость элементов
        right_layout.addWidget(QLabel('Видимость:'))
        visibility_layout = QHBoxLayout()
        
        self.show_beacons = QCheckBox("Маяки")
        self.show_beacons.setChecked(True)
        self.show_beacons.stateChanged.connect(self.redraw)
        visibility_layout.addWidget(self.show_beacons)
        
        self.show_signals = QCheckBox("Сигналы")
        self.show_signals.setChecked(True)
        self.show_signals.stateChanged.connect(self.redraw)
        visibility_layout.addWidget(self.show_signals)
        
        self.show_speed_limits = QCheckBox("Ограничения")
        self.show_speed_limits.setChecked(True)
        self.show_speed_limits.stateChanged.connect(self.redraw)
        visibility_layout.addWidget(self.show_speed_limits)
        
        right_layout.addLayout(visibility_layout)
        
        right_layout.addWidget(QLabel('═' * 40))
        
        # Кнопки сохранения
        save_button = QPushButton('💾 СОХРАНИТЬ')
        save_button.setStyleSheet("QPushButton { background-color: #2d5a2d; font-weight: bold; padding: 10px; color: white; }")
        save_button.clicked.connect(self.save_route)
        right_layout.addWidget(save_button)
        
        clear_button = QPushButton('🗑️ Очистить')
        clear_button.setStyleSheet("QPushButton { background-color: #5a2d2d; padding: 8px; color: white; }")
        clear_button.clicked.connect(self.clear_all)
        right_layout.addWidget(clear_button)
        
        right_layout.addStretch()
        
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, 3)
        
        self.view.setFocus()
        self.update_direction_labels()
        self.update_beacons_table()
    
    def change_direction(self, index):
        self.current_direction = 'even' if index == 0 else 'odd'
        self.update_direction_labels()
    
    def update_direction_labels(self):
        direction_text = "ЧЁТНОЕ" if self.current_direction == 'even' else "НЕЧЁТНОЕ"
        color = "🔵" if self.current_direction == 'even' else "🔴"
        
        # Обновляем заголовки во всех вкладках
        self.tabs.setTabText(0, f"{color} МАЯКИ")
        self.tabs.setTabText(1, f"🚦 СИГНАЛЫ {direction_text}")
        self.tabs.setTabText(2, f"⚠️ ОГРАНИЧЕНИЯ")
        self.tabs.setTabText(3, f"🚉 СТАНЦИИ")
    
    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите карту", "", "Images (*.png *.jpg *.bmp)")
        if path:
            self.image_path = path
            pixmap = QPixmap(path)
            self.pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.clear()
            self.scene.addItem(self.pixmap_item)
            self.scene.setSceneRect(self.pixmap_item.boundingRect())
            self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            self.redraw()
    
    def on_map_click(self, event):
        if self.pixmap_item is None:
            return
        scene_pos = self.view.mapToScene(event.pos())
        self.last_mouse_pos = QPoint(int(scene_pos.x()), int(scene_pos.y()))
    
    def on_mouse_move(self, event):
        scene_pos = self.view.mapToScene(event.pos())
        x, y = int(scene_pos.x()), int(scene_pos.y())
        self.coord_label.setText(f"X: {x} | Y: {y}")
    
    def add_beacon(self):
        if self.image_path is None:
            QMessageBox.warning(self, "Ошибка", "Загрузите карту!")
            return
        
        km = self.km_spin.value()
        pk = self.pk_spin.value()
        x = self.last_mouse_pos.x()
        y = self.last_mouse_pos.y()
        
        if x == 0 and y == 0:
            QMessageBox.warning(self, "Ошибка", "Нажмите на карту!")
            return
        
        # Рассчитываем метры правильно: 1км1пк = 1000м, 1км2пк = 1100м и т.д.
        meters = km * 1000 + (pk - 1) * 100
        
        beacon = {
            'km': km,
            'pk': pk,
            'meters': meters,
            'x': x,
            'y': y
        }
        
        if self.current_direction == 'even':
            self.beacons_even.append(beacon)
        else:
            self.beacons_odd.append(beacon)
        
        self.redraw()
        self.update_status()
        self.update_beacons_table()
        
        # Автоинкремент пикета/километра
        if pk < 10:
            self.pk_spin.setValue(pk + 1)
        else:
            if km < 26:
                self.km_spin.setValue(km + 1)
                self.pk_spin.setValue(1)
    
    def undo_beacon(self):
        if self.current_direction == 'even' and self.beacons_even:
            self.beacons_even.pop()
        elif self.current_direction == 'odd' and self.beacons_odd:
            self.beacons_odd.pop()
        self.redraw()
        self.update_status()
        self.update_beacons_table()
    
    def update_beacons_table(self):
        self.beacons_table.setRowCount(0)
        
        # Добавляем чётные маяки
        for i, beacon in enumerate(self.beacons_even):
            self.beacons_table.insertRow(i)
            self.beacons_table.setItem(i, 0, QTableWidgetItem(str(beacon['km'])))
            self.beacons_table.setItem(i, 1, QTableWidgetItem(str(beacon['pk'])))
            self.beacons_table.setItem(i, 2, QTableWidgetItem("Чётный"))
            
            # Кнопка удаления
            delete_btn = QPushButton("×")
            delete_btn.setStyleSheet("font-weight: bold; color: red; background: transparent; border: none;")
            delete_btn.clicked.connect(lambda _, idx=i: self.delete_beacon_even(idx))
            self.beacons_table.setCellWidget(i, 3, delete_btn)
        
        # Добавляем нечётные маяки
        for i, beacon in enumerate(self.beacons_odd):
            row = i + len(self.beacons_even)
            self.beacons_table.insertRow(row)
            self.beacons_table.setItem(row, 0, QTableWidgetItem(str(beacon['km'])))
            self.beacons_table.setItem(row, 1, QTableWidgetItem(str(beacon['pk'])))
            self.beacons_table.setItem(row, 2, QTableWidgetItem("Нечётный"))
            
            # Кнопка удаления
            delete_btn = QPushButton("×")
            delete_btn.setStyleSheet("font-weight: bold; color: red; background: transparent; border: none;")
            delete_btn.clicked.connect(lambda _, idx=i: self.delete_beacon_odd(idx))
            self.beacons_table.setCellWidget(row, 3, delete_btn)
    
    def delete_beacon_even(self, index):
        if 0 <= index < len(self.beacons_even):
            del self.beacons_even[index]
            self.redraw()
            self.update_status()
            self.update_beacons_table()
    
    def delete_beacon_odd(self, index):
        if 0 <= index < len(self.beacons_odd):
            del self.beacons_odd[index]
            self.redraw()
            self.update_status()
            self.update_beacons_table()
    
    def add_signal(self):
        name = self.signal_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите имя!")
            return
        
        meters = self.signal_meters.value()
        default_state = self.signal_default_state.currentText()
        manual_state = self.signal_manual_state.currentText()
        
        # Если выбрано "Нет ручного переключения", устанавливаем manual_state как None
        if manual_state == "Нет ручного переключения":
            manual_state = None
        
        signal = {
            'name': name,
            'meters': meters,
            'default_state': default_state,
            'manual_state': manual_state
        }
        
        if self.current_direction == 'even':
            self.signals_even.append(signal)
        else:
            self.signals_odd.append(signal)
        
        self.signal_name.clear()
        self.update_status()
        self.update_signals_table()
    
    def update_signals_table(self):
        self.signals_table.setRowCount(0)
        
        # Добавляем чётные сигналы
        for i, signal in enumerate(self.signals_even):
            self.signals_table.insertRow(i)
            self.signals_table.setItem(i, 0, QTableWidgetItem(signal['name']))
            self.signals_table.setItem(i, 1, QTableWidgetItem(str(signal['meters'])))
            self.signals_table.setItem(i, 2, QTableWidgetItem(signal['default_state']))
            self.signals_table.setItem(i, 3, QTableWidgetItem(signal['manual_state'] if signal['manual_state'] else "Нет"))
            
            # Кнопка удаления
            delete_btn = QPushButton("×")
            delete_btn.setStyleSheet("font-weight: bold; color: red; background: transparent; border: none;")
            delete_btn.clicked.connect(lambda _, idx=i: self.delete_signal_even(idx))
            self.signals_table.setCellWidget(i, 4, delete_btn)
        
        # Добавляем нечётные сигналы
        for i, signal in enumerate(self.signals_odd):
            row = i + len(self.signals_even)
            self.signals_table.insertRow(row)
            self.signals_table.setItem(row, 0, QTableWidgetItem(signal['name']))
            self.signals_table.setItem(row, 1, QTableWidgetItem(str(signal['meters'])))
            self.signals_table.setItem(row, 2, QTableWidgetItem(signal['default_state']))
            self.signals_table.setItem(row, 3, QTableWidgetItem(signal['manual_state'] if signal['manual_state'] else "Нет"))
            
            # Кнопка удаления
            delete_btn = QPushButton("×")
            delete_btn.setStyleSheet("font-weight: bold; color: red; background: transparent; border: none;")
            delete_btn.clicked.connect(lambda _, idx=i: self.delete_signal_odd(idx))
            self.signals_table.setCellWidget(row, 4, delete_btn)
    
    def delete_signal_even(self, index):
        if 0 <= index < len(self.signals_even):
            del self.signals_even[index]
            self.update_status()
            self.update_signals_table()
    
    def delete_signal_odd(self, index):
        if 0 <= index < len(self.signals_odd):
            del self.signals_odd[index]
            self.update_status()
            self.update_signals_table()
    
    def add_speed_limit(self):
        from_meters = self.speed_from_meters.value()
        to_meters = self.speed_to_meters.value()
        
        if from_meters >= to_meters:
            QMessageBox.warning(self, "Ошибка", "Начальная точка должна быть раньше конечной!")
            return
        
        speed_limit = {
            'from_meters': from_meters,
            'to_meters': to_meters,
            'speed_kmh': self.speed_limit.value()
        }
        
        self.speed_limits.append(speed_limit)
        self.update_status()
        self.update_speed_limits_table()
    
    def update_speed_limits_table(self):
        self.speed_limits_table.setRowCount(0)
        
        for i, limit in enumerate(self.speed_limits):
            self.speed_limits_table.insertRow(i)
            self.speed_limits_table.setItem(i, 0, QTableWidgetItem(str(limit['from_meters'])))
            self.speed_limits_table.setItem(i, 1, QTableWidgetItem(str(limit['to_meters'])))
            self.speed_limits_table.setItem(i, 2, QTableWidgetItem(f"{limit['speed_kmh']} км/ч"))
            
            # Кнопка удаления
            delete_btn = QPushButton("×")
            delete_btn.setStyleSheet("font-weight: bold; color: red; background: transparent; border: none;")
            delete_btn.clicked.connect(lambda _, idx=i: self.delete_speed_limit(idx))
            self.speed_limits_table.setCellWidget(i, 3, delete_btn)
    
    def delete_speed_limit(self, index):
        if 0 <= index < len(self.speed_limits):
            del self.speed_limits[index]
            self.update_status()
            self.update_speed_limits_table()
    
    def add_station(self):
        name = self.station_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название!")
            return
        
        from_meters = self.station_from_meters.value()
        to_meters = self.station_to_meters.value()
        
        if from_meters >= to_meters:
            QMessageBox.warning(self, "Ошибка", "Начальная точка должна быть раньше конечной!")
            return
        
        station = {
            'name': name,
            'from_meters': from_meters,
            'to_meters': to_meters
        }
        
        self.stations.append(station)
        self.station_name.clear()
        self.update_status()
        self.update_stations_table()
    
    def update_stations_table(self):
        self.stations_table.setRowCount(0)
        
        for i, station in enumerate(self.stations):
            self.stations_table.insertRow(i)
            self.stations_table.setItem(i, 0, QTableWidgetItem(station['name']))
            self.stations_table.setItem(i, 1, QTableWidgetItem(str(station['from_meters'])))
            self.stations_table.setItem(i, 2, QTableWidgetItem(str(station['to_meters'])))
            
            # Кнопка удаления
            delete_btn = QPushButton("×")
            delete_btn.setStyleSheet("font-weight: bold; color: red; background: transparent; border: none;")
            delete_btn.clicked.connect(lambda _, idx=i: self.delete_station(idx))
            self.stations_table.setCellWidget(i, 3, delete_btn)
    
    def delete_station(self, index):
        if 0 <= index < len(self.stations):
            del self.stations[index]
            self.update_status()
            self.update_stations_table()
    
    def draw_plus(self, x, y, color, size=4):
        h_line = QGraphicsLineItem(x - size, y, x + size, y)
        h_line.setPen(QPen(color, 2))
        self.scene.addItem(h_line)
        
        v_line = QGraphicsLineItem(x, y - size, x, y + size)
        v_line.setPen(QPen(color, 2))
        self.scene.addItem(v_line)
    
    def draw_triangle(self, x, y, color, size=6):
        points = [
            QPoint(x, y - size),
            QPoint(x - size, y + size),
            QPoint(x + size, y + size)
        ]
        triangle = QGraphicsPolygonItem(QPolygon(points))
        triangle.setBrush(color)
        triangle.setPen(QPen(color.darker(), 1))
        self.scene.addItem(triangle)
    
    def draw_speed_limit(self, x, y, speed, color):
        circle = QGraphicsEllipseItem(x - 10, y - 10, 20, 20)
        circle.setPen(QPen(color, 2))
        circle.setBrush(QColor(0, 0, 0, 30))
        self.scene.addItem(circle)
        
        self.add_label(x, y, str(speed), color, 8)
    
    def add_label(self, x, y, text, color, size=10):
        label = QGraphicsTextItem(text)
        label.setDefaultTextColor(color)
        label.setFont(QFont("Arial", size))
        label.setPos(x - 10, y - 10)
        self.scene.addItem(label)
    
    def redraw(self):
        if self.pixmap_item is None:
            return
        
        for item in list(self.scene.items()):
            if item != self.pixmap_item:
                self.scene.removeItem(item)
        
        # Рисуем маршруты
        for beacons, color, label in [
            (self.beacons_even, self.color_even, "Ч"),
            (self.beacons_odd, self.color_odd, "Н")
        ]:
            if len(beacons) > 1:
                for i in range(len(beacons) - 1):
                    x1, y1 = beacons[i]['x'], beacons[i]['y']
                    x2, y2 = beacons[i + 1]['x'], beacons[i + 1]['y']
                    
                    line = QGraphicsLineItem(x1, y1, x2, y2)
                    line.setPen(QPen(color, 1))
                    self.scene.addItem(line)
        
        # Рисуем маяки
        if self.show_beacons.isChecked():
            for beacon in self.beacons_even:
                self.draw_plus(beacon['x'], beacon['y'], self.color_even)
                self.add_label(beacon['x'], beacon['y'] - 15, f"{beacon['km']}.{beacon['pk']}", self.color_even)
            
            for beacon in self.beacons_odd:
                self.draw_plus(beacon['x'], beacon['y'], self.color_odd)
                self.add_label(beacon['x'], beacon['y'] - 15, f"{beacon['km']}.{beacon['pk']}", self.color_odd)
        
        # Рисуем сигналы
        if self.show_signals.isChecked():
            for signal in self.signals_even:
                self.draw_triangle(signal['x'], signal['y'], self.color_even, 6)
                self.add_label(signal['x'] + 10, signal['y'] - 10, signal['name'], self.color_even)
            
            for signal in self.signals_odd:
                self.draw_triangle(signal['x'], signal['y'], self.color_odd, 6)
                self.add_label(signal['x'] + 10, signal['y'] - 10, signal['name'], self.color_odd)
        
        # Рисуем ограничения скорости
        if self.show_speed_limits.isChecked():
            for limit in self.speed_limits:
                # Определяем позицию для отображения ограничения
                x_pos = self.last_mouse_pos.x() if self.last_mouse_pos.x() > 0 else 100
                y_pos = self.last_mouse_pos.y() if self.last_mouse_pos.y() > 0 else 100
                self.draw_speed_limit(x_pos, y_pos, limit['speed_kmh'], QColor(0, 150, 0))
    
    def update_status(self):
        self.status_label.setText(
            f"Чётных: {len(self.beacons_even)} | Нечётных: {len(self.beacons_odd)} | "
            f"Сигналов: {len(self.signals_even) + len(self.signals_odd)} | Станций: {len(self.stations)}"
        )
        
        self.beacon_list_label.setText(
            f"Маяков: {len(self.beacons_even) + len(self.beacons_odd)} "
            f"(чётных: {len(self.beacons_even)}, нечётных: {len(self.beacons_odd)})"
        )
        
        self.signal_list_label.setText(f"Сигналов: {len(self.signals_even) + len(self.signals_odd)}")
        self.station_list_label.setText(f"Станций: {len(self.stations)}")
        self.speed_list_label.setText(f"Ограничений: {len(self.speed_limits)}")
    
    def save_route(self):
        # Создаем полный список маяков с указанием направления
        beacons = []
        for beacon in self.beacons_even:
            beacons.append({
                'km': beacon['km'],
                'pk': beacon['pk'],
                'meters': beacon['meters'],
                'x': beacon['x'],
                'y': beacon['y'],
                'direction': 'even'
            })
        
        for beacon in self.beacons_odd:
            beacons.append({
                'km': beacon['km'],
                'pk': beacon['pk'],
                'meters': beacon['meters'],
                'x': beacon['x'],
                'y': beacon['y'],
                'direction': 'odd'
            })
        
        # Сортируем маяки по расстоянию
        beacons.sort(key=lambda x: x['meters'])
        
        # Создаем полный список сигналов с указанием направления
        signals = []
        for signal in self.signals_even:
            signals.append({
                'name': signal['name'],
                'meters': signal['meters'],
                'default_state': signal['default_state'],
                'manual_state': signal['manual_state'],
                'direction': 'even'
            })
        
        for signal in self.signals_odd:
            signals.append({
                'name': signal['name'],
                'meters': signal['meters'],
                'default_state': signal['default_state'],
                'manual_state': signal['manual_state'],
                'direction': 'odd'
            })
        
        # Сортируем сигналы по расстоянию
        signals.sort(key=lambda x: x['meters'])
        
        # Добавляем км и пк для станций
        stations = []
        for station in self.stations:
            # Вычисляем км и пк из метров
            from_km = station['from_meters'] // 1000
            from_pk = (station['from_meters'] % 1000) // 100 + 1
            
            to_km = station['to_meters'] // 1000
            to_pk = (station['to_meters'] % 1000) // 100 + 1
            
            stations.append({
                'name': station['name'],
                'from_meters': station['from_meters'],
                'to_meters': station['to_meters'],
                'from_km': from_km,
                'from_pk': from_pk,
                'to_km': to_km,
                'to_pk': to_pk
            })
        
        # Сортируем станции по началу
        stations.sort(key=lambda x: x['from_meters'])
        
        # Добавляем км и пк для ограничений скорости
        speed_limits = []
        for limit in self.speed_limits:
            # Вычисляем км и пк из метров
            from_km = limit['from_meters'] // 1000
            from_pk = (limit['from_meters'] % 1000) // 100 + 1
            
            to_km = limit['to_meters'] // 1000
            to_pk = (limit['to_meters'] % 1000) // 100 + 1
            
            speed_limits.append({
                'from_meters': limit['from_meters'],
                'to_meters': limit['to_meters'],
                'from_km': from_km,
                'from_pk': from_pk,
                'to_km': to_km,
                'to_pk': to_pk,
                'speed_kmh': limit['speed_kmh']
            })
        
        # Сортируем ограничения по началу
        speed_limits.sort(key=lambda x: x['from_meters'])
        
        # Создаем структуру как в оригинальном route.json
        route_data = {
            "metadata": {
                "name": "MTA Province RZD Route",
                "total_meters": 26700,
                "description": "Маршрут РЖД - 26км 7пк"
            },
            "beacons": beacons,
            "stations": stations,
            "speed_limits": speed_limits,
            "signals": signals
        }
        
        home = os.path.expanduser('~')
        file_path = os.path.join(home, 'route.json')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(route_data, f, ensure_ascii=False, indent=2)
        
        QMessageBox.information(self, "✓ Успех",
                              f"Сохранено в:\n{file_path}\n\n"
                              f"Всего маяков: {len(beacons)}\n"
                              f"Всего сигналов: {len(signals)}\n"
                              f"Станций: {len(stations)}\n"
                              f"Ограничений: {len(speed_limits)}")
    
    def clear_all(self):
        reply = QMessageBox.question(self, "Подтверждение", "Очистить ВСЕ данные?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.beacons_even = []
            self.beacons_odd = []
            self.signals_even = []
            self.signals_odd = []
            self.stations = []
            self.speed_limits = []
            self.redraw()
            self.update_status()
            self.update_beacons_table()
            self.update_signals_table()
            self.update_speed_limits_table()
            self.update_stations_table()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.view.translate(0, 50)
        elif event.key() == Qt.Key_Down:
            self.view.translate(0, -50)
        elif event.key() == Qt.Key_Left:
            self.view.translate(50, 0)
        elif event.key() == Qt.Key_Right:
            self.view.translate(-50, 0)
        elif event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            self.view.scale(1.1, 1.1)
        elif event.key() == Qt.Key_Minus:
            self.view.scale(0.909, 0.909)
        elif event.key() == Qt.Key_Z:
            self.undo_beacon()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if not event.isAutoRepeat():
                self.add_beacon()
        else:
            super().keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RouteDigitizer()
    window.show()
    sys.exit(app.exec_())