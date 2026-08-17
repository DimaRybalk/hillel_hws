import logging
import requests
from django.conf import settings
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)


class WarehouseServiceError(APIException):
    status_code = 502
    default_detail = "Сервіс складу тимчасово недоступний."


class WarehouseClient:
    def __init__(self):
        self.base_url = getattr(
            settings, "WAREHOUSE_SERVICE_URL", "http://project_b:8001"
        )
        self.jwt_token = None

    def _get_auth_headers(self) -> dict:
        if not self.jwt_token:
            auth_url = f"{self.base_url}/api/user/token/"
            username = getattr(settings, "WAREHOUSE_SERVICE_USER", "shop_service")
            password = getattr(settings, "WAREHOUSE_SERVICE_PASS", "my_secure_password_123")

            payload = {
                "username": username,
                "password": password,
            }
            headers = {
                "Host": "localhost",
                "Content-Type": "application/json",
            }

            try:
                response = requests.post(auth_url, json=payload, headers=headers, timeout=5)
                response.raise_for_status()
                self.jwt_token = response.json().get("access")
            except requests.RequestException as e:
                logger.error(
                    f"Помилка авторизації в сервісі складу: {e}", exc_info=True
                )
                raise WarehouseServiceError("Не вдалося авторизуватися на складі.")

        return {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
            "Host": "localhost",
        }

    def _make_request(self, method: str, endpoint: str, data: dict = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        headers = self._get_auth_headers()

        try:
            response = requests.request(
                method, url, json=data, headers=headers, timeout=5
            )

            if response.status_code == 401:
                self.jwt_token = None
                headers = self._get_auth_headers()
                response = requests.request(
                    method, url, json=data, headers=headers, timeout=5
                )

            if response.status_code >= 400:
                logger.warning(
                    f"Склад повернув помилку [{response.status_code}] на {url}: {response.text}"
                )
                response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout:
            logger.error(f"Таймаут з'єднання зі складом: {url}")
            raise WarehouseServiceError("Склад не відповідає (Timeout).")
        except requests.exceptions.RequestException as exc:
            logger.error(
                f"Помилка зв'язку зі складом: {exc}",
                exc_info=True,
            )
            error_msg = (
                response.json().get("error", "Помилка складу")
                if "response" in locals() and response.content
                else "Склад недоступний"
            )
            raise APIException(detail=error_msg)

    def reserve_book(self, book_id: int, amount: int, order_id: int = None) -> dict:
        endpoint = f"/api/inventory/items/{book_id}/reserve/"
        payload = {
            "amount": amount,
            "comment": (
                f"Резерв для замовлення #{order_id}" if order_id else "Резерв магазину"
            ),
        }
        return self._make_request("POST", endpoint, payload)

    def confirm_sale(self, book_id: int, amount: int, order_id: int = None) -> dict:
        endpoint = f"/api/inventory/items/{book_id}/confirm-sale/"
        payload = {
            "amount": amount,
            "comment": (
                f"Списання замовлення #{order_id}" if order_id else "Оплата замовлення"
            ),
        }
        return self._make_request("POST", endpoint, payload)

    def release_reservation(
        self, book_id: int, amount: int, order_id: int = None
    ) -> dict:
        endpoint = f"/api/inventory/items/{book_id}/release/"
        payload = {
            "amount": amount,
            "comment": (
                f"Скасування замовлення #{order_id}" if order_id else "Скасування броні"
            ),
        }
        return self._make_request("POST", endpoint, payload)