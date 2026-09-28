from fastapi import APIRouter

router = APIRouter()


@router.post("/login")
def login() -> None:
    pass


@router.post("/logout")
def logout() -> None:
    pass
