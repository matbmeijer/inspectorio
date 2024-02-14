from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Literal, Optional, Union

import httpx

from inspectorio.sight.base_inspectorio_sight import BaseInspectorioSight

DEFAULT_LIMIT = 10


class InspectorioSight(BaseInspectorioSight):
    """
    InspectorioSight client, that uses synchronous requests to interact with the
    Inspectorio Sight API. For batch requests with methods like `list_all_*()`,
    it uses threading to speed up retrieval.
    """

    def __init__(
        self,
        base_url: Literal[
            "https://sight.inspectorio.com/api/v1",
            "https://sight.pre.inspectorio.com/api/v1",
            "https://sight.stg.inspectorio.com/api/v1",
        ] = "https://sight.inspectorio.com/api/v1",
        concurrent_fetches_limit: int = 10,
        **kwargs,
    ) -> None:
        """
        Initializes the InspectorioSight client. Uses synchronous requests to
        interact with the Inspectorio Sight API. For batch requests with methods
        like `list_all_*()`, it uses threading to parallelize requests.

        Args:
            base_url: The base URL for the Inspectorio Sight API. Can be one of
                three environments (production, pre-production, staging).
            concurrent_fetches_limit: The maximum number of concurrent fetches
                allowed. Cannot exceed 20 as per Inspectorio API guidelines.
            kwargs: Additional keyword arguments to be passed to the
                `httpx.Client`.

        The Inspectorio API supports up to 20 concurrent requests to
            optimize data integration speed.
        """
        super().__init__(base_url, concurrent_fetches_limit, **kwargs)
        self._session: Optional[httpx.Client] = httpx.Client(**self._client_kwargs)

    def __enter__(self):
        self._session = httpx.Client(**self._client_kwargs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()

    def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Union[Dict[str, Any], None]:
        """A generic method to make HTTP requests."""
        url = f"{self._base_url}{endpoint}"
        response = self._session.request(
            method=method, url=url, headers=self._headers, **kwargs
        )
        if response.is_success:
            return response.json() if response.text else {}
        else:
            self._handle_api_error(response)

    def login(self, username: str, password: str) -> None:
        auth_payload = {"username": username, "password": password}
        data = self._make_request("POST", "/auth/login", json=auth_payload)
        if data and "token" in data.get("data", {}):
            self._token = data["data"]["token"]
            self._headers = {"token": f"{self._token}"}
        else:
            raise KeyError("Token not found in response")

    @staticmethod
    def _handle_api_error(response: httpx.Response) -> None:
        """Handle API error responses."""
        try:
            error_data = response.json()
            error_code = error_data.get("errorCode", "Unknown")
            error_message = error_data.get("message", "An unknown error occurred.")
            raise Exception(
                f"API Error {response.status_code} [{error_code}]: {error_message}"
            )
        except ValueError:
            raise Exception(f"API Error {response.status_code}: {response.text}")

    @staticmethod
    def _clean_kwargs(kwargs: dict, remove_keys: Union[List[str], str]) -> dict:
        remove_keys = [remove_keys] if isinstance(remove_keys, str) else remove_keys
        return {k: v for k, v in kwargs.items() if k not in remove_keys}

    def _fetch_all_with_pagination(
        self, fetch_function: Callable, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        A general method to fetch all items with pagination in a parallel fashion.
        """
        get_total_kwargs = self._clean_kwargs(kwargs, ["total_safe_limit", "limit"])
        initial_data = fetch_function(limit=1, **get_total_kwargs)
        total_items = initial_data.get("total", 0)
        if total_items == 0:
            return []

        total_safe_limit = kwargs.get("total_safe_limit", total_items)
        total_items = min(total_safe_limit, total_items)
        limit = kwargs.get("limit", DEFAULT_LIMIT)
        offsets = range(0, total_items, limit)

        batch_kwargs = self._clean_kwargs(kwargs, ["total_safe_limit", "offset"])

        def fetch_and_append_data(offset):
            return fetch_function(offset=offset, **batch_kwargs)

        with ThreadPoolExecutor(max_workers=self._concurrent_fetches_limit) as executor:
            tasks = [
                executor.submit(fetch_and_append_data, offset) for offset in offsets
            ]
            return [task.result() for task in tasks]

    def list_bookings(
        self,
        offset: int = 0,
        status: Optional[
            Literal["NEW", "WAIVED", "CONFIRMED", "REJECTED", "MERGED", "CANCELED"]
        ] = None,
        to_organization_id: Optional[str] = None,
        updated_from: Optional[str] = None,
        created_to: Optional[str] = None,
        order: str = "created_date:desc",
        updated_to: Optional[str] = None,
        created_from: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
    ) -> Dict[str, Any]:
        params = {
            "status": status,
            "offset": offset,
            "limit": limit,
            "order": order,
            "to_organization_id": to_organization_id,
            "updated_from": updated_from,
            "updated_to": updated_to,
            "created_from": created_from,
            "created_to": created_to,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._make_request("GET", "/bookings", params=params)

    def get_booking(self, booking_id: str) -> Dict[str, Any]:
        return self._make_request("GET", f"/bookings/{booking_id}")

    def list_all_bookings(self, **kwargs) -> List[Dict[str, Any]]:
        return self._fetch_all_with_pagination(self.list_bookings, **kwargs)

    def list_products(self) -> Dict[str, Any]:
        return self._make_request("GET", "/products")

    def list_purchase_orders(
        self,
        po_number: Optional[str] = None,
        offset: int = 0,
        delivery_date_to: Optional[str] = None,
        delivery_date_from: Optional[str] = None,
        opo_number: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
    ) -> Dict[str, Any]:
        params = {
            "po_number": po_number,
            "offset": offset,
            "delivery_date_to": delivery_date_to,
            "delivery_date_from": delivery_date_from,
            "opo_number": opo_number,
            "limit": limit,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._make_request("GET", "/purchase-orders", params=params)

    def list_all_purchase_orders(self, **kwargs) -> List[Dict[str, Any]]:
        return self._fetch_all_with_pagination(self.list_purchase_orders, **kwargs)

    def create_purchase_order(
        self, purchase_order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._make_request("POST", "/purchase-orders", json=purchase_order_data)

    def list_reports(
        self,
        inspection_date_from: Optional[str] = None,
        inspection_date_to: Optional[str] = None,
        style_id: Optional[str] = None,
        offset: int = 0,
        system_updated_from: Optional[str] = None,
        status: Optional[Literal["in-progress", "pending", "completed"]] = None,
        system_updated_to: Optional[str] = None,
        updated_from: Optional[str] = None,
        created_to: Optional[str] = None,
        order: str = "created_date:desc",
        updated_to: Optional[str] = None,
        created_from: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
        capa_status: Optional[
            Literal[
                "Waiting for Response",
                "Submitted",
                "Submitted by Reviewer",
                "Rejected",
                "Re-inspection Requested (Solved)",
                "Re-inspection Requested (Unsolved)",
                "Approved",
            ]
        ] = None,
    ) -> Dict[str, Any]:
        params = {
            "inspection_date_from": inspection_date_from,
            "inspection_date_to": inspection_date_to,
            "style_id": style_id,
            "offset": offset,
            "system_updated_from": system_updated_from,
            "status": status,
            "system_updated_to": system_updated_to,
            "updated_from": updated_from,
            "created_to": created_to,
            "order": order,
            "updated_to": updated_to,
            "created_from": created_from,
            "limit": limit,
            "capa_status": capa_status,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._make_request("GET", "/reports", params=params)

    def list_all_reports(self, **kwargs) -> List[Dict[str, Any]]:
        return self._fetch_all_with_pagination(self.list_reports, **kwargs)

    def get_report(self, report_id: str) -> Dict[str, Any]:
        return self._make_request("GET", f"/reports/{report_id}")

    def list_factory_risk_profiles(
        self,
        date_to: str,
        date_from: str,
        offset: int = 0,
        date_type: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
    ) -> Dict[str, Any]:
        params = {
            "offset": offset,
            "limit": limit,
            "date_to": date_to,
            "date_from": date_from,
            "date_type": date_type,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._make_request(
            "GET", "/analytics/factory-risk-profile", params=params
        )

    def list_all_factory_risk_profiles(self, **kwargs) -> List[Dict[str, Any]]:
        return self._fetch_all_with_pagination(
            self.list_factory_risk_profiles, **kwargs
        )

    def get_factory_risk_profile(
        self,
        factory_id: str,
        date_to: str,
        date_from: str,
        client_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = {
            "date_to": date_to,
            "date_from": date_from,
            "client_id": client_id,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._make_request(
            "GET", f"/analytics/factory-risk-profile/{factory_id}", params=params
        )

    def list_assignments(
        self,
        factory_city: Optional[str] = None,
        assignment_created_from: Optional[str] = None,
        offset: int = 0,
        expected_inspection_date_to: Optional[str] = None,
        expected_inspection_date_from: Optional[str] = None,
        assignment_created_to: Optional[str] = None,
        assignment_updated_to: Optional[str] = None,
        factory_country: Optional[str] = None,
        assignment_updated_from: Optional[str] = None,
        order: str = "assignment_created_date:desc",
        assignment_status: Optional[
            Literal[
                "NEW",
                "PRE-ASSIGNED",
                "ASSIGNED",
                "RELEASED",
                "IN-PROGRESS",
                "COMPLETED",
                "ABORTED",
            ]
        ] = None,
        executor_organization: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
    ) -> Dict[str, Any]:
        params = {
            "factory_city": factory_city,
            "assignment_created_from": assignment_created_from,
            "offset": offset,
            "expected_inspection_date_to": expected_inspection_date_to,
            "expected_inspection_date_from": expected_inspection_date_from,
            "assignment_created_to": assignment_created_to,
            "assignment_updated_to": assignment_updated_to,
            "factory_country": factory_country,
            "assignment_updated_from": assignment_updated_from,
            "order": order,
            "assignment_status": assignment_status,
            "executor_organization": executor_organization,
            "limit": limit,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._make_request("GET", "/assignments", params=params)

    def list_all_assignments(self, **kwargs) -> List[Dict[str, Any]]:
        return self._fetch_all_with_pagination(self.list_assignments, **kwargs)

    def get_assignment(self, assignment_id: str) -> Dict[str, Any]:
        return self._make_request("GET", f"/assignments/{assignment_id}")

    def list_brands(
        self, offset: int = 0, limit: int = DEFAULT_LIMIT
    ) -> Dict[str, Any]:
        params = {"offset": offset, "limit": limit}
        return self._make_request("GET", "/brands", params=params)

    def list_all_brands(self, **kwargs) -> List[Dict[str, Any]]:
        return self._fetch_all_with_pagination(self.list_brands, **kwargs)

    def get_brand(self, brand_id: str) -> Dict[str, Any]:
        return self._make_request("GET", f"/brands/{brand_id}")

    def update_brand(self, brand_id: str, brand_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._make_request("PUT", f"/brands/{brand_id}", json=brand_data)

    def delete_brand(self, brand_id: str) -> None:
        self._make_request("DELETE", f"/brands/{brand_id}")

    def get_capa(self, report_id: str) -> Dict[str, Any]:
        return self._make_request("GET", f"/capas/{report_id}")

    def create_file_upload_session(self, payload: dict) -> Dict[str, Any]:
        return self._make_request("POST", "/file-upload-session", json=payload)

    def list_lab_test_reports(
        self, offset: int = 0, limit: int = DEFAULT_LIMIT
    ) -> Dict[str, Any]:
        params = {"offset": offset, "limit": limit}
        return self._make_request("GET", "/lab-test-reports", params=params)

    def list_all_lab_test_reports(self, **kwargs) -> List[Dict[str, Any]]:
        return self._fetch_all_with_pagination(self.list_lab_test_reports, **kwargs)

    def create_lab_test_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._make_request("POST", "/lab-test-reports", json=report_data)

    def get_lab_test_report(self, lab_test_report_id: str) -> Dict[str, Any]:
        return self._make_request("GET", f"/lab-test-reports/{lab_test_report_id}")

    def update_lab_test_report(
        self, lab_test_report_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._make_request(
            "PUT", f"/lab-test-reports/{lab_test_report_id}", json=data
        )

    def delete_lab_test_report(self, lab_test_report_id: str) -> None:
        self._make_request("DELETE", f"/lab-test-reports/{lab_test_report_id}")

    def get_measurement_chart(self, style_id: str) -> Dict[str, Any]:
        return self._make_request("GET", f"/measurement-charts/{style_id}")

    def create_measurement_chart(
        self, style_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._make_request("POST", f"/measurement-charts/{style_id}", json=data)

    def update_measurement_chart(
        self, style_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._make_request("PUT", f"/measurement-charts/{style_id}", json=data)

    def list_metadata(
        self,
        namespace: Literal["analytics", "inspection"],
        offset: int = 0,
        updated_from: Optional[str] = None,
        created_to: Optional[str] = None,
        order: str = "created_date:desc",
        updated_to: Optional[str] = None,
        created_from: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
    ) -> Dict[str, Any]:
        params = {
            "offset": offset,
            "updated_from": updated_from,
            "created_to": created_to,
            "order": order,
            "updated_to": updated_to,
            "created_from": created_from,
            "limit": limit,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._make_request("GET", f"/metadata/{namespace}", params=params)

    def list_all_metadata(self, **kwargs) -> List[Dict[str, Any]]:
        return self._fetch_all_with_pagination(self.list_metadata, **kwargs)

    def create_metadata(
        self,
        namespace: Literal["analytics", "inspection"],
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        return self._make_request("POST", f"/metadata/{namespace}", json=data)

    def get_metadata(
        self, namespace: Literal["analytics", "inspection"], uid: str
    ) -> Dict[str, Any]:
        return self._make_request("GET", f"/metadata/{namespace}/{uid}")

    def update_metadata(
        self,
        namespace: Literal["analytics", "inspection"],
        uid: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        return self._make_request("PUT", f"/metadata/{namespace}/{uid}", json=metadata)

    def delete_metadata(
        self, namespace: Literal["analytics", "inspection"], uid: str
    ) -> None:
        self._make_request("DELETE", f"/metadata/{namespace}/{uid}")

    def list_organizations(
        self, offset: int = 0, limit: int = DEFAULT_LIMIT, name: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {"offset": offset, "limit": limit, "name": name}
        params = {k: v for k, v in params.items() if v is not None}
        return self._make_request("GET", "/organizations", params=params)

    def list_all_organizations(self, **kwargs) -> List[Dict[str, Any]]:
        return self._fetch_all_with_pagination(self.list_organizations, **kwargs)

    def create_organization(self, organization_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._make_request("POST", "/organizations", json=organization_data)

    def get_organization(self, organization_id: str) -> Dict[str, Any]:
        return self._make_request("GET", f"/organizations/{organization_id}")

    def update_organization(
        self, organization_id: str, organization_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._make_request(
            "PUT", f"/organizations/{organization_id}", json=organization_data
        )

    def delete_organization(self, organization_id: str) -> None:
        self._make_request("DELETE", f"/organizations/{organization_id}")

    def get_purchase_order(self, po_number: str) -> Dict[str, Any]:
        return self._make_request("GET", f"/purchase-orders/{po_number}")

    def update_purchase_order(
        self, po_number: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._make_request("PUT", f"/purchase-orders/{po_number}", json=payload)

    def delete_purchase_order(self, po_number: str) -> None:
        self._make_request("DELETE", f"/purchase-orders/{po_number}")

    def update_delete_purchase_order(
        self, po_number: str, action: Literal["update", "delete"]
    ) -> Union[Dict[str, Any], None]:
        return self._make_request(
            "POST",
            f"/purchase-orders/{po_number}/actions/{action}",
            json={"action": action},
        )

    def list_time_and_actions(
        self,
        po_number: Optional[str] = None,
        offset: int = 0,
        status: Optional[
            Literal[
                "UPCOMING", "NEW", "IN-PROGRESS", "CANCELED", "ABORTED", "COMPLETED"
            ]
        ] = None,
        updated_from: Optional[str] = None,
        created_to: Optional[str] = None,
        updated_to: Optional[str] = None,
        created_from: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
    ) -> Dict[str, Any]:
        params = {
            "po_number": po_number,
            "offset": offset,
            "status": status,
            "updated_from": updated_from,
            "created_to": created_to,
            "updated_to": updated_to,
            "created_from": created_from,
            "limit": limit,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._make_request("GET", "/time-and-actions", params=params)

    def list_all_time_and_actions(self, **kwargs) -> List[Dict[str, Any]]:
        return self._fetch_all_with_pagination(self.list_time_and_actions, **kwargs)

    def get_time_and_action(self, id: str) -> Dict[str, Any]:
        return self._make_request("GET", f"/time-and-actions/{id}")

    def update_time_and_actions_milestones(
        self, ta_id: str, data: dict
    ) -> Dict[str, Any]:
        return self._make_request(
            "PUT", f"/time-and-actions/{ta_id}/milestones", json=data
        )

    def get_time_and_actions_production_status(
        self, ta_id: str, production_status_level: Optional[str] = None
    ) -> Dict[str, Any]:
        params = (
            {"productionStatusLevel": production_status_level}
            if production_status_level
            else {}
        )
        return self._make_request(
            "GET", f"/time-and-actions/{ta_id}/production-status", params=params
        )

    def update_time_and_actions_production_status(
        self, ta_id: str, data: dict
    ) -> Dict[str, Any]:
        return self._make_request(
            "PUT", f"/time-and-actions/{ta_id}/production-status", json=data
        )
