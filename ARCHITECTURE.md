# Zombie Survival — архитектура

## 1. Компоненты

Одностраничный vanilla-JS клиент отдаётся Django. REST API используется для команд и первичной загрузки данных; WebSocket Channels — только для мгновенной синхронизации. Бизнес-правила игры находятся в `game/services.py`, поэтому не зависят от транспорта, SQLite или PostgreSQL.

```
Browser (HTML/CSS/ES6) ── REST/JWT ── Django REST Framework
          │                         │
          └──── WebSocket/JWT ──────┴── Django Channels ── Redis (production)
                                            │
                                      SQLite / PostgreSQL
```

Приложения: `accounts` — пользователь и JWT; `rooms` — лобби и доступ; `game` — жизненный цикл, роли, XP, карта; `history` — завершённые матчи; `websocket` — consumer и маршрутизация. В development применяется `InMemoryChannelLayer`, при `REDIS_URL` — Redis channel layer.

## 2. Схема данных

| Модель | Назначение и связи |
|---|---|
| `accounts.User` | Кастомный пользователь (`AbstractUser`): email, nickname, avatar. `User → PlayerStats` 1:1. |
| `rooms.Room` | Настройки комнаты, организатор (`FK User`), code, password_hash, состояние. `Room → RoomPlayer` 1:N. |
| `rooms.RoomPlayer` | Участник комнаты: `FK Room`, `FK User`, ready, current_role, joined_at; уникален по room/user. |
| `game.Game` | Один запуск комнаты: `OneToOne Room`, состояние, started/ended, duration, winner, карта и JSON-геометрия. |
| `game.GameEvent` | Журнал и уведомления: `FK Game`, type, message, payload, created_at. |
| `accounts.PlayerStats` | Агрегаты профиля: XP/level, games/wins, счётчики ролей; `OneToOne User`. |
| `history.GameHistory` | Неизменяемый итог: `FK Game` (nullable), участники JSON, победитель, дата/длительность. |

`Room.players` — ManyToMany с User через `RoomPlayer`; все FK используют `PROTECT` или `CASCADE` по владению. Поле URL базы настраивается `DATABASE_URL`, код моделей не меняется при переходе на PostgreSQL.

## 3. REST API

| Префикс | Методы |
|---|---|
| `/api/auth/` | `register`, `token`, `token/refresh`, `logout` |
| `/api/profile/` | `GET/PATCH me`, `POST avatar` |
| `/api/rooms/` | `GET/POST rooms`, `POST join`, detail, ready, leave, kick, transfer, start, map |
| `/api/game/` | current game, role, stop, finish, timer, roles, events |
| `/api/history/` | `GET` личной истории |
| `/health/` | readiness/liveness JSON |

Все изменяющие методы требуют JWT. Проверки полномочий организатора централизованы в `rooms.permissions.IsOrganizer`; запуск и завершение выполняются транзакционно в сервисах.

## 4. WebSocket

`/ws/rooms/<code>/?token=<access JWT>` добавляет авторизованного участника в группу `room_<code>`. Сообщения сервера: `lobby.updated`, `game.started`, `game.updated`, `game.event`, `game.finished`, `error`. Клиент выполняет экспоненциальное переподключение и после reconnect повторно получает REST snapshot. Изменения делаются REST-командами и рассылаются consumer-ом из сервисов, что исключает дублирование логики.

## 5. Безопасность и эксплуатация

Секреты только в окружении; пароль комнаты хэшируется; JWT короткоживущий; owner-only команды проверяются сервером. Production включает HTTPS/secure cookies, WhiteNoise, структурированное console-логирование, `collectstatic`, миграции в `build.sh`, Gunicorn+Uvicorn worker. Медиа на ephemeral-диске Render годятся для бесплатной демонстрации; для постоянных аватаров достаточно указать `MEDIA_STORAGE` (S3-совместимое хранилище) при дальнейшем расширении.
