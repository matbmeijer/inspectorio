import warnings
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional, Union

DEFAULT_LIMIT = 10


class BaseInspectorioSight(ABC):
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
        if concurrent_fetches_limit > 20:
            warnings.warn(
                "concurrent_fetches_limit cannot be greater than 20, setting to 20."
            )
            concurrent_fetches_limit = 20
        self._concurrent_fetches_limit: int = concurrent_fetches_limit

        self._base_url: str = base_url
        self._client_kwargs: Dict[str, Any] = kwargs
        self._token: Optional[str] = None
        self._headers: Dict[str, str] = {}

    @abstractmethod
    def login(self, username: str, password: str) -> None:
        """
        Authenticates with the Inspectorio Sight platform using the provided username
        and password. On successful authentication, stores the authentication token
        for subsequent API calls.

        Args:
            username (str): The username of the user.
            password (str): The password of the user.

        Raises:
            KeyError: If the response from the API does not contain an authentication
                token. This is indicative of a failure to authenticate, possibly due to
                incorrect credentials or an issue with the user's account.

            Exception: If an error occurs during the API call. This includes scenarios such
                as bad requests (400), unauthorized access (401), validation errors (422),
                rate-limiting (429), or internal server errors (500). The exception message
                will detail the nature of the error based on the API's response.

        API Endpoint:
            POST /api/v1/auth/login

        Note:
            This method should be called before making any other API calls that require
            authentication.
        """
        pass

    @abstractmethod
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
        """
        List bookings with optional filters and pagination. This method allows
        filtering bookings by their status, association to an organization, creation,
        and update timestamps. It also supports ordering and pagination of the results.

        Args:
            offset (int, optional): The number of items to skip before starting to
                collect the result set. Defaults to 0.
            status (str, optional): Filter bookings by their status. Possible values
                are "NEW", "WAIVED", "CONFIRMED", "REJECTED", "MERGED", "CANCELED".
                Defaults to None.
            to_organization_id (str, optional): Filter bookings that are booked to the
                specified organization ID. Defaults to None.
            updated_from (str, optional): Filter bookings updated from this date and
                time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
            created_to (str, optional): Filter bookings created up to this date and time
                in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
            order (str, optional): Specifies the order of the results. Defaults to
                "created_date:desc". Possible ordering is based on creation date,
                either ascending or descending.
            updated_to (str, optional): Filter bookings updated up to this date and time
                in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
            created_from (str, optional): Filter bookings created from this date and time
                in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
            limit (int, optional): The maximum number of items to return. Defaults to 10,
                with a maximum allowable value of 100.

        Returns:
            Dict[str, Any]: A dictionary containing the list of bookings matching the
                criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors or
                any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/bookings
        """
        pass

    @abstractmethod
    def get_booking(self, booking_id: str) -> Dict[str, Any]:
        """
        Retrieves details for a specific booking by its ID.

        Args:
            booking_id (str): The unique identifier of the booking to retrieve.

        Returns:
            Dict[str, Any]: A dictionary containing the details of the booking. The
            structure of this dictionary conforms to the CustomResponse16 schema
            defined in the Inspectorio Sight API documentation.

        Raises:
            Exception: If an error occurs during the API call. This can be due to various
                reasons such as the booking not being found (resulting in a 400 Bad Request),
                unauthorized access (401), validation errors (422), rate-limiting (429),
                or internal server errors (500). The exception message will include the HTTP
                status code and a description of the error based on the API's response.

        API Endpoint:
            GET /api/v1/bookings/{booking_id}
        """
        pass

    @abstractmethod
    def list_all_bookings(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetches all bookings, but handles automatically API pagination. Underlying it has
        parallel requests using the `list_bookings()` method. Yet, as it handles
        pagination, it does not need the `offset` parameter.

        Args:
            status (str, optional): Filter bookings by their status. Possible
                values are "NEW", "WAIVED", "CONFIRMED", "REJECTED", "MERGED",
                "CANCELED". Defaults to None.
            to_organization_id (str, optional): Filter bookings that are booked
                to the specified organization ID. Defaults to None.
            updated_from (str, optional): Filter bookings updated from this date
                and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
            created_to (str, optional): Filter bookings created up to this date
                and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
            order (str, optional): Specifies the order of the results. Defaults
                to "created_date:desc". Possible ordering is based on creation date,
                either ascending or descending.
            updated_to (str, optional): Filter bookings updated up to this date
                and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
            created_from (str, optional): Filter bookings created from this date
                and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
            limit (int, optional): The maximum number of items to return.
                Defaults to 10, with a maximum allowable value of 100.
            total_safe_limit (int, optional): An optional parameter to test out
                if pagination is working correctly on a sample (e.g. 1000 extractions)

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the list of bookings
                matching the criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.


        API Endpoint:
            GET /api/v1/bookings
        """
        pass

    @abstractmethod
    def list_products(self) -> Dict[str, Any]:
        """
        Lists all products available in the Inspectorio Sight platform. This method
        sends a GET request to the /products endpoint and returns a dictionary
        containing a list of products. The products are returned according to the
        permissions and access rights of the authenticated user.

        Returns:
            Dict[str, Any]: A dictionary containing the list of products. The structure
                of this dictionary conforms to the ProductListResponse schema defined in
                the Inspectorio Sight API documentation.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request. The specific nature
                of the error (e.g., Unauthorized, Bad Request, Rate-limiting Error,
                Validation Error, Internal Error) is determined by the API's response.

        API Endpoint:
            GET /api/v1/products
        """
        pass

    @abstractmethod
    def list_purchase_orders(
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

        Args:
            po_number (str, optional): Purchase order number to be stored in
                Inspectorio. Defaults to None.
            offset (int, optional): The number of items to skip before starting
                to collect the result set. Defaults to 0.
            delivery_date_to (str, optional): Purchase order delivery date to in
                ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
            delivery_date_from (str, optional): Purchase order delivery date
                from in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
            opo_number (str, optional): Original purchase order number stored in
                the client's system. Defaults to None.
            limit (int, optional): The maximum number of items to return.
                Defaults to 10, with a maximum allowable value of 100.

        Returns:
            Dict[str, Any]: A dictionary containing the list of purchase orders matching
                the criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/purchase-orders
        """
        pass

    @abstractmethod
    def list_all_purchase_orders(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetches all purchase-order, but handles automatically API pagination. Underlying
        it has parallel requests using the `list_purchase_orders()` method. Yet,
        as it handles pagination, it does not need the `offset` parameter.

        Args:
            po_number (str, optional): Purchase order number to be stored in
                Inspectorio. Defaults to None.
            delivery_date_to (str, optional): Purchase order delivery date to in
                ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
            delivery_date_from (str, optional): Purchase order delivery date from
                in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Defaults to None.
            opo_number (str, optional): Original purchase order number stored in
                the client's system. Defaults to None.
            limit (int, optional): The maximum number of items to return.
                Defaults to 10, with a maximum allowable value of 100.
            total_safe_limit (int, optional): An optional parameter to test out
                if pagination is working correctly on a sample (e.g. 1000 extractions)

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the list of purchase
                orders matching the criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/purchase-orders
        """
        pass

    @abstractmethod
    def create_purchase_order(
        self, purchase_order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a Purchase Order with the provided data.

        Args:
            purchase_order_data (Dict[str, Any]): The data for the new purchase
                order. Must conform to the API's expected schema for purchase order
                creation.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the API, typically
                including details of the created purchase order.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            POST /api/v1/purchase-orders
        """
        pass

    @abstractmethod
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
        """
        List reports with optional filters and pagination based on a range of criteria
        including inspection dates, style ID, system update dates, creation and update
        timestamps, report status, and CAPA status. Supports ordering and pagination of
        the results.

        Args:
            inspection_date_from (Optional[str]): Start date for filtering by the range
                of inspection dates. Format: YYYY-MM-DDTHH:MM:SSZ.
            inspection_date_to (Optional[str]): End date for filtering by the range of
                inspection dates. Format: YYYY-MM-DDTHH:MM:SSZ.
            style_id (Optional[str]): Style ID of items included in reports for filtering.
            offset (int): Pagination offset for the results. Default is 0.
            system_updated_from (Optional[str]): Start date for filtering by the range
                of system update dates. Format: YYYY-MM-DDTHH:MM:SSZ.
            status (Optional[Literal["in-progress", "pending", "completed"]]): Status of
                the reports for filtering.
            system_updated_to (Optional[str]): End date for filtering by the range of
                system update dates. Format: YYYY-MM-DDTHH:MM:SSZ.
            updated_from (Optional[str]): Start date for filtering by the range of
                report update dates. Format: YYYY-MM-DDTHH:MM:SSZ.
            created_to (Optional[str]): End date for filtering by the range of report
                creation dates. Format: YYYY-MM-DDTHH:MM:SSZ.
            order (str): Ordering of the reports in the response, by default
                'created_date:desc' for descending order of creation dates.
            updated_to (Optional[str]): End date for filtering by the range of report
                update dates. Format: YYYY-MM-DDTHH:MM:SSZ.
            created_from (Optional[str]): Start date for filtering by the range of
                report creation dates. Format: YYYY-MM-DDTHH:MM:SSZ.
            limit (int): Maximum number of results to return per page. Default is
                defined by DEFAULT_LIMIT.
            capa_status (Optional[Literal[...]]): CAPA status of the report for filtering.

        Returns:
            Dict[str, Any]: A dictionary containing the list of reports matching the
                criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/reports
        """
        pass

    @abstractmethod
    def list_all_reports(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetches all reports, but handles automatically API pagination. Underlying it has
        parallel requests using the `list_reports()` method. Yet, as it handles
        pagination, it does not need the `offset` parameter.

        Args:
            inspection_date_from (Optional[str]): Start date for filtering by the range
                of inspection dates. Format: YYYY-MM-DDTHH:MM:SSZ.
            inspection_date_to (Optional[str]): End date for filtering by the range of
                inspection dates. Format: YYYY-MM-DDTHH:MM:SSZ.
            style_id (Optional[str]): Style ID of items included in reports for filtering.
            system_updated_from (Optional[str]): Start date for filtering by the range
                of system update dates. Format: YYYY-MM-DDTHH:MM:SSZ.
            status (Optional[Literal["in-progress", "pending", "completed"]]): Status of
                the reports for filtering.
            system_updated_to (Optional[str]): End date for filtering by the range of
                system update dates. Format: YYYY-MM-DDTHH:MM:SSZ.
            updated_from (Optional[str]): Start date for filtering by the range of
                report update dates. Format: YYYY-MM-DDTHH:MM:SSZ.
            created_to (Optional[str]): End date for filtering by the range of report
                creation dates. Format: YYYY-MM-DDTHH:MM:SSZ.
            order (str): Ordering of the reports in the response, by default
                'created_date:desc' for descending order of creation dates.
            updated_to (Optional[str]): End date for filtering by the range of report
                update dates. Format: YYYY-MM-DDTHH:MM:SSZ.
            created_from (Optional[str]): Start date for filtering by the range of
                report creation dates. Format: YYYY-MM-DDTHH:MM:SSZ.
            limit (int): Maximum number of results to return per page. Default is
                defined by DEFAULT_LIMIT.
            capa_status (Optional[Literal[...]]): CAPA status of the report for filtering.
            total_safe_limit (int, optional): An optional parameter to test out
                if pagination is working correctly on a sample (e.g. 1000 extractions)

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the list of reports
                matching the criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/reports
        """
        pass

    @abstractmethod
    def get_report(self, report_id: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific report.

        Args:
            report_id (str): The unique identifier for the report.

        Returns:
            Dict[str, Any]: A dictionary containing the details of the report if the
                request is successful.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/reports/{report_id}
        """
        pass

    @abstractmethod
    def list_factory_risk_profiles(
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

        Args:
            date_to (str): End date of the query range in yyyy-mm-dd format.
            date_from (str): Start date of the query range in yyyy-mm-dd format.
            offset (int, optional): The number of items to skip before starting to
                collect the result set. Defaults to 0.
            limit (int, optional): The maximum number of items to return. Defaults to 10,
                with a maximum allowable value of 100.
            date_type (str, optional): The type of the filtered date, such as
                "process_computed_date". Case-sensitive. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing the list of factory risk profiles matching the
                criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/analytics/factory-risk-profile
        """
        pass

    @abstractmethod
    def list_all_factory_risk_profiles(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetches all factory risk profiles, but handles automatically API pagination.
        Underlying it has parallel requests using the `list_factory_risk_profiles()`
        method. Yet, as it handles pagination, it does not need the `offset` parameter.

        Args:
            date_to (str): End date of the query range in yyyy-mm-dd format.
            date_from (str): Start date of the query range in yyyy-mm-dd format.
            limit (int, optional): The maximum number of items to return. Defaults to 10,
                with a maximum allowable value of 100.
            date_type (str, optional): The type of the filtered date, such as
                "process_computed_date". Case-sensitive. Defaults to None.
            total_safe_limit (int, optional): An optional parameter to test out
                if pagination is working correctly on a sample (e.g. 1000 extractions)

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the list of factory
                risk profiles matching the criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/analytics/factory-risk-profile
        """
        pass

    @abstractmethod
    def get_factory_risk_profile(
        self,
        factory_id: str,
        date_to: str,
        date_from: str,
        client_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get Factory Risk Profile for a given factory ID within a specified date range.

        Args:
            factory_id (str): Unique identifier for the factory.
            date_to (str): End date of the query range in yyyy-mm-dd format.
            date_from (str): Start date of the query range in yyyy-mm-dd format.
            client_id (Optional[str]): Unique identifier of the Brand or Retailer
                that the factory produces for.

        Returns:
            Dict[str, Any]: A dictionary containing the factory risk profile if the
                request is successful.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/analytics/factory-risk-profile/{factory_id}
        """
        pass

    @abstractmethod
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
        """
        List Assignments with optional filters. This method allows filtering assignments
        by multiple criteria including factory location, assignment creation and update
        dates, expected inspection dates, assignment status, and supports pagination.

        Args:
            factory_city (Optional[str]): Factory's city of assignments.
                Case-sensitive.
            assignment_created_from (Optional[str]): Assignment created from in
                date and time.
            offset (int, optional): The number of items to skip before starting
                to collect the result set. Defaults to 0.
            expected_inspection_date_to (Optional[str]): End date of the range
                of the expected inspection date in assignments.
            expected_inspection_date_from (Optional[str]): Start date of the
                range of the expected inspection date in assignments.
            assignment_created_to (Optional[str]): Assignment created to in
                date and time.
            assignment_updated_to (Optional[str]): Assignment updated to in
                date and time.
            factory_country (Optional[str]): Factory's country code of
                assignments. Case-insensitive.
            assignment_updated_from (Optional[str]): Assignment updated from
                in date and time.
            order (str, optional): Order of the list of assignments. Defaults
                to "assignment_created_date:desc".
            assignment_status (Optional[Literal["NEW", "PRE-ASSIGNED",
                "ASSIGNED", "RELEASED", "IN-PROGRESS", "COMPLETED", "ABORTED"]]): Status
                of assignments.
            executor_organization (Optional[str]): Inspection Executor of
                assignments. Allows filtering with the Local Organization ID or the
                text "owner". Case-sensitive.
            limit (int, optional): The maximum number of items to return.
                Defaults to 10, with a maximum allowable value of 100.

        Returns:
            Dict[str, Any]: A dictionary containing the list of assignments matching
                the criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/assignments
        """
        pass

    @abstractmethod
    def list_all_assignments(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetches all assignments, but handles automatically API pagination.
        Underlying it has parallel requests using the `list_assignments()`
        method. Yet, as it handles pagination, it does not need the `offset` parameter.

        Args:
            factory_city (Optional[str]): Factory's city of assignments.
                Case-sensitive.
            assignment_created_from (Optional[str]): Assignment created from in
                date and time.
            expected_inspection_date_to (Optional[str]): End date of the range
                of the expected inspection date in assignments.
            expected_inspection_date_from (Optional[str]): Start date of the
                range of the expected inspection date in assignments.
            assignment_created_to (Optional[str]): Assignment created to in
                date and time.
            assignment_updated_to (Optional[str]): Assignment updated to in
                date and time.
            factory_country (Optional[str]): Factory's country code of
                assignments. Case-insensitive.
            assignment_updated_from (Optional[str]): Assignment updated from
                in date and time.
            order (str, optional): Order of the list of assignments. Defaults
                to "assignment_created_date:desc".
            assignment_status (Optional[Literal["NEW", "PRE-ASSIGNED",
                "ASSIGNED", "RELEASED", "IN-PROGRESS", "COMPLETED", "ABORTED"]]): Status
                of assignments.
            executor_organization (Optional[str]): Inspection Executor of
                assignments. Allows filtering with the Local Organization ID or the
                text "owner". Case-sensitive.
            limit (int, optional): The maximum number of items to return.
                Defaults to 10, with a maximum allowable value of 100.
            total_safe_limit (int, optional): An optional parameter to test out
                if pagination is working correctly on a sample (e.g. 1000 extractions)

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the list of assignments
                matching the criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/assignments
        """
        pass

    @abstractmethod
    def get_assignment(self, assignment_id: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific assignment.

        Args:
            assignment_id (str): The unique identifier for the assignment.

        Returns:
            Dict[str, Any]: A dictionary containing the details of the assignment if
                the request is successful.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/assignments/{assignment_id}
        """
        pass

    @abstractmethod
    def list_brands(
        self, offset: int = 0, limit: int = DEFAULT_LIMIT
    ) -> Dict[str, Any]:
        """
        List brands with optional pagination.

        Args:
            offset (int, optional): The number of items to skip before starting
                to collect the result set. Defaults to 0.
            limit (int, optional): The maximum number of items to return.
                Defaults to 10, with a maximum allowable value of 100.

        Returns:
            Dict[str, Any]: A dictionary containing the list of brands matching the criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/brands
        """
        pass

    @abstractmethod
    def list_all_brands(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetches all brands, but handles automatically API pagination. Underlying it has
        parallel requests using the `list_brands()` method. Yet, as it handles
        pagination, it does not need the `offset` parameter.

        Args:
            limit (int, optional): The maximum number of items to return.
                Defaults to 10, with a maximum allowable value of 100.
            total_safe_limit (int, optional): An optional parameter to test out
                if pagination is working correctly on a sample (e.g. 1000 extractions)

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the list of brands
                matching the criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/brands
        """
        pass

    @abstractmethod
    def get_brand(self, brand_id: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific brand.

        Args:
            brand_id (str): The unique identifier for the brand.

        Returns:
            Dict[str, Any]: A dictionary containing the details of the brand if the
                request is successful.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/brands/{brand_id}
        """
        pass

    @abstractmethod
    def update_brand(self, brand_id: str, brand_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update brand details.

        Args:
            brand_id (str): The unique identifier for the brand.
            brand_data (Dict[str, Any]): A dictionary containing the brand data
                to be updated.

        Returns:
            Dict[str, Any]: A dictionary containing the updated details of the brand if
                the request is successful.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            PUT /api/v1/brands/{brand_id}
        """
        pass

    @abstractmethod
    def delete_brand(self, brand_id: str) -> None:
        """
        Delete a brand by its ID.

        Args:
            brand_id (str): The unique identifier for the brand.

        Returns:
            None: This method does not return any value. It completes when the brand is
                successfully deleted.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            DELETE /api/v1/brands/{brand_id}
        """
        pass

    @abstractmethod
    def get_capa(self, report_id: str) -> Dict[str, Any]:
        """
        Retrieve CAPA details for a specific report.

        Args:
            report_id (str): The unique identifier for the report.

        Returns:
            Dict[str, Any]: A dictionary containing the details of the CAPA if the
                request is successful.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/capas/{report_id}
        """
        pass

    @abstractmethod
    def create_file_upload_session(self, payload: dict) -> Dict[str, Any]:
        """
        Creates a file upload session.

        Args:
            payload (dict): The payload for creating a file upload session.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the API call.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            POST /api/v1/file-upload-session
        """
        pass

    @abstractmethod
    def list_lab_test_reports(
        self, offset: int = 0, limit: int = DEFAULT_LIMIT
    ) -> Dict[str, Any]:
        """
        List Lab Test Reports with optional pagination parameters.

        Args:
            offset (int, optional): The number of items to skip before starting
                to collect the result set. Defaults to 0.
            limit (int, optional): The maximum number of items to return.
                Defaults to 10, with a maximum allowable value of 100.

        Returns:
            Dict[str, Any]: A dictionary containing the list of lab test reports
                matching the criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/lab-test-reports
        """
        pass

    @abstractmethod
    def list_all_lab_test_reports(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetches all lab test reports, but handles automatically API pagination.
        Underlying it has parallel requests using the `list_lab_test_reports()`
        method. Yet, as it handles pagination, it does not need the `offset` parameter.

        Args:
            limit (int, optional): The maximum number of items to return.
                Defaults to 10, with a maximum allowable value of 100.
            total_safe_limit (int, optional): An optional parameter to test out
                if pagination is working correctly on a sample (e.g. 1000 extractions)

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the list of lab test
                reports matching the criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/lab-test-reports
        """
        pass

    @abstractmethod
    def create_lab_test_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new Lab Test Report.

        Args:
            report_data (Dict[str, Any]): The data for the new lab test report.

        Returns:
            Dict[str, Any]: A dictionary containing the newly created lab test report's
                details.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            POST /api/v1/lab-test-reports
        """
        pass

    @abstractmethod
    def get_lab_test_report(self, lab_test_report_id: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific lab test report by its ID. This method sends a
        GET request to fetch details of a specific lab test report. It returns the
        report details as a dictionary. Raises exceptions if the fetch fails due to
        reasons such as unauthorized access, report not found, or server errors.

        Args:
            lab_test_report_id (str): The unique identifier of the lab test
                report to retrieve.

        Returns:
            Dict[str, Any]: A dictionary containing the details of the lab test report
                if the request is successful.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/lab-test-reports/{lab_test_report_id}
        """
        pass

    @abstractmethod
    def update_lab_test_report(
        self, lab_test_report_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a specific lab test report by its ID with the provided data.

        Args:
            lab_test_report_id (str): The unique identifier of the lab test
                report to update.
            data (Dict[str, Any]): A dictionary containing the update data for
                the lab test report.

        Returns:
            Dict[str, Any]: A dictionary containing the updated lab test report details
                if the request is successful.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            PUT /api/v1/lab-test-reports/{lab_test_report_id}
        """
        pass

    @abstractmethod
    def delete_lab_test_report(self, lab_test_report_id: str) -> None:
        """
        Delete a specific lab test report by its ID. This method sends a DELETE request
        to the server to remove the specified lab test report. If the request is
        successful, the lab test report is deleted from the server. Raises exceptions
        if the deletion fails due to reasons such as unauthorized access, report not
        found, or server errors.

        Args:
            lab_test_report_id (str): The unique identifier of the lab test
                report to delete.

        Returns:
            None: This method does not return any value. It completes when the lab test
                report is successfully deleted.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            DELETE /api/v1/lab-test-reports/{lab_test_report_id}
        """
        pass

    @abstractmethod
    def get_measurement_chart(self, style_id: str) -> Dict[str, Any]:
        """
        Retrieve measurement chart details for a specific style.

        Args:
            style_id (str): The unique identifier for the style.

        Returns:
            Dict[str, Any]: A dictionary containing the details of the measurement chart
                if the request is successful.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/measurement-charts/{style_id}
        """
        pass

    @abstractmethod
    def create_measurement_chart(
        self, style_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a measurement chart for a specific style.

        Args:
            style_id (str): The unique identifier for the style.
            data (Dict[str, Any]): The data for creating the measurement chart
                according to the MeasurementForm schema.

        Returns:
            Dict[str, Any]: A dictionary containing the details of the newly created
                measurement chart.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            POST /api/v1/measurement-charts/{style_id}
        """
        pass

    @abstractmethod
    def update_measurement_chart(
        self, style_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update measurement chart details for a specific style.

        Args:
            style_id (str): The unique identifier for the style.
            data (Dict[str, Any]): The data for updating the measurement chart
                according to the MeasurementForm schema.

        Returns:
            Dict[str, Any]: A dictionary containing the details of the updated
                measurement chart.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            PUT /api/v1/measurement-charts/{style_id}
        """
        pass

    @abstractmethod
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
        """
        List Metadata with optional filters and pagination.

        Args:
            namespace (str): The logical type of data set by Inspectorio.
                Possible values are "analytics", "inspection".
            offset (int, optional): The number of items to skip before starting
                to collect the result set. Defaults to 0.
            updated_from (str, optional): Start date of the range when metadata
                was updated in ISO 8601 format. Defaults to None.
            created_to (str, optional): End date of the range when metadata was
                created in ISO 8601 format. Defaults to None.
            order (str, optional): Order of metadata in ascending or descending
                based on date filters ("created_date", "updated_date"). Defaults to
                "created_date:desc".
            updated_to (str, optional): End date of the range when metadata was
                updated in ISO 8601 format. Defaults to None.
            created_from (str, optional): Start date of the range when metadata
                was created in ISO 8601 format. Defaults to None.
            limit (int, optional): The limitation of the returned results,
                defaults to 10 with a maximum of 100.

        Returns:
            Dict[str, Any]: A dictionary containing the list of metadata matching the
                criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/metadata/{namespace}
        """
        pass

    @abstractmethod
    def list_all_metadata(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetches all metadata, but handles automatically API pagination. Underlying it
        has parallel requests using the `list_metadata()` method. Yet, as it handles
        pagination, it does not need the `offset` parameter.

        Args:
            namespace (str): The logical type of data set by Inspectorio.
                Possible values are "analytics", "inspection".
            updated_from (str, optional): Start date of the range when metadata
                was updated in ISO 8601 format. Defaults to None.
            created_to (str, optional): End date of the range when metadata was
                created in ISO 8601 format. Defaults to None.
            order (str, optional): Order of metadata in ascending or descending
                based on date filters ("created_date", "updated_date"). Defaults to
                "created_date:desc".
            updated_to (str, optional): End date of the range when metadata was
                updated in ISO 8601 format. Defaults to None.
            created_from (str, optional): Start date of the range when metadata
                was created in ISO 8601 format. Defaults to None.
            limit (int, optional): The limitation of the returned results,
                defaults to 10 with a maximum of 100.
            total_safe_limit (int, optional): An optional parameter to test out
                if pagination is working correctly on a sample (e.g. 1000 extractions)

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the list of metadata
                matching the criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/metadata/{namespace}
        """
        pass

    @abstractmethod
    def create_metadata(
        self,
        namespace: Literal["analytics", "inspection"],
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create Metadata.

        Args:
            namespace (Literal["analytics", "inspection"]): The logical type of
                data set by Inspectorio. Possible values are "analytics", "inspection".
            data (Dict[str, Any]): The data to create metadata with, conforming
                to the MetadataCreate schema.

        Returns:
            Dict[str, Any]: A dictionary containing the created metadata response.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            POST /api/v1/metadata/{namespace}
        """
        pass

    @abstractmethod
    def get_metadata(
        self, namespace: Literal["analytics", "inspection"], uid: str
    ) -> Dict[str, Any]:
        """
        Retrieve metadata for a given UID and namespace.

        Args:
            namespace (Literal["analytics", "inspection"]): The logical type of
                data set by Inspectorio.
            uid (str): Unique identifier within Ecosystem + Namespace, considered
                as unique keys.

        Returns:
            Dict[str, Any]: A dictionary containing the metadata if the request is
                successful.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/metadata/{namespace}/{uid}
        """
        pass

    def update_metadata(
        self,
        namespace: Literal["analytics", "inspection"],
        uid: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update metadata for a given UID and namespace.

        Args:
            namespace (Literal["analytics", "inspection"]): The logical type of
                data set by Inspectorio.
            uid (str): Unique identifier within Ecosystem + Namespace, considered
                as unique keys.
            metadata (Dict[str, Any]): The metadata to update.

        Returns:
            Dict[str, Any]: A dictionary containing the updated metadata if the request
                is successful.

        Raises:Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            PUT /api/v1/metadata/{namespace}/{uid}
        """
        pass

    def delete_metadata(
        self, namespace: Literal["analytics", "inspection"], uid: str
    ) -> None:
        """
        Delete metadata for a given UID and namespace.

        Args:
            namespace (Literal["analytics", "inspection"]): The logical type of
                data set by Inspectorio.
            uid (str): Unique identifier within Ecosystem + Namespace, considered
                as unique keys.

        Returns:
            None: This method does not return any value. It completes when the metadata
                is successfully deleted.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            DELETE /api/v1/metadata/{namespace}/{uid}
        """
        pass

    def list_organizations(
        self, offset: int = 0, limit: int = DEFAULT_LIMIT, name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List organizations with optional filtering by name.

        Args:
            offset (int, optional): The number of items to skip before starting
                to collect the result set. Defaults to 0.
            limit (int, optional): The limit on the number of items to return in
                the response. Defaults to 10, with a maximum of 100.
            name (str, optional): Filter organizations by name.

        Returns:
            Dict[str, Any]: A dictionary containing the list of organizations.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/organizations
        """
        pass

    def list_all_organizations(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetches all metadata, but handles automatically API pagination. Underlying it has
        parallel requests using the `list_organizations()` method. Yet, as it handles
        pagination, it does not need the `offset` parameter.

        Args:
            limit (int, optional): The limit on the number of items to return in
                the response. Defaults to 10, with a maximum of 100.
            name (str, optional): Filter organizations by name.
            total_safe_limit (int, optional): An optional parameter to test out
                if pagination is working correctly on a sample (e.g. 1000 extractions)

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the list of
                organizations matching the criteria.
        """
        pass

    def create_organization(self, organization_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new organization.

        Args:
            organization_data (Dict[str, Any]): A dictionary containing data of
                the organization to create.

        Returns:
            Dict[str, Any]: A dictionary containing the created organization's details.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            POST /api/v1/organizations
        """
        pass

    def get_organization(self, organization_id: str) -> Dict[str, Any]:
        """
        Retrieve details of a specific organization.

        Args:
            organization_id (str): The unique identifier of the organization.

        Returns:
            Dict[str, Any]: A dictionary containing details of the specified organization.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/organizations/{organization_id}
        """
        pass

    def update_organization(
        self, organization_id: str, organization_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update details of a specific organization.

        Args:
            organization_id (str): The unique identifier of the organization to
                update.
            organization_data (Dict[str, Any]): A dictionary containing the update
                data for the organization.

        Returns:
            Dict[str, Any]: A dictionary containing the updated details of the
                organization.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            PUT /api/v1/organizations/{organization_id}
        """
        pass

    def delete_organization(self, organization_id: str) -> None:
        """
        Delete a specific organization.

        Args:
            organization_id (str): The unique identifier of the organization to
                delete.

        Returns:
            None: This method does not return any value. It completes when the
                organization is successfully deleted.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP errors
                or any other issues encountered during the request.

        API Endpoint:
            DELETE /api/v1/organizations/{organization_id}
        """
        pass

    def get_purchase_order(self, po_number: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific purchase order.

        Args:
            po_number (str): The unique identifier for the purchase order.

        Returns:
            Dict[str, Any]: A dictionary containing the details of the purchase order
                if the request is successful.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/purchase-orders/{po_number}
        """
        pass

    def update_purchase_order(
        self, po_number: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update details for a specific purchase order.

        Args:
            po_number (str): The unique identifier for the purchase order.
            payload (Dict[str, Any]): The data to update the purchase order with.

        Returns:
            Dict[str, Any]: A dictionary containing the updated details of the purchase
                order if the request is successful.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            PUT /api/v1/purchase-orders/{po_number}
        """
        pass

    def delete_purchase_order(self, po_number: str) -> None:
        """
        Delete a specific purchase order.

        Args:
            po_number (str): The unique identifier for the purchase order to be
                deleted.

        Returns:
            None: This method does not return any value. It completes when the purchase
                order is successfully deleted.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            DELETE /api/v1/purchase-orders/{po_number}
        """
        pass

    def update_delete_purchase_order(
        self, po_number: str, action: Literal["update", "delete"]
    ) -> Union[Dict[str, Any], None]:
        """
        Update or delete a Purchase Order based on the provided action.

        Args:
            po_number (str): The Purchase Order number to be updated or deleted.
            action (Literal["update", "delete"]): Specifies the action to be
                performed on the Purchase Order.
                - "update": Updates the Purchase Order. The method behaves like a PUT
                    request.
                - "delete": Deletes the Purchase Order. The method behaves like a DELETE
                    request.

        Returns:
        Dict[str, Any]: A dictionary representing the response of the action performed.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            POST /api/v1/purchase-orders/{po_number}/actions/{action}
        """
        pass

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
        """
        List Time and Actions with optional filters and pagination. This method allows
        filtering Time and Actions by purchase order number, status, and creation/update
        timestamps. It also supports pagination of the results.

        Args:
            po_number (str, optional): Filter Time and Actions by purchase order
                number.
            offset (int, optional): The number of items to skip before starting
                to collect the result set.
            status (str, optional): Filter Time and Actions by their status.
                Possible values are "UPCOMING", "NEW", "IN-PROGRESS", "CANCELED",
                "ABORTED", "COMPLETED".
            updated_from (str, optional): Filter Time and Actions updated from
                this date and time.
            created_to (str, optional): Filter Time and Actions created up to
                this date and time.
            updated_to (str, optional): Filter Time and Actions updated to this
                date and time.
            created_from (str, optional): Filter Time and Actions created from
                this date and time.
            limit (int, optional): The maximum number of items to return.
                Defaults to 10.

        Returns:
            Dict[str, Any]: A dictionary containing the list of Time and Actions
                matching the criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/time-and-actions
        """
        pass

    def list_all_time_and_actions(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetches all Time and Actions, but handles automatically API pagination.
        Underlying it has parallel requests using the `list_time_and_actions()`
        method. Yet, as it handles pagination, it does not need the `offset` parameter.

        Args:
            po_number (str, optional): Filter Time and Actions by purchase order
                number.
            status (str, optional): Filter Time and Actions by their status.
                Possible values are "UPCOMING", "NEW", "IN-PROGRESS", "CANCELED",
                "ABORTED", "COMPLETED".
            updated_from (str, optional): Filter Time and Actions updated from
                this date and time.
            created_to (str, optional): Filter Time and Actions created up to
                this date and time.
            updated_to (str, optional): Filter Time and Actions updated to this
                date and time.
            created_from (str, optional): Filter Time and Actions created from
                this date and time.
            limit (int, optional): The maximum number of items to return.
                Defaults to 10.
            total_safe_limit (int, optional): An optional parameter to test out
                if pagination is working correctly on a sample (e.g. 1000 extractions)

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the list of
                Time and Actions matching the criteria.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/time-and-actions
        """
        pass

    def get_time_and_action(self, id: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific Time and Action.

        Args:
            id (str): The unique identifier for the Time and Action.

        Returns:
            Dict[str, Any]: A dictionary containing the details of the Time and Action
                if the request is successful.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/time-and-actions/{id}
        """
        pass

    def update_time_and_actions_milestones(
        self, ta_id: str, data: dict
    ) -> Dict[str, Any]:
        """
        Update Time and Actions milestones.

        Args:
            ta_id (str): The unique identifier for the Time and Action.
            data (dict): The data to update the Time and Action milestones.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the API after
                updating the milestones.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            PUT /api/v1/time-and-actions/{ta_id}/milestones
        """
        pass

    def get_time_and_actions_production_status(
        self, ta_id: str, production_status_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get Time and Actions production status.

        Args:
            ta_id (str): The unique identifier for the Time and Action.
            production_status_level (str, optional): The level of production
                status, either "poLevel" or "itemLevel".

        Returns:
            Dict[str, Any]: A dictionary containing the Time and Actions production
                status.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            GET /api/v1/time-and-actions/{ta_id}/production-status
        """
        pass

    def update_time_and_actions_production_status(
        self, ta_id: str, data: dict
    ) -> Dict[str, Any]:
        """
        Update Time and Actions production status.

        Args:
            ta_id (str): The unique identifier for the Time and Action.
            data (dict): The data to update the Time and Action production status.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the API after
                updating the production status.

        Raises:
            Exception: If an error occurs during the API call. This includes HTTP
                errors or any other issues encountered during the request.

        API Endpoint:
            PUT /api/v1/time-and-actions/{ta_id}/production-status
        """
        pass
