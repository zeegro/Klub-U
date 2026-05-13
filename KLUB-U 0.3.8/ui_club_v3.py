"""
UI_CLUB_V3.PY - ИСПРАВЛЕННАЯ ВЕРСИЯ
1. Статус перенесен на отдельную строку ПОД данными.
2. Ячейка СТАНЦИЯ имеет фиксированную ширину.
3. Все данные (Расстояние/Тип/Название) в одну строку.
"""

import sys
import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen
from PyQt5.QtCore import Qt, QRect, QSize
import ctypes

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


def get_pixel_font(size=10):
    """Пиксельный шрифт"""
    return QFont("Courier New", size, QFont.Bold)


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


class SpeedometerWidget(QWidget):
    """Незамкнутый полукруговой спидометр"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_speed = 0
        self.max_speed = 60
        self.setMinimumSize(240, 240)
    
    def set_speeds(self, current: int, maximum: int):
        self.current_speed = min(current, 160)
        self.max_speed = maximum
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        radius = min(w, h) // 2 - 40
        
        speeds_angles = [
            (0, -210), (20, -180), (40, -150), (60, -120),
            (80, -90), (100, -60), (120, -30), (140, 0), (160, 30),
        ]
        
        for speed, angle_deg in speeds_angles:
            rad = math.radians(angle_deg)
            x1 = cx + radius * math.cos(rad)
            y1 = cy + radius * math.sin(rad)
            x2 = cx + (radius - 15) * math.cos(rad)
            y2 = cy + (radius - 15) * math.sin(rad)
            
            painter.setPen(QPen(WHITE, 2))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            x_text = cx + (radius + 25) * math.cos(rad)
            y_text = cy + (radius + 25) * math.sin(rad)
            painter.setFont(get_pixel_font(9))
            painter.setPen(WHITE)
            painter.drawText(int(x_text - 15), int(y_text - 10), 30, 20, Qt.AlignCenter, str(speed))
        
        painter.setPen(QPen(WHITE, 2))
        start_angle = -30 * 16
        span_angle = 240 * 16
        painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2, start_angle, span_angle)        
        
        painter.setFont(get_pixel_font(16))
        painter.setPen(GREEN)
        painter.drawText(cx - 60, cy - 30, 120, 30, Qt.AlignCenter, f"{self.current_speed:3d}")
        
        painter.setPen(RED)
        painter.drawText(cx - 60, cy + 15, 120, 30, Qt.AlignCenter, f"{self.max_speed:3d}")


class CellsDisplay(QLabel):
    """Ячейка с фиксированной или минимальной шириной"""
    
    def __init__(self, char_count=9, parent=None, fixed_width=None):
        super().__init__(parent)
        self.char_count = char_count
        self.text_value = "0" * char_count
        
        # Базовый размер
        self.setMinimumHeight(28)
        base_width = char_count * 22 + 6
        
        self.setMinimumWidth(base_width)
        
        # Если задана фиксированная ширина, ограничиваем рост
        if fixed_width:
            self.setMaximumWidth(fixed_width)
            self.setMinimumWidth(fixed_width) # Делаем её жестко фиксированной
            
        self.set_style()
    
    def set_style(self):
        self.setStyleSheet(f"""
            background-color: {CELL_BG.name()};
            border: 1px solid {WHITE.name()};
            padding: 2px;
            color: {WHITE.name()};
        """)
    
    def set_value(self, value):
        self.text_value = str(value).zfill(self.char_count)[-self.char_count:]
        display_text = " ".join(self.text_value)
        self.setText(display_text)
        self.setFont(get_pixel_font(11))
        self.set_style()


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
        }
    
    def init_ui(self):
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet(f"background-color: {BG_COLOR.name()};")
        self.setWindowTitle("КЛУБ-У v3.2")
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # ===== ВЕРХНЯЯ ЧАСТЬ =====
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)
        
        # КООРДИНАТА
        coord_label = QLabel("КООРДИНАТА")
        coord_label.setFont(QFont("Arial", 9, QFont.Bold))
        coord_label.setStyleSheet(f"color: {WHITE.name()};")
        self.display_coords = CellsDisplay(8)
        coord_group = QVBoxLayout()
        coord_group.setContentsMargins(0, 0, 0, 0)
        coord_group.setSpacing(2)
        coord_group.addWidget(coord_label)
        coord_group.addWidget(self.display_coords)
        
        # СТАНЦИЯ (ФИКСИРОВАННАЯ ШИРИНА)
        station_label = QLabel("СТАНЦИЯ")
        station_label.setFont(QFont("Arial", 9, QFont.Bold))
        station_label.setStyleSheet(f"color: {WHITE.name()};")
        # Передаем fixed_width (например, 200 пикселей)
        self.display_station = CellsDisplay(8, fixed_width=200) 
        station_group = QVBoxLayout()
        station_group.setContentsMargins(0, 0, 0, 0)
        station_group.setSpacing(2)
        station_group.addWidget(station_label)
        station_group.addWidget(self.display_station)
        
        # ВРЕМЯ
        time_label = QLabel("ВРЕМЯ")
        time_label.setFont(QFont("Arial", 9, QFont.Bold))
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
        dist_label.setFont(QFont("Arial", 9, QFont.Bold))
        dist_label.setStyleSheet(f"color: {WHITE.name()};")
        self.display_distance = CellsDisplay(4)
        dist_group = QVBoxLayout()
        dist_group.setContentsMargins(0, 0, 0, 0)
        dist_group.setSpacing(2)
        dist_group.addWidget(dist_label)
        dist_group.addWidget(self.display_distance)
        bottom_layout.addLayout(dist_group)

        # 2. ТИП
        type_label = QLabel("ТИП")
        type_label.setFont(QFont("Arial", 9, QFont.Bold))
        type_label.setStyleSheet(f"color: {WHITE.name()};")
        self.display_obj_type = CellsDisplay(6)
        type_group = QVBoxLayout()
        type_group.setContentsMargins(0, 0, 0, 0)
        type_group.setSpacing(2)
        type_group.addWidget(type_label)
        type_group.addWidget(self.display_obj_type)
        bottom_layout.addLayout(type_group)

        # 3. НАЗВАНИЕ
        name_label = QLabel("НАЗВАНИЕ")
        name_label.setFont(QFont("Arial", 9, QFont.Bold))
        name_label.setStyleSheet(f"color: {WHITE.name()};")
        self.display_obj_name = CellsDisplay(6)
        name_group = QVBoxLayout()
        name_group.setContentsMargins(0, 0, 0, 0)
        name_group.setSpacing(2)
        name_group.addWidget(name_label)
        name_group.addWidget(self.display_obj_name)
        bottom_layout.addLayout(name_group)

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
        px = f"{self.current_data['px']:04d}"
        py = f"{self.current_data['py']:04d}"
        self.display_coords.set_value(px + py)
        
        station = self.current_data['station']
        if station:
            self.display_station.set_value(station[:8])
        else:
            self.display_station.set_value("--------")
        
        self.display_time.set_value(self.current_data.get('game_time', "00:00"))
        
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
        
        signal_name = self.current_data['next_signal']
        if signal_name:
            self.display_obj_type.set_value("SIGNAL")
            self.display_obj_name.set_value(signal_name.ljust(6)[:6])
        else:
            self.display_obj_type.set_value("------")
            self.display_obj_name.set_value("------")
        
        # Пример обновления статуса (логика должна быть снаружи)
        # self.set_status("🟢 АКТИВЕН", GREEN.name())
    
    def set_status(self, status: str, color: str = None):
        self.display_status.setText(status)
        if color:
            self.display_status.setStyleSheet(f"color: {color};")


def make_window_topmost(hwnd):
    try:
        ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 3)
    except:
        pass