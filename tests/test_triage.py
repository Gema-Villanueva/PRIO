from fastapi.testclient import TestClient

from backend.main import app

# Creamos un cliente para probar la API sin arrancar Uvicorn.
client = TestClient(app)


# Comprobamos que se eliminan los espacios exteriores.
def test_triage_trims_message():
    response = client.post(
        "/triage/",
        json={
            "message": "  No puedo entrar  ",
            "user_role": "guest",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "No puedo entrar"


# Comprobamos que un mensaje compuesto solo por espacios se rechaza.
def test_triage_rejects_whitespace_message():
    response = client.post(
        "/triage/",
        json={
            "message": "   ",
            "user_role": "guest",
        },
    )

    assert response.status_code == 422


# Comprobamos que se rechazan los roles no permitidos.
def test_triage_rejects_invalid_role():
    response = client.post(
        "/triage/",
        json={
            "message": "No puedo entrar",
            "user_role": "admin",
        },
    )

    assert response.status_code == 422