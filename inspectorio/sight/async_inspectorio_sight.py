import warnings
from asyncio import Semaphore, gather
from typing import Any, Callable, Dict, List, Literal, Optional, Union

import httpx

DEFAULT_LIMIT = 10


class AsyncInspectorioSight:
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
        Initializes the AsyncInspectorioSight client.

        :param base_url: The base URL for the Inspectorio Sight API. Can be one of three environments (production, pre-production, staging).
        :param concurrent_fetches_limit: The maximum number of concurrent fetches allowed. Cannot exceed 20 as per Inspectorio API guidelines.
        :param kwargs: Additional keyword arguments to be passed to the httpx.AsyncClient.

        The Inspectorio API supports up to 20 concurrent asynchronous requests to optimize data integration speed.
        """
        # Validate and set concurrent_fetches_limit to ensure it does not exceed 20
        if concurrent_fetches_limit > 20:
            warnings.warn(
                "concurrent_fetches_limit cannot be greater than 20, setting to 20."
            )
            concurrent_fetches_limit = 20
        self._concurrent_fetches_limit: int = concurrent_fetches_limit

        self._base_url: str = base_url
        self._client_kwargs: Dict[str, Any] = kwargs
        self._session: Optional[httpx.AsyncClient] = None
        self._token: Optional[str] = None
        self._headers: Dict[str, str] = {}

    async def __aenter__(self):
        self._session = httpx.AsyncClient(**self._client_kwargs)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.aclose()

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Union[Dict[str, Any], None]:
        """A generic method to make HTTP requests."""
        url = f"{self._base_url}{endpoint}"
        response = await self._session.request(
            method, url, headers=self._headers, **kwargs
        )
        if response.is_success:
            return response.json() if response.text else {}
        else:
            await self.handle_api_error(response)

    async def login(self, username: str, password: str) -> None:
        """Authenticate asynchronously and store authentication token."""
        auth_payload = {"username": username, "password": password}
        data = await self._make_request("POST", "/auth/login", json=auth_payload)
        if data and "token" in data.get("data", {}):
            self._token = data["data"]["token"]
            self._headers = {"token": f"{self._token}"}
        else:
            raise KeyError("Token not found in response")

    @staticmethod
    async def handle_api_error(response: httpx.Response) -> None:
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
    async def _clean_kwargs(kwargs: dict, remove_keys: Union[List[str], str]) -> dict:
        remove_keys = [remove_keys] if isinstance(remove_keys, str) else remove_keys
        return {k: v for k, v in kwargs.items() if k not in remove_keys}

    async def _fetch_all_with_pagination(
        self, fetch_function: Callable, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        A general method to fetch all items with pagination.
        :param fetch_function: The function to fetch data with pagination.
        :param kwargs: Additional keyword arguments to pass to the fetch function.
        """
        get_total_kwargs = await self._clean_kwargs(
            kwargs, ["total_safe_limit", "limit"]
        )
        initial_data = await fetch_function(limit=1, **get_total_kwargs)
        total_items = initial_data.get("total", 0)
        if total_items == 0:
            return []

        total_safe_limit = kwargs.get("total_safe_limit", total_items)
        total_items = min(total_safe_limit, total_items)
        limit = kwargs.get("limit", DEFAULT_LIMIT)
        offsets = range(0, total_items, limit)

        semaphore = Semaphore(self._concurrent_fetches_limit)
        batch_kwargs = await self._clean_kwargs(kwargs, ["total_safe_limit", "offset"])

        async def fetch_and_append_data(offset):
            async with semaphore:
                return await fetch_function(offset=offset, **batch_kwargs)

        tasks = [fetch_and_append_data(offset) for offset in offsets]
        return await gather(*tasks)

    async def list_bookings(
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
        """
        List bookings with optional filters and pagination. This method allows
        filtering bookings by their status, association to an organization, creation,
        and update timestamps. It also supports ordering and pagination of the results.

        Parameters:
        - offset (int, optional): The number of items to skip before starting to
            collect the result set. Defaults to 0.
        - status (str, optional): Filter bookings by their status. Possible values
            are "NEW", "WAIVED", "CONFIRMED", "REJECTED", "MERGED", "CANCELED".
            Defaults to None.
        - to_organization_id (str, optional): Filter bookings that are booked to the
            specified organization ID. Defaults to None.
        - updated_from (str, optional): Filter bookings updated from this date and
            time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
        - created_to (str, optional): Filter bookings created up to this date and time
            in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
        - order (str, optional): Specifies the order of the results. Defaults to
            "created_date:desc". Possible ordering is based on creation date,
            either ascending or descending.
        - updated_to (str, optional): Filter bookings updated up to this date and time
            in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
        - created_from (str, optional): Filter bookings created from this date and time
            in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
        - limit (int, optional): The maximum number of items to return. Defaults to 10,
            with a maximum allowable value of 100.

        Returns:
        Dict[str, Any]: A dictionary containing the list of bookings matching the
            criteria.

        Raises:
        - Exception: If an error occurs during the API call. This includes HTTP errors or any other issues encountered during the request.
        """
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
        return await self._make_request("GET", "/bookings", params=params)

    async def get_booking(self, booking_id: str) -> Dict[str, Any]:
        """Retrieve details for a specific booking."""
        return await self._make_request("GET", f"/bookings/{booking_id}")

    async def list_all_bookings(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch all bookings with pagination handling."""
        return await self._fetch_all_with_pagination(self.list_bookings, **kwargs)

    async def list_products(self) -> Dict[str, Any]:
        """
        List all products.
        """
        return await self._make_request("GET", "/products")

    async def list_purchase_orders(
        self,
        po_number: Optional[str] = None,
        offset: int = 0,
        delivery_date_to: Optional[str] = None,
        delivery_date_from: Optional[str] = None,
        opo_number: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
    ) -> Dict[str, Any]:
        """
        List Purchase Orders with optional filters and pagination.

        Parameters:
        - po_number (str, optional): Purchase order number to be stored in Inspectorio. Defaults to None.
        - offset (int, optional): The number of items to skip before starting to collect the result set. Defaults to 0.
        - delivery_date_to (str, optional): Purchase order delivery date to in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
        - delivery_date_from (str, optional): Purchase order delivery date from in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
        - opo_number (str, optional): Original purchase order number stored in the client's system. Defaults to None.
        - limit (int, optional): The maximum number of items to return. Defaults to 10, with a maximum allowable value of 100.

        Returns:
        Dict[str, Any]: A dictionary containing the list of purchase orders matching the criteria.

        Raises:
        - Exception: If an error occurs during the API call. This includes HTTP errors or any other issues encountered during the request.
        """
        params = {
            "po_number": po_number,
            "offset": offset,
            "delivery_date_to": delivery_date_to,
            "delivery_date_from": delivery_date_from,
            "opo_number": opo_number,
            "limit": limit,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return await self._make_request("GET", "/purchase-orders", params=params)

    async def list_all_purchase_orders(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch all purchase_orders with pagination handling."""
        return await self._fetch_all_with_pagination(
            self.list_purchase_orders, **kwargs
        )

    async def create_purchase_order(
        self, purchase_order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a Purchase Order with the provided data.

        Parameters:
        - purchase_order_data (Dict[str, Any]): The data for the new purchase order. Must conform to the API's expected
            schema for purchase order creation.

        Returns:
        Dict[str, Any]: A dictionary containing the response from the API, typically including details of the created purchase order.

        Raises:
        - Exception: If an error occurs during the API call. This includes HTTP errors or any other issues encountered during the request.
        """
        return await self._make_request(
            "POST", "/purchase-orders", json=purchase_order_data
        )

    async def list_reports(
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
        """
        List reports with optional filters and pagination. This method allows
        filtering reports by various criteria such as inspection dates, style ID,
        system update dates, creation and update timestamps, report status, and CAPA status.
        It also supports ordering and pagination of the results.

        Parameters are defined as per the Swagger documentation provided.

        Returns:
        Dict[str, Any]: A dictionary containing the list of reports matching the criteria.

        Raises:
        - Exception: If an error occurs during the API call. This includes HTTP errors or any other issues encountered during the request.
        """
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
        return await self._make_request("GET", "/reports", params=params)

    async def list_all_reports(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch all reports with pagination handling."""
        return await self._fetch_all_with_pagination(self.list_reports, **kwargs)

    async def get_report(self, report_id: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific report.

        Parameters:
        - report_id (str): The unique identifier for the report.

        Returns:
        Dict[str, Any]: A dictionary containing the details of the report if the request is successful.

        Raises:
        - Exception: If an error occurs during the API call or if the request is unsuccessful.
        """
        return await self._make_request("GET", f"/reports/{report_id}")

    async def list_factory_risk_profiles(
        self,
        date_to: str,
        date_from: str,
        offset: int = 0,
        date_type: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
    ) -> Dict[str, Any]:
        """
        List Factory Risk Profiles with optional filters. This method allows
        filtering factory risk profiles by date range and supports pagination.

        Parameters:
        - date_to (str): End date of the query range in yyyy-mm-dd format.
        - date_from (str): Start date of the query range in yyyy-mm-dd format.
        - offset (int, optional): The number of items to skip before starting to
            collect the result set. Defaults to 0.
        - limit (int, optional): The maximum number of items to return. Defaults to 10,
            with a maximum allowable value of 100.
        - date_type (str, optional): The type of the filtered date, such as
            "process_computed_date". Case-sensitive. Defaults to None.

        Returns:
        Dict[str, Any]: A dictionary containing the list of factory risk profiles matching the
            criteria.
        """
        params = {
            "offset": offset,
            "limit": limit,
            "date_to": date_to,
            "date_from": date_from,
            "date_type": date_type,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return await self._make_request(
            "GET", "/analytics/factory-risk-profile", params=params
        )

    async def list_all_factory_risk_profiles(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch all factory risk profiles with pagination handling."""
        return await self._fetch_all_with_pagination(
            self.list_factory_risk_profiles, **kwargs
        )

    async def get_factory_risk_profile(
        self,
        factory_id: str,
        date_to: str,
        date_from: str,
        client_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get Factory Risk Profile for a given factory ID within a specified date range.

        Parameters:
        - factory_id (str): Unique identifier for the factory.
        - date_to (str): End date of the query range in yyyy-mm-dd format.
        - date_from (str): Start date of the query range in yyyy-mm-dd format.
        - client_id (Optional[str]): Unique identifier of the Brand or Retailer that the factory produces for.

        Returns:
        Dict[str, Any]: A dictionary containing the factory risk profile if the request is successful.

        Raises:
        - Exception: If an error occurs during the API call or if the request is unsuccessful.
        """
        params = {
            "date_to": date_to,
            "date_from": date_from,
            "client_id": client_id,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return await self._make_request(
            "GET", f"/analytics/factory-risk-profile/{factory_id}", params=params
        )

    async def list_assignments(
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
        return await self._make_request("GET", "/assignments", params=params)

    async def list_all_assignments(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch all assignments with pagination handling."""
        return await self._fetch_all_with_pagination(self.list_assignments, **kwargs)

    async def get_assignment(self, assignment_id: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific assignment.

        Parameters:
        - assignment_id (str): The unique identifier for the assignment.

        Returns:
        Dict[str, Any]: A dictionary containing the details of the assignment if the request is successful.

        Raises:
        - Exception: If an error occurs during the API call or if the request is unsuccessful.
        """
        return await self._make_request("GET", f"/assignments/{assignment_id}")

    async def list_brands(
        self, offset: int = 0, limit: int = DEFAULT_LIMIT
    ) -> Dict[str, Any]:
        """
        List brands with optional pagination.

        Parameters:
        - offset (int, optional): The number of items to skip before starting to collect the result set. Defaults to 0.
        - limit (int, optional): The maximum number of items to return. Defaults to 10, with a maximum allowable value of 100.

        Returns:
        Dict[str, Any]: A dictionary containing the list of brands matching the criteria.

        Raises:
        - Exception: If an error occurs during the API call. This includes HTTP errors or any other issues encountered during the request.
        """
        params = {"offset": offset, "limit": limit}
        return await self._make_request("GET", "/brands", params=params)

    async def list_all_brands(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch all brands with pagination handling."""
        return await self._fetch_all_with_pagination(self.list_brands, **kwargs)

    async def get_brand(self, brand_id: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific brand.

        Parameters:
        - brand_id (str): The unique identifier for the brand.

        Returns:
        Dict[str, Any]: A dictionary containing the details of the brand if the request is successful.
        """
        return await self._make_request("GET", f"/brands/{brand_id}")

    async def update_brand(
        self, brand_id: str, brand_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update brand details.

        Parameters:
        - brand_id (str): The unique identifier for the brand.
        - brand_data (Dict[str, Any]): A dictionary containing the brand data to be updated.

        Returns:
        Dict[str, Any]: A dictionary containing the updated details of the brand if the request is successful.
        """
        return await self._make_request("PUT", f"/brands/{brand_id}", json=brand_data)

    async def delete_brand(self, brand_id: str) -> None:
        """
        Delete a brand by its ID.

        Parameters:
        - brand_id (str): The unique identifier for the brand.
        """
        await self._make_request("DELETE", f"/brands/{brand_id}")

    async def get_capa(self, report_id: str) -> Dict[str, Any]:
        """
        Retrieve CAPA details for a specific report.

        Parameters:
        - report_id (str): The unique identifier for the report.

        Returns:
        Dict[str, Any]: A dictionary containing the details of the CAPA if the request is successful.

        Raises:
        - Exception: If an error occurs during the API call or if the request is unsuccessful.
        """
        return await self._make_request("GET", f"/capas/{report_id}")

    async def create_file_upload_session(self, payload: dict) -> Dict[str, Any]:
        """
        Creates a file upload session.

        Parameters:
        - payload (dict): The payload for creating a file upload session.

        Returns:
        Dict[str, Any]: A dictionary containing the response from the API call.

        Raises:
        - Exception: If an error occurs during the API call.
        """
        return await self._make_request("POST", "/file-upload-session", json=payload)

    async def list_lab_test_reports(
        self, offset: int = 0, limit: int = DEFAULT_LIMIT
    ) -> Dict[str, Any]:
        """
        List Lab Test Reports with optional pagination parameters.

        Parameters:
        - offset (int, optional): The number of items to skip before starting to collect the result set. Defaults to 0.
        - limit (int, optional): The maximum number of items to return. Defaults to 10, with a maximum allowable value of 100.

        Returns:
        Dict[str, Any]: A dictionary containing the list of lab test reports matching the criteria.
        """
        params = {"offset": offset, "limit": limit}
        return await self._make_request("GET", "/lab-test-reports", params=params)

    async def list_all_lab_test_reports(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch all lab test reports with pagination handling."""
        return await self._fetch_all_with_pagination(
            self.list_lab_test_reports, **kwargs
        )

    async def create_lab_test_report(
        self, report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new Lab Test Report.

        Parameters:
        - report_data (Dict[str, Any]): The data for the new lab test report.

        Returns:
        Dict[str, Any]: A dictionary containing the newly created lab test report's details.
        """
        return await self._make_request("POST", "/lab-test-reports", json=report_data)

    async def get_lab_test_report(self, lab_test_report_id: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific lab test report by its ID.

        Parameters:
        - lab_test_report_id (str): The unique identifier of the lab test report to retrieve.

        Returns:
        Dict[str, Any]: A dictionary containing the details of the lab test report if the request is successful.

        This method sends a GET request to fetch details of a specific lab test report.
        It returns the report details as a dictionary. Raises exceptions if the fetch fails
        due to reasons such as unauthorized access, report not found, or server errors.
        """
        return await self._make_request(
            "GET", f"/lab-test-reports/{lab_test_report_id}"
        )

    async def update_lab_test_report(
        self, lab_test_report_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a specific lab test report by its ID with the provided data.

        Parameters:
        - lab_test_report_id (str): The unique identifier of the lab test report to update.
        - data (Dict[str, Any]): A dictionary containing the update data for the lab test report.

        Returns:
        Dict[str, Any]: A dictionary containing the updated lab test report details if the request is successful.

        Raises:
        - Exception: If an error occurs during the API call, such as HTTP errors, validation errors, or if the lab test
            report is not found.
        """

        return await self._make_request(
            "PUT", f"/lab-test-reports/{lab_test_report_id}", json=data
        )

    async def delete_lab_test_report(self, lab_test_report_id: str) -> None:
        """
        Delete a specific lab test report by its ID.

        Parameters:
        - lab_test_report_id (str): The unique identifier of the lab test report to delete.

        This method sends a DELETE request to the server to remove the specified lab test report.
        If the request is successful, the lab test report is deleted from the server.
        Raises exceptions if the deletion fails due to reasons such as unauthorized access,
        report not found, or server errors.
        """
        await self._make_request("DELETE", f"/lab-test-reports/{lab_test_report_id}")

    async def get_measurement_chart(self, style_id: str) -> Dict[str, Any]:
        """
        Retrieve measurement chart details for a specific style.

        Parameters:
        - style_id (str): The unique identifier for the style.

        Returns:
        Dict[str, Any]: A dictionary containing the details of the measurement chart if the request is successful.

        Raises:
        - Exception: If an error occurs during the API call or if the request is unsuccessful.
        """

        return await self._make_request("GET", f"/measurement-charts/{style_id}")

    async def create_measurement_chart(
        self, style_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a measurement chart for a specific style.

        Parameters:
        - style_id (str): The unique identifier for the style.
        - data (Dict[str, Any]): The data for creating the measurement chart according to the MeasurementForm schema.

        Returns:
        Dict[str, Any]: A dictionary containing the details of the newly created measurement chart.

        Raises:
        - Exception: If an error occurs during the API call or if the request is unsuccessful.
        """

        return await self._make_request(
            "POST", f"/measurement-charts/{style_id}", json=data
        )

    async def update_measurement_chart(
        self, style_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update measurement chart details for a specific style.

        Parameters:
        - style_id (str): The unique identifier for the style.
        - data (Dict[str, Any]): The data for updating the measurement chart according to the MeasurementForm schema.

        Returns:
        Dict[str, Any]: A dictionary containing the details of the updated measurement chart.

        Raises:
        - Exception: If an error occurs during the API call or if the request is unsuccessful.
        """

        return await self._make_request(
            "PUT", f"/measurement-charts/{style_id}", json=data
        )

    async def list_metadata(
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
        """
        List Metadata with optional filters and pagination.

        Parameters:
        - namespace (str): The logical type of data set by Inspectorio. Possible values are "analytics", "inspection".
        - offset (int, optional): The number of items to skip before starting to collect the result set. Defaults to 0.
        - updated_from (str, optional): Start date of the range when metadata was updated in ISO 8601 format. Defaults to None.
        - created_to (str, optional): End date of the range when metadata was created in ISO 8601 format. Defaults to None.
        - order (str, optional): Order of metadata in ascending or descending based on date filters ("created_date", "updated_date"). Defaults to "created_date:desc".
        - updated_to (str, optional): End date of the range when metadata was updated in ISO 8601 format. Defaults to None.
        - created_from (str, optional): Start date of the range when metadata was created in ISO 8601 format. Defaults to None.
        - limit (int, optional): The limitation of the returned results, defaults to 10 with a maximum of 100.

        Returns:
        Dict[str, Any]: A dictionary containing the list of metadata matching the criteria.
        """
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
        return await self._make_request("GET", f"/metadata/{namespace}", params=params)

    async def list_all_metadata(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch all metadata with pagination handling."""
        return await self._fetch_all_with_pagination(self.list_metadata, **kwargs)

    async def create_metadata(
        self,
        namespace: Literal["analytics", "inspection"],
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create Metadata.

        Parameters:
        - namespace (str): The logical type of data set by Inspectorio. Possible values are "analytics", "inspection".
        - data (Dict[str, Any]): The data to create metadata with, conforming to the MetadataCreate schema.

        Returns:
        Dict[str, Any]: A dictionary containing the created metadata response.
        """
        return await self._make_request("POST", f"/metadata/{namespace}", json=data)

    async def get_metadata(
        self, namespace: Literal["analytics", "inspection"], uid: str
    ) -> Dict[str, Any]:
        """
        Retrieve metadata for a given UID and namespace.

        Parameters:
        - namespace (Literal["analytics", "inspection"]): The logical type of data set by Inspectorio.
        - uid (str): Unique identifier within Ecosystem + Namespace, considered as unique keys.

        Returns:
        Dict[str, Any]: A dictionary containing the metadata if the request is successful.

        Raises:
        - Exception: If an error occurs during the API call. This includes HTTP errors or any other issues encountered during the request.
        """
        return await self._make_request("GET", f"/metadata/{namespace}/{uid}")

    async def update_metadata(
        self,
        namespace: Literal["analytics", "inspection"],
        uid: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update metadata for a given UID and namespace.

        Parameters:
        - namespace (Literal["analytics", "inspection"]): The logical type of data set by Inspectorio.
        - uid (str): Unique identifier within Ecosystem + Namespace, considered as unique keys.
        - metadata (Dict[str, Any]): The metadata to update.

        Returns:
        Dict[str, Any]: A dictionary containing the updated metadata if the request is successful.

        Raises:
        - Exception: If an error occurs during the API call. This includes HTTP errors or any other issues encountered during the request.
        """
        return await self._make_request(
            "PUT", f"/metadata/{namespace}/{uid}", json=metadata
        )

    async def delete_metadata(
        self, namespace: Literal["analytics", "inspection"], uid: str
    ) -> None:
        """
        Delete metadata for a given UID and namespace.

        Parameters:
        - namespace (Literal["analytics", "inspection"]): The logical type of data set by Inspectorio.
        - uid (str): Unique identifier within Ecosystem + Namespace, considered as unique keys.

        Raises:
        - Exception: If an error occurs during the API call. This includes HTTP errors or any other issues encountered during the request.
        """
        await self._make_request("DELETE", f"/metadata/{namespace}/{uid}")

    async def list_organizations(
        self, offset: int = 0, limit: int = DEFAULT_LIMIT, name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List organizations with optional filtering by name.

        Parameters:
        - offset (int, optional): The number of items to skip before starting to collect the result set. Defaults to 0.
        - limit (int, optional): The limit on the number of items to return in the response. Defaults to 10, with a maximum of 100.
        - name (str, optional): Filter organizations by name.

        Returns:
        Dict[str, Any]: A dictionary containing the list of organizations.
        """

        params = {"offset": offset, "limit": limit, "name": name}
        params = {k: v for k, v in params.items() if v is not None}
        return await self._make_request("GET", "/organizations", params=params)

    async def list_all_organizations(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch all organizations with pagination handling."""
        return await self._fetch_all_with_pagination(self.list_organizations, **kwargs)

    async def create_organization(
        self, organization_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new organization.

        Parameters:
        - organization_data (Dict[str, Any]): A dictionary containing data of the organization to create.

        Returns:
        Dict[str, Any]: A dictionary containing the created organization's details.
        """

        return await self._make_request(
            "POST", "/organizations", json=organization_data
        )

    async def get_organization(self, organization_id: str) -> Dict[str, Any]:
        """
        Retrieve details of a specific organization.

        Parameters:
        - organization_id (str): The unique identifier of the organization.

        Returns:
        Dict[str, Any]: A dictionary containing details of the specified organization.
        """

        return await self._make_request("GET", f"/organizations/{organization_id}")

    async def update_organization(
        self, organization_id: str, organization_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update details of a specific organization.

        Parameters:
        - organization_id (str): The unique identifier of the organization to update.
        - organization_data (Dict[str, Any]): A dictionary containing the update data for the organization.

        Returns:
        Dict[str, Any]: A dictionary containing the updated details of the organization.
        """

        return await self._make_request(
            "PUT", f"/organizations/{organization_id}", json=organization_data
        )

    async def delete_organization(self, organization_id: str) -> None:
        """
        Delete a specific organization.

        Parameters:
        - organization_id (str): The unique identifier of the organization to delete.
        """

        await self._make_request("DELETE", f"/organizations/{organization_id}")

    async def get_purchase_order(self, po_number: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific purchase order.

        Parameters:
        - po_number (str): The unique identifier for the purchase order.

        Returns:
        Dict[str, Any]: A dictionary containing the details of the purchase order if the request is successful.

        Raises:
        - Exception: If an error occurs during the API call or if the request is unsuccessful.
        """
        return await self._make_request("GET", f"/purchase-orders/{po_number}")

    async def update_purchase_order(
        self, po_number: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update details for a specific purchase order.

        Parameters:
        - po_number (str): The unique identifier for the purchase order.
        - payload (Dict[str, Any]): The data to update the purchase order with.

        Returns:
        Dict[str, Any]: A dictionary containing the updated details of the purchase order if the request is successful.

        Raises:
        - Exception: If an error occurs during the API call or if the request is unsuccessful.
        """
        return await self._make_request(
            "PUT", f"/purchase-orders/{po_number}", json=payload
        )

    async def delete_purchase_order(self, po_number: str) -> None:
        """
        Delete a specific purchase order.

        Parameters:
        - po_number (str): The unique identifier for the purchase order to be deleted.

        Raises:
        - Exception: If an error occurs during the API call or if the request is unsuccessful.
        """
        await self._make_request("DELETE", f"/purchase-orders/{po_number}")

    async def update_delete_purchase_order(
        self, po_number: str, action: Literal["update", "delete"]
    ) -> Union[Dict[str, Any], None]:
        """
        Update or delete a Purchase Order based on the provided action.

        Parameters:
        - po_number (str): The Purchase Order number to be updated or deleted.
        - action (Literal["update", "delete"]): Specifies the action to be performed on the Purchase Order.
            - "update": Updates the Purchase Order. The method behaves like a PUT request.
            - "delete": Deletes the Purchase Order. The method behaves like a DELETE request.

        Returns:
        Dict[str, Any]: A dictionary representing the response of the action performed.

        Raises:
        - Exception: If an error occurs during the API call or if the action is not successful.
        """
        return await self._make_request(
            "POST",
            f"/purchase-orders/{po_number}/actions/{action}",
            json={"action": action},
        )

    async def list_time_and_actions(
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
        """
        List Time and Actions with optional filters and pagination. This method allows
        filtering Time and Actions by purchase order number, status, and creation/update
        timestamps. It also supports pagination of the results.

        Parameters:
        - po_number (str, optional): Filter Time and Actions by purchase order number.
        - offset (int, optional): The number of items to skip before starting to collect the result set.
        - status (str, optional): Filter Time and Actions by their status. Possible values
            are "UPCOMING", "NEW", "IN-PROGRESS", "CANCELED", "ABORTED", "COMPLETED".
        - updated_from (str, optional): Filter Time and Actions updated from this date and time.
        - created_to (str, optional): Filter Time and Actions created up to this date and time.
        - updated_to (str, optional): Filter Time and Actions updated to this date and time.
        - created_from (str, optional): Filter Time and Actions created from this date and time.
        - limit (int, optional): The maximum number of items to return. Defaults to 10.

        Returns:
        Dict[str, Any]: A dictionary containing the list of Time and Actions matching the criteria.
        """
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
        return await self._make_request("GET", "/time-and-actions", params=params)

    async def list_all_time_and_actions(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch all time and actions with pagination handling."""
        return await self._fetch_all_with_pagination(
            self.list_time_and_actions, **kwargs
        )

    async def get_time_and_action(self, id: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific Time and Action.

        Parameters:
        - id (str): The unique identifier for the Time and Action.

        Returns:
        Dict[str, Any]: A dictionary containing the details of the Time and Action if the request is successful.
        """
        return await self._make_request("GET", f"/time-and-actions/{id}")

    async def update_time_and_actions_milestones(
        self, ta_id: str, data: dict
    ) -> Dict[str, Any]:
        """
        Update Time and Actions milestones.

        Parameters:
        - ta_id (str): The unique identifier for the Time and Action.
        - data (dict): The data to update the Time and Action milestones.

        Returns:
        Dict[str, Any]: A dictionary containing the response from the API after updating the milestones.
        """
        return await self._make_request(
            "PUT", f"/time-and-actions/{ta_id}/milestones", json=data
        )

    async def get_time_and_actions_production_status(
        self, ta_id: str, productionStatusLevel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get Time and Actions production status.

        Parameters:
        - ta_id (str): The unique identifier for the Time and Action.
        - productionStatusLevel (str, optional): The level of production status, either "poLevel" or "itemLevel".

        Returns:
        Dict[str, Any]: A dictionary containing the Time and Actions production status.
        """
        params = (
            {"productionStatusLevel": productionStatusLevel}
            if productionStatusLevel
            else {}
        )
        return await self._make_request(
            "GET", f"/time-and-actions/{ta_id}/production-status", params=params
        )

    async def update_time_and_actions_production_status(
        self, ta_id: str, data: dict
    ) -> Dict[str, Any]:
        """
        Update Time and Actions production status.

        Parameters:
        - ta_id (str): The unique identifier for the Time and Action.
        - data (dict): The data to update the Time and Action production status.

        Returns:
        Dict[str, Any]: A dictionary containing the response from the API after updating the production status.
        """
        return await self._make_request(
            "PUT", f"/time-and-actions/{ta_id}/production-status", json=data
        )
