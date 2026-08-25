"""
Metadata Service 测试配置
"""
import pytest


def pytest_addoption(parser):
    """添加自定义 pytest 选项"""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that call external APIs",
    )


def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test with external APIs"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    if config.getoption("--run-integration"):
        # 运行所有测试
        return

    skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture
def anyio_backend():
    """配置 anyio 后端"""
    return "asyncio"
