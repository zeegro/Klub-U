import sys
import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QPixmap, QIcon
from PyQt5.QtCore import Qt, QRect, QSize
import ctypes

#
# UI colors (separated per element — no shared “global green/white/etc”)
#
COLOR_WINDOW_BG = QColor(45, 47, 50)

# CellsDisplay (generic “data cells”)
COLOR_CELLS_CONTAINER_BG = QColor(110, 110, 110)
COLOR_CELLS_CONTAINER_BORDER = QColor(255, 255, 255)
COLOR_CELLS_CELL_BORDER = QColor(255, 255, 255)
COLOR_CELLS_CELL_BG = QColor(65, 70, 75)
COLOR_CELLS_TEXT_DEFAULT = QColor(100, 255, 100)
COLOR_CELLS_TEXT_STATION = QColor(200, 150, 50)

# Labels (captions)
COLOR_LABEL_TEXT_COORDS = QColor(255, 255, 255)
COLOR_LABEL_TEXT_STATION = QColor(255, 255, 255)
COLOR_LABEL_TEXT_TIME = QColor(255, 255, 255)
COLOR_LABEL_TEXT_SCHEDULE_TIME = QColor(255, 255, 255)
COLOR_LABEL_TEXT_DISTANCE = QColor(255, 255, 255)

# Status line
COLOR_STATUS_TEXT_DEFAULT = QColor(255, 68, 68)

# SpeedCellsDisplay (inside speedometer)
COLOR_SPEED_CELLS_CONTAINER_BG = QColor(110, 110, 110)
COLOR_SPEED_CELLS_CONTAINER_BORDER = QColor(255, 255, 255)
COLOR_SPEED_CELLS_CELL_BORDER = QColor(255, 255, 255)
COLOR_SPEED_CELLS_CELL_BG = QColor(65, 70, 75)
COLOR_SPEED_CELLS_TEXT_CURRENT = QColor(0, 255, 0)
COLOR_SPEED_CELLS_TEXT_MAX = QColor(255, 0, 0)
COLOR_SPEED_CELLS_TEXT_LEADING_ZERO = QColor(100, 100, 100)
COLOR_SPEED_UNIT_TEXT = QColor(255, 255, 255)

# Speedometer paint
COLOR_SPEEDOMETER_ARC = QColor(255, 255, 255)
COLOR_SPEEDOMETER_SCALE_TEXT = QColor(255, 255, 255)
COLOR_SPEEDOMETER_DOT_OFF = QColor(100, 100, 100)
COLOR_SPEEDOMETER_DOT_CURRENT_ON = QColor(0, 255, 0)
COLOR_SPEEDOMETER_DOT_MAX_ON = QColor(255, 0, 0)
COLOR_SPEEDOMETER_UNIT_PAINT_TEXT = QColor(255, 255, 255)

# Lamps
LAMP_ON_GREEN_1 = QColor(0, 255, 0)
LAMP_ON_GREEN_2 = QColor(0, 255, 0)
LAMP_ON_GREEN_3 = QColor(0, 255, 0)
LAMP_ON_GREEN_4 = QColor(0, 255, 0)
LAMP_ON_YELLOW = QColor(255, 255, 0)
LAMP_ON_RED_1 = QColor(255, 0, 0)
LAMP_ON_RED_2 = QColor(255, 0, 0)
LAMP_ON_MOON_WHITE = QColor(255, 255, 255)

LAMP_OFF_GREEN = QColor(0, 50, 0)
LAMP_OFF_YELLOW = QColor(50, 50, 0)
LAMP_OFF_RED = QColor(50, 0, 0)
LAMP_OFF_NEUTRAL = QColor(50, 50, 50)
LAMP_MOON_WHITE_TEXT = QColor(255, 255, 255)

# Speedometer sizing — change this to fit your screen
SPEEDOMETER_SCALE = 0.75

def _s(v: int) -> int:
    return max(1, int(round(v * SPEEDOMETER_SCALE)))

# Center speed digits inside speedometer (visual size multiplier)
SPEED_CENTER_MULT = 2


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


class VerticalLampWidget(QWidget):
    """Вертикальные прямоугольные лампочки (8 штук в столбик)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lamp_states = [False] * 8
        self.lamp_colors = [
            LAMP_ON_GREEN_1, LAMP_ON_GREEN_2, LAMP_ON_GREEN_3, LAMP_ON_GREEN_4,
            LAMP_ON_YELLOW, LAMP_ON_RED_1, LAMP_ON_RED_2, LAMP_ON_MOON_WHITE,
        ]
        
        self.lamp_width = _s(55)
        self.setMinimumWidth(self.lamp_width + _s(10))
        self.setMaximumWidth(self.lamp_width + _s(15))
        # По высоте не растягиваем (чтобы не было "хвоста" ниже спидометра)
        self.setFixedHeight(_s(420))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    
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

        # Равномерно распределяем лампы по всей высоте виджета
        top_bottom_margin = _s(6)
        available_h = max(1, self.height() - (top_bottom_margin * 2))
        # Лампы не растягиваем: высота фиксирована, растёт только spacing
        lamp_h = _s(20)
        spacing = max(1, int((available_h - (lamp_h * 8)) / 7)) if available_h > lamp_h * 8 else 1

        stack_h = (lamp_h * 8) + (spacing * 7)
        y = (self.height() - stack_h) // 2
        
        for i in range(8):
            rect = QRect(x, y, self.lamp_width, lamp_h)
            
            if i == 5:  # Комбинированная
                if self.lamp_states[i]:
                    top_rect = QRect(x, y, self.lamp_width, lamp_h // 2)
                    painter.setBrush(LAMP_ON_YELLOW)
                    painter.setPen(QPen(LAMP_ON_YELLOW.lighter(), 1))
                    painter.drawRect(top_rect)
                    
                    bottom_rect = QRect(x, y + lamp_h // 2, self.lamp_width, lamp_h // 2)
                    painter.setBrush(LAMP_ON_RED_1)
                    painter.setPen(QPen(LAMP_ON_RED_1.lighter(), 1))
                    painter.drawRect(bottom_rect)
                else:
                    top_rect = QRect(x, y, self.lamp_width, lamp_h // 2)
                    painter.setBrush(LAMP_OFF_YELLOW)
                    painter.setPen(QPen(LAMP_OFF_YELLOW.lighter(), 1))
                    painter.drawRect(top_rect)
                    
                    bottom_rect = QRect(x, y + lamp_h // 2, self.lamp_width, lamp_h // 2)
                    painter.setBrush(LAMP_OFF_RED)
                    painter.setPen(QPen(LAMP_OFF_RED.lighter(), 1))
                    painter.drawRect(bottom_rect)
            else:
                if self.lamp_states[i]:
                    color = self.lamp_colors[i]
                    painter.setBrush(color)
                    painter.setPen(QPen(color.lighter(), 2))
                else:
                    if i < 4:
                        color = LAMP_OFF_GREEN
                    elif i == 4:
                        color = LAMP_OFF_YELLOW
                    elif i == 6:
                        color = LAMP_OFF_RED
                    else:
                        color = LAMP_OFF_NEUTRAL
                    
                    painter.setBrush(color)
                    painter.setPen(QPen(color.lighter(), 1))
                
                painter.drawRect(rect)
                
                if i == 7 and self.lamp_states[i]:
                    painter.setPen(QPen(LAMP_MOON_WHITE_TEXT))
                    painter.setFont(QFont('Arial', 8, QFont.Bold))
                    painter.drawText(rect, Qt.AlignCenter, 'М')
            
            y += lamp_h + spacing


class SpeedCellsDisplay(QWidget):
    """Ячейка для отображения скорости с серыми ведущими нулями"""
    
    def __init__(self, text_color_on: QColor, parent=None):
        super().__init__(parent)
        self.speed_value = 0
        self.text_color_on = text_color_on

        border = 2
        cell_w = _s(16) * SPEED_CENTER_MULT
        cell_h = _s(20) * SPEED_CENTER_MULT
        pad = _s(4)
        gap = _s(2)
        
        # Контейнер для ячеек
        container_frame = QFrame()
        container_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_SPEED_CELLS_CONTAINER_BG.name()};
                border: 2px solid {COLOR_SPEED_CELLS_CONTAINER_BORDER.name()};
            }}
        """)
        
        # Макет для ячеек
        cells_layout = QHBoxLayout()
        cells_layout.setContentsMargins(pad, pad, pad, pad)
        cells_layout.setSpacing(gap)
        
        # Создаём 3 ячейки для цифр скорости
        self.char_labels = []
        for i in range(3):
            label = QLabel("0")
            label.setFont(get_pixel_font(9 * SPEED_CENTER_MULT))
            label.setAlignment(Qt.AlignCenter)
            label.setFixedSize(cell_w, cell_h)
            
            label.setStyleSheet(f"""
                background-color: {COLOR_SPEED_CELLS_CELL_BG.name()};
                border: 1px solid {COLOR_SPEED_CELLS_CELL_BORDER.name()};
                color: {self.text_color_on.name()};
                padding: 0px;
                margin: 0px;
            """)
            
            self.char_labels.append(label)
            cells_layout.addWidget(label)
        
        container_frame.setLayout(cells_layout)
        inner_w = (cell_w * 3) + (pad * 2) + (gap * 2)
        inner_h = (cell_h) + (pad * 2)
        container_frame.setFixedSize(inner_w + (border * 2), inner_h + (border * 2))
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container_frame, 0, Qt.AlignCenter)
        
        self.setLayout(main_layout)
        self.setFixedSize(container_frame.size())
    
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
                    background-color: {COLOR_SPEED_CELLS_CELL_BG.name()};
                    border: 1px solid {COLOR_SPEED_CELLS_CELL_BORDER.name()};
                    color: {COLOR_SPEED_CELLS_TEXT_LEADING_ZERO.name()};
                """)
            else:
                # Остальные цифры - цветные
                self.char_labels[i].setStyleSheet(f"""
                    background-color: {COLOR_SPEED_CELLS_CELL_BG.name()};
                    border: 1px solid {COLOR_SPEED_CELLS_CELL_BORDER.name()};
                    color: {self.text_color_on.name()};
                """)
            
            self.char_labels[i].setText(char)



class SpeedometerWidget(QWidget):
    """Полукруговой спидометр с текущей и максимальной скоростью в ячейках"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_speed = 0
        self.max_speed = 0
        # Размер виджета спидометра управляется SPEEDOMETER_SCALE
        self.setFixedSize(_s(420), _s(420))
        
        # Главный макет - вертикальный
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)
        
        # Спидометр - рисуемый виджет
        self.speedometer_paint = SpeedometerPaintWidget(self)
        self.speedometer_paint.setFixedSize(_s(420), _s(420))
        main_layout.addWidget(self.speedometer_paint)

        # Оверлей (внутри спидометра по центру)
        self.current_speed_display = SpeedCellsDisplay(COLOR_SPEED_CELLS_TEXT_CURRENT, self.speedometer_paint)
        self.max_speed_display = SpeedCellsDisplay(COLOR_SPEED_CELLS_TEXT_MAX, self.speedometer_paint)
        self.label_kmh = QLabel("км/ч", self.speedometer_paint)
        self.label_kmh.setFont(get_label_font(max(8, _s(9) // 1)))
        self.label_kmh.setAlignment(Qt.AlignCenter)
        self.label_kmh.setStyleSheet(f"color: {COLOR_SPEED_UNIT_TEXT.name()}; background: transparent;")

        self.speedometer_paint.set_overlay_widgets(
            self.current_speed_display, self.max_speed_display, self.label_kmh
        )
        
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
        self.max_speed = 0
        self._overlay_current = None
        self._overlay_max = None
        self._overlay_unit = None
    
    def set_speeds(self, current: int, maximum: int):
        self.current_speed = current
        self.max_speed = maximum

    def set_overlay_widgets(self, current_widget: QWidget, max_widget: QWidget, unit_label: QLabel):
        self._overlay_current = current_widget
        self._overlay_max = max_widget
        self._overlay_unit = unit_label
        self._position_overlay()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_overlay()

    def _position_overlay(self):
        if not self._overlay_current or not self._overlay_max or not self._overlay_unit:
            return

        cx = self.width() // 2
        cy = self.height() // 2

        gap = _s(6)
        w1, h1 = self._overlay_current.sizeHint().width(), self._overlay_current.sizeHint().height()
        w2, h2 = self._overlay_max.sizeHint().width(), self._overlay_max.sizeHint().height()
        wu, hu = self._overlay_unit.sizeHint().width(), self._overlay_unit.sizeHint().height()

        total_h = h1 + gap + h2 + gap + hu

        # Центрируем внутри спидометра ровно по центру
        start_y = cy - total_h // 2

        self._overlay_current.move(cx - w1 // 2, start_y)
        self._overlay_max.move(cx - w2 // 2, start_y + h1 + gap)
        self._overlay_unit.setFixedWidth(max(w1, w2))
        self._overlay_unit.move(cx - self._overlay_unit.width() // 2, start_y + h1 + gap + h2 + gap)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        radius = min(w, h) // 2 - _s(50)
        
        # Рисуем дугу спидометра
        painter.setPen(QPen(COLOR_SPEEDOMETER_ARC, _s(3)))
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
            # Чуть дальше от точек скорости
            x_text = cx + (radius + _s(32)) * math.cos(rad)
            y_text = cy + (radius + _s(32)) * math.sin(rad)
            painter.setFont(get_pixel_font(max(8, _s(9) // 1)))
            painter.setPen(COLOR_SPEEDOMETER_SCALE_TEXT)
            painter.drawText(int(x_text - 15), int(y_text - 10), 30, 20, Qt.AlignCenter, str(speed))
        
        # Генерируем точки для каждых 5 км/ч (0, 5, 10, 15... 160)
        # Включая 160 км/ч: 0..160 шаг 5 => 33 точки
        num_points = 33
        angle_step = 240 / (num_points - 1)
        
        for i in range(num_points):
            speed = i * 5
            angle_deg = -210 + (i * angle_step)
            rad = math.radians(angle_deg)
            
            # ===== ЗЕЛЁНЫЕ ТОЧКИ (текущая скорость) - ТОЛЬКО ОДНА =====
            inner_radius = radius - _s(10)
            x_inner = cx + inner_radius * math.cos(rad)
            y_inner = cy + inner_radius * math.sin(rad)
            
            if speed == self.current_speed:
                # Только точка, соответствующая текущей скорости
                painter.setBrush(COLOR_SPEEDOMETER_DOT_CURRENT_ON)
                painter.setPen(QPen(COLOR_SPEEDOMETER_DOT_CURRENT_ON.lighter(), 1))
            else:
                # Остальные серые
                painter.setBrush(COLOR_SPEEDOMETER_DOT_OFF)
                painter.setPen(QPen(COLOR_SPEEDOMETER_DOT_OFF, 1))
            
            dot = _s(7)
            painter.drawEllipse(int(x_inner) - dot // 2, int(y_inner) - dot // 2, dot, dot)
            
            # ===== КРАСНЫЕ ТОЧКИ (максимальная скорость) - ТОЛЬКО ОДНА =====
            outer_radius = radius + _s(10)
            x_outer = cx + outer_radius * math.cos(rad)
            y_outer = cy + outer_radius * math.sin(rad)
            
            if speed == self.max_speed:
                # Только точка, соответствующая максимальной скорости
                painter.setBrush(COLOR_SPEEDOMETER_DOT_MAX_ON)
                painter.setPen(QPen(COLOR_SPEEDOMETER_DOT_MAX_ON.lighter(), 1))
            else:
                # Остальные серые
                painter.setBrush(COLOR_SPEEDOMETER_DOT_OFF)
                painter.setPen(QPen(COLOR_SPEEDOMETER_DOT_OFF, 1))
            
            dot = _s(7)
            painter.drawEllipse(int(x_outer) - dot // 2, int(y_outer) - dot // 2, dot, dot)


class CellsDisplay(QWidget):
    """Ячейка с отдельными клетками для каждого символа, обёрнутыми в общий контейнер"""
    
    def __init__(self, char_count=9, parent=None, text_color=None):
        super().__init__(parent)
        self.char_count = char_count
        self.text_value = "0" * char_count
        self.text_color = text_color if text_color else COLOR_CELLS_TEXT_DEFAULT

        border = 2
        cell_w = 16
        cell_h = 20
        pad = 4
        gap = 2
        
        # Создаём контейнер (фрейм) для всех ячеек
        container_frame = QFrame()
        container_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CELLS_CONTAINER_BG.name()};
                border: 2px solid {COLOR_CELLS_CONTAINER_BORDER.name()};
            }}
        """)
        
        # Создаём горизонтальный макет для ячеек
        cells_layout = QHBoxLayout()
        cells_layout.setContentsMargins(pad, pad, pad, pad)
        cells_layout.setSpacing(gap)
        
        # Создаём отдельные метки для каждого символа
        self.char_labels = []
        for i in range(char_count):
            label = QLabel("0")
            label.setFont(get_pixel_font(9))
            label.setAlignment(Qt.AlignCenter)
            label.setFixedSize(cell_w, cell_h)
            
            # Стиль для каждой отдельной ячейки
            label.setStyleSheet(f"""
                background-color: {COLOR_CELLS_CELL_BG.name()};
                border: 1px solid {COLOR_CELLS_CELL_BORDER.name()};
                color: {self.text_color.name()};
                padding: 0px;
                margin: 0px;
            """)
            
            self.char_labels.append(label)
            cells_layout.addWidget(label)
        
        container_frame.setLayout(cells_layout)
        inner_w = (cell_w * char_count) + (pad * 2) + (gap * max(0, char_count - 1))
        inner_h = (cell_h) + (pad * 2)
        container_frame.setFixedSize(inner_w + (border * 2), inner_h + (border * 2))
        
        # Добавляем контейнер в главный макет
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(container_frame, 0, Qt.AlignCenter)
        self.setLayout(main_layout)
        
        # Установка размеров
        self.setFixedSize(container_frame.size())
    
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
        self.setWindowFlags(
            Qt.Window | Qt.WindowStaysOnTopHint | Qt.MSWindowsFixedSizeDialogHint
        )
        # Размер окна берём от контента (без хардкода), но без растягивания
        self.setMinimumSize(QSize(0, 0))
        self.setStyleSheet(f"background-color: {COLOR_WINDOW_BG.name()};")
        
        # Установка иконки окна
        icon_pixmap = QPixmap("assets/images/logo.png")
        if not icon_pixmap.isNull():
            icon = QIcon(icon_pixmap)
            self.setWindowIcon(icon)
        
        # Инициализация статуса
        self.status = "НЕАКТИВЕН"
        self.status_color = COLOR_STATUS_TEXT_DEFAULT
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
        schedule_time_label.setStyleSheet(f"color: {COLOR_LABEL_TEXT_SCHEDULE_TIME.name()};")
        # 8 символов: "␠00:00␠␠"
        self.display_schedule_time = CellsDisplay(8)
        schedule_time_group = QVBoxLayout()
        schedule_time_group.setContentsMargins(0, 0, 0, 0)
        schedule_time_group.setSpacing(2)
        schedule_time_group.addWidget(schedule_time_label, 0, Qt.AlignRight)
        schedule_time_group.addWidget(self.display_schedule_time, 0, Qt.AlignRight)

        schedule_time_widget = QWidget()
        schedule_time_widget.setLayout(schedule_time_group)
        schedule_time_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        schedule_time_widget.setFixedWidth(self.display_schedule_time.width())
        top_header_layout.addWidget(schedule_time_widget, 0, Qt.AlignRight)
        
        main_layout.addLayout(top_header_layout)
        
        # ===== ВЕРХНЯЯ ЧАСТЬ =====
        top_layout = QHBoxLayout()
        top_layout.setSpacing(7)
        
        # КООРДИНАТА (9 символов с точкой)
        coord_label = QLabel("КООРДИНАТА")
        coord_label.setFont(get_label_font(9))
        coord_label.setStyleSheet(f"color: {COLOR_LABEL_TEXT_COORDS.name()};")
        self.display_coords = CellsDisplay(9)
        coord_group = QVBoxLayout()
        coord_group.setContentsMargins(0, 0, 0, 0)
        coord_group.setSpacing(2)
        coord_group.addWidget(coord_label)
        coord_group.addWidget(self.display_coords)
        
        # СТАНЦИЯ (ФИКСИРОВАННАЯ ШИРИНА, жёлто-оранжевый текст)
        station_label = QLabel("СТАНЦИЯ")
        station_label.setFont(get_label_font(9))
        station_label.setStyleSheet(f"color: {COLOR_LABEL_TEXT_STATION.name()};")
        # Передаем fixed_width и цвет текста
        self.display_station = CellsDisplay(8, text_color=COLOR_CELLS_TEXT_STATION)
        station_group = QVBoxLayout()
        station_group.setContentsMargins(0, 0, 0, 0)
        station_group.setSpacing(2)
        station_group.addWidget(station_label)
        station_group.addWidget(self.display_station)
        
        # ВРЕМЯ
        time_label = QLabel("ВРЕМЯ")
        time_label.setFont(get_label_font(9))
        time_label.setStyleSheet(f"color: {COLOR_LABEL_TEXT_TIME.name()};")
        self.display_time = CellsDisplay(8)
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
        dist_label.setStyleSheet(f"color: {COLOR_LABEL_TEXT_DISTANCE.name()};")
        self.display_distance = CellsDisplay(4)
        dist_group = QVBoxLayout()
        dist_group.setContentsMargins(0, 0, 0, 0)
        dist_group.setSpacing(2)
        dist_group.addWidget(dist_label)
        dist_group.addWidget(self.display_distance)
        bottom_layout.addLayout(dist_group)

        # 2. ИНФОРМАЦИЯ (объединённая ячейка для ТИП + НАЗВАНИЕ) - БЕЗ ПОДПИСИ
        self.display_obj_info = CellsDisplay(12)  # 6 символов для типа + 6 для названия
        bottom_layout.addWidget(self.display_obj_info, 0, Qt.AlignBottom)

        bottom_layout.addStretch() # Распорка справа, чтобы не растягивались

        # Добавляем строку с данными в главный макет
        main_layout.addLayout(bottom_layout) 
        
        self.setLayout(main_layout)
        self.adjustSize()
        self.setFixedSize(self.sizeHint())
    
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
        
        # Время (формат: 00.00.00)
        game_time = self.current_data.get('game_time', "00:00")
        if isinstance(game_time, str) and len(game_time) >= 5:
            # "HH:MM" -> "HH.MM.00"
            self.display_time.set_value(f"{game_time[:5].replace(':', '.')}.00")
        else:
            self.display_time.set_value("00.00.00")
        
        # Время по графику (формат: "␠00:00␠␠")
        schedule_time = self.current_data.get('schedule_time', "00:00")
        if isinstance(schedule_time, str) and len(schedule_time) >= 5:
            schedule_display = schedule_time[:5]
        else:
            schedule_display = "00:00"
        self.display_schedule_time.set_value(f" {schedule_display}  ")
        
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
        # Цвет оставляем на будущее, но UI-строки статуса больше нет
        if color and not isinstance(color, str):
            self.status_color = color
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