"""Sitenin yazılı içerikleri: çalışma programları ve rehber metni (özgün)."""

# Her hafta: (ad, sözel maddeler, sayısal maddeler, ders kimlikleri)
PROGRAM_1 = [
    ("Paragrafın temeli ve temel işlemler",
     ["Her gün 30 paragraf: ana düşünce, yardımcı düşünce, kesin çıkarım", "Boşluk doldurma (sözel 1–8)"],
     ["Sayılar, kesir, üslü ve köklü sayılar: kural + kolay soru", "Denklem kurma"],
     ["s01", "s02", "s03", "y01", "y02", "y03", "y04", "y06"]),
    ("Paragraf yapısı ve problemler",
     ["Cümle sıralama, yer değiştirme, akışı bozan cümle (sözel 9–18)", "Uzun metin: günde 2 blok, süreli"],
     ["Sayı-kesir, yaş, yüzde, oran-orantı problemleri", "Cumartesi: ilk tam deneme (150 dk) ve analiz"],
     ["s05", "s06", "s07", "y10", "y11"]),
    ("Sözel mantık ve sayısal mantık",
     ["Sözel mantık: sıralama ve koşullu kurgu (sözel 43–50)", "Her gün 20 paragraf devam"],
     ["Sayısal mantık ve ortak öncüllü bloklar", "Tanımlı işlem ve grafik-tablo"],
     ["s08", "s09", "y16", "y09", "y13"]),
    ("Deneme ve tekrar",
     ["Üç tam deneme, sınav saatinde", "Her denemenin ertesi günü: yanlışların konu dökümü"],
     ["Yalnız yanlış çıkan konulara dönüş", "Son 3 gün: hafif tekrar ve uyku düzeni"], []),
]

PROGRAM_2 = [
    ("Paragrafın temeli", ["Her gün 25 paragraf: önce konu, sonra ana düşünce; süre tut", "Yardımcı düşünce, 'değinilmemiştir', kesin çıkarım"],
     ["Sayılar, kesir ve ondalık, üslü ve köklü sayılar"], ["s01", "s02", "y01", "y02", "y03", "y04"]),
    ("Boşluk doldurma, anlatım, denklemler", ["Boşluk doldurma ve kesin çıkarım (sözel 1–8)", "Anlatım biçimleri ve yazar tutumu"],
     ["Çarpanlara ayırma, denklem kurma", "Eşitsizlik, mutlak değer"], ["s03", "s04", "y05", "y06", "y07"]),
    ("Paragraf yapısı ve problemler", ["Cümle sıralama (9–12), yer değiştirme ve akışı bozan cümle (13–18)", "Sınav başına ~10 soru: en verimli sözel konu"],
     ["Sayı-kesir, yaş, yüzde, kâr-zarar, oran-orantı", "Cumartesi: ilk tam deneme (150 dk) ve analiz"], ["s05", "s06", "y10", "y11"]),
    ("Uzun metin ve sayısal mantık", ["Uzun metin blokları (29–42): metni bir kez oku, soruları seri çöz", "Günde 2 uzun metin bloğu, süreli"],
     ["Sayısal mantık ve ortak öncüllü bloklar: sınav başına ~11 soru", "Tanımlı işlem ve kümeler"], ["s07", "y16", "y09"]),
    ("Sözel mantık ve tablo", ["Sözel mantık: sıralama, eşleştirme, koşullu kurgu (43–50)", "Her gün 15 paragraf devam"],
     ["Grafik-tablo yorumlama", "Bölünebilme, EBOB-EKOK"], ["s08", "s09", "y13", "y08"]),
    ("Geometri seçici + deneme", ["İki tam sözel test, süreli (60 dk)", "Hata defterinden paragraf tekrarı"],
     ["Üçgen ve dörtgen temelleri: yalnız kural + kolay soru", "Hareket ve temel olasılık", "Cumartesi: tam deneme"], ["y14", "y15", "y12"]),
    ("Deneme haftası", ["Üç tam deneme, sınav saatinde (10.15)", "Her denemenin ertesi günü: yanlışların konu dökümü"],
     ["Yalnız yanlış çıkan konulara dönüş", "Süre dağılımını kontrol et: sözel önce mi, sayısal önce mi?"], []),
    ("Son hafta", ["Yeni konu yok; hata defteri ve kısa paragraf setleri", "Bir hafif deneme, sınavdan en geç 3 gün önce"],
     ["Sınav giriş belgesini ÖSYM AİS'ten al, sınav yerini önceden gör", "Kimlik, kurşun kalem, silgi; son iki gün uyku düzeni"], []),
]

PROGRAM_3 = [
    ("Ana düşünce ve sayılar", ["Paragrafta konu, ana düşünce, başlık; günde 25 paragraf", "Cümle boşluğu doldurma (sözel 1–5)"],
     ["Sayı kümeleri, basamak, tek-çift, faktöriyel", "Kesir ve ondalık işlemleri"], ["s01", "y01", "y02"]),
    ("Çıkarım ve üslü-köklü", ["Yardımcı düşünce, 'değinilmemiştir' soruları", "Kesin çıkarım (sözel 6–8): 'kesinlikle' ile 'olabilir' farkı"],
     ["Üslü ve köklü sayılar", "Çarpanlara ayırma, özdeşlikler"], ["s02", "s03", "y03", "y04", "y05"]),
    ("Anlatım ve denklemler", ["Anlatım biçimleri, yazar tutumu", "Süreli paragraf: 20 soru / 25 dk"],
     ["Denklem, eşitsizlik, mutlak değer", "Bölünebilme, EBOB-EKOK"], ["s04", "y06", "y07", "y08"]),
    ("Cümle sıralama ve problemler", ["Cümle sıralama (sözel 9–12): ilk cümle, bağlaç ve zamir ipuçları"],
     ["Sayı-kesir ve yaş problemleri", "Kümeler ve tanımlı işlem"], ["s05", "y10", "y09"]),
    ("Yer değiştirme ve yüzde", ["Cümle yer değiştirme (13–15)", "Anlam akışını bozan cümle (16–18)"],
     ["Yüzde, indirim, zam, kâr-zarar", "Oran-orantı"], ["s06", "y11"]),
    ("Uzun metin ve hareket", ["Uzun metin (29–42): günde 2 blok, süreli", "Cumartesi: ilk tam deneme (150 dk) ve analiz"],
     ["Hareket, işçi-havuz, temel olasılık"], ["s07", "y12"]),
    ("Sözel mantık I ve grafik", ["Sıralama ve eşleştirme bulmacaları, tablo şablonu", "Her gün 20 paragraf devam"],
     ["Grafik ve tablo yorumlama"], ["s08", "y13"]),
    ("Sözel mantık II ve üçgenler", ["Koşullu kurgu: 'kesin doğru', 'olabilir', 'hangisi bilinirse'"],
     ["Açılar, üçgen, Pisagor, özel üçgenler"], ["s09", "y14"]),
    ("Sayısal mantık ve dörtgenler", ["Tam sözel test, süreli (60 dk)", "Zayıf bant analizi: en çok yanlış hangi aralıkta?"],
     ["Sayısal mantık ve ortak öncüllü bloklar", "Dörtgen ve çember temelleri"], ["y16", "y15"]),
    ("1. deneme haftası", ["İki tam deneme, sınav saatinde", "Her denemenin ertesi günü: yanlışların konu dökümü"],
     ["Hata defteri: sayısal"], []),
    ("2. deneme haftası", ["Üç tam deneme", "Süre dağılımını kontrol et"], ["Yalnız zayıf konulara dönüş"], []),
    ("Son hafta", ["Yeni konu yok; hata defteri ve kısa paragraf setleri", "Bir hafif deneme, sınavdan en geç 3 gün önce"],
     ["Sınav giriş belgesi, kimlik, kalem", "Son iki gün uyku düzeni"], []),
]

PROGRAMLAR = {
    1: dict(baslik="1 aylık ALES çalışma programı", kisa="1 aylık",
            giris="Sınava 4 hafta kaldıysa her konuya yetişmek mümkün değil. Bu plan, en çok soru getiren konulara odaklanır: "
                  "paragrafın bütün tipleri, temel işlemler, problemler, sözel ve sayısal mantık. Geometri bilinçli olarak dışarıda bırakıldı; "
                  "sınav başına ~6 soru getirir ama 4 haftada verimli öğrenilmesi zordur.",
            gunluk="Günde 4 saat: 60 dk paragraf, 75 dk haftanın sözel konusu, 75 dk sayısal, 30 dk hata defteri.",
            haftalar=PROGRAM_1),
    2: dict(baslik="2 aylık ALES çalışma programı", kisa="2 aylık",
            giris="8 haftalık, öncelik sıralı plan. Sıra, son 11 ALES'teki 1100 sorunun konu dağılımına göre kuruldu: "
                  "en çok soru getiren konular önce, az soru getiren ve zaman alan konular seçici. Son iki hafta deneme ve tekrara ayrıldı.",
            gunluk="Günde yaklaşık 3 saat: 45 dk paragraf, 60 dk sözel konu, 60 dk sayısal konu, 15 dk hata defteri.",
            haftalar=PROGRAM_2),
    3: dict(baslik="3 aylık ALES çalışma programı", kisa="3 aylık",
            giris="12 haftalık plan: dokuz hafta konu, üç hafta deneme. Sıfırdan başlayan biri için bütün konulara temel düzeyde yetişir; "
                  "paragraf her gün devam eder, geometri 8. ve 9. haftalarda kural düzeyinde işlenir.",
            gunluk="Günde yaklaşık 3 saat: 45 dk paragraf, 60 dk sözel konu, 60 dk sayısal konu, 15 dk hata defteri.",
            haftalar=PROGRAM_3),
    4: dict(baslik="4 aylık ALES çalışma programı", kisa="4 aylık",
            giris="16 haftalık, dört fazlı plan: paragraf temeli, paragraf yapısı ve uzun metin, sözel mantık ve geometri, deneme. "
                  "Sıfırdan başlayanlar için en rahat tempo; Telegram grubumuzdaki kamp da bu programı izler.",
            gunluk="Günde yaklaşık 3 saat: 45 dk paragraf, 60 dk sözel konu, 60 dk sayısal konu, 15 dk hata defteri.",
            haftalar=None),  # build.py program16.json'dan doldurur
}

REHBER = """
<p>ALES'e hiç bilmeden başlamak korkutucu görünür: 100 soru, 150 dakika, iki ayrı test. Ama sınavın yapısı her yıl şaşırtıcı ölçüde aynıdır.
Neyin kaç soru getirdiğini bilen biri, sıfırdan başlasa bile çalışma zamanını doğru yere harcar. Bu rehber, son 11 ALES'teki 1100 sorunun
konu dağılımına dayanarak bunu adım adım anlatıyor.</p>

<h2>1. Önce sınavı tanı</h2>
<ul class="liste">
<li><b>İki test:</b> 50 soruluk Sözel ve 50 soruluk Sayısal. Süre ikisi için toplam 150 dakika; hangisinden başlayacağın sana kalmış.</li>
<li><b>Net:</b> Dört yanlış bir doğruyu götürür. Emin olmadığın soruyu boş bırakmak çoğu zaman daha iyidir.</li>
<li><b>Puan türleri:</b> Sözel, Sayısal ve Eşit Ağırlık. Başvuracağın program hangi puan türünü istiyorsa ağırlığın o teste kayar; ama diğer test de puanına katkı yapar, sıfır bırakılmamalı.</li>
</ul>

<h2>2. Puanı getiren yer: paragraf</h2>
<p>Sözel testteki soruların yaklaşık <b>%72'si paragraf temellidir</b>: ana düşünce, çıkarım, cümle sıralama, akışı bozan cümle, uzun metin. Yani Sözel'in çoğu
"bir metni doğru okumak" becerisine dayanır ve bu beceri her gün çalışınca gelişir. Sıfırdan başlıyorsan ilk iş, her gün <b>20–25 paragraf</b>
çözmeyi alışkanlık hâline getirmektir. İlk haftalarda süre tutma; doğru düşünme yolunu otur. Üçüncü haftadan sonra süreye geç: 20 paragraf, 25 dakika.</p>
<p>Başlangıç sırası: <a href="../dersler/paragrafta-ana-dusunce-konu-ve-baslik/">ana düşünce</a> →
<a href="../dersler/yardimci-dusunce-ve-cikarim/">yardımcı düşünce ve çıkarım</a> →
<a href="../dersler/cumle-siralama/">cümle sıralama</a> → <a href="../dersler/uzun-metin-bloklari/">uzun metin</a>.</p>

<h2>3. Sayısal'da sıfırdan: önce temel, sonra mantık</h2>
<p>Sayısal testin en büyük tek konusu <b>sayısal mantık</b>tır (sınav başına ortalama 11 soru). Bu sorular ileri matematik istemez;
kuralı okuyup uygulamayı ister. Ama temel işlemlerde hız yoksa sayısal mantık da yavaş gider. Bu yüzden sıra şöyle olmalı:</p>
<ol>
<li><b>Temel işlemler ve sayılar</b> (ilk 2 hafta): kesir, üslü, köklü sayılar, basamak, tek-çift. Kolay puandır; sınavın ilk soruları buradan gelir.</li>
<li><b>Denklem ve problemler</b>: sayı-kesir, yaş, yüzde, oran-orantı. Problemlerin hepsi "metni denkleme çevirmek" becerisidir.</li>
<li><b>Sayısal mantık ve grafik-tablo</b>: kural tanımlı bloklar, tablo okuma.</li>
<li><b>Geometri en sona</b>: sınav başına ~6 soru getirir ama öğrenmesi uzundur. Zamanın azsa temel kuralları (iç açılar, Pisagor, alan) öğren, gerisini bırak.</li>
</ol>

<h2>4. Günlük düzen</h2>
<p>Günde 3 saat, sıfırdan başlayan biri için 3–4 ayda sınava hazır olmaya yeter. Önerilen bölünüş:</p>
<ul class="liste">
<li><b>45 dk paragraf</b> (her gün, istisnasız)</li>
<li><b>60 dk haftanın sözel konusu:</b> önce dersi oku, sonra yalnız o tipte soru çöz</li>
<li><b>60 dk haftanın sayısal konusu</b></li>
<li><b>15 dk hata defteri:</b> bugün yanlış yaptığın her sorunun nedenini tek cümleyle yaz ("'kesinlikle' sözcüğünü atladım", "yüzdeyi yanlış tabana uyguladım")</li>
</ul>

<h2>5. Deneme ne zaman başlar?</h2>
<p>İlk tam denemeyi konu çalışmasının ortasında çöz (4 aylık planda 8. hafta civarı); amaç puan değil, süreyi görmek. Son 3–4 haftada her hafta
2–3 deneme çöz ve her birinin ertesi günü yanlışları konulara göre say. En çok yanlış çıkan iki konu, o haftanın tekrar konusu olur.
Çıkmış soruları <a href="https://www.osym.gov.tr/">ÖSYM'nin sitesinden</a> ücretsiz çözebilirsin; en gerçekçi deneme onlardır.</p>

<h2>6. Ne kadar sürede hazırlanılır?</h2>
<p>Sınava kalan süreye göre hazır planlar: <a href="../ales-calisma-programi/1-aylik/">1 aylık</a>,
<a href="../ales-calisma-programi/2-aylik/">2 aylık</a>, <a href="../ales-calisma-programi/3-aylik/">3 aylık</a> ve
<a href="../ales-calisma-programi/4-aylik/">4 aylık</a>. Sıfırdan başlıyorsan ve zamanın varsa 3–4 aylık planı seç.</p>

<h2>Sık yapılan hatalar</h2>
<ul class="liste">
<li><b>Paragrafı "zaten Türkçe biliyorum" diye ertelemek.</b> Paragraf soruları dikkat ve yöntem ister; her gün çalışılmadan oturmaz.</li>
<li><b>Geometriye ilk haftalarda gömülmek.</b> Az soru getiren ve zaman alan konuya erken başlamak, kolay puanları kaçırtır.</li>
<li><b>Yalnızca soru çözüp yanlışlara bakmamak.</b> Net, yanlışın nedenini bulunca artar.</li>
<li><b>Sınav saatinde hiç deneme çözmemek.</b> Son haftalarda denemeleri sınav saatinde (10.15) çöz.</li>
</ul>
"""
