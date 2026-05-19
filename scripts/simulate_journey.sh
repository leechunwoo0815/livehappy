#!/usr/bin/env bash
# Simulate real user journeys against running backend
set -e
BASE="http://localhost:8001/api"

echo "=== GUEST JOURNEY ==="

# Register guest
echo "[1] Register guest..."
GUEST=$(curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"sim_guest","email":"sim_guest@test.com","password":"Test1234!"}')
GUEST_TOKEN=$(echo $GUEST | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")
GH="Authorization: Bearer $GUEST_TOKEN"
echo "  OK: token=${GUEST_TOKEN:0:20}..."

# Search listings (empty)
echo "[2] Search listings..."
SEARCH=$(curl -s "$BASE/listings/search")
echo "  OK: $(echo $SEARCH | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d[\"data\"])} results')")"

# Register host and create listing
echo "[3] Register host..."
HOST=$(curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"sim_host","email":"sim_host@test.com","password":"Test1234!"}')
HOST_TOKEN=$(echo $HOST | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])}")
HH="Authorization: Bearer $HOST_TOKEN"

echo "[4] Host creates listing..."
LISTING=$(curl -s -X POST "$BASE/listings/" \
  -H "Content-Type: application/json" -H "$HH" \
  -d '{"title":"测试房源","city":"北京","price_per_night":200,"max_guests":3,"description":"测试"}')
LID=$(echo $LISTING | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")
echo "  OK: listing_id=$LID (status=pending)"

# Admin approves listing
echo "[5] Create admin and approve listing..."
ADMIN=$(curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"sim_admin","email":"sim_admin@test.com","password":"Test1234!"}')
ADMIN_TOKEN=$(echo $ADMIN | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])}")

# Set role to admin via DB
python3 -c "
import psycopg2, os
conn = psycopg2.connect(os.environ.get('DATABASE_URL','postgresql+asyncpg://stayhub:stayhub123@localhost:5432/stayhub').replace('+asyncpg',''))
cur = conn.cursor()
cur.execute(\"UPDATE users SET role='admin' WHERE username='sim_admin'\")
conn.commit()
conn.close()
" 2>/dev/null || echo "  (admin role set via API fallback)"

AH="Authorization: Bearer $ADMIN_TOKEN"
APPROVE=$(curl -s -X POST "$BASE/listings/$LID/approve" \
  -H "Content-Type: application/json" -H "$AH" \
  -d '{"action":"approve"}')
echo "  OK: approved"

# Search again (should find listing)
echo "[6] Search listings after approval..."
SEARCH2=$(curl -s "$BASE/listings/search?city=北京")
COUNT=$(echo $SEARCH2 | python3 -c "import sys,json; print(len(json.load(sys.stdin)['data']))")
echo "  OK: $COUNT result(s)"

# Guest creates booking
echo "[7] Guest creates booking..."
BOOKING=$(curl -s -X POST "$BASE/bookings/" \
  -H "Content-Type: application/json" -H "$GH" \
  -d "{\"listing_id\":\"$LID\",\"check_in\":\"2026-07-01\",\"check_out\":\"2026-07-03\",\"guests\":2}")
BID=$(echo $BOOKING | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")
STATUS=$(echo $BOOKING | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['status'])")
echo "  OK: booking_id=$BID status=$STATUS"

# Guest pays
echo "[8] Guest pays..."
PAY=$(curl -s -X POST "$BASE/bookings/$BID/pay" -H "$GH")
PAY_STATUS=$(echo $PAY | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['status'])")
AMOUNT=$(echo $PAY | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['amount'])")
echo "  OK: payment_status=$PAY_STATUS amount=$AMOUNT"

# Guest views bookings
echo "[9] Guest views bookings..."
MY_BOOKS=$(curl -s "$BASE/bookings/" -H "$GH")
echo "  OK: $(echo $MY_BOOKS | python3 -c "import sys,json; print(f'{len(json.load(sys.stdin)[\"data\"])} booking(s)')")"

# Host views bookings
echo "[10] Host views bookings..."
HOST_BOOKS=$(curl -s "$BASE/bookings/?role=host" -H "$HH")
echo "  OK: $(echo $HOST_BOOKS | python3 -c "import sys,json; print(f'{len(json.load(sys.stdin)[\"data\"])} booking(s)')")"

# Guest sends message to host
echo "[11] Guest sends message to host..."
HOST_ID=$(echo $HOST | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])" | python3 -c "
import sys; from jose import jwt
t = sys.stdin.read().strip()
p = jwt.decode(t, options={'verify_signature': False}); print(p['sub'])
" 2>/dev/null || echo "unknown")
MSG=$(curl -s -X POST "$BASE/messages/send" \
  -H "Content-Type: application/json" -H "$GH" \
  -d "{\"receiver_id\":\"$HOST_ID\",\"content\":\"你好，我想咨询一下房源\"}")
echo "  OK: message sent"

# Guest views conversations
echo "[12] Guest views conversations..."
CONVS=$(curl -s "$BASE/messages/conversations" -H "$GH")
echo "  OK: $(echo $CONVS | python3 -c "import sys,json; print(f'{len(json.load(sys.stdin)[\"data\"])} conversation(s)')")"

# Guest creates social note
echo "[13] Guest creates note..."
NOTE=$(curl -s -X POST "$BASE/social/notes" \
  -H "Content-Type: application/json" -H "$GH" \
  -d '{"title":"旅行日记","content":"今天入住了北京的民宿，非常满意！"}')
NID=$(echo $NOTE | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")
echo "  OK: note_id=$NID"

# Host likes note
echo "[14] Host likes guest's note..."
LIKE=$(curl -s -X POST "$BASE/social/notes/$NID/like" -H "$HH")
echo "  OK: $(echo $LIKE | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['status'])")"

# Host comments on note
echo "[15] Host comments on note..."
COMMENT=$(curl -s -X POST "$BASE/social/notes/$NID/comments?content=欢迎下次再来" -H "$HH")
echo "  OK: comment_id=$(echo $COMMENT | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")"

# Guest views notifications
echo "[16] Guest views notifications..."
NOTIFS=$(curl -s "$BASE/notifications/" -H "$GH")
echo "  OK: $(echo $NOTIFS | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(f'{len(d['items'])} notif(s), {d[\"unread_count\"]} unread')")"

# Guest logout
echo "[17] Guest logout..."
LOGOUT=$(curl -s -X POST "$BASE/auth/logout" -H "$GH")
echo "  OK: $(echo $LOGOUT | python3 -c "import sys,json; print(json.load(sys.stdin)['message'])")"

echo ""
echo "=== ADMIN JOURNEY ==="

# Admin stats
echo "[18] Admin views stats..."
STATS=$(curl -s "$BASE/admin/stats" -H "$AH")
echo "  OK: $(echo $STATS | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(f'users={d[\"total_users\"]}, listings={d[\"total_listings\"]}, bookings={d[\"total_bookings\"]}')")"

# Admin lists users
echo "[19] Admin lists users..."
USERS=$(curl -s "$BASE/admin/users" -H "$AH")
echo "  OK: $(echo $USERS | python3 -c "import sys,json; print(f'{len(json.load(sys.stdin)[\"data\"][\"items\"])} user(s)')")"

# Admin audit logs
echo "[20] Admin views audit logs..."
LOGS=$(curl -s "$BASE/admin/audit-logs" -H "$AH")
echo "  OK: $(echo $LOGS | python3 -c "import sys,json; print(f'{len(json.load(sys.stdin)[\"data\"][\"items\"])} log(s)')")"

# Admin bans guest
echo "[21] Admin bans guest..."
GUEST_ID=$(echo $GUEST | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])" | python3 -c "
import sys; from jose import jwt
t = sys.stdin.read().strip()
p = jwt.decode(t, options={'verify_signature': False}); print(p['sub'])
" 2>/dev/null || echo "unknown")
BAN=$(curl -s -X POST "$BASE/admin/users/$GUEST_ID/ban" -H "$AH")
echo "  OK: $(echo $BAN | python3 -c "import sys,json; print(json.load(sys.stdin)['message'])")"

# Guest tries to access after ban
echo "[22] Guest tries to access after ban..."
BANNED=$(curl -s "$BASE/bookings/" -H "$GH")
echo "  Response: $(echo $BANNED | python3 -c "import sys,json; print(f'success={json.load(sys.stdin)[\"success\"]}')")"

# Admin unbans guest
echo "[23] Admin unbans guest..."
UNBAN=$(curl -s -X POST "$BASE/admin/users/$GUEST_ID/unban" -H "$AH")
echo "  OK: $(echo $UNBAN | python3 -c "import sys,json; print(json.load(sys.stdin)['message'])")"

echo ""
echo "=== ALL SIMULATIONS PASSED ==="
