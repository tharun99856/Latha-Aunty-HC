import urllib.request
import json


def api(method, path, data=None):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f"http://localhost:8000{path}", data=body, method=method)
    if body:
        req.add_header("Content-Type", "application/json")
    return json.loads(urllib.request.urlopen(req).read())


s = api("POST", "/api/session/open")
print("Session opened:", s["date"])

for i in range(5):
    phone = f"98765432{i:02d}" if i < 3 else None
    t = api("POST", "/api/token", {"phone": phone})
    print(f"  {t['number']} | pos={t['position']} wait={t['estimated_wait']}min | phone={t.get('phone') or '-'}")

q = api("GET", "/api/queue")
print(f"\nQueue: {q['waiting']} waiting, inactive={q['doctor_inactive']}")

n = api("POST", "/api/queue/next")
print(f"Doctor called: {n.get('number', 'empty')}")

q2 = api("GET", "/api/queue")
ct = q2["current_token"]
print(f"Now: {q2['waiting']} waiting, serving={ct['number'] if ct else '-'}")

n2 = api("POST", "/api/queue/next")
print(f"Doctor called: {n2.get('number', 'empty')}")

q3 = api("GET", "/api/queue")
print(f"Now: {q3['waiting']} waiting, served today={q3['session']['total_served']}")

ts = api("GET", "/api/token/T-004")
print(f"\nT-004: status={ts['status']}, pos={ts.get('position', '-')}, wait={ts.get('estimated_wait', '-')}min")

print("\nAll tests passed.")
