"""ALES Kampı sitesi: kaynak/ → _site/  (GitHub Actions her gün ve her push'ta çalıştırır)

Kitap kırpımı, ÖSYM soru metni İÇERMEZ. Girdiler (hepsi bu depoda):
  kaynak/ders/*.html               özgün konu anlatımları
  kaynak/veri/dersler.json         ders listesi
  kaynak/veri/analiz.json          1100 sorunun konu/zorluk etiketleri (yalnız sayımlar yayımlanır)
  kaynak/veri/program16.json       16 haftalık program
  kaynak/veri/sorular/*.json       Günün Sorusu bankası (özgün); yalnız günü GEÇMİŞ sorular yayımlanır
  kaynak/icerik.py                 1-2-3 aylık programlar, rehber metni
  kaynak/CNAME (varsa)             özel alan adı
  kaynak/veri/guncelleme.json      sayfa başına içerik özeti + son değişiklik tarihi (derleme günceller, Actions commit'ler)

Kullanım:  python kaynak/build.py
"""
import glob, hashlib, html, json, os, re, shutil, statistics, sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

KOK = os.path.dirname(os.path.abspath(__file__))
VERI = os.path.join(KOK, "veri")
CIKTI = os.path.join(os.path.dirname(KOK), "_site")
sys.path.insert(0, KOK)
from icerik import PROGRAMLAR, REHBER  # noqa: E402

CNAME = open(os.path.join(KOK, "CNAME")).read().strip() if os.path.exists(os.path.join(KOK, "CNAME")) else None
BASE = os.environ.get("SITE_BASE") or (f"https://{CNAME}" if CNAME else "https://alesrotasi.github.io")
TG = "https://t.me/+yu1PnT-cz9ZiM2Fk"  # @aleskampi, "Site" davet bağlantısı (katılım kaynağı sayılır)
TG_GENEL = "https://t.me/aleskampi"
GC = open(os.path.join(KOK, "goatcounter.txt")).read().strip() if os.path.exists(os.path.join(KOK, "goatcounter.txt")) else None
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
NAV = [("ales-puan-hesaplama/", "Puan hesaplama"), ("ales-3-hazirlik/", "ALES/3 planı"), ("ales-calisma-programi/", "Çalışma programı"), ("dersler/", "Dersler"),
       ("sorular/", "Çözümlü sorular"), ("konu-analizi/", "Konu analizi")]
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
GUNC_DOSYA = os.path.join(VERI, "guncelleme.json")
GUNC = json.load(open(GUNC_DOSYA, encoding="utf-8")) if os.path.exists(GUNC_DOSYA) else {}
KAYNAK_ANALIZ = (f"son {NS} ALES ({SINAVLAR[0]} – {SINAVLAR[-1]}) sorusunun ALES Kampı tarafından yapılan konu ve zorluk etiketlemesi "
                 f'(<a href="{BASE}/konu-analizi/">konu analizi</a>)')
KAYNAK_OSYM = '<a href="https://www.osym.gov.tr/">ÖSYM</a> 2026-ALES başvuru kılavuzu'


def tarih_tr(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {AYLAR[d.month - 1]} {d.year}"


def guncel_tarih(yol, govde):
    """İçerik değiştiyse bugünün tarihi, değişmediyse son değişikliğin tarihi (sitemap lastmod ve 'Son güncelleme' için)."""
    h = hashlib.sha1(govde.encode("utf-8")).hexdigest()[:12]
    e = GUNC.get(yol)
    if not e or e[0] != h:
        e = GUNC[yol] = [h, BUGUN_TR.isoformat()]
    return e[1]


BOSLUK_NOKTA = re.compile(r"\s+([.,;:])")


def sss(kalemler, baslik="Sık sorulanlar"):
    """[(soru, cevap_html)] → (HTML bölümü, FAQPage JSON-LD). Cevabın ilk cümlesi soruyu doğrudan yanıtlar."""
    h = "".join(f"<details><summary>{esc(q)}</summary><p>{a}</p></details>" for q, a in kalemler)
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": BOSLUK_NOKTA.sub(lambda m: m.group(1), ilk_cumle(a, 10000))}} for q, a in kalemler]}
    return f'<section class="sss"><h2>{esc(baslik)}</h2>{h}</section>', ld


def rakamlar():
    """Analizden alıntılanabilir temel sayılar."""
    soz, say = konu_istat("SOZ"), konu_istat("SAY")
    soz_top = sum(n for _, n, _, _ in soz)
    par = sum(n for k, n, _, _ in soz if k.startswith("Paragraf") or k == "Uzun Metin Okuma")
    k = {s: sum(1 for r in SORULAR if r["bolum"] == b and r["konu"] in ks) for s, _, _, b, ks, _ in KONU_SAYFALARI}
    zor = max(soz + say, key=lambda x: x[2])
    sb = lambda n: virgul(round(n / NS, 1))
    return dict(par_oran=round(100 * par / soz_top), par=sb(par), sozm=sb(k["sozel-mantik"]), saym=sb(k["sayisal-mantik"]),
                geo=sb(k["geometri"]), prob=sb(k["problemler"]), temel=sb(k["temel-matematik"]), grafik=sb(k["grafik-tablo"]),
                zor_ad=ad(zor[0]), zor_puan=virgul(round(zor[2], 2)))


def bulgular():
    r = rakamlar()
    return [f"ALES Sözel testindeki soruların yaklaşık %{r['par_oran']}'si paragraf temellidir (ana düşünce, çıkarım, paragraf yapısı, uzun metin): sınav başına ortalama {r['par']} soru.",
            f"ALES Sayısal testinde en çok soru getiren tek konu sayısal mantıktır: sınav başına ortalama {r['saym']} soru.",
            f"Sözel mantık sınav başına ortalama {r['sozm']} soru getirir ve en zor etiketlenen konudur (1–3 ölçeğinde ortalama zorluk {r['zor_puan']}).",
            f"Temel matematik (temel işlemler, sayı kavramları, denklem, bölünebilme, kümeler, tanımlı işlem) sınav başına ortalama {r['temel']} soru, problemler {r['prob']} soru getirir.",
            f"Geometri sınav başına ortalama {r['geo']} soru getirir; öğrenmesi en uzun süren konu olduğundan kısa hazırlıkta en sona bırakılabilir.",
            f"Grafik ve tablo yorumlama sınav başına ortalama {r['grafik']} sorudur."]


def sayfa(yol, baslik, aciklama, govde, kok, jsonld=None, aktif="", kaynak=None):
    url = BASE + "/" + yol
    if yol != "404.html":
        t = guncel_tarih(yol, govde)
        govde += (f'\n<p class="guncel">Son güncelleme: <time datetime="{t}">{tarih_tr(t)}</time>'
                  + (f" · Kaynak: {kaynak}" if kaynak else "") + "</p>")
        jsonld = (jsonld or []) + [{"@context": "https://schema.org", "@type": "WebPage", "name": baslik, "url": url, "inLanguage": "tr",
                                    "description": aciklama, "dateModified": t,
                                    "isPartOf": {"@type": "WebSite", "name": "ALES Kampı", "url": BASE + "/"},
                                    "publisher": {"@type": "Organization", "name": "ALES Kampı", "url": BASE + "/"}}]
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
<meta property="og:site_name" content="ALES Kampı">
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
<a class="logo" href="{kok}">ALES <b>Kampı</b></a>
<nav>{navh}<a class="tg" href="{TG}">Telegram grubu</a></nav>
</div></header>
<main class="ic">
{govde}
</main>
<footer class="alt"><div class="ic">
<p><b>ALES Kampı</b>: ALES'e sıfırdan hazırlananlar için ücretsiz konu anlatımları, çözümlü sorular, konu analizi ve çalışma programları.
Günlük soru, haftalık kamp ve akademik ilanlar için <a href="{TG}">Telegram grubu @aleskampi</a>.</p>
<p class="altlink"><a href="{kok}ales-puan-hesaplama/">ALES puan hesaplama</a> · <a href="{kok}ales-nasil-calisilir/">ALES'e sıfırdan nasıl çalışılır?</a> · <a href="{kok}ales-konulari/">ALES konuları ve soru dağılımı</a> · <a href="{kok}ales-calisma-programi/">1-2-3-4 aylık programlar</a> · <a href="{kok}sorular/">Çözümlü sorular</a></p>
<p class="iletisim"><a href="{kok}hakkinda/">Hakkında</a> · <a href="{kok}gizlilik/">Gizlilik ve KVKK</a> · İletişim: <a href="mailto:esraaksoyy34@gmail.com">esraaksoyy34@gmail.com</a></p>
<p class="kucuk">© ALES Kampı. İçerikler özgündür ve izinsiz çoğaltılamaz; hiçbir yayınevi kitabından ya da ÖSYM sorusundan alıntı içermez. ALES, ÖSYM'nin düzenlediği bir sınavdır;
bu site ÖSYM ile bağlantılı değildir. Resmî bilgi için <a href="https://www.osym.gov.tr/">osym.gov.tr</a>.</p>
</div></footer>
<div class="baski-notu">Bu içerik ALES Kampı'na aittir: {BASE}/</div>
{f'<script data-goatcounter="https://{GC}.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>' if GC else ""}
<script>
(function(){{var serbest=function(e){{return e.target&&e.target.closest&&e.target.closest("input,textarea,select")}};
["copy","cut","contextmenu","dragstart","selectstart"].forEach(function(t){{document.addEventListener(t,function(e){{if(!serbest(e))e.preventDefault()}})}});}})();
</script>
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
    rk = rakamlar()
    sss_h, sss_ld = sss([
        ("ALES'te kaç soru var, süre ne kadar?", "ALES'te 50 sözel ve 50 sayısal olmak üzere 100 soru vardır; süre 150 dakikadır. Dört yanlış bir doğruyu götürür. Güncel kurallar için ÖSYM'nin başvuru kılavuzuna bak."),
        ("ALES'te en çok hangi konudan soru çıkar?", f"Sözel'de paragraf: son {NS} sınavda sözel soruların yaklaşık %{rk['par_oran']}'si paragraf temelliydi. Sayısal'da en büyük tek konu sayısal mantık (sınav başına ortalama {rk['saym']} soru). Ayrıntı: <a href=\"konu-analizi/\">konu analizi</a>."),
        ("Sıfırdan başlıyorum, nereden başlamalıyım?", f"Paragraftan başla: sözel soruların yaklaşık %{rk['par_oran']}'si paragraf temelli. <a href=\"dersler/{DERS['s01']['slug']}/\">Paragrafta ana düşünce</a> dersiyle başla, sayısalda <a href=\"dersler/{DERS['y01']['slug']}/\">sayılar ve temel kavramlar</a> ile paralel ilerle. Ayrıntılı yol: <a href=\"ales-nasil-calisilir/\">ALES'e sıfırdan nasıl çalışılır?</a>"),
        ("ALES puanı kaç yıl geçerlidir?", "ALES sonuçları açıklandığı tarihten itibaren 5 yıl geçerlidir. Yaklaşık puanını <a href=\"ales-puan-hesaplama/\">ALES puan hesaplama</a> sayfasında görebilirsin."),
        ("Çıkmış soruları nereden çözebilirim?", "ÖSYM, geçmiş sınavların soru kitapçıklarını kendi sitesinde ücretsiz yayımlar: <a href=\"https://www.osym.gov.tr/\">osym.gov.tr</a> → Çıkmış Sorular. Bu sitedeki sorular özgündür, ÖSYM sorusu değildir."),
        ("Bu site ücretli mi?", "Hayır. Dersler, sorular, analiz ve programlar ücretsizdir; üyelik gerekmez."),
    ])
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
<a class="duyuru mavi" href="ales-puan-hesaplama/"><b>Kaç net kaç puan?</b> ÖSYM formülüyle yaklaşık ALES puanını hesapla →</a>

<section class="ozet">
<div><h2>Sözel'de en çok soru</h2><ol>{li(konu_istat("SOZ"))}</ol><p><a href="ales-konulari/">Bütün konular →</a></p></div>
<div><h2>Sayısal'da en çok soru</h2><ol>{li(konu_istat("SAY"))}</ol><p><a href="konu-analizi/">Konu analizi →</a></p></div>
</section>

{tg_kutu()}
{sonbolum}
<section><h2 id="sozel">Sözel dersler</h2><div class="kartlar">{soz}</div></section>
<section><h2 id="sayisal">Sayısal dersler</h2><div class="kartlar">{say}</div></section>

{sss_h}
"""
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "ALES Kampı", "url": BASE + "/", "inLanguage": "tr"},
          {"@context": "https://schema.org", "@type": "Organization", "name": "ALES Kampı", "url": BASE + "/", "sameAs": [TG_GENEL], "email": "esraaksoyy34@gmail.com"}, sss_ld]
    yaz("", sayfa("", "ALES Kampı · ALES'e sıfırdan hazırlık: konu anlatımı, çözümlü sorular, çalışma programı",
                  f"ALES sözel ve sayısal için ücretsiz {len(DERSLER)} konu anlatımı, çözümlü sorular, son {NS} sınavın konu dağılımı ve 1-2-3-4 aylık çalışma programları.",
                  g, "", ld, kaynak=KAYNAK_ANALIZ))


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
              kirinti(("ALES Kampı", BASE + "/"), ("Dersler", BASE + "/dersler/"), (d["baslik"], u))]
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
        ld = [kirinti(("ALES Kampı", BASE + "/"), ("Çözümlü sorular", BASE + "/sorular/"), (baslik, u))]
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
    rk = rakamlar()
    bul = "".join(f"<li>{esc(x)}</li>" for x in bulgular())
    sss_h, sss_ld = sss([
        ("ALES Sözel'de en çok hangi konu çıkar?", f"Paragraf. Son {NS} ALES'te sözel soruların yaklaşık %{rk['par_oran']}'si paragraf temelliydi (sınav başına ortalama {rk['par']} soru); ardından sözel mantık gelir (ortalama {rk['sozm']} soru)."),
        ("ALES Sayısal'da en çok hangi konu çıkar?", f"Sayısal mantık: sınav başına ortalama {rk['saym']} soru. Konu grubu olarak bakılırsa temel matematik konuları toplam {rk['temel']}, problemler {rk['prob']} soru getirir."),
        ("ALES'te geometri kaç soru çıkar?", f"Sınav başına ortalama {rk['geo']} soru. Ayrıntı: <a href=\"../ales-konulari/geometri/\">ALES'te geometri</a>."),
        ("ALES'in en zor konusu hangisi?", f"Etiketlemeye göre {rk['zor_ad'].lower()}: 1 (kolay) – 3 (zor) ölçeğinde ortalama zorluk {rk['zor_puan']}. Zorluk etiketleri ALES Kampı'nın değerlendirmesidir."),
    ])
    g = f"""
<header class="baslik"><h1>ALES'te hangi konudan kaç soru çıkıyor?</h1>
<p class="giris">Son {NS} ALES sınavındaki ({SINAVLAR[0]} – {SINAVLAR[-1]}) {len(SORULAR)} sorunun tamamı konu ve zorluğa göre tek tek etiketlendi. Aşağıdaki tablolar bu etiketlerin sayımıdır.</p></header>
<section class="bulgular"><h2>Öne çıkan bulgular</h2><ol>{bul}</ol>
<p class="kucuk">Alıntılarken kaynak: ALES Kampı, “ALES soru dağılımı” ({SINAVLAR[0]} – {SINAVLAR[-1]}, {len(SORULAR)} soru), {BASE}/konu-analizi/</p></section>
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
{sss_h}
{yontem()}
{tg_kutu()}
"""
    yaz("konu-analizi/", sayfa("konu-analizi/", "ALES soru dağılımı: hangi konudan kaç soru çıkıyor?",
                               f"Son {NS} ALES sınavındaki {len(SORULAR)} sorunun konu ve zorluk dağılımı: sözel paragraf, sözel mantık, sayısal mantık, problemler ve geometri.",
                               g, "../", [sss_ld], "konu-analizi/", kaynak=KAYNAK_ANALIZ))


def yontem():
    return (f'<section class="not"><h2>Yöntem</h2><p>Veri: son {NS} ALES ({SINAVLAR[0]} – {SINAVLAR[-1]}), {len(SORULAR)} soru. '
            "Konu ve zorluk etiketleri ALES Kampı tarafından verilmiştir; zorluk 1 (kolay) – 3 (zor) ölçeğinde bizim değerlendirmemizdir, "
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
                                         [kirinti(("ALES Kampı", BASE + "/"), ("ALES konuları", BASE + "/ales-konulari/"), (baslik, u))], "konu-analizi/",
                                         kaynak=KAYNAK_ANALIZ))
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
                                g, "../", None, "konu-analizi/", kaynak=KAYNAK_ANALIZ))


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
    h = [f"<h1>{esc(P['baslik'])}</h1><p class='k'>ALES Kampı · {esc(BASE.split('//')[1])} · Telegram: @aleskampi</p>",
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
                                                        [kirinti(("ALES Kampı", BASE + "/"), ("Çalışma programları", BASE + "/ales-calisma-programi/"), (P["baslik"], u))],
                                                        "ales-calisma-programi/", kaynak=KAYNAK_ANALIZ))
        kartlar += (f'<a class="kart" href="{n}-aylik/"><span class="etiket say">{len(haftalar)} hafta</span><b>{esc(P["baslik"])}</b>'
                    f'<span class="m">{esc(ilk_cumle(P["giris"], 110))}</span></a>')
    rk = rakamlar()
    sss_h, sss_ld = sss([
        ("ALES'e kaç ay çalışmak gerekir?", "Sıfırdan başlayan biri için 3–4 ay rahat bir süredir; bu sürede geometri dahil her konuya yetişilir. 1–2 ayda da hazırlanılabilir, ama yalnız en çok soru getiren konulara öncelik vererek."),
        ("ALES için günde kaç saat çalışmalıyım?", "Programlarımız günde yaklaşık 3 saat üzerine kurulu (1 aylık programda 4 saat): 45 dk paragraf, 60 dk sözel konu, 60 dk sayısal konu ve 15 dk hata defteri. Süreden çok her gün düzenli çalışmak belirleyicidir."),
        ("ALES'e çalışırken hangi konudan başlanmalı?", f"Paragraftan. Sözel soruların yaklaşık %{rk['par_oran']}'si paragraf temelli; sayısalda ise temel işlemler ve sayı kavramlarıyla başlayıp sayısal mantığa (sınav başına ortalama {rk['saym']} soru) erken geçmek gerekir."),
        ("Geometriyi atlayabilir miyim?", f"Vaktin 1 ay kadarsa evet. Geometri sınav başına ortalama {rk['geo']} soru getirir ama öğrenmesi en uzun konudur; 1 aylık programımızda bilinçli olarak dışarıda, 2 aylıkta yalnız temel kural düzeyinde."),
        ("Deneme sınavına ne zaman başlamalıyım?", "Konuların çoğunu bir kez gördükten sonra: 4 aylık programda son 3–4 hafta, 2 aylıkta son 2 hafta. Her denemenin ertesi günü yanlışlarını analiz et; analiz edilmeyen deneme net getirmez."),
    ])
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
{sss_h}
{tg_kutu()}
"""
    yaz("ales-calisma-programi/", sayfa("ales-calisma-programi/", "ALES çalışma programı: 1, 2, 3 ve 4 aylık (PDF)",
                                        "Sıfırdan ALES için 1, 2, 3 ve 4 aylık çalışma programları: hafta hafta konular, günlük düzen ve indirilebilir PDF.",
                                        g, "../", [sss_ld], "ales-calisma-programi/", kaynak=KAYNAK_ANALIZ))
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
    rk = rakamlar()
    sss_h, sss_ld = sss([
        ("2026 ALES/3 ne zaman?", "29 Kasım 2026 Pazar, saat 10.15'te. Sınav 150 dakikadır; 50 sözel ve 50 sayısal soru sorulur."),
        ("ALES/3 başvurusu ne zaman, ücreti ne kadar?", "Başvurular 7–15 Ekim 2026 arasında ÖSYM AİS (ais.osym.gov.tr) üzerinden yapılır. Ücret 1.200 TL; ödemenin son günü 16 Ekim. Geç başvuru günü 21 Ekim."),
        ("ALES/3 sonuçları ne zaman açıklanır?", "17 Aralık 2026'da, sonuc.osym.gov.tr üzerinden."),
        ("ALES'e 8 haftada hazırlanılır mı?", f"Evet, öncelik sırasıyla çalışırsan. Sözel'in yaklaşık %{rk['par_oran']}'si paragraf, Sayısal'ın en büyük konusu sayısal mantık (sınav başına ortalama {rk['saym']} soru); bu plan önce bunları, en son geometriyi kural düzeyinde işler ve son iki haftayı denemeye ayırır."),
    ])
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
{sss_h}
{tg_kutu()}
"""
    yaz("ales-3-hazirlik/", sayfa("ales-3-hazirlik/", "2026 ALES/3'e 8 haftada hazırlık planı (29 Kasım)",
                                  "29 Kasım 2026 ALES/3 için 8 haftalık çalışma planı: başvuru tarihleri, hafta hafta konular, günlük düzen ve son hafta hazırlığı.",
                                  g, "../", [sss_ld], "ales-3-hazirlik/", kaynak=f"{KAYNAK_OSYM}; {KAYNAK_ANALIZ}"))


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
           "author": {"@type": "Organization", "name": "ALES Kampı"}, "url": u, "datePublished": "2026-10-01",
           "dateModified": BUGUN_TR.isoformat()}]
    yaz("ales-nasil-calisilir/", sayfa("ales-nasil-calisilir/", "ALES'e sıfırdan nasıl çalışılır? Adım adım rehber",
                                       "ALES'e sıfırdan hazırlık: önce hangi konu, günlük düzen, paragraf ve sayısal mantık stratejisi, deneme zamanlaması ve sık yapılan hatalar.",
                                       g, "../", ld, kaynak=KAYNAK_ANALIZ))


PUAN = json.load(open(os.path.join(VERI, "puan_istatistik.json"), encoding="utf-8"))


def puan_aralik(say_net, soz_net, tur):
    """Kılavuz formülüyle, yayımlanmış ÖSYM istatistik setleri × korelasyon senaryolarının min–max'ı (+ ek pay)."""
    import math
    a, b = PUAN["agirlik"][tur]
    r = []
    for st in PUAN["setler"]:
        (ms, ss), (mv, sv) = st["say"], st["soz"]
        sp = lambda n, m, s: 50 + 10 * (n - m) / s
        AP = a * sp(say_net, ms, ss) + b * sp(soz_net, mv, sv)
        B = a * sp(50, ms, ss) + b * sp(50, mv, sv)
        for rho in PUAN["korelasyon"]:
            S = 10 * math.sqrt(a * a + b * b + 2 * a * b * rho)
            r.append(70 + 30 * (2 * (AP - 50) - S) / (2 * (B - 50) - S))
    k = PUAN["ek_pay"]
    return max(0, min(r) - k), min(100, max(r) + k)


def puan_sayfasi():
    def tablo(tur, satir, sutun, satir_ad, sutun_ad, ters=False):
        s = f'<div class="tablo"><table><thead><tr><th>{satir_ad} ↓ / {sutun_ad} →</th>' + "".join(f"<th>{c}</th>" for c in sutun) + "</tr></thead><tbody>"
        for x in satir:
            s += f"<tr><td><b>{x} net</b></td>"
            for y in sutun:
                lo, hi = puan_aralik(y, x, tur) if not ters else puan_aralik(x, y, tur)
                s += f"<td>{round(lo)}–{round(hi)}</td>"
            s += "</tr>"
        return s + "</tbody></table></div>"
    soz_t = tablo("SOZ", [20, 25, 30, 35, 40, 45], [0, 10, 20, 30], "Sözel net", "Sayısal net")
    say_t = tablo("SAY", [10, 15, 20, 25, 30, 35, 40], [10, 20, 30, 40], "Sayısal net", "Sözel net", ters=True)
    ea_t = tablo("EA", [20, 25, 30, 35, 40], [10, 15, 20, 25, 30], "Sözel net", "Sayısal net")
    kaynak = "".join(f'<li><a href="{s["url"]}">{esc(s["ad"])}</a>: sözel ort. {virgul(s["soz"][0])} (ss {virgul(s["soz"][1])}), '
                     f'sayısal ort. {virgul(s["say"][0])} (ss {virgul(s["say"][1])})</li>' for s in PUAN["setler"])
    js = json.dumps(PUAN, ensure_ascii=False)
    o1, o2, o3 = puan_aralik(10, 30, "SOZ"), puan_aralik(20, 40, "SOZ"), puan_aralik(30, 20, "SAY")
    ar = lambda x: f"{round(x[0])}–{round(x[1])}"
    sss_h, sss_ld = sss([
        ("ALES puanı nasıl hesaplanır?", "Önce her test için net bulunur (doğru − yanlış ÷ 4). Netler, o sınava girenlerin ortalamasına göre standart puana çevrilir, puan türüne göre ağırlıklandırılır (Sözel: %75 sözel + %25 sayısal; Sayısal: tersi; Eşit Ağırlık: %50 + %50) ve ÖSYM formülüyle 0–100 arası ALES puanına dönüştürülür."),
        ("Kaç net kaç puan eder?", f"Kesin cevap sınava girenlerin ortalamasına bağlıdır, ama yaklaşık olarak: 30 sözel + 10 sayısal net ALES Sözel'de {ar(o1)}, 40 sözel + 20 sayısal net {ar(o2)}; 30 sayısal + 20 sözel net ALES Sayısal'da {ar(o3)} puan aralığına düşer."),
        ("ALES'te 4 yanlış 1 doğruyu götürür mü?", "Evet. Her testte net = doğru − yanlış ÷ 4; boş bırakılan soru neti etkilemez."),
        ("Yüksek lisans için kaç ALES puanı gerekir?", "Lisansüstü Eğitim ve Öğretim Yönetmeliğine göre tezli yüksek lisans için ilgili puan türünde en az 55; lisans derecesiyle doktoraya başvuruda 80, yüksek lisansla 55. Araştırma görevliliği için en az 70 aranır. Üniversiteler daha yüksek taban belirleyebilir; başvurduğun ilanı kontrol et."),
        ("ALES puanı kaç yıl geçerlidir?", "5 yıl. Sonucun açıklandığı tarihten itibaren beş yıl boyunca başvurularda kullanılabilir."),
    ])
    g = f"""
<header class="baslik"><p class="ust-yazi">Yaklaşık hesap · ÖSYM formülü</p><h1>ALES puan hesaplama: kaç net kaç puan?</h1>
<p class="giris">Doğru ve yanlış sayını gir; ÖSYM kılavuzundaki formülle üç puan türünde <b>yaklaşık puan aralığını</b> hesaplayalım.
Kesin puanı yalnızca ÖSYM verebilir: puan, o sınava giren herkesin ortalamasına bağlıdır ve ÖSYM bu ortalamaları 2018'den beri yayımlamıyor.
Bu yüzden tek bir sayı değil, dürüst bir aralık gösteriyoruz.</p></header>

<section class="hesap" id="hesap">
<div class="girdi">
<fieldset><legend>Sözel (50 soru)</legend><label>Doğru <input type="number" id="sozD" min="0" max="50" value="30" inputmode="numeric"></label><label>Yanlış <input type="number" id="sozY" min="0" max="50" value="8" inputmode="numeric"></label></fieldset>
<fieldset><legend>Sayısal (50 soru)</legend><label>Doğru <input type="number" id="sayD" min="0" max="50" value="15" inputmode="numeric"></label><label>Yanlış <input type="number" id="sayY" min="0" max="50" value="6" inputmode="numeric"></label></fieldset>
</div>
<p class="netler" id="netler"></p>
<div class="sonuclar" id="sonuc"></div>
<p class="kucuk" id="uyari" hidden></p>
</section>

<section><h2>Hangi net kaç puan? (ALES Sözel puanı)</h2><p>Hücreler yaklaşık puan aralığıdır.</p>{soz_t}</section>
<section><h2>ALES Sayısal puanı</h2>{say_t}</section>
<section><h2>ALES Eşit Ağırlık puanı</h2>{ea_t}</section>

<section class="not"><h2>Nasıl hesaplıyoruz?</h2>
<p>ÖSYM'nin <a href="{PUAN["kilavuz"]}">2026-ALES başvuru kılavuzuna</a> göre (Bölüm 3.9):</p>
<ol class="liste">
<li><b>Ham puan (net)</b> = doğru − yanlış ÷ 4, her test için ayrı.</li>
<li>Her testin ham puanı, o sınavdaki bütün adayların ortalaması 50, standart sapması 10 olacak biçimde <b>standart puana</b> çevrilir.</li>
<li><b>Ağırlıklı puan:</b> Sayısal puan türü %75 sayısal + %25 sözel; Sözel puan türü %25 sayısal + %75 sözel; Eşit Ağırlık %50 + %50.</li>
<li><b>ALES puanı</b> = 70 + 30 × [2(AP − X) − S] ÷ [2(B − X) − S]. AP adayın ağırlıklı puanı; X, S, B ise sınavdaki ağırlıklı puanların ortalaması, standart sapması ve en büyüğüdür.</li>
</ol>
<p>Test ortalamaları ve standart sapmalar sınavdan sınava değişir ve ÖSYM bunları en son 2017–2018'de yayımladı. Aralığı bu üç resmî istatistik setiyle,
sözel-sayısal ilişkisi için üç farklı varsayımla hesaplayıp her iki yana {PUAN["ek_pay"]} puan pay ekliyoruz:</p>
<ul class="liste">{kaynak}</ul>
<p>Gerçek puanın bu aralığın dışına düşmesi mümkündür, özellikle çok düşük ve çok yüksek netlerde. Resmî puan için <a href="https://sonuc.osym.gov.tr">sonuc.osym.gov.tr</a>.</p></section>
{sss_h}
{tg_kutu()}
<script>
const P={js};
const sp=(n,m,s)=>50+10*(n-m)/s;
function aralik(sn,vn,t){{const [a,b]=P.agirlik[t];const r=[];for(const st of P.setler){{const [ms,ss]=st.say,[mv,sv]=st.soz;const AP=a*sp(sn,ms,ss)+b*sp(vn,mv,sv);const B=a*sp(50,ms,ss)+b*sp(50,mv,sv);for(const rho of P.korelasyon){{const S=10*Math.sqrt(a*a+b*b+2*a*b*rho);r.push(70+30*(2*(AP-50)-S)/(2*(B-50)-S));}}}}return [Math.max(0,Math.min(...r)-P.ek_pay),Math.min(100,Math.max(...r)+P.ek_pay)];}}
const al=id=>Math.max(0,Math.min(50,parseInt(document.getElementById(id).value)||0));
function hesapla(){{const sD=al('sozD'),sY=al('sozY'),yD=al('sayD'),yY=al('sayY');const uy=document.getElementById('uyari');
const tasan=(sD+sY>50)||(yD+yY>50);uy.hidden=!tasan;uy.textContent=tasan?'Bir testte doğru + yanlış 50\\'yi geçemez.':'';
const vn=sD-sY/4,sn=yD-yY/4;document.getElementById('netler').innerHTML='Sözel net: <b>'+vn.toFixed(2).replace('.',',')+'</b> · Sayısal net: <b>'+sn.toFixed(2).replace('.',',')+'</b>';
const T=[['SOZ','ALES Sözel'],['EA','ALES Eşit Ağırlık'],['SAY','ALES Sayısal']];
document.getElementById('sonuc').innerHTML=T.map(([k,ad])=>{{const [lo,hi]=aralik(sn,vn,k);return '<div><span>'+ad+'</span><b>'+Math.round(lo)+'–'+Math.round(hi)+'</b><small>yaklaşık</small></div>';}}).join('');}}
document.querySelectorAll('#hesap input').forEach(i=>i.addEventListener('input',hesapla));hesapla();
</script>
"""
    ld = [{"@context": "https://schema.org", "@type": "WebApplication", "name": "ALES puan hesaplama (yaklaşık)", "url": BASE + "/ales-puan-hesaplama/",
           "applicationCategory": "EducationalApplication", "operatingSystem": "Web", "inLanguage": "tr", "isAccessibleForFree": True,
           "offers": {"@type": "Offer", "price": "0", "priceCurrency": "TRY"}}, sss_ld]
    yaz("ales-puan-hesaplama/", sayfa("ales-puan-hesaplama/", "ALES puan hesaplama 2026: kaç net kaç puan? (ÖSYM formülü)",
                                      "ALES puanını ÖSYM kılavuzundaki formülle yaklaşık hesapla: sözel, sayısal ve eşit ağırlık puan aralıkları ve kaç net kaç puan tablosu.",
                                      g, "../", ld, "ales-puan-hesaplama/", kaynak=f'<a href="{PUAN["kilavuz"]}">ÖSYM 2026-ALES kılavuzu, Bölüm 3.9</a> ve ÖSYM sayısal bilgileri'))


def hakkinda():
    g = f"""
<article class="ders"><header><p class="ust-yazi">ALES Kampı</p><h1>Hakkında</h1></header>
<div class="govde rehber">
<p><b>ALES Kampı</b>, ALES'e sıfırdan hazırlananlar için ücretsiz bir çalışma rehberidir: {len(DERSLER)} konu anlatımı, her gün yeni
çözümlü sorular, sınava kalan süreye göre çalışma programları, konu dağılımı analizi ve yaklaşık puan hesaplama.
Aynı ekip, her gün soru ve kamp görevi paylaşılan <a href="{TG}">@aleskampi Telegram grubunu</a> yönetir.</p>
<h2>İçerik nasıl hazırlanıyor?</h2>
<ul class="liste">
<li><b>Konu dağılımı:</b> son {NS} ALES'teki ({SINAVLAR[0]} – {SINAVLAR[-1]}) {len(SORULAR)} sorunun her biri konu ve zorluğa göre tek tek etiketlendi. Zorluk etiketleri bizim değerlendirmemizdir.</li>
<li><b>Dersler ve sorular özgündür.</b> Hiçbir yayınevi kitabından ya da ÖSYM sorusundan alıntı yapılmaz; sorular ALES'in soru tiplerini örnek alarak sıfırdan yazılır.
Sayısal soruların cevapları bilgisayarla ayrıca doğrulanır; sözel sorularda her yanlış şıkkın neden yanlış olduğu çözümde gösterilir.</li>
<li><b>Puan hesaplama</b> ÖSYM kılavuzundaki resmî formülü ve ÖSYM'nin yayımladığı son istatistikleri kullanır; bu yüzden tek bir sayı değil, yaklaşık bir aralık verir.</li>
<li><b>Tarih ve kurallar</b> ÖSYM'nin kılavuzlarından alınır; son söz her zaman <a href="https://www.osym.gov.tr/">osym.gov.tr</a>'dedir. ALES Kampı ÖSYM ile bağlantılı değildir.</li>
</ul>
<h2>Hata mı buldun?</h2>
<p>Bir soruda ikinci bir doğru cevap, bir derste yanlış bilgi ya da çalışmayan bir sayfa gördüysen yaz; kontrol edip düzeltiriz:
<a href="mailto:esraaksoyy34@gmail.com">esraaksoyy34@gmail.com</a></p>
<h2>Kullanım</h2>
<p>Siteyi kişisel çalışman için özgürce kullanabilirsin. İçeriklerin başka bir sitede, kitapta ya da kanalda izinsiz çoğaltılmasına izin verilmez; alıntı yapmak istersen kaynak bağlantısı vererek yap.</p>
</div></article>
{tg_kutu()}
"""
    yaz("hakkinda/", sayfa("hakkinda/", "Hakkında · ALES Kampı", "ALES Kampı nedir, içerikler nasıl hazırlanıyor, veri kaynakları ve iletişim.", g, "../"))


def gizlilik():
    e = '<a href="mailto:esraaksoyy34@gmail.com">esraaksoyy34@gmail.com</a>'
    sayac = ("<li><b>Ziyaret istatistiği (GoatCounter).</b> Hangi sayfaların ne kadar okunduğunu görmek için çerez kullanmayan GoatCounter hizmeti kullanılır. "
             "Bu hizmet sayfa adresini, geldiğin bağlantıyı (referrer), tarayıcı/işletim sistemi türünü, ekran boyutunu ve IP adresinden çıkarılan ülke bilgisini "
             "toplu istatistik olarak kaydeder; IP adresini saklamaz, çerez bırakmaz ve seni siteler arasında izlemez. "
             "<i>Hukuki sebep:</i> siteyi geliştirmedeki meşru menfaat (KVKK m. 5/2-f).</li>"
             if GC else "")
    g = f"""
<article class="ders"><header><p class="ust-yazi">ALES Kampı</p><h1>Gizlilik ve KVKK aydınlatma metni</h1></header>
<div class="govde rehber">
<p>Bu metin, 6698 sayılı Kişisel Verilerin Korunması Kanunu (KVKK) m. 10 uyarınca, ALES Kampı sitesini kullanırken hangi kişisel verilerin, hangi amaç ve hukuki sebeple işlendiğini açıklar.</p>
<h2>Veri sorumlusu</h2>
<p>Veri sorumlusu, ücretsiz ve gönüllü olarak yayımlanan ALES Kampı sitesinin sahibi <b>Esra Sultan Aslan</b>'dır. Kişisel verilerle ilgili her talep için iletişim adresi: {e}. Site ÖSYM ya da herhangi bir kurumla bağlantılı değildir.</p>
<h2>İşlenen veriler</h2>
<ul class="liste">
<li><b>Üyelik ve form yok.</b> Site üyelik istemez, form içermez, reklam ya da çerez kullanmaz.</li>
<li><b>Sunucu kayıtları.</b> Site GitHub Pages üzerinde yayımlanır. GitHub, her web sunucusu gibi güvenlik ve kötüye kullanımın önlenmesi amacıyla sayfa isteklerini IP adresi, tarih-saat ve tarayıcı bilgisiyle kayıt altına alır. <i>Hukuki sebep:</i> meşru menfaat (KVKK m. 5/2-f). Bu kayıtlara biz erişmeyiz; GitHub'ın kendi gizlilik bildirimine tabidir.</li>
{sayac}
</ul>
<h2>Yurt dışına aktarım</h2>
<p>Barındırma (GitHub, ABD){" ve ziyaret istatistiği (GoatCounter)" if GC else ""} hizmetleri yurt dışındaki sunucularda çalıştığı için yukarıdaki teknik veriler, yalnızca bu hizmetlerin sunulması amacıyla ve KVKK m. 9'daki şartlar çerçevesinde yurt dışında işlenir.</p>
<h2>Telegram grubu</h2>
<p>Sitedeki Telegram bağlantıları seni Telegram'a götürür; gruba katılmak isteğe bağlıdır. Telegram'da paylaştığın bilgiler (kullanıcı adın, mesajların, anket cevapların) Telegram'ın kendi gizlilik politikasına tabidir ve grubun diğer üyelerince görülebilir. Grup botu, grup içi istatistik (ör. anketlerdeki doğru cevap oranı, gruba hangi davet bağlantısıyla katılındığının sayısı) dışında kişisel veri saklamaz.</p>
<h2>Bize e-posta gönderdiğinde</h2>
<p>E-posta adresin, adın (paylaştıysan) ve mesajın yalnızca sana cevap vermek ve bildirdiğin hatayı düzeltmek için kullanılır; kimseyle paylaşılmaz, yazışma bitince makul süre içinde silinir. E-posta hizmeti yurt dışındaki bir sağlayıcı (Google) üzerinden yürür. <i>Hukuki sebep:</i> iletişimi senin başlatman ve talebine cevap verilmesindeki meşru menfaat (KVKK m. 5/2-f).</p>
<h2>Hakların</h2>
<p>KVKK m. 11 uyarınca verilerinin işlenip işlenmediğini öğrenme, bilgi isteme, düzeltilmesini ya da silinmesini isteme, aktarıldığı üçüncü kişileri bilme, itiraz etme ve zararın giderilmesini isteme haklarına sahipsin. Başvurunu {e} adresine yazabilirsin; en geç 30 gün içinde cevaplanır. Cevabı yeterli bulmazsan Kişisel Verileri Koruma Kurulu'na şikâyette bulunabilirsin.</p>
<p>Bu metin, veri işlemeyi etkileyen bir değişiklik olduğunda güncellenir.</p>
</div></article>
"""
    yaz("gizlilik/", sayfa("gizlilik/", "Gizlilik ve KVKK · ALES Kampı", "ALES Kampı KVKK aydınlatma metni: işlenen veriler (sunucu kayıtları, çerezsiz ziyaret istatistiği, e-posta), hukuki sebepler, yurt dışı aktarım ve hakların.", g, "../"))


def llms_txt():
    """Yapay zekâ araçları için sitenin özeti (llmstxt.org biçimi)."""
    L = lambda yol, ad, acik: f"- [{ad}]({BASE}/{yol}): {acik}"
    s = [f"# ALES Kampı", "",
         f"> ALES'e (Akademik Personel ve Lisansüstü Eğitime Giriş Sınavı, ÖSYM) sıfırdan hazırlananlar için ücretsiz Türkçe kaynak: "
         f"{len(DERSLER)} özgün konu anlatımı, her gün yeni çözümlü özgün sorular, son {NS} ALES'in ({SINAVLAR[0]} – {SINAVLAR[-1]}) "
         f"{len(SORULAR)} sorusunun konu ve zorluk dağılımı, 1-2-3-4 aylık çalışma programları ve ÖSYM formülüyle yaklaşık puan hesaplama. "
         "Üyelik ve ücret yok. ÖSYM ile bağlantılı değildir.", "",
         "## Konu analizinden öne çıkan bulgular", ""] + [f"- {x}" for x in bulgular()] + [
         f"- Kaynak: {BASE}/konu-analizi/ (zorluk etiketleri ALES Kampı'nın değerlendirmesidir, ÖSYM sınıflandırması değildir)", "",
         "## Ana sayfalar", "",
         L("ales-puan-hesaplama/", "ALES puan hesaplama", "kaç net kaç puan; ÖSYM 2026 kılavuzu formülüyle Sözel, Sayısal ve Eşit Ağırlık puan aralığı"),
         L("konu-analizi/", "ALES soru dağılımı", f"son {NS} sınavda hangi konudan kaç soru çıktığı, zorluk ve paragraf metin alanları"),
         L("ales-konulari/", "ALES konuları", "konu konu soru sayısı, sınav sınav değişim ve soru tipleri"),
         L("ales-calisma-programi/", "ALES çalışma programı", "sıfırdan 1, 2, 3 ve 4 aylık hafta hafta planlar ve PDF"),
         L("ales-3-hazirlik/", "2026 ALES/3 hazırlık planı", "29 Kasım 2026 sınavı için tarihler ve 8 haftalık plan"),
         L("ales-nasil-calisilir/", "ALES'e sıfırdan nasıl çalışılır?", "adım adım hazırlık rehberi"),
         L("sorular/", "Çözümlü sorular", "her gün eklenen özgün sözel ve sayısal sorular, ayrıntılı çözümleriyle"),
         L("hakkinda/", "Hakkında", "içeriklerin nasıl hazırlandığı, veri kaynakları ve iletişim"), "",
         "## Konu anlatımları", ""] + [
         L(f"dersler/{d['slug']}/", d["baslik"], f"{bolum_ad(d['bolum'])}; sınavda ortalama {virgul(ders_soru(d))} soru") for d in SIRA] + [
         "", "## Topluluk", "", f"- [Telegram grubu @aleskampi]({TG_GENEL}): her gün 1 sözel + 1 sayısal soru, akşam çözümü, 16 haftalık kamp, ALES/3 hatırlatmaları", ""]
    return "\n".join(s)


def ekler(yollar):
    yaz("404.html", sayfa("404.html", "Sayfa bulunamadı | ALES Kampı", "Aradığın sayfa bulunamadı.",
                          f'<header class="baslik"><h1>Sayfa bulunamadı</h1><p class="giris"><a href="{BASE}/">Ana sayfaya dön</a> · <a href="{BASE}/sorular/">Çözümlü sorular</a> · <a href="{BASE}/dersler/">Dersler</a></p></header>', BASE + "/"))
    sm = "".join(f"<url><loc>{BASE}/{y}</loc><lastmod>{GUNC.get(y, [0, BUGUN_TR.isoformat()])[1]}</lastmod></url>" for y in yollar)
    yaz("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    yaz("sitemap.txt", "".join(f"{BASE}/{y}\n" for y in yollar))  # düz metin yedek sitemap (Search Console "getirilemedi" derse)
    yaz("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\nSitemap: {BASE}/sitemap.txt\n")
    open(os.path.join(CIKTI, ".nojekyll"), "w").close()
    yaz("llms.txt", llms_txt())
    json.dump({y: GUNC[y] for y in sorted(GUNC) if y in yollar}, open(GUNC_DOSYA, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    if os.path.exists(os.path.join(KOK, "indexnow.txt")):  # IndexNow anahtar dosyası (Bing, Yandex vb.)
        k = open(os.path.join(KOK, "indexnow.txt")).read().strip()
        yaz(f"{k}.txt", k)
    for f in ["favicon.svg", "CNAME"] + [os.path.basename(x) for x in glob.glob(os.path.join(KOK, "google*.html"))]:
        if os.path.exists(os.path.join(KOK, f)):
            shutil.copy(os.path.join(KOK, f), CIKTI)


if __name__ == "__main__":
    shutil.rmtree(CIKTI, ignore_errors=True)
    os.makedirs(CIKTI)
    ana_sayfa(); ders_sayfalari(); soru_sayfalari(); analiz(); konu_sayfalari(); programlar(); ales3(); rehber(); puan_sayfasi(); hakkinda(); gizlilik()
    yollar = (["", "ales-puan-hesaplama/", "ales-3-hazirlik/", "ales-calisma-programi/"] + [f"ales-calisma-programi/{n}-aylik/" for n in (1, 2, 3, 4)] +
              ["ales-nasil-calisilir/", "dersler/"] + [f"dersler/{d['slug']}/" for d in SIRA] +
              ["sorular/"] + [f"sorular/{q['slug']}/" for q in YAYIN] +
              ["konu-analizi/", "ales-konulari/", "hakkinda/", "gizlilik/"] + [f"ales-konulari/{s[0]}/" for s in KONU_SAYFALARI])
    ekler(yollar)
    print(f"Site: {CIKTI} · {len(yollar)} sayfa · {len(YAYIN)} yayımlanmış soru · taban {BASE}")
