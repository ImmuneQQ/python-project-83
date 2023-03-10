DROP TABLE IF EXISTS urls CASCADE;
DROP TABLE IF EXISTS url_checks CASCADE;

CREATE TABLE urls (
    id int PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(255) UNIQUE,
    created_at timestamp
);

CREATE TABLE url_checks (
    id int PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    url_id int REFERENCES urls (id),
    status_code int,
    h1 varchar(255),
    title varchar(255),
    description varchar(255),
    created_at timestamp
);