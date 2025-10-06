#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, json, glob
import xml.etree.ElementTree as ET

NS    = {"tei": "http://www.tei-c.org/ns/1.0"}
XMLNS = "{http://www.w3.org/XML/1998/namespace}"

def text_of(el):
    return (el.text or "").strip() if el is not None else ""

def deep_text(el):
    if el is None:
        return ""
    parts = []
    if el.text:
        parts.append(el.text)
    for c in list(el):
        parts.append(deep_text(c))
        if c.tail:
            parts.append(c.tail)
    return "".join(parts)

def get_metadata(root):
    od = root.find(".//tei:history/tei:origin/tei:origDate", NS)
    date_text = text_of(od)
    date_nb   = od.get("notBefore-custom") if od is not None else ""
    date_na   = od.get("notAfter-custom")  if od is not None else ""
    anc, mod = [], []
    for pn in root.findall(".//tei:history/tei:origin/tei:origPlace/tei:placeName", NS):
        t = (pn.get("type") or "").lower()
        if t == "ancient": anc.append(text_of(pn))
        if t == "modern":  mod.append(text_of(pn))
    return date_text, (date_nb or ""), (date_na or ""), "; ".join(anc), "; ".join(mod)

def get_translations(root):
    translations = {}
    for div in root.findall(".//tei:div[@type='translation']", NS):
        lang = div.get(XMLNS + "lang") or ""
        ps   = [text_of(p) for p in div.findall(".//tei:p", NS)]
        content = "\n".join([p for p in ps if p])
        if content.strip():
            translations[lang] = content
    return translations

def get_commentary(root):
    out = []
    for div in root.findall(".//tei:div[@type='commentary']", NS):
        lang = div.get(XMLNS + "lang") or ""
        resp = div.get("resp") or ""
        for note in div.findall(".//tei:note", NS):
            n_resp = note.get("resp") or resp
            target = note.get("target") or ""
            ps = note.findall(".//tei:p", NS)
            if ps:
                text = "\n".join(deep_text(p).strip() for p in ps if deep_text(p).strip())
            else:
                text = deep_text(note).strip()
            out.append({
                "target": target,
                "lang": lang,
                "resp": n_resp,
                "text": text
            })
    return out

# ---- RENDERERS ----

def render_diplomatic(n):
    out = []
    if n.text: out.append(n.text)
    for c in list(n):
        tag = c.tag.split('}')[-1] if isinstance(c.tag, str) else None
        if tag == "lb":
            out.append("\n")
        elif tag in ("w","num","pc"):
            out.append(c.text or "")
        elif tag == "unclear":
            out.append(c.text or "")
        elif tag == "gap":
            qty    = c.attrib.get("quantity")
            extent = c.attrib.get("extent")
            reason = c.attrib.get("reason")
            if qty:
                out.append(f"[gap:{reason}:{qty}]")
            elif extent:
                out.append(f"[gap:{reason}:{extent}]")
            else:
                out.append(f"[gap:{reason}]")
        else:
            out.append(render_diplomatic(c))
        if c.tail: out.append(c.tail)
    return "".join(out)

def render_plain(n):
    out = []
    if n.text: out.append(n.text)
    for c in list(n):
        tag = c.tag.split('}')[-1] if isinstance(c.tag, str) else None
        if tag == "lb":
            out.append("\n")
        elif tag in ("w","num","pc"):
            out.append(c.text or "")
        elif tag == "unclear":
            out.append("?")
        elif tag == "gap":
            qty    = c.attrib.get("quantity")
            extent = (c.attrib.get("extent") or "").lower()
            if qty and qty.isdigit():
                out.append("?" * int(qty))
            elif extent == "unknown" or not qty:
                out.append("#")
        else:
            out.append(render_plain(c))
        if c.tail: out.append(c.tail)
    return "".join(out)

def render_reconstruction(n):
    out = []
    if n.text: out.append(n.text)
    for c in list(n):
        tag = c.tag.split('}')[-1] if isinstance(c.tag, str) else None
        if tag == "lb":
            out.append("\n")
        elif tag in ("w","num","pc"):
            out.append(c.text or "")
        elif tag == "unclear":
            out.append(c.text or "")
        elif tag == "supplied":
            out.append(c.text or "")
        elif tag == "choice":
            expan = c.find(".//tei:expan", NS)
            if expan is not None and text_of(expan):
                out.append(text_of(expan))
            else:
                out.append(render_reconstruction(c))
        elif tag == "gap":
            qty    = c.attrib.get("quantity")
            extent = (c.attrib.get("extent") or "").lower()
            if qty and qty.isdigit():
                out.append("?" * int(qty))
            elif extent == "unknown" or not qty:
                out.append("#")
        else:
            out.append(render_reconstruction(c))
        if c.tail: out.append(c.tail)
    return "".join(out)

# ---- MAIN ----

def extract_record(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    xml_id = root.attrib.get(XMLNS + "id", os.path.basename(xml_path))

    date_text, date_nb, date_na, place_anc, place_mod = get_metadata(root)
    translations = get_translations(root)
    commentary   = get_commentary(root)

    ab_nodes = root.findall(".//tei:div[@type='edition']//tei:ab", NS)
    diplomatic, plain, reconstruction = [], [], []
    for ab in ab_nodes:
        diplomatic.append(     render_diplomatic(ab).strip() )
        plain.append(          render_plain(ab).strip() )
        reconstruction.append( render_reconstruction(ab).strip() )

    return {
        "xml_id": xml_id,
        "date_text": date_text,
        "date_notBefore": date_nb,
        "date_notAfter": date_na,
        "place_ancient": place_anc,
        "place_modern": place_mod,
        "diplomatic": diplomatic,
        "reconstruction": reconstruction,
        "plain": plain,
        "translations": translations,
        "commentary": commentary,
        "source_xml": os.path.basename(xml_path)
    }

def main():
    # Only look in current folder, no recursion
    xml_paths = sorted(glob.glob("*.xml"))
    if not xml_paths:
        print("No XML files found in current folder.")
        return

    records = []
    for i, p in enumerate(xml_paths, 1):
        try:
            rec = extract_record(p)
            records.append(rec)
        except Exception as e:
            print(f"[WARN] Skipping {p}: {e}")

    # Always fixed output names
    with open("ItAnt_Faliscan.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Wrote ItAnt_Faliscan.json ({len(records)} records)")

    with open("ItAnt_Faliscan.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote ItAnt_Faliscan.jsonl ({len(records)} lines)")

if __name__ == "__main__":
    main()


