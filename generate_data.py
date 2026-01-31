import psycopg2, random, datetime

conn = psycopg2.connect(dbname="shane", host="localhost")
cur = conn.cursor()

NUM_USERS = 100000
NUM_POSTS = 500000
NUM_COMMENTS = 1000000

for i in range(NUM_USERS):
    cur.execute("INSERT INTO users (username, created_at) VALUES (%s, %s)",
                (f"user{i}", datetime.datetime.now()))
conn.commit()

for i in range(NUM_POSTS):
    cur.execute("INSERT INTO posts (user_id, body, created_at) VALUES (%s, %s, %s)",
                (random.randint(1, NUM_USERS), "hello world", datetime.datetime.now()))
conn.commit()

for i in range(NUM_COMMENTS):
    cur.execute("INSERT INTO comments (post_id, user_id, body, created_at) VALUES (%s, %s, %s, %s)",
                (random.randint(1, NUM_POSTS), random.randint(1, NUM_USERS),
                 "nice", datetime.datetime.now()))
conn.commit()
