from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional
import hashlib
import abc

class ФазаРоста(Enum):
    ВСХОДЫ = "Всходы"
    ВЕГЕТАЦИЯ = "Вегетация"
    ЦВЕТЕНИЕ = "Цветение"
    СОЗРЕВАНИЕ = "Созревание"

class ОценкаСостояния(Enum):
    УДОВЛЕТВОРИТЕЛЬНОЕ = "Удовлетворительное"
    ТРЕБУЕТ_ВНИМАНИЯ = "Требует внимания"
    КРИТИЧЕСКОЕ = "Критическое"

class ОценкаПоказателя(Enum):
    НОРМАЛЬНАЯ = "Нормальная"
    НИЗКАЯ = "Низкая"
    ВЫСОКАЯ = "Высокая"
    КРИТИЧЕСКАЯ = "Критическая"

class СтатусПроблемы(Enum):
    ТРЕБУЕТ_ВНИМАНИЯ = "Требует внимания"
    В_РАБОТЕ = "В работе"
    УСТРАНЕНА = "Устранена"

class ТипНаблюдения(Enum):
    ПОКАЗАТЕЛИ = "Показатели"
    ВИЗУАЛЬНЫЙ_ОСМОТР = "Визуальный осмотр"
    ВЫПОЛНЕННАЯ_РАБОТА = "Выполненная работа"
    ЗАМЕТКА = "Заметка"

@dataclass
class Пользователь:
    id: str
    фио: str
    логин: str
    хэш_пароля: str
    email: str = ""
    статус: str = "Активен"

    def проверить_пароль(self, пароль: str) -> bool:
        return self.хэш_пароля == hashlib.sha256(пароль.encode("utf-8")).hexdigest()

    @staticmethod
    def хэшировать(пароль: str) -> str:
        return hashlib.sha256(пароль.encode("utf-8")).hexdigest()

    def может_регистрировать_культуры(self) -> bool: return False
    def может_вносить_наблюдения(self) -> bool: return False
    def может_смотреть_отчеты(self) -> bool: return False
    def может_управлять_датчиками(self) -> bool: return False

@dataclass
class Агроном(Пользователь):
    def может_регистрировать_культуры(self) -> bool: return True
    def может_вносить_наблюдения(self) -> bool: return True
    def может_смотреть_отчеты(self) -> bool: return True

@dataclass
class РаботникПоля(Пользователь):
    def может_вносить_наблюдения(self) -> bool: return True

@dataclass
class Руководитель(Пользователь):
    def может_смотреть_отчеты(self) -> bool: return True
    def может_управлять_датчиками(self) -> bool: return True

@dataclass
class Участок:
    id: str
    название: str
    площадь: float = 0.0

class IИсточникДанных(abc.ABC):
    @abc.abstractmethod
    def получить_показания(self) -> dict: pass

@dataclass
class Датчик(IИсточникДанных):
    id: str
    тип_датчика: str
    id_участка: Optional[str]
    статус: str
    последнее_показание: str

    def получить_показания(self) -> dict:
        import random
        if self.статус != "Активен":
            return {self.тип_датчика: self.последнее_показание}
        if "Влажность" in self.тип_датчика:
            self.последнее_показание = f"{random.randint(15, 45)} %"
        elif "Температура" in self.тип_датчика:
            self.последнее_показание = f"+{random.randint(18, 30)} °C"
        else:
            self.последнее_показание = f"{random.randint(40000, 60000)} люкс"
        return {self.тип_датчика: self.последнее_показание}

class МетеоСервис(IИсточникДанных):
    def __init__(self):
        self._кэш = {"Температура": "+21 °C", "Влажность почвы": "18 %", "Освещённость": "54 000 люкс"}
    def получить_показания(self) -> dict:
        try: raise ConnectionError("Метеосервис недоступен")
        except ConnectionError: return self._кэш

@dataclass
class Наблюдение:
    id: str
    id_культуры: str
    дата_время: datetime
    тип: ТипНаблюдения
    автор: str
    запись: str

@dataclass
class Проблема:
    id: str
    id_культуры: str
    описание: str
    статус: СтатусПроблемы
    выявлена: datetime

@dataclass
class Культура:
    id: str
    название: str
    сорт: str
    id_участка: str
    дата_посадки: date
    фаза_роста: ФазаРоста
    оценка: ОценкаСостояния
    влажность_почвы: str = ""
    влажность_оценка: ОценкаПоказателя = ОценкаПоказателя.НОРМАЛЬНАЯ
    температура: str = ""
    температура_оценка: ОценкаПоказателя = ОценкаПоказателя.НОРМАЛЬНАЯ
    освещенность: str = ""
    освещенность_оценка: ОценкаПоказателя = ОценкаПоказателя.НОРМАЛЬНАЯ

@dataclass
class Уведомление:
    id: str
    id_культуры: str
    время: datetime
    сообщение: str
    важность: str = "Информация"
    прочитано: bool = False

class IАнализаторИзображений(abc.ABC):
    @abc.abstractmethod
    def проанализировать(self, фото_путь: str) -> str: pass
class АнализаторИзображений(IАнализаторИзображений):
    def проанализировать(self, фото_путь: str) -> str: return "Заболеваний не выявлено"

class IПрогнозистУрожайности(abc.ABC):
    @abc.abstractmethod
    def спрогнозировать(self, культура: Культура) -> float: pass
class ПрогнозистУрожайности(IПрогнозистУрожайности):
    def спрогнозировать(self, культура: Культура) -> float:
        return 45.0 if культура.оценка == ОценкаСостояния.УДОВЛЕТВОРИТЕЛЬНОЕ else 25.0

class IУстройствоПолива(abc.ABC):
    @abc.abstractmethod
    def включить_полив(self, id_участка: str) -> None: pass
class УстройствоПолива(IУстройствоПолива):
    def включить_полив(self, id_участка: str) -> None:
        print(f"[Умный полив] Полив на участке {id_участка} включен.")