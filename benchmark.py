print("Importing FIles...")
import psycopg2
from psycopg2.pool import SimpleConnectionPool
import time
import random
import statistics
from concurrent.futures import ThreadPoolExecutor
import sys

print("Starting benchmark...")
NUM_CLIENTS = int(sys.argv[1]) if len(sys.argv) > 1 else 10
DURATION_SECONDS = 10
NUM_CONNECTIONS = NUM_CLIENTS

pool = SimpleConnectionPool(1, NUM_CONNECTIONS, dbname="shane", host="127.0.0.1", port=5432, user="shane", password="shane123")

queries = [
    ("user_posts", "user_id", "SELECT p.id, p.body FROM posts p WHERE p.user_id = %s ORDER BY p.created_at DESC LIMIT 20"),
    ("post_comments", "post_id", "SELECT c.id, c.body FROM comments c WHERE c.post_id = %s LIMIT 20"),
    ("user_comment_count", "user_id", "SELECT COUNT(*) FROM comments WHERE user_id = %s"),
    ("recent_posts", None, "SELECT id, body FROM posts ORDER BY created_at DESC LIMIT 50"),
]

QUERY_NAMES = [q[0] for q in queries]

def pct(sorted_list, p):
    if not sorted_list:
        return float("nan")
    idx = int(len(sorted_list) * p)
    if idx >= len(sorted_list):
        idx = len(sorted_list) - 1
    return sorted_list[idx]

def summarize(name, lat_list):
    lat_list = sorted(lat_list)
    n = len(lat_list)
    if n == 0:
        return f"{name}: n=0"
    return (f"{name}: n={n} "
            f"avg={statistics.mean(lat_list):.2f}ms "
            f"p50={pct(lat_list,0.50):.2f}ms "
            f"p95={pct(lat_list,0.95):.2f}ms "
            f"p99={pct(lat_list,0.99):.2f}ms")

def run_queries(client_id):
    conn = pool.getconn()
    cur = conn.cursor()
    
    query_count = 0
    per_q = {
        "user_posts": [],
        "post_comments": [],
        "user_comment_count": [],
        "recent_posts": []
    }
    start_time = time.time()
    
    while time.time() - start_time < DURATION_SECONDS:
        qname, ptype, query_sql = random.choice(queries)
        
        query_start = time.time()

        if "user_id" == ptype:
            param = (random.randint(1, 100000),)
            cur.execute(query_sql, param)
        elif "post_id" == ptype:
            param = (random.randint(1, 500000),)
            cur.execute(query_sql, param)
        else:
            param = None
            cur.execute(query_sql)

        cur.fetchall()
        query_time = (time.time() - query_start) * 1000
        
        per_q[qname].append(query_time)
        query_count += 1
    
    cur.close()
    pool.putconn(conn)

    return query_count, per_q

print(f"Running benchmark with {NUM_CLIENTS} concurrent clients for {DURATION_SECONDS} seconds...")
print("=" * 60)

start_time = time.time()

with ThreadPoolExecutor(max_workers=NUM_CLIENTS) as executor:
    futures = [executor.submit(run_queries, i) for i in range(NUM_CLIENTS)]
    results = [f.result() for f in futures]

elapsed = time.time() - start_time

total_queries = sum(r[0] for r in results)

merged = {name: [] for name, _, _ in queries}
for _, per_q in results:
    for name, lst in per_q.items():
        merged[name].extend(lst)

all_latencies = []
for lst in merged.values():
    all_latencies.extend(lst)
all_latencies.sort()


throughput = total_queries / elapsed
p50 = all_latencies[len(all_latencies) // 2]
p95 = all_latencies[int(len(all_latencies) * 0.95)]
p99 = all_latencies[int(len(all_latencies) * 0.99)]
avg_latency = statistics.mean(all_latencies)

print("=" * 60)
print("RESULTS:")
print(f"  Total queries: {total_queries}")
print(f"  Duration: {elapsed:.2f} seconds")
print(f"  Throughput: {throughput:.2f} queries/sec")
print(f"  Latency (avg): {avg_latency:.2f} ms")
print(f"  Latency (p50): {p50:.2f} ms")
print(f"  Latency (p95): {p95:.2f} ms")
print(f"  Latency (p99): {p99:.2f} ms")
print("=" * 60)

with open(f"results_{NUM_CLIENTS}clients.txt", "w") as f:
    f.write(f"Clients: {NUM_CLIENTS}\n")
    f.write(f"Throughput: {throughput:.2f} qps\n")
    f.write(f"Latency p50: {p50:.2f} ms\n")
    f.write(f"Latency p95: {p95:.2f} ms\n")
    f.write(f"Latency p99: {p99:.2f} ms\n")

print(f"Results saved to results_{NUM_CLIENTS}clients.txt")

for names in QUERY_NAMES:
    print(summarize(names, merged[names]))

