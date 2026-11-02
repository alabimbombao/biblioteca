"""Pruebas de registro, login, tokens y contraseñas."""

from app.models.usuario import RolUsuario
from tests.conftest import cabecera, crear_usuario, token_de


def _datos_registro(email="ana@example.com", password="Ana12345"):
    return {
        "email": email,
        "nombre": "Ana Torres",
        "telefono": "300 123 4567",
        "password": password,
        "confirmar_password": password,
    }


def test_registro_password_debil(cliente):
    respuesta = cliente.post(
        "/api/v1/auth/registro",
        json=_datos_registro(password="abcdefgh"),
    )

    assert respuesta.status_code == 422


def test_registro_confirmacion_distinta(cliente):
    datos = _datos_registro()
    datos["confirmar_password"] = "OtraClave123"

    respuesta = cliente.post("/api/v1/auth/registro", json=datos)

    assert respuesta.status_code == 422


def test_registro_valido(cliente):
    respuesta = cliente.post(
        "/api/v1/auth/registro", json=_datos_registro()
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["rol"] == "socio"
    assert cuerpo["socio_id"] is not None
    assert cuerpo["email"] == "ana@example.com"
    assert "password" not in cuerpo
    assert "password_hash" not in cuerpo


def test_registro_duplicado_ignora_mayusculas(cliente):
    cliente.post("/api/v1/auth/registro", json=_datos_registro())

    respuesta = cliente.post(
        "/api/v1/auth/registro",
        json=_datos_registro(email="ANA@EXAMPLE.COM"),
    )

    assert respuesta.status_code == 409


def test_login_credenciales_invalidas(cliente, ana):
    incorrecta = cliente.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "Incorrecta1"},
    )
    inexistente = cliente.post(
        "/api/v1/auth/login",
        data={"username": "nadie@example.com", "password": "Incorrecta1"},
    )

    assert incorrecta.status_code == 401
    assert inexistente.status_code == 401
    assert incorrecta.json()["detail"] == "Credenciales inválidas"
    assert inexistente.json()["detail"] == "Credenciales inválidas"
    assert incorrecta.headers["WWW-Authenticate"] == "Bearer"


def test_login_correcto_entrega_tokens(cliente, ana):
    respuesta = cliente.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "Ana12345"},
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["expires_in"] == 900
    assert cuerpo["access_token"]
    assert cuerpo["refresh_token"]


def test_me_sin_token_responde_401_con_cabecera(cliente):
    respuesta = cliente.get("/api/v1/auth/me")

    assert respuesta.status_code == 401
    assert respuesta.headers["WWW-Authenticate"] == "Bearer"


def test_me_token_alterado(cliente, ana):
    token = token_de(ana)
    alterado = token[:-1] + ("a" if token[-1] != "a" else "b")

    respuesta = cliente.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {alterado}"},
    )

    assert respuesta.status_code == 401


def test_refresh_token_no_sirve_como_access(cliente, ana):
    respuesta = cliente.get(
        "/api/v1/auth/me",
        headers=cabecera(ana, "refresh"),
    )

    assert respuesta.status_code == 401


def test_access_token_no_sirve_para_refresh(cliente, ana):
    respuesta = cliente.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": token_de(ana, "access")},
    )

    assert respuesta.status_code == 401


def test_rotacion_y_reutilizacion_de_refresh_token(cliente, ana):
    login = cliente.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "Ana12345"},
    ).json()

    primero = login["refresh_token"]
    segundo = cliente.post(
        "/api/v1/auth/refresh", json={"refresh_token": primero}
    )
    assert segundo.status_code == 200
    nuevo_refresh = segundo.json()["refresh_token"]

    reutilizado = cliente.post(
        "/api/v1/auth/refresh", json={"refresh_token": primero}
    )
    assert reutilizado.status_code == 401

    # Al detectar la reutilización se revocan todos los tokens del usuario.
    revocado = cliente.post(
        "/api/v1/auth/refresh", json={"refresh_token": nuevo_refresh}
    )
    assert revocado.status_code == 401


def test_logout_revoca_el_refresh_token(cliente, ana):
    login = cliente.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "Ana12345"},
    ).json()

    salida = cliente.post(
        "/api/v1/auth/logout",
        json={"refresh_token": login["refresh_token"]},
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert salida.status_code == 204

    intento = cliente.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login["refresh_token"]},
    )
    assert intento.status_code == 401


def test_bloqueo_tras_cinco_intentos_fallidos(cliente, ana):
    for _ in range(5):
        cliente.post(
            "/api/v1/auth/login",
            data={"username": "ana@example.com", "password": "Incorrecta1"},
        )

    respuesta = cliente.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "Ana12345"},
    )

    assert respuesta.status_code == 423
    assert respuesta.json()["detail"] == "Cuenta bloqueada temporalmente"


def test_cambio_de_password_revoca_tokens(cliente, ana):
    login = cliente.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "Ana12345"},
    ).json()

    cambio = cliente.patch(
        "/api/v1/auth/me/password",
        json={
            "password_actual": "Ana12345",
            "password_nueva": "Nueva1234",
        },
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert cambio.status_code == 204

    anterior = cliente.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "Ana12345"},
    )
    assert anterior.status_code == 401

    nueva = cliente.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "Nueva1234"},
    )
    assert nueva.status_code == 200

    refresh_viejo = cliente.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login["refresh_token"]},
    )
    assert refresh_viejo.status_code == 401


def test_password_actual_incorrecta(cliente, ana):
    respuesta = cliente.patch(
        "/api/v1/auth/me/password",
        json={
            "password_actual": "Incorrecta1",
            "password_nueva": "Nueva1234",
        },
        headers=cabecera(ana),
    )

    assert respuesta.status_code == 422


def test_usuario_inactivo_no_puede_entrar_ni_usar_token(cliente, db):
    inactivo = crear_usuario(
        db,
        "inactivo@example.com",
        "Inactivo123",
        RolUsuario.bibliotecario,
        activo=False,
    )

    login = cliente.post(
        "/api/v1/auth/login",
        data={"username": "inactivo@example.com", "password": "Inactivo123"},
    )
    assert login.status_code == 403
    assert login.json()["detail"] == "Usuario inactivo"

    me = cliente.get("/api/v1/auth/me", headers=cabecera(inactivo))
    assert me.status_code == 403


def test_limite_de_peticiones_en_login(cliente, ana):
    respuestas = [
        cliente.post(
            "/api/v1/auth/login",
            data={"username": "ana@example.com", "password": "Incorrecta1"},
        )
        for _ in range(11)
    ]

    assert respuestas[-1].status_code == 429


def test_limite_de_peticiones_en_registro(cliente):
    respuestas = []
    for indice in range(6):
        respuestas.append(
            cliente.post(
                "/api/v1/auth/registro",
                json=_datos_registro(
                    email=f"usuario{indice}@example.com"
                ),
            )
        )

    assert respuestas[-1].status_code == 429


def test_registro_limite_no_bloquea_las_primeras(cliente):
    # Se ejecuta en un proceso limpio por la fixture autouse de slowapi.
    primera = cliente.post(
        "/api/v1/auth/registro", json=_datos_registro()
    )
    assert primera.status_code == 201
