# -*- coding: utf-8 -*-
# MajorLoginRes_pb2.py — generated for MajorLoginRes.proto
# Descriptor built at import time (no protoc needed).
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pb2 as _descriptor_pb2
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

# --------------------------------------------------------------------
# (optional) runtime version check — tolerant across protobuf versions
# --------------------------------------------------------------------
try:
    from google.protobuf import runtime_version as _runtime_version
    _runtime_version.ValidateProtobufRuntimeVersion(
        _runtime_version.Domain.PUBLIC, 6, 30, 0, "", "MajorLoginRes.proto"
    )
except Exception:
    pass

_sym_db = _symbol_database.Default()

# --------------------------------------------------------------------
# Build FileDescriptorProto for MajorLoginRes.proto
# --------------------------------------------------------------------
_fdp               = _descriptor_pb2.FileDescriptorProto()
_fdp.name          = "MajorLoginRes.proto"
_fdp.package       = ""
_fdp.syntax        = "proto3"

_main              = _fdp.message_type.add()
_main.name         = "MajorLoginRes"


def _f(msg, name, num, ftype, label=1, type_name="", json_name=""):
    """Append a FieldDescriptorProto to msg."""
    fd = msg.field.add()
    fd.name   = name
    fd.number = num
    fd.label  = label          # 1 = LABEL_OPTIONAL (proto3 always optional)
    fd.type   = ftype          # see FieldDescriptorProto.Type enum
    if type_name:
        fd.type_name = type_name
    if json_name:
        fd.json_name = json_name
    return fd


# ── Main message fields ──────────────────────────────────────────────
# Wire-type reference:
#   3  = TYPE_INT64
#   5  = TYPE_INT32
#   8  = TYPE_BOOL
#   9  = TYPE_STRING
#   11 = TYPE_MESSAGE
#   12 = TYPE_BYTES
_f(_main, "account_id",        1, 3)
_f(_main, "lock_region",       2, 9)
_f(_main, "noti_region",       3, 9)
_f(_main, "ip_region",         4, 9)
_f(_main, "agora_environment", 5, 9)
_f(_main, "new_active_region", 6, 9)
_f(_main, "token",             8, 9)
_f(_main, "ttl",               9, 5)
_f(_main, "server_url",       10, 9)
_f(_main, "emulator_score",   12, 3)
_f(_main, "blacklist",        13, 11, type_name=".MajorLoginRes.BlacklistInfoRes")
_f(_main, "queue_info",       15, 11, type_name=".MajorLoginRes.LoginQueueInfo")
_f(_main, "tp_url",           16, 9)
_f(_main, "app_server_id",    17, 3)
_f(_main, "ano_url",          18, 9)
_f(_main, "ip_city",          19, 9)
_f(_main, "ip_subdivision",   20, 9)
_f(_main, "kts",              21, 3)
_f(_main, "ak",               22, 12)
_f(_main, "aiv",              23, 12)
_f(_main, "tp_url_2",         24, 9)
_f(_main, "aux",              25, 11, type_name=".MajorLoginRes.AuxInfo")
_f(_main, "auth",             27, 12)

# ── Nested: BlacklistInfoRes ─────────────────────────────────────────
_bl = _main.nested_type.add()
_bl.name = "BlacklistInfoRes"
_f(_bl, "ban_reason",      1, 5)
_f(_bl, "expire_duration", 2, 3)
_f(_bl, "ban_time",        3, 3)

# ── Nested: LoginQueueInfo ───────────────────────────────────────────
_q = _main.nested_type.add()
_q.name = "LoginQueueInfo"
_f(_q, "allow",           1, 8)
_f(_q, "queue_position",  2, 3)
_f(_q, "need_wait_secs",  3, 3)
_f(_q, "queue_is_full",   4, 8)

# ── Nested: AuxInfo ──────────────────────────────────────────────────
_a = _main.nested_type.add()
_a.name = "AuxInfo"
_f(_a, "region", 1, 9)
_f(_a, "f2",     2, 5)
_f(_a, "f3",     3, 5)
_f(_a, "f4",     4, 5)
_f(_a, "f5",     5, 5)
_f(_a, "f6",     6, 5)
_f(_a, "f7",     7, 5)

# --------------------------------------------------------------------
# Register descriptor
# --------------------------------------------------------------------
_serialized = _fdp.SerializeToString()
DESCRIPTOR  = _descriptor_pool.Default().AddSerializedFile(_serialized)

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(
    DESCRIPTOR, "MajoRLoGinrEs_pb2", _globals
)

# --------------------------------------------------------------------
# Debug offsets (optional, mirror of protoc output)
# --------------------------------------------------------------------
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None

# @@protoc_insertion_point(module_scope)