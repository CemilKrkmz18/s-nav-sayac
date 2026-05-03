import json
import os
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)

# ── Ayarlar ───────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 123456789
BILDIRIM_SAATI = 8
BILDIRIM_DAKIKA = 0
VERI_DOSYASI = "veri.json"

# ── SABİT SINAVLAR ────────────────────────────────────────────────────────────
SINAVLAR = {
    "YKS TYT": "2026-06-21 09:00",
    "YKS AYT": "2026-06-22 09:00",
    "KPSS":    "2026-09-06 09:00",
}

# ── MOTİVASYON SÖZLERİ ───────────────────────────────────────────────────────
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

# ── GÜNLÜK İPUÇLARI ──────────────────────────────────────────────────────────
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
    """Günün sıra numarasına göre her sınav için bir ipucu seç."""
    gun_no = datetime.now().timetuple().tm_yday  # yılın kaçıncı günü
    satirlar = ["💡 *Günün Sınav Taktikleri*\n"]
    for sinav_adi, ipucu_listesi in IPUCLARI.items():
        ipucu = ipucu_listesi[gun_no % len(ipucu_listesi)]
        satirlar.append(f"*{sinav_adi}:*\n{ipucu}")
    return "\n\n".join(satirlar)


def kalan_sure(tarih_str: str) -> str:
    sinav_dt = datetime.strptime(tarih_str, "%Y-%m-%d %H:%M")
    simdi = datetime.now()
    fark = sinav_dt - simdi

    if fark.total_seconds() <= 0:
        return "✅ Bu sınav gerçekleşti."

    toplam_saniye = int(fark.total_seconds())
    gun = toplam_saniye // 86400
    saat = (toplam_saniye % 86400) // 3600
    dakika = (toplam_saniye % 3600) // 60

    parcalar = []
    if gun > 0:
        parcalar.append(f"*{gun}* gün")
    if saat > 0:
        parcalar.append(f"*{saat}* saat")
    if dakika > 0 or (gun == 0 and saat == 0):
        parcalar.append(f"*{dakika}* dakika")

    return "⏳ " + " ".join(parcalar) + " kaldı"


def guncelleme_zamani() -> str:
    return datetime.now().strftime("%H:%M:%S")


def sinav_butonlari() -> InlineKeyboardMarkup:
    butonlar = []
    for ad in SINAVLAR:
        butonlar.append([InlineKeyboardButton(f"📌 {ad}", callback_data=f"sinav_{ad}")])
    butonlar.append([InlineKeyboardButton("💡 Günün Taktikleri", callback_data="ipucu")])
    return InlineKeyboardMarkup(butonlar)


def sinav_detay_metni(ad: str, motivasyon: str) -> str:
    tarih_str = SINAVLAR[ad]
    tarih_gosterim = tarih_str.split(" ")[0]
    sure = kalan_sure(tarih_str)
    guncellendi = guncelleme_zamani()
    return (
        f"📌 *{ad}*\n"
        f"📅 Tarih: {tarih_gosterim}\n"
        f"{sure}\n\n"
        f"{motivasyon}\n\n"
        f"🔄 _Son güncelleme: {guncellendi}_"
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


# ── Komutlar ──────────────────────────────────────────────────────────────────
async def baslat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    veri = veri_yukle()
    chat_id = update.effective_chat.id
    if chat_id not in veri["aboneler"]:
        veri["aboneler"].append(chat_id)
        veri_kaydet(veri)
        karsilama = "👋 *Hoş geldin!* Her sabah saat {:02d}:{:02d}'de bildirim alacaksın.\n\n".format(
            BILDIRIM_SAATI, BILDIRIM_DAKIKA
        )
    else:
        karsilama = "✅ Zaten abonesin!\n\n"

    await update.message.reply_text(
        karsilama + "Hangi sınavın geri sayımını görmek istersin?",
        reply_markup=sinav_butonlari(),
        parse_mode="Markdown"
    )


async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hangi sınavı görmek istersin?",
        reply_markup=sinav_butonlari()
    )


async def iptal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    veri = veri_yukle()
    chat_id = update.effective_chat.id
    if chat_id in veri["aboneler"]:
        veri["aboneler"].remove(chat_id)
        veri_kaydet(veri)
        await update.message.reply_text("🔕 Bildirimler durduruldu. Tekrar almak için /start yaz.")
    else:
        await update.message.reply_text("Zaten bildirim almıyordun.")


async def test_bildirim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await sabah_bildirimi(context)
    await update.message.reply_text("✅ Test bildirimi gönderildi!")


async def istatistik(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    veri = veri_yukle()
    await update.message.reply_text(
        f"👥 Toplam abone: *{len(veri['aboneler'])}*", parse_mode="Markdown"
    )


# ── Buton tıklamaları ─────────────────────────────────────────────────────────
async def buton_tiklandi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    ad = query.data[len("sinav_"):]
    if ad not in SINAVLAR:
        await query.edit_message_text("❌ Sınav bulunamadı.")
        return

    motivasyon = random.choice(MOTIVASYON)
    await query.edit_message_text(
        text=sinav_detay_metni(ad, motivasyon),
        parse_mode="Markdown",
        reply_markup=sinav_detay_butonlari(ad, motivasyon)
    )


async def ipucu_tiklandi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text=gunun_ipucu(),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Geri", callback_data="geri")]
        ])
    )


async def yenile_tiklandi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("🔄 Güncellendi!")

    parca = query.data[len("yenile_"):]
    son_alt_cizgi = parca.rfind("_")
    ad = parca[:son_alt_cizgi]
    mot_index = int(parca[son_alt_cizgi + 1:])

    if ad not in SINAVLAR:
        await query.edit_message_text("❌ Sınav bulunamadı.")
        return

    motivasyon = MOTIVASYON[mot_index]
    await query.edit_message_text(
        text=sinav_detay_metni(ad, motivasyon),
        parse_mode="Markdown",
        reply_markup=sinav_detay_butonlari(ad, motivasyon)
    )


async def geri_don(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text="Hangi sınavı görmek istersin?",
        reply_markup=sinav_butonlari()
    )


# ── Sabah bildirimi ───────────────────────────────────────────────────────────
async def sabah_bildirimi(context: ContextTypes.DEFAULT_TYPE) -> None:
    veri = veri_yukle()
    motivasyon = random.choice(MOTIVASYON)
    mesaj = (
        "🌅 *Günaydın!* İşte bugünün sınav durumu:\n\n"
        + tum_sinavlar_metni()
        + f"\n\n{motivasyon}\n\n"
        + "─────────────────\n"
        + gunun_ipucu()
    )
    for chat_id in veri.get("aboneler", []):
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=mesaj,
                parse_mode="Markdown",
                reply_markup=sinav_butonlari()
            )
        except Exception as e:
            print(f"Gönderilemedi (chat_id={chat_id}): {e}")


# ── Ana fonksiyon ─────────────────────────────────────────────────────────────
def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", baslat))
    app.add_handler(CommandHandler("liste", liste))
    app.add_handler(CommandHandler("iptal", iptal))
    app.add_handler(CommandHandler("test", test_bildirim))
    app.add_handler(CommandHandler("istatistik", istatistik))
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
