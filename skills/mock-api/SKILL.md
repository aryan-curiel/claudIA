---
name: mock-api
description: Build a fully mocked FastAPI project from context (text description, markdown file, or folder). Creates entities with REST endpoints, pagination/filtering/ordering, repository pattern with abstract + mocked implementations, and uv/ruff/ty project setup.
---

# Build Mock API

Generate a complete, runnable FastAPI project with mocked data repositories from a domain description.

## Invocation

```
/mock-api <context>
```

`<context>` is one of:
- Inline text describing the domain and entities
- Path to a `.md` spec file
- Path to a folder — read all `.md` files in it

---

## Step 1 — Read context and extract entities

If context is a file path, read it. If a folder, read all `.md` files in it. Extract:

- **Project name** — infer from context (snake_case). If ambiguous, ask once before proceeding.
- **Package name** — same as project name with hyphens replaced by underscores.
- **Entities** — each entity has: name (PascalCase), fields with types, and which fields are filterable/sortable. When not provided, infer from context.

---

## Step 2 — Check if project exists

If a `pyproject.toml` exists in the current directory, skip project creation and go to Step 3. Otherwise:

```bash
uv init <project-name> --app
cd <project-name>
uv add "fastapi[standard]" pydantic
uv add --dev ruff ty
```

Set `pyproject.toml` to include:

```toml
[tool.ruff.lint]
# See: https://docs.astral.sh/ruff/rules/
select = [
    "E4",   # pycodestyle errors - Import errors and indentation issues
    "E7",   # pycodestyle errors - Statement issues (multiple statements on one line, etc.)
    "E9",   # pycodestyle errors - Runtime errors (syntax errors, I/O errors)
    "F",    # Pyflakes - General Python code quality (unused imports, undefined names, etc.)
    "B",    # flake8-bugbear - Common bugs and design problems
    "S",    # flake8-bandit - Security issues and vulnerabilities
    "FAST", # FastAPI - FastAPI-specific best practices
    "PERF", # Perflint - Performance anti-patterns
    "T20",  # flake8-print - Detect print statements
    "LOG",  # flake8-logging - Logging best practices
    # "G",     # flake8-logging-format - Logging format string issues
    "ASYNC", # flake8-async - Async/await best practices and common mistakes
    "C90",   # mccabe - Complexity checks
    "UP",
]
ignore = [
    "PERF401", # manual-list-comprehension
    "PERF403", # manual-dict-comprehension

    "FAST001", # fast-api-redundant-response-model
    "FAST002", # fast-api-non-annotated-dependency
]

[tool.ruff.lint.per-file-ignores]
"test_*.py" = ["B011", "S101", "T20"]
"**/tests/**/*.py" = ["B011", "C901", "S101", "S106", "T20"]
"**/{docs,scripts,tests,tools}/*.py" = ["T20"]
"**/migrations/versions/*.py" = ["T20", "E402"]
"bootstrap/**/*.py" = ["T20", "S701"]
"**/*.ipynb" = ["E402", "T20", "B007"]
"**/project_management/cli/**/*.py" = ["T20", "ASYNC230"]

[tool.ruff.lint.mccabe]
max-complexity = 15

[tool.ruff.lint.flake8-bugbear]
extend-immutable-calls = [
    "fastapi.Depends",
    "fastapi.Path",
    "fastapi.Query",
    "fastapi.Header",
    "fastapi.Cookie",
    "fastapi.Body",
    "fastapi.Form",
    "fastapi.File",
    "fastapi.UploadFile",
]

[tool.ruff.format]
line-ending = "lf"
```

Remove the auto-generated `src/<package>/main.py` placeholder — you will create it from the template below.

---

## Step 3 — Create folder structure

Create the following structure under `src/<package>/`. Create `__init__.py` in every package directory.

```
src/<package>/
├── __init__.py
├── main.py
├── api/
│   ├── __init__.py
│   └── <domain>/               # one per entity
│       ├── __init__.py
│       ├── router.py
│       └── dtos.py
├── repositories/
│   ├── __init__.py
│   ├── abstract.py
│   └── <domain>_repository.py  # one per entity
└── shared/
    ├── __init__.py
    └── pagination.py
```

---

## Templates

Use these templates exactly. Replace `<package>`, `<Domain>`, `<domain>`, `<domains>` with the real names.

---

### `shared/pagination.py`

```python
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
```

---

### `repositories/abstract.py`

```python
import uuid
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from <package>.shared.pagination import PaginatedResponse, PaginationParams

EntityT = TypeVar("EntityT")
CreateT = TypeVar("CreateT")
UpdateT = TypeVar("UpdateT")
FilterT = TypeVar("FilterT")
OrderT = TypeVar("OrderT")


class AbstractRepository(ABC, Generic[EntityT, CreateT, UpdateT, FilterT, OrderT]):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> EntityT | None: ...

    @abstractmethod
    async def list(
        self,
        pagination: PaginationParams,
        filters: FilterT,
        ordering: OrderT,
    ) -> PaginatedResponse[EntityT]: ...

    @abstractmethod
    async def create(self, data: CreateT) -> EntityT: ...

    @abstractmethod
    async def update(self, id: uuid.UUID, data: UpdateT) -> EntityT | None: ...

    @abstractmethod
    async def delete(self, id: uuid.UUID) -> bool: ...
```

---

### `api/<domain>/dtos.py`

Populate fields from the entity definition. `Update<Domain>Request` has all fields optional.

```python
import uuid
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel


class <Domain>Response(BaseModel):
    id: uuid.UUID
    # --- entity fields ---

    model_config = {"from_attributes": True}


class Create<Domain>Request(BaseModel):
    # --- required fields (no id) ---


class Update<Domain>Request(BaseModel):
    # --- all fields optional for partial update ---


class <Domain>Ordering(BaseModel):
    # Each entry is a field name, optionally prefixed with "-" for descending.
    # e.g. ordering=name&ordering=-created_at  →  sort by name asc, then created_at desc
    ordering: Annotated[list[str], Query()] = []


class <Domain>Filter(BaseModel):
    # optional filter fields, all None by default
    # use the same types as the entity, but all Optional
    pass
```

---

### `repositories/<domain>_repository.py`

```python
import uuid
from typing import Annotated

from fastapi import Depends

from <package>.api.<domain>.dtos import (
    <Domain>Filter,
    <Domain>Ordering,
    <Domain>Response,
    Create<Domain>Request,
    Update<Domain>Request,
)
from <package>.repositories.abstract import AbstractRepository
from <package>.shared.pagination import PaginatedResponse, PaginationParams

_mock_store: dict[uuid.UUID, <Domain>Response] = {}


class <Domain>MockRepository(
    AbstractRepository[
        <Domain>Response,
        Create<Domain>Request,
        Update<Domain>Request,
        <Domain>Filter,
        <Domain>Ordering,
    ]
):
    async def get_by_id(self, id: uuid.UUID) -> <Domain>Response | None:
        return _mock_store.get(id)

    async def list(
        self,
        pagination: PaginationParams,
        filters: <Domain>Filter,
        ordering: <Domain>Ordering,
    ) -> PaginatedResponse[<Domain>Response]:
        items = list(_mock_store.values())

        # Apply filters — exact match on non-None filter fields
        for field, value in filters.model_dump(exclude_none=True).items():
            items = [i for i in items if getattr(i, field, None) == value]

        # Apply ordering — process fields right-to-left for stable multi-key sort
        for field_expr in reversed(ordering.ordering):
            descending = field_expr.startswith("-")
            field_name = field_expr.lstrip("-")
            items.sort(
                key=lambda x, f=field_name: (getattr(x, f) is None, getattr(x, f)),
                reverse=descending,
            )

        total = len(items)
        page = items[pagination.offset : pagination.offset + pagination.limit]
        return PaginatedResponse(
            items=page,
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )

    async def create(self, data: Create<Domain>Request) -> <Domain>Response:
        entity = <Domain>Response(id=uuid.uuid4(), **data.model_dump())
        _mock_store[entity.id] = entity
        return entity

    async def update(self, id: uuid.UUID, data: Update<Domain>Request) -> <Domain>Response | None:
        if id not in _mock_store:
            return None
        updated = _mock_store[id].model_copy(update=data.model_dump(exclude_unset=True))
        _mock_store[id] = updated
        return updated

    async def delete(self, id: uuid.UUID) -> bool:
        return _mock_store.pop(id, None) is not None


def get_<domain>_repository() -> AbstractRepository[
    <Domain>Response,
    Create<Domain>Request,
    Update<Domain>Request,
    <Domain>Filter,
    <Domain>Ordering,
]:
    return <Domain>MockRepository()


# Convenience type alias for use in routers
<Domain>RepoDep = Annotated[
    AbstractRepository[
        <Domain>Response,
        Create<Domain>Request,
        Update<Domain>Request,
        <Domain>Filter,
        <Domain>Ordering,
    ],
    Depends(get_<domain>_repository),
]
```

---

### `api/<domain>/router.py`

```python
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from <package>.api.<domain>.dtos import (
    <Domain>Filter,
    <Domain>Ordering,
    <Domain>Response,
    Create<Domain>Request,
    Update<Domain>Request,
)
from <package>.repositories.<domain>_repository import <Domain>RepoDep
from <package>.shared.pagination import PaginatedResponse, PaginationParams

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[<Domain>Response])
async def list_<domains>(
    pagination: Annotated[PaginationParams, Depends()],
    filters: Annotated[<Domain>Filter, Depends()],
    ordering: Annotated[<Domain>Ordering, Depends()],
    repo: <Domain>RepoDep,
) -> PaginatedResponse[<Domain>Response]:
    return await repo.list(pagination=pagination, filters=filters, ordering=ordering)


@router.post("/", response_model=<Domain>Response, status_code=status.HTTP_201_CREATED)
async def create_<domain>(
    data: Create<Domain>Request,
    repo: <Domain>RepoDep,
) -> <Domain>Response:
    return await repo.create(data)


@router.get("/{id}", response_model=<Domain>Response)
async def get_<domain>(
    id: uuid.UUID,
    repo: <Domain>RepoDep,
) -> <Domain>Response:
    entity = await repo.get_by_id(id)
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="<Domain> not found")
    return entity


@router.patch("/{id}", response_model=<Domain>Response)
async def update_<domain>(
    id: uuid.UUID,
    data: Update<Domain>Request,
    repo: <Domain>RepoDep,
) -> <Domain>Response:
    entity = await repo.update(id, data)
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="<Domain> not found")
    return entity


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_<domain>(
    id: uuid.UUID,
    repo: <Domain>RepoDep,
) -> None:
    deleted = await repo.delete(id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="<Domain> not found")
```

---

### `main.py`

Import all routers. Register each with a REST-plural prefix and a display tag.

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from <package>.api.<domain1>.router import router as <domain1>_router
# repeat for each entity


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="<Project Name> API",
    description="Mocked API for <Project Name>",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(<domain1>_router, prefix="/<domains1>", tags=["<Domain1>"])
# repeat for each entity
```

---

## Step 4 — Finish up

After writing all files:

```bash
uv sync
fastapi dev src/<package>/main.py
```

Confirm the server starts and `/docs` loads without errors. If there are import errors, fix them before reporting completion.

Report back with:
- The list of entities generated
- The base URL and docs URL
- The command to start the server
