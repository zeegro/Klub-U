"""
UI_CLUB_V3.PY - ИСПРАВЛЕННАЯ ВЕРСИЯ
1. Статус перенесен на отдельную строку ПОД данными.
2. Ячейка СТАНЦИЯ имеет фиксированную ширину.
3. Все данные (Расстояние/Тип/Название) в одну строку.
"""

import sys
import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QPixmap, QIcon
from PyQt5.QtCore import Qt, QRect, QSize
import ctypes


def get_pixel_font(size=10):
    """Пиксельный шрифт - Robot Rondo Dotmatrix для ячеек"""
    font = QFont()
    font.setFamily("Robot Rondo Dotmatrix")
    font.setPointSize(size)
    font.setBold(True)
    return font


def get_label_font(size=9):
    """Шрифт для подписей - Microsoft Sans Serif"""
    font = QFont()
    font.setFamily("Microsoft Sans Serif")
    font.setPointSize(size)
    font.setBold(True)
    return font


# Цвета
BG_COLOR = QColor(45, 47, 50)        # #2D2F32
CELL_BG = QColor(65, 70, 75)         # Чуть светлее фона
GREEN = QColor(0, 255, 0)
YELLOW = QColor(255, 255, 0)
RED = QColor(255, 0, 0)
WHITE = QColor(255, 255, 255)
DARK_GREEN = QColor(0, 50, 0)
DARK_YELLOW = QColor(50, 50, 0)
DARK_RED = QColor(50, 0, 0)
CELL_TEXT = QColor(100, 255, 100)    # Тёмно-салатовый для текста в ячейках
STATION_TEXT = QColor(200, 150, 50)  # Жёлто-оранжевый для станции


class VerticalLampWidget(QWidget):
    """Вертикальные прямоугольные лампочки (8 штук в столбик)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lamp_states = [False] * 8
        self.lamp_colors = [
            GREEN, GREEN, GREEN, GREEN, YELLOW, RED, RED, WHITE,
        ]
        
        self.lamp_width = 50
        self.lamp_height = 20
        self.spacing = 5
        
        total_height = 8 * self.lamp_height + 7 * self.spacing
        self.setMinimumSize(self.lamp_width + 10, total_height + 10)
        self.setMaximumWidth(self.lamp_width + 15)
    
    def set_signal_state(self, signal_state: str):
        """Установить состояние по названию сигнала"""
        self.lamp_states = [False] * 8
        state_lower = signal_state.lower() if signal_state else ""
        
        if 'один зеленый' in state_lower:
            self.lamp_states[0] = True
        elif 'один желтый мигающий' in state_lower or 'желтый мигающий' in state_lower:
            self.lamp_states[0] = True
        elif 'один желтый' in state_lower:
            self.lamp_states[4] = True
        elif 'один красный' in state_lower:
            self.lamp_states[6] = True
        elif 'два желтых' in state_lower:
            self.lamp_states[3] = True
            self.lamp_states[4] = True
        elif 'один лунно-белый' in state_lower:
            self.lamp_states[7] = True
        elif 'один синий' in state_lower:
            self.lamp_states[7] = True
        
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        x = (self.width() - self.lamp_width) // 2
        y = 5
        
        for i in range(8):
            rect = QRect(x, y, self.lamp_width, self.lamp_height)
            
            if i == 5:  # Комбинированная
                if self.lamp_states[i]:
                    top_rect = QRect(x, y, self.lamp_width, self.lamp_height // 2)
                    painter.setBrush(YELLOW)
                    painter.setPen(QPen(YELLOW.lighter(), 1))
                    painter.drawRect(top_rect)
                    
                    bottom_rect = QRect(x, y + self.lamp_height // 2, self.lamp_width, self.lamp_height // 2)
                    painter.setBrush(RED)
                    painter.setPen(QPen(RED.lighter(), 1))
                    painter.drawRect(bottom_rect)
                else:
                    top_rect = QRect(x, y, self.lamp_width, self.lamp_height // 2)
                    painter.setBrush(DARK_YELLOW)
                    painter.setPen(QPen(DARK_YELLOW.lighter(), 1))
                    painter.drawRect(top_rect)
                    
                    bottom_rect = QRect(x, y + self.lamp_height // 2, self.lamp_width, self.lamp_height // 2)
                    painter.setBrush(DARK_RED)
                    painter.setPen(QPen(DARK_RED.lighter(), 1))
                    painter.drawRect(bottom_rect)
            else:
                if self.lamp_states[i]:
                    color = self.lamp_colors[i]
                    painter.setBrush(color)
                    painter.setPen(QPen(color.lighter(), 2))
                else:
                    if i < 4: color = DARK_GREEN
                    elif i == 4: color = DARK_YELLOW
                    elif i == 6: color = DARK_RED
                    else: color = QColor(50, 50, 50)
                    
                    painter.setBrush(color)
                    painter.setPen(QPen(color.lighter(), 1))
                
                painter.drawRect(rect)
                
                if i == 7 and self.lamp_states[i]:
                    painter.setPen(QPen(WHITE))
                    painter.setFont(QFont('Arial', 8, QFont.Bold))
                    painter.drawText(rect, Qt.AlignCenter, 'М')
            
            y += self.lamp_height + self.spacing


class SpeedCellsDisplay(QWidget):
    """Ячейка для отображения скорости с серыми ведущими нулями"""
    
    def __init__(self, color=GREEN, parent=None):
        super().__init__(parent)
        self.speed_value = 0
        self.color = color
        
        # Контейнер для ячеек
        container_frame = QFrame()
        container_frame.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: 2px solid {WHITE.name()};
                padding: 2px;
            }}
        """)
        
        # Макет для ячеек
        cells_layout = QHBoxLayout()
        cells_layout.setContentsMargins(2, 2, 2, 2)
        cells_layout.setSpacing(1)
        
        # Создаём 3 ячейки для цифр скорости
        self.char_labels = []
        for i in range(3):
            label = QLabel("0")
            label.setFont(get_pixel_font(9))
            label.setAlignment(Qt.AlignCenter)
            label.setFixedWidth(14)
            label.setFixedHeight(18)
            
            label.setStyleSheet(f"""
                background-color: {CELL_BG.name()};
                border: 1px solid {WHITE.name()};
                color: {color.name()};
            """)
            
            self.char_labels.append(label)
            cells_layout.addWidget(label)
        
        container_frame.setLayout(cells_layout)
        container_frame.setFixedHeight(26)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container_frame)
        
        self.setLayout(main_layout)
        self.setFixedHeight(26)
    
    def set_speed(self, speed):
        self.speed_value = speed
        speed_str = f"{speed:03d}"
        
        # Находим первую ненулевую цифру
        first_nonzero = 0
        for i, char in enumerate(speed_str):
            if char != '0':
                first_nonzero = i
                break
        
        if speed_str == "000":
            first_nonzero = 3
        
        # Обновляем каждую ячейку
        for i, char in enumerate(speed_str):
            if i < first_nonzero:
                # Ведущие нули - серые
                self.char_labels[i].setStyleSheet(f"""
                    background-color: {CELL_BG.name()};
                    border: 1px solid {WHITE.name()};
                    color: rgb(100, 100, 100);
                """)
            else:
                # Остальные цифры - цветные
                self.char_labels[i].setStyleSheet(f"""
                    background-color: {CELL_BG.name()};
                    border: 1px solid {WHITE.name()};
                    color: {self.color.name()};
                """)
            
            self.char_labels[i].setText(char)



class SpeedometerWidget(QWidget):
    """Полукруговой спидометр с текущей и максимальной скоростью в ячейках"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_speed = 0
        self.max_speed = 60
        self.setFixedSize(350, 420)
        
        # Главный макет - вертикальный
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(8)
        
        # Спидометр - рисуемый виджет
        self.speedometer_paint = SpeedometerPaintWidget(self)
        self.speedometer_paint.setFixedSize(350, 240)
        main_layout.addWidget(self.speedometer_paint)
        
        # Контейнер для скоростей (вертикальный)
        speeds_layout = QVBoxLayout()
        speeds_layout.setContentsMargins(0, 0, 0, 0)
        speeds_layout.setSpacing(3)
        
        # Текущая скорость
        self.current_speed_display = SpeedCellsDisplay(GREEN, self)
        speeds_layout.addWidget(self.current_speed_display, 0, Qt.AlignCenter)
        
        # Максимальная скорость
        self.max_speed_display = SpeedCellsDisplay(RED, self)
        speeds_layout.addWidget(self.max_speed_display, 0, Qt.AlignCenter)
        
        # Подпись км/ч
        label_kmh = QLabel("км/ч")
        label_kmh.setFont(get_label_font(9))
        label_kmh.setAlignment(Qt.AlignCenter)
        label_kmh.setStyleSheet(f"color: {WHITE.name()};")
        speeds_layout.addWidget(label_kmh, 0, Qt.AlignCenter)
        
        main_layout.addLayout(speeds_layout)
        
        self.setLayout(main_layout)
    
    def set_speeds(self, current: int, maximum: int):
        self.current_speed = min(current, 160)
        self.max_speed = maximum
        self.speedometer_paint.set_speeds(self.current_speed, self.max_speed)
        self.current_speed_display.set_speed(self.current_speed)
        self.max_speed_display.set_speed(self.max_speed)
        self.speedometer_paint.update()


class SpeedometerPaintWidget(QWidget):
    """Рисует спидометр с точками индикаторов и скоростями в ячейках"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_speed = 0
        self.max_speed = 60
    
    def set_speeds(self, current: int, maximum: int):
        self.current_speed = current
        self.max_speed = maximum
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        radius = min(w, h) // 2 - 40
        
        # Рисуем дугу спидометра
        painter.setPen(QPen(WHITE, 3))
        start_angle = -30 * 16
        span_angle = 240 * 16
        painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2, start_angle, span_angle)
        
        # Скорости по шкале (0, 20, 40, 60...)
        speeds_angles = [
            (0, -210), (20, -180), (40, -150), (60, -120),
            (80, -90), (100, -60), (120, -30), (140, 0), (160, 30),
        ]
        
        # Рисуем числовую шкалу и точки
        for speed, angle_deg in speeds_angles:
            rad = math.radians(angle_deg)
            
            # Рисуем цифры на шкале
            x_text = cx + (radius + 25) * math.cos(rad)
            y_text = cy + (radius + 25) * math.sin(rad)
            painter.setFont(get_pixel_font(9))
            painter.setPen(WHITE)
            painter.drawText(int(x_text - 15), int(y_text - 10), 30, 20, Qt.AlignCenter, str(speed))
        
        # Генерируем точки для каждых 5 км/ч (0, 5, 10, 15... 160)
        num_points = 32
        angle_step = 240 / num_points
        
        for i in range(num_points):
            speed = i * 5
            angle_deg = -210 + (i * angle_step)
            rad = math.radians(angle_deg)
            
            # ===== ЗЕЛЁНЫЕ ТОЧКИ (текущая скорость) - ТОЛЬКО ОДНА =====
            inner_radius = radius - 10  # Приблизили к линии (было -25)
            x_inner = cx + inner_radius * math.cos(rad)
            y_inner = cy + inner_radius * math.sin(rad)
            
            if speed == self.current_speed:
                # Только точка, соответствующая текущей скорости
                painter.setBrush(GREEN)
                painter.setPen(QPen(GREEN.lighter(), 1))
            else:
                # Остальные серые
                painter.setBrush(QColor(100, 100, 100))
                painter.setPen(QPen(QColor(100, 100, 100), 1))
            
            painter.drawEllipse(int(x_inner) - 3, int(y_inner) - 3, 6, 6)
            
            # ===== КРАСНЫЕ ТОЧКИ (максимальная скорость) - ТОЛЬКО ОДНА =====
            outer_radius = radius + 10
            x_outer = cx + outer_radius * math.cos(rad)
            y_outer = cy + outer_radius * math.sin(rad)
            
            if speed == self.max_speed:
                # Только точка, соответствующая максимальной скорости
                painter.setBrush(RED)
                painter.setPen(QPen(RED.lighter(), 1))
            else:
                # Остальные серые
                painter.setBrush(QColor(100, 100, 100))
                painter.setPen(QPen(QColor(100, 100, 100), 1))
            
            painter.drawEllipse(int(x_outer) - 3, int(y_outer) - 3, 6, 6)
        
        # Подпись км/ч внизу
        painter.setPen(WHITE)
        painter.setFont(get_pixel_font(10))
        painter.drawText(cx - 30, cy + 50, 60, 20, Qt.AlignCenter, "км/ч")


class CellsDisplay(QWidget):
    """Ячейка с отдельными клетками для каждого символа, обёрнутыми в общий контейнер"""
    
    def __init__(self, char_count=9, parent=None, text_color=None):
        super().__init__(parent)
        self.char_count = char_count
        self.text_value = "0" * char_count
        self.text_color = text_color if text_color else CELL_TEXT
        
        # Создаём контейнер (фрейм) для всех ячеек
        container_frame = QFrame()
        container_frame.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: 2px solid {WHITE.name()};
                padding: 2px;
            }}
        """)
        
        # Создаём горизонтальный макет для ячеек
        cells_layout = QHBoxLayout()
        cells_layout.setContentsMargins(2, 2, 2, 2)
        cells_layout.setSpacing(1)  # Маленький промежуток между ячейками
        
        # Создаём отдельные метки для каждого символа
        self.char_labels = []
        for i in range(char_count):
            label = QLabel("0")
            label.setFont(get_pixel_font(9))
            label.setAlignment(Qt.AlignCenter)
            label.setFixedWidth(14)
            label.setFixedHeight(18)
            
            # Стиль для каждой отдельной ячейки
            label.setStyleSheet(f"""
                background-color: {CELL_BG.name()};
                border: 1px solid {WHITE.name()};
                color: {self.text_color.name()};
            """)
            
            self.char_labels.append(label)
            cells_layout.addWidget(label)
        
        container_frame.setLayout(cells_layout)
        container_frame.setFixedHeight(26)  # Зафиксированная высота контейнера
        
        # Добавляем контейнер в главный макет
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(container_frame)
        self.setLayout(main_layout)
        
        # Установка размеров
        self.setFixedHeight(26)
        base_width = char_count * 16 + 10
        self.setFixedWidth(base_width)
    
    def set_value(self, value):
        self.text_value = str(value).zfill(self.char_count)[-self.char_count:]
        
        # Обновляем каждую ячейку отдельно
        for i, char in enumerate(self.text_value):
            if i < len(self.char_labels):
                self.char_labels[i].setText(char)


class ClubUIv3(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        self.current_data = {
            'px': 0, 'py': 0,
            'km': 1, 'pk': 1, 'meters': 0,
            'station': None,
            'speed_limit': 60,
            'current_speed': 0,
            'next_signal': None,
            'next_signal_distance': 0,
            'next_signal_default_state': None,
            'direction': 1,
            'game_time': "00:00",
            'schedule_time': "00:00",
        }
    
    def init_ui(self):
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        # Устанавливаем фиксированный размер окна (не растягивается)
        self.setFixedSize
        self.setStyleSheet(f"background-color: {BG_COLOR.name()};")
        
        # Установка иконки окна
        icon_pixmap = QPixmap("assets/images/logo.png")
        if not icon_pixmap.isNull():
            icon = QIcon(icon_pixmap)
            self.setWindowIcon(icon)
        
        # Инициализация статуса
        self.status = "НЕАКТИВЕН"
        self.status_color = RED
        self.update_window_title()
        
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # ===== ВЕРХНЯЯ СТРОКА: ЛОГОТИП СЛЕВА, ВРЕМЯ ПО ГРАФИКУ СПРАВА =====
        top_header_layout = QHBoxLayout()
        top_header_layout.setSpacing(15)
        
        # ЛОГОТИП (слева)
        logo_label = QLabel()
        logo_pixmap = QPixmap("assets/images/klub-u.png")
        if not logo_pixmap.isNull():
            scaled_pixmap = logo_pixmap.scaledToHeight(26, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        top_header_layout.addWidget(logo_label, 0, Qt.AlignLeft)
        
        top_header_layout.addStretch()
        
        # ВРЕМЯ ПО ГРАФИКУ (справа, формат 00.00)
        schedule_time_label = QLabel("ВРЕМЯ ПО ГРАФИКУ")
        schedule_time_label.setFont(get_label_font(9))
        schedule_time_label.setStyleSheet(f"color: {WHITE.name()};")
        self.display_schedule_time = CellsDisplay(5)  # 5 символов для 00.00
        schedule_time_group = QVBoxLayout()
        schedule_time_group.setContentsMargins(0, 0, 0, 0)
        schedule_time_group.setSpacing(2)
        schedule_time_group.addWidget(schedule_time_label)
        schedule_time_group.addWidget(self.display_schedule_time)
        top_header_layout.addLayout(schedule_time_group)
        
        main_layout.addLayout(top_header_layout)
        
        # ===== ВЕРХНЯЯ ЧАСТЬ =====
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)
        
        # КООРДИНАТА (9 символов с точкой)
        coord_label = QLabel("КООРДИНАТА")
        coord_label.setFont(get_label_font(9))
        coord_label.setStyleSheet(f"color: {WHITE.name()};")
        self.display_coords = CellsDisplay(9)
        coord_group = QVBoxLayout()
        coord_group.setContentsMargins(0, 0, 0, 0)
        coord_group.setSpacing(2)
        coord_group.addWidget(coord_label)
        coord_group.addWidget(self.display_coords)
        
        # СТАНЦИЯ (ФИКСИРОВАННАЯ ШИРИНА, жёлто-оранжевый текст)
        station_label = QLabel("СТАНЦИЯ")
        station_label.setFont(get_label_font(9))
        station_label.setStyleSheet(f"color: {WHITE.name()};")
        # Передаем fixed_width и цвет текста
        self.display_station = CellsDisplay(8, text_color=STATION_TEXT) 
        station_group = QVBoxLayout()
        station_group.setContentsMargins(0, 0, 0, 0)
        station_group.setSpacing(2)
        station_group.addWidget(station_label)
        station_group.addWidget(self.display_station)
        
        # ВРЕМЯ
        time_label = QLabel("ВРЕМЯ")
        time_label.setFont(get_label_font(9))
        time_label.setStyleSheet(f"color: {WHITE.name()};")
        self.display_time = CellsDisplay(5)
        time_group = QVBoxLayout()
        time_group.setContentsMargins(0, 0, 0, 0)
        time_group.setSpacing(2)
        time_group.addWidget(time_label)
        time_group.addWidget(self.display_time)
        
        top_layout.addLayout(coord_group)
        top_layout.addLayout(station_group) # Убрал коэффициент растяжения, чтобы ширина фиксировалась
        top_layout.addLayout(time_group)
        top_layout.addStretch()
        
        main_layout.addLayout(top_layout)
        
        # ===== СРЕДНЯЯ ЧАСТЬ =====
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(40)
        
        self.lamps = VerticalLampWidget()
        middle_layout.addWidget(self.lamps, 0, Qt.AlignTop)
        
        self.speedometer = SpeedometerWidget()
        middle_layout.addWidget(self.speedometer, 0, Qt.AlignTop | Qt.AlignHCenter)
        
        middle_layout.addStretch()
        main_layout.addLayout(middle_layout, 1)
        
        # ===== НИЖНЯЯ ЧАСТЬ: ДАННЫЕ (ОДНА СТРОКА) =====
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # 1. РАССТОЯНИЕ
        dist_label = QLabel("РАССТОЯНИЕ")
        dist_label.setFont(get_label_font(9))
        dist_label.setStyleSheet(f"color: {WHITE.name()};")
        self.display_distance = CellsDisplay(4)
        dist_group = QVBoxLayout()
        dist_group.setContentsMargins(0, 0, 0, 0)
        dist_group.setSpacing(2)
        dist_group.addWidget(dist_label)
        dist_group.addWidget(self.display_distance)
        bottom_layout.addLayout(dist_group)

        # 2. ИНФОРМАЦИЯ (объединённая ячейка для ТИП + НАЗВАНИЕ) - БЕЗ ПОДПИСИ
        self.display_obj_info = CellsDisplay(12)  # 6 символов для типа + 6 для названия
        bottom_layout.addWidget(self.display_obj_info)

        bottom_layout.addStretch() # Распорка справа, чтобы не растягивались

        # Добавляем строку с данными в главный макет
        main_layout.addLayout(bottom_layout) 
        
        # ===== СТРОКА СТАТУСА (ПОД ДАННЫМИ) =====
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 5, 0, 0) # Отступ сверху 5
        
        self.display_status = QLabel("🔴 ОЖИДАНИЕ")
        self.display_status.setFont(get_pixel_font(11))
        self.display_status.setStyleSheet(f"color: {RED.name()};")
        
        status_layout.addWidget(self.display_status)
        status_layout.addStretch() # Прижать статус влево
        
        main_layout.addLayout(status_layout)
        
        self.setLayout(main_layout)
    
    def update_data(self, data: dict):
        self.current_data.update(data)
        self.update_display()
    
    def update_display(self):
        # Координаты с точкой (формат: 0000.0000)
        px = f"{self.current_data['px']:04d}"
        py = f"{self.current_data['py']:04d}"
        self.display_coords.set_value(px + "." + py)
        
        station = self.current_data['station']
        if station:
            self.display_station.set_value(station[:8])
        else:
            self.display_station.set_value("--------")
        
        self.display_time.set_value(self.current_data.get('game_time', "00:00"))
        
        # Время по графику (формат: 00.00)
        schedule_time = self.current_data.get('schedule_time', "00:00")
        # Преобразуем формат для отображения в ячейке
        if isinstance(schedule_time, str) and len(schedule_time) >= 5:
            # "00:00" -> "00.00"
            schedule_display = schedule_time.replace(':', '.')
            self.display_schedule_time.set_value(schedule_display[:5])  # 5 символов для 00.00
        else:
            self.display_schedule_time.set_value("00.00")
        
        current = self.current_data['current_speed']
        maximum = self.current_data['speed_limit'] or 60
        self.speedometer.set_speeds(current, maximum)
        
        signal_state = self.current_data['next_signal_default_state']
        self.lamps.set_signal_state(signal_state)
        
        distance = self.current_data['next_signal_distance']
        if distance is not None:
            self.display_distance.set_value(f"{distance:04d}")
        else:
            self.display_distance.set_value("9999")
        
        # Объединённая информация об объекте (ТИП + НАЗВАНИЕ)
        signal_name = self.current_data['next_signal']
        if signal_name:
            obj_type = "СВЕТОФОР"
            obj_name = signal_name.ljust(6)[:6]
            combined_info = (obj_type + obj_name).ljust(12)[:12]
        else:
            combined_info = "------------"
        
        self.display_obj_info.set_value(combined_info)
        
        # Пример обновления статуса (логика должна быть снаружи)
        # self.set_status("🟢 АКТИВЕН", GREEN.name())
    
    def set_status(self, status: str, color=None):
        self.status = status
        if color:
            # Если color это строка, используем её как есть
            if isinstance(color, str):
                self.display_status.setStyleSheet(f"color: {color};")
            # Если это QColor, используем .name()
            else:
                self.status_color = color
                self.display_status.setStyleSheet(f"color: {color.name()};")
        self.display_status.setText(status)
        self.update_window_title()
    
    def update_window_title(self):
        """Обновляет заголовок окна с форматом: КЛУБ - У | статус"""
        title = f"КЛУБ - У | {self.status}"
        self.setWindowTitle(title)


def make_window_topmost(hwnd):
    try:
        ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 3)
    except:
        pass