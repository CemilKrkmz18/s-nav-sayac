import json
import os
import random
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ── Ayarlar ───────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 1110751204
BILDIRIM_SAATI = 8
BILDIRIM_DAKIKA = 0
VERI_DOSYASI = "veri.json"

# ── Türkiye saat dilimi ───────────────────────────────────────────────────────
TR = timezone(timedelta(hours=3))

def simdi_tr() -> datetime:
    return datetime.now(TR).replace(tzinfo=None)

# ── SABİT SINAVLAR (10:15 başlangıç saati) ───────────────────────────────────
SINAVLAR = {
    "YKS TYT": "2026-06-21 10:15",
    "YKS AYT": "2026-06-22 10:15",
    "KPSS":    "2026-09-06 10:15",
}

# ── 2025 PUAN KATSAYILARI ────────────────────────────────────────────────────
TYT_KATSAYILAR = {
    "Türkçe": 2.83, "Sosyal Bilimler": 2.99,
    "Temel Matematik": 3.28, "Fen Bilimleri": 2.53,
}
TYT_BASLANGIC = 145.47

SAY_KATSAYILAR = {
    "Türkçe": 1.20, "Sosyal Bilimler": 1.27,
    "Temel Matematik": 1.39, "Fen Bilimleri": 1.07,
    "Matematik": 2.89, "Fizik": 2.46, "Kimya": 2.53, "Biyoloji": 2.61,
}
SAY_BASLANGIC = 132.87

EA_KATSAYILAR = {
    "Türkçe": 1.19, "Sosyal Bilimler": 1.26,
    "Temel Matematik": 1.38, "Fen Bilimleri": 1.07,
    "Matematik": 2.88, "Edebiyat": 2.94, "Tarih-1": 2.53, "Coğrafya-1": 2.85,
}
EA_BASLANGIC = 129.34

SOZ_KATSAYILAR = {
    "Türkçe": 1.13, "Sosyal Bilimler": 1.19,
    "Temel Matematik": 1.31, "Fen Bilimleri": 1.01,
    "Edebiyat": 2.79, "Tarih-1": 2.39, "Coğrafya-1": 2.70,
    "Tarih-2": 3.80, "Coğrafya-2": 2.47, "Felsefe Grubu": 3.76, "DKAB": 2.36,
}
SOZ_BASLANGIC = 129.61

# ── TAHMİNİ SIRALAMA TABLOSU (2025 ÖSYM verilerine dayalı) ───────────────────
# (puan_esigi, tahmini_siralama) — puan bu eşiğin üzerindeyse bu sıralama verilir
TYT_SIRALAMA = [
    (490, 1_000), (480, 3_000), (470, 6_000), (460, 12_000),
    (450, 22_000), (440, 40_000), (430, 65_000), (420, 100_000),
    (410, 145_000), (400, 200_000), (390, 265_000), (380, 340_000),
    (370, 425_000), (360, 520_000), (350, 620_000), (340, 730_000),
    (330, 850_000), (320, 980_000), (310, 1_120_000), (300, 1_270_000),
    (280, 1_550_000), (260, 1_800_000), (240, 2_000_000), (0, 2_500_000),
]

SAY_SIRALAMA = [
    (490, 500), (480, 1_500), (470, 3_000), (460, 6_000),
    (450, 10_000), (440, 16_000), (430, 25_000), (420, 37_000),
    (410, 52_000), (400, 72_000), (390, 97_000), (380, 128_000),
    (370, 165_000), (360, 210_000), (350, 260_000), (340, 315_000),
    (320, 430_000), (300, 560_000), (280, 700_000), (0, 900_000),
]

EA_SIRALAMA = [
    (490, 500), (480, 1_500), (470, 3_000), (460, 6_000),
    (450, 10_000), (440, 17_000), (430, 27_000), (420, 40_000),
    (410, 57_000), (400, 78_000), (390, 104_000), (380, 136_000),
    (370, 174_000), (360, 218_000), (350, 268_000), (340, 325_000),
    (320, 445_000), (300, 575_000), (0, 850_000),
]

SOZ_SIRALAMA = [
    (490, 300), (480, 1_000), (470, 2_200), (460, 4_500),
    (450, 8_000), (440, 13_000), (430, 20_000), (420, 30_000),
    (410, 43_000), (400, 59_000), (390, 79_000), (380, 103_000),
    (370, 132_000), (360, 165_000), (350, 203_000), (0, 350_000),
]

def tahmini_siralama(puan: float, tablo: list) -> str:
    for esik, siralama in tablo:
        if puan > esik:
            return f"~{siralama:,}".replace(",", ".")
    return "—"

# ── BÖLÜM LİSTELERİ ──────────────────────────────────────────────────────────
TYT_BOLUMLER = [
    ("Türkçe", 40), ("Sosyal Bilimler", 20),
    ("Temel Matematik", 40), ("Fen Bilimleri", 20),
]
AYT_BOLUMLER = [
    ("Matematik", 40), ("Fizik", 14), ("Kimya", 13), ("Biyoloji", 13),
    ("Edebiyat", 24), ("Tarih-1", 10), ("Coğrafya-1", 6),
    ("Tarih-2", 11), ("Coğrafya-2", 11), ("Felsefe Grubu", 12), ("DKAB", 6),
]

SINAV_SEC, BOLUM_GIR = range(2)

# ── MOTİVASYON ───────────────────────────────────────────────────────────────
MOTIVASYON = [
    "💪 Bugün çalıştığın her dakika, yarının başarısına bir adım!",
    "🌟 Zorlu yollar güzel manzaralara çıkar. Devam et!",
    "🔥 Vazgeçmek yok! Sen bunu başarabilirsin.",
    "📚 Küçük adımlar bile seni hedefe yaklaştırır.",
    "🎯 Odaklan, çalış, kazan. Sıra sende!",
    "🚀 Her gün biraz daha iyi olmak yeterli. Harika gidiyorsun!",
    "⭐ Emek asla boşa gitmez. Sonuç gelecek!",
    "🌈 Bugünün yorgunluğu, yarının gururudur.",
    "🏆 Kendine inan. En büyük rakibin dünkü halinden!",
    "✨ Bir gün daha geride kaldı, hedefe bir adım daha yakınsın!",
]

# ── İPUÇLARI ─────────────────────────────────────────────────────────────────
IPUCLARI = {
    "YKS TYT": [
        "📐 Matematik'te işlem hızını artırmak için her gün en az 20 temel işlem sorusu çöz.",
        "📖 Türkçe'de paragraf sorularında önce soruyu oku, sonra metne dön. Zaman kazandırır.",
        "🔢 Temel Matematik'te formül ezberlemek yerine mantığını anlamaya çalış.",
        "⏱️ TYT'de zaman yönetimi kritik. Her bölüme kaç dakika ayıracağını önceden belirle.",
        "📝 Yanlış yaptığın soruları bir deftere yaz ve haftada bir tekrar çöz.",
        "🧠 Fen Bilimleri'nde günlük hayatla bağlantı kur, ezber yapmaktan kaçın.",
        "📊 Sosyal Bilimler'de harita ve grafik sorularına özellikle çalış, kolay puan kaynağı.",
        "🎯 Her gün en az bir deneme sınavı bölümü çöz, süreyi mutlaka tut.",
        "💡 Dil Bilgisi kurallarını öğrenmek için cümle örnekleri üret.",
        "🔄 Çözdüğün denemelerin analizini yap, hangi konuda hata yaptığını belirle.",
        "📅 Çalışma programı yap ama esnek tut, kaçırdığın günleri telafi et.",
        "🧩 TYT Türkçe'de en çok puan kaybettiren konu: anlatım bozuklukları. Özellikle çalış.",
        "➗ Kesir ve oran-orantı sorularını günlük pratikle pekiştir.",
        "🌡️ Fen'de fizik formüllerini birbirine karıştırma, her birinin hangi durumda kullanıldığını öğren.",
        "📰 Güncel olayları takip et, Sosyal'de son dönemde çıkan güncel sorulara hazırlıklı ol.",
    ],
    "YKS AYT": [
        "📐 AYT Matematik'te türev ve integral birbirini tamamlar, ikisini birlikte çalış.",
        "📖 Edebiyat'ta dönem dönem çalış: Divan → Tanzimat → Servet-i Fünun → Cumhuriyet.",
        "🧪 Kimya'da mol hesaplamalarını otomatik hale getir, sınavda zaman kazanırsın.",
        "🔬 Biyoloji'de hücre bölünmesi ve genetik en çok soru çıkan konular, öncelik ver.",
        "⚡ Fizik'te vektör kavramını iyi öğren, birçok konunun temeli buradan geçiyor.",
        "📜 Tarih'te olayların nedenlerini ve sonuçlarını birlikte öğren, salt tarih ezberleme.",
        "🗺️ Coğrafya'da Türkiye haritasını ezberle, bölge soruları kolay puandır.",
        "🌍 Felsefe'de akımları ve temsilcileri birlikte öğren, birini unutursan diğeri hatırlatır.",
        "📚 AYT Türk Dili'nde şair/yazar eserlerini karıştırmamak için tablo yap.",
        "🧮 Logaritma ve üslü sayılarda pratik yapmak için her gün 10 soru çöz.",
        "🔭 Astronomi konuları AYT Coğrafya'da sürpriz soru olabilir, göz at.",
        "💊 Kimya'da organik bileşikler için fonksiyonel grupları mutlaka ezberle.",
        "📐 AYT'de analitik geometri ciddi yer tutar, koordinat sistemi sorularına özel vakit ayır.",
        "🎭 Edebiyat'ta nazım biçimlerini karıştırma: divan şiiri nazım biçimleri ayrı, halk şiiri ayrı.",
        "⚗️ Kimya denklemlerini denkleştirme pratiği yap, sınavda 2-3 soru mutlaka çıkar.",
    ],
    "KPSS": [
        "🏛️ Anayasa konusunu iyi öğren, KPSS'de en çok soru çıkan alanlardan biri.",
        "📜 Türk tarihi için kronolojik bir çalışma planı yap, olayları sıraya diz.",
        "🗺️ Coğrafya'da iklim tipleri ve Türkiye'nin bölgesel özellikleri sık soru çıkar.",
        "⚖️ Hukuk sorularında madde ezberlemek yerine mantığını kavra.",
        "📊 KPSS Matematik'te temel konular yeterli, ileri düzey konulara vakit harcama.",
        "🖊️ Türkçe'de cümle tamamlama ve anlam sorularına özellikle bak.",
        "📅 Atatürk İlkeleri ve İnkılapları kronolojik sırayla çalış, tarihler önemli.",
        "🧠 Eğitim Bilimleri için kavram haritaları oluştur, terimleri karıştırmamak için.",
        "📰 Güncel olayları takip et, KPSS'de zaman zaman güncel sorular çıkabiliyor.",
        "🔄 Çıkmış soruları çözmek en etkili KPSS hazırlık yöntemidir, mutlaka yap.",
        "📐 Geometri soruları KPSS'de basit düzeyde, temel formülleri gözden geçir.",
        "🌐 Vatandaşlık bilgisi için Türkiye Cumhuriyeti'nin temel kurumlarını iyi öğren.",
        "📚 Alan bilgisi sınavı için mezun olduğun bölümün temel kaynaklarını gözden geçir.",
        "⏱️ KPSS'de zaman baskısı yüksek, deneme sınavlarında süreyi mutlaka tut.",
        "🎯 Puan türüne göre odaklan: KPSSP3 için Eğitim Bilimleri kritik, boş bırakma.",
    ],
}


# ── Yardımcılar ───────────────────────────────────────────────────────────────
def veri_yukle() -> dict:
    if os.path.exists(VERI_DOSYASI):
        with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"aboneler": []}

def veri_kaydet(veri: dict) -> None:
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)

def gunun_ipucu() -> str:
    gun_no = simdi_tr().timetuple().tm_yday
    satirlar = ["💡 *Günün Sınav Taktikleri*\n"]
    for sinav_adi, ipucu_listesi in IPUCLARI.items():
        ipucu = ipucu_listesi[gun_no % len(ipucu_listesi)]
        satirlar.append(f"*{sinav_adi}:*\n{ipucu}")
    return "\n\n".join(satirlar)

def kalan_sure(tarih_str: str) -> str:
    sinav_dt = datetime.strptime(tarih_str, "%Y-%m-%d %H:%M")
    fark = sinav_dt - simdi_tr()
    if fark.total_seconds() <= 0:
        return "✅ Bu sınav gerçekleşti."
    toplam_saniye = int(fark.total_seconds())
    gun = toplam_saniye // 86400
    saat = (toplam_saniye % 86400) // 3600
    dakika = (toplam_saniye % 3600) // 60
    parcalar = []
    if gun > 0: parcalar.append(f"*{gun}* gün")
    if saat > 0: parcalar.append(f"*{saat}* saat")
    if dakika > 0 or (gun == 0 and saat == 0): parcalar.append(f"*{dakika}* dakika")
    return "⏳ " + " ".join(parcalar) + " kaldı"

def guncelleme_zamani() -> str:
    return simdi_tr().strftime("%H:%M:%S")

def kullanici_adi(user) -> str:
    return user.full_name if user.full_name else (user.username or str(user.id))

def net_hesapla(dogru: float, yanlis: float) -> float:
    return dogru - (yanlis / 4)

def tyt_puan_hesapla(netler: dict) -> float:
    puan = TYT_BASLANGIC
    for bolum, net in netler.items():
        puan += net * TYT_KATSAYILAR.get(bolum, 0)
    return round(puan, 2)

def ayt_puan_hesapla(tyt_netler: dict, ayt_netler: dict) -> dict:
    puanlar = {}
    say = SAY_BASLANGIC
    for b, n in tyt_netler.items(): say += n * SAY_KATSAYILAR.get(b, 0)
    for b in ["Matematik", "Fizik", "Kimya", "Biyoloji"]:
        say += ayt_netler.get(b, 0) * SAY_KATSAYILAR.get(b, 0)
    puanlar["SAY"] = round(say, 2)

    ea = EA_BASLANGIC
    for b, n in tyt_netler.items(): ea += n * EA_KATSAYILAR.get(b, 0)
    for b in ["Matematik", "Edebiyat", "Tarih-1", "Coğrafya-1"]:
        ea += ayt_netler.get(b, 0) * EA_KATSAYILAR.get(b, 0)
    puanlar["EA"] = round(ea, 2)

    soz = SOZ_BASLANGIC
    for b, n in tyt_netler.items(): soz += n * SOZ_KATSAYILAR.get(b, 0)
    for b in ["Edebiyat", "Tarih-1", "Coğrafya-1", "Tarih-2", "Coğrafya-2", "Felsefe Grubu", "DKAB"]:
        soz += ayt_netler.get(b, 0) * SOZ_KATSAYILAR.get(b, 0)
    puanlar["SÖZ"] = round(soz, 2)

    return puanlar

def sinav_butonlari() -> InlineKeyboardMarkup:
    butonlar = []
    for ad in SINAVLAR:
        butonlar.append([InlineKeyboardButton(f"📌 {ad}", callback_data=f"sinav_{ad}")])
    butonlar.append([InlineKeyboardButton("💡 Günün Taktikleri", callback_data="ipucu")])
    butonlar.append([InlineKeyboardButton("🧮 Puan Hesapla", callback_data="puan_menu")])
    return InlineKeyboardMarkup(butonlar)

def sinav_detay_metni(ad: str, motivasyon: str) -> str:
    tarih_str = SINAVLAR[ad]
    tarih_gosterim = tarih_str.split(" ")[0]
    sure = kalan_sure(tarih_str)
    return (
        f"📌 *{ad}*\n📅 Tarih: {tarih_gosterim}\n{sure}\n\n"
        f"{motivasyon}\n\n🔄 _Son güncelleme: {guncelleme_zamani()}_"
    )

def sinav_detay_butonlari(ad: str, motivasyon: str) -> InlineKeyboardMarkup:
    mot_index = MOTIVASYON.index(motivasyon) if motivasyon in MOTIVASYON else 0
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Yenile", callback_data=f"yenile_{ad}_{mot_index}")],
        [InlineKeyboardButton("🔙 Geri", callback_data="geri")]
    ])

def tum_sinavlar_metni() -> str:
    satirlar = ["📅 *Sınav Geri Sayımları*\n"]
    for ad, tarih_str in sorted(SINAVLAR.items(), key=lambda x: x[1]):
        tarih_gosterim = tarih_str.split(" ")[0]
        sure = kalan_sure(tarih_str)
        satirlar.append(f"• *{ad}* — {tarih_gosterim}\n  {sure}")
    return "\n".join(satirlar)


# ── Admin bildirimi ───────────────────────────────────────────────────────────
async def admin_bildir(context, mesaj: str) -> None:
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=mesaj, parse_mode="Markdown")
    except Exception as e:
        print(f"Admin bildirimi gönderilemedi: {e}")


# ── Komutlar ──────────────────────────────────────────────────────────────────
async def baslat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    veri = veri_yukle()
    chat_id = update.effective_chat.id
    user = update.effective_user
    ad = kullanici_adi(user)
    username = f"@{user.username}" if user.username else "—"
    if chat_id not in veri["aboneler"]:
        veri["aboneler"].append(chat_id)
        veri_kaydet(veri)
        karsilama = "👋 *Hoş geldin!* Her sabah saat {:02d}:{:02d}'de bildirim alacaksın.\n\n".format(BILDIRIM_SAATI, BILDIRIM_DAKIKA)
        await admin_bildir(context,
            f"🟢 *Yeni kullanıcı katıldı!*\n👤 İsim: {ad}\n🔗 Kullanıcı adı: {username}\n"
            f"🆔 ID: `{chat_id}`\n📊 Toplam abone: *{len(veri['aboneler'])}*\n🕐 Saat: {guncelleme_zamani()}"
        )
    else:
        karsilama = "✅ Zaten abonesin!\n\n"
    await update.message.reply_text(
        karsilama + "Hangi sınavın geri sayımını görmek istersin?",
        reply_markup=sinav_butonlari(), parse_mode="Markdown"
    )

async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hangi sınavı görmek istersin?", reply_markup=sinav_butonlari())

async def iptal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    veri = veri_yukle()
    chat_id = update.effective_chat.id
    user = update.effective_user
    ad = kullanici_adi(user)
    username = f"@{user.username}" if user.username else "—"
    if chat_id in veri["aboneler"]:
        veri["aboneler"].remove(chat_id)
        veri_kaydet(veri)
        await update.message.reply_text("🔕 Bildirimler durduruldu. Tekrar almak için /start yaz.")
        await admin_bildir(context,
            f"🔴 *Kullanıcı ayrıldı!*\n👤 İsim: {ad}\n🔗 Kullanıcı adı: {username}\n"
            f"🆔 ID: `{chat_id}`\n📊 Kalan abone: *{len(veri['aboneler'])}*\n🕐 Saat: {guncelleme_zamani()}"
        )
    else:
        await update.message.reply_text("Zaten bildirim almıyordun.")

async def test_bildirim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await sabah_bildirimi(context)
    await update.message.reply_text("✅ Test bildirimi gönderildi!")

async def istatistik(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    veri = veri_yukle()
    await update.message.reply_text(f"👥 Toplam abone: *{len(veri['aboneler'])}*", parse_mode="Markdown")


# ── Geri sayım butonları ──────────────────────────────────────────────────────
async def buton_tiklandi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    ad = query.data[len("sinav_"):]
    if ad not in SINAVLAR:
        await query.edit_message_text("❌ Sınav bulunamadı.")
        return
    motivasyon = random.choice(MOTIVASYON)
    await query.edit_message_text(
        text=sinav_detay_metni(ad, motivasyon), parse_mode="Markdown",
        reply_markup=sinav_detay_butonlari(ad, motivasyon)
    )

async def ipucu_tiklandi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text=gunun_ipucu(), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="geri")]])
    )

async def yenile_tiklandi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("🔄 Güncellendi!")
    parca = query.data[len("yenile_"):]
    son = parca.rfind("_")
    ad = parca[:son]
    mot_index = int(parca[son + 1:])
    if ad not in SINAVLAR:
        await query.edit_message_text("❌ Sınav bulunamadı.")
        return
    motivasyon = MOTIVASYON[mot_index]
    await query.edit_message_text(
        text=sinav_detay_metni(ad, motivasyon), parse_mode="Markdown",
        reply_markup=sinav_detay_butonlari(ad, motivasyon)
    )

async def geri_don(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Hangi sınavı görmek istersin?", reply_markup=sinav_butonlari())


# ── PUAN HESAPLAMA ────────────────────────────────────────────────────────────
async def puan_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🧮 *Puan Hesaplama*\n\nHangi sınav için hesaplayalım?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 TYT", callback_data="hesap_TYT")],
            [InlineKeyboardButton("📝 AYT (SAY/EA/SÖZ)", callback_data="hesap_AYT")],
            [InlineKeyboardButton("🔙 Geri", callback_data="geri")],
        ])
    )
    return SINAV_SEC

async def hesap_sinav_sec(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    sinav_turu = query.data.replace("hesap_", "")
    context.user_data["sinav_turu"] = sinav_turu
    context.user_data["bolum_index"] = 0
    context.user_data["netler"] = {}
    context.user_data["bolumler"] = TYT_BOLUMLER if sinav_turu == "TYT" else TYT_BOLUMLER + AYT_BOLUMLER
    bolum_adi, soru_sayisi = context.user_data["bolumler"][0]
    await query.edit_message_text(
        f"📝 *{sinav_turu} Puan Hesaplama*\n\n"
        f"Bölüm 1/{len(context.user_data['bolumler'])}: *{bolum_adi}* ({soru_sayisi} soru)\n\n"
        f"Doğru ve yanlış sayını gir:\nÖrnek: `25 5` (25 doğru, 5 yanlış)",
        parse_mode="Markdown"
    )
    return BOLUM_GIR

async def bolum_gir(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    metin = update.message.text.strip()
    try:
        parcalar = metin.split()
        dogru = float(parcalar[0])
        yanlis = float(parcalar[1]) if len(parcalar) > 1 else 0.0
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Hatalı format. Örnek: `25 5`", parse_mode="Markdown")
        return BOLUM_GIR

    bolumler = context.user_data["bolumler"]
    index = context.user_data["bolum_index"]
    bolum_adi, soru_sayisi = bolumler[index]

    if dogru + yanlis > soru_sayisi:
        await update.message.reply_text(f"❌ {bolum_adi} için max {soru_sayisi} soru. Tekrar gir.")
        return BOLUM_GIR

    net = net_hesapla(dogru, yanlis)
    context.user_data["netler"][bolum_adi] = net
    context.user_data["bolum_index"] += 1

    if context.user_data["bolum_index"] < len(bolumler):
        sonraki_bolum, sonraki_soru = bolumler[context.user_data["bolum_index"]]
        await update.message.reply_text(
            f"✅ *{bolum_adi}*: {net:.2f} net\n\n"
            f"Bölüm {context.user_data['bolum_index']+1}/{len(bolumler)}: *{sonraki_bolum}* ({sonraki_soru} soru)\n\n"
            f"Doğru ve yanlış sayını gir:\nÖrnek: `25 5`",
            parse_mode="Markdown"
        )
        return BOLUM_GIR
    else:
        return await hesaplama_sonuc(update, context)

async def hesaplama_sonuc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    sinav_turu = context.user_data["sinav_turu"]
    netler = context.user_data["netler"]

    if sinav_turu == "TYT":
        tyt_netler = {b: netler.get(b, 0) for b, _ in TYT_BOLUMLER}
        puan = tyt_puan_hesapla(tyt_netler)
        toplam_net = sum(tyt_netler.values())
        siralama = tahmini_siralama(puan, TYT_SIRALAMA)

        mesaj = f"🎯 *TYT Puan Sonucu*\n\n📊 *Net Dağılımı:*\n"
        for bolum, net in tyt_netler.items():
            mesaj += f"• {bolum}: `{net:.2f}`\n"
        mesaj += (
            f"\n📈 *Toplam Net:* `{toplam_net:.2f}`\n"
            f"🏆 *Tahmini TYT Puanı:* `{puan}`\n"
            f"📊 *Tahmini Sıralama:* `{siralama}`\n\n"
            f"_⚠️ Sıralama tahminidir, OBP dahil değildir._"
        )
    else:
        tyt_netler = {b: netler.get(b, 0) for b, _ in TYT_BOLUMLER}
        ayt_netler = {b: netler.get(b, 0) for b, _ in AYT_BOLUMLER}
        tyt_puan = tyt_puan_hesapla(tyt_netler)
        ayt_puanlar = ayt_puan_hesapla(tyt_netler, ayt_netler)
        tyt_toplam = sum(tyt_netler.values())
        ayt_toplam = sum(ayt_netler.values())

        mesaj = f"🎯 *AYT Puan Sonucu*\n\n📊 *TYT Netleri:*\n"
        for bolum, net in tyt_netler.items():
            mesaj += f"• {bolum}: `{net:.2f}`\n"
        mesaj += f"• *TYT Toplam:* `{tyt_toplam:.2f}` net → `{tyt_puan}` puan\n\n"
        mesaj += f"📊 *AYT Netleri:*\n"
        for bolum, net in ayt_netler.items():
            mesaj += f"• {bolum}: `{net:.2f}`\n"
        mesaj += f"• *AYT Toplam Net:* `{ayt_toplam:.2f}`\n\n"
        mesaj += f"🏆 *Tahmini Puanlar ve Sıralamalar:*\n"
        siralama_tablolari = {"SAY": SAY_SIRALAMA, "EA": EA_SIRALAMA, "SÖZ": SOZ_SIRALAMA}
        for tur, puan in ayt_puanlar.items():
            siralama = tahmini_siralama(puan, siralama_tablolari[tur])
            mesaj += f"• *{tur}:* `{puan}` puan → `{siralama}` sıra\n"
        mesaj += f"\n_⚠️ Sıralama tahminidir, OBP dahil değildir._"

    await update.message.reply_text(
        mesaj, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Ana Menü", callback_data="geri")]])
    )
    context.user_data.clear()
    return ConversationHandler.END

async def hesap_iptal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("❌ Puan hesaplama iptal edildi.", reply_markup=sinav_butonlari())
    return ConversationHandler.END


# ── Sabah bildirimi ───────────────────────────────────────────────────────────
async def sabah_bildirimi(context: ContextTypes.DEFAULT_TYPE) -> None:
    veri = veri_yukle()
    motivasyon = random.choice(MOTIVASYON)
    mesaj = (
        "🌅 *Günaydın!* İşte bugünün sınav durumu:\n\n"
        + tum_sinavlar_metni()
        + f"\n\n{motivasyon}\n\n─────────────────\n"
        + gunun_ipucu()
    )
    basarili = 0
    for chat_id in veri.get("aboneler", []):
        try:
            await context.bot.send_message(chat_id=chat_id, text=mesaj, parse_mode="Markdown", reply_markup=sinav_butonlari())
            basarili += 1
        except Exception as e:
            print(f"Gönderilemedi (chat_id={chat_id}): {e}")
    await admin_bildir(context,
        f"📬 *Sabah bildirimi gönderildi!*\n✅ Başarılı: *{basarili}* kişi\n"
        f"👥 Toplam abone: *{len(veri['aboneler'])}*\n🕐 Saat: {guncelleme_zamani()}"
    )


# ── Ana fonksiyon ─────────────────────────────────────────────────────────────
def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    puan_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(hesap_sinav_sec, pattern="^hesap_")],
        states={BOLUM_GIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, bolum_gir)]},
        fallbacks=[CommandHandler("iptal", hesap_iptal)],
        per_message=False,
    )

    app.add_handler(CommandHandler("start", baslat))
    app.add_handler(CommandHandler("liste", liste))
    app.add_handler(CommandHandler("iptal", iptal))
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

    print(f"✅ Bot çalışıyor... Bildirim saati: {BILDIRIM_SAATI:02d}:{BILDIRIM_DAKIKA:02d}")
    app.run_polling()


if __name__ == "__main__":
    main()
