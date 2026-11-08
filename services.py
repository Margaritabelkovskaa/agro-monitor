import uuid
from datetime import datetime, date
from repositories import *
from models import *


class ОценщикКультуры:
    def __init__(self, norm_repo: NormRepository):
        self.norm_repo = norm_repo

    def определить_фазу(self, культура: Культура) -> ФазаРоста:
        дней = (date.today() - культура.дата_посадки).days
        if дней < 14: return ФазаРоста.ВСХОДЫ
        if дней < 60: return ФазаРоста.ВЕГЕТАЦИЯ
        if дней < 90: return ФазаРоста.ЦВЕТЕНИЕ
        return ФазаРоста.СОЗРЕВАНИЕ

    def _оценить(self, значение: int, норма) -> ОценкаПоказателя:
        lo, hi = норма
        if значение < lo - 10 or значение > hi + 10: return ОценкаПоказателя.КРИТИЧЕСКАЯ
        if значение < lo: return ОценкаПоказателя.НИЗКАЯ
        if значение > hi: return ОценкаПоказателя.ВЫСОКАЯ
        return ОценкаПоказателя.НОРМАЛЬНАЯ

    def сформировать_оценку(self, культура: Культура) -> ОценкаСостояния:
        try:
            влаж = float(культура.влажность_почвы.replace("%", "").strip())
        except:
            return культура.оценка

        нормы = self.norm_repo.find(культура.название, культура.фаза_роста.value)
        культура.влажность_оценка = self._оценить(int(влаж), нормы["влажность"])

        if культура.влажность_оценка == ОценкаПоказателя.КРИТИЧЕСКАЯ: return ОценкаСостояния.КРИТИЧЕСКОЕ
        if культура.влажность_оценка in (
        ОценкаПоказателя.НИЗКАЯ, ОценкаПоказателя.ВЫСОКАЯ): return ОценкаСостояния.ТРЕБУЕТ_ВНИМАНИЯ
        return ОценкаСостояния.УДОВЛЕТВОРИТЕЛЬНОЕ

    def сформировать_рекомендацию(self, культура: Культура) -> str:
        if культура.влажность_оценка == ОценкаПоказателя.КРИТИЧЕСКАЯ:
            return "Критически низкая влажность почвы. Срочно требуется полив!"
        elif культура.влажность_оценка == ОценкаПоказателя.НИЗКАЯ:
            return "Низкая влажность почвы. Рекомендуется организовать полив."
        if культура.температура_оценка == ОценкаПоказателя.ВЫСОКАЯ: return "Высокая температура. Рекомендуется проверить состояние растений."
        return "Все показатели в норме. Дополнительный уход не требуется."


class СервисИстории:
    def __init__(self, obs_repo): self.obs_repo = obs_repo

    def добавить(self, id_культуры, тип, автор, запись, conn=None):
        obs = Наблюдение(str(uuid.uuid4()), id_культуры, datetime.now(), тип, автор, запись)
        self.obs_repo.save(obs, conn);
        return obs

    def история(self, id_культуры): return self.obs_repo.get_by_culture(id_культуры)


class СервисОповещений:
    def __init__(self, notif_repo): self.notif_repo = notif_repo

    def отправить(self, id_культуры, сообщение, важность="Внимание", conn=None):
        у = Уведомление(str(uuid.uuid4()), id_культуры, datetime.now(), сообщение, важность)
        self.notif_repo.save(у, conn);
        return у

    def уведомления(self): return self.notif_repo.get_all()


class ГенераторОтчетов:
    def __init__(self, culture_repo): self.culture_repo = culture_repo

    def сформировать(self, start, end):
        cultures = self.culture_repo.get_all()
        stats = {"total": len(cultures),
                 "ok": sum(1 for c in cultures if c.оценка == ОценкаСостояния.УДОВЛЕТВОРИТЕЛЬНОЕ),
                 "warn": sum(1 for c in cultures if c.оценка == ОценкаСостояния.ТРЕБУЕТ_ВНИМАНИЯ),
                 "crit": sum(1 for c in cultures if c.оценка == ОценкаСостояния.КРИТИЧЕСКОЕ)}
        return stats, cultures


class СервисАдминистрирования:
    def __init__(self, user_repo, plot_repo, sensor_repo, culture_repo):
        self.user_repo = user_repo;
        self.plot_repo = plot_repo;
        self.sensor_repo = sensor_repo;
        self.culture_repo = culture_repo