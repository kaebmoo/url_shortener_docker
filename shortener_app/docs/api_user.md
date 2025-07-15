Different databases handle auto-incrementing primary keys in slightly different ways. Below are the correct ways to define an auto-incrementing primary key depending on the database system you're using.

### PostgreSQL
PostgreSQL uses the `SERIAL` or `BIGSERIAL` type to create auto-incrementing integer columns.

```sql
CREATE TABLE api_user (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone_number VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    role_id INTEGER,
    api_key_id INTEGER,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (api_key_id) REFERENCES api_key(id)
);
```

### MySQL
In MySQL, you should use `AUTO_INCREMENT` for auto-incrementing columns.

```sql
CREATE TABLE api_user (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone_number VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    role_id INTEGER,
    api_key_id INTEGER,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (api_key_id) REFERENCES api_key(id)
);
```

### SQLite
SQLite does use `AUTOINCREMENT`, but it has stricter requirements compared to other databases. You need to define the `id` column as `INTEGER PRIMARY KEY` without explicitly using `AUTOINCREMENT` unless you need it to strictly increment without reusing deleted values.

```sql
CREATE TABLE api_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone_number VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    role_id INTEGER,
    api_key_id INTEGER,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (api_key_id) REFERENCES api_key(id)
);
```

### Summary:
- **PostgreSQL**: Use `SERIAL`.
- **MySQL**: Use `AUTO_INCREMENT`.
- **SQLite**: Use `AUTOINCREMENT` carefully, only if needed.

Make sure you're using the right syntax for your specific database system. Let me know which database you're using, and I can tailor the SQL statement further if necessary!