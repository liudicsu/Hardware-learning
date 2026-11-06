#!/usr/bin/env python3
"""Synthetic exhaustive ACL table, NOT DDS, authentication or encryption.
The same domain/topic/principal requests and intended grants feed every arm.
Material presence stands for pre-provisioned identity, NOT a verified signature.
Enforce missing-material denial is an initialization failure in real ROS;
we count its would-be receive requests as denied, without starting any node.
"""
from collections import Counter
from itertools import product

DOMAIN = 7
TOPICS = ("/scan", "/cmd_vel", "/debug")
GRANTS = {"listener": {"/scan"}, "operator": {"/scan", "/cmd_vel"},
          "visitor": set(), "unknown": set()}
MATERIALS = {"listener", "operator", "visitor"}
REQUESTS = tuple(product((7, 8), GRANTS, TOPICS))
ARMS = ("domain_only", "missing_enclave_Enforce", "enclave_ACL_Enforce")


def decision(arm, domain, principal, topic):
    if arm not in ARMS:
        raise ValueError(arm)
    if domain != DOMAIN:
        return False, "other_domain"
    if arm == "domain_only":
        return True, "domain_only"
    if arm == "missing_enclave_Enforce" or principal not in MATERIALS:
        return False, "missing_materials"
    if topic not in GRANTS[principal]:
        return False, "policy_deny"
    return True, "allow"


def evaluate(arm, requests=REQUESTS):
    counts = Counter()
    for domain, principal, topic in requests:
        intended = domain == DOMAIN and topic in GRANTS[principal]
        received, reason = decision(arm, domain, principal, topic)
        counts[reason] += 1
        counts["received"] += received
        counts["unauthorized_receive"] += received and not intended
        counts["legitimate_denied"] += intended and not received
    return counts


def main():
    print("Synthetic exhaustive ACL: 24 shared requests; same_domain=12; intended_allowed=3")
    print("arm received unauthorized_receive legitimate_denied other_domain missing_materials policy_deny")
    for arm in ARMS:
        c = evaluate(arm)
        keys = ("received", "unauthorized_receive", "legitimate_denied",
                "other_domain", "missing_materials", "policy_deny")
        print(arm, *(c[k] for k in keys))
    print("Enforce: valid visitor still denied; unknown has no materials; /debug is never granted.")
    print("DOMAIN_ID is not security; missing enclave blocks initialization, not a packet filter.")
    print("No crypto, DDS handshake, QoS or lifecycle simulation; no certification claim.")


if __name__ == "__main__":
    main()
