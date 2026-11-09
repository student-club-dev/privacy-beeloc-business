# Beeloc Business — huquqiy sayt

Foydalanish shartlari, Maxfiylik siyosati, To'lov va qaytarish siyosati va Yordam sahifalari (uz / ru / en).
GitHub Pages orqali beriladi.

## Tuzilma

```
content/<til>/<hujjat>.md   ← YAGONA manba: matnni faqat shu yerda o'zgartiring
build.py                    ← markdown → HTML
uz/ ru/ en/                 ← yig'ilgan sahifalar (qo'lda tahrirlamang)
privacy-policy.html         ← App Store / Play Console'da ro'yxatdan o'tgan eski manzil (en)
support.html                ← App Store "Support URL" (en)
assets/                     ← style.css, favicon
```

## Matnni yangilash

1. `content/<til>/*.md` ni tahrirlang (sanani va versiyani ham yangilang).
2. Yig'ing va ilovadagi matnlarni ham yangilang:

   ```
   python3 build.py --sync-app ~/AndroidStudioProjects/ElonUz/dev/core/uikit/src/commonMain/composeResources/files/legal
   ```

3. Ikkala repo'ni commit/push qiling.

Markdown faqat: `#`, `##`, `###`, paragraf, `- ` ro'yxat, jadval, `**qalin**`, `> ` izoh.
Havola (`[matn](url)`) yozmang — ilovadagi ko'rsatkich uni tanimaydi. Email avtomatik havola bo'ladi.
`[kvadrat qavs]` saytda sariq bilan belgilanadi — to'ldirilmagan joy degani.

## O'z domenini ulash (masalan `legal.studentclub.uz`)

Tartib muhim — aks holda do'konlardagi havolalar ishlamay qoladi:

1. DNS: `legal` → **CNAME** → `student-club-dev.github.io`
2. `dig legal.studentclub.uz +short` GitHub manzilini ko'rsatguncha kuting.
3. Repo → Settings → Pages → Custom domain: `legal.studentclub.uz` → **Enforce HTTPS**.
   (GitHub o'zi `CNAME` faylini yaratadi.)
4. Ilovada `LegalLinks.BASE` ni `https://legal.studentclub.uz` ga almashtiring.
5. App Store Connect va Play Console'dagi Privacy Policy / Support URL'ni yangilang.
   Eski `github.io/beeloc-business/...` manzillari GitHub tomonidan yangi domenga yo'naltiriladi.
