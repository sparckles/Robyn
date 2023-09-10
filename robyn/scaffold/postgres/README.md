docker run
    --name some-postgres
    -p 5455:5432
    -e POSTGRES_USER=postgres
    -e POSTGRES_PASSWORD=password
    -e POSTGRES_DB=postgresDB
    -d
    postgres
