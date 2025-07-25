import pytest

from src.analyzer.repo_analyzer import build_repo_model


@pytest.mark.asyncio
async def test_build_repo_model():
    result = await build_repo_model(
        "/Users/oleh/stuff/wiki_generator/be/tmp/rich-cli"
    )
    print(result)
    assert False
