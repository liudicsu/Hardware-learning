"""List the topics in m4_gazebo's bridge.yaml by direction, for the gazebo-sim bridge diagram (D086).

check_diagrams runs this (the spec's `script`) and requires the diagram's lines in its output, so the drawn topic
lists, their order and the type pairs named in the caption all come from the file ros_gz_bridge actually loads.
Standard library only: bridge.yaml is a flat list of "- key: value" entries.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRIDGE = os.path.join(ROOT, "examples", "month-4", "gazebo-sim", "m4_gazebo", "config", "bridge.yaml")


def entries():
    out, cur = [], None
    with open(BRIDGE) as f:
        for raw in f:
            line = raw.split("#", 1)[0].rstrip()
            if not line:
                continue
            if line.startswith("- "):
                cur = {}
                out.append(cur)
                line = line[2:]
            key, _, value = line.strip().partition(":")
            cur[key.strip()] = value.strip()
    return out


def main():
    es = entries()
    print(f"{len(es)} bridged topics")
    for d in ("GZ_TO_ROS", "ROS_TO_GZ"):
        print(f"{d}: " + ", ".join(e["ros_topic_name"] for e in es if e["direction"] == d))
    print("same name on both sides: " + ("yes" if all(e["ros_topic_name"] == e["gz_topic_name"] for e in es) else "no"))
    for e in es:
        ros, gz = e["ros_type_name"].split("/")[-1], e["gz_type_name"].split(".")[-1]
        if ros != gz:
            print(f"type differs: {e['ros_topic_name']} {e['ros_type_name']} {'<-' if e['direction'] == 'GZ_TO_ROS' else '->'} {e['gz_type_name']}")


if __name__ == "__main__":
    main()
