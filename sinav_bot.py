import json
import os
from datetime import date, datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ── Ayarlar ───────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 123456789          # @userinfobot'tan öğren, sadece sen /istatistik yapabilirsin
BILDIRIM_SAATI = 8
BILDIRIM_DAKIKA = 0
VERI_DOSYASI = "veri.json"

# ── SABİT SINAVLAR — sadece buradan düzenlenir ────────────────────────────────
SINAVLAR = {
    "YKS TYT":  "2026-06-21",
    "YKS AYT":  "2026-06-22",
    "KPSS": "2026-09-06",
    # Yeni sınav eklemek için: "SınavAdı": "YYYY-MM-DD",
}
# ─────────────────────────────────────────────────────────────────────────────


def veri_yukle() -> dict:
    if os.path.exists(VERI_DOSYASI):
        with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"aboneler": []}


def veri_kaydet(veri: dict) -> None:
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)


def kalan_gun(tarih_str: str) -> int:
    return (date.fromisoformat(tarih_str) - date.today()).days


def geri_sayim_metni() -> str:
    satirlar = ["📅 *Sınav Geri Sayımları*\n"]
    for ad, tarih in sorted(SINAVLAR.items(), key=lambda x: x[1]):
        gun = kalan_gun(tarih)
        if gun < 0:
            durum = f"✅ Geçti ({abs(gun)} gün önce)"
        elif gun == 0:
            durum = "🔥 *BUGÜN!*"
        elif gun == 1:
            durum = "⚠️ *Yarın!*"
        else:
            durum = f"⏳ {gun} gün kaldı"
        satirlar.append(f"• *{ad}* — {tarih}\n  {durum}")
    return "\n".join(satirlar)


# ── Kullanıcı komutları ───────────────────────────────────────────────────────
async def baslat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    veri = veri_yukle()
    chat_id = update.effective_chat.id
    if chat_id not in veri["aboneler"]:
        veri["aboneler"].append(chat_id)
        veri_kaydet(veri)
        karsilama = "👋 *Hoş geldin!* Artık her sabah saat {:02d}:{:02d}'de bildirim alacaksın.\n\n".format(
            BILDIRIM_SAATI, BILDIRIM_DAKIKA
        )
    else:
        karsilama = "✅ Zaten abonesin! Her sabah bildirim alıyorsun.\n\n"

    await update.message.reply_text(
        karsilama + geri_sayim_metni(), parse_mode="Markdown"
    )


async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(geri_sayim_metni(), parse_mode="Markdown")


async def iptal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    veri = veri_yukle()
    chat_id = update.effective_chat.id
    if chat_id in veri["aboneler"]:
        veri["aboneler"].remove(chat_id)
        veri_kaydet(veri)
        await update.message.reply_text("🔕 Bildirimler durduruldu. Tekrar almak için /start yaz.")
    else:
        await update.message.reply_text("Zaten bildirim almıyordun.")


# ── Admin komutu ──────────────────────────────────────────────────────────────
async def istatistik(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    veri = veri_yukle()
    await update.message.reply_text(
        f"👥 Toplam abone: *{len(veri['aboneler'])}*", parse_mode="Markdown"
    )


# ── Zamanlanmış sabah bildirimi ───────────────────────────────────────────────
async def sabah_bildirimi(context: ContextTypes.DEFAULT_TYPE) -> None:
    veri = veri_yukle()
    mesaj = "🌅 *Günaydın!* İşte bugünün sınav durumu:\n\n" + geri_sayim_metni()
    for chat_id in veri.get("aboneler", []):
        try:
            await context.bot.send_message(chat_id=chat_id, text=mesaj, parse_mode="Markdown")
        except Exception as e:
            print(f"Gönderilemedi (chat_id={chat_id}): {e}")


# ── Ana fonksiyon ─────────────────────────────────────────────────────────────
def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", baslat))
    app.add_handler(CommandHandler("liste", liste))
    app.add_handler(CommandHandler("iptal", iptal))
    app.add_handler(CommandHandler("istatistik", istatistik))

    app.job_queue.run_daily(
        sabah_bildirimi,
        time=datetime.strptime(f"{BILDIRIM_SAATI:02d}:{BILDIRIM_DAKIKA:02d}", "%H:%M").time(),
    )

    print(f"✅ Bot çalışıyor... Bildirim saati: {BILDIRIM_SAATI:02d}:{BILDIRIM_DAKIKA:02d}")
    app.run_polling()


if __name__ == "__main__":
    main()
