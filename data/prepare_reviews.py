#!/usr/bin/env python3
import json, random, pathlib, re, html

RANDOM_SEED = 42
SPLIT = (0.8, 0.1, 0.1)  # train/val/test
BASE_IN = pathlib.Path("data/raw")       # kök dizinden çalıştır
BASE_OUT = pathlib.Path("data/processed")
LABEL_MAP = {"negative": 0, "positive": 1}

random.seed(RANDOM_SEED)

def is_domain_dir(d: pathlib.Path) -> bool:
    return d.is_dir() and (d/"positive.review").exists() and (d/"negative.review").exists()

def extract_review_texts(path: pathlib.Path):
    """<review_text> ... </review_text> bloklarını al, temizle ve döndür."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # review_text içeriklerini yakala (çok satırlı olabilir)
    raw_texts = re.findall(r"<review_text>\s*(.*?)\s*</review_text>", content, flags=re.DOTALL|re.IGNORECASE)

    cleaned = []
    for t in raw_texts:
        t = html.unescape(t)                 # HTML kaçışlarını çöz (&amp; -> &)
        t = re.sub(r"<[^>]+>", " ", t)       # kalmış olası etiketleri sil
        t = re.sub(r"\s+", " ", t).strip()   # boşlukları sadeleştir
        if len(t) >= 5:                      # çok kısa/boş parçaları ele
            cleaned.append(t)
    return cleaned

def stratified_split(items, ratios=(0.8, 0.1, 0.1)):
    items = items[:]
    random.shuffle(items)
    n = len(items)
    n_train = int(n * ratios[0])
    n_val = int(n * ratios[1])
    return items[:n_train], items[n_train:n_train+n_val], items[n_train+n_val:]

def write_jsonl(path: pathlib.Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def main():
    domains = sorted([d.name for d in BASE_IN.iterdir() if is_domain_dir(d)])
    global_train, global_val, global_test = [], [], []

    for dom in domains:
        dpath = BASE_IN / dom
        rows = []
        for lab_name, lab_id in LABEL_MAP.items():
            texts = extract_review_texts(dpath / f"{lab_name}.review")
            for i, t in enumerate(texts):
                rows.append({
                    "id": f"{dom}-{lab_name}-{i}",
                    "domain": dom,
                    "label": lab_id,
                    "text": t
                })

        # sınıf dengesi korunarak böl
        by_label = {lid: [] for lid in LABEL_MAP.values()}
        for r in rows: by_label[r["label"]].append(r)

        dom_train, dom_val, dom_test = [], [], []
        for lid, lst in by_label.items():
            tr, va, te = stratified_split(lst, SPLIT)
            dom_train += tr; dom_val += va; dom_test += te

        for lst in (dom_train, dom_val, dom_test): random.shuffle(lst)

        # domain bazında yaz
        out_d = BASE_OUT / "by_domain" / dom
        write_jsonl(out_d / "train.jsonl", dom_train)
        write_jsonl(out_d / "val.jsonl", dom_val)
        write_jsonl(out_d / "test.jsonl", dom_test)

        global_train += dom_train; global_val += dom_val; global_test += dom_test

    write_jsonl(BASE_OUT / "global" / "train.jsonl", global_train)
    write_jsonl(BASE_OUT / "global" / "val.jsonl", global_val)
    write_jsonl(BASE_OUT / "global" / "test.jsonl", global_test)

    # özet
    from collections import Counter
    def c(rows, key): return dict(Counter([r[key] for r in rows]))
    print("Domains:", domains)
    print("Global train:", len(global_train), c(global_train, "domain"), c(global_train, "label"))
    print("Global val  :", len(global_val),   c(global_val, "domain"), c(global_val, "label"))
    print("Global test :", len(global_test),  c(global_test, "domain"), c(global_test, "label"))

if __name__ == "__main__":
    main()

