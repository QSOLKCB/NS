# SPDX-License-Identifier: Apache-2.0
"""Hardened compatibility layer for candidate-transform validation primitives."""
from __future__ import annotations
import re
from typing import Any
from .transform_common_base import *
from .transform_common_base import FORBIDDEN_AUTHORITY, SAFE_ID, TransformError

_SOLVED_WORD=re.compile(r"\bsolved\b",re.IGNORECASE)

def text(value:Any,field:str)->str:
    if not isinstance(value,str) or not value.strip(): raise TransformError(f"{field} must be a non-empty string")
    try:value.encode("utf-8","strict")
    except UnicodeEncodeError as exc: raise TransformError(f"{field} must be valid UTF-8 without lone surrogates") from exc
    return value

def safe_id(value:Any,field:str)->str:
    text(value,field)
    if not SAFE_ID.fullmatch(value): raise TransformError(f"{field} must be a component-safe ID of at most 128 characters")
    return value

def unique_text(values:tuple[str,...],field:str,nonempty:bool=False)->None:
    if nonempty and not values: raise TransformError(f"{field} must be non-empty")
    for value in values:text(value,field)
    if len(values)!=len(set(values)): raise TransformError(f"{field} must contain unique values")

def contains_authority(text_value:str)->bool:
    lower=text_value.lower()
    return any(phrase in lower for phrase in FORBIDDEN_AUTHORITY) or _SOLVED_WORD.search(text_value) is not None
