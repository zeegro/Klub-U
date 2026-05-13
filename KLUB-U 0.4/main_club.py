"""
MAIN_CLUB.PY - ФИНАЛЬНАЯ ВЕРСИЯ V2
Главное приложение КЛУБ-У v2.0
С поддержкой четных/нечетных маршрутов и расширенными данными сигналов
"""
import sys
import time
import math
from threading import Thread
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal, QObject, Qt
import location_adapter_v2 as location_adapter
import routes_data
from ui_club_v3 import ClubUIv3, make_window_topmost

# ============================================
# РАБОЧИЙ ПРОЦЕСС ПОИСКА КООРДИНАТ
# ============================================
class LocationWorker(QObject):
    """Рабочий процесс поиска координат"""
    location_updated = pyqtSignal(dict)
    status_changed = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.running = False
        self.enabled = False
        self.interval = 0.5
        self.current_direction = 1  # 1 = четные, 2 = нечетные

    def find_nearest_beacons(self, px: int, py: int, count: int = 8):
        """Находит ближайшие маяки"""
        beacons = routes_data.route_manager.beacons
        distances = []
        
        for beacon in beacons:
            dist = math.sqrt((beacon['x'] - px)**2 + (beacon['y'] - py)**2)
            distances.append((beacon, dist))
        
        distances.sort(key=lambda x: x[1])
        return distances[:count]

    def set_direction(self, direction: int):
        """Устанавливает направление маршрута (1=четные, 2=нечетные)"""
        if direction in (1, 2):
            self.current_direction = direction
            routes_data.set_direction(direction)
            print(f"[Worker] Направление изменено на: {'четные' if direction == 1 else 'нечетные'}")

    def run(self):
        """Основной цикл"""
        print("[Worker] Запуск поиска координат...")
        self.running = True
        
        while self.running:
            try:
                if not self.enabled:
                    time.sleep(0.2)
                    continue
                
                coords = location_adapter.find_player_icon()
                
                if coords:
                    px, py = coords
                    location_info = routes_data.route_manager.get_location_info(px, py)
                    
                    # Добавляем ближайшие маяки в информацию
                    nearest_beacons = self.find_nearest_beacons(px, py)
                    location_info['nearest_beacons'] = nearest_beacons
                    
                    # Логируем информацию
                    km = location_info['km']
                    pk = location_info['pk']
                    meters = location_info['meters']
                    speed = location_info['speed_limit']
                    station = location_info['station']
                    signal = location_info['next_signal']
                    signal_dist = location_info['next_signal_distance']
                    
                    log_msg = f"[Worker] {km}км{pk}пк | {meters}м | V={speed} км/ч"
                    if station:
                        log_msg += f" | 🚉 {station}"
                    if signal:
                        log_msg += f" | 🚦 {signal}+{signal_dist}м"
                    
                    print(log_msg)
                    
                    self.location_updated.emit(location_info)
                    self.status_changed.emit("🟢 АКТИВЕН", "#00ff00")
                else:
                    if location_adapter.is_gta_running():
                        self.status_changed.emit("🟡 ИЩЕТ КАРТУ", "#ffff00")
                    else:
                        self.status_changed.emit("🔴 GTA НЕ ЗАПУЩЕНА", "#ff4444")
                
                time.sleep(self.interval)
                
            except Exception as e:
                print(f"[Worker] Ошибка: {e}")
                self.status_changed.emit("🔴 ОШИБКА", "#ff4444")
                time.sleep(1)

    def toggle(self):
        """Включить/отключить поиск"""
        self.enabled = not self.enabled
        if self.enabled:
            print("[Worker] Поиск ВКЛЮЧЕН (Alt+K)")
        else:
            print("[Worker] Поиск ОТКЛЮЧЕН (Alt+K)")

    def stop(self):
        """Остановить"""
        self.running = False

# ============================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ============================================
class ClubApplication:
    """Главное приложение КЛУБ-У"""
    def __init__(self):
        print("[App] Инициализация КЛУБ-У v3.0")
        
        # Инициализируем маршрут (по умолчанию четные маршруты)
        try:
            routes_data.init_routes('route.json', debug=False, direction=1)
            print("[App] ✓ Маршрут загружен (четные маршруты по умолчанию)")
        except Exception as e:
            print(f"[App] ✗ Ошибка загрузки маршрута: {e}")
            sys.exit(1)
        
        # Qt приложение
        self.qt_app = QApplication(sys.argv)
        
        # Основное окно
        self.ui = ClubUIv3()
        self.ui.show()
        
        try:
            hwnd = int(self.ui.winId())
            make_window_topmost(hwnd)
        except:
            pass
        
        # Рабочий процесс
        self.worker = LocationWorker()
        self.worker.location_updated.connect(self.ui.update_data)
        self.worker.status_changed.connect(self.ui.set_status)
        
        self.worker_thread = Thread(target=self.worker.run, daemon=True)
        self.worker_thread.start()
        
        print("[App] ✓ Готово")
        print("[App] Горячие клавиши: ")
        print("[App]   Alt+K - включение/отключение поиска")
        print("[App]   Alt+1 - четные маршруты (направление 1)")
        print("[App]   Alt+2 - нечетные маршруты (направление 2)")
        print("[App]   Alt+S - сохранить отладочный скриншот")
        
        self.setup_hotkeys()

    def setup_hotkeys(self):
        """Настройка горячих клавиш"""
        try:
            import keyboard as kb
            kb.add_hotkey('alt+k', self.toggle_search)
            kb.add_hotkey('alt+1', lambda: self.worker.set_direction(1))
            kb.add_hotkey('alt+2', lambda: self.worker.set_direction(2))
            kb.add_hotkey('alt+s', lambda: location_adapter.save_debug_screenshot())
            print("[App] ✓ Горячие клавиши активированы")
        except ImportError:
            print("[App] ⚠️ keyboard не установлена - горячие клавиши недоступны")
        except Exception as e:
            print(f"[App] ⚠️ Ошибка настройки горячих клавиш: {e}")

    def toggle_search(self):
        """Alt+K - включить/отключить"""
        self.worker.toggle()

    def run(self):
        """Запуск приложения"""
        sys.exit(self.qt_app.exec_())

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════╗
║             КЛУБ-У v3.0                           ║
║  Комплексное Локомотивное Устройство Безопасности ║
║   Alt+K - поиск | Alt+1/2 - маршрут | Alt+S - SS  ║
╚════════════════════════════════════════════════════╝
    """)
    try:
        app = ClubApplication()
        app.run()
    except KeyboardInterrupt:
        print("\n[App] Остановлено пользователем")
    except Exception as e:
        print(f"\n[App] ✗ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
