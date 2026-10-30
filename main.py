from abc import ABC, abstractmethod


# 5. Клас Duration, інтервал часу

class Duration:
    
    MS_IN_SECOND = 1000
    MS_IN_MINUTE = 60 * MS_IN_SECOND
    MS_IN_HOUR = 60 * MS_IN_MINUTE
    MS_IN_DAY = 24 * MS_IN_HOUR

    def __init__(
        self, days=0, hours=0, minutes=0, seconds=0, milliseconds=0
    ):
        total = (
            days * self.MS_IN_DAY
            + hours * self.MS_IN_HOUR
            + minutes * self.MS_IN_MINUTE
            + seconds * self.MS_IN_SECOND
            + milliseconds
        )
        self.total_milliseconds = total

    @property
    def total_milliseconds(self):
        return self._total_ms

    @total_milliseconds.setter
    def total_milliseconds(self, value):
        if value < 0:
            raise ValueError(
                "Час не може бути від'ємним"
            )  # захист від мінусових значень
        self._total_ms = value

    @property
    def days(self):
        return self._total_ms // self.MS_IN_DAY

    @property
    def hours(self):
        return (self._total_ms % self.MS_IN_DAY) // self.MS_IN_HOUR

    @property
    def minutes(self):
        return (self._total_ms % self.MS_IN_HOUR) // self.MS_IN_MINUTE

    @property
    def seconds(self):
        return (self._total_ms % self.MS_IN_MINUTE) // self.MS_IN_SECOND

    @property
    def milliseconds(self):
        return self._total_ms % self.MS_IN_SECOND

    def total_hours(self):
        return self._total_ms / self.MS_IN_HOUR

    def add(self, other):
        return Duration(
            milliseconds=self._total_ms + other.total_milliseconds
        )

    def subtract(self, other):
        if other.total_milliseconds > self._total_ms:
            raise ValueError("Різниця не може бути меншою за нуль")
        return Duration(
            milliseconds=self._total_ms - other.total_milliseconds
        )

    def is_longer_than(self, other):
        return self._total_ms > other.total_milliseconds

    def __repr__(self):
        return f"Duration({self.days}д {self.hours}год {self.minutes}хв)"


# 1.Клас-Item Абстрактний базовий клас для книг і журналів

class Item(ABC):

    library_name = "Центральна міська бібліотека"

    def __init__(self, title: str, year: int):
        self.title = title
        self.year = year

    @abstractmethod
    def loan_days(self) -> int:
        pass

    def describe(self) -> str:
        return f"'{self.title}' ({self.year}), термін: {self.loan_days()} дн. [Бібліотека: {self.library_name}]"

    def loan_period(self) -> Duration:
        # Повертає термін у вигляді нашого Duration
        return Duration(days=self.loan_days())



# 4. Клас- Downloadable для всього

class Downloadable:

    def __init__(self, size_mb: float, **kwargs):
        super().__init__(**kwargs)
        self.size_mb = size_mb

    def download(self):
        return f"Завантажуємо файл розміром {self.size_mb} MB..."



# 2. Взаємозамінні підтипи

class Book(Item):

    def __init__(self, title: str, year: int, author: str):
        super().__init__(title, year)
        self.author = author

    def loan_days(self) -> int:
        return 21

    def describe(self) -> str:
        # Доповнюємо батьківський опис автором
        return f"[Книга] Автор: {self.author}, {super().describe()}"


class Magazine(Item):

    def loan_days(self) -> int:
        return 7

    def describe(self) -> str:
        return f"[Журнал] {super().describe()}"


class AudioBook(Downloadable, Item):

    def __init__(self, title: str, year: int, size_mb: float):
        super().__init__(size_mb=size_mb, title=title, year=year)

    def loan_days(self) -> int:
        return 14

    def describe(self) -> str:
        return f"[Аудіокнига] {super().describe()}, розмір: {self.size_mb} MB"


# 3. інкапсуляція та захист даних

class Reader:

    def __init__(self, name: str, pin: str):
        self.name = name
        self.__pin = pin  
        self._borrowed = [] 
        self._fine = 0.0  

    @property
    def borrowed(self) -> tuple:
        
        return tuple(self._borrowed)

    @property
    def fine(self) -> float:
        return self._fine

    @fine.setter
    def fine(self, value: float):
        if value < 0:
            raise ValueError("Штраф не може бути від'ємним")
        self._fine = float(value)

    def can_borrow(self) -> bool:
        return len(self._borrowed) < 3

    def add_borrowed(self, item: Item):
        if not self.can_borrow():
            raise ValueError(
                f"Читач {self.name} вже взяв максимум (3 примірники)"
            )
        self._borrowed.append(item)

    def remove_borrowed(self, item: Item):
        if item in self._borrowed:
            self._borrowed.remove(item)

    def pay_fine(self, amount: float, pin: str):
        if pin != self.__pin:
            raise PermissionError("Невірний PIN")
        if amount > self._fine:
            raise ValueError("Сума більша за розмір штрафу")
        self._fine -= amount
        return f"Оплачено {amount} грн. Залишок: {self._fine} грн"



# 4. Бібліотека (композиція)

class Library:

    def __init__(self):
        self.items = []
        self.readers = []
        self._status = (
            {}
        ) 

    def add_item(self, item: Item):
        self.items.append(item)
        self._status[item] = None

    def register(self, reader: Reader):
        if reader not in self.readers:
            self.readers.append(reader)

    def lend(self, reader: Reader, item: Item):
        if item not in self.items:
            raise ValueError("Цієї книги немає у фонді")
        if self._status[item] is not None:
            raise ValueError(f"'{item.title}' зараз на руках")
        if not reader.can_borrow():
            raise ValueError(
                f"У читача {reader.name} вичерпано ліміт у 3 книги"
            )

        self._status[item] = reader
        reader.add_borrowed(item)

    def give_back(self, reader: Reader, item: Item):
        if self._status.get(item) != reader:
            raise ValueError(f"Читач {reader.name} не брав '{item.title}'")

        self._status[item] = None
        reader.remove_borrowed(item)

    def overdue(self, item: Item, kept_for: Duration) -> Duration:
        allowed = item.loan_period()
        # Якщо тримали довше за дозволене — повертаємо прострочку
        if kept_for.is_longer_than(allowed):
            return kept_for.subtract(allowed)
        return Duration()  # нуль прострочки



# Test

if __name__ == "__main__":
    print("=== 1. Атрибут класу та абстракція ===")
    book = Book("Кобзар", 1840, "Тарас Шевченко")
    mag = Magazine("National Geographic", 2023)
    audio = AudioBook("Dune", 2021, size_mb=650)

    print("Було:", book.library_name)
    Item.library_name = "Наукова бібліотека ім. Вернадського"
    print("Стало у книги:  ", book.library_name)
    print("Стало у журналу:", mag.library_name)

    print("\n=== 2. Поліморфізм (один цикл для різних типів) ===")
    for item in [book, mag, audio]:
        print(item.describe())

    print("\n=== 3. Інкапсуляція (Reader та PIN) ===")
    reader = Reader("Олена", pin="1234")
    reader.fine = 100.0
    print("Штраф виставлено:", reader.fine)

    try:
        reader.pay_fine(50, pin="0000")  # помилилися з PIN
    except PermissionError as e:
        print("Перевірка PIN спрацювала:", e)

    reader.pay_fine(40, pin="1234")
    print("Після часткової сплати:", reader.fine)

    print("\n=== 4. MRO та міксин Downloadable ===")
    print("Порядок успадкування для AudioBook:")
    for cls in AudioBook.__mro__:
        print(" ->", cls.__name__)
    print(audio.download())

    print("\n=== 5. Розрахунок прострочення через Duration ===")
    dur = Duration(hours=26, minutes=70)
    print(
        f"Duration(26 год, 70 хв) -> {dur.days} дн., {dur.hours} год., {dur.minutes} хв."
    )

    library = Library()
    library.add_item(book)
    library.register(reader)
    library.lend(reader, book)

    real_time = Duration(days=23, hours=5)
    overdue_time = library.overdue(book, kept_for=real_time)
    print(
        f"Прострочено на: {overdue_time.days} дн. {overdue_time.hours} год."
    )