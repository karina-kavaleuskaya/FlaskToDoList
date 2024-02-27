import psycopg2


def get_connection(db_name):
    conection = psycopg2.connect(
        dbname=db_name,
        host='****',
        port='****',
        user='****',
        password='****'
    )
    return conection


def main():
    with get_connection("todo_list") as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users(
                id SERIAL PRIMARY KEY,
                user_name TEXT NOT NULL,
                password TEXT NOT NULL 
                )
                """
            )
            conn.commit()

            cursor.execute(
                """
                INSERT INTO users(user_name, password)
                VALUES ('admin', '1111')
                """
            )
            conn.commit()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS todo_list(
                id SERIAL,
                user_id INT NOT NULL,
                category TEXT NOT NULL,
                name TEXT NOT NULL, 
                priority TEXT NOT NULL,
                texts TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
                )
                """
            )
            conn.commit()

            cursor.execute(
                """
                INSERT INTO todo_list(user_id, category, name, priority, texts)
                VALUES ('1', 'Cosplay', 'Val', 'Medium', 'Need to call Tany')
                """
            )
            conn.commit()


if __name__ == '__main__':
    main()
