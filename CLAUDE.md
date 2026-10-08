# fitnes-objave: navodila za pripravo objav

Ta repozitorij hrani vse za carousele profila **@fitnesdanijel** (Instagram `fitnesdanijel`, TikTok `fitnes.danijel`). Lastnik je Danijel; z njim se pogovarjaj v slovenščini, objave pa so v **srbščini, latinica, ekavica**.

## Kaj se objavlja

- Carousel 7 slajdov, 1080 × 1350 JPG: naslovnica, 5 nasvetov, zaključek.
- Ritem: **ponedeljek, sreda, petek ob 10:00** (Europe/Ljubljana), samo **Instagram + TikTok**.
- Omejitev brezplačnega Metricoola: 20 objav na mesec, vsako omrežje šteje posebej. Torej **največ 10 carouselov na koledarski mesec**. Števec se ponastavi 1. v mesecu. Facebooka ne dodajaj.
- Cik-cak: objave se izmenjujejo med `"type": "plan"` (zaključek "Napiši PLAN u komentar i šaljem ti link u poruku", vodi na smrsajza21dan.com) in `"type": "follow"` (zaključek "Zaprati", z napovedjo naslednje teme). Zadnja objava v `plan/dnevnik.md` pove, kateri tip je na vrsti.
- Cilj vsebine: koristen nasvet, ki gradi zaupanje. Brez obljub o številu izgubljenih kilogramov, brez diagnoz. Trditve naj bodo zmerne in točne. Pri temah o bolečinah ali poškodbah v opis dodaj napotek k zdravniku ali fizioterapevtu.

## Dizajn (ne spreminjaj brez Danijelove želje)

- Barve: modra `#1F3BE0`, krem `#FBF3E2`, črna `#111111`.
- Pisavi: Barlow Condensed 900 (naslovi), Barlow (besedilo).
- Lik: izrezane poze v `lik/`. Imena poz za `"pose"` so v slovarju `POSES` v `orodja/naredi.py`: `ledja, pokazuje, dupli, povrce, voda, obrok, cucanj, sklek, trk, hod-napred, hod-profil, san`. Datoteki `lik-04-odmor.png` in `lik-14-okret.png` nista v uporabi (prva ima svetel madež, druga je list s 4 pogledi).
- Postavitev se namenoma menja, da objave niso enake: 3 različice naslovnice, 4 različice slajda z nasvetom (lok desno, lok levo, modra podlaga, pas zgoraj) in 2 zaključka. Izbiro določa številka objave v `orodja/naredi.py`; barve, pisave in ton besedila ostanejo vedno isti. Po želji lahko objavi v JSON dodaš `"cover_layout"` in `"layouts"`.
- Znotraj ene objave naj se poza ne ponovi. Zaključek tipa plan uporablja `pokazuje`. Poza naj se vsaj približno ujema z vsebino slajda.
- Nove poze: Danijel jih pošlje sam. Ozadje odstraniš s `orodja/cut.py` (prilagodi poti), datoteko dodaš v `lik/` in vnos v `POSES`.

## Postopek za nov mesec

1. `npm install` (pisave) in preveri, da deluje `python3 -c "import playwright"`; Chromium je v okolju že nameščen.
2. Preberi `plan/dnevnik.md` (kaj je že objavljeno) in `plan/teme.md` (zaloga tem). Ne ponavljaj tem.
3. Izračunaj datume: vsi ponedeljki, srede in petki v mesecu, **največ 10**. Če jih je več, izpusti zadnje.
4. Napiši `plan/LLLL-MM.json` po vzoru `plan/2026-10.json`. Številke `n` se nadaljujejo od zadnje v dnevniku. Omejitve dolžin: `title` do približno 25 znakov, `body` 1 do 2 kratki povedi, `action` do približno 40 znakov, `word` 3 do 6 črk.
5. Izriši: `python3 orodja/naredi.py plan/LLLL-MM.json`. Skript sam zmanjša pisavo, kjer je treba, in izpiše `OPOZORILO`, če se kaj še vedno preliva; takrat skrajšaj besedilo.
6. **Poglej vsak `objave/dan-NN/pregled.jpg`** in popravi prekrivanja, odrezano besedilo ali poze, ki ne sodijo k vsebini.
7. Commit in push na `main`. Zapomni si SHA zadnjega commita.
8. Razporedi v Metricoolu (`createScheduledPost`, `blogId` **7294989**, časovni pas `Europe/Ljubljana`). Slike podaj kot
   `https://raw.githubusercontent.com/connectdigitalforce-eng/fitnes-objave/<SHA>/objave/dan-NN/slajd-0X.jpg` (vedno s SHA, ne z `main`, zaradi predpomnilnika).
   `providers`: instagram in tiktok; `instagramData`: `{"type":"POST","showReelOnFeed":true}`; `tiktokData`: `{"title": <tiktok_title>, "privacyOption":"PUBLIC_TO_EVERYONE","autoAddMusic":true,"photoCoverIndex":0}`; `text`: polje `caption`.
   Pred tem z `getScheduledPosts` preveri, da za te datume še ni objav.
9. Dopolni `plan/dnevnik.md`, commit in push.
10. Danijelu pošlji kratek povzetek v slovenščini: datumi, naslovi, povezava do Metricoola in opomnik, da lahko vsako objavo tam popravi ali izbriše.

## Česar ne delaj

- Ne odgovarjaj na komentarje in ne pošiljaj sporočil; to dela Danijel sam.
- Ne objavljaj več kot 10 carouselov na mesec in ne dodajaj omrežij.
- Repozitorij je javen: vanj ne dajaj ničesar zasebnega.
