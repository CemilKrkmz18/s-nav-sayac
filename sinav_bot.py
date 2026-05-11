import json
import os
import random
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 1110751204
BILDIRIM_SAATI = 8
BILDIRIM_DAKIKA = 0
VERI_DOSYASI = "veri.json"
TR = timezone(timedelta(hours=3))

def simdi_tr():
    return datetime.now(TR).replace(tzinfo=None)

SINAVLAR = {
    "YKS TYT": "2026-06-21 10:15",
    "YKS AYT": "2026-06-22 10:15",
    "KPSS":    "2026-09-06 10:15",
}

# ── KATSAYILAR ────────────────────────────────────────────────────────────────
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

# OBP katkı katsayısı (ÖSYM 2025: 0.12 * OBP)
OBP_KATSAYI = 0.12

# ── SIRALAMA TABLOLARI ────────────────────────────────────────────────────────
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

TYT_BOLUMLER = [("Türkçe",40),("Sosyal Bilimler",20),("Temel Matematik",40),("Fen Bilimleri",20)]
AYT_BOLUMLER = [("Matematik",40),("Fizik",14),("Kimya",13),("Biyoloji",13),
                ("Edebiyat",24),("Tarih-1",10),("Coğrafya-1",6),
                ("Tarih-2",11),("Coğrafya-2",11),("Felsefe Grubu",12),("DKAB",6)]

SINAV_SEC, BOLUM_GIR, OBP_GIR = range(3)

# ── MOTİVASYON (kısa tutuldu — karakter limiti için) ─────────────────────────
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


# ── Veri ─────────────────────────────────────────────────────────────────────
def veri_yukle():
    if os.path.exists(VERI_DOSYASI):
        with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"aboneler": []}

def veri_kaydet(veri):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)

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
    """OBP 50-100 arası not, 250-500 arası direkt OBP olabilir."""
    if 50 <= obp_degeri <= 100:
        obp = obp_degeri * 5  # diploma notunu OBP'ye çevir
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
    return InlineKeyboardMarkup(b)

def detay_metni(ad, mot):
    tarih = SINAVLAR[ad].split(" ")[0]
    # Kısa format — inline mesaj karakter limitine uygun
    return f"📌 *{ad}*\n📅 {tarih}\n{kalan_sure(ad if ad in SINAVLAR else ad)}\n\n{mot}\n\n🔄 _{saat_str()}_"

def detay_metni2(ad, mot):
    tarih_str = SINAVLAR[ad]
    tarih = tarih_str.split(" ")[0]
    sure = kalan_sure(tarih_str)
    return f"📌 *{ad}*\n📅 {tarih}\n{sure}\n\n{mot}\n\n🔄 _{saat_str()}_"

def tum_sinavlar():
    s = ["📅 *Geri Sayımlar*\n"]
    for ad, ts in sorted(SINAVLAR.items(), key=lambda x: x[1]):
        s.append(f"• *{ad}* — {ts.split()[0]}\n  {kalan_sure(ts)}")
    return "\n".join(s)


# ── Admin ─────────────────────────────────────────────────────────────────────
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
    yeni = chat_id not in veri["aboneler"]
    if yeni:
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
        text=detay_metni2(ad, mot), parse_mode="Markdown",
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
        text=detay_metni2(ad, mot), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yenile", callback_data=f"yenile_{ad}_{mot_i}")],
            [InlineKeyboardButton("🔙 Geri", callback_data="geri")]
        ])
    )

async def geri_don(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Hangi sınavı görmek istersin?", reply_markup=sinav_butonlari())


# ── PUAN HESAPLAMA ────────────────────────────────────────────────────────────
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
        "bolumler": TYT_BOLUMLER if tur == "TYT" else TYT_BOLUMLER + AYT_BOLUMLER
    })
    b, s = context.user_data["bolumler"][0]
    await query.edit_message_text(
        f"📝 *{tur} Hesaplama*\n\n"
        f"1/{len(context.user_data['bolumler'])}: *{b}* ({s} soru)\n\n"
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

    bolumler = context.user_data["bolumler"]
    i = context.user_data["bolum_index"]
    b, s = bolumler[i]

    if d + y > s:
        await update.message.reply_text(f"❌ Max {s} soru. Tekrar:")
        return BOLUM_GIR

    context.user_data["netler"][b] = net(d, y)
    context.user_data["bolum_index"] += 1

    if context.user_data["bolum_index"] < len(bolumler):
        nb, ns = bolumler[context.user_data["bolum_index"]]
        await update.message.reply_text(
            f"✅ *{b}*: {context.user_data['netler'][b]:.2f} net\n\n"
            f"{context.user_data['bolum_index']+1}/{len(bolumler)}: *{nb}* ({ns} soru)\n\n"
            f"Doğru yanlış: `25 5`",
            parse_mode="Markdown"
        )
        return BOLUM_GIR
    else:
        await update.message.reply_text(
            "✅ Tüm bölümler tamamlandı!\n\n"
            "📊 *OBP (Diploma Notu) gir:*\n"
            "• Diploma notu: `85` (50-100 arası)\n"
            "• Direkt OBP: `425` (250-500 arası)\n"
            "• OBP'siz hesapla: `0`",
            parse_mode="Markdown"
        )
        return OBP_GIR

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

        mesaj = f"🎯 *TYT Sonucu*\n\n"
        mesaj += f"📊 *Netler:*\n"
        for b, n in tyt_n.items():
            mesaj += f"• {b}: `{n:.2f}`\n"
        mesaj += f"\n📈 Toplam Net: `{toplam:.2f}`\n"
        mesaj += f"🏆 Ham Puan: `{puan}`\n"
        mesaj += f"📊 Sıralama (OBP'siz): `{siralama}`\n"
        if obp_val > 0:
            mesaj += f"\n📋 OBP Katkısı: `+{obp_k}`\n"
            mesaj += f"🏆 Yerleştirme Puanı: `{puan_obp}`\n"
            mesaj += f"📊 Sıralama (OBP'li): `{siralama_obp}`\n"
        mesaj += f"\n_⚠️ Tahmindir, resmi değildir._"

    else:
        tyt_n = {b: netler.get(b, 0) for b, _ in TYT_BOLUMLER}
        ayt_n = {b: netler.get(b, 0) for b, _ in AYT_BOLUMLER}
        tyt_p = tyt_puan(tyt_n)
        puanlar = ayt_puanlar(tyt_n, ayt_n)
        tyt_top = sum(tyt_n.values())
        ayt_top = sum(ayt_n.values())
        tablolar = {"SAY": SAY_S, "EA": EA_S, "SÖZ": SOZ_S}

        mesaj = f"🎯 *AYT Sonucu*\n\n"
        mesaj += f"📊 *TYT Netleri:* (toplam: `{tyt_top:.2f}`, puan: `{tyt_p}`)\n"
        for b, n in tyt_n.items():
            mesaj += f"• {b}: `{n:.2f}`\n"
        mesaj += f"\n📊 *AYT Netleri:* (toplam: `{ayt_top:.2f}`)\n"
        for b, n in ayt_n.items():
            mesaj += f"• {b}: `{n:.2f}`\n"
        mesaj += f"\n🏆 *Puanlar ve Sıralamalar:*\n"
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
        mesaj += f"\n_⚠️ Tahmindir, resmi değildir._"

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
    app.add_handler(puan_conv)
    app.add_handler(CallbackQueryHandler(puan_menu, pattern="^puan_menu$"))
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
    main()
