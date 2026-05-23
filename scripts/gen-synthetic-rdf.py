#!/usr/bin/env python3
"""
Generate synthetic RDF data for the v2 SHACL shapes.

Produces two files in --out-dir:
  - synthetic-valid.ttl    : N Tours, all constraints satisfied
  - synthetic-invalid.ttl  : M Tours, each carrying exactly one violation
                              of a known shape constraint

Validate with:
  pyshacl -s ontology/v2/shapes.ttl -d <file>.ttl -f human

Stdlib only.
"""
from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

PREFIXES = """\
@prefix ph:      <https://pedalhidrografi.co/censo/1.0/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix prov:    <http://www.w3.org/ns/prov#> .
@prefix schema:  <https://schema.org/> .
@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .
@prefix id:      <https://pedalhidrografi.co/id/> .

"""

LICENSES = [
    "<https://creativecommons.org/licenses/by-sa/4.0/>",
    "<https://creativecommons.org/licenses/by/4.0/>",
    "<https://creativecommons.org/publicdomain/zero/1.0/>",
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def rnd_lat() -> float:
    return round(random.uniform(-23.70, -23.40), 6)


def rnd_lon() -> float:
    return round(random.uniform(-46.80, -46.50), 6)


def rnd_dt(base: datetime, jitter_min: int = 60 * 24 * 30) -> str:
    delta = timedelta(minutes=random.randint(-jitter_min, jitter_min))
    return (base + delta).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# entity builders — each returns a turtle block (string)
# ---------------------------------------------------------------------------

def person(tag: str, name: str) -> tuple[str, str]:
    iri = f"id:person/{tag}"
    block = (
        f"{iri} a schema:Person ;\n"
        f'    schema:name "{name}" .\n'
    )
    return iri, block


def geo(tag: str, lat: float | None = None, lon: float | None = None) -> tuple[str, str]:
    iri = f"id:geo/{tag}"
    lat = rnd_lat() if lat is None else lat
    lon = rnd_lon() if lon is None else lon
    block = (
        f"{iri} a schema:GeoCoordinates ;\n"
        f"    schema:latitude  {lat:.6f}e+0 ;\n"
        f"    schema:longitude {lon:.6f}e+0 .\n"
    )
    return iri, block


def photo(tag: str, author_iri: str, geo_iri: str,
          fov: float | None = None,
          license_iri: str | None = None,
          drop: set[str] | None = None) -> tuple[str, str]:
    drop = drop or set()
    iri = f"id:photo/{tag}"
    fov = round(random.uniform(40, 110), 2) if fov is None else fov
    license_iri = random.choice(LICENSES) if license_iri is None else license_iri
    lines = [f"{iri} a ph:Photo ;"]
    if "location" not in drop:
        lines.append(f"    ph:hasLocation {geo_iri} ;")
    if "fov" not in drop:
        lines.append(f"    ph:fieldOfView {fov} ;")
    if "author" not in drop:
        lines.append(f"    ph:hasAuthor {author_iri} ;")
    if "license" not in drop:
        lines.append(f"    dcterms:license {license_iri} ;")
    block = "\n".join(lines).rstrip(" ;") + " .\n"
    return iri, block


def narrative(tag: str, author_iri: str, content: str | None = None,
              drop: set[str] | None = None) -> tuple[str, str]:
    drop = drop or set()
    iri = f"id:narrative/{tag}"
    content = content if content is not None else f"Texto da narrativa {tag}."
    lines = [f"{iri} a ph:NarrativeText ;"]
    if "content" not in drop:
        lines.append(f'    ph:content "{content}" ;')
    if "author" not in drop:
        lines.append(f"    ph:hasAuthor {author_iri} ;")
    block = "\n".join(lines).rstrip(" ;") + " .\n"
    return iri, block


def ig_stats(tag: str, observed_at: str,
             likes: int | None = None,
             shares: int | None = None,
             reposts: int | None = None,
             drop: set[str] | None = None) -> tuple[str, str]:
    drop = drop or set()
    iri = f"id:igstats/{tag}"
    likes = random.randint(0, 500) if likes is None else likes
    shares = random.randint(0, 50) if shares is None else shares
    reposts = random.randint(0, 10) if reposts is None else reposts
    lines = [f"{iri} a ph:InstagramPostStats ;"]
    if "observedAt" not in drop:
        lines.append(f'    prov:generatedAtTime "{observed_at}"^^xsd:dateTime ;')
    if "likes" not in drop:
        lines.append(f"    ph:likes {likes} ;")
    if "shares" not in drop:
        lines.append(f"    ph:messageShares {shares} ;")
    if "reposts" not in drop:
        lines.append(f"    ph:reposts {reposts} ;")
    block = "\n".join(lines).rstrip(" ;") + " .\n"
    return iri, block


def ig_post(tag: str, narrative_iri: str, stats_iris: list[str],
            url: str | None = None,
            drop: set[str] | None = None) -> tuple[str, str]:
    drop = drop or set()
    iri = f"id:igpost/{tag}"
    url = url if url is not None else f"<https://instagram.com/p/{tag}>"
    lines = [f"{iri} a ph:InstagramPost ;"]
    if "url" not in drop:
        lines.append(f"    schema:url {url} ;")
    if "narrative" not in drop:
        lines.append(f"    ph:hasNarrativeText {narrative_iri} ;")
    if "stats" not in drop and stats_iris:
        joined = " , ".join(stats_iris)
        lines.append(f"    ph:hasInstagramPostStats {joined} ;")
    block = "\n".join(lines).rstrip(" ;") + " .\n"
    return iri, block


def plan_stats(tag: str,
               distance_km: float | None = None,
               ascent_m: float | None = None,
               energy_kj: float | None = None,
               drop: set[str] | None = None) -> tuple[str, str]:
    drop = drop or set()
    iri = f"id:planstats/{tag}"
    distance_km = round(random.uniform(15, 80), 2) if distance_km is None else distance_km
    ascent_m = round(random.uniform(50, 800), 1) if ascent_m is None else ascent_m
    energy_kj = round(random.uniform(800, 4000), 1) if energy_kj is None else energy_kj
    lines = [f"{iri} a ph:PlannedRouteStats ;"]
    if "distance" not in drop:
        lines.append(f"    ph:distanceKm {distance_km} ;")
    if "ascent" not in drop:
        lines.append(f"    ph:ascentMeters {ascent_m} ;")
    if "energy" not in drop:
        lines.append(f"    ph:estimatedMovementEnergyKj {energy_kj} ;")
    block = "\n".join(lines).rstrip(" ;") + " .\n"
    return iri, block


def planned_route(tag: str, author_iri: str, stats_iri: str | None,
                  url: str | None = None,
                  drop: set[str] | None = None) -> tuple[str, str]:
    drop = drop or set()
    iri = f"id:plannedroute/{tag}"
    url = url if url is not None else f"<https://ridewithgps.com/routes/{tag}>"
    lines = [f"{iri} a ph:PlannedRoute ;"]
    if "url" not in drop:
        lines.append(f"    schema:url {url} ;")
    if "author" not in drop:
        lines.append(f"    ph:hasAuthor {author_iri} ;")
    if "stats" not in drop and stats_iri:
        lines.append(f"    ph:hasPlannedRouteStats {stats_iri} ;")
    block = "\n".join(lines).rstrip(" ;") + " .\n"
    return iri, block


def tour(tag: str, plan_iri: str | None, photo_iris: list[str],
         post_iris: list[str]) -> tuple[str, str]:
    iri = f"id:tour/{tag}"
    lines = [f"{iri} a ph:Tour ;"]
    if plan_iri:
        lines.append(f"    ph:hasPlannedRoute {plan_iri} ;")
    if photo_iris:
        lines.append(f"    ph:hasPhoto {' , '.join(photo_iris)} ;")
    if post_iris:
        lines.append(f"    ph:hasInstagramPost {' , '.join(post_iris)} ;")
    block = "\n".join(lines).rstrip(" ;") + " .\n"
    return iri, block


# ---------------------------------------------------------------------------
# valid corpus
# ---------------------------------------------------------------------------

def make_valid_tour(tag: str, base_dt: datetime) -> str:
    blocks: list[str] = []

    p_iri, p_block = person(f"author-{tag}", f"Autor {tag}")
    blocks.append(p_block)

    photo_iris: list[str] = []
    for i in range(random.randint(1, 4)):
        g_iri, g_block = geo(f"{tag}-{i}")
        blocks.append(g_block)
        ph_iri, ph_block = photo(f"{tag}-{i}", p_iri, g_iri)
        blocks.append(ph_block)
        photo_iris.append(ph_iri)

    post_iris: list[str] = []
    if random.random() < 0.7:
        n_iri, n_block = narrative(f"{tag}", p_iri)
        blocks.append(n_block)
        stats_iris: list[str] = []
        for j in range(random.randint(1, 3)):
            obs_at = rnd_dt(base_dt, jitter_min=60 * 24 * 7)
            s_iri, s_block = ig_stats(f"{tag}-{j}", obs_at)
            blocks.append(s_block)
            stats_iris.append(s_iri)
        post_iri, post_block = ig_post(f"{tag}", n_iri, stats_iris)
        blocks.append(post_block)
        post_iris.append(post_iri)

    plan_iri: str | None = None
    if random.random() < 0.8:
        ps_iri, ps_block = plan_stats(f"{tag}")
        blocks.append(ps_block)
        plan_iri, plan_block = planned_route(f"{tag}", p_iri, ps_iri)
        blocks.append(plan_block)

    _, t_block = tour(tag, plan_iri, photo_iris, post_iris)
    blocks.append(t_block)

    return "\n".join(blocks)


# ---------------------------------------------------------------------------
# invalid corpus — one violation per Tour, tag identifies which
# ---------------------------------------------------------------------------

VIOLATIONS = [
    "photo_missing_location",
    "photo_missing_author",
    "photo_missing_license",
    "photo_fov_out_of_range",
    "geo_lat_out_of_range",
    "narrative_empty_content",
    "narrative_missing_author",
    "stats_missing_observed_at",
    "stats_negative_likes",
    "post_missing_url",
    "post_missing_narrative",
    "plan_missing_url",
    "plan_missing_author",
    "plan_distance_zero",
    "plan_negative_ascent",
    "tour_two_planned_routes",
]


def make_invalid_tour(tag: str, kind: str, base_dt: datetime) -> str:
    blocks: list[str] = []
    p_iri, p_block = person(f"author-{tag}", f"Autor {tag}")
    blocks.append(p_block)

    g_iri, g_block = geo(
        f"{tag}-0",
        lat=200.0 if kind == "geo_lat_out_of_range" else None,
    )
    blocks.append(g_block)

    drop_photo: set[str] = set()
    fov_override: float | None = None
    if kind == "photo_missing_location":
        drop_photo.add("location")
    elif kind == "photo_missing_author":
        drop_photo.add("author")
    elif kind == "photo_missing_license":
        drop_photo.add("license")
    elif kind == "photo_fov_out_of_range":
        fov_override = 270.0

    ph_iri, ph_block = photo(
        f"{tag}-0", p_iri, g_iri, fov=fov_override, drop=drop_photo,
    )
    blocks.append(ph_block)

    drop_narr: set[str] = set()
    content_override: str | None = None
    if kind == "narrative_empty_content":
        content_override = ""
    elif kind == "narrative_missing_author":
        drop_narr.add("author")
    n_iri, n_block = narrative(
        f"{tag}", p_iri, content=content_override, drop=drop_narr,
    )
    blocks.append(n_block)

    drop_stats: set[str] = set()
    likes_override: int | None = None
    if kind == "stats_missing_observed_at":
        drop_stats.add("observedAt")
    elif kind == "stats_negative_likes":
        likes_override = -5
    s_iri, s_block = ig_stats(
        f"{tag}-0", rnd_dt(base_dt), likes=likes_override, drop=drop_stats,
    )
    blocks.append(s_block)

    drop_post: set[str] = set()
    if kind == "post_missing_url":
        drop_post.add("url")
    elif kind == "post_missing_narrative":
        drop_post.add("narrative")
    post_iri, post_block = ig_post(f"{tag}", n_iri, [s_iri], drop=drop_post)
    blocks.append(post_block)

    drop_pstats: set[str] = set()
    dist_override: float | None = None
    ascent_override: float | None = None
    if kind == "plan_distance_zero":
        dist_override = 0.0
    elif kind == "plan_negative_ascent":
        ascent_override = -10.0
    ps_iri, ps_block = plan_stats(
        f"{tag}",
        distance_km=dist_override,
        ascent_m=ascent_override,
        drop=drop_pstats,
    )
    blocks.append(ps_block)

    drop_plan: set[str] = set()
    if kind == "plan_missing_url":
        drop_plan.add("url")
    elif kind == "plan_missing_author":
        drop_plan.add("author")
    plan_iri, plan_block = planned_route(
        f"{tag}", p_iri, ps_iri, drop=drop_plan,
    )
    blocks.append(plan_block)

    # tour body — most kinds: standard 1 plan; the two_planned_routes kind
    # produces an extra ph:hasPlannedRoute to violate sh:maxCount 1
    if kind == "tour_two_planned_routes":
        ps2_iri, ps2_block = plan_stats(f"{tag}-extra")
        blocks.append(ps2_block)
        plan2_iri, plan2_block = planned_route(f"{tag}-extra", p_iri, ps2_iri)
        blocks.append(plan2_block)
        t_iri = f"id:tour/{tag}"
        t_block = (
            f"{t_iri} a ph:Tour ;\n"
            f"    ph:hasPlannedRoute {plan_iri} , {plan2_iri} ;\n"
            f"    ph:hasPhoto {ph_iri} ;\n"
            f"    ph:hasInstagramPost {post_iri} .\n"
        )
        blocks.append(t_block)
    else:
        _, t_block = tour(tag, plan_iri, [ph_iri], [post_iri])
        blocks.append(t_block)

    header = f"# violation kind: {kind}\n"
    return header + "\n".join(blocks)


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--valid-count", type=int, default=20)
    ap.add_argument("--invalid-count", type=int, default=len(VIOLATIONS))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "ontology" / "v2",
    )
    args = ap.parse_args()

    random.seed(args.seed)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    base_dt = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)

    valid_path = args.out_dir / "synthetic-valid.ttl"
    invalid_path = args.out_dir / "synthetic-invalid.ttl"

    with valid_path.open("w", encoding="utf-8") as f:
        f.write("# Synthetic — should produce ZERO SHACL violations.\n\n")
        f.write(PREFIXES)
        for i in range(args.valid_count):
            f.write(make_valid_tour(f"v{i:03d}", base_dt))
            f.write("\n")

    with invalid_path.open("w", encoding="utf-8") as f:
        f.write(
            "# Synthetic — each Tour intentionally violates one constraint.\n"
            f"# Violation kinds covered: {len(VIOLATIONS)}\n\n"
        )
        f.write(PREFIXES)
        for i in range(args.invalid_count):
            kind = VIOLATIONS[i % len(VIOLATIONS)]
            f.write(make_invalid_tour(f"i{i:03d}-{kind}", kind, base_dt))
            f.write("\n")

    print(f"wrote {valid_path} ({args.valid_count} tours)")
    print(f"wrote {invalid_path} ({args.invalid_count} tours)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
