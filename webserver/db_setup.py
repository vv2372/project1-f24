from sqlalchemy import create_engine, text

DB_USER = "vd2468"
DB_PASSWORD = "vd2468_vv2372"
DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
DATABASEURI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/w4111"

engine = create_engine(DATABASEURI)

def create_tables():
    with engine.connect() as conn:
        conn.execute(text("SET schema 'vd2468';"))
        conn.execute(text("SET search_path TO vd2468;"))
        conn.commit()

        conn.execute(text("DROP TABLE IF EXISTS test;"))
        conn.execute(text("""CREATE TABLE IF NOT EXISTS test (
          id serial,
          name text
        );"""))
        conn.execute(text("INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');"))
        conn.commit()

if __name__ == "__main__":
    create_tables()
    print("Database setup complete.")