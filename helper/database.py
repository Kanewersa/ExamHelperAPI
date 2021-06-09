import psycopg2

DROP_TABLES = """
        DO $$ DECLARE
      r RECORD;
    BEGIN
      FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
        EXECUTE 'DROP TABLE ' || quote_ident(r.tablename) || ' CASCADE';
      END LOOP;
    END $$;
    """

CREATE_TABLES = (
    """
    CREATE SEQUENCE IF NOT EXISTS terms_id_seq;
    """,
    """
    CREATE SEQUENCE IF NOT EXISTS courses_id_seq;
    """,
    """
    CREATE SEQUENCE IF NOT EXISTS exams_id_seq;
    """,
    """
    CREATE SEQUENCE IF NOT EXISTS questions_id_seq;
    """,
    """
    CREATE SEQUENCE IF NOT EXISTS answers_id_seq;
    """,
    """
    CREATE SEQUENCE IF NOT EXISTS votes_id_seq;
    """,
    """
    CREATE SEQUENCE IF NOT EXISTS users_id_seq;
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
    id INT NOT NULL UNIQUE DEFAULT nextval('users_id_seq'),
    name VARCHAR(255) NOT NULL,
    ip_address VARCHAR(15) NOT NULL,
    PRIMARY KEY (id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS terms (
    id INT NOT NULL UNIQUE DEFAULT nextval('terms_id_seq'),
    name VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS courses (
    id INT NOT NULL UNIQUE DEFAULT nextval('courses_id_seq'),
    name VARCHAR(255) NOT NULL,
    term_id INT NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_term
        FOREIGN KEY(term_id)
            REFERENCES terms(id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS exams (
    id INT NOT NULL UNIQUE DEFAULT nextval('exams_id_seq'),
    name VARCHAR(255) NOT NULL,
    description VARCHAR(255),
    course_id INT NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_course
        FOREIGN KEY(course_id)
            REFERENCES courses(id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS questions (
    id INT NOT NULL UNIQUE DEFAULT nextval('questions_id_seq'),
    content TEXT NOT NULL,
    image TEXT NOT NULL,
    exam_id INT NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_exam
        FOREIGN KEY(exam_id)
            REFERENCES exams(id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS answers (
    id INT NOT NULL UNIQUE DEFAULT nextval('answers_id_seq'),
    question_id INT NOT NULL,
    content VARCHAR(255) NOT NULL,
    image TEXT,
    upvotes INT DEFAULT 0,
    downvotes INT DEFAULT 0,
    CONSTRAINT fk_question
        FOREIGN KEY(question_id)
            REFERENCES questions(id)
    );
    """
    # ,
    # """
    # CREATE TABLE IF NOT EXISTS votes (
    # id INT NOT NULL UNIQUE DEFAULT nextval('votes_id_seq'),
    # answer_id INT,
    # question_id INT,
    # value INT NOT NULL
    # );
    # """
)


class DatabaseManager:
    cur = None
    con = None

    def __init__(self):
        self.con = None
        self.cur = None

    def connect(self):
        self.con = psycopg2.connect(database="postgres", user="postgres", password="czekoladka", host="127.0.0.1")
        self.cur = self.con.cursor()
        DatabaseManager.con = self.con
        DatabaseManager.cur = self.con.cursor()

    def drop_tables(self):
        self.cur.execute(DROP_TABLES)
        self.con.commit()

    def create_tables(self):
        for table in CREATE_TABLES:
            self.cur.execute(table)
        self.con.commit()

    def disconnect(self):
        self.con.close()

    def execute(self, statement):
        self.cur.execute(statement.command)
        return self.cur.fetchall()


class Statement:
    def __init__(self):
        self.command = ""
        self.returningStatement = False

    def insert(self, column, *values):
        values = ', '.join(f"'{value}'" for value in values)
        self.command = "INSERT INTO " + column + " VALUES("+values+")"
        return self

    def returning(self):
        self.returningStatement = True
        self.command += " RETURNING *"
        return self

    def get_all(self, table):
        self.command += "SELECT * FROM " + table
        return self

    def where(self, cond):
        self.command += " WHERE " + cond
        return self

    def equals(self, cond):
        self.command += " = '" + cond + "'"
        return self

    def update(self, table, value):
        self.command = "UPDATE " + table + " SET " + value
        return self

    def drop(self, table):
        self.command = "DROP TABLE IF EXISTS " + table
        return self

    def execute(self):
        DatabaseManager.cur.execute(self.command)
        if DatabaseManager.cur.description is not None:
            if self.returningStatement:
                DatabaseManager.con.commit()
            return DatabaseManager.cur.fetchall()
        else:
            DatabaseManager.con.commit()
