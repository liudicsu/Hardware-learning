"""stl_info.py: check an exported STL before you slice it.

Prints the bounding box, the triangle count, whether every edge is shared by exactly two
triangles (a "watertight" mesh that slicers can fill), the volume, and the mass of a solid
print. Reads ASCII or binary STL. No packages needed.
Usage: python3 stl_info.py part.stl [density g/cm^3, default 1.24 for PLA]
"""
import struct
import sys
from collections import Counter


def load(path):
    data = open(path, "rb").read()
    if data[:5] == b"solid" and b"facet" in data[:400]:          # ASCII STL
        nums = [tuple(map(float, line.split()[1:4]))
                for line in data.decode().splitlines() if line.strip().startswith("vertex")]
        return [nums[i:i + 3] for i in range(0, len(nums), 3)]
    (count,) = struct.unpack_from("<I", data, 80)                 # binary STL
    tris = []
    for i in range(count):
        v = struct.unpack_from("<12f", data, 84 + 50 * i)
        tris.append([v[3:6], v[6:9], v[9:12]])
    return tris


def volume(tris):
    """Sum of signed tetrahedra from the origin: exact for a closed mesh."""
    total = 0.0
    for a, b, c in tris:
        total += (a[0] * (b[1] * c[2] - b[2] * c[1])
                  - a[1] * (b[0] * c[2] - b[2] * c[0])
                  + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
    return abs(total)


def main():
    path = sys.argv[1]
    density = float(sys.argv[2]) if len(sys.argv) > 2 else 1.24
    tris = load(path)
    pts = [p for t in tris for p in t]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    edges = Counter()
    for t in tris:
        for i in range(3):
            edges[tuple(sorted((t[i], t[(i + 1) % 3])))] += 1
    open_edges = sum(1 for n in edges.values() if n != 2)
    vol = volume(tris) / 1000.0                                   # mm^3 -> cm^3
    print(f"size: {hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2] - lo[2]:.1f} mm")
    print(f"triangles: {len(tris)}, edges not shared by exactly 2: {open_edges}"
          + ("  (watertight)" if open_edges == 0 else "  (NOT watertight: fix before slicing)"))
    print(f"volume: {vol:.2f} cm^3, solid mass at {density} g/cm^3: {vol * density:.1f} g")


if __name__ == "__main__":
    main()
