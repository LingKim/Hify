from app.core.responses import PageParams, PageResult, Result


def test_result_success_wraps_payload() -> None:
    result = Result.success(data={"status": "ok"})

    assert result.model_dump() == {
        "code": 200,
        "message": "success",
        "data": {"status": "ok"},
    }


def test_page_result_computes_total_pages() -> None:
    page_result = PageResult.create(
        items=[{"id": 1}, {"id": 2}],
        total=21,
        page=2,
        page_size=20,
    )

    assert page_result.model_dump() == {
        "list": [{"id": 1}, {"id": 2}],
        "total": 21,
        "page": 2,
        "pageSize": 20,
        "totalPages": 2,
    }


def test_page_params_compute_offset_and_aliases() -> None:
    params = PageParams(page=2, pageSize=20)

    assert params.offset == 20
    assert params.model_dump(by_alias=True) == {
        "page": 2,
        "pageSize": 20,
    }
