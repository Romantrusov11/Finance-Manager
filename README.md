# Personal Finance Manager

Проект для лабораторных работ: GUI + backend + база данных + сеть + JWT + 2FA + CRUD + статистика + графики + фоновая генерация отчёта + тесты.

## Запуск backend

Открой CMD:

```bat
cd /d C:\MAI\Finance-Manager\backend
C:\MAI\Finance-Manager\venv\Scripts\python.exe -m pip install -r requirements.txt
C:\MAI\Finance-Manager\venv\Scripts\python.exe -m uvicorn main:app --reload
```

Проверка: http://127.0.0.1:8000/docs

## Запуск frontend

Открой второе окно CMD:

```bat
cd /d C:\MAI\Finance-Manager\frontend
C:\MAI\Finance-Manager\venv\Scripts\python.exe -m pip install -r requirements.txt
C:\MAI\Finance-Manager\venv\Scripts\python.exe main.py
```

## Проверка GUI

1. Register — создать пользователя.
2. Login — войти.
3. Load Transactions — загрузить список.
4. Add Transaction — добавить транзакцию.
5. Edit Selected Transaction — изменить транзакцию.
6. Delete Selected Transaction — удалить транзакцию.
7. Show Statistics — показать статистику.
8. Show Charts — показать график.
9. Setup 2FA — включить двухфакторную аутентификацию.
10. Generate Report in Background — запустить фоновую генерацию отчёта.
11. Check Report Status — проверить статус отчёта.

## Запуск тестов

```bat
cd /d C:\MAI\Finance-Manager\backend
C:\MAI\Finance-Manager\venv\Scripts\python.exe -m pip install pytest httpx
C:\MAI\Finance-Manager\venv\Scripts\python.exe -m pytest tests
```

## Что закрывает проект

- Лаба 1: тема и обоснование — персональный финансовый помощник.
- Лаба 2: архитектура — frontend PySide6, backend FastAPI, SQLite, REST API.
- Лаба 3: прототип — сервер `/status`, клиент, база.
- Лаба 4: регистрация, логин, JWT, 2FA.
- Лаба 5: CRUD транзакций, статистика, графики.
- Лаба 6: QThread на клиенте + BackgroundTasks на сервере.
- Лаба 7: pytest-тесты API.
