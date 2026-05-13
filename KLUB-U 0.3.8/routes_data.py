"""
ROUTES_DATA.PY - ИСПРАВЛЕННАЯ ВЕРСИЯ v2.1
Работа с маршрутом: преобразование координат, получение информации
ИСПРАВЛЕНО:
- speed_limits и stations теперь загружаются из 'objects' в JSON
- Поддержка новой структуры JSON (even_route, odd_route, objects)
"""
import json
import math
from typing import Tuple, Optional, Dict, List

class RouteManager:
    """Менеджер маршрута с поддержкой разных направлений"""
    
    def __init__(self, route_file: str = 'route.json', debug: bool = False, direction: int = 1):
        """
        Загружает маршрут из JSON
        Args:
            route_file: путь к файлу маршрута
            debug: включить подробное логирование
            direction: 1 = четные маршруты (even_route), 2 = нечетные (odd_route)
        """
        self.debug = debug
        self.direction = direction  # 1 = even, 2 = odd
        
        with open(route_file, 'r', encoding='utf-8') as f:
            self.route = json.load(f)
        
        self.metadata = self.route.get('metadata', {})
        
        # Загружаем данные для текущего направления
        self._load_direction_data()
        
        print("[Routes] Маршрут загружен")
        print(f"  Название: {self.metadata.get('name', 'Unknown')}")
        print(f"  Всего метров: {self.metadata.get('total_meters', 0)}")
        print(f"  Текущее направление: {'четные' if self.direction == 1 else 'нечетные'}")
        print(f"  Маяков: {len(self.beacons)}")
        print(f"  Сигналов: {len(self.signals)}")
        print(f"  Ограничений скорости: {len(self.speed_limits)}")
        print(f"  Станций: {len(self.stations)}")
        
        if self.debug:
            print("[Routes] ✓ Режим отладки ВКЛЮЧЕН")

    def _load_direction_data(self):
        """Загружает данные для текущего направления"""
        route_key = 'even_route' if self.direction == 1 else 'odd_route'
        
        if route_key not in self.route:
            raise ValueError(f"В файле маршрута отсутствует '{route_key}'")
        
        route_data = self.route[route_key]
        
        # Beacons и signals загружаются из конкретного маршрута
        self.beacons = route_data.get('beacons', [])
        self.signals = route_data.get('signals', [])
        
        # Stations и speed_limits загружаются из глобального objects (общие для обоих маршрутов)
        objects_data = self.route.get('objects', {})
        self.stations = objects_data.get('stations', [])
        self.speed_limits = objects_data.get('speed_limits', [])

    def set_direction(self, direction: int):
        """
        Изменяет направление маршрута (1 = четные, 2 = нечетные)
        """
        if direction not in (1, 2):
            raise ValueError("Direction должен быть 1 (четные) или 2 (нечетные)")
        
        self.direction = direction
        self._load_direction_data()
        direction_name = 'четные (даже)' if direction == 1 else 'нечетные'
        print(f"[Routes] Направление изменено на: {direction_name}")

    def pixel_to_meters(self, px: int, py: int, debug: bool = False) -> float:
        """
        Преобразует пиксельные координаты в метры с подробным логированием
        """
        
        if self.debug or debug:
            print(f"[Debug] Входные координаты: ({px}, {py})")
        
        # Вычисляем расстояние до каждого маяка
        distances = []
        for beacon in self.beacons:
            dist = math.sqrt((beacon['x'] - px)**2 + (beacon['y'] - py)**2)
            distances.append(dist)
        
        if self.debug or debug:
            print(f"[Debug] Расстояния до маяков (первые 5):")
            for i, (beacon, dist) in enumerate(zip(self.beacons[:5], distances[:5])):
                print(f"  {beacon['km']}км{beacon['pk']}пк ({beacon['meters']}м): {dist:.1f}px")
        
        # Находим два ближайших маяка
        sorted_indices = sorted(range(len(distances)), key=lambda i: distances[i])
        closest_idx = sorted_indices[0]
        second_closest_idx = sorted_indices[1]
        
        if self.debug or debug:
            print(f"[Debug] Ближайшие маяки:")
            print(f"  1-й: {self.beacons[closest_idx]['km']}км{self.beacons[closest_idx]['pk']}пк ({self.beacons[closest_idx]['meters']}м) - {distances[closest_idx]:.1f}px")
            print(f"  2-й: {self.beacons[second_closest_idx]['km']}км{self.beаcons[second_closest_idx]['pk']}пк ({self.beacons[second_closest_idx]['meters']}м) - {distances[second_closest_idx]:.1f}px")
        
        # Если совпадает с маяком - возвращаем точное значение
        if distances[closest_idx] < 5:
            meters = self.beacons[closest_idx]['meters']
            
            if self.debug or debug:
                print(f"[Debug] ТОЧНОЕ СОВПАДЕНИЕ с маяком: {meters}м")
            
            return meters
        
        # Иначе интерполируем между двумя ближайшими
        beacon1 = self.beacons[closest_idx]
        beacon2 = self.beacons[second_closest_idx]
        
        # Используем явные meters из JSON
        m1 = beacon1['meters']
        m2 = beacon2['meters']
        
        # Расстояния в пикселях
        d1 = distances[closest_idx]
        d2 = distances[second_closest_idx]
        
        # Линейная интерполяция
        total_pixel_dist = math.sqrt((beacon2['x'] - beacon1['x'])**2 + 
                                   (beacon2['y'] - beacon1['y'])**2)
        
        if total_pixel_dist == 0:
            if self.debug or debug:
                print(f"[Debug] ОШИБКА: Расстояние между маяками 0px! Возвращаем {m1}м")
            return m1
        
        # ОБРАТНАЯ ИНТЕРПОЛЯЦИЯ ПО РАССТОЯНИЯМ
        weight1 = d2 / (d1 + d2)  # Вес beacon1
        weight2 = d1 / (d1 + d2)  # Вес beacon2
        
        meters = m1 * weight1 + m2 * weight2
        
        if self.debug or debug:
            print("[Debug] ИНТЕРПОЛЯЦИЯ:")
            print(f"  Beacon1: {beacon1['km']}км{beacon1['pk']}пк ({m1}м) - {d1:.1f}px - вес {weight1:.4f}")
            print(f"  Beacon2: {beacon2['km']}км{beacon2['pk']}пк ({m2}м) - {d2:.1f}px - вес {weight2:.4f}")
            print(f"  Расстояние между маяками: {total_pixel_dist:.1f}px")
            print(f"  Результат: {meters:.0f}м (веса: {weight1:.2f}, {weight2:.2f})")
        
        return meters

    def meters_to_km_pk(self, meters: int) -> Tuple[int, int]:
        """Конвертирует метры в км и пк"""
        km = (meters // 1000) + 1
        pk = ((meters % 1000) // 100) + 1
        return km, pk

    def get_speed_limit(self, meters: int) -> Optional[int]:
        """Получает ограничение скорости для текущего положения"""
        for limit in self.speed_limits:
            if limit['from_meters'] <= meters <= limit['to_meters']:
                return limit['speed_kmh']
        return None

    def get_current_station(self, meters: int) -> Optional[str]:
        """Получает название текущей станции"""
        for station in self.stations:
            if station['from_meters'] <= meters <= station['to_meters']:
                return station['name']
        return None

    def get_next_signal(self, meters: int, distance_ahead: int = 2000) -> Optional[Dict]:
        """
        Получает ближайший светофор впереди
        Возвращает: {name, meters, default_state, manual_state, distance}
        """
        next_signals = []
        for signal in self.signals:
            if meters < signal['meters'] <= meters + distance_ahead:
                next_signals.append(signal)
        
        if next_signals:
            closest_signal = min(next_signals, key=lambda s: s['meters'])
            return closest_signal
        return None

    def get_all_signals(self) -> List[Dict]:
        """Получает все светофоры на маршруте"""
        return self.signals.copy()

    def get_signal_by_name(self, name: str) -> Optional[Dict]:
        """Получает светофор по названию"""
        for signal in self.signals:
            if signal['name'].lower() == name.lower():
                return signal
        return None

    def get_location_info(self, px: int, py: int, debug: bool = False) -> Dict:
        """
        Получает полную информацию о текущем положении.
        """
        
        meters = int(self.pixel_to_meters(px, py, debug=debug or self.debug))
        km, pk = self.meters_to_km_pk(meters)
        speed_limit = self.get_speed_limit(meters)
        station = self.get_current_station(meters)
        next_signal = self.get_next_signal(meters)
        
        signal_name = None
        signal_distance = None
        signal_default_state = None
        signal_manual_state = None
        
        if next_signal:
            signal_name = next_signal['name']
            signal_distance = next_signal['meters'] - meters
            signal_default_state = next_signal.get('default_state', '')
            signal_manual_state = next_signal.get('manual_state', '')
        
        return {
            'meters': meters,
            'km': km,
            'pk': pk,
            'speed_limit': speed_limit,
            'station': station,
            'next_signal': signal_name,
            'next_signal_distance': signal_distance,
            'next_signal_default_state': signal_default_state,
            'next_signal_manual_state': signal_manual_state,
            'px': px,
            'py': py,
            'direction': self.direction
        }

# Глобальный экземпляр
route_manager = None

def init_routes(route_file: str = 'route.json', debug: bool = False, direction: int = 1):
    """
    Инициализирует глобальный маршрут
    """
    global route_manager
    route_manager = RouteManager(route_file, debug=debug, direction=direction)
    return route_manager

def set_direction(direction: int):
    """Изменить текущее направление маршрута"""
    if route_manager is None:
        raise RuntimeError("Routes not initialized. Call init_routes() first.")
    route_manager.set_direction(direction)

def get_location_info(px: int, py: int, debug: bool = False) -> Dict:
    """Быстрый доступ к информации о положении"""
    if route_manager is None:
        raise RuntimeError("Routes not initialized. Call init_routes() first.")
    return route_manager.get_location_info(px, py, debug=debug)
