# Backend Auth / RBAC API

Backend-сервис аутентификации и ролевого управления доступом (RBAC).

**Стек:** Django · Django REST Framework · PostgreSQL · PyJWT · bcrypt · drf-spectacular · Pytest

---

## Быстрый старт

```bash
# 1. Скопировать и заполнить переменные окружения
cp .env.example .env

# 2. Поднять PostgreSQL
docker-compose up -d

# 3. Применить миграции
python manage.py migrate

# 4. Заполнить БД начальными данными
python manage.py seed_db

# 6. Запустить тесты
pytest tests/ -v

# 6. Запустить сервер
python manage.py runserver
```

Swagger UI доступен по адресу: **http://127.0.0.1:8000/api/docs/**

---

## Переменные окружения (.env)

| Переменная | Описание | Пример |
|-----------|---------|--------|
| `SECRET_KEY` | Django secret key | `django-insecure-...` |
| `DEBUG` | Режим отладки | `True` |
| `DB_NAME` | Имя базы данных | `backend_auth` |
| `DB_USER` | Пользователь БД | `project_admin` |
| `DB_PASSWORD` | Пароль БД | `admin` |
| `DB_HOST` | Хост БД | `127.0.0.1` |
| `DB_PORT` | Порт БД | `5432` |
| `JWT_SECRET` | Секрет для подписи JWT | `your-jwt-secret` |
| `JWT_EXPIRATION_HOURS` | Время жизни токена (ч) | `24` |


---

## Тестовые пользователи

После выполнения `python manage.py seed_db`:

| Email | Пароль | Роль |
|-------|--------|------|
| admin@test.com | test1234 | admin |
| manager@test.com | test1234 | manager |
| user@test.com | test1234 | user |
| guest@test.com | test1234 | guest |


---

## Схема БД

<img src="docker/schema.svg" width="600">

## Схема БД (в таблицах)

### `roles`
| Поле | Тип | Описание |
|------|-----|---------|
| id | PK | |
| name | varchar(100), unique | Название роли |
| description | text | Описание |

### `users`
| Поле | Тип | Описание |
|------|-----|---------|
| id | PK | |
| email | varchar, unique | Логин |
| first_name | varchar(150) | Имя |
| last_name | varchar(150) | Фамилия |
| patronymic | varchar(150) | Отчество |
| password_hash | varchar(255) | bcrypt-хеш пароля |
| role_id | FK → roles | Роль пользователя |
| is_active | bool | False = soft deleted |
| is_staff | bool | Доступ к Django admin |
| created_at | datetime | Дата создания |
| updated_at | datetime | Дата обновления |
| deleted_at | datetime, null | Дата удаления (soft) |

### `token_blacklist`
| Поле | Тип | Описание |
|------|-----|---------|
| id | PK | |
| jti | uuid, unique | ID токена из JWT payload |
| expired_at | datetime | Время истечения токена |

### `business_elements`
| Поле | Тип | Описание |
|------|-----|---------|
| id | PK | |
| name | varchar(100), unique | Название ресурса (products, orders...) |
| description | text | Описание |

### `access_rules`
| Поле | Тип | Описание |
|------|-----|---------|
| id | PK | |
| role_id | FK → roles | Роль |
| element_id | FK → business_elements | Ресурс |
| read | bool | Чтение своих объектов |
| read_all | bool | Чтение всех объектов |
| create | bool | Создание |
| update | bool | Обновление своих объектов |
| update_all | bool | Обновление всех объектов |
| delete | bool | Удаление своих объектов |
| delete_all | bool | Удаление всех объектов |

Уникальное ограничение: `(role_id, element_id)`.

**Связи:**
```
roles ──< users (role_id)
roles ──< access_rules (role_id)
business_elements ──< access_rules (element_id)
```

---

## RBAC — система ролевого доступа

### Принцип работы

Каждый защищённый ресурс имеет имя (`rbac_element`). При запросе система:

1. Получает роль текущего пользователя
2. Находит `AccessRule` для пары (роль, ресурс)
3. Маппит HTTP-метод в поле разрешения:

| HTTP-метод | Поле в AccessRule |
|-----------|------------------|
| GET | `read` |
| POST | `create` |
| PATCH / PUT | `update` |
| DELETE | `delete` |

4. Если поле `True` → 200, иначе → 403. Без токена → 401.

### read vs read_all

- `read = True` — пользователь видит **только свои** объекты
- `read_all = True` — пользователь видит **все** объекты в системе

Аналогично для `update` / `update_all` и `delete` / `delete_all`.

### Матрица прав (seed data)

| Роль | products | orders | shops |
|------|----------|--------|-------|
| **admin** | всё | всё | всё |
| **manager** | read_all, create, update | read_all, create, update | read_all |
| **user** | read | read, create, update | read |
| **guest** | read | — | read |

### Типы проверок

- **`IsAdmin`** — прямая проверка `role.name == 'admin'`. Используется для admin API.
- **`RBACPermission`** — проверка через таблицу `access_rules`. Используется для бизнес-ресурсов.

---

## API Endpoints

### Аутентификация

| Метод | URL | Защита | Описание |
|-------|-----|--------|---------|
| POST | `/api/auth/register/` | — | Регистрация нового пользователя |
| POST | `/api/auth/login/` | — | Логин, возвращает JWT токен |
| POST | `/api/auth/logout/` | Bearer token | Инвалидация токена (blacklist) |

### Профиль

| Метод | URL | Защита | Описание |
|-------|-----|--------|---------|
| GET | `/api/auth/me/` | Bearer token | Просмотр своего профиля |
| PATCH | `/api/auth/me/` | Bearer token | Обновление профиля / смена пароля |
| DELETE | `/api/auth/me/` | Bearer token | Soft-удаление аккаунта + logout |

### Admin API (только role=admin)

| Метод | URL | Защита | Описание |
|-------|-----|--------|---------|
| GET | `/api/admin/access-rules/` | IsAdmin | Список всех правил доступа |
| POST | `/api/admin/access-rules/` | IsAdmin | Создать правило |
| GET | `/api/admin/access-rules/{id}/` | IsAdmin | Правило по ID |
| PATCH | `/api/admin/access-rules/{id}/` | IsAdmin | Обновить правило |
| DELETE | `/api/admin/access-rules/{id}/` | IsAdmin | Удалить правило |
| PATCH | `/api/admin/users/{id}/role/` | IsAdmin | Сменить роль пользователя |

### Бизнес-ресурсы (mock)

| Метод | URL | Защита | Описание |
|-------|-----|--------|---------|
| GET | `/api/products/` | RBACPermission | Список товаров |
| GET | `/api/orders/` | RBACPermission | Список заказов |
| GET | `/api/shops/` | RBACPermission | Список магазинов |

---

## Примеры curl-запросов

### Регистрация
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "secret123", "password_confirm": "secret123", "first_name": "Иван", "last_name": "Иванов"}'
```

### Логин
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "test1234"}'
# → {"access_token": "<JWT>", "token_type": "Bearer"}
```

### Просмотр профиля
```bash
curl http://127.0.0.1:8000/api/auth/me/ \
  -H "Authorization: Bearer <TOKEN>"
```

### Получить список товаров
```bash
curl http://127.0.0.1:8000/api/products/ \
  -H "Authorization: Bearer <TOKEN>"
```

### Сменить роль пользователя (admin)
```bash
curl -X PATCH http://127.0.0.1:8000/api/admin/users/2/role/ \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"role": 2}'
```


