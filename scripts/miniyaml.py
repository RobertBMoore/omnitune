"""miniyaml — a tiny, dependency-free parser for the omnitune.config.yaml SUBSET.

Supports: nested maps (indent-based), scalar strings (quoted/unquoted/empty),
block lists of maps (`- key: val` + indented keys), and inline flow lists
(`["a", "b"]`). It does NOT support anchors, multiline scalars, or flow maps.
The omnitune.config schema is documented to stay within this subset so the lint can
run with zero dependencies (PyYAML not required).
"""


def _strip_inline_comment(s):
    out = []
    q = None
    depth = 0
    for i, c in enumerate(s):
        if q:
            out.append(c)
            if c == q:
                q = None
        elif c in ('"', "'"):
            q = c
            out.append(c)
        elif c in "[{":
            depth += 1
            out.append(c)
        elif c in "]}":
            depth = max(0, depth - 1)
            out.append(c)
        elif c == "#" and depth == 0 and (i == 0 or s[i - 1] == " "):
            break
        else:
            out.append(c)
    return "".join(out).rstrip()


def _flow_list(v):
    v = v.strip()
    assert v[0] == "[" and v[-1] == "]", v
    inner = v[1:-1].strip()
    if not inner:
        return []
    items = []
    cur = ""
    q = None
    for c in inner:
        if q:
            cur += c
            if c == q:
                q = None
        elif c in ('"', "'"):
            q = c
            cur += c
        elif c == ",":
            items.append(cur)
            cur = ""
        else:
            cur += c
    if cur.strip() != "":
        items.append(cur)
    return [_scalar(x) for x in items]


def _scalar(v):
    v = v.strip()
    if v == "":
        return ""
    if len(v) >= 2 and ((v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'")):
        return v[1:-1]
    if v.startswith("["):
        return _flow_list(v)
    return v


def load(text):
    toks = []
    for raw in text.split("\n"):
        line = _strip_inline_comment(raw)
        if line.strip() == "":
            continue
        indent = len(line) - len(line.lstrip(" "))
        toks.append((indent, line.strip()))
    pos = [0]

    def parse_block():
        indent, content = toks[pos[0]]
        if content.startswith("- "):
            return parse_list(indent)
        return parse_map(indent)

    def parse_map(indent):
        d = {}
        while pos[0] < len(toks):
            ind, content = toks[pos[0]]
            if ind != indent or content.startswith("- "):
                break
            key, _, rest = content.partition(":")
            key = key.strip()
            rest = rest.strip()
            pos[0] += 1
            if rest == "":
                if pos[0] < len(toks) and toks[pos[0]][0] > indent:
                    d[key] = parse_block()
                else:
                    d[key] = ""
            else:
                d[key] = _scalar(rest)
        return d

    def parse_list(indent):
        items = []
        while pos[0] < len(toks):
            ind, content = toks[pos[0]]
            if ind != indent or not content.startswith("- "):
                break
            item = content[2:].strip()
            pos[0] += 1
            if ":" in item:
                key, _, rest = item.partition(":")
                m = {key.strip(): _scalar(rest.strip())}
                while (pos[0] < len(toks) and toks[pos[0]][0] > indent
                       and not toks[pos[0]][1].startswith("- ")):
                    k2, _, r2 = toks[pos[0]][1].partition(":")
                    pos[0] += 1
                    m[k2.strip()] = _scalar(r2.strip())
                items.append(m)
            else:
                items.append(_scalar(item))
        return items

    if not toks:
        return {}
    return parse_block()
