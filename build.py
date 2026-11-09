#!/usr/bin/env python3
"""Builds the Beeloc Business legal site from content/<lang>/<doc>.md.

    python3 build.py                 # writes <lang>/*.html, index.html and the legacy pages
    python3 build.py --sync-app DIR  # also copies terms/privacy markdown into the app's
                                     # composeResources/files/legal (DIR), so the app and the
                                     # site always show the same text

No third-party packages: the markdown subset (headings, paragraphs, lists, tables, bold,
blockquotes) is the same one the app's LegalSheet understands.
"""
import html
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
LANGS = ["uz", "ru", "en"]
DOCS = ["terms", "privacy", "payment", "support"]
APP_DOCS = ["terms", "privacy"]

UI = {
    "uz": {
        "html_lang": "uz",
        "brand": "Beeloc Business",
        "tagline": "Huquqiy hujjatlar va yordam",
        "home_title": "Beeloc Business — hujjatlar",
        "home_lead": "Beeloc Business — tadbirkorlar uchun biznes, talabalarga chegirma va ish e'lonlarini joylash ilovasi. Bu yerda ilovadan foydalanish qoidalari, ma'lumotlaringiz qanday himoyalanishi va to'lov tartibi bilan tanishishingiz mumkin.",
        "nav": {"terms": "Foydalanish shartlari", "privacy": "Maxfiylik siyosati", "payment": "To'lov va qaytarish", "support": "Yordam"},
        "desc": {
            "terms": "Ilovadan foydalanish qoidalari, kontentga talablar, javobgarlik.",
            "privacy": "Qanday ma'lumot yig'iladi, qanday himoyalanadi va huquqlaringiz.",
            "payment": "Obuna narxi, to'lov usullari, avtomatik uzaytirish va pulni qaytarish.",
            "support": "Ko'p beriladigan savollar, aloqa va hisobni o'chirish.",
        },
        "toc": "Mundarija",
        "print": "Chop etish / PDF",
        "open": "Ochish",
        "operator": "Operator: YaTT Qo'shshayev Qahhor G'afurovich",
    },
    "ru": {
        "html_lang": "ru",
        "brand": "Beeloc Business",
        "tagline": "Правовые документы и поддержка",
        "home_title": "Beeloc Business — документы",
        "home_lead": "Beeloc Business — приложение для предпринимателей: размещение бизнеса, скидок для студентов и вакансий. Здесь собраны правила использования, сведения о защите ваших данных и порядок оплаты.",
        "nav": {"terms": "Условия использования", "privacy": "Политика конфиденциальности", "payment": "Оплата и возврат", "support": "Поддержка"},
        "desc": {
            "terms": "Правила использования, требования к контенту, ответственность.",
            "privacy": "Какие данные собираются, как защищаются и ваши права.",
            "payment": "Цена подписки, способы оплаты, автопродление и возврат.",
            "support": "Частые вопросы, контакты и удаление аккаунта.",
        },
        "toc": "Содержание",
        "print": "Печать / PDF",
        "open": "Открыть",
        "operator": "Оператор: ИП Qo'shshayev Qahhor G'afurovich",
    },
    "en": {
        "html_lang": "en",
        "brand": "Beeloc Business",
        "tagline": "Legal documents and support",
        "home_title": "Beeloc Business — documents",
        "home_lead": "Beeloc Business is an app for business owners to publish their business, student discounts and job postings. Here you can read the rules for using the app, how your data is protected and how payments work.",
        "nav": {"terms": "Terms of Use", "privacy": "Privacy Policy", "payment": "Payment and Refunds", "support": "Support"},
        "desc": {
            "terms": "Rules for using the app, content requirements, liability.",
            "privacy": "What data we collect, how we protect it and your rights.",
            "payment": "Subscription price, payment methods, auto-renewal and refunds.",
            "support": "FAQ, contact details and account deletion.",
        },
        "toc": "Contents",
        "print": "Print / PDF",
        "open": "Open",
        "operator": "Operator: Sole proprietor Qo'shshayev Qahhor G'afurovich",
    },
}

LANG_LABEL = {"uz": "O'zbekcha", "ru": "Русский", "en": "English"}

# Old URLs already registered in App Store Connect and Play Console: keep them serving full pages.
LEGACY = {"privacy-policy.html": ("en", "privacy"), "support.html": ("en", "support")}


# ---------- markdown ----------

EMAIL = re.compile(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
BOLD = re.compile(r"\*\*(.+?)\*\*")
PLACEHOLDER = re.compile(r"\[([^\]]+)\](?!\()")


def inline(text: str) -> str:
    out = html.escape(text, quote=False)
    out = BOLD.sub(r"<strong>\1</strong>", out)
    out = PLACEHOLDER.sub(r'<mark class="todo">[\1]</mark>', out)
    out = EMAIL.sub(r'<a href="mailto:\1">\1</a>', out)
    return out


def slug(text: str, used: set) -> str:
    base = re.sub(r"[^\w]+", "-", text.lower(), flags=re.UNICODE).strip("-") or "s"
    s, n = base, 2
    while s in used:
        s, n = f"{base}-{n}", n + 1
    used.add(s)
    return s


def render(md: str):
    """Returns (title, body_html, toc[(id, text)])."""
    title, parts, toc, used = "", [], [], set()
    para, items, table = [], [], []

    def flush_para():
        if para:
            parts.append("<p>" + "<br>\n".join(inline(l) for l in para) + "</p>")
            para.clear()

    def flush_list():
        if items:
            parts.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    def flush_table():
        if table:
            rows = [r for r in table if not all(re.fullmatch(r":?-+:?", c) for c in r if c)]
            head, body = rows[0], rows[1:]
            h = "".join(f"<th>{inline(c)}</th>" for c in head)
            b = "".join("<tr>" + "".join(f'<td data-label="{html.escape(head[i] if i < len(head) else "")}">{inline(c)}</td>' for i, c in enumerate(r)) + "</tr>" for r in body)
            parts.append(f'<div class="table"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>')
            table.clear()

    def flush_all():
        flush_para(); flush_list(); flush_table()

    for raw in md.splitlines():
        line = raw.strip()
        if not line:
            flush_all()
        elif line.startswith("# "):
            flush_all(); title = line[2:].strip()
        elif line.startswith("---"):
            flush_all()
        elif line.startswith("### "):
            flush_all()
            parts.append(f'<h3 id="{slug(line[4:], used)}">{inline(line[4:])}</h3>')
        elif line.startswith("## "):
            flush_all()
            hid = slug(line[3:], used)
            toc.append((hid, line[3:]))
            parts.append(f'<h2 id="{hid}">{inline(line[3:])}</h2>')
        elif line.startswith("> "):
            flush_all(); parts.append(f'<p class="note">{inline(line[2:])}</p>')
        elif line.startswith("- "):
            flush_para(); flush_table(); items.append(line[2:])
        elif line.startswith("|"):
            flush_para(); flush_list()
            table.append([c.strip() for c in line.strip("|").split("|")])
        else:
            flush_list(); flush_table(); para.append(line)
    flush_all()
    return title, "\n".join(parts), toc


# ---------- page shell ----------

def page(lang, current, title, body, prefix, alt_paths, description):
    ui = UI[lang]
    cur_page, cur_lang = ' aria-current="page"', ' aria-current="true"'
    nav = "".join(
        f'<a href="{prefix}{lang}/{d}.html"{cur_page if d == current else ""}>{ui["nav"][d]}</a>'
        for d in DOCS
    )
    langs = "".join(
        f'<a href="{prefix}{alt_paths[l]}" lang="{l}"{cur_lang if l == lang else ""}>{l.upper()}</a>'
        for l in LANGS
    )
    hreflang = "".join(f'<link rel="alternate" hreflang="{l}" href="{prefix}{alt_paths[l]}">' for l in LANGS)
    footer_links = " · ".join(f'<a href="{prefix}{lang}/{d}.html">{ui["nav"][d]}</a>' for d in DOCS)
    return f"""<!doctype html>
<html lang="{ui['html_lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<meta name="theme-color" content="#0b1f4d">
{hreflang}
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
<header class="top">
  <div class="wrap bar">
    <a class="brand" href="{prefix}{lang}/index.html"><span class="dot"></span>{ui['brand']}</a>
    <nav class="langs" aria-label="Language">{langs}</nav>
  </div>
  <div class="wrap"><nav class="tabs" aria-label="Documents">{nav}</nav></div>
</header>
<main class="wrap">
{body}
</main>
<footer class="wrap foot">
  <p>{footer_links}</p>
  <p>{ui['operator']} · <a href="mailto:quvonchbekgafurov07@gmail.com">quvonchbekgafurov07@gmail.com</a></p>
  <p>© 2026 Beeloc</p>
</footer>
</body>
</html>
"""


def doc_body(lang, title, body, toc):
    ui = UI[lang]
    toc_html = ""
    if len(toc) > 3:
        toc_html = (f'<details class="toc" open><summary>{ui["toc"]}</summary><ol>'
                    + "".join(f'<li><a href="#{i}">{html.escape(t)}</a></li>' for i, t in toc)
                    + "</ol></details>")
    return (f'<article class="doc"><div class="doc-head"><h1>{html.escape(title)}</h1>'
            f'<button class="print" type="button" onclick="window.print()">{ui["print"]}</button></div>'
            f"{toc_html}{body}</article>")


def home_body(lang):
    ui = UI[lang]
    cards = "".join(
        f'<a class="card" href="{d}.html"><strong>{ui["nav"][d]}</strong><span>{ui["desc"][d]}</span><em>{ui["open"]} →</em></a>'
        for d in DOCS
    )
    return (f'<section class="hero"><h1>{ui["home_title"]}</h1><p>{ui["home_lead"]}</p></section>'
            f'<section class="cards">{cards}</section>')


def build():
    written = []
    for lang in LANGS:
        out = ROOT / lang
        out.mkdir(exist_ok=True)
        for d in DOCS:
            title, body, toc = render((CONTENT / lang / f"{d}.md").read_text(encoding="utf-8"))
            alts = {l: f"{l}/{d}.html" for l in LANGS}
            (out / f"{d}.html").write_text(
                page(lang, d, f"{title} — Beeloc Business", doc_body(lang, title, body, toc), "../", alts, UI[lang]["desc"][d]),
                encoding="utf-8")
            written.append(f"{lang}/{d}.html")
        alts = {l: f"{l}/index.html" for l in LANGS}
        (out / "index.html").write_text(
            page(lang, None, UI[lang]["home_title"], home_body(lang), "../", alts, UI[lang]["home_lead"]), encoding="utf-8")
        written.append(f"{lang}/index.html")

    for name, (lang, d) in LEGACY.items():
        title, body, toc = render((CONTENT / lang / f"{d}.md").read_text(encoding="utf-8"))
        alts = {l: f"{l}/{d}.html" for l in LANGS}
        (ROOT / name).write_text(
            page(lang, d, f"{title} — Beeloc Business", doc_body(lang, title, body, toc), "", alts, UI[lang]["desc"][d]),
            encoding="utf-8")
        written.append(name)

    (ROOT / "index.html").write_text(ROOT_INDEX, encoding="utf-8")
    (ROOT / "404.html").write_text(ROOT_INDEX, encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    written += ["index.html", "404.html"]
    return written


ROOT_INDEX = """<!doctype html>
<html lang="uz">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Beeloc Business</title>
<script>
  (function () {
    var l = (navigator.language || "uz").slice(0, 2).toLowerCase();
    var lang = l === "ru" ? "ru" : l === "en" ? "en" : "uz";
    var base = location.pathname.indexOf("/beeloc-business/") === 0 ? "/beeloc-business/" : "/";
    location.replace(base + lang + "/index.html");
  })();
</script>
</head>
<body>
<main class="wrap">
  <h1>Beeloc Business</h1>
  <p><a href="uz/index.html">O'zbekcha</a> · <a href="ru/index.html">Русский</a> · <a href="en/index.html">English</a></p>
</main>
</body>
</html>
"""


def sync_app(target: Path):
    for lang in ["uz", "ru", "en"]:
        for d in APP_DOCS:
            shutil.copyfile(CONTENT / lang / f"{d}.md", target / f"{d}_{lang}.md")
            print("app:", target / f"{d}_{lang}.md")


if __name__ == "__main__":
    for f in build():
        print("site:", f)
    if "--sync-app" in sys.argv:
        sync_app(Path(sys.argv[sys.argv.index("--sync-app") + 1]).expanduser())
