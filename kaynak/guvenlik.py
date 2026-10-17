# -*- coding: utf-8 -*-
"""Sayfa güvenliği: İçerik Güvenlik Politikası (CSP) + ihlal sayımı.

Her HTML sayfasına, o sayfadaki satır içi betiklerin sha256 parmak izleriyle bir CSP <meta> etiketi eklenir:
yalnız bizim yazdığımız betikler çalışır; araya sızdırılan (hack, enjeksiyon) bir betik tarayıcıda engellenir.
Engellenen bir şey olursa tarayıcı 'securitypolicyviolation' olayı üretir; başa eklenen küçük betik bunu
yalnız türü ve kaynağın alan adıyla sayaca bildirir (panel → Güvenlik → CSP ihlalleri).
Satır içi olay işleyicisi (onclick=…) KULLANMA: CSP engeller; data-* + addEventListener kullan.
ALES deposunda bu dosyanın kopyası var (kaynak/guvenlik.py) — değişince harezmi.dev/_uret_yonetim.py kopyalar.
"""
import base64, hashlib, re

_BETIK = re.compile(r"<script(?![^>]*\bsrc=)(?![^>]*application/ld\+json)[^>]*>(.*?)</script>", re.S | re.I)


def ihlal_betigi(uc):
    """<head> başına: CSP ihlallerini say (kendi başına çalışır; sayaç betiği yüklenmeden önceki ihlalleri de yakalar)."""
    return ("<script>(function(){var n=0;document.addEventListener('securitypolicyviolation',function(e){if(++n>5)return;"
            "if(['dhbtkampi.com','mbstskampi.com','aleskampi.com'].indexOf(location.hostname)<0)return;"
            "var d=(e.effectiveDirective||e.violatedDirective||'diger').split(' ')[0].replace(/[^a-z-]/g,'').slice(0,30),k=e.blockedURI||'';"
            "try{k=k.indexOf(':')>0&&k.indexOf('//')>0?new URL(k).hostname:k}catch(x){}k=(k||'satir-ici').toLowerCase().replace(/[^a-z0-9.-]/g,'').slice(0,60)||'satir-ici';"
            "var b=JSON.stringify({p:location.pathname,o:'csp',yon:d,kay:k});try{navigator.sendBeacon('" + uc + "',b)}catch(x){}})})();</script>")


def csp_ekle(html, kaynaklar):
    """kaynaklar: {'media-src': '...', 'connect-src': '...'} gibi ek izinler. Parmak izleri en son (renk teması vb. uygulandıktan sonra) hesaplanmalı."""
    izler = sorted({"'sha256-" + base64.b64encode(hashlib.sha256(m.group(1).encode("utf-8")).digest()).decode() + "'" for m in _BETIK.finditer(html)})
    yon = {"default-src": "'self'", "script-src": "'self' " + " ".join(izler), "style-src": "'self' 'unsafe-inline'", "img-src": "'self' data:",
           "font-src": "'self'", "media-src": "'self'", "connect-src": "'self'", "object-src": "'none'", "base-uri": "'self'", "form-action": "'self'"}
    for k, v in kaynaklar.items():
        yon[k] = (yon.get(k, "") + " " + v).strip()
    deger = "; ".join(f"{k} {v}" for k, v in yon.items()) + "; upgrade-insecure-requests"
    meta = f'<meta http-equiv="Content-Security-Policy" content="{deger}">'
    return re.sub(r'(<meta charset="utf-8">)', lambda m: m.group(1) + "\n" + meta, html, count=1, flags=re.I) if '<meta charset="utf-8">' in html else html.replace("<head>", "<head>\n" + meta, 1)
