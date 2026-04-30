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
    "YKS TYT": "2026-06-21 10:15",
    "YKS AYT": "2026-06-22 10:15",
    "KPSS":    "2026-09-06 10:15",
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


def veri_yukle() -> dict:
    if os.path.exists(VERI_DOSYASI):
        with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"aboneler": []}


def veri_kaydet(veri: dict) -> None:
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)


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


def sinav_butonlari() -> InlineKeyboardMarkup:
    butonlar = []
    for ad in SINAVLAR:
        butonlar.append([InlineKeyboardButton(f"📌 {ad}", callback_data=f"sinav_{ad}")])
    return InlineKeyboardMarkup(butonlar)


def sinav_detay(ad: str) -> str:
    tarih_str = SINAVLAR[ad]
    tarih_gosterim = tarih_str.split(" ")[0]
    sure = kalan_sure(tarih_str)
    motivasyon = random.choice(MOTIVASYON)
    return (
        f"📌 *{ad}*\n"
        f"📅 Tarih: {tarih_gosterim}\n"
        f"{sure}\n\n"
        f"{motivasyon}"
    )


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

    await query.edit_message_text(
        text=sinav_detay(ad),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Geri", callback_data="geri")]
        ])
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
    mesaj = "🌅 *Günaydın!* İşte bugünün sınav durumu:\n\n" + tum_sinavlar_metni() + f"\n\n{motivasyon}"
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
    app.add_handler(CallbackQueryHandler(buton_tiklandi, pattern="^sinav_"))

    app.job_queue.run_daily(
        sabah_bildirimi,
        time=datetime.strptime(f"{BILDIRIM_SAATI:02d}:{BILDIRIM_DAKIKA:02d}", "%H:%M").time(),
    )

    print(f"✅ Bot çalışıyor... Bildirim saati: {BILDIRIM_SAATI:02d}:{BILDIRIM_DAKIKA:02d}")
    app.run_polling()


if __name__ == "__main__":
    main()
