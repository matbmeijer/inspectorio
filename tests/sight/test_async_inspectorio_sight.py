import pytest
import respx

from inspectorio.sight import AsyncInspectorioSight


@pytest.mark.asyncio
async def test_base_url_initialization():
    """Test initialization with different base URLs."""
    base_url = "https://sight.pre.inspectorio.com/api/v1"
    client = AsyncInspectorioSight(base_url=base_url)
    assert client._base_url == base_url


@pytest.mark.asyncio
async def test_session_initialization_and_closure():
    """Test the HTTP client session is correctly initialized and closed."""
    async with AsyncInspectorioSight() as client:
        assert client._session is not None
    assert client._session.is_closed


@pytest.mark.asyncio
async def test_login_success():
    with respx.mock as mock_httpx:
        mock_url = "https://sight.inspectorio.com/api/v1/auth/login"
        mock_response = {"data": {"token": "test_token"}}
        mock_httpx.post(mock_url).respond(json=mock_response, status_code=200)
        async with AsyncInspectorioSight() as client:
            await client.login(username="test_user", password="test_pass")
            assert client._token == "test_token"
            assert client._headers == {"token": "test_token"}


@pytest.mark.asyncio
async def test_handle_api_error_with_non_json_response():
    """Test API error handling with a non-JSON response."""
    with respx.mock as mock_httpx:
        mock_url = "https://sight.inspectorio.com/api/v1/test"
        mock_httpx.get(mock_url).respond(
            content=b"Not a JSON response", status_code=500
        )
        async with AsyncInspectorioSight() as client:
            with pytest.raises(Exception) as exc_info:
                await client._make_request("GET", "/test")
            assert "API Error 500: Not a JSON response" in str(exc_info.value)


@pytest.mark.asyncio
async def test_login_with_invalid_token_in_response():
    """Test login method when the response does not contain a valid token."""
    with respx.mock as mock_httpx:
        mock_url = "https://sight.inspectorio.com/api/v1/auth/login"
        mock_response = {}  # Simulating a response without a token
        mock_httpx.post(mock_url).respond(json=mock_response, status_code=200)
        async with AsyncInspectorioSight() as client:
            with pytest.raises(KeyError):
                await client.login(username="test_user", password="test_pass")


@pytest.mark.asyncio
async def test_login_failure():
    with respx.mock as mock_httpx:
        mock_url = "https://sight.inspectorio.com/api/v1/auth/login"
        mock_response = {"errorCode": "Unauthorized", "message": "Invalid credentials"}
        mock_httpx.post(mock_url).respond(json=mock_response, status_code=401)
        async with AsyncInspectorioSight() as client:
            with pytest.raises(Exception) as exc_info:
                await client.login(username="wrong_user", password="wrong_pass")

            assert "API Error 401 [Unauthorized]: Invalid credentials" in str(
                exc_info.value
            )


@pytest.mark.asyncio
async def test_make_request_success():
    with respx.mock as mock_httpx:
        mock_url = "https://sight.inspectorio.com/api/v1/test"
        mock_response = {"data": "success"}
        mock_httpx.get(mock_url).respond(json=mock_response, status_code=200)
        async with AsyncInspectorioSight() as client:
            response = await client._make_request("GET", "/test")
            assert response == mock_response


@pytest.mark.asyncio
async def test_make_request_failure():
    with respx.mock as mock_httpx:
        mock_url = "https://sight.inspectorio.com/api/v1/test"
        mock_response = {"errorCode": "NotFound", "message": "Resource not found"}
        mock_httpx.get(mock_url).respond(json=mock_response, status_code=404)
        async with AsyncInspectorioSight() as client:
            with pytest.raises(Exception) as exc_info:
                await client._make_request("GET", "/test")
            assert "API Error 404 [NotFound]: Resource not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_all_with_pagination():
    items_per_page = 5
    total_items = 12
    all_items = [{"id": i} for i in range(total_items)]
    with respx.mock as mock_httpx:
        base_url = "https://sight.inspectorio.com/api/v1"
        endpoint = "/items"
        # Mock the initial request to fetch the total number of items
        mock_httpx.get(f"{base_url}{endpoint}?limit=1&offset=0").respond(
            json={"data": [all_items[0]], "total": total_items}
        )
        # Continue with the existing mocking setup for subsequent requests
        for offset in range(0, total_items, items_per_page):
            mock_response = {
                "data": all_items[offset : offset + items_per_page],
                "total": total_items,
            }
            mock_httpx.get(
                f"{base_url}{endpoint}?limit={items_per_page}&offset={offset}"
            ).respond(json=mock_response)

        async with AsyncInspectorioSight() as client:

            async def mock_fetch_function(limit, offset=0):
                return await client._make_request(
                    "GET", f"/items?limit={limit}&offset={offset}"
                )

            result_pages = await client._fetch_all_with_pagination(
                mock_fetch_function, limit=items_per_page
            )

            # Flatten the list of results into a single list of items
            flattened_results = [item for page in result_pages for item in page["data"]]

            # Adjust the assertions
            assert (
                len(flattened_results) == total_items
            ), "The total number of items does not match the expected total."
            assert all(
                item in flattened_results for item in all_items
            ), "Not all expected items are in the results."


@pytest.mark.asyncio
async def test_fetch_all_with_pagination_no_items():
    """Test _fetch_all_with_pagination method when there are no items to fetch."""
    with respx.mock as mock_httpx:
        base_url = "https://sight.inspectorio.com/api/v1"
        endpoint = "/empty"
        # Correctly mock the request with expected query parameters
        mock_httpx.get(
            f"{base_url}{endpoint}", params={"limit": 1, "offset": 0}
        ).respond(
            json={
                "data": {},
                "total": 0,
            }  # Ensure the mock response structure matches expected
        )
        async with AsyncInspectorioSight() as client:

            async def mock_fetch_function(limit, offset=0):
                return await client._make_request(
                    "GET", f"/empty?limit={limit}&offset={offset}"
                )

            result = await client._fetch_all_with_pagination(mock_fetch_function)
            assert len(result) == 0


@pytest.mark.asyncio
async def test_clean_kwargs():
    async with AsyncInspectorioSight() as client:
        original_kwargs = {"key1": "value1", "key2": "value2", "remove_this": "gone"}
        cleaned_kwargs = await client._clean_kwargs(original_kwargs, "remove_this")
        assert "remove_this" not in cleaned_kwargs
        assert cleaned_kwargs == {"key1": "value1", "key2": "value2"}
