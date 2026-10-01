"""ALES Rotası sitesi: kaynak/ → _site/  (GitHub Actions her gün ve her push'ta çalıştırır)

Kitap kırpımı, ÖSYM soru metni İÇERMEZ. Girdiler (hepsi bu depoda):
  kaynak/ders/*.html               özgün konu anlatımları
  kaynak/veri/dersler.json         ders listesi
  kaynak/veri/analiz.json          1100 sorunun konu/zorluk etiketleri (yalnız sayımlar yayımlanır)
  kaynak/veri/program16.json       16 haftalık program
  kaynak/veri/sorular/*.json       Günün Sorusu bankası (özgün); yalnız günü GEÇMİŞ sorular yayımlanır
  kaynak/icerik.py                 1-2-3 aylık programlar, rehber metni
  kaynak/CNAME (varsa)             özel alan adı

Kullanım:  python kaynak/build.py
"""
import glob, html, json, os, re, shutil, statistics, sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

KOK = os.path.dirname(os.path.abspath(__file__))
VERI = os.path.join(KOK, "veri")
CIKTI = os.path.join(os.path.dirname(KOK), "_site")
sys.path.insert(0, KOK)
from icerik import PROGRAMLAR, REHBER  # noqa: E402

CNAME = open(os.path.join(KOK, "CNAME")).read().strip() if os.path.exists(os.path.join(KOK, "CNAME")) else None
BASE = os.environ.get("SITE_BASE") or (f"https://{CNAME}" if CNAME else "https://esraaksoy29.github.io/ales-rotasi")
TG = "https://t.me/aleskampi"
BUGUN_TR = datetime.now(timezone(timedelta(hours=3))).date()
KAMP_BASI = date(2026, 9, 28)
esc = html.escape
virgul = lambda x: str(x).replace(".", ",")


def slug(s):
    tr = str.maketrans("çğıöşüÇĞİÖŞÜâîû", "cgiosuCGIOSUaiu")
    s = re.sub(r"\([^)]*\)", "", s).translate(tr).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


# ---------------------------------------------------------------- veri
DERSLER = json.load(open(os.path.join(VERI, "dersler.json"), encoding="utf-8"))
for d in DERSLER:
    d["slug"] = slug(d["baslik"])
    d["html"] = open(os.path.join(KOK, "ders", d["id"] + ".html"), encoding="utf-8").read()
SIRA = sorted(DERSLER, key=lambda d: (d["bolum"] != "SOZ", int(d["id"][1:])))
DERS = {d["id"]: d for d in DERSLER}

AN = json.load(open(os.path.join(VERI, "analiz.json"), encoding="utf-8"))
SORULAR = AN["sorular"]
for r in SORULAR:
    r["konu"] = {"Denklem-Eşitsizlik": "Denklem-Eşitsizlik-Mutlak Değer"}.get(r["konu"], r["konu"])
ALANLAR = AN["alanlar"]
SINAVLAR = sorted({r["sinav"] for r in SORULAR})
NS = len(SINAVLAR)
PROGRAM16 = json.load(open(os.path.join(VERI, "program16.json"), encoding="utf-8"))

KONU_AD = {"Paragraf-Yardımcı Düşünce/Çıkarım": "Paragraf: yardımcı düşünce ve çıkarım",
           "Paragraf-Yapı": "Paragraf yapısı: sıralama, yer değiştirme, akışı bozan",
           "Paragraf-Ana Düşünce": "Paragraf: ana düşünce ve başlık",
           "Paragraf-Anlatım": "Paragraf: anlatım biçimi ve yazar tutumu",
           "Uzun Metin Okuma": "Uzun metin okuma", "Cümlede Anlam": "Cümlede anlam ve boşluk doldurma",
           "Sözcükte Anlam": "Sözcükte anlam", "Sözel Mantık": "Sözel mantık",
           "Yüzde-Kar-Zarar-Faiz": "Yüzde, kâr-zarar, faiz", "Tanımlı İşlem-Fonksiyon": "Tanımlı işlem ve fonksiyon",
           "Bölünebilme-EBOB-EKOK-Asal": "Bölünebilme, EBOB-EKOK, asal sayılar",
           "Permütasyon-Kombinasyon-Olasılık": "Permütasyon, kombinasyon, olasılık",
           "Denklem-Eşitsizlik-Mutlak Değer": "Denklem, eşitsizlik, mutlak değer",
           "Geometri-Açılar-Üçgen": "Geometri: açılar ve üçgen", "Geometri-Dörtgen-Çokgen": "Geometri: dörtgen ve çokgen",
           "Geometri-Çember-Daire": "Geometri: çember ve daire", "Geometri-Katı Cisimler": "Geometri: katı cisimler",
           "Geometri-Analitik": "Analitik geometri", "Grafik-Tablo Yorumlama": "Grafik ve tablo yorumlama",
           "Sayı-Kesir Problemleri": "Sayı-kesir problemleri", "Sayısal Mantık": "Sayısal mantık",
           "Temel İşlemler": "Temel işlemler (kesir, üslü, köklü)", "Sayı Kavramları": "Sayı kavramları",
           "Oran-Orantı": "Oran-orantı", "Hareket Problemleri": "Hareket problemleri",
           "Karışım Problemleri": "Karışım ve işçi-havuz problemleri", "Yaş Problemleri": "Yaş problemleri"}
ad = lambda k: KONU_AD.get(k, k.replace("-", ", "))

# Konu sayfaları (arama: "ales ... kaç soru", "ales ... konuları")
KONU_SAYFALARI = [
    ("paragraf", "ALES'te paragraf kaç soru çıkar?", "Paragraf", "SOZ",
     ["Paragraf-Yardımcı Düşünce/Çıkarım", "Paragraf-Yapı", "Paragraf-Ana Düşünce", "Paragraf-Anlatım", "Uzun Metin Okuma"],
     ["s01", "s02", "s04", "s05", "s06", "s07"]),
    ("sozel-mantik", "ALES'te sözel mantık kaç soru çıkar?", "Sözel mantık", "SOZ", ["Sözel Mantık"], ["s08", "s09"]),
    ("cumlede-anlam", "ALES'te cümlede anlam ve boşluk doldurma", "Cümlede anlam", "SOZ", ["Cümlede Anlam", "Sözcükte Anlam"], ["s03"]),
    ("sayisal-mantik", "ALES'te sayısal mantık kaç soru çıkar?", "Sayısal mantık", "SAY", ["Sayısal Mantık"], ["y16"]),
    ("geometri", "ALES'te geometri kaç soru çıkar?", "Geometri", "SAY",
     ["Geometri-Açılar-Üçgen", "Geometri-Dörtgen-Çokgen", "Geometri-Çember-Daire", "Geometri-Katı Cisimler", "Geometri-Analitik"], ["y14", "y15"]),
    ("problemler", "ALES'te problemler kaç soru çıkar?", "Problemler", "SAY",
     ["Sayı-Kesir Problemleri", "Yaş Problemleri", "Yüzde-Kar-Zarar-Faiz", "Oran-Orantı", "Hareket Problemleri", "Karışım Problemleri"],
     ["y10", "y11", "y12"]),
    ("temel-matematik", "ALES'te temel matematik konuları ve soru sayıları", "Temel matematik", "SAY",
     ["Temel İşlemler", "Sayı Kavramları", "Denklem-Eşitsizlik-Mutlak Değer", "Bölünebilme-EBOB-EKOK-Asal", "Kümeler", "Tanımlı İşlem-Fonksiyon"],
     ["y01", "y02", "y03", "y04", "y05", "y06", "y07", "y08", "y09"]),
    ("grafik-tablo", "ALES'te grafik ve tablo soruları", "Grafik-tablo", "SAY", ["Grafik-Tablo Yorumlama"], ["y13"]),
    ("olasilik", "ALES'te olasılık, permütasyon ve kombinasyon", "Olasılık", "SAY", ["Permütasyon-Kombinasyon-Olasılık"], ["y12"]),
]


def konu_istat(bolum):
    c = defaultdict(list)
    for r in SORULAR:
        if r["bolum"] == bolum and r["konu"] != "Diğer":
            c[r["konu"]].append(r["zorluk"])
    return sorted(((k, len(v), statistics.mean(v), Counter(v)) for k, v in c.items()), key=lambda x: -x[1])


def ders_soru(d):
    if d.get("band"):
        a, b = d["band"]
        return b - a + 1
    return round(sum(1 for r in SORULAR if r["bolum"] == d["bolum"] and r["konu"] in d["konu"]) / NS, 1)


def ders_icin(konu, bolum):
    return next((d for d in DERSLER if d["bolum"] == bolum and konu in d["konu"]), None)


# ---------------------------------------------------------------- günün sorusu arşivi
def soru_dersi(konu, bolum):
    k = konu.replace("İ", "i").replace("I", "ı").lower()
    if bolum == "sozel":
        kural = [("sözel mantık", "s09" if re.search(r"koşul|olabilir|bilinirse|kesin doğru", k) else "s08"),
                 ("uzun metin", "s07"), ("akış", "s06"), ("yer değiştirme", "s06"), ("sıralama", "s05"),
                 ("boşlu", "s03"), ("kesin çıkarım", "s03"), ("çıkarım", "s02"),
                 ("anlatım|tutum|altı çizili|düşünceyi geliştirme", "s04"), ("ana düşünce", "s01")]
    else:
        kural = [("sayısal mantık", "y16"), ("grafik", "y13"), ("üçgen|açı|pisagor|benzerlik", "y14"),
                 (r"dikdörtgen|kare \(|kare ve|yamuk|dörtgen|çember|daire", "y15"),
                 ("hareket|olasılık|işçi|havuz|karışım", "y12"), ("yaş|sayı-kesir|kesir problemi", "y10"),
                 ("yüzde|kâr|zarar|oran", "y11"), ("küme|tanımlı", "y09"), ("bölünebil|ebob", "y08"),
                 ("mutlak|eşitsizlik|işaret", "y07"), ("çarpan|özdeşlik", "y05"), ("üslü|kuvvet", "y03"),
                 ("köklü", "y04"), ("denklem", "y06"), ("kesir|ondalık", "y02"), ("basamak|rakam|tek-çift|faktöriyel|sayı kavram", "y01")]
    for rx, did in kural:
        if re.search(rx, k):
            return did
    return None


def yayinlanan_sorular():
    """Çözümü grupta yayımlanmış (günü geçmiş) sorular: gün n, n+1. günden itibaren sitede."""
    gun_bugun = (BUGUN_TR - KAMP_BASI).days + 1
    out = []
    for p in sorted(glob.glob(os.path.join(VERI, "sorular", "sorular_hafta*.json"))):
        for g in json.load(open(p, encoding="utf-8")):
            if g["gun"] >= gun_bugun:
                continue
            for b, bad in (("sozel", "Sözel"), ("sayisal", "Sayısal")):
                q = g[b]
                temiz = re.sub(r"\s*\((tekrar|zor|deneme)\)", "", q["konu"])
                q2 = dict(q, gun=g["gun"], bolum=b, bolum_ad=bad, temiz_konu=temiz, ders=soru_dersi(q["konu"], b),
                          tarih=(KAMP_BASI + timedelta(days=g["gun"] - 1)).isoformat())
                q2["slug"] = f"{g['gun']}-{b}-{slug(temiz)}"
                out.append(q2)
    return out


YAYIN = yayinlanan_sorular()

# ---------------------------------------------------------------- şablon
CSS = open(os.path.join(KOK, "stil.css"), encoding="utf-8").read()
NAV = [("ales-3-hazirlik/", "ALES/3 planı"), ("ales-calisma-programi/", "Çalışma programı"), ("dersler/", "Dersler"),
       ("sorular/", "Çözümlü sorular"), ("konu-analizi/", "Konu analizi")]


def sayfa(yol, baslik, aciklama, govde, kok, jsonld=None, aktif=""):
    url = BASE + "/" + yol
    navh = "".join(f'<a href="{kok}{h}"{" aria-current=page" if aktif == h else ""}>{t}</a>' for h, t in NAV)
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in (jsonld or []))
    return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(baslik)}</title>
<meta name="description" content="{esc(aciklama)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="ALES Rotası">
<meta property="og:title" content="{esc(baslik)}">
<meta property="og:description" content="{esc(aciklama)}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="tr_TR">
<meta name="theme-color" content="#1f4e5f">
<link rel="icon" href="{kok}favicon.svg" type="image/svg+xml">
<style>{CSS}</style>
{ld}
</head>
<body>
<header class="ust"><div class="ic">
<a class="logo" href="{kok}">ALES <b>Rotası</b></a>
<nav>{navh}<a class="tg" href="{TG}">Telegram grubu</a></nav>
</div></header>
<main class="ic">
{govde}
</main>
<footer class="alt"><div class="ic">
<p><b>ALES Rotası</b>: ALES'e sıfırdan hazırlananlar için ücretsiz konu anlatımları, çözümlü sorular, konu analizi ve çalışma programları.
Günlük soru, haftalık kamp ve akademik ilanlar için <a href="{TG}">Telegram grubu @aleskampi</a>.</p>
<p class="altlink"><a href="{kok}ales-nasil-calisilir/">ALES'e sıfırdan nasıl çalışılır?</a> · <a href="{kok}ales-konulari/">ALES konuları ve soru dağılımı</a> · <a href="{kok}ales-calisma-programi/">1-2-3-4 aylık programlar</a> · <a href="{kok}sorular/">Çözümlü sorular</a></p>
<p class="kucuk">İçerikler özgündür; hiçbir yayınevi kitabından ya da ÖSYM sorusundan alıntı içermez. ALES, ÖSYM'nin düzenlediği bir sınavdır;
bu site ÖSYM ile bağlantılı değildir. Resmî bilgi için <a href="https://www.osym.gov.tr/">osym.gov.tr</a>.</p>
</div></footer>
</body>
</html>
"""


def yaz(yol, icerik):
    p = os.path.join(CIKTI, yol) if yol.endswith((".html", ".xml", ".txt")) else os.path.join(CIKTI, yol, "index.html")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(icerik)


def kirinti(*parcalar):
    """[(ad, url)] → BreadcrumbList JSON-LD"""
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": a, "item": u} for i, (a, u) in enumerate(parcalar)]}


def tg_kutu():
    return (f'<aside class="tgkutu"><div><b>Her gün 1 sözel + 1 sayısal soru</b>'
            f'<p>Telegram grubunda sabah soru, akşam çözüm; her gün kamp görevi; ALES/3 hatırlatmaları ve '
            f'ALES şartlı akademik ilanlar.</p></div><a class="dugme" href="{TG}">@aleskampi grubuna katıl</a></aside>')


def bolum_ad(b):
    return "Sözel" if b == "SOZ" else "Sayısal"


def ders_kart(d, kok):
    return (f'<a class="kart" href="{kok}dersler/{d["slug"]}/"><span class="etiket {d["bolum"].lower()}">'
            f'{bolum_ad(d["bolum"])} · {d["hafta"]}. hafta</span><b>{esc(d["baslik"])}</b>'
            f'<span class="m">sınavda ortalama {virgul(ders_soru(d))} soru</span></a>')


def ilk_cumle(h, n=155):
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()
    if len(t) <= n:
        return t
    t = t[:n]
    return t[:t.rfind(" ")] + "…"


def ders_link(did, kok):
    d = DERS[did]
    return f'<a href="{kok}dersler/{d["slug"]}/">{esc(d["baslik"])}</a>'


# ---------------------------------------------------------------- sayfalar
def ana_sayfa():
    soz = "".join(ders_kart(d, "") for d in SIRA if d["bolum"] == "SOZ")
    say = "".join(ders_kart(d, "") for d in SIRA if d["bolum"] == "SAY")
    li = lambda st: "".join(f"<li><b>{esc(ad(k))}</b> · sınavda ortalama {virgul(round(n / NS, 1))} soru</li>" for k, n, _, _ in st[:4])
    son = sorted(YAYIN, key=lambda q: (-q["gun"], q["bolum"]))[:6]
    sonh = "".join(f'<a class="kart" href="sorular/{q["slug"]}/"><span class="etiket {"soz" if q["bolum"] == "sozel" else "say"}">'
                   f'{q["bolum_ad"]} · {q["gun"]}. gün</span><b>{esc(q["temiz_konu"])}</b></a>' for q in son)
    sonbolum = f'<section><h2>Son çözümlü sorular</h2><div class="kartlar">{sonh}</div><p><a href="sorular/">Bütün çözümlü sorular →</a></p></section>' if son else ""
    g = f"""
<section class="kahraman">
<p class="ust-yazi">ALES hazırlık · Sözel ve Sayısal</p>
<h1>ALES'e sıfırdan hazırlık için ücretsiz rota</h1>
<p class="giris">{len(DERSLER)} konu anlatımı, her gün yeni çözümlü sorular, son {NS} ALES'teki {len(SORULAR)} sorunun konu dağılımı ve
1, 2, 3 ya da 4 aylık çalışma programları. Her ders, o konudan sınavda kaç soru çıktığıyla birlikte.</p>
<div class="dugmeler"><a class="dugme" href="ales-calisma-programi/">Çalışma programını seç</a><a class="dugme ikincil" href="ales-nasil-calisilir/">Sıfırdan nasıl başlanır?</a></div>
</section>

<a class="duyuru" href="ales-3-hazirlik/"><b>29 Kasım ALES/3'e mi giriyorsun?</b> Başvuru tarihleri ve 8 haftalık öncelik sıralı plan →</a>

<section class="ozet">
<div><h2>Sözel'de en çok soru</h2><ol>{li(konu_istat("SOZ"))}</ol><p><a href="ales-konulari/">Bütün konular →</a></p></div>
<div><h2>Sayısal'da en çok soru</h2><ol>{li(konu_istat("SAY"))}</ol><p><a href="konu-analizi/">Konu analizi →</a></p></div>
</section>

{tg_kutu()}
{sonbolum}
<section><h2 id="sozel">Sözel dersler</h2><div class="kartlar">{soz}</div></section>
<section><h2 id="sayisal">Sayısal dersler</h2><div class="kartlar">{say}</div></section>

<section class="sss">
<h2>Sık sorulanlar</h2>
<details><summary>ALES'te kaç soru var, süre ne kadar?</summary><p>ALES'te 50 sözel ve 50 sayısal olmak üzere 100 soru vardır; süre 150 dakikadır. Dört yanlış bir doğruyu götürür. Güncel kurallar için ÖSYM'nin başvuru kılavuzuna bak.</p></details>
<details><summary>Sıfırdan başlıyorum, nereden başlamalıyım?</summary><p>Sözel'deki soruların yaklaşık üçte ikisi paragraf temellidir. <a href="dersler/{DERS['s01']['slug']}/">Paragrafta ana düşünce</a> dersiyle başla, sayısalda <a href="dersler/{DERS['y01']['slug']}/">sayılar ve temel kavramlar</a> ile paralel ilerle. Ayrıntılı yol: <a href="ales-nasil-calisilir/">ALES'e sıfırdan nasıl çalışılır?</a></p></details>
<details><summary>Çıkmış soruları nereden çözebilirim?</summary><p>ÖSYM, geçmiş sınavların soru kitapçıklarını kendi sitesinde ücretsiz yayımlar: <a href="https://www.osym.gov.tr/">osym.gov.tr</a> → Çıkmış Sorular. Bu sitedeki sorular özgündür, ÖSYM sorusu değildir.</p></details>
<details><summary>Bu site ücretli mi?</summary><p>Hayır. Dersler, sorular, analiz ve programlar ücretsizdir; üyelik gerekmez.</p></details>
</section>
"""
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "ALES Rotası", "url": BASE + "/", "inLanguage": "tr"},
          {"@context": "https://schema.org", "@type": "Organization", "name": "ALES Rotası", "url": BASE + "/", "sameAs": [TG]}]
    yaz("", sayfa("", "ALES Rotası · ALES'e sıfırdan hazırlık: konu anlatımı, çözümlü sorular, çalışma programı",
                  f"ALES sözel ve sayısal için ücretsiz {len(DERSLER)} konu anlatımı, çözümlü sorular, son {NS} sınavın konu dağılımı ve 1-2-3-4 aylık çalışma programları.",
                  g, "", ld))


def ders_sayfalari():
    for i, d in enumerate(SIRA):
        onceki, sonraki = (SIRA[i - 1] if i else None), (SIRA[i + 1] if i + 1 < len(SIRA) else None)
        m = re.search(r'<div class="alesde">(.*?)</div>', d["html"], re.S)
        aciklama = ilk_cumle(m.group(1) if m else d["html"])
        nav = '<nav class="onson">'
        nav += f'<a href="../{onceki["slug"]}/">← {esc(onceki["baslik"])}</a>' if onceki else "<span></span>"
        nav += f'<a href="../{sonraki["slug"]}/">{esc(sonraki["baslik"])} →</a>' if sonraki else "<span></span>"
        nav += "</nav>"
        ilgili = [q for q in YAYIN if q["ders"] == d["id"]][-6:]
        ilgh = ""
        if ilgili:
            ilgh = ('<section><h2>Bu konudan çözümlü sorular</h2><ul class="liste">' +
                    "".join(f'<li><a href="../../sorular/{q["slug"]}/">{q["gun"]}. gün · {esc(q["temiz_konu"])}</a></li>' for q in ilgili) +
                    "</ul></section>")
        bolum_link = "sozel" if d["bolum"] == "SOZ" else "sayisal"
        g = f"""
<nav class="iz"><a href="../../">Ana sayfa</a> › <a href="../#{bolum_link}">{bolum_ad(d["bolum"])} dersler</a></nav>
<article class="ders">
<header><p class="ust-yazi">ALES {bolum_ad(d["bolum"])} · {d["hafta"]}. hafta</p>
<h1>{esc(d["baslik"])}</h1>
<p class="m">Bu konudan sınavda ortalama <b>{virgul(ders_soru(d))} soru</b> çıkıyor (son {NS} ALES).</p></header>
<div class="govde">{d["html"]}</div>
</article>
{ilgh}
{tg_kutu()}
{nav}
"""
        baslik = f"ALES {d['baslik'][0].upper() + d['baslik'][1:]} · {bolum_ad(d['bolum'])} konu anlatımı"
        u = f"{BASE}/dersler/{d['slug']}/"
        ld = [{"@context": "https://schema.org", "@type": "LearningResource", "name": d["baslik"], "description": aciklama,
               "inLanguage": "tr", "learningResourceType": "Konu anlatımı", "isAccessibleForFree": True,
               "about": f"ALES {bolum_ad(d['bolum'])}", "url": u},
              kirinti(("ALES Rotası", BASE + "/"), ("Dersler", BASE + "/dersler/"), (d["baslik"], u))]
        yaz(f"dersler/{d['slug']}/", sayfa(f"dersler/{d['slug']}/", baslik, aciklama, g, "../../", ld, "dersler/"))
    soz = "".join(ders_kart(d, "../") for d in SIRA if d["bolum"] == "SOZ")
    say = "".join(ders_kart(d, "../") for d in SIRA if d["bolum"] == "SAY")
    g = f"""
<header class="baslik"><h1>ALES konu anlatımları</h1>
<p class="giris">{len(DERSLER)} ders: her biri kuralları, çözümlü örnekleri ve sık düşülen tuzaklarıyla. Kartlardaki sayı, o konudan son {NS} ALES'te sınav başına ortalama kaç soru çıktığını gösterir.</p></header>
<section><h2 id="sozel">Sözel</h2><div class="kartlar">{soz}</div></section>
<section><h2 id="sayisal">Sayısal</h2><div class="kartlar">{say}</div></section>
{tg_kutu()}
"""
    yaz("dersler/", sayfa("dersler/", "ALES konu anlatımları · Sözel ve Sayısal dersler",
                          f"ALES sözel ve sayısal {len(DERSLER)} ücretsiz konu anlatımı: paragraf, sözel mantık, temel işlemler, problemler, geometri ve sayısal mantık.",
                          g, "../", None, "dersler/"))


def soru_html(q, cozum_acik=False):
    metin = ""
    if q.get("metin"):
        metin = (f'<pre class="veri">{esc(q["metin"])}</pre>' if q["bolum"] == "sayisal"
                 else "".join(f"<p>{esc(p)}</p>" for p in q["metin"].split("\n") if p.strip()))
    siklar = "".join(f"<li><b>{h})</b> {esc(t)}</li>" for h, t in zip("ABCDE", q["siklar"]))
    coz = "".join(f"<p>{esc(p)}</p>" for p in q["cozum"].split("\n") if p.strip())
    return (f'<div class="soru-kutu">{metin}<p class="kok">{esc(q["soru"])}</p><ol class="siklar">{siklar}</ol>'
            f'<details{" open" if cozum_acik else ""}><summary>Cevabı ve çözümü göster</summary>'
            f'<p class="sonuc">Cevap: {"ABCDE"[q["dogru"]]}</p>{coz}</details></div>')


def soru_sayfalari():
    for q in YAYIN:
        u = f"{BASE}/sorular/{q['slug']}/"
        ders = f'<p class="ilgili">Konunun anlatımı: {ders_link(q["ders"], "../../")}</p>' if q["ders"] else ""
        yildiz = {1: "kolay", 2: "orta", 3: "zor"}[q["zorluk"]]
        g = f"""
<nav class="iz"><a href="../../">Ana sayfa</a> › <a href="../">Çözümlü sorular</a></nav>
<article class="ders">
<header><p class="ust-yazi">ALES {q["bolum_ad"]} · {esc(q["temiz_konu"])} · {yildiz}</p>
<h1>ALES {q["bolum_ad"].lower()} sorusu: {esc(q["temiz_konu"])}</h1>
<p class="m">Günün Sorusu, {q["gun"]}. gün. Özgün soru; ALES'teki soru tipini ve zorluğunu örnek alır. Önce kendin çöz, sonra çözümü aç.</p></header>
<div class="govde">{soru_html(q)}{ders}</div>
</article>
{tg_kutu()}
"""
        baslik = f"ALES {q['bolum_ad']} sorusu: {q['temiz_konu']} (çözümlü) #{q['gun']}"
        acik = ilk_cumle(f"Çözümlü ALES {q['bolum_ad'].lower()} sorusu ({q['temiz_konu']}): " + (q.get("metin") or q["soru"]), 155)
        ld = [kirinti(("ALES Rotası", BASE + "/"), ("Çözümlü sorular", BASE + "/sorular/"), (baslik, u))]
        yaz(f"sorular/{q['slug']}/", sayfa(f"sorular/{q['slug']}/", baslik, acik, g, "../../", ld, "sorular/"))
    # merkez sayfa: derse göre gruplu
    grup = defaultdict(list)
    for q in YAYIN:
        grup[q["ders"]].append(q)
    bloklar = ""
    for d in SIRA:
        qs = grup.get(d["id"])
        if not qs:
            continue
        bloklar += (f'<section><h2>{esc(d["baslik"])} <span class="sayac">{len(qs)}</span></h2><ul class="liste">' +
                    "".join(f'<li><a href="{q["slug"]}/">{esc(q["temiz_konu"])}</a> <span class="m">· {q["gun"]}. gün</span></li>' for q in qs) +
                    f'</ul><p class="ilgili">Konu anlatımı: {ders_link(d["id"], "../")}</p></section>')
    g = f"""
<header class="baslik"><h1>ALES çözümlü sorular</h1>
<p class="giris">Telegram grubundaki Günün Sorusu'nun arşivi: her gün bir sözel ve bir sayısal özgün soru, ayrıntılı çözümü ve tuzak şıkların açıklamasıyla.
Sorular grupta paylaşıldıktan bir gün sonra buraya eklenir. Şu an {len(YAYIN)} soru var.</p></header>
{tg_kutu()}
{bloklar or '<p>İlk sorular yakında burada.</p>'}
"""
    yaz("sorular/", sayfa("sorular/", "ALES çözümlü sorular: sözel ve sayısal, konu konu",
                          "ALES sözel ve sayısal çözümlü özgün sorular: paragraf, sözel mantık, sayısal mantık, problemler, geometri. Her gün yeni soru.",
                          g, "../", None, "sorular/"))


def analiz():
    def tablo(bolum):
        st = konu_istat(bolum)
        mx = st[0][1]
        s = '<div class="tablo"><table><thead><tr><th>Konu</th><th>Toplam</th><th>Sınav başına</th><th>Zorluk</th></tr></thead><tbody>'
        for k, n, z, c in st:
            d = ders_icin(k, bolum)
            isim = f'<a href="../dersler/{d["slug"]}/">{esc(ad(k))}</a>' if d else esc(ad(k))
            zr = "kolay" if z < 1.85 else ("orta" if z < 2.3 else "zor")
            s += (f'<tr><td>{isim}<span class="cubuk" style="--o:{n / mx:.3f}"></span></td><td>{n}</td>'
                  f'<td>{virgul(round(n / NS, 1))}</td><td><span class="z {zr}">{zr}</span> {virgul(round(z, 2))}</td></tr>')
        return s + "</tbody></table></div>"
    alan = Counter(a["alan"] for a in ALANLAR if a["alan"] != "Diğer")
    amx = max(alan.values())
    alan_html = "".join(f'<li><span>{esc(k.replace("-", ", "))}</span><span class="cubuk" style="--o:{v / amx:.3f}"></span><b>%{round(100 * v / len(ALANLAR))}</b></li>'
                        for k, v in alan.most_common())
    soz, say = konu_istat("SOZ"), konu_istat("SAY")
    paragraf = sum(n for k, n, _, _ in soz if k.startswith("Paragraf") or k == "Uzun Metin Okuma")
    sm = next(n for k, n, _, _ in say if k == "Sayısal Mantık")
    konular = "".join(f'<a class="kart" href="../ales-konulari/{s}/"><b>{esc(b)}</b></a>' for s, b, *_ in KONU_SAYFALARI)
    g = f"""
<header class="baslik"><h1>ALES'te hangi konudan kaç soru çıkıyor?</h1>
<p class="giris">Son {NS} ALES sınavındaki ({SINAVLAR[0]} – {SINAVLAR[-1]}) {len(SORULAR)} sorunun tamamı konu ve zorluğa göre tek tek etiketlendi. Aşağıdaki tablolar bu etiketlerin sayımıdır.</p></header>
<section class="ozet">
<div><h2>%{round(100 * paragraf / sum(n for _, n, _, _ in soz))}</h2><p>Sözel soruların paragraf temelli olanları (ana düşünce, çıkarım, yapı, uzun metin)</p></div>
<div><h2>{virgul(round(sm / NS, 1))}</h2><p>Sayısal'da sınav başına sayısal mantık sorusu: en büyük tek konu</p></div>
<div><h2>{virgul(round(sum(n for k, n, _, _ in say if k.startswith("Geometri")) / NS, 1))}</h2><p>Sayısal'da sınav başına geometri sorusu</p></div>
</section>
<section><h2>Konu konu ayrıntı</h2><div class="kartlar">{konular}</div></section>
<section><h2>Sözel: konu dağılımı</h2>{tablo("SOZ")}</section>
<section><h2>Sayısal: konu dağılımı</h2>{tablo("SAY")}</section>
<section><h2>Sözel paragraflar hangi alanlardan geliyor?</h2>
<p>{len(ALANLAR)} sözel sorunun metni konu alanına göre sınıflandırıldı. Paragraf çalışırken farklı alanlardan metin okumak, sınavdaki metin çeşitliliğine hazırlar.</p>
<ul class="alanlar">{alan_html}</ul></section>
{yontem()}
{tg_kutu()}
"""
    yaz("konu-analizi/", sayfa("konu-analizi/", "ALES soru dağılımı: hangi konudan kaç soru çıkıyor?",
                               f"Son {NS} ALES sınavındaki {len(SORULAR)} sorunun konu ve zorluk dağılımı: sözel paragraf, sözel mantık, sayısal mantık, problemler ve geometri.",
                               g, "../", None, "konu-analizi/"))


def yontem():
    return (f'<section class="not"><h2>Yöntem</h2><p>Veri: son {NS} ALES ({SINAVLAR[0]} – {SINAVLAR[-1]}), {len(SORULAR)} soru. '
            "Konu ve zorluk etiketleri ALES Rotası tarafından verilmiştir; zorluk 1 (kolay) – 3 (zor) ölçeğinde bizim değerlendirmemizdir, "
            "ÖSYM'nin resmî bir sınıflandırması değildir. Soru metinleri bu sitede yer almaz; çıkmış soruların kendisine ÖSYM'nin sitesinden ulaşabilirsin.</p></section>")


def konu_sayfalari():
    for s, baslik, kisa, bolum, konular, dersler in KONU_SAYFALARI:
        rs = [r for r in SORULAR if r["bolum"] == bolum and r["konu"] in konular]
        n = len(rs)
        per = Counter(r["sinav"] for r in rs)
        mx = max(per.values())
        zor = Counter(r["zorluk"] for r in rs)
        nolar = sorted(r["no"] for r in rs)
        q1, q3 = nolar[len(nolar) // 4], nolar[(3 * len(nolar)) // 4]
        alt = Counter(r["alt"].strip().lower() for r in rs if r.get("alt")).most_common(10)
        alt_konu = Counter(r["konu"] for r in rs)
        sinav_tab = "".join(f'<tr><td>{x}</td><td>{per.get(x, 0)}<span class="cubuk" style="--o:{per.get(x, 0) / mx:.3f}"></span></td></tr>' for x in SINAVLAR)
        konu_tab = "".join(f"<li><b>{esc(ad(k))}</b>: {v} soru (sınav başına {virgul(round(v / NS, 1))})</li>" for k, v in alt_konu.most_common()) if len(konular) > 1 else ""
        alt_tab = "".join(f"<li>{esc(a)} <span class='m'>({v})</span></li>" for a, v in alt)
        ilgili = [q for q in YAYIN if q["ders"] in dersler][-8:]
        ilgh = "".join(f'<li><a href="../../sorular/{q["slug"]}/">{esc(q["temiz_konu"])}</a> <span class="m">· {q["bolum_ad"]}</span></li>' for q in ilgili)
        g = f"""
<nav class="iz"><a href="../../">Ana sayfa</a> › <a href="../">ALES konuları</a></nav>
<header class="baslik"><p class="ust-yazi">ALES {bolum_ad(bolum)} · {esc(kisa)}</p><h1>{esc(baslik)}</h1>
<p class="giris">Son {NS} ALES'te {esc(kisa.lower())} konusundan toplam <b>{n} soru</b> çıktı: sınav başına ortalama <b>{virgul(round(n / NS, 1))} soru</b>.
Bu sorular {bolum_ad(bolum)} testinde çoğunlukla <b>{q1}–{q3}.</b> sorular arasında yer alıyor.</p></header>
<section class="ozet">
<div><h2>{virgul(round(n / NS, 1))}</h2><p>Sınav başına ortalama soru</p></div>
<div><h2>{min(per.get(x, 0) for x in SINAVLAR)}–{mx}</h2><p>Bir sınavda en az ve en çok</p></div>
<div><h2>%{round(100 * zor[3] / n)}</h2><p>Zor olarak etiketlenen soruların oranı (kolay %{round(100 * zor[1] / n)}, orta %{round(100 * zor[2] / n)})</p></div>
</section>
{"<section><h2>Alt konulara göre</h2><ul class='liste'>" + konu_tab + "</ul></section>" if konu_tab else ""}
<section><h2>Sınav sınav soru sayısı</h2><div class="tablo"><table><thead><tr><th>Sınav</th><th>Soru</th></tr></thead><tbody>{sinav_tab}</tbody></table></div></section>
{"<section><h2>En sık soru tipleri</h2><ul class='liste'>" + alt_tab + "</ul></section>" if alt_tab else ""}
<section><h2>Nasıl çalışılır?</h2><p>Konu anlatımları: {", ".join(ders_link(x, "../../") for x in dersler)}.</p>
{"<p>Çözümlü sorular:</p><ul class='liste'>" + ilgh + "</ul>" if ilgh else ""}</section>
{yontem()}
{tg_kutu()}
"""
        acik = f"Son {NS} ALES'te {kisa.lower()} sınav başına ortalama {virgul(round(n / NS, 1))} soru: sınav sınav dağılım, soru tipleri, zorluk ve çalışma yolu."
        u = f"{BASE}/ales-konulari/{s}/"
        yaz(f"ales-konulari/{s}/", sayfa(f"ales-konulari/{s}/", baslik, acik, g, "../../",
                                         [kirinti(("ALES Rotası", BASE + "/"), ("ALES konuları", BASE + "/ales-konulari/"), (baslik, u))], "konu-analizi/"))
    kart = "".join(f'<a class="kart" href="{s}/"><span class="etiket {b.lower()}">{bolum_ad(b)}</span><b>{esc(t)}</b>'
                   f'<span class="m">sınav başına {virgul(round(sum(1 for r in SORULAR if r["bolum"] == b and r["konu"] in k) / NS, 1))} soru</span></a>'
                   for s, t, _, b, k, _ in KONU_SAYFALARI)
    g = f"""
<header class="baslik"><h1>ALES konuları ve soru dağılımı</h1>
<p class="giris">ALES'te 50 sözel ve 50 sayısal soru var. Hangi konudan kaç soru çıktığını, sınav sınav değişimini ve en sık soru tiplerini konu konu inceleyebilirsin.
Tüm tablo için <a href="../konu-analizi/">konu analizi</a>.</p></header>
<div class="kartlar">{kart}</div>
{tg_kutu()}
"""
    yaz("ales-konulari/", sayfa("ales-konulari/", "ALES konuları 2026: sözel ve sayısal konular, soru dağılımı",
                                "ALES sözel ve sayısal konuları ve soru dağılımı: paragraf, sözel mantık, sayısal mantık, problemler, geometri, temel matematik.",
                                g, "../", None, "konu-analizi/"))


def program_haftalari(n):
    if n == 4:
        out, w = [], 0
        for faz, odak, haftalar in PROGRAM16:
            for ad_, soz, say in haftalar:
                w += 1
                out.append((ad_, [x.replace("çıkmış sorulardan", "ÖSYM çıkmış sorularından") for x in soz],
                            [x.replace("çıkmış sorulardan", "ÖSYM çıkmış sorularından") for x in say],
                            [d["id"] for d in SIRA if d["hafta"] == w]))
        return out
    return PROGRAMLAR[n]["haftalar"]


def hafta_kartlari(haftalar, kok, tarihler=None):
    s = ""
    for i, (ad_, soz, say, dersler) in enumerate(haftalar, 1):
        ul = lambda xs: "".join(f"<li>{esc(x)}</li>" for x in xs)
        t = f" · {esc(tarihler[i - 1])}" if tarihler else ""
        s += f'<div class="hafta"><h3><span>{i}. hafta{t}</span> {esc(ad_)}</h3><h4>Sözel</h4><ul>{ul(soz)}</ul>'
        if say:
            s += f"<h4>Sayısal</h4><ul>{ul(say)}</ul>"
        if dersler:
            s += '<p class="ilgili">Dersler: ' + ", ".join(ders_link(x, kok) for x in dersler) + "</p>"
        s += "</div>"
    return f'<div class="haftalar">{s}</div>'


def pdf_yap(n, yol):
    """Programın yazdırılabilir PDF'i (PyMuPDF Story; Türkçe karakterli yazı tipi gerekir)."""
    try:
        import pymupdf
    except ImportError:
        print("  ! pymupdf yok, PDF atlandı")
        return False
    fontlar = [("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
               ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")]
    f = next((x for x in fontlar if os.path.exists(x[0]) and os.path.exists(x[1])), None)
    if not f:
        print("  ! yazı tipi yok, PDF atlandı")
        return False
    P = PROGRAMLAR[n]
    arsiv = pymupdf.Archive()
    arsiv.add(open(f[0], "rb").read(), "n.ttf")
    arsiv.add(open(f[1], "rb").read(), "b.ttf")
    css = ("@font-face{font-family:T;src:url(n.ttf)} @font-face{font-family:T;src:url(b.ttf);font-weight:bold} "
           "*{font-family:T} body{font-size:10pt;line-height:1.35} h1{font-size:18pt;color:#1f4e5f;margin:0 0 4pt} "
           "h2{font-size:11.5pt;color:#1f4e5f;margin:9pt 0 2pt} p{margin:0 0 4pt} ul{margin:0 0 2pt 12pt} li{margin:0} .k{color:#555;font-size:9pt}")
    h = [f"<h1>{esc(P['baslik'])}</h1><p class='k'>ALES Rotası · {esc(BASE.split('//')[1])} · Telegram: @aleskampi</p>",
         f"<p>{esc(P['giris'])}</p><p><b>Günlük düzen:</b> {esc(P['gunluk'])}</p>"]
    for i, (ad_, soz, say, dersler) in enumerate(program_haftalari(n), 1):
        h.append(f"<h2>{i}. hafta: {esc(ad_)}</h2><ul>" + "".join(f"<li><b>Sözel:</b> {esc(x)}</li>" for x in soz) +
                 "".join(f"<li><b>Sayısal:</b> {esc(x)}</li>" for x in say) + "</ul>")
        if dersler:
            h.append("<p class='k'>Konu anlatımı: " + ", ".join(esc(DERS[x]["baslik"]) for x in dersler) + "</p>")
    h.append(f"<p class='k'>Konu anlatımları ve çözümlü sorular: {esc(BASE)}/ · Her gün soru ve kamp: t.me/aleskampi</p>")
    story = pymupdf.Story(html="".join(h), user_css=css, archive=arsiv)
    w = pymupdf.DocumentWriter(yol)
    mb = pymupdf.paper_rect("a4")
    alan = mb + (42, 42, -42, -42)
    devam = True
    while devam:
        dev = w.begin_page(mb)
        devam, _ = story.place(alan)
        story.draw(dev)
        w.end_page()
    w.close()
    return True


def programlar():
    os.makedirs(os.path.join(CIKTI, "pdf"), exist_ok=True)
    kartlar = ""
    for n in (1, 2, 3, 4):
        P = PROGRAMLAR[n]
        haftalar = program_haftalari(n)
        pdf_ad = f"ales-calisma-programi-{n}-aylik.pdf"
        pdf_var = pdf_yap(n, os.path.join(CIKTI, "pdf", pdf_ad))
        pdf_l = f'<a class="dugme ikincil" href="../../pdf/{pdf_ad}">PDF olarak indir</a>' if pdf_var else ""
        diger = " · ".join(f'<a href="../{k}-aylik/">{PROGRAMLAR[k]["kisa"]}</a>' for k in (1, 2, 3, 4) if k != n)
        g = f"""
<nav class="iz"><a href="../../">Ana sayfa</a> › <a href="../">Çalışma programları</a></nav>
<header class="baslik"><p class="ust-yazi">{len(haftalar)} hafta · sıfırdan</p><h1>{esc(P["baslik"])}</h1>
<p class="giris">{esc(P["giris"])}</p>
<div class="dugmeler">{pdf_l}<a class="dugme ikincil" href="{TG}">Grupla birlikte çalış</a></div></header>
<section><h2>Günlük düzen</h2><p>{esc(P["gunluk"])} Hata defterine, o gün yanlış yaptığın her sorunun nedenini tek cümleyle yaz.</p></section>
<section><h2>Hafta hafta plan</h2>{hafta_kartlari(haftalar, "../../")}</section>
<section><h2>Başka bir süre mi?</h2><p>{diger} · <a href="../../ales-nasil-calisilir/">ALES'e sıfırdan nasıl çalışılır?</a></p></section>
{tg_kutu()}
"""
        u = f"{BASE}/ales-calisma-programi/{n}-aylik/"
        yaz(f"ales-calisma-programi/{n}-aylik/", sayfa(f"ales-calisma-programi/{n}-aylik/", f"{P['baslik']} (sıfırdan, PDF)",
                                                        ilk_cumle(f"{P['baslik']}: {P['giris']}", 155), g, "../../",
                                                        [kirinti(("ALES Rotası", BASE + "/"), ("Çalışma programları", BASE + "/ales-calisma-programi/"), (P["baslik"], u))],
                                                        "ales-calisma-programi/"))
        kartlar += (f'<a class="kart" href="{n}-aylik/"><span class="etiket say">{len(haftalar)} hafta</span><b>{esc(P["baslik"])}</b>'
                    f'<span class="m">{esc(ilk_cumle(P["giris"], 110))}</span></a>')
    g = f"""
<header class="baslik"><h1>ALES çalışma programı: 1, 2, 3 ve 4 aylık</h1>
<p class="giris">Sınava kalan süreye göre seç. Hepsi sıfırdan başlayanlar için yazıldı ve son {NS} ALES'teki konu dağılımına göre önceliklendirildi;
her birinin yazdırılabilir PDF'i var. 29 Kasım'daki sınava hazırlanıyorsan <a href="../ales-3-hazirlik/">tarihli ALES/3 planına</a> bak.</p></header>
<div class="kartlar">{kartlar}</div>
<section><h2>Hangisini seçmeliyim?</h2><ul class="liste">
<li><b>Sıfırdan ve 3 aydan fazla vaktin varsa:</b> 4 aylık. En rahat tempo; geometri dahil her konu.</li>
<li><b>Temelin biraz varsa ya da 3 ayın varsa:</b> 3 aylık.</li>
<li><b>2 ay:</b> öncelik sıralı; geometri yalnız kural düzeyinde.</li>
<li><b>1 ay:</b> yalnız en çok soru getiren konular ve deneme. Geometri dışarıda.</li>
</ul></section>
{tg_kutu()}
"""
    yaz("ales-calisma-programi/", sayfa("ales-calisma-programi/", "ALES çalışma programı: 1, 2, 3 ve 4 aylık (PDF)",
                                        "Sıfırdan ALES için 1, 2, 3 ve 4 aylık çalışma programları: hafta hafta konular, günlük düzen ve indirilebilir PDF.",
                                        g, "../", None, "ales-calisma-programi/"))
    # eski adres: /program/ → 4 aylık
    hedef = f"{BASE}/ales-calisma-programi/4-aylik/"
    yaz("program/", f'<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>Taşındı</title>'
                    f'<link rel="canonical" href="{hedef}"><meta http-equiv="refresh" content="0; url={hedef}"></head>'
                    f'<body><a href="{hedef}">4 aylık ALES çalışma programı</a></body></html>')


ALES3_TARIH = ["5–11 Ekim", "12–18 Ekim", "19–25 Ekim", "26 Ekim – 1 Kasım", "2–8 Kasım", "9–15 Kasım", "16–22 Kasım", "23–29 Kasım"]


def ales3():
    soz = konu_istat("SOZ")
    paragraf = sum(n for k, n, _, _ in soz if k.startswith("Paragraf") or k == "Uzun Metin Okuma")
    haftalar = [list(h) for h in PROGRAMLAR[2]["haftalar"]]
    haftalar[0][2] = haftalar[0][2] + ["Başvuruyu bu hafta yap (7–15 Ekim)"]
    g = f"""
<header class="baslik"><p class="ust-yazi">2026-ALES/3 · 29 Kasım 2026</p>
<h1>ALES/3'e 8 haftada hazırlık planı</h1>
<p class="giris">29 Kasım'daki sınava 8 hafta kala sıfırdan başlayanlar için öncelik sıralı plan. Sıra, son {NS} ALES'teki
{len(SORULAR)} sorunun konu dağılımına göre kuruldu: en çok soru getiren konular önce, az soru getiren ve zaman alan konular seçici.</p>
<div class="dugmeler"><a class="dugme ikincil" href="../pdf/ales-calisma-programi-2-aylik.pdf">Planı PDF olarak indir</a></div></header>
<section class="ozet">
<div><h2>7–15 Ekim</h2><p>Başvuru (ÖSYM AİS). Ücret ödemede son gün 16 Ekim; geç başvuru 21 Ekim.</p></div>
<div><h2>29 Kasım</h2><p>Sınav: Pazar, 10.15, 150 dakika. 50 sözel + 50 sayısal soru.</p></div>
<div><h2>17 Aralık</h2><p>Sonuçlar. Bahar dönemi lisansüstü ilanları genellikle bu tarihten sonra yoğunlaşır.</p></div>
</section>
<p class="kucuk">Tarihler ÖSYM'nin 2026-ALES başvuru kılavuzundan alınmıştır; değişiklik olabilir, son söz <a href="https://www.osym.gov.tr/">osym.gov.tr</a>'dedir.</p>
<section><h2>Bu plan neye göre kuruldu?</h2>
<ul class="liste">
<li><b>Sözel'in %{round(100 * paragraf / sum(n for _, n, _, _ in soz))}'si paragraf temelli.</b> İlk dört hafta paragrafın her tipine ayrıldı; her gün paragraf çözmek planın omurgası.</li>
<li><b>Sayısal'da en büyük tek konu sayısal mantık</b> (sınav başına ~11 soru) ve temel işlemler kolay puandır. Geometri sınav başına ~6 soru ama öğrenmesi uzun: 8 haftalık planda yalnız temel kurallar.</li>
<li><b>Son iki hafta deneme ve tekrar.</b> Yeni konu açmak yerine yanlışları kapatmak bu aşamada daha çok net getirir.</li>
</ul></section>
<section><h2>Hafta hafta plan</h2>{hafta_kartlari(haftalar, "../", ALES3_TARIH)}</section>
<section><h2>Günlük düzen (yaklaşık 3 saat)</h2>
<ul class="liste">
<li><b>45 dk paragraf:</b> 20–25 paragraf, süre tutarak.</li>
<li><b>60 dk haftanın sözel konusu:</b> önce dersi oku, sonra o tipte soru çöz.</li>
<li><b>60 dk haftanın sayısal konusu.</b></li>
<li><b>15 dk hata defteri:</b> bugün yanlış yaptığın soruların nedeni, tek cümleyle.</li>
</ul></section>
{tg_kutu()}
"""
    yaz("ales-3-hazirlik/", sayfa("ales-3-hazirlik/", "2026 ALES/3'e 8 haftada hazırlık planı (29 Kasım)",
                                  "29 Kasım 2026 ALES/3 için 8 haftalık çalışma planı: başvuru tarihleri, hafta hafta konular, günlük düzen ve son hafta hazırlığı.",
                                  g, "../", None, "ales-3-hazirlik/"))


def rehber():
    g = f"""
<nav class="iz"><a href="../">Ana sayfa</a></nav>
<article class="ders"><header><p class="ust-yazi">Rehber · sıfırdan başlayanlar</p><h1>ALES'e sıfırdan nasıl çalışılır?</h1>
<p class="m">Son {NS} ALES'teki {len(SORULAR)} sorunun konu dağılımına dayanan adım adım yol haritası.</p></header>
<div class="govde rehber">{REHBER}</div></article>
{tg_kutu()}
"""
    u = BASE + "/ales-nasil-calisilir/"
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": "ALES'e sıfırdan nasıl çalışılır?", "inLanguage": "tr",
           "author": {"@type": "Organization", "name": "ALES Rotası"}, "url": u, "datePublished": "2026-10-01",
           "dateModified": BUGUN_TR.isoformat()}]
    yaz("ales-nasil-calisilir/", sayfa("ales-nasil-calisilir/", "ALES'e sıfırdan nasıl çalışılır? Adım adım rehber",
                                       "ALES'e sıfırdan hazırlık: önce hangi konu, günlük düzen, paragraf ve sayısal mantık stratejisi, deneme zamanlaması ve sık yapılan hatalar.",
                                       g, "../", ld))


def ekler(yollar):
    yaz("404.html", sayfa("404.html", "Sayfa bulunamadı | ALES Rotası", "Aradığın sayfa bulunamadı.",
                          f'<header class="baslik"><h1>Sayfa bulunamadı</h1><p class="giris"><a href="{BASE}/">Ana sayfaya dön</a> · <a href="{BASE}/sorular/">Çözümlü sorular</a> · <a href="{BASE}/dersler/">Dersler</a></p></header>', BASE + "/"))
    sm = "".join(f"<url><loc>{BASE}/{y}</loc><lastmod>{BUGUN_TR.isoformat()}</lastmod></url>" for y in yollar)
    yaz("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    yaz("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
    open(os.path.join(CIKTI, ".nojekyll"), "w").close()
    for f in ["favicon.svg", "CNAME"] + [os.path.basename(x) for x in glob.glob(os.path.join(KOK, "google*.html"))]:
        if os.path.exists(os.path.join(KOK, f)):
            shutil.copy(os.path.join(KOK, f), CIKTI)


if __name__ == "__main__":
    shutil.rmtree(CIKTI, ignore_errors=True)
    os.makedirs(CIKTI)
    ana_sayfa(); ders_sayfalari(); soru_sayfalari(); analiz(); konu_sayfalari(); programlar(); ales3(); rehber()
    yollar = (["", "ales-3-hazirlik/", "ales-calisma-programi/"] + [f"ales-calisma-programi/{n}-aylik/" for n in (1, 2, 3, 4)] +
              ["ales-nasil-calisilir/", "dersler/"] + [f"dersler/{d['slug']}/" for d in SIRA] +
              ["sorular/"] + [f"sorular/{q['slug']}/" for q in YAYIN] +
              ["konu-analizi/", "ales-konulari/"] + [f"ales-konulari/{s[0]}/" for s in KONU_SAYFALARI])
    ekler(yollar)
    print(f"Site: {CIKTI} · {len(yollar)} sayfa · {len(YAYIN)} yayımlanmış soru · taban {BASE}")
