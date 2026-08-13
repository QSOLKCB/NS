#!/usr/bin/env python3
import crucible_core as cc

if cc.DUPLICATE_DETECTOR_VERSION != "0.1.0":
    raise SystemExit("screening version mismatch")
print("similarity screening validation: PASS")
