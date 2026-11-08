from injector import Инжектор
from database import init_db

if __name__ == "__main__":
    init_db()
    injector = Инжектор()
    injector.служба_сбора.запустить_опрос() # Запускаем фоновый опрос
    injector.создать_окно_входа().показать()