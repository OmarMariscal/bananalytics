import flet as ft
from frontend.app import App


USE_MOCK = False

if USE_MOCK:
    from service.mock.mock_backend_service import MockBackendService
    backend_service = MockBackendService()
else:
    from service.backend.backend_service import BackendService
    backend_service = BackendService()

ft.app(target=lambda page: App(backend_service, page))