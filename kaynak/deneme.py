"""Haftalık mini deneme (/ales-deneme/): kampın biten her haftasının Günün Sorusu'ları (7 sayısal + 7 sözel) süreli deneme olur.
Yalnız günü geçmiş (çözümü yayımlanmış) sorular kullanılır; bot bankasının gelecek günleri açığa çıkmaz. Süre ALES'in soru başına
süresiyle orantılıdır (100 soru / 150 dk → 14 soru / 21 dk); 4 yanlış 1 doğruyu götürür. Cevaplar ve sonuç yalnız tarayıcıda (localStorage).
JavaScript düz metin sabitidir (f-string değil); DHBT - MBSTS/site/kaynak/deneme.py'deki betiğin ALES uyarlaması.
"""
import json

SURE_SORU = 1.5  # dakika (ALES: 150 dk / 100 soru)

CSS = """.deneme .dsoru{margin:1.1em 0;padding-top:1em;border-top:1px dashed var(--cizgi);display:grid;gap:10px}.deneme .dsoru p{margin:0;line-height:1.7}
.dsik{list-style:none;padding:0;margin:0;display:grid;gap:7px}
.dsik button{width:100%;text-align:left;font:inherit;font-size:16px;line-height:1.5;padding:9px 12px;border:1px solid var(--cizgi);border-radius:8px;background:var(--yuzey);cursor:pointer;color:var(--murekkep)}
.dsik button:hover:not([disabled]){border-color:var(--vurgu)}.dsik button b{display:inline-block;width:1.6em;color:var(--soluk)}
.dsik button.secili{background:var(--vurgu-acik);border-color:var(--vurgu);font-weight:600}
.dsik button.dogru{background:rgba(47,125,79,.14);border-color:var(--iyi)}.dsik button.yanlis{background:rgba(190,50,50,.13);border-color:#c0392b}
.dsik button[disabled]{cursor:default}.daciklama{padding:12px 14px;border-radius:6px;background:var(--vurgu-acik);display:grid;gap:8px}
.dbos{font-size:14px;color:var(--soluk)}.deneme h2.dbolum{margin-top:1.4em}
.dbaslat,.dsonuc{margin:1.2em 0;padding:18px clamp(14px,3vw,24px);background:var(--yuzey);border:1px solid var(--cizgi);border-radius:10px;display:grid;gap:10px}
.dbaslat ul{margin:0;padding-left:1.2em;display:grid;gap:5px}.dbuyuk{font:inherit;font-weight:700;font-size:17px;padding:11px 22px;border-radius:6px;border:0;background:var(--vurgu);color:#fff;cursor:pointer;justify-self:start}
.dcubuk{position:fixed;left:0;right:0;bottom:0;z-index:20;background:#1f4e5f;color:#fff;padding:9px 16px;display:flex;gap:14px;align-items:center;justify-content:center;flex-wrap:wrap;font-size:15.5px;box-shadow:0 -2px 10px rgba(0,0,0,.2)}
.dcubuk b{font-variant-numeric:tabular-nums;font-size:17px}.dcubuk button{font:inherit;font-weight:700;padding:6px 16px;border-radius:6px;border:0;background:#fff;color:#1f4e5f;cursor:pointer}
.dcubuk[hidden]{display:none}body.deneme-acik{padding-bottom:64px}.dcubuk.az b.dkalan{color:#ffd54f}
.dsonuc h2{margin:0}.dsonuc .dnet{font-size:1.6em;font-weight:700;color:var(--vurgu-ink)}.dsonuc table{border-collapse:collapse;width:100%}
.dsonuc th,.dsonuc td{border:1px solid var(--cizgi);padding:6px 10px;text-align:left}.dsonuc ul{margin:0;padding-left:1.2em}
.dtekrar{font:inherit;font-size:14px;background:none;border:0;color:var(--soluk);text-decoration:underline;cursor:pointer;padding:0}
.dliste{list-style:none;padding:0;display:grid;gap:8px;grid-template-columns:repeat(auto-fill,minmax(230px,1fr))}
.dliste a{display:block;padding:12px 14px;border:1px solid var(--cizgi);border-radius:8px;background:var(--yuzey);text-decoration:none;color:var(--murekkep)}
.dliste a:hover{border-color:var(--vurgu)}.dliste b{display:block;font-size:17px;color:var(--vurgu-ink)}.dliste span{font-size:14.5px;color:var(--soluk)}
.dliste span.bitti{color:var(--iyi);font-weight:600}"""

JS = """<script>
(function(){
  var k=document.querySelector('.deneme');if(!k)return;
  var anahtar=k.dataset.anahtar,sure=+k.dataset.sure*60,ceza=+k.dataset.ceza,D={};
  try{D=JSON.parse(localStorage.getItem(anahtar)||'{}')||{}}catch(e){}
  D.c=D.c||{};
  var sorular=[].slice.call(k.querySelectorAll('.dsoru')),govde=k.querySelector('.dgovde'),cubuk=k.querySelector('.dcubuk'),
      kalanY=k.querySelector('.dkalan'),sayY=k.querySelector('.dsay'),sonucY=k.querySelector('.dsonuc'),sayac=null;
  function kaydet(){try{localStorage.setItem(anahtar,JSON.stringify(D))}catch(e){}}
  function tr(n){return n.toLocaleString('tr-TR',{maximumFractionDigits:2})}
  function isaretle(){sorular.forEach(function(s,i){s.querySelectorAll('.dsik button').forEach(function(b,j){b.classList.toggle('secili',D.c[i]===j)})});
    sayY.textContent=Object.keys(D.c).length+' / '+sorular.length}
  function zaman(){var kalan=Math.max(0,Math.round(sure-(Date.now()-D.bas)/1000));
    kalanY.textContent=Math.floor(kalan/60)+':'+('0'+kalan%60).slice(-2);cubuk.classList.toggle('az',kalan<=180);
    if(kalan<=0)bitir(true)}
  function ac(){k.querySelector('.dbaslat').hidden=true;govde.hidden=false;
    if(!D.bitti){cubuk.hidden=false;document.body.classList.add('deneme-acik');isaretle();zaman();sayac=setInterval(zaman,1000)}}
  function hesapla(){var R={},bol={};
    sorular.forEach(function(s,i){var b=s.dataset.bolum,d=s.dataset.ders,c=D.c[i],dg=+s.dataset.dogru;
      bol[b]=bol[b]||{d:0,y:0,b:0};R[d]=R[d]||{ad:s.dataset.dersAd,d:0,y:0,b:0,konu:{}};
      var t=c===undefined?'b':(c===dg?'d':'y');bol[b][t]++;R[d][t]++;
      if(t!=='d')R[d].konu[s.dataset.url]=s.dataset.konuAd});
    return {bol:bol,ders:R}}
  function goster(){var H=hesapla(),toplam=0,dogru=0,satir='',konular='';
    Object.keys(H.bol).forEach(function(b){var x=H.bol[b],net=x.d-(ceza?x.y/ceza:0);toplam+=net;dogru+=x.d;
      satir+='<tr><td>'+b+'</td><td>'+x.d+'</td><td>'+x.y+'</td><td>'+x.b+'</td>'+(ceza?'<td><b>'+tr(net)+'</b></td>':'')+'</tr>'});
    var ders='';Object.keys(H.ders).forEach(function(d){var x=H.ders[d];ders+='<tr><td>'+x.ad+'</td><td>'+x.d+'</td><td>'+x.y+'</td><td>'+x.b+'</td></tr>';
      Object.keys(x.konu).forEach(function(u){konular+='<li><a href="'+u+'">'+x.konu[u]+'</a></li>'})});
    var dk=D.sure?Math.max(1,Math.round(D.sure/60)):null;
    sonucY.innerHTML='<h2>Sonucun</h2><p class="dnet">'+(ceza?tr(toplam)+' net':dogru+' / '+sorular.length+' doğru')+'</p>'
      +(dk?'<p>Süre: '+dk+' dakika'+(D.dolan?' (süre doldu)':'')+'</p>':'')
      +'<div><table><thead><tr><th>Test</th><th>Doğru</th><th>Yanlış</th><th>Boş</th>'+(ceza?'<th>Net</th>':'')+'</tr></thead><tbody>'+satir+'</tbody></table></div>'
      +'<h3>Konulara göre</h3><div><table><thead><tr><th>Konu</th><th>Doğru</th><th>Yanlış</th><th>Boş</th></tr></thead><tbody>'+ders+'</tbody></table></div>'
      +(konular?'<h3>Tekrar etmen gereken konular</h3><p>Yanlış ya da boş bıraktığın soruların konu anlatımları:</p><ul>'+konular+'</ul>':'<p>Bütün soruları doğru cevapladın, tebrikler!</p>')
      +'<p>Aşağıda her sorunun doğru cevabı ve çözümü var. <button type="button" class="dtekrar">Denemeyi sıfırla ve yeniden çöz</button></p>';
    sonucY.hidden=false;
    sonucY.querySelector('.dtekrar').addEventListener('click',function(){if(confirm('Bu denemedeki cevapların ve sonucun silinsin mi?')){try{localStorage.removeItem(anahtar)}catch(e){}location.reload()}});
    sorular.forEach(function(s,i){var dg=+s.dataset.dogru;s.querySelectorAll('.dsik button').forEach(function(b,j){b.disabled=true;b.classList.remove('secili');
      if(j===dg)b.classList.add('dogru');else if(j===D.c[i])b.classList.add('yanlis')});
      if(D.c[i]===undefined)s.querySelector('.dbos').hidden=false;s.querySelector('.daciklama').hidden=false});
    return {net:toplam,dogru:dogru}}
  function bitir(dolan){if(D.bitti)return;
    if(!dolan){var bos=sorular.length-Object.keys(D.c).length;
      if(!confirm(bos?bos+' soru boş. Denemeyi bitirmek istiyor musun?':'Denemeyi bitirip sonucunu görmek istiyor musun?'))return}
    clearInterval(sayac);D.bitti=1;D.dolan=dolan?1:0;D.sure=Math.min(sure,Math.round((Date.now()-D.bas)/1000));
    var s=goster();D.ozet=ceza?tr(s.net)+' net':s.dogru+' doğru';kaydet();
    cubuk.hidden=true;document.body.classList.remove('deneme-acik');
    if(window.ist){var o=s.dogru/sorular.length;ist('test',o<.5?'0-49':o<.8?'50-79':'80-100')}
    sonucY.scrollIntoView({behavior:'smooth'})}
  sorular.forEach(function(s,i){s.querySelectorAll('.dsik button').forEach(function(b,j){b.addEventListener('click',function(){
    if(D.bitti)return;if(D.c[i]===j)delete D.c[i];else D.c[i]=j;kaydet();isaretle()})})});
  k.querySelector('.dbasla').addEventListener('click',function(){D={bas:Date.now(),c:{}};kaydet();if(window.ist)ist('test-basla');ac();window.scrollTo(0,govde.offsetTop-10)});
  cubuk.querySelector('button').addEventListener('click',function(){bitir(false)});
  if(D.bitti){ac();goster()}else if(D.bas){ac()}
})();
</script>"""

LISTE_JS = """<script>
(function(){document.querySelectorAll('.dliste a[data-anahtar]').forEach(function(a){var D=null;
  try{D=JSON.parse(localStorage.getItem(a.dataset.anahtar)||'null')}catch(e){}
  var s=a.querySelector('span');if(!D||!D.bas)return;
  if(D.bitti){s.textContent='Çözüldü: '+D.ozet;s.className='bitti'}else s.textContent='Devam ediyor';
})})();
</script>"""


def haftalar(YAYIN):
    """Yedi günü de yayımlanmış kamp haftaları: [(hafta, sayısal sorular, sözel sorular)]."""
    gunler = {}
    for q in YAYIN:
        gunler.setdefault(q["gun"], {})[q["bolum"]] = q
    out, h = [], 1
    while all(g in gunler and len(gunler[g]) == 2 for g in range(7 * h - 6, 7 * h + 1)):
        gs = range(7 * h - 6, 7 * h + 1)
        out.append((h, [gunler[g]["sayisal"] for g in gs], [gunler[g]["sozel"] for g in gs]))
        h += 1
    return out


def sayfalar(g):
    esc, sayfa, yaz, kirinti, DERS, BASE, tg_kutu = g["esc"], g["sayfa"], g["yaz"], g["kirinti"], g["DERS"], g["BASE"], g["tg_kutu"]
    hf = haftalar(g["YAYIN"])
    yollar = []

    def soru(i, test, q):
        metin = ""
        if q.get("metin"):
            metin = (f'<pre class="veri">{esc(q["metin"])}</pre>' if q["bolum"] == "sayisal"
                     else "".join(f"<p>{esc(p)}</p>" for p in q["metin"].split("\n") if p.strip()))
        siklar = "".join(f'<li><button type="button"><b>{h})</b> {esc(t)}</button></li>' for h, t in zip("ABCDE", q["siklar"]))
        coz = "".join(f"<p>{esc(p)}</p>" for p in q["cozum"].split("\n") if p.strip())
        d = DERS.get(q["ders"]) if q.get("ders") else None
        url = f'../../dersler/{d["slug"]}/' if d else f'../../sorular/{q["slug"]}/'
        konu_ad = d["baslik"] if d else q["temiz_konu"]
        ders_bag = f' · Konu anlatımı: <a href="{url}">{esc(konu_ad)}</a>' if d else ""
        return (f'<div class="dsoru" data-dogru="{int(q["dogru"])}" data-bolum="{test}" data-ders="{esc(q.get("ders") or q["slug"])}" '
                f'data-ders-ad="{esc(konu_ad)}" data-url="{url}" data-konu-ad="{esc(konu_ad)}">'
                f'<p><b>{i}.</b></p>{metin}<p class="kok">{esc(q["soru"])}</p><ol class="dsik">{siklar}</ol>'
                f'<p class="dbos" hidden>Bu soruyu boş bıraktın.</p><div class="daciklama" hidden><p><b>Cevap {"ABCDE"[q["dogru"]]}.</b></p>{coz}'
                f'<p><a href="../../sorular/{q["slug"]}/">Sorunun sayfası</a>{ders_bag}</p></div></div>')

    for n, say, soz in hf:
        adet = len(say) + len(soz)
        dk = round(adet * SURE_SORU)
        yol = f"ales-deneme/{n}/"
        parca = [f'<h2 class="dbolum">Sayısal test (1–{len(say)}. sorular)</h2>']
        parca += [soru(i, "Sayısal", q) for i, q in enumerate(say, 1)]
        parca.append(f'<h2 class="dbolum">Sözel test ({len(say) + 1}–{adet}. sorular)</h2>')
        parca += [soru(i, "Sözel", q) for i, q in enumerate(soz, len(say) + 1)]
        konular = ", ".join(sorted({q["temiz_konu"] for q in say + soz}))
        sonraki = f' · <a href="../{n + 1}/">Mini deneme {n + 1}</a>' if n < len(hf) else ""
        govde = f"""
<nav class="iz"><a href="../../">Ana sayfa</a> › <a href="../">ALES deneme</a> › Mini deneme {n}</nav>
<header class="baslik"><h1>ALES mini deneme {n}: {adet} soru, {dk} dakika</h1>
<p class="giris">Kampın {n}. haftasının sayısal ve sözel soruları süreli bir mini deneme olarak. ALES'teki gibi önce sayısal, sonra sözel test.</p></header>
<section class="deneme" data-anahtar="deneme:ales:{n}" data-sure="{dk}" data-ceza="4">
<div class="dbaslat">
<p><b>Nasıl çözülür?</b></p>
<ul><li>{adet} soru, {dk} dakika (ALES'te soru başına düşen süre kadar). <b>4 yanlış 1 doğruyu götürür</b>; hiç fikrin olmayan soruyu boş bırak.</li>
<li>Başla'ya dokununca süre işlemeye başlar. Bir seçeneğe dokunarak işaretle; aynı seçeneğe yeniden dokunursan işaret kalkar.</li>
<li>Sayfayı kapatsan da cevapların ve kalan süren bu tarayıcıda saklanır. Süre dolunca deneme kendiliğinden biter.</li>
<li>Bitirince sayısal ve sözel netini, konulara göre sonucunu ve her sorunun çözümünü görürsün.</li></ul>
<p><button type="button" class="dbuyuk dbasla">Başla ({dk} dakika)</button></p>
</div>
<div class="dsonuc" hidden></div>
<div class="dgovde" hidden>{"".join(parca)}</div>
<div class="dcubuk" hidden>Kalan süre <b class="dkalan">–</b> · Cevaplanan <b class="dsay">–</b> <button type="button">Bitir</button></div>
</section>
<p class="m">Sorular ALES Kampı'nın özgün sorularıdır (Telegram grubundaki Günün Sorusu); ÖSYM'nin ya da yayınevlerinin sorusu değildir. Bu denemenin konuları: {esc(konular)}. Bütün denemeler: <a href="../">ALES deneme</a>{sonraki}</p>
<style>{CSS}</style>{JS}"""
        baslik = f"ALES Mini Deneme {n} ({adet} Soru, {dk} Dakika, Online)"
        acik = f"ALES mini deneme {n}: {len(say)} sayısal + {len(soz)} sözel özgün soru, {dk} dakika, süreli ve online. Bitirince netini, konu konu sonucunu ve çözümleri gör."
        yaz(yol, sayfa(yol, baslik, acik, govde, "../../",
                       [kirinti(("ALES Kampı", BASE + "/"), ("ALES deneme", BASE + "/ales-deneme/"), (f"Mini deneme {n}", BASE + "/" + yol))], "ales-deneme/"))
        yollar.append(yol)

    liste = "".join(f'<li><a href="{n}/" data-anahtar="deneme:ales:{n}"><b>Mini deneme {n}</b><span>Çözülmedi</span></a></li>' for n, _, _ in hf)
    toplam = sum(len(a) + len(b) for _, a, b in hf)
    sss_html, sss_ld = g["sss"]([
        ("ALES mini denemesi kaç soru, kaç dakika?", f"Her mini deneme 7 sayısal ve 7 sözel olmak üzere 14 soru ve {round(14 * SURE_SORU)} dakikadır. Süre, ALES'te soru başına düşen süreyle orantılıdır (100 soru, 150 dakika). 4 yanlış 1 doğruyu götürür."),
        ("Denemelerdeki sorular nereden?", "Telegram grubumuzda her gün sorulan Günün Sorusu'ndan. Sorular ALES Kampı'nın özgün sorularıdır; ÖSYM'nin çıkmış sorularını ya da yayınevlerinin sorularını kullanmıyoruz."),
        ("Yeni deneme ne zaman eklenir?", "Kampın her haftası bitip o haftanın son sorusunun çözümü grupta paylaşıldıktan sonra, o haftanın 14 sorusu yeni bir mini deneme olarak eklenir."),
        ("Tam ALES denemesi var mı?", "Şimdilik yok. Mini denemeler gerçek sınavın soru tipini, sırasını (önce sayısal, sonra sözel) ve soru başına süresini örnek alır; puanını görmek için netlerini puan hesaplama sayfasına girebilirsin."),
    ])
    govde = f"""
<nav class="iz"><a href="../">Ana sayfa</a> › ALES deneme</nav>
<header class="baslik"><h1>ALES deneme: haftalık süreli mini denemeler</h1>
<p class="giris">{len(hf)} mini deneme, toplam {toplam} özgün soru. Her deneme 7 sayısal + 7 sözel soru ve {round(14 * SURE_SORU)} dakika; bitirince sayısal ve sözel netini, konu konu sonucunu ve çözümleri görürsün. Kampın her haftası bitince yeni bir deneme eklenir. Üyelik gerekmez.</p></header>
<section><h2>Mini denemeler</h2>
<ul class="dliste">{liste}</ul>
<p class="m">Sonuçların yalnız bu tarayıcıda saklanır; sunucuya gönderilmez.</p></section>
<div class="govde rehber">
<h2>Mini denemeler nasıl hazırlandı?</h2>
<p>Her mini deneme, Telegram grubumuzda bir hafta boyunca sorulan Günün Sorusu'ndan oluşur: 7 sayısal ve 7 sözel soru. Sorular ALES Kampı'nın özgün sorularıdır; ALES'teki soru tiplerini ve zorluk düzeyini örnek alır, ÖSYM'nin ya da yayınevlerinin sorusu değildir. Sıra ALES'teki gibidir: önce sayısal, sonra sözel test.</p>
<p>Süre soru başına 1,5 dakikadır (ALES: 100 soru, 150 dakika) ve <b>4 yanlış 1 doğruyu götürür</b>. Bitirince sayısal ve sözel netini ayrı ayrı görürsün; bu netlerle yaklaşık puanını <a href="../ales-puan-hesaplama/">ALES puan hesaplama</a> sayfasında hesaplayabilirsin. 14 soruluk denemenin neti tam sınavın netini doğrudan göstermez, eğilimi gösterir.</p>
<h2>Denemeden verim almak için</h2>
<ul><li><b>Gerçek sınav gibi çöz.</b> Ara vermeden, süreyi durdurmadan.</li>
<li><b>Boş bırakma kararını denemede öğren.</b> Hiç fikrin olmayan soruyu boş bırak, iki seçeneğe indirebildiğin soruyu işaretle.</li>
<li><b>Sonuçta konuya bak.</b> "Tekrar etmen gereken konular" listesi doğrudan konu anlatımına götürür.</li></ul>
<p>İlgili: <a href="../sorular/">Çözümlü sorular</a> · <a href="../konu-analizi/">ALES soru dağılımı</a> · <a href="../ales-calisma-programi/">Çalışma programları</a></p>
</div>
{tg_kutu()}
{sss_html}
<style>{CSS}</style>{LISTE_JS}"""
    yaz("ales-deneme/", sayfa("ales-deneme/", f"ALES Deneme Çöz: Online, Süreli Mini Denemeler ({len(hf)} Deneme)",
                              f"Ücretsiz online ALES denemesi: {len(hf)} süreli mini deneme, her biri 7 sayısal + 7 sözel özgün soru ve {round(14 * SURE_SORU)} dakika. Net, konu konu sonuç ve çözümler.",
                              govde, "../", [kirinti(("ALES Kampı", BASE + "/"), ("ALES deneme", BASE + "/ales-deneme/")), sss_ld], "ales-deneme/"))
    return ["ales-deneme/"] + yollar
