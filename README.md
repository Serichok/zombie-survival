# Zombie Survival

Production-ready Django/Channels приложение для уличной игры. Технические решения, модели и сообщения real-time описаны в [ARCHITECTURE.md](ARCHITECTURE.md).

## Локальный запуск

Нужен Python 3.11+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py makemigrations accounts rooms game history
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Откройте `http://127.0.0.1:8000/`. Для проверки ASGI в development можно также выполнить `daphne -b 127.0.0.1 -p 8000 backend.asgi:application`. Не запускайте оба сервера на одном порту. API доступен по `/api/`, health-check — `/health/`; WebSocket: `ws://127.0.0.1:8000/ws/rooms/<CODE>/?token=<JWT>`.

SQLite — значение по умолчанию. Для PostgreSQL добавьте `DATABASE_URL=postgresql://...` в `.env`; миграции и бизнес-логика останутся теми же. Добавьте `REDIS_URL=redis://...`, чтобы переключить Channels с InMemory на Redis.

## Публикация на GitHub

```powershell
git init
git add .
git commit -m "Initial Zombie Survival release"
git branch -M main
git remote add origin https://github.com/<YOUR_ACCOUNT>/zombie-survival.git
git push -u origin main
```

Не коммитьте `.env`, `db.sqlite3`, `media/` и `staticfiles/`: они уже исключены `.gitignore`.

## Бесплатный Render — пошагово

1. Загрузите репозиторий на GitHub командами выше.
2. В [Render](https://render.com) выберите **New → Web Service**, подключите GitHub и выберите репозиторий.
3. Выберите **Free**, Runtime **Python**, регион ближе к игрокам. Задайте Build Command: `bash build.sh` и Start Command: `gunicorn backend.asgi:application -k uvicorn.workers.UvicornWorker --workers 1 --timeout 120`.
4. В Environment добавьте `SECRET_KEY` (случайная строка), `DEBUG=false`, `ALLOWED_HOSTS=<ваш-сервис>.onrender.com`, `CSRF_TRUSTED_ORIGINS=https://<ваш-сервис>.onrender.com`, `TIME_ZONE=Asia/Qyzylorda`.
5. Нажмите **Create Web Service**. Build script установит зависимости, соберёт static и применит миграции автоматически. URL из панели Render — публичная ссылка приложения; проверьте `<URL>/health/`.
6. Для постоянной базы создайте Render PostgreSQL и вставьте его Internal Database URL в `DATABASE_URL`, затем redeploy. Для масштабируемых WebSocket создайте Render Key Value/совместимый Redis и укажите `REDIS_URL`. На Free Web Service локальные SQLite и загруженные аватары находятся на ephemeral filesystem и исчезают при redeploy/restart/spin-down — для аватаров укажите S3-совместимые переменные из `.env.example`.

`render.yaml` позволяет создать сервис через **New → Blueprint**. После создания замените в Render значение `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS` на фактический домен сервиса: placeholder в YAML нельзя угадать до создания сервиса.

> Важно: актуальный Free Render — хороший вариант для тестов и демо, но не для постоянной реальной игры: сервис засыпает через 15 минут без входящих запросов и просыпается около минуты; его файловая система эфемерна. Free Postgres истекает через 30 дней, а Free Key Value не сохраняет данные после рестарта. Эти ограничения подтверждены в [официальной документации Render](https://render.com/docs/free). Для живого постоянного турнира используйте платный Web Service + PostgreSQL и Redis/S3; код и environment-переменные уже к этому готовы.

## Проверка после деплоя

1. Зарегистрируйте двух пользователей, создайте комнату, подключитесь по шестизначному коду.
2. В лобби должны обновляться готовность и список участников без reload.
3. Организатор запускает игру: всем открывается игровая страница, роли скрыты друг от друга.
4. Отправьте игровое событие и завершите матч — XP и история должны появиться в профиле.

## Администрирование

`/admin/` доступен после `createsuperuser`. Организаторские HTTP-команды закрыты серверной проверкой владельца комнаты; клиентская видимость кнопок не является защитой.
