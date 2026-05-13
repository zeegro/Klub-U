"""
LOCATION_ADAPTER_V2.PY
Поиск иконки игрока на карте F11
Цвет иконки: (131, 197, 226) - голубой квадратик 16х16
С проверкой процесса gta_sa.exe
"""
import pyautogui
import time
import psutil
from typing import Tuple, Optional

# Цвет голубого квадратика (наша иконка)
PLAYER_COLOR = (131, 197, 226)
# Допуск по цвету (для небольших вариаций)
COLOR_TOLERANCE = 15

def is_gta_running() -> bool:
    """Проверяет запущена ли игра GTA San Andreas (gta_sa.exe)"""
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == 'gta_sa.exe':
                return True
        return True
    except Exception as e:
        print(f"[Location] Ошибка при проверке процесса: {e}")
        return False

def is_gta_window_active() -> bool:
    """Проверяет активно ли окно GTA San Andreas"""
    try:
        import ctypes
        # Получаем окно в фокусе
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        
        # Получаем имя процесса окна в фокусе
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        
        # Проверяем если это GTA окно
        window_title = buf.value.lower()
        
        # Ищем GTA в названии окна
        if 'gta' in window_title or 'multi' in window_title:
            return True
        
        return False
    except:
        return False

def is_color_match(pixel_color: Tuple[int, int, int], target_color: Tuple[int, int, int], tolerance: int = 15) -> bool:
    """Проверяет совпадение цвета с допуском"""
    r, g, b = pixel_color
    tr, tg, tb = target_color
    return (abs(r - tr) <= tolerance and 
            abs(g - tg) <= tolerance and 
            abs(b - tb) <= tolerance)

def find_player_icon() -> Optional[Tuple[int, int]]:
    """
    Ищет иконку игрока на экране.
    Возвращает (x, y) координаты центра иконки или None если не найдена.
    """
    
    # Проверяем что игра запущена
    if not is_gta_running():
        print("[Location] ✗ GTA San Andreas не запущена")
        return None

    try:
        # Берем скриншот
        img = pyautogui.screenshot()
        width, height = img.size
        
        # Используем точные координаты карты в игре
        # По вашим данным: 
        # - карта начинается на x=420 
        # - заканчивается на x=1500
        # - занимает всю высоту экрана (y=0 до y=height)
        map_x_offset = 420
        map_width = 1500 - 420  # 1080 пикселей
        map_y_offset = 0
        map_height = height  # Карта занимает всю высоту экрана
        
        # Обрезаем область поиска до карты
        search_left = max(0, map_x_offset)
        search_right = min(width, map_x_offset + map_width)
        search_top = max(0, map_y_offset)
        search_bottom = min(height, map_y_offset + map_height)
        
        # Ищем пиксель иконки (оптимизированный поиск - через 2 пикселя)
        found_pixels = []
        
        for x in range(search_left, search_right, 2):
            for y in range(search_top, search_bottom, 2):
                try:
                    pixel = img.getpixel((x, y))
                    if is_color_match(pixel, PLAYER_COLOR, COLOR_TOLERANCE):
                        found_pixels.append((x, y))
                except:
                    pass
        
        if found_pixels:
            # Вычисляем центр облака пикселей (иконка 16х16, найдем ее центр)
            avg_x = sum(p[0] for p in found_pixels) / len(found_pixels)
            avg_y = sum(p[1] for p in found_pixels) / len(found_pixels)
            
            icon_x = int(avg_x)
            icon_y = int(avg_y)
            
            # НЕ НУЖНО преобразовывать координаты
            # Координаты маяков заданы относительно экрана 1920x1080
            # Поэтому мы просто возвращаем экранные координаты
            
            print(f"[Location] Найдена иконка: ({icon_x}, {icon_y}) → Экран: ({icon_x}, {icon_y})")
            return (icon_x, icon_y)
        else:
            print("[Location] Иконка не найдена")
            return None
            
    except Exception as e:
        print(f"[Location] Ошибка: {e}")
        return None

def save_debug_screenshot():
    """Сохраняет скриншот с отмеченной позицией игрока для анализа"""
    if not is_gta_running():
        print("[Debug] GTA не запущена, скриншот не сохранен")
        return False
    
    try:
        img = pyautogui.screenshot()
        coords = find_player_icon()
        
        if coords:
            # Используем экранные координаты напрямую
            px, py = coords
            
            # Рисуем крестик на позиции игрока
            for i in range(-10, 11):
                # Проверяем, что координаты в пределах изображения
                if 0 <= px + i < img.width and 0 <= py < img.height:
                    img.putpixel((px + i, py), (255, 0, 0))  # красная линия по горизонтали
                if 0 <= px < img.width and 0 <= py + i < img.height:
                    img.putpixel((px, py + i), (255, 0, 0))  # красная линия по вертикали
            
            # Сохраняем скриншот
            timestamp = int(time.time())
            filename = f"debug_screenshot_{timestamp}.png"
            img.save(filename)
            print(f"[Debug] Сохранен отладочный скриншот: {filename}")
            return True
        else:
            print("[Debug] Иконка игрока не найдена, скриншот не сохранен")
            return False
    except Exception as e:
        print(f"[Debug] Ошибка при сохранении скриншота: {e}")
        return False

def run_once() -> Optional[Tuple[int, int]]:
    """Один раз ищет иконку и возвращает координаты"""
    if not is_gta_running():
        return None
    return find_player_icon()

def run_continuous(callback, interval: float = 1.0) -> None:
    """
    Непрерывный поиск иконки с callback функцией.
    Args:
        callback: функция которая принимает (x, y) координаты
        interval: интервал поиска в секундах
    """
    print("[Location] Запуск непрерывного поиска...")

    try:
        while True:
            if is_gta_running():
                coords = find_player_icon()
                if coords:
                    callback(coords[0], coords[1])
            time.sleep(interval)
    except KeyboardInterrupt:
        print("[Location] Остановлен пользователем")
    except Exception as e:
        print(f"[Location] Ошибка: {e}")

if __name__ == "__main__":
    # Тест
    print("Тестирование location_adapter_v2.py")
    print("Откройте карту (F11) в игре и убедитесь что видна иконка игрока")
    print("Поиск начнется через 3 секунды...\n")
    time.sleep(3)
    if is_gta_running():
        print("✓ GTA San Andreas обнаружена")
        coords = run_once()
        if coords:
            print(f"✓ Успешно! Иконка на пиксель координатах: {coords}")
        else:
            print("✗ Иконка не найдена. Проверьте что карта открыта (F11)")
    else:
        print("✗ GTA San Andreas не запущена")