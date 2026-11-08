from typing import List, Optional
from datetime import date, datetime
from database import get_connection
from models import *

class UserRepository:
    def find_by_login(self, login: str) -> Optional[Пользователь]:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE login = ?", (login,)).fetchone()
            if not row: return None
            return self._row_to_user(row)

    def get_all(self) -> List[Пользователь]:
        with get_connection() as conn:
            return [self._row_to_user(r) for r in conn.execute("SELECT * FROM users").fetchall()]

    def _row_to_user(self, r) -> Пользователь:
        base_args = (r["id"], r["fio"], r["login"], r["password_hash"], r["email"], r["status"])
        if r["role"] == "Агроном": return Агроном(*base_args)
        if r["role"] == "РаботникПоля": return РаботникПоля(*base_args)
        if r["role"] == "Руководитель": return Руководитель(*base_args)
        return Пользователь(*base_args)

class PlotRepository:
    def get_all(self) -> List[Участок]:
        with get_connection() as conn:
            return [Участок(r["id"], r["name"], r["area"]) for r in conn.execute("SELECT * FROM plots").fetchall()]
    def get_by_id(self, id: str) -> Optional[Участок]:
        with get_connection() as conn:
            r = conn.execute("SELECT * FROM plots WHERE id = ?", (id,)).fetchone()
            return Участок(r["id"], r["name"], r["area"]) if r else None

class SensorRepository:
    def get_all(self) -> List[Датчик]:
        with get_connection() as conn:
            return [Датчик(r["id"], r["type"], r["plot_id"], r["status"], r["last_reading"]) for r in conn.execute("SELECT * FROM sensors").fetchall()]
    def get_by_plot(self, plot_id: str) -> List[Датчик]:
        with get_connection() as conn:
            return [Датчик(r["id"], r["type"], r["plot_id"], r["status"], r["last_reading"]) for r in conn.execute("SELECT * FROM sensors WHERE plot_id = ? AND status = 'Активен'", (plot_id,)).fetchall()]
    def update_reading(self, sensor_id: str, new_reading: str):
        with get_connection() as conn: conn.execute("UPDATE sensors SET last_reading = ? WHERE id = ?", (new_reading, sensor_id))
    def create(self, sensor: Датчик):
        with get_connection() as conn: conn.execute("INSERT INTO sensors VALUES (?, ?, ?, ?, ?)", (sensor.id, sensor.тип_датчика, sensor.id_участка, sensor.статус, sensor.последнее_показание))

class CultureRepository:
    def get_all(self) -> List[Культура]:
        with get_connection() as conn: return [self._row_to_culture(r) for r in conn.execute("SELECT * FROM cultures").fetchall()]
    def get_by_id(self, id: str) -> Optional[Культура]:
        with get_connection() as conn:
            r = conn.execute("SELECT * FROM cultures WHERE id = ?", (id,)).fetchone()
            return self._row_to_culture(r) if r else None
    def get_by_plot(self, plot_id: str) -> List[Культура]:
        with get_connection() as conn: return [self._row_to_culture(r) for r in conn.execute("SELECT * FROM cultures WHERE plot_id = ?", (plot_id,)).fetchall()]
    def save(self, c: Культура):
        with get_connection() as conn:
            conn.execute("""INSERT OR REPLACE INTO cultures 
                (id, name, sort, plot_id, planting_date, growth_phase, state_rating, soil_moisture, soil_moisture_rating, temperature, temperature_rating, light, light_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (c.id, c.название, c.сорт, c.id_участка, str(c.дата_посадки), c.фаза_роста.value, c.оценка.value, c.влажность_почвы, c.влажность_оценка.value, c.температура, c.температура_оценка.value, c.освещенность, c.освещенность_оценка.value))
    def update_moisture(self, culture_id: str, value: str):
        with get_connection() as conn: conn.execute("UPDATE cultures SET soil_moisture = ? WHERE id = ?", (value, culture_id))
    def update_temperature(self, culture_id: str, value: str):
        with get_connection() as conn: conn.execute("UPDATE cultures SET temperature = ? WHERE id = ?", (value, culture_id))
    def _row_to_culture(self, r) -> Культура:
        return Культура(r["id"], r["name"], r["sort"], r["plot_id"], date.fromisoformat(r["planting_date"]),
            next(ФазаРоста(x.value) for x in ФазаРоста if x.value == r["growth_phase"]), next(ОценкаСостояния(x.value) for x in ОценкаСостояния if x.value == r["state_rating"]),
            r["soil_moisture"], next(ОценкаПоказателя(x.value) for x in ОценкаПоказателя if x.value == r["soil_moisture_rating"]),
            r["temperature"], next(ОценкаПоказателя(x.value) for x in ОценкаПоказателя if x.value == r["temperature_rating"]),
            r["light"], next(ОценкаПоказателя(x.value) for x in ОценкаПоказателя if x.value == r["light_rating"]))

class ObservationRepository:
    def get_by_culture(self, culture_id: str) -> List[Наблюдение]:
        with get_connection() as conn: return [self._row_to_obs(r) for r in conn.execute("SELECT * FROM observations WHERE culture_id = ? ORDER BY datetime DESC", (culture_id,)).fetchall()]
    def save(self, o: Наблюдение, conn=None):
        own = conn is None
        if own: conn = get_connection()
        conn.execute("INSERT INTO observations VALUES (?, ?, ?, ?, ?, ?)", (o.id, o.id_культуры, o.дата_время.strftime("%Y-%m-%d %H:%M:%S"), o.тип.value, o.автор, o.запись))
        if own: conn.commit(); conn.close()
    def _row_to_obs(self, r) -> Наблюдение:
        return Наблюдение(r["id"], r["culture_id"], datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M:%S"), next(ТипНаблюдения(x.value) for x in ТипНаблюдения if x.value == r["type"]), r["author"], r["record"])

class ProblemRepository:
    def save(self, p: Проблема, conn=None):
        own = conn is None
        if own: conn = get_connection()
        conn.execute("INSERT INTO problems VALUES (?, ?, ?, ?, ?)", (p.id, p.id_культуры, p.описание, p.статус.value, p.выявлена.strftime("%Y-%m-%d %H:%M:%S")))
        if own: conn.commit(); conn.close()

class NotificationRepository:
    def get_all(self) -> List[Уведомление]:
        with get_connection() as conn:
            return [Уведомление(r["id"], r["culture_id"], datetime.strptime(r["time"], "%Y-%m-%d %H:%M:%S"), r["message"], r["importance"], bool(r["is_read"])) for r in conn.execute("SELECT * FROM notifications ORDER BY time DESC").fetchall()]
    def save(self, n: Уведомление, conn=None):
        own = conn is None
        if own: conn = get_connection()
        conn.execute("INSERT INTO notifications VALUES (?, ?, ?, ?, ?, ?)", (n.id, n.id_культуры, n.время.strftime("%Y-%m-%d %H:%M:%S"), n.сообщение, n.важность, int(n.прочитано)))
        if own: conn.commit(); conn.close()
    def mark_all_read(self):
        with get_connection() as conn: conn.execute("UPDATE notifications SET is_read = 1")

class NormRepository:
    def find(self, culture_name: str, phase: str) -> dict:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM norms WHERE culture_name = ? AND growth_phase = ?", (culture_name, phase)).fetchone()
            if not row: return {"влажность": (20, 60), "температура": (15, 30)}
            return {"влажность": (row["moisture_min"], row["moisture_max"]), "температура": (row["temp_min"], row["temp_max"])}