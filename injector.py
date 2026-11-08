import uuid
import threading
import time
import random
from datetime import datetime, date
from repositories import *
from services import *
from models import *
from views import *
from database import get_connection
from settings import ОПРОС_ДАТЧИКОВ_СЕК

class AuthController:
    def __init__(self, user_repo): self.user_repo = user_repo
    def войти(self, логин, пароль):
        user = self.user_repo.find_by_login(логин)
        if user and user.статус == "Активен" and user.проверить_пароль(пароль): return user
        return None

class CultureController:
    def __init__(self, culture_repo, evaluator, sensor_repo):
        self.repo = culture_repo; self.evaluator = evaluator; self.sensor_repo = sensor_repo
    def все(self): return self.repo.get_all()
    def зарегистрировать(self, user: Пользователь, название, сорт, id_участка, дата_посадки):
        if not user.может_регистрировать_культуры(): raise PermissionError("Только Агроном может регистрировать культуры")
        культура = Культура(str(uuid.uuid4()), название, сорт, id_участка, дата_посадки, ФазаРоста.ВСХОДЫ, ОценкаСостояния.УДОВЛЕТВОРИТЕЛЬНОЕ)
        культура.фаза_роста = self.evaluator.определить_фазу(культура)
        культура.влажность_почвы = "30 %"
        культура.температура = "+20 °C"
        культура.освещенность = "50 000 люкс"
        if not self.sensor_repo.get_by_plot(id_участка):
            self.sensor_repo.create(Датчик(str(uuid.uuid4()), "Влажность почвы", id_участка, "Активен", "30 %"))
        self.repo.save(культура)
        return культура

class ObservationController:
    def __init__(self, history, evaluator, culture_repo, notifier, problem_repo):
        self.history = history; self.evaluator = evaluator; self.culture_repo = culture_repo
        self.notifier = notifier; self.problem_repo = problem_repo
    def добавить(self, user: Пользователь, культура, тип, запись):
        if not user.может_вносить_наблюдения(): raise PermissionError("Нет прав на внесение наблюдений")
        conn = get_connection()
        try:
            conn.execute("BEGIN")
            self.history.добавить(культура.id, тип, f"{user.фио}", запись, conn=conn)
            старая = культура.оценка
            новая = self.evaluator.сформировать_оценку(культура)
            культура.оценка = новая
            conn.execute("UPDATE cultures SET state_rating = ?, soil_moisture_rating = ? WHERE id = ?", (новая.value, культура.влажность_оценка.value, культура.id))
            if новая == ОценкаСостояния.КРИТИЧЕСКОЕ and старая != ОценкаСостояния.КРИТИЧЕСКОЕ:
                self.problem_repo.save(Проблема(str(uuid.uuid4()), культура.id, "Критическая влажность", СтатусПроблемы.ТРЕБУЕТ_ВНИМАНИЯ, datetime.now()), conn=conn)
            if новая != старая and новая != ОценкаСостояния.УДОВЛЕТВОРИТЕЛЬНОЕ:
                self.notifier.отправить(культура.id, f"«{культура.название}»: {новая.value}", "Критическое" if новая == ОценкаСостояния.КРИТИЧЕСКОЕ else "Внимание", conn=conn)
            conn.commit()
        except Exception:
            conn.rollback(); raise
        finally: conn.close()

class NotificationController:
    def __init__(self, notifier, repo): self.notifier = notifier; self.repo = repo
    def все(self): return self.notifier.уведомления()
    def mark_all_read(self): self.repo.mark_all_read()

class ReportController:
    def __init__(self, generator): self.generator = generator
    def сформировать(self, start, end): return self.generator.сформировать(start, end)

class AdminController:
    def __init__(self, service, sensor_repo): self.service = service; self.sensor_repo = sensor_repo
    def участки(self): return self.service.plot_repo.get_all()
    def датчики(self): return self.service.sensor_repo.get_all()
    def пользователи(self): return self.service.user_repo.get_all()
    def создать_датчик(self, plot_id: str, тип_датчика: str):
        sensor_id = f"Д-{random.randint(100, 999)}"
        new_sensor = Датчик(sensor_id, тип_датчика, plot_id, "Активен", "0 %")
        self.sensor_repo.create(new_sensor)
        return new_sensor

class СлужбаСбораДанных:
    def __init__(self, culture_repo, sensor_repo, evaluator, notifier):
        self.culture_repo = culture_repo; self.sensor_repo = sensor_repo
        self.evaluator = evaluator; self.notifier = notifier; self._running = False
    def запустить_опрос(self):
        self._running = True
        threading.Thread(target=self._цикл_опроса, daemon=True).start()
    def _цикл_опроса(self):
        while self._running:
            time.sleep(ОПРОС_ДАТЧИКОВ_СЕК)
            try:
                for s in self.sensor_repo.get_all():
                    if s.статус == "Активен" and s.id_участка:
                        s.получить_показания()
                        self.sensor_repo.update_reading(s.id, s.последнее_показание)
                        for c in self.culture_repo.get_by_plot(s.id_участка):
                            if "Влажность" in s.тип_датчика:
                                c.влажность_почвы = s.последнее_показание
                                self.culture_repo.update_moisture(c.id, s.последнее_показание)
                            elif "Температура" in s.тип_датчика:
                                c.температура = s.последнее_показание
                                self.culture_repo.update_temperature(c.id, s.последнее_показание)
                            старая = c.оценка
                            новая = self.evaluator.сформировать_оценку(c)
                            if новая != старая and новая != ОценкаСостояния.УДОВЛЕТВОРИТЕЛЬНОЕ:
                                последние = self.notifier.уведомления()
                                уже_есть = any(n.id_культуры == c.id and not n.прочитано for n in последние)
                                if not уже_есть:
                                    self.notifier.отправить(c.id, f"«{c.название}»: {новая.value}", "Критическое" if новая == ОценкаСостояния.КРИТИЧЕСКОЕ else "Внимание")
                            c.оценка = новая
                            self.culture_repo.save(c)
            except Exception as e: pass

class Инжектор:
    def __init__(self):
        self._init_repositories(); self._init_services(); self._init_controllers(); self._init_extensions()
    def _init_repositories(self):
        self.user_repo = UserRepository(); self.plot_repo = PlotRepository(); self.sensor_repo = SensorRepository()
        self.culture_repo = CultureRepository(); self.obs_repo = ObservationRepository()
        self.problem_repo = ProblemRepository(); self.notif_repo = NotificationRepository(); self.norm_repo = NormRepository()
    def _init_services(self):
        self.evaluator = ОценщикКультуры(self.norm_repo)
        self.history_service = СервисИстории(self.obs_repo)
        self.notification_service = СервисОповещений(self.notif_repo)
        self.report_generator = ГенераторОтчетов(self.culture_repo)
        self.admin_service = СервисАдминистрирования(self.user_repo, self.plot_repo, self.sensor_repo, self.culture_repo)
        self.служба_сбора = СлужбаСбораДанных(self.culture_repo, self.sensor_repo, self.evaluator, self.notification_service)
    def _init_controllers(self):
        self.auth_controller = AuthController(self.user_repo)
        self.culture_controller = CultureController(self.culture_repo, self.evaluator, self.sensor_repo)
        self.observation_controller = ObservationController(self.history_service, self.evaluator, self.culture_repo, self.notification_service, self.problem_repo)
        self.notification_controller = NotificationController(self.notification_service, self.notif_repo)
        self.report_controller = ReportController(self.report_generator)
        self.admin_controller = AdminController(self.admin_service, self.sensor_repo)
    def _init_extensions(self):
        self.image_analyzer = АнализаторИзображений(); self.yield_predictor = ПрогнозистУрожайности(); self.smart_watering = УстройствоПолива()
    def создать_окно_входа(self): return LoginWindow(self.auth_controller, self)
    def создать_главное_окно(self, user): return MainWindow(user, self)
    def создать_окно_карточки(self, cid, user): return CultureCardWindow(cid, user, self)
    def создать_окно_регистрации(self, user): return RegisterWindow(self, user)
    def создать_окно_журнала(self, cid): return JournalWindow(cid, self)
    def создать_окно_наблюдения(self, cid, user): return AddObservationWindow(cid, user, self)
    def создать_окно_оповещений(self, user): return NotificationWindow(self, user)
    def создать_окно_отчета(self): return ReportWindow(self)
    def создать_окно_админа(self, tab=0): return AdminWindow(self, tab)