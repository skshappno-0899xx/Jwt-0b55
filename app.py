# KAWSARx64 Premium JWT Generator API
# tg: @kawsar449x
# Render-ready version

import os
import json
import base64
import ssl
import gzip
import http.client
import urllib3
import requests
import logging
from io import BytesIO
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from flask import Flask, request, jsonify

import MajoRLoGinrEs_pb2

# ============================================================
# APP + LOGGING
# ============================================================
app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("kawsar")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CREDIT = {"dev": "KAWSARx64", "tg": "@kawsar449x"}

# ============================================================
# CONFIG
# ============================================================
MajorLoginHost  = "loginbp.ppmainecoonghj.com"
MajorLoginPath  = "/MajorLogin"
FreeFireVersion = "OB55"

GUEST_URL     = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"
CLIENT_ID     = 100067
CLIENT_SECRET = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"

AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

RESPONSE_HEADER_LEN = 64
DEFAULT_REGION      = "BD"
DEFAULT_LANG        = "bn"

# Version file — Render ephemeral disk এ হারিয়ে গেলে env var fallback
VERSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ob_version.txt")


def get_version():
    # 1) env var priority (Render dashboard এ সেট করা যায়)
    env_v = os.environ.get("OB_VERSION")
    if env_v:
        return env_v.strip()
    # 2) file
    try:
        if os.path.exists(VERSION_FILE):
            return open(VERSION_FILE).read().strip()
    except Exception:
        pass
    # 3) default
    return FreeFireVersion


def set_version(v):
    # Try file first (works locally / with disk)
    try:
        with open(VERSION_FILE, "w") as f:
            f.write(v)
        return True
    except Exception as e:
        log.warning(f"set_version failed (ephemeral disk?): {e}")
        return False


# ============================================================
# PROTOBUF ENCODER
# ============================================================
def encode_varint(num: int) -> bytes:
    if num < 0:
        raise ValueError("Number must be non-negative")
    out = []
    while True:
        b = num & 0x7F
        num >>= 7
        if num:
            b |= 0x80
        out.append(b)
        if not num:
            break
    return bytes(out)


def create_field(num, val):
    if isinstance(val, bool):
        return encode_varint((num << 3) | 0) + encode_varint(int(val))
    if isinstance(val, int):
        return encode_varint((num << 3) | 0) + encode_varint(val)
    if isinstance(val, (str, bytes)):
        v = val.encode() if isinstance(val, str) else val
        return encode_varint((num << 3) | 2) + encode_varint(len(v)) + v
    if isinstance(val, dict):
        nested = create_packet(val)
        return encode_varint((num << 3) | 2) + encode_varint(len(nested)) + nested
    return b""


def create_packet(fields: dict) -> bytes:
    return b"".join(create_field(k, v) for k, v in fields.items())


# ============================================================
# AES-CBC
# ============================================================
def encrypt_api(plain_hex: str) -> str:
    plain  = bytes.fromhex(plain_hex)
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(plain, AES.block_size)).hex()


def _aes_decrypt(data: bytes) -> bytes:
    try:
        cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
        dec = cipher.decrypt(data)
        padlen = dec[-1]
        if 1 <= padlen <= 16 and all(b == padlen for b in dec[-padlen:]):
            dec = dec[:-padlen]
        return dec
    except Exception:
        return b""


# ============================================================
# RESPONSE DECODER
# ============================================================
def decode_response(resp: bytes):
    def _try_parse(blob: bytes):
        if not blob:
            return None
        try:
            m = MajoRLoGinrEs_pb2.MajorLoginRes()
            m.ParseFromString(blob)
            if m.account_id > 0 and (m.lock_region or m.noti_region or m.token):
                return m
        except Exception:
            pass
        return None

    m = _try_parse(resp)
    if m:
        return m, "plaintext proto", resp

    if len(resp) > RESPONSE_HEADER_LEN:
        m = _try_parse(resp[RESPONSE_HEADER_LEN:])
        if m:
            return m, f"plaintext proto (skip {RESPONSE_HEADER_LEN}B sig)", resp[RESPONSE_HEADER_LEN:]

    if len(resp) >= 16 and len(resp) % 16 == 0:
        dec = _aes_decrypt(resp)
        if dec:
            m = _try_parse(dec)
            if m:
                return m, "AES-CBC", dec

            if len(dec) > RESPONSE_HEADER_LEN:
                m = _try_parse(dec[RESPONSE_HEADER_LEN:])
                if m:
                    return m, f"AES-CBC (skip {RESPONSE_HEADER_LEN}B sig)", dec[RESPONSE_HEADER_LEN:]

    return None, "unknown", resp


# ============================================================
# JWT DECODER
# ============================================================
def decode_jwt(token: str) -> dict:
    try:
        if not token or not isinstance(token, str):
            return {}
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        raw = base64.urlsafe_b64decode(payload_b64)
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


# ============================================================
# BUILD MajorLogin REQUEST BODY
# ============================================================
def build_major_login_body(access_token: str, open_id: str,
                           region: str = DEFAULT_REGION,
                           lang: str = DEFAULT_LANG) -> bytes:
    fields = {
        3:  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        4:  "free fire",
        5:  1,
        7:  "1.132.4",
        8:  "Android OS 15 / API-35 (AP3A.240617.008/T.R4T2.24e2a71-650ec)",
        9:  "Handheld",
        10: "airtel now cirkle",
        11: "WIFI",
        12: 1666,
        13: 750,
        14: "360",
        15: "ARM64 FP ASIMD AES | 2000 | 8",
        16: 7723,
        17: "Mali-G52 MC2",
        18: "OpenGL ES 3.2 v1.r49p1-03bet0.19498e0ae1d5dac223383c39a2e58f04",
        19: "Google|3744f365-78fe-424a-871e-f77a0a095356",
        20: "103.109.214.50",
        21: lang,
        22: open_id,
        23: "8",
        24: "Handheld",
        25: "realme RMX3710",
        26: region,
        29: access_token,
        30: 1,
        41: "airtel now cirkle",
        42: "WIFI",
        57: "7428b253defc164018c604a1ebbfebdf",
        60: 225554,
        61: 155321,
        62: 733,
        64: 155845,
        65: 225554,
        66: 155845,
        67: 225554,
        73: 2,
        74: "/data/app/~~ln8dFa29BUuPBtG4A-WwXQ==/com.dts.freefireth-tXx7bnxvKbykwJzwnEHs2Q==/lib/arm64",
        76: 1,
        77: "b8e0cd5e295eee42f5860d3c86e483dd|/data/app/~~ln8dFa29BUuPBtG4A-WwXQ==/com.dts.freefireth-tXx7bnxvKbykwJzwnEHs2Q==/base.apk",
        78: 3,
        79: 2,
        81: "64",
        83: "2019121229",
        85: 3,
        86: "OpenGLES2",
        87: 8191,
        88: 8,
        92: 9754,
        93: "android",
        94: "KqsHT+PFj/2sTPjf+unI9C5rnnStUzOFVqOADw9TI8tgL2bTnmzrBM/dEzyqy4BtAVua+w9mgLRIMrjXa67/qXm0pz5uQWsxC6sd8Um7OmMNHRmy",
        95: 111207,
        96: '{"cur_rate":[60,45,90],"support_etc2":false}',
        97: 1,
        99: "4",
        100: "4",
        102: "4455414f055f5f0336",
        104: 52972,
        105: 1,
        106: "https://dl-bs.ggpolarbear.com/live/ABHotUpdates/|https://core-bs.ggpolarbear.com/live/ABHotUpdates/|6b2078db9d22dd98f8e9386a39af8462",
        107: "c8e41b7a93f02d56e1a94c7b8203f5d1",
    }
    return create_packet(fields)


# ============================================================
# GARENA GUEST TOKEN
# ============================================================
def get_access_token(uid, password):
    headers = {
        "User-Agent":   "GarenaMSDK/4.0.42(M2006C3LII ;Android 10;en;IN;app 1.126.2 2019120816;)",
        "Accept":       "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "Connection":   "Keep-Alive",
    }
    payload = {
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "client_type":   2,
        "password":      password,
        "response_type": "token",
        "uid":           int(uid),
    }
    try:
        r = requests.post(GUEST_URL, headers=headers, json=payload,
                          verify=False, timeout=15)
        if r.status_code == 200:
            j = r.json()
            if j.get("code") == 0:
                d = j.get("data", {}) or {}
                return d.get("access_token"), d.get("open_id")
    except Exception as e:
        log.warning(f"get_access_token error: {e}")
    return None, None


# ============================================================
# MAJOR LOGIN REQUEST
# ============================================================
def major_login_request(access_token, open_id,
                        region=DEFAULT_REGION, lang=DEFAULT_LANG):
    try:
        ob        = get_version()
        plaintext = build_major_login_body(access_token, open_id, region, lang)
        body      = bytes.fromhex(encrypt_api(plaintext.hex()))

        ctx  = ssl._create_unverified_context()
        conn = http.client.HTTPSConnection(MajorLoginHost, context=ctx, timeout=15)
        conn.request("POST", MajorLoginPath, body=body, headers={
            'User-Agent':       'UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)',
            'Accept':           '*/*',
            'Accept-Encoding':  'deflate, gzip',
            'Authorization':    'Bearer',
            'X-Ga':             'v1 1',
            'X-Ga-Sv':          '1789556611',
            'Releaseversion':   ob,
            'Content-Type':     'application/x-www-form-urlencoded',
            'X-Unity-Version':  '2018.4.12f1',
        })

        resp = conn.getresponse()
        raw  = resp.read()
        if resp.getheader("Content-Encoding") == "gzip":
            with gzip.GzipFile(fileobj=BytesIO(raw)) as f:
                raw = f.read()
        conn.close()

        if resp.status in (200, 201):
            return raw, None
        return None, f"HTTP {resp.status}: {raw[:120].decode('utf-8', 'replace')}"
    except Exception as e:
        return None, str(e)


# ============================================================
# CORE
# ============================================================
def generate_jwt(uid, password):
    if not uid or not password:
        return {"success": False, "message": "UID and Password required", **CREDIT}
    if not str(uid).isdigit() or len(str(uid)) < 8:
        return {"success": False, "message": "Invalid UID format", **CREDIT}

    access_token, open_id = get_access_token(uid, password)
    if not access_token or not open_id:
        return {"success": False, "message": "Invalid UID or Password", **CREDIT}

    raw, err = major_login_request(access_token, open_id)
    if not raw:
        return {"success": False,
                "message": f"Login failed — {err or 'account may be banned'}",
                **CREDIT}

    res, mode, _ = decode_response(raw)
    if not res or not res.token:
        return {"success": False,
                "message": "No JWT token received",
                "decode_mode": mode,
                **CREDIT}

    jwt_payload = decode_jwt(res.token)

    return {
        "success":          True,
        "uid":              str(uid),
        "region":           res.lock_region or res.noti_region or DEFAULT_REGION,
        "token":            res.token,

        "account_id":       str(res.account_id),
        "kts":              res.kts,
        "ak":               res.ak.hex() if res.ak else "",
        "aiv":              res.aiv.hex() if res.aiv else "",

        "lock_region":      res.lock_region,
        "noti_region":      res.noti_region,
        "ip_region":        res.ip_region,
        "agora_environment": res.agora_environment,
        "server_url":       res.server_url,
        "tp_url":           res.tp_url,
        "ip_city":          res.ip_city,
        "ip_subdivision":   res.ip_subdivision,

        "queue_allow":      res.queue_info.allow if res.HasField("queue_info") else None,

        "external_id":      jwt_payload.get("external_id", ""),
        "external_uid":     jwt_payload.get("external_uid", ""),
        "signature_md5":    jwt_payload.get("signature_md5", ""),
        "exp":              jwt_payload.get("exp"),

        "decode_mode":      mode,
        **CREDIT,
    }


# ============================================================
# ROUTES
# ============================================================
@app.get("/token")
def api_token():
    uid      = request.args.get("uid", "").strip()
    password = request.args.get("password", "").strip()

    result = generate_jwt(uid, password)

    if not result.get("success"):
        return jsonify(result)

    return jsonify({
        "success":    True,
        "token":      result["token"],
        "account_id": result["account_id"],
        "region":     result["region"],
    })


@app.get("/KAWSARx64")
def kawsar_route():
    uid      = request.args.get("uid", "").strip()
    password = request.args.get("password", "").strip()
    return jsonify(generate_jwt(uid, password))


@app.post("/KAWSARx64")
def kawsar_post():
    d        = request.get_json(silent=True) or {}
    uid      = d.get("uid", request.form.get("uid", "")).strip()
    password = d.get("password", request.form.get("password", "")).strip()
    return jsonify(generate_jwt(uid, password))


@app.get("/update+")
def version_up():
    v = get_version()
    try:
        num  = int(v.replace("OB", ""))
        newv = f"OB{num + 1}"
        ok   = set_version(newv)
        return jsonify({
            "success": True,
            "old": v,
            "new": newv,
            "persisted": ok,
            "note": None if ok else "Ephemeral disk — set OB_VERSION env var on Render to persist",
            **CREDIT
        })
    except Exception:
        return jsonify({"success": False, "error": "Bad version format",
                        "current": v, **CREDIT})


@app.get("/update-")
def version_down():
    v = get_version()
    try:
        num  = int(v.replace("OB", ""))
        newv = f"OB{num - 1}"
        ok   = set_version(newv)
        return jsonify({
            "success": True,
            "old": v,
            "new": newv,
            "persisted": ok,
            "note": None if ok else "Ephemeral disk — set OB_VERSION env var on Render to persist",
            **CREDIT
        })
    except Exception:
        return jsonify({"success": False, "error": "Bad version format",
                        "current": v, **CREDIT})


@app.get("/version")
def version_check():
    return jsonify({"ReleaseVersion": get_version(), **CREDIT})


@app.get("/health")
def health():
    """Render health check endpoint."""
    return jsonify({"status": "ok", "version": get_version()}), 200


@app.get("/")
def index():
    return jsonify({
        "name":    "KAWSARx64 JWT API",
        "version": get_version(),
        "routes":  {
            "/token":     "GET ?uid=&password=",
            "/KAWSARx64": "GET/POST ?uid=&password=",
            "/update+":   "Increment OB version",
            "/update-":   "Decrement OB version",
            "/version":   "Current OB version",
            "/health":    "Health check",
        },
        **CREDIT,
    })


# ============================================================
# MAIN (local dev only — Render uses gunicorn)
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8789))
    log.info(f"✅ KAWSARx64 JWT API running on port {port}")
    log.info(f"📌 Version: {get_version()}")
    app.run(host="0.0.0.0", port=port, debug=False)