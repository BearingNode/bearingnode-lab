#!/usr/bin/env python3
"""Build the published figure by inlining its binary assets.

    python3 artefacts/build.py

`src/*.template.html` is the hand-maintained source. This injects the two things
that cannot live in a text file:

* **The font.** Roboto, Latin subset, single variable woff2, base64 as a `data:`
  URI. It has to be embedded rather than linked because the Wix HTML element
  renders in a sandboxed iframe with no `allow-same-origin`, where a fetch for an
  externally-hosted font fails. A `data:` URI needs no fetch and no origin.
* **The logo.** The official BearingNode asset, vendored into `logos/` so the
  build has no dependency on the private `branding` submodule (RAID I05,
  `public-lab` register). Its paths are styled by a CSS class in a
  `<defs><style>` block; inlined into another document that class leaks and
  non-browser renderers drop it, so the fill is promoted onto each path.
  Geometry untouched.

Output is a single self-contained file: no external requests at all, which is
asserted by `checks.js`.
"""
from __future__ import annotations

import base64
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONT = HERE / "fonts" / "Roboto-latin-variable.woff2"
LOGO = HERE / "logos" / "Logomark_horisontal_dark.svg"

BUILDS = [
    ("src/framework-entry.template.html", "bearingnode-mcp-lineage-framework-entry.html", None),
    ("src/signal-scope.template.html", "bearingnode-mcp-lineage-signal-scope.html", "src/signal-scope.data.js"),
    ("src/call-chain.template.html", "bearingnode-mcp-lineage-call-chain.html", None),
]


def logo_svg() -> str:
    """The official logomark as a standalone, self-contained <svg>."""
    raw = LOGO.read_text(encoding="utf-8")
    view_box = re.search(r'viewBox="([\d.\s-]+)"', raw).group(1)
    fill = re.search(r"fill:\s*(#[0-9a-fA-F]{3,6})", raw).group(1)

    body = re.sub(r"<defs>.*?</defs>", "", raw, flags=re.S)
    body = re.sub(r"^.*?<svg[^>]*>", "", body, flags=re.S).replace("</svg>", "")
    body = body.replace('class="cls-1"', f'fill="{fill}"')
    body = re.sub(r"\n\s*\n", "\n", body).strip()

    if "cls-" in body or "<style" in body:
        raise SystemExit("logo: a class or style block survived inlining")

    return f'<svg viewBox="{view_box}" role="img" aria-label="BearingNode">{body}</svg>'


def third_party_logo(filename: str, label: str) -> str:
    """Inline a third-party project mark without letting its stylesheet escape.

    Both marks ship a `<style>` block. OpenLineage's carries `.cls-N { fill: … }`
    rules; OpenTelemetry's carries a bare `svg { … }` selector that would apply to
    every other SVG in the host document. Class rules are promoted onto the paths
    and the block is dropped. Geometry and colour are untouched — these are other
    people's trademarks and are used unmodified.
    """
    raw = (HERE / "logos" / filename).read_text(encoding="utf-8")

    style = re.search(r"<style[^>]*>(.*?)</style>", raw, flags=re.S)
    if style:
        for cls, fill in re.findall(r"\.([\w-]+)\s*\{\s*fill:\s*(#[0-9a-fA-F]{3,6})\s*;?\s*\}", style.group(1)):
            raw = raw.replace(f'class="{cls}"', f'fill="{fill}"')
        raw = re.sub(r"<style[^>]*>.*?</style>", "", raw, flags=re.S)

    raw = re.sub(r"<\?xml[^>]*\?>", "", raw)
    raw = re.sub(r"<!DOCTYPE[^>]*>", "", raw, flags=re.I)
    raw = re.sub(r'\sid="[^"]*"', "", raw)          # ids would collide once inlined
    raw = re.sub(r'\sclass="[^"]*"', "", raw)       # any class that survived has no rule left

    view_box = re.search(r'viewBox="([\d.\s-]+)"', raw).group(1)
    body = re.sub(r"^.*?<svg[^>]*>", "", raw, flags=re.S).replace("</svg>", "").strip()

    if "<style" in body or "class=" in body:
        raise SystemExit(f"{filename}: a style or class survived inlining")

    return f'<svg viewBox="{view_box}" role="img" aria-label="{label}">{body}</svg>'


def main() -> None:
    font_b64 = base64.b64encode(FONT.read_bytes()).decode()
    logo = logo_svg()
    print(f"font  {FONT.name}: {FONT.stat().st_size:,} bytes -> {len(font_b64):,} base64 chars")
    print(f"logo  {LOGO.name}: {logo.count('<path')} paths")

    for src_name, out_name, data_name in BUILDS:
        template = (HERE / src_name).read_text(encoding="utf-8")
        for token in ("__ROBOTO_B64__", "__LOGO_SVG__"):
            if token not in template:
                raise SystemExit(f"{src_name}: missing {token}")

        out = template.replace("__ROBOTO_B64__", font_b64).replace("__LOGO_SVG__", logo)

        if "__OTEL_LOGO__" in out or "__OL_LOGO__" in out:
            out = out.replace("__OTEL_LOGO__", third_party_logo("opentelemetry-horizontal-color.svg", "OpenTelemetry"))
            out = out.replace("__OL_LOGO__", third_party_logo("openlineage-horizontal-color.svg", "OpenLineage"))
            print("logos inlined: OpenTelemetry (CNCF), OpenLineage (LF AI & Data) — unmodified")

        if data_name:
            # The content lives in its own module so it can be edited against the
            # primary sources it cites. Inlined here, since the figure must be a
            # single self-contained file with no fetches.
            data = (HERE / data_name).read_text(encoding="utf-8")
            data = re.sub(r"^export const ", "const ", data, flags=re.M)
            if "export " in data:
                raise SystemExit(f"{data_name}: an export survived inlining")
            out = out.replace("__DATA__", data)
            print(f"data  {data_name}: {data.count('{ id:')} items")
        elif "__DATA__" in out:
            raise SystemExit(f"{src_name}: has __DATA__ but no data file configured")

        (HERE / out_name).write_text(out, encoding="utf-8")
        print(f"built {out_name}: {len(out):,} bytes")


if __name__ == "__main__":
    main()
