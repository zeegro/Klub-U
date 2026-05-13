import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                             QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QSpinBox, QComboBox, QMessageBox)
from PyQt5.QtGui import QPixmap, QImage, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtWidgets import QGraphicsEllipseItem


class RouteDigitizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.zoom_level = 1.0
        self.image_path = None
        self.points = []  # Список точек: {'x': int, 'y': int, 'km': int, 'pk': int, 'direction': str}
        self.current_direction = 'even'
        
    def initUI(self):
        self.setWindowTitle('Route Digitizer - Оцифровка маршрута')
        self.setGeometry(100, 100, 1400, 900)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QHBoxLayout()
        
        # Левая часть - карта
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("QGraphicsView { background-color: #222; }")
        self.view.mousePressEvent = self.on_map_click
        main_layout.addWidget(self.view, 3)
        
        # Правая часть - контролы
        right_layout = QVBoxLayout()
        
        # Загрузка карты
        load_button = QPushButton('Загрузить карту (F11 скриншот)')
        load_button.clicked.connect(self.load_image)
        right_layout.addWidget(load_button)
        
        # Информация
        right_layout.addWidget(QLabel('═' * 40))
        info_label = QLabel('Информация:\n\nСтрелки: перемещение\n+ / -: приближение\nZ: отмена последней\nEnter: сохранить')
        info_label.setStyleSheet("QLabel { font-size: 11px; color: #666; }")
        right_layout.addWidget(info_label)
        
        right_layout.addWidget(QLabel('═' * 40))
        
        # Выбор направления
        direction_label = QLabel('Направление:')
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(['even (Чётное)', 'odd (Нечётное)'])
        self.direction_combo.currentIndexChanged.connect(self.change_direction)
        right_layout.addWidget(direction_label)
        right_layout.addWidget(self.direction_combo)
        
        # КМ и ПК
        km_label = QLabel('Км:')
        self.km_spin = QSpinBox()
        self.km_spin.setRange(1, 26)
        self.km_spin.setValue(1)
        right_layout.addWidget(km_label)
        right_layout.addWidget(self.km_spin)
        
        pk_label = QLabel('ПК:')
        self.pk_spin = QSpinBox()
        self.pk_spin.setRange(1, 10)
        self.pk_spin.setValue(1)
        right_layout.addWidget(pk_label)
        right_layout.addWidget(self.pk_spin)
        
        right_layout.addWidget(QLabel('═' * 40))
        
        # Координаты мышки
        self.coord_label = QLabel('X: 0 | Y: 0')
        self.coord_label.setStyleSheet("QLabel { font-weight: bold; font-size: 12px; }")
        right_layout.addWidget(self.coord_label)
        
        # Zoom уровень
        self.zoom_label = QLabel('Zoom: 100%')
        self.zoom_label.setStyleSheet("QLabel { color: #666; }")
        right_layout.addWidget(self.zoom_label)
        
        right_layout.addWidget(QLabel('═' * 40))
        
        # Кнопка добавления точки
        add_button = QPushButton('Добавить точку (КЛИК НА КАРТЕ или ENTER)')
        add_button.setStyleSheet("QPushButton { background-color: #2d5a2d; font-weight: bold; padding: 10px; }")
        add_button.clicked.connect(self.add_point)
        right_layout.addWidget(add_button)
        
        # Кнопка отмены
        undo_button = QPushButton('Отмена последней (Z)')
        undo_button.setStyleSheet("QPushButton { background-color: #5a2d2d; padding: 8px; }")
        undo_button.clicked.connect(self.undo_point)
        right_layout.addWidget(undo_button)
        
        # Статус
        right_layout.addWidget(QLabel('═' * 40))
        self.status_label = QLabel('Точек добавлено: 0')
        self.status_label.setStyleSheet("QLabel { font-weight: bold; font-size: 12px; color: #0f0; }")
        right_layout.addWidget(self.status_label)
        
        self.points_list_label = QLabel()
        self.points_list_label.setStyleSheet("QLabel { font-size: 10px; color: #888; max-height: 200px; overflow-y: auto; }")
        right_layout.addWidget(self.points_list_label)
        
        # Кнопка сохранения
        right_layout.addWidget(QLabel('═' * 40))
        save_button = QPushButton('Сохранить в файл (Enter)')
        save_button.setStyleSheet("QPushButton { background-color: #2d5a2d; font-weight: bold; padding: 10px; }")
        save_button.clicked.connect(self.save_points)
        right_layout.addWidget(save_button)
        
        # Кнопка очистки
        clear_button = QPushButton('Очистить всё')
        clear_button.setStyleSheet("QPushButton { background-color: #5a2d2d; padding: 8px; }")
        clear_button.clicked.connect(self.clear_all)
        right_layout.addWidget(clear_button)
        
        right_layout.addStretch()
        
        # Добавляем левую и правую части
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        right_widget.setMaximumWidth(300)
        
        main_layout.addWidget(right_widget, 1)
        central_widget.setLayout(main_layout)
        
        # Фокус на view
        self.view.setFocus()
        self.last_mouse_pos = QPoint(0, 0)
        
    def load_image(self):
        file_dialog = QFileDialog()
        image_path, _ = file_dialog.getOpenFileName(self, "Выберите карту", "", "Image Files (*.png *.jpg *.bmp)")
        
        if image_path:
            self.image_path = image_path
            pixmap = QPixmap(image_path)
            self.pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.clear()
            self.scene.addItem(self.pixmap_item)
            self.scene.setSceneRect(self.pixmap_item.boundingRect())
            
            # Отступ по краям
            self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            self.zoom_level = 1.0
            self.update_zoom_label()
            self.redraw_points()
            
            QMessageBox.information(self, "Успех", f"Карта загружена: {image_path}")
    
    def on_map_click(self, event):
        if self.pixmap_item is None:
            return
            
        scene_pos = self.view.mapToScene(event.pos())
        self.last_mouse_pos = QPoint(int(scene_pos.x()), int(scene_pos.y()))
        self.coord_label.setText(f"X: {int(scene_pos.x())} | Y: {int(scene_pos.y())}")
    
    def add_point(self):
        if self.image_path is None:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите карту!")
            return
        
        km = self.km_spin.value()
        pk = self.pk_spin.value()
        x = self.last_mouse_pos.x()
        y = self.last_mouse_pos.y()
        
        if x == 0 and y == 0:
            QMessageBox.warning(self, "Ошибка", "Нажмите на карту, чтобы установить координаты!")
            return
        
        point = {
            'x': x,
            'y': y,
            'km': km,
            'pk': pk,
            'direction': self.current_direction
        }
        
        self.points.append(point)
        self.redraw_points()
        self.update_status()
        
        # Автоинкремент для удобства
        if pk < 10:
            self.pk_spin.setValue(pk + 1)
        else:
            if km < 26:
                self.km_spin.setValue(km + 1)
                self.pk_spin.setValue(1)
    
    def undo_point(self):
        if self.points:
            self.points.pop()
            self.redraw_points()
            self.update_status()
    
    def redraw_points(self):
        if self.pixmap_item is None:
            return
        
        # Удаляем старые точки
        for item in self.scene.items():
            if isinstance(item, QGraphicsEllipseItem):
                self.scene.removeItem(item)
        
        # Рисуем новые
        for i, point in enumerate(self.points):
            color = QColor(100, 200, 255) if point['direction'] == 'even' else QColor(255, 100, 100)
            ellipse = QGraphicsEllipseItem(point['x'] - 4, point['y'] - 4, 8, 8)
            ellipse.setPen(QPen(color, 2))
            ellipse.setBrush(color)
            self.scene.addItem(ellipse)
    
    def update_status(self):
        even_count = len([p for p in self.points if p['direction'] == 'even'])
        odd_count = len([p for p in self.points if p['direction'] == 'odd'])
        
        self.status_label.setText(f"Чётное: {even_count} | Нечётное: {odd_count} | Всего: {len(self.points)}")
        
        # Список последних 10 точек
        last_points = self.points[-10:]
        points_text = "\n".join([f"{p['direction']:4} {p['km']:2}км{p['pk']}пк  X:{p['x']:4d} Y:{p['y']:4d}" 
                                 for p in last_points])
        self.points_list_label.setText(points_text)
    
    def change_direction(self, index):
        self.current_direction = 'even' if index == 0 else 'odd'
        self.km_spin.setValue(1)
        self.pk_spin.setValue(1)
    
    def save_points(self):
        if not self.points:
            QMessageBox.warning(self, "Ошибка", "Нет точек для сохранения!")
            return
        
        file_path = os.path.join(os.path.dirname(self.image_path) if self.image_path else '.', 
                                'route_points.json')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.points, f, ensure_ascii=False, indent=2)
        
        QMessageBox.information(self, "Успех", f"Точки сохранены в:\n{file_path}")
    
    def clear_all(self):
        reply = QMessageBox.question(self, "Подтверждение", 
                                    "Вы уверены? Это удалит все точки!",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.points = []
            self.redraw_points()
            self.update_status()
    
    def update_zoom_label(self):
        self.zoom_label.setText(f"Zoom: {int(self.zoom_level * 100)}%")
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.view.translate(0, 50)
        elif event.key() == Qt.Key_Down:
            self.view.translate(0, -50)
        elif event.key() == Qt.Key_Left:
            self.view.translate(50, 0)
        elif event.key() == Qt.Key_Right:
            self.view.translate(-50, 0)
        elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            self.zoom_level *= 1.1
            self.view.scale(1.1, 1.1)
            self.update_zoom_label()
        elif event.key() == Qt.Key_Minus:
            self.zoom_level /= 1.1
            self.view.scale(0.909, 0.909)
            self.update_zoom_label()
        elif event.key() == Qt.Key_Z:
            self.undo_point()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.isAutoRepeat():
                return
            self.add_point()
        else:
            super().keyPressEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RouteDigitizer()
    window.show()
    sys.exit(app.exec_())