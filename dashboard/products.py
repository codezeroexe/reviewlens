"""Product names for display. The dataset's product_id is an opaque code; product_title says what it is.

IDs stay the key everywhere (filters, links, reports). Names are only for showing people.
"""

import pandas as pd

MAX_WIDTH = 70


class Names:
    def __init__(self, df: pd.DataFrame | None = None):
        self.titles: dict[str, str] = {}
        self.shared: set[str] = set()  # titles used by more than one id (e.g. colour variants)
        if df is not None and "product_id" in df and "product_title" in df:
            first = df.dropna(subset=["product_title"]).drop_duplicates("product_id")
            self.titles = dict(zip(first["product_id"].astype(str), first["product_title"].astype(str).str.strip()))
            counts = pd.Series(list(self.titles.values())).value_counts()
            self.shared = set(counts[counts > 1].index)

    def label(self, product_id) -> str:
        """Short product name; the id is added only when two products share a name. Unknown id: the id itself."""
        pid = str(product_id)
        title = self.titles.get(pid)
        if not title:
            return pid
        short = title if len(title) <= MAX_WIDTH else title[:MAX_WIDTH - 1].rstrip() + "…"
        return f"{short} ({pid})" if title in self.shared else short

    def for_ids(self, ids) -> dict[str, str]:
        return {str(i): self.label(i) for i in set(ids) if str(i) in self.titles}


if __name__ == "__main__":
    demo = pd.DataFrame({"product_id": ["A", "B", "C"], "product_title": ["Same", "Same", "x" * 90]})
    n = Names(demo)
    assert n.label("A") == "Same (A)" and n.label("B") == "Same (B)"
    assert n.label("C").endswith("…") and len(n.label("C")) == MAX_WIDTH
    assert n.label("Z") == "Z" and n.for_ids(["A", "Z"]) == {"A": "Same (A)"}
    print("products self-check OK")
