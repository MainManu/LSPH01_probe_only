import psycopg2 as pg
import time

log_initialized = False
log_filename =""

def init_testing_db(drop=False):
    # connect to the database
    conn = pg.connect(
        host="localhost",
        database="grafana",
        user="user",
        password="verySecure"
    )
    # create a cursor
    cur = conn.cursor()
    if drop:
        drop_testing_table(cur)
    create_testing_table(cur)
    return conn, cur

def init_db(drop=False, host="localhost", database="grafana", user="user", password="verySecure", table_name="probe_data"):
    # connect to the database
    conn = pg.connect(
        host=host,
        database=database,
        # user="user",
        # password="verySecure"
        user = user,
        password = password
    )
    # create a cursor
    cur = conn.cursor()
    if drop:
        drop_table(cur)
    # add_column(cur, conn, 'ph_should_be', 'REAL')
        create_table(cur, table_name=table_name)
    return conn, cur

def create_table(cur, table_name="probe_data"):
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            ph_high_res NUMERIC(5,2),
            ph_low_res NUMERIC(5,1),
            temperature NUMERIC(5,1),
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            name VARCHAR(255), 
            ph_should_be NUMERIC(5,2)
        )
    """)

def create_testing_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS probe_testing_data (
            id SERIAL PRIMARY KEY,
            ph_high_res NUMERIC(5,2),
            ph_low_res NUMERIC(5,1),
            temperature NUMERIC(5,1),
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            name VARCHAR(255),
            ph_should_be NUMERIC(5,2)
        )
    """)

def drop_testing_table(cur):
    cur.execute("""
        DROP TABLE IF EXISTS probe_testing_data
    """)

def drop_table(cur):
    cur.execute("""
        DROP TABLE IF EXISTS probe_data
    """)

def insert_testing_data(cur, conn, ph_high_res, ph_low_res, temperature, name='probe1', ph_should_be=100.0):
    cur.execute("""
        INSERT INTO probe_testing_data (ph_high_res, ph_low_res, temperature, name, ph_should_be)
        VALUES (%s, %s, %s, %s, %s)
    """, (ph_high_res, ph_low_res, temperature, name, ph_should_be))
    conn.commit()



def insert_data(cur, conn, ph_high_res, ph_low_res, temperature, name='probe1', ph_should_be=100.0, time=None):
    if time:
        cur.execute("""
            INSERT INTO probe_data (ph_high_res, ph_low_res, temperature, name, ph_should_be, time)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (ph_high_res, ph_low_res, temperature, name, ph_should_be, time))
    else:
        cur.execute("""
            INSERT INTO probe_data (ph_high_res, ph_low_res, temperature, name, ph_should_be)
            VALUES (%s, %s, %s, %s, %s)
        """, (ph_high_res, ph_low_res, temperature, name, ph_should_be))
        conn.commit()

def insert_data_csv(ph_high_res, ph_low_res, temperature, name='probe1', ph_should_be=100.0, timestamp=None):
    global log_initialized
    global log_filename
    if log_initialized == False:
        log_filename = f"log_{time.asctime().replace(' ', '_')}.csv"
        with open(log_filename, "a") as logfile:
            logfile.write("probe_name,timestamp,ph_high_res,temperature,ph_should_be\n")
        log_initialized = True

        
    with open(log_filename,"a") as log:
        log.write(f"{name},{timestamp},{ph_high_res},{temperature}, {ph_should_be}\n")



def add_column(cur, conn, column_name, data_type):
    cur.execute(f"""
        ALTER TABLE probe_data
        ADD COLUMN  IF NOT EXISTS {column_name} {data_type}
    """)
    conn.commit()


def merge_tables(merge_host, merge_database, merge_user, merge_password, merge_table_name, also_to_remote=False):
    conn1, cur1 = init_db() # the defaultdatabase
    conn2, cur2= init_db(host=merge_host, database=merge_database, user=merge_user, password=merge_password, table_name=merge_table_name) # the database to be merged

    cur2.execute(f"""
        SELECT * FROM public.{merge_table_name}
    """)
    data_to_merge = cur2.fetchall()
    data_to_merge_no_id = [row[1:] for row in data_to_merge] # id might be different in the two databases for identical data
    cur1.execute(f"""
            SELECT * FROM public.probe_data
        """)
    local_data = cur1.fetchall()
    local_data_no_id = [row[1:] for row in local_data] # id might be different in the two databases for identical data

    for row in data_to_merge_no_id:
        #check if the row is already in the default database
        if row not in local_data_no_id:
            insert_data(cur1, conn1,ph_high_res=row[0],ph_low_res=row[1],temperature=row[2],time=row[3], name=row[4],ph_should_be=row[5])
            print(f"Inserted {row[4]} into default database")
        else:
            print(f"Duplicate found in remote: {row[3]}, skipping...")
    
    # merge data to remote database
    if also_to_remote:
        for row in local_data_no_id:
            if row not in data_to_merge_no_id:
                insert_data(cur2, conn2,ph_high_res=row[0],ph_low_res=row[1],temperature=row[2],time=row[3], name=row[4],ph_should_be=row[5])
                print(f"Inserted {row[4]} into remote database")
            else:
                print(f"Duplicate found locally: {row[3]}, skipping...")
    
    conn1.commit()
    conn2.commit()
    conn1.close()
    conn2.close()

if __name__ == "__main__":
    # init_db()
    # init_testing_db()
    insert_data_csv(0,0,0,"hi",100,0)
