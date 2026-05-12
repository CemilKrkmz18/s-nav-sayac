import json
import threading
import os
import random
from datetime import datetime, timezone, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ── Flask (Render uyku modunu önler) ─────────────────────────────────────────
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Bot çalışıyor! 🤖"

def flask_calistir():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

# ── Ayarlar ───────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 1110751204
BILDIRIM_SAATI = 8
BILDIRIM_DAKIKA = 0
VERI_DOSYASI = "veri.json"
TR = timezone(timedelta(hours=3))

def simdi_tr():
    return datetime.now(TR).replace(tzinfo=None)

# ── Sınavlar ──────────────────────────────────────────────────────────────────
SINAVLAR = {
    "YKS TYT": "2026-06-21 10:15",
    "YKS AYT": "2026-06-22 10:15",
    "KPSS":    "2026-09-06 10:15",
}

# ── Puan katsayıları ──────────────────────────────────────────────────────────
TYT_K = {"Türkçe": 2.83, "Sosyal Bilimler": 2.99, "Temel Matematik": 3.28, "Fen Bilimleri": 2.53}
TYT_B = 145.47

SAY_K = {"Türkçe": 1.20, "Sosyal Bilimler": 1.27, "Temel Matematik": 1.39, "Fen Bilimleri": 1.07,
         "Matematik": 2.89, "Fizik": 2.46, "Kimya": 2.53, "Biyoloji": 2.61}
SAY_B = 132.87

EA_K = {"Türkçe": 1.19, "Sosyal Bilimler": 1.26, "Temel Matematik": 1.38, "Fen Bilimleri": 1.07,
        "Matematik": 2.88, "Edebiyat": 2.94, "Tarih-1": 2.53, "Coğrafya-1": 2.85}
EA_B = 129.34

SOZ_K = {"Türkçe": 1.13, "Sosyal Bilimler": 1.19, "Temel Matematik": 1.31, "Fen Bilimleri": 1.01,
         "Edebiyat": 2.79, "Tarih-1": 2.39, "Coğrafya-1": 2.70,
         "Tarih-2": 3.80, "Coğrafya-2": 2.47, "Felsefe Grubu": 3.76, "DKAB": 2.36}
SOZ_B = 129.61

OBP_KATSAYI = 0.12

# ── Sıralama tabloları ────────────────────────────────────────────────────────
TYT_S = [(490,1000),(480,3000),(470,6000),(460,12000),(450,22000),(440,40000),
         (430,65000),(420,100000),(410,145000),(400,200000),(390,265000),
         (380,340000),(370,425000),(360,520000),(350,620000),(340,730000),
         (330,850000),(320,980000),(310,1120000),(300,1270000),(0,2500000)]

SAY_S = [(490,500),(480,1500),(470,3000),(460,6000),(450,10000),(440,16000),
         (430,25000),(420,37000),(410,52000),(400,72000),(390,97000),
         (380,128000),(370,165000),(360,210000),(350,260000),(340,315000),
         (320,430000),(300,560000),(0,900000)]

EA_S = [(490,500),(480,1500),(470,3000),(460,6000),(450,10000),(440,17000),
        (430,27000),(420,40000),(410,57000),(400,78000),(390,104000),
        (380,136000),(370,174000),(360,218000),(350,268000),(340,325000),
        (320,445000),(300,575000),(0,850000)]

SOZ_S = [(490,300),(480,1000),(470,2200),(460,4500),(450,8000),(440,13000),
         (430,20000),(420,30000),(410,43000),(400,59000),(390,79000),
         (380,103000),(370,132000),(360,165000),(350,203000),(0,350000)]

def tahmini_siralama(puan, tablo):
    for esik, siralama in tablo:
        if puan > esik:
            return f"~{siralama:,}".replace(",", ".")
    return "—"

# ── Bölümler ──────────────────────────────────────────────────────────────────
TYT_BOLUMLER = [("Türkçe",40),("Sosyal Bilimler",20),("Temel Matematik",40),("Fen Bilimleri",20)]
AYT_BOLUMLER = [("Matematik",40),("Fizik",14),("Kimya",13),("Biyoloji",13),
                ("Edebiyat",24),("Tarih-1",10),("Coğrafya-1",6),
                ("Tarih-2",11),("Coğrafya-2",11),("Felsefe Grubu",12),("DKAB",6)]

SINAV_SEC, BOLUM_GIR, OBP_GIR = range(3)

# ── Motivasyon ────────────────────────────────────────────────────────────────
MOTIVASYON = [
    "💪 Her dakika yarının başarısına bir adım!",
    "🔥 Vazgeçmek yok, sen başarabilirsin!",
    "🎯 Odaklan, çalış, kazan. Sıra sende!",
    "⭐ Emek asla boşa gitmez!",
    "🏆 En büyük rakibin dünkü halinden!",
    "🚀 Her gün biraz daha iyi olmak yeterli!",
    "🌟 Zorlu yollar güzel manzaralara çıkar!",
    "✨ Hedefe bir adım daha yakınsın!",
    "📚 Küçük adımlar büyük başarılar getirir!",
    "🌈 Bugünün yorgunluğu yarının gururudur!",
]

# ── İpuçları ──────────────────────────────────────────────────────────────────
IPUCLARI = {
    "YKS TYT": [
        "📐 Her gün en az 20 temel matematik sorusu çöz.",
        "📖 Paragraf sorularında önce soruyu oku, sonra metne dön.",
        "🔢 Formül ezberlemek yerine mantığını anla.",
        "⏱️ Her bölüme kaç dakika ayıracağını belirle.",
        "📝 Yanlışlarını deftere yaz, haftada bir tekrar çöz.",
        "🧠 Fen'de ezber yerine günlük hayatla bağlantı kur.",
        "📊 Harita ve grafik sorularına özellikle çalış.",
        "🎯 Her gün en az bir deneme bölümü çöz.",
        "💡 Dil Bilgisi için cümle örnekleri üret.",
        "🔄 Denemelerin analizini yap, hangi konuda hata yaptığını bul.",
        "📅 Çalışma programı yap ama esnek tut.",
        "🧩 Anlatım bozukluklarına özellikle çalış.",
        "➗ Kesir ve oran-orantı sorularını her gün pratik yap.",
        "🌡️ Fizik formüllerini hangi durumda kullanacağını öğren.",
        "📰 Güncel olayları takip et.",
    ],
    "YKS AYT": [
        "📐 Türev ve integrali birlikte çalış.",
        "📖 Edebiyat: Divan→Tanzimat→Servet-i Fünun→Cumhuriyet.",
        "🧪 Mol hesaplamalarını otomatik hale getir.",
        "🔬 Hücre bölünmesi ve genetiğe öncelik ver.",
        "⚡ Vektör kavramını iyi öğren.",
        "📜 Olayların nedenlerini ve sonuçlarını birlikte öğren.",
        "🗺️ Türkiye haritasını ezberle.",
        "🌍 Felsefe akımlarını temsilcileriyle öğren.",
        "📚 Şair/yazar eserlerini tablo yaparak öğren.",
        "🧮 Logaritma için her gün 10 soru çöz.",
        "🔭 AYT Coğrafya'da astronomi konularına göz at.",
        "💊 Organik bileşikler için fonksiyonel grupları ezberle.",
        "📐 Analitik geometriye özel vakit ayır.",
        "🎭 Divan ve halk şiiri nazım biçimlerini karıştırma.",
        "⚗️ Kimya denklemlerini denkleştirme pratiği yap.",
    ],
    "KPSS": [
        "🏛️ Anayasa konusuna öncelik ver.",
        "📜 Tarihi kronolojik sırayla çalış.",
        "🗺️ İklim tipleri ve bölgesel özelliklere bak.",
        "⚖️ Hukuku ezber değil mantıkla öğren.",
        "📊 Temel matematik konuları yeterli.",
        "🖊️ Cümle tamamlama sorularına özellikle bak.",
        "📅 Atatürk İlkeleri için tarihler önemli.",
        "🧠 Eğitim Bilimleri için kavram haritası yap.",
        "📰 Güncel olayları takip et.",
        "🔄 Çıkmış soruları çözmek en etkili yöntem.",
        "📐 Geometri temel formülleri gözden geçir.",
        "🌐 Temel kurumları iyi öğren.",
        "📚 Mezun olduğun bölümün temel kaynaklarını gözden geçir.",
        "⏱️ Deneme sınavlarında süreyi mutlaka tut.",
        "🎯 Puan türüne göre odaklan.",
    ],
}

# ── Veri işlemleri ────────────────────────────────────────────────────────────
def veri_yukle():
    if os.path.exists(VERI_DOSYASI):
        with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"aboneler": [], "denemeler": {}, "kronometreler": {}}

def veri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)

def deneme_kaydet(chat_id, tur, netler, puan, toplam_net):
    veri = veri_yukle()
    if "denemeler" not in veri:
        veri["denemeler"] = {}
    key = str(chat_id)
    if key not in veri["denemeler"]:
        veri["denemeler"][key] = []
    veri["denemeler"][key].append({
        "tarih": simdi_tr().strftime("%Y-%m-%d %H:%M"),
        "tur": tur,
        "netler": netler,
        "puan": puan,
        "toplam_net": round(toplam_net, 2),
    })
    veri["denemeler"][key] = veri["denemeler"][key][-20:]
    veri_kaydet(veri)

def kullanici_denemeleri(chat_id):
    veri = veri_yukle()
    return veri.get("denemeler", {}).get(str(chat_id), [])

# ── Kronometre veri işlemleri ─────────────────────────────────────────────────
def kronometre_yukle(chat_id):
    """Kullanıcının kronometre verisini döndürür."""
    veri = veri_yukle()
    return veri.get("kronometreler", {}).get(str(chat_id), {
        "durum": "durdu",        # "calisiyor" | "durdu"
        "baslangic": None,       # ISO string — en son başlatıldığı an
        "gecen_sure": 0,         # Daha önce birikmiş saniye (durdurma sonrası)
        "son_bildirim_saati": 0, # Kaçıncı saat bildiriminde kaldık
    })

def kronometre_kaydet(chat_id, veri_k):
    veri = veri_yukle()
    if "kronometreler" not in veri:
        veri["kronometreler"] = {}
    veri["kronometreler"][str(chat_id)] = veri_k
    veri_kaydet(veri)

def kronometre_toplam_saniye(veri_k):
    """Şu anki toplam geçen süreyi saniye cinsinden hesaplar."""
    toplam = veri_k.get("gecen_sure", 0)
    if veri_k.get("durum") == "calisiyor" and veri_k.get("baslangic"):
        baslangic = datetime.fromisoformat(veri_k["baslangic"])
        toplam += (simdi_tr() - baslangic).total_seconds()
    return int(toplam)

def sure_formatla(saniye):
    """Saniyeyi SS:DD:ss formatına çevirir."""
    s = int(saniye)
    saat = s // 3600
    dakika = (s % 3600) // 60
    saniye_k = s % 60
    return f"{saat:02d}:{dakika:02d}:{saniye_k:02d}"

# ── Yardımcı fonksiyonlar ─────────────────────────────────────────────────────
def gunun_ipucu():
    gun_no = simdi_tr().timetuple().tm_yday
    satirlar = ["💡 *Günün Taktikleri*\n"]
    for ad, liste in IPUCLARI.items():
        satirlar.append(f"*{ad}:*\n{liste[gun_no % len(liste)]}")
    return "\n\n".join(satirlar)

def kalan_sure(tarih_str):
    fark = datetime.strptime(tarih_str, "%Y-%m-%d %H:%M") - simdi_tr()
    if fark.total_seconds() <= 0:
        return "✅ Geçti"
    s = int(fark.total_seconds())
    g, h, m = s // 86400, (s % 86400) // 3600, (s % 3600) // 60
    p = []
    if g: p.append(f"*{g}* gün")
    if h: p.append(f"*{h}* saat")
    if m or (not g and not h): p.append(f"*{m}* dk")
    return "⏳ " + " ".join(p) + " kaldı"

def saat_str():
    return simdi_tr().strftime("%H:%M:%S")

def kullanici_adi(user):
    return user.full_name or user.username or str(user.id)

def net(d, y):
    return d - y / 4

def tyt_puan(netler):
    return round(TYT_B + sum(netler[b] * TYT_K.get(b, 0) for b in netler), 2)

def obp_katki(obp_degeri):
    if 50 <= obp_degeri <= 100:
        obp = obp_degeri * 5
    else:
        obp = obp_degeri
    return round(OBP_KATSAYI * obp, 2)

def ayt_puanlar(tyt_n, ayt_n):
    say = SAY_B + sum(tyt_n[b] * SAY_K.get(b, 0) for b in tyt_n)
    for b in ["Matematik","Fizik","Kimya","Biyoloji"]:
        say += ayt_n.get(b, 0) * SAY_K.get(b, 0)

    ea = EA_B + sum(tyt_n[b] * EA_K.get(b, 0) for b in tyt_n)
    for b in ["Matematik","Edebiyat","Tarih-1","Coğrafya-1"]:
        ea += ayt_n.get(b, 0) * EA_K.get(b, 0)

    soz = SOZ_B + sum(tyt_n[b] * SOZ_K.get(b, 0) for b in tyt_n)
    for b in ["Edebiyat","Tarih-1","Coğrafya-1","Tarih-2","Coğrafya-2","Felsefe Grubu","DKAB"]:
        soz += ayt_n.get(b, 0) * SOZ_K.get(b, 0)

    return {"SAY": round(say, 2), "EA": round(ea, 2), "SÖZ": round(soz, 2)}

def sinav_butonlari():
    b = [[InlineKeyboardButton(f"📌 {ad}", callback_data=f"sinav_{ad}")] for ad in SINAVLAR]
    b.append([InlineKeyboardButton("💡 Günün Taktikleri", callback_data="ipucu")])
    b.append([InlineKeyboardButton("🧮 Puan Hesapla", callback_data="puan_menu")])
    b.append([InlineKeyboardButton("⏱️ Kronometre", callback_data="kronometre_menu")])
    return InlineKeyboardMarkup(b)

def detay_metni(ad, mot):
    tarih_str = SINAVLAR[ad]
    tarih = tarih_str.split(" ")[0]
    sure = kalan_sure(tarih_str)
    return f"📌 *{ad}*\n📅 {tarih}\n{sure}\n\n{mot}\n\n🔄 _{saat_str()}_"

def tum_sinavlar():
    s = ["📅 *Geri Sayımlar*\n"]
    for ad, ts in sorted(SINAVLAR.items(), key=lambda x: x[1]):
        s.append(f"• *{ad}* — {ts.split()[0]}\n  {kalan_sure(ts)}")
    return "\n".join(s)

# ── Kronometre klavye ─────────────────────────────────────────────────────────
def kronometre_klavye(durum):
    """Duruma göre kronometre butonlarını oluşturur."""
    if durum == "calisiyor":
        satirlar = [
            [InlineKeyboardButton("⏸️ Durdur", callback_data="krono_durdur")],
            [InlineKeyboardButton("🔄 Yenile", callback_data="krono_yenile")],
            [InlineKeyboardButton("🗑️ Sıfırla", callback_data="krono_sifirla")],
            [InlineKeyboardButton("🔙 Geri", callback_data="geri")],
        ]
    else:
        satirlar = [
            [InlineKeyboardButton("▶️ Başlat", callback_data="krono_baslat")],
            [InlineKeyboardButton("🗑️ Sıfırla", callback_data="krono_sifirla")],
            [InlineKeyboardButton("🔙 Geri", callback_data="geri")],
        ]
    return InlineKeyboardMarkup(satirlar)

def kronometre_metni(chat_id):
    """Kronometre ekran metnini oluşturur."""
    veri_k = kronometre_yukle(chat_id)
    toplam = kronometre_toplam_saniye(veri_k)
    durum_ikon = "🟢 Çalışıyor" if veri_k["durum"] == "calisiyor" else "🔴 Durdu"
    return (
        f"⏱️ *Kronometre*\n\n"
        f"```\n{sure_formatla(toplam)}\n```\n"
        f"Durum: {durum_ikon}\n\n"
        f"_Her 1 saat dolduğunda bildirim alırsın._\n"
        f"🕐 _{saat_str()}_"
    )

# ── Admin bildirimi ───────────────────────────────────────────────────────────
async def admin_bildir(context, mesaj):
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=mesaj, parse_mode="Markdown")
    except Exception as e:
        print(f"Admin bildirimi hatası: {e}")

# ── Komutlar ──────────────────────────────────────────────────────────────────
async def baslat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    veri = veri_yukle()
    chat_id = update.effective_chat.id
    user = update.effective_user
    if chat_id not in veri["aboneler"]:
        veri["aboneler"].append(chat_id)
        veri_kaydet(veri)
        karsilama = f"👋 *Hoş geldin!* Her sabah {BILDIRIM_SAATI:02d}:{BILDIRIM_DAKIKA:02d}'de bildirim alacaksın.\n\n"
        await admin_bildir(context,
            f"🟢 *Yeni kullanıcı!*\n👤 {kullanici_adi(user)}\n"
            f"🔗 @{user.username or '—'}\n🆔 `{chat_id}`\n"
            f"📊 Toplam: *{len(veri['aboneler'])}*\n🕐 {saat_str()}")
    else:
        karsilama = "✅ Zaten abonesin!\n\n"
    await update.message.reply_text(
        karsilama + "Hangi sınavı görmek istersin?",
        reply_markup=sinav_butonlari(), parse_mode="Markdown")

async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hangi sınavı görmek istersin?", reply_markup=sinav_butonlari())

async def bildirim_iptal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    veri = veri_yukle()
    chat_id = update.effective_chat.id
    user = update.effective_user
    if chat_id in veri["aboneler"]:
        veri["aboneler"].remove(chat_id)
        veri_kaydet(veri)
        await update.message.reply_text("🔕 Bildirimler durduruldu. Tekrar için /start yaz.")
        await admin_bildir(context,
            f"🔴 *Kullanıcı ayrıldı!*\n👤 {kullanici_adi(user)}\n"
            f"🔗 @{user.username or '—'}\n🆔 `{chat_id}`\n"
            f"📊 Kalan: *{len(veri['aboneler'])}*\n🕐 {saat_str()}")
    else:
        await update.message.reply_text("Zaten bildirim almıyordun.")

async def test_bildirim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await sabah_bildirimi(context)
    await update.message.reply_text("✅ Test bildirimi gönderildi!")

async def istatistik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    veri = veri_yukle()
    await update.message.reply_text(f"👥 Toplam abone: *{len(veri['aboneler'])}*", parse_mode="Markdown")

async def gecmis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    denemeler = kullanici_denemeleri(chat_id)
    if not denemeler:
        await update.message.reply_text(
            "📭 Henüz kayıtlı deneme yok.\n🧮 Puan hesapla butonundan deneme gir!",
            reply_markup=sinav_butonlari())
        return
    son5 = denemeler[-5:][::-1]
    mesaj = "📋 *Son Denemeler*\n\n"
    for i, d in enumerate(son5, 1):
        mesaj += f"*{i}.* {d['tarih']} — {d['tur']}\n"
        mesaj += f"   Net: `{d['toplam_net']}` | Puan: `{d['puan']}`\n\n"
    await update.message.reply_text(mesaj, parse_mode="Markdown", reply_markup=sinav_butonlari())

async def analiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    denemeler = kullanici_denemeleri(chat_id)
    if len(denemeler) < 2:
        await update.message.reply_text(
            "📊 Analiz için en az 2 deneme gerekli!\n🧮 Puan hesapla butonundan deneme gir.",
            reply_markup=sinav_butonlari())
        return

    mesaj = "📊 *Gelişim Analizi*\n\n"
    for tur in ["TYT", "AYT"]:
        tur_denemeleri = [d for d in denemeler if d["tur"] == tur]
        if len(tur_denemeleri) < 2:
            continue
        mesaj += f"*{tur} Analizi ({len(tur_denemeleri)} deneme):*\n"
        en_iyi = max(tur_denemeleri, key=lambda x: x["toplam_net"])
        en_kotu = min(tur_denemeleri, key=lambda x: x["toplam_net"])
        mesaj += f"🏅 En iyi: `{en_iyi['toplam_net']}` net ({en_iyi['tarih'][:10]})\n"
        mesaj += f"📉 En düşük: `{en_kotu['toplam_net']}` net ({en_kotu['tarih'][:10]})\n"

        if len(tur_denemeleri) >= 4:
            son3 = tur_denemeleri[-3:]
            onceki3 = tur_denemeleri[-6:-3] if len(tur_denemeleri) >= 6 else tur_denemeleri[:-3]
            son3_ort = sum(d["toplam_net"] for d in son3) / len(son3)
            onceki3_ort = sum(d["toplam_net"] for d in onceki3) / len(onceki3)
            fark = son3_ort - onceki3_ort
            trend = f"📈 +{fark:.1f}" if fark > 0 else f"📉 {fark:.1f}"
            mesaj += f"Trend: {trend} net (son 3 ortalama)\n"

        son3_d = tur_denemeleri[-3:]
        bolum_ortalamalari = {}
        for d in son3_d:
            for bolum, net_val in d.get("netler", {}).items():
                if bolum not in bolum_ortalamalari:
                    bolum_ortalamalari[bolum] = []
                bolum_ortalamalari[bolum].append(net_val)

        if bolum_ortalamalari:
            soru_sayilari = dict(TYT_BOLUMLER + AYT_BOLUMLER)
            normalize = {}
            for b, vals in bolum_ortalamalari.items():
                ort = sum(vals) / len(vals)
                maks = soru_sayilari.get(b, 40)
                normalize[b] = ort / maks
            en_zayif = min(normalize, key=normalize.get)
            mesaj += f"⚠️ Zayıf bölüm: *{en_zayif}* (bu hafta önceliklendir!)\n"
        mesaj += "\n"

    await update.message.reply_text(mesaj, parse_mode="Markdown", reply_markup=sinav_butonlari())

# ── Geri sayım butonları ──────────────────────────────────────────────────────
async def buton_tiklandi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ad = query.data[len("sinav_"):]
    if ad not in SINAVLAR:
        await query.edit_message_text("❌ Sınav bulunamadı.")
        return
    mot = random.choice(MOTIVASYON)
    mot_i = MOTIVASYON.index(mot)
    await query.edit_message_text(
        text=detay_metni(ad, mot), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yenile", callback_data=f"yenile_{ad}_{mot_i}")],
            [InlineKeyboardButton("🔙 Geri", callback_data="geri")]
        ])
    )

async def ipucu_tiklandi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text=gunun_ipucu(), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="geri")]])
    )

async def yenile_tiklandi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🔄 Güncellendi!")
    parca = query.data[len("yenile_"):]
    son = parca.rfind("_")
    ad, mot_i = parca[:son], int(parca[son+1:])
    if ad not in SINAVLAR:
        await query.edit_message_text("❌ Sınav bulunamadı.")
        return
    mot = MOTIVASYON[mot_i]
    await query.edit_message_text(
        text=detay_metni(ad, mot), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yenile", callback_data=f"yenile_{ad}_{mot_i}")],
            [InlineKeyboardButton("🔙 Geri", callback_data="geri")]
        ])
    )

async def geri_don(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Hangi sınavı görmek istersin?", reply_markup=sinav_butonlari())

# ── Puan hesaplama ────────────────────────────────────────────────────────────
async def puan_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🧮 *Puan Hesaplama*\n\nHangi sınav?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 TYT", callback_data="hesap_TYT")],
            [InlineKeyboardButton("📝 AYT (SAY/EA/SÖZ)", callback_data="hesap_AYT")],
            [InlineKeyboardButton("🔙 Geri", callback_data="geri")],
        ])
    )
    return SINAV_SEC

async def hesap_sinav_sec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tur = query.data.replace("hesap_", "")
    context.user_data.update({
        "sinav_turu": tur,
        "bolum_index": 0,
        "netler": {},
        "tyt_bolumler": TYT_BOLUMLER,
        "ayt_bolumler": AYT_BOLUMLER,
        "asama": "TYT",
    })
    b, s = TYT_BOLUMLER[0]
    await query.edit_message_text(
        f"📝 *{tur} Hesaplama*\n\n"
        f"{'📋 Önce TYT bölümlerini gir:\n' if tur == 'AYT' else ''}"
        f"TYT 1/{len(TYT_BOLUMLER)}: *{b}* ({s} soru)\n\n"
        f"Doğru yanlış gir: `25 5`",
        parse_mode="Markdown"
    )
    return BOLUM_GIR

async def bolum_gir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    metin = update.message.text.strip()
    try:
        p = metin.split()
        d, y = float(p[0]), float(p[1]) if len(p) > 1 else 0.0
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Format: `25 5`", parse_mode="Markdown")
        return BOLUM_GIR

    tur = context.user_data["sinav_turu"]
    asama = context.user_data["asama"]
    i = context.user_data["bolum_index"]
    bolumler = context.user_data["tyt_bolumler"] if asama == "TYT" else context.user_data["ayt_bolumler"]
    b, s = bolumler[i]

    if d + y > s:
        await update.message.reply_text(f"❌ Max {s} soru. Tekrar:")
        return BOLUM_GIR

    context.user_data["netler"][b] = net(d, y)
    context.user_data["bolum_index"] += 1

    if asama == "TYT" and context.user_data["bolum_index"] >= len(context.user_data["tyt_bolumler"]):
        if tur == "AYT":
            context.user_data["asama"] = "AYT"
            context.user_data["bolum_index"] = 0
            nb, ns = context.user_data["ayt_bolumler"][0]
            await update.message.reply_text(
                f"✅ *{b}*: {context.user_data['netler'][b]:.2f} net\n\n"
                f"✅ TYT bölümleri tamamlandı!\n\n"
                f"📋 Şimdi AYT bölümlerini gir:\n"
                f"AYT 1/{len(context.user_data['ayt_bolumler'])}: *{nb}* ({ns} soru)\n\n"
                f"Doğru yanlış: `25 5`",
                parse_mode="Markdown"
            )
            return BOLUM_GIR
        else:
            await update.message.reply_text(
                f"✅ *{b}*: {context.user_data['netler'][b]:.2f} net\n\n"
                "✅ Tüm bölümler tamamlandı!\n\n"
                "📊 *OBP (Diploma Notu) gir:*\n"
                "• Diploma notu: `85` (50-100 arası)\n"
                "• Direkt OBP: `425` (250-500 arası)\n"
                "• OBP'siz hesapla: `0`",
                parse_mode="Markdown"
            )
            return OBP_GIR

    if asama == "AYT" and context.user_data["bolum_index"] >= len(context.user_data["ayt_bolumler"]):
        await update.message.reply_text(
            f"✅ *{b}*: {context.user_data['netler'][b]:.2f} net\n\n"
            "✅ Tüm bölümler tamamlandı!\n\n"
            "📊 *OBP (Diploma Notu) gir:*\n"
            "• Diploma notu: `85` (50-100 arası)\n"
            "• Direkt OBP: `425` (250-500 arası)\n"
            "• OBP'siz hesapla: `0`",
            parse_mode="Markdown"
        )
        return OBP_GIR

    nb, ns = bolumler[context.user_data["bolum_index"]]
    etiket = "TYT" if asama == "TYT" else "AYT"
    await update.message.reply_text(
        f"✅ *{b}*: {context.user_data['netler'][b]:.2f} net\n\n"
        f"{etiket} {context.user_data['bolum_index']+1}/{len(bolumler)}: *{nb}* ({ns} soru)\n\n"
        f"Doğru yanlış: `25 5`",
        parse_mode="Markdown"
    )
    return BOLUM_GIR

async def obp_gir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    metin = update.message.text.strip()
    try:
        obp_val = float(metin)
    except ValueError:
        await update.message.reply_text("❌ Sayı gir. Örnek: `85` veya `0`", parse_mode="Markdown")
        return OBP_GIR
    context.user_data["obp"] = obp_val
    return await hesaplama_sonuc(update, context)

async def hesaplama_sonuc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tur = context.user_data["sinav_turu"]
    netler = context.user_data["netler"]
    obp_val = context.user_data.get("obp", 0)
    obp_k = obp_katki(obp_val) if obp_val > 0 else 0

    if tur == "TYT":
        tyt_n = {b: netler.get(b, 0) for b, _ in TYT_BOLUMLER}
        puan = tyt_puan(tyt_n)
        puan_obp = round(puan + obp_k, 2)
        toplam = sum(tyt_n.values())
        siralama = tahmini_siralama(puan, TYT_S)
        siralama_obp = tahmini_siralama(puan_obp, TYT_S)

        mesaj = "🎯 *TYT Sonucu*\n\n📊 *Netler:*\n"
        for b, n in tyt_n.items():
            mesaj += f"• {b}: `{n:.2f}`\n"
        mesaj += f"\n📈 Toplam Net: `{toplam:.2f}`\n"
        mesaj += f"🏆 Ham Puan: `{puan}`\n"
        mesaj += f"📊 Sıralama (OBP'siz): `{siralama}`\n"
        if obp_val > 0:
            mesaj += f"\n📋 OBP Katkısı: `+{obp_k}`\n"
            mesaj += f"🏆 Yerleştirme Puanı: `{puan_obp}`\n"
            mesaj += f"📊 Sıralama (OBP'li): `{siralama_obp}`\n"
        mesaj += "\n_⚠️ Tahmindir, resmi değildir._"

        chat_id = update.effective_chat.id
        gecmis_d = kullanici_denemeleri(chat_id)
        onceki = [d for d in gecmis_d if d["tur"] == tur]
        if onceki:
            en_iyi = max(onceki, key=lambda x: x["toplam_net"])
            if toplam > en_iyi["toplam_net"]:
                mesaj += f"\n\n🏅 *Yeni rekor! Önceki: {en_iyi['toplam_net']:.2f} net*"
        bir_hafta_once = simdi_tr().replace(day=max(1, simdi_tr().day - 7))
        gecen_hafta = [d for d in onceki if datetime.strptime(d["tarih"], "%Y-%m-%d %H:%M") >= bir_hafta_once]
        if gecen_hafta:
            gecen_net = sum(d["toplam_net"] for d in gecen_hafta) / len(gecen_hafta)
            fark = toplam - gecen_net
            if fark > 0:
                mesaj += f"\n📈 Geçen haftaya göre *+{fark:.1f} net* artış!"
            elif fark < 0:
                mesaj += f"\n📉 Geçen haftaya göre *{fark:.1f} net* düşüş."
        deneme_kaydet(chat_id, tur, {b: round(n, 2) for b, n in tyt_n.items()}, puan, toplam)

    else:
        tyt_n = {b: netler.get(b, 0) for b, _ in TYT_BOLUMLER}
        ayt_n = {b: netler.get(b, 0) for b, _ in AYT_BOLUMLER}
        tyt_p = tyt_puan(tyt_n)
        puanlar = ayt_puanlar(tyt_n, ayt_n)
        tyt_top = sum(tyt_n.values())
        ayt_top = sum(ayt_n.values())
        tablolar = {"SAY": SAY_S, "EA": EA_S, "SÖZ": SOZ_S}

        mesaj = "🎯 *AYT Sonucu*\n\n"
        mesaj += f"📊 *TYT Netleri:* (toplam: `{tyt_top:.2f}`, puan: `{tyt_p}`)\n"
        for b, n in tyt_n.items():
            mesaj += f"• {b}: `{n:.2f}`\n"
        mesaj += f"\n📊 *AYT Netleri:* (toplam: `{ayt_top:.2f}`)\n"
        for b, n in ayt_n.items():
            mesaj += f"• {b}: `{n:.2f}`\n"
        mesaj += "\n🏆 *Puanlar ve Sıralamalar:*\n"
        for tur_adi, p in puanlar.items():
            s = tahmini_siralama(p, tablolar[tur_adi])
            p_obp = round(p + obp_k, 2)
            s_obp = tahmini_siralama(p_obp, tablolar[tur_adi])
            mesaj += f"\n*{tur_adi}:*\n"
            mesaj += f"  Ham: `{p}` → Sıra: `{s}`\n"
            if obp_val > 0:
                mesaj += f"  OBP'li: `{p_obp}` → Sıra: `{s_obp}`\n"
        if obp_val > 0:
            mesaj += f"\n📋 OBP Katkısı: `+{obp_k}`\n"
        mesaj += "\n_⚠️ Tahmindir, resmi değildir._"

        chat_id = update.effective_chat.id
        gecmis_d = kullanici_denemeleri(chat_id)
        onceki = [d for d in gecmis_d if d["tur"] == tur]
        if onceki:
            en_iyi = max(onceki, key=lambda x: x["toplam_net"])
            if ayt_top > en_iyi["toplam_net"]:
                mesaj += f"\n\n🏅 *Yeni rekor! Önceki: {en_iyi['toplam_net']:.2f} net*"
        bir_hafta_once = simdi_tr().replace(day=max(1, simdi_tr().day - 7))
        gecen_hafta = [d for d in onceki if datetime.strptime(d["tarih"], "%Y-%m-%d %H:%M") >= bir_hafta_once]
        if gecen_hafta:
            gecen_net = sum(d["toplam_net"] for d in gecen_hafta) / len(gecen_hafta)
            fark = ayt_top - gecen_net
            if fark > 0:
                mesaj += f"\n📈 Geçen haftaya göre *+{fark:.1f} net* artış!"
            elif fark < 0:
                mesaj += f"\n📉 Geçen haftaya göre *{fark:.1f} net* düşüş."
        deneme_kaydet(chat_id, tur, {b: round(n, 2) for b, n in {**tyt_n, **ayt_n}.items()},
                      puanlar.get("SAY", 0), ayt_top)

    mesaj += "\n\n_/gecmis → geçmiş denemeler | /analiz → gelişim_"
    await update.message.reply_text(
        mesaj, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Ana Menü", callback_data="geri")]])
    )
    context.user_data.clear()
    return ConversationHandler.END

async def hesap_iptal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ İptal edildi.", reply_markup=sinav_butonlari())
    return ConversationHandler.END

# ── Kronometre buton işleyicileri ─────────────────────────────────────────────
async def kronometre_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kronometre menüsünü açar."""
    query = update.callback_query
    await query.answer()
    chat_id = query.from_user.id
    veri_k = kronometre_yukle(chat_id)
    await query.edit_message_text(
        text=kronometre_metni(chat_id),
        parse_mode="Markdown",
        reply_markup=kronometre_klavye(veri_k["durum"])
    )

async def krono_canli_guncelle(context: ContextTypes.DEFAULT_TYPE):
    """Her 10 saniyede kronometre mesajını canlı günceller."""
    data = context.job.data
    chat_id = data["chat_id"]
    message_id = data["message_id"]
    veri_k = kronometre_yukle(chat_id)

    # Kronometre durdurulduysa job'u sonlandır
    if veri_k["durum"] != "calisiyor":
        context.job.schedule_removal()
        return

    yeni_metin = kronometre_metni(chat_id)
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=yeni_metin,
            parse_mode="Markdown",
            reply_markup=kronometre_klavye("calisiyor"),
        )
    except Exception:
        # Mesaj değişmediyse Telegram hata verir — görmezden gel
        pass


async def krono_baslat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kronometreyi başlatır veya devam ettirir."""
    query = update.callback_query
    await query.answer("▶️ Başlatıldı!")
    chat_id = query.from_user.id
    veri_k = kronometre_yukle(chat_id)

    if veri_k["durum"] == "calisiyor":
        return

    # Başlat
    veri_k["durum"] = "calisiyor"
    veri_k["baslangic"] = simdi_tr().isoformat()
    kronometre_kaydet(chat_id, veri_k)

    # Önce mesajı güncelle → message_id'yi al
    mesaj = await query.edit_message_text(
        text=kronometre_metni(chat_id),
        parse_mode="Markdown",
        reply_markup=kronometre_klavye("calisiyor"),
    )
    message_id = mesaj.message_id

    # Varolan job'ları temizle
    for job_name in [f"krono_{chat_id}", f"krono_canli_{chat_id}"]:
        for j in context.job_queue.get_jobs_by_name(job_name):
            j.schedule_removal()

    # Her 3600 saniyede saatlik bildirim
    context.job_queue.run_repeating(
        krono_saat_bildirimi,
        interval=3600,
        first=3600,
        name=f"krono_{chat_id}",
        data={"chat_id": chat_id},
        chat_id=chat_id,
    )

    # Her 10 saniyede canlı güncelleme
    context.job_queue.run_repeating(
        krono_canli_guncelle,
        interval=10,
        first=10,
        name=f"krono_canli_{chat_id}",
        data={"chat_id": chat_id, "message_id": message_id},
        chat_id=chat_id,
    )

async def krono_durdur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kronometreyi durdurur, süreyi biriktirir."""
    query = update.callback_query
    await query.answer("⏸️ Durduruldu!")
    chat_id = query.from_user.id
    veri_k = kronometre_yukle(chat_id)

    if veri_k["durum"] != "calisiyor":
        return

    # Geçen süreyi biriktir
    baslangic = datetime.fromisoformat(veri_k["baslangic"])
    veri_k["gecen_sure"] += (simdi_tr() - baslangic).total_seconds()
    veri_k["durum"] = "durdu"
    veri_k["baslangic"] = None

    # Her iki job'u da durdur
    for job_name in [f"krono_{chat_id}", f"krono_canli_{chat_id}"]:
        for j in context.job_queue.get_jobs_by_name(job_name):
            j.schedule_removal()

    kronometre_kaydet(chat_id, veri_k)
    await query.edit_message_text(
        text=kronometre_metni(chat_id),
        parse_mode="Markdown",
        reply_markup=kronometre_klavye("durdu")
    )

async def krono_sifirla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kronometreyi sıfırlar."""
    query = update.callback_query
    await query.answer("🗑️ Sıfırlandı!")
    chat_id = query.from_user.id

    # Her iki job'u da temizle
    for job_name in [f"krono_{chat_id}", f"krono_canli_{chat_id}"]:
        for j in context.job_queue.get_jobs_by_name(job_name):
            j.schedule_removal()

    sifir = {
        "durum": "durdu",
        "baslangic": None,
        "gecen_sure": 0,
        "son_bildirim_saati": 0,
    }
    kronometre_kaydet(chat_id, sifir)
    await query.edit_message_text(
        text=kronometre_metni(chat_id),
        parse_mode="Markdown",
        reply_markup=kronometre_klavye("durdu")
    )

async def krono_yenile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kronometre ekranını günceller."""
    query = update.callback_query
    await query.answer("🔄 Güncellendi!")
    chat_id = query.from_user.id
    veri_k = kronometre_yukle(chat_id)
    await query.edit_message_text(
        text=kronometre_metni(chat_id),
        parse_mode="Markdown",
        reply_markup=kronometre_klavye(veri_k["durum"])
    )

async def krono_saat_bildirimi(context: ContextTypes.DEFAULT_TYPE):
    """Her 1 saat dolunca kullanıcıya bildirim gönderir."""
    chat_id = context.job.data["chat_id"]
    veri_k = kronometre_yukle(chat_id)

    if veri_k["durum"] != "calisiyor":
        return

    toplam = kronometre_toplam_saniye(veri_k)
    saat_sayisi = toplam // 3600

    mot = random.choice(MOTIVASYON)
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"⏰ *{saat_sayisi} saat doldu!*\n\n"
            f"⏱️ Toplam çalışma süresi: `{sure_formatla(toplam)}`\n\n"
            f"{mot}\n\n"
            f"_Kronometren hâlâ çalışıyor. Duraklatmak için /krono yaz._"
        ),
        parse_mode="Markdown"
    )

async def krono_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/krono komutuyla doğrudan kronometre ekranı açar."""
    chat_id = update.effective_chat.id
    veri_k = kronometre_yukle(chat_id)
    mesaj = await update.message.reply_text(
        text=kronometre_metni(chat_id),
        parse_mode="Markdown",
        reply_markup=kronometre_klavye(veri_k["durum"])
    )
    # Kronometre çalışıyorsa bu yeni mesaj için canlı güncelleme başlat
    if veri_k["durum"] == "calisiyor":
        canli_job = f"krono_canli_{chat_id}"
        for j in context.job_queue.get_jobs_by_name(canli_job):
            j.schedule_removal()
        context.job_queue.run_repeating(
            krono_canli_guncelle,
            interval=10,
            first=10,
            name=canli_job,
            data={"chat_id": chat_id, "message_id": mesaj.message_id},
            chat_id=chat_id,
        )

# ── Sabah bildirimi ───────────────────────────────────────────────────────────
async def sabah_bildirimi(context: ContextTypes.DEFAULT_TYPE):
    veri = veri_yukle()
    mot = random.choice(MOTIVASYON)
    mesaj = (
        "🌅 *Günaydın!*\n\n"
        + tum_sinavlar()
        + f"\n\n{mot}\n\n─────────────────\n"
        + gunun_ipucu()
    )
    basarili = 0
    for chat_id in veri.get("aboneler", []):
        try:
            await context.bot.send_message(chat_id=chat_id, text=mesaj,
                parse_mode="Markdown", reply_markup=sinav_butonlari())
            basarili += 1
        except Exception as e:
            print(f"Gönderilemedi {chat_id}: {e}")
    await admin_bildir(context,
        f"📬 *Sabah bildirimi!*\n✅ Başarılı: *{basarili}*\n"
        f"👥 Toplam: *{len(veri['aboneler'])}*\n🕐 {saat_str()}")

# ── Ana fonksiyon ─────────────────────────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    puan_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(hesap_sinav_sec, pattern="^hesap_")],
        states={
            BOLUM_GIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, bolum_gir)],
            OBP_GIR:   [MessageHandler(filters.TEXT & ~filters.COMMAND, obp_gir)],
        },
        fallbacks=[CommandHandler("iptal", hesap_iptal)],
        per_message=False,
    )

    app.add_handler(CommandHandler("start", baslat))
    app.add_handler(CommandHandler("liste", liste))
    app.add_handler(CommandHandler("iptal", bildirim_iptal))
    app.add_handler(CommandHandler("test", test_bildirim))
    app.add_handler(CommandHandler("istatistik", istatistik))
    app.add_handler(CommandHandler("gecmis", gecmis))
    app.add_handler(CommandHandler("analiz", analiz))
    app.add_handler(CommandHandler("krono", krono_komutu))       # ← yeni komut
    app.add_handler(puan_conv)
    app.add_handler(CallbackQueryHandler(puan_menu, pattern="^puan_menu$"))
    app.add_handler(CallbackQueryHandler(kronometre_menu, pattern="^kronometre_menu$"))  # ← yeni
    app.add_handler(CallbackQueryHandler(krono_baslat, pattern="^krono_baslat$"))        # ← yeni
    app.add_handler(CallbackQueryHandler(krono_durdur, pattern="^krono_durdur$"))        # ← yeni
    app.add_handler(CallbackQueryHandler(krono_sifirla, pattern="^krono_sifirla$"))      # ← yeni
    app.add_handler(CallbackQueryHandler(krono_yenile, pattern="^krono_yenile$"))        # ← yeni
    app.add_handler(CallbackQueryHandler(geri_don, pattern="^geri$"))
    app.add_handler(CallbackQueryHandler(ipucu_tiklandi, pattern="^ipucu$"))
    app.add_handler(CallbackQueryHandler(yenile_tiklandi, pattern="^yenile_"))
    app.add_handler(CallbackQueryHandler(buton_tiklandi, pattern="^sinav_"))

    app.job_queue.run_daily(
        sabah_bildirimi,
        time=datetime.strptime(f"{BILDIRIM_SAATI:02d}:{BILDIRIM_DAKIKA:02d}", "%H:%M").time(),
    )

    print(f"✅ Bot çalışıyor... {BILDIRIM_SAATI:02d}:{BILDIRIM_DAKIKA:02d}")
    app.run_polling()

if __name__ == "__main__":
    t = threading.Thread(target=flask_calistir, daemon=True)
    t.start()
    main()
