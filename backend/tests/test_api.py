import time
import uuid
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def unique_user():
    uid = uuid.uuid4().hex[:8]
    return {"username": f"user_{uid}", "email": f"user_{uid}@example.com", "password": "1234"}


def register_login():
    user = unique_user()
    assert client.post("/auth/register", json=user).status_code == 200
    response = client.post("/auth/login", json={"username": user["username"], "password": user["password"]})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

# Проверяем, что сервер запущен и endpoint /status отвечает корректно
def test_status():
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

# Проверяем регистрацию нового пользователя и последующий вход в систему
# После успешного логина сервер должен вернуть JWT access_token
def test_register_and_login():
    user = unique_user()
    assert client.post("/auth/register", json=user).status_code == 200
    response = client.post("/auth/login", json={"username": user["username"], "password": user["password"]})
    assert response.status_code == 200
    assert "access_token" in response.json()

# Проверяем основной функционал транзакций:
# создание, получение списка, редактирование, удаление
# Также проверяем, что endpoint статистики возвращает рассчитанные данные
def test_transactions_crud_and_statistics():
    headers = register_login()
    create_response = client.post(
        "/transactions",
        headers=headers,
        json={"amount": 100, "category": "Food", "description": "Test transaction"},
    )
    assert create_response.status_code == 200
    transaction_id = create_response.json()["id"]

    get_response = client.get("/transactions", headers=headers)
    assert get_response.status_code == 200
    assert len(get_response.json()) >= 1

    update_response = client.put(
        f"/transactions/{transaction_id}",
        headers=headers,
        json={"amount": 150, "category": "Transport", "description": "Updated"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["amount"] == 150

    stats_response = client.get("/statistics", headers=headers)
    assert stats_response.status_code == 200
    assert "total_amount" in stats_response.json()

    delete_response = client.delete(f"/transactions/{transaction_id}", headers=headers)
    assert delete_response.status_code == 200

# Проверяем запуск фоновой генерации отчёта
# Сервер должен сразу вернуть report_id, не ожидая завершения генерации
def test_report_generation():
    headers = register_login()
    client.post("/transactions", headers=headers, json={"amount": 200, "category": "Education", "description": "Books"})
    response = client.post("/reports/generate", headers=headers)
    assert response.status_code == 200
    report_id = response.json()["report_id"]
    time.sleep(6)
    status_response = client.get(f"/reports/{report_id}", headers=headers)
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "done"
