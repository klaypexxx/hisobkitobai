# Yuk hisob + Telegram bot

## 1. Bot yaratish
Telegramda @BotFather -> /newbot -> TOKEN oling.

## 2. Serverga qo'yish (Railway tavsiya)
1. Bu papkani GitHub'ga yuklang, Railway'da "New Project -> Deploy from GitHub".
2. Service ichida **Volume** qo'shing, mount path: `/data` (usiz ma'lumot o'chib ketadi).
3. Variables:
   - `BOT_TOKEN` = BotFather bergan token
   - `APP_PASSWORD` = ilova uchun parol (login bo'sh, faqat parol)
   - `ALLOWED_IDS` = Telegram ID (avval bo'sh qoldiring)
4. Settings -> Networking -> Generate Domain. Shu havola sizning ilovangiz.

## 3. Telegram ID olish
Botga biror narsa yozing, u "Ruxsat yo'q. Sizning ID: 123456" deb javob beradi.
Shu raqamni `ALLOWED_IDS` ga yozing (bir nechta bo'lsa vergul bilan). Qayta ishga tushadi.

## 4. Ishlatish
Botga chek rasmini yuboring, izohga telefonning oxirgi 4 raqamini yozing (yoki avval rasm, keyin raqam).
Bot shu raqam bilan tugaydigan to'lanmagan yukni topib, chekni biriktiradi va "To'langan" qiladi.
Bir nechta mos kelsa, ro'yxat chiqaradi, raqamini yozasiz.

Eslatma: bitta worker bilan ishlating (Procfile'da shunday), aks holda bot ikki marta javob beradi.
