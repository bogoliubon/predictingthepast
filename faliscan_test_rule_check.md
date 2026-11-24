# Rules needed to map the 35 Faliscan test texts back to Latin

**Status: draft for YQ to check.** This lists, for every text in the Faliscan test set
(`faliscan_eval_set.json`, 35 texts), the words that differ from their Latin equivalent
and the changes needed to turn each one into Latin spelling. It then compares those
changes with the rules in `Faliscan-Latin-sound-correspondences.md` ("the table").

What we need from YQ:

1. **Check the Latin equivalents** in the per-text tables (section 4). They are a first
   reading. Only a few were checked against Bakkum's commentary (*keset* = *gessit*,
   *cauio pauiceo* = Gavius Pavicius, *cauiacue* = Gaviaque, *titoi* as a genitive,
   *menerua* as a dative, *felicinate* as a genitive).
2. **Rule on the changes that are missing from the table** (section 2): is each one a
   real correspondence, under what condition, and where in Bakkum?
3. **Give conditions for the ambiguous rules already in the table** (section 3).

## 1. Coverage

A word counts as mapped only if every change it needs is in the rule set. 172 words in
the 35 texts differ from their Latin equivalent.

| Rule set | Changed words fully mapped | Texts fully mapped |
|---|---|---|
| The 5 rules tested so far (-o → -us, -o → -um, cu → qu, p → b, e → ae) | 34 of 172 (20%) | 2 of 35 |
| All rules in the table | 87 of 172 (51%) | 5 of 35 |
| The table plus the missing spelling changes of section 2.1 | 128 of 172 (74%) | 12 of 35 |

Without the four Early Faliscan texts (EF 1-4), which are written without word division
and are partly obscure, the last row is 110 of 141 (78%).

How often each rule of the table is needed:

| Change (Faliscan → Latin) | Texts | Words |
|---|---|---|
| -o → -us | 22 | 45 |
| e → i before a vowel (*uecineo* → *Vecinius*) | 15 | 19 |
| e → i elsewhere (*hec* → *hic*, *dedet* → *dedit*) | 15 | 19 |
| p → b | 14 | 16 |
| -os/-om → -us/-um, with s/m written (*zextos* → *Sextus*) | 4 | 11 |
| e → ae | 7 | 8 |
| ai → ae | 5 | 6 |
| ou/o → u | 5 | 6 |
| drop final d | 5 | 6 |
| cu → qu | 5 | 5 |
| medial f → b | 3 | 4 |
| add final s | 4 | 4 |
| add final m (u already written: *sacru* → *sacrum*) | 2 | 3 |
| -o → -um | 2 | 2 |
| add n before a consonant | 2 | 2 |
| initial f → h | 2 | 2 |
| oi/o → i | 2 | 2 |
| initial h → f | 1 | 1 |
| -ied → -die | 1 | 1 |

## 2. Changes the test set needs that are not in the table

### 2.1 Spelling changes (could become rules)

| Change (Faliscan → Latin) | Texts | Words | Every instance |
|---|---|---|---|
| **c, k or q → g** (no letter g, as with p for b) | 12 | 19 | eqo → ego (EF 1); arcentelom → argentulum (EF 1); eco → ego (EF 3); quto → guttus? (EF 3); kaios → Gaius (EF 4); caui a → Gavia (LF 222-223); cauia → Gavia (LF 222-223); macistratu → magistratum (LF 242); keset → gessit (LF 242); cauia → Gavia (LF 242); cauio → Gavius (MF 11-12); cauio → Gavius (MF 146); caui → Gavi (MF 146); cauio → Gavius (MF 272); cauia → Gavia (MF 42); caui → Gavi (MF 42); canumede → Ganymedes (MF 62); cauiacue → Gaviaque (MF 80); cauio → Gavius (MLF 308) |
| **z → s** | 6 | 7 | zextos → Sextus (EF 1); zertenea → Sertinia (LF 221); folcozeo → Folcosius (LF 330); zextoi → Sexti (LF 330); -olcuzeo → Folcosius (LF 332); zenatuo → senatus (LF/Lat 214); zeruatronia → Servatronia (MF 272) |
| **add final c** (*he* for *hec*) | 5 | 5 | he → hic (LF 220); he → hic (LF 221); he → hic (LF 224-225); hecupa → hic cubant (LF 226); fecupa → hic cubat (MLF 305) |
| **add final r** | 4 | 4 | mate → mater (LF 221); uxo → uxor (LF 222-223); uxo → uxor (LF 242); censo → censor (LtF 232) |
| **add final t** | 3 | 3 | cupa → cubat (LF 221); hecupa → hic cubant (LF 226); fecupa → hic cubat (MLF 305) |
| **double the consonant** (geminates written single) | 4 | 4 | keset → gessit (LF 242); cela → cella (MF 11-12); fuloniacue → Fulloniaque (MLF 313); tulio → Tullius (MLF 346) |
| **k or q → c** | 2 | 4 | f[.f]iqod → finxerunt (EF 1); karai → carae (EF 1); kapena → Capena (EF 4); kaleptia → Caleptia (EF 4) |
| **final d → r** | 2 | 3 | cuestod → quaestor (LF 242); pretod → praetor (LF 242); pretod → praetor (LF/Lat 214) |

Adding these eight raises coverage from 87 to 128 words.

### 2.2 Differences that a spelling rule cannot fix

| Difference | Texts | Words | Every instance |
|---|---|---|---|
| Different ending or form (genitives in -oi, -o(s), -es; *pipafo* against Latin *bibam*) | 15 | 25 | f[.f]iqod → finxerunt (EF 1); porded → (por)dedit (EF 1); pepara[i] → peperi (EF 1); douiad → det (EF 1); uotenosio → Volteni (EF 3); titias → Titiae (EF 3); duenas → bonae (EF 3); ues → vos (EF 4); petrunes → Petronia? (LF 226); zextoi → Sexti (LF 330); menerua → Minervae (LF/Lat 214); zenatuo → senatus (LF/Lat 214); locies → Lucii (MF 11-12); calitenes → Calitenes (MF 265); aronto → Arruntis (MF 265); cesies → Caesii (MF 265); lartio → Lartis (MF 265); fasies → ? (MF 41); satelie → Satelies (MF 42); felicinate → Felicinatis (MF 42); pipafo → bibam (MF 59-60); titoi → Titi (MLF 305); titio → Titi (f.) (MLF 312); uoltilio → Voltili (f.) (MLF 346); facet → fecit (MF 470) |
| r or l left out inside the word | 3 | 5 | uotenosio → Volteni (EF 3); uotilia → Voltilia (LF 222-223); maci → Marci (LF 222-223); acacelini → Acarcelini (LF 222-223); clipeaio → Clipearius (MF 470) |
| Other vowel differences | 6 | 7 | maxomo → Maximus (LF 220); uootum → votum (LF/Lat 214); cuncaptum → conceptum (LF/Lat 214); maxomo → Maximus (MF 272); canumede → Ganymedes (MF 62); manomo → Manumus? (MF 80); oufilo → Aufilus (MF 470) |
| du → b (archaic, shared with early Latin *duenos*) | 1 | 2 | duenom → bonum (EF 3); duenas → bonae (EF 3) |
| Meaning unclear | 5 | 7 | pescosal → ? (Cap 431); afluc → ? (Cap 431); huticilom → ? (EF 1); propramom → ? (EF 2); pramod → ? (EF 2); quto → guttus? (EF 3); file → filius? (MLF 308) |

Five texts are also written without word division, or with almost none: EF 1, EF 2,
EF 3, EF 4 and MLF 308.

## 3. Rules in the table that need a condition

- **-o → -us or -um.** Needed 45 times as -us and twice as -um, but some -o endings
  are already correct Latin (*cupido*, *cuando*, the dative *numesio*). Which -o should
  be rewritten? Restricting the rule to names in -io/-eo would catch most cases.
- **e → i.** Needed 38 times, but most e stay e. Before a vowel (*uecineo*, *fileo*) the
  context is clear. Elsewhere (*hec*, *dedet*, *keset*, *menerua*, *letei*) it depends on
  the word.
- **p → b and c → g.** Most p and c stay as they are. In this test set nearly all the
  cases are a few words: *cupat*/*cupa* (cubat), *cauio*/*cauia* (Gavius, Gavia), *pi*/*pis* (bis).
- **Formula words.** *hec/he cupat*, *cauio/cauia*, *uxo*, *fileo/hileo* and
  *loferta/loifirta* recur across the tomb inscriptions. A short word list may be more
  reliable for these than stacked rules.

## 4. The 35 texts

Only words that differ from their Latin equivalent are listed. In the last column,
**bold** = one of the 5 rules tested so far; plain = in the table; *italic* = not in the table.

### Cap 431

`pescosal quod afluc plaria t l dedet libes feron dono m mereto`

| Faliscan | Latin | Changes needed |
|---|---|---|
| dedet | dedit | e → i elsewhere |
| libes | libens | add n before consonant |
| dono | donum | **-o → -um** |
| mereto | merito | e → i elsewhere |
| pescosal | ? | *meaning unclear* |
| afluc | ? | *meaning unclear* |

### Cap 435

`m t u genucilio sen l feroneai dedit`

| Faliscan | Latin | Changes needed |
|---|---|---|
| genucilio | Genucilius | **-o → -us** |
| feroneai | Feroniae | ai → ae, e → i before a vowel |

### EF 1

`ceres far---e---tom ------uf----ui--m ------adeuios mamazextosmed f-fiqod prauiosurnam sociaipordedkarai eqournelatitelafitaidupes arcen telomhuticilom pe parai-douiad`

| Faliscan | Latin | Changes needed |
|---|---|---|
| euios | Euius | -os/-om → -us/-um |
| zextos | Sextus | *z → s*, -os/-om → -us/-um |
| med | me | drop final d |
| f[.f]iqod | finxerunt | *k/q → c*, *different ending or form* |
| prauios | Pravius | -os/-om → -us/-um |
| sociai | sociae | ai → ae |
| porded | (por)dedit | *different ending or form* |
| karai | carae | *k/q → c*, ai → ae |
| eqo | ego | *c/k/q → g* |
| arcentelom | argentulum | *c/k/q → g*, -os/-om → -us/-um |
| huticilom | ? | -os/-om → -us/-um, *meaning unclear* |
| pepara[i] | peperi | *different ending or form* |
| douiad | det | *different ending or form* |
| (whole text) |  | *no word division* |

### EF 2

`propramom pramedumompramodpramedumom pramodpropramod pr amodumom`

| Faliscan | Latin | Changes needed |
|---|---|---|
| propramom | ? | -os/-om → -us/-um, *meaning unclear* |
| pramod | ? | drop final d, *meaning unclear* |
| (whole text) |  | *no word division* |

### EF 3

`ecoquto-euotenosiotitiasduenomduenassaluetoduoltene`

| Faliscan | Latin | Changes needed |
|---|---|---|
| eco | ego | *c/k/q → g* |
| quto | guttus? | *c/k/q → g*, *meaning unclear* |
| uotenosio | Volteni | *different ending or form*, *r/l left out inside the word* |
| titias | Titiae | *different ending or form* |
| duenom | bonum | *du → b*, -os/-om → -us/-um |
| duenas | bonae | *du → b*, *different ending or form* |
| salue[to]d | salveto | drop final d |
| (whole text) |  | *no word division* |

### EF 4

`e--azieputilepekapenarufiakaleptiauessaluetesociaiofetioskaiosuelosa manossaluetosaluesseiteiofeteqemeneses-eie`

| Faliscan | Latin | Changes needed |
|---|---|---|
| kapena | Capena | *k/q → c* |
| kaleptia | Caleptia | *k/q → c* |
| ues | vos | *different ending or form* |
| sociai | sociae | ai → ae |
| ofetios | Ofetius | -os/-om → -us/-um |
| kaios | Gaius | *c/k/q → g*, -os/-om → -us/-um |
| uelos | Velus | -os/-om → -us/-um |
| amanos | Amanus | -os/-om → -us/-um |
| seite | sitis | e → i elsewhere, add final s |
| (whole text) |  | *no word division* |

### LF 220

`uoltio uecineo maxomo iuneo he cupat caaconia`

| Faliscan | Latin | Changes needed |
|---|---|---|
| uoltio | Voltius | **-o → -us** |
| uecineo | Vecinius | **-o → -us**, e → i before a vowel |
| maxomo | Maximus | **-o → -us**, *other vowel difference* |
| iuneo | Iunius | **-o → -us**, e → i before a vowel |
| he | hic | e → i elsewhere, *add final c* |
| cupat | cubat | **p → b** |

### LF 221

`uipia zertenea loferta marci acarcelini mate he cupa`

| Faliscan | Latin | Changes needed |
|---|---|---|
| uipia | Vibia | **p → b** |
| zertenea | Sertinia | *z → s*, e → i elsewhere, e → i before a vowel |
| loferta | liberta | medial f → b, oi/o → i |
| mate | mater | *add final r* |
| he | hic | e → i elsewhere, *add final c* |
| cupa | cubat | **p → b**, *add final t* |

### LF 222-223

`caui a uecinea uotilia maci acacelini uxo marcio acarcelinio cauia uecinea heccupat`

| Faliscan | Latin | Changes needed |
|---|---|---|
| caui a | Gavia | *c/k/q → g* |
| uecinea | Vecinia | e → i before a vowel |
| uotilia | Voltilia | *r/l left out inside the word* |
| maci | Marci | *r/l left out inside the word* |
| acacelini | Acarcelini | *r/l left out inside the word* |
| uxo | uxor | *add final r* |
| marcio | Marcius | **-o → -us** |
| acarcelinio | Acarcelinius | **-o → -us** |
| cauia | Gavia | *c/k/q → g* |
| uecinea | Vecinia | e → i before a vowel |
| hec | hic | e → i elsewhere |
| cupat | cubant | **p → b** |

### LF 224-225

`ca uecineo uoltio he cupat meania ca uecineo ca mania`

| Faliscan | Latin | Changes needed |
|---|---|---|
| uecineo | Vecinius | **-o → -us**, e → i before a vowel |
| uoltio | Voltius | **-o → -us** |
| he | hic | e → i elsewhere, *add final c* |
| cupat | cubat | **p → b** |
| uecineo | Vecinius | **-o → -us**, e → i before a vowel |

### LF 226

`tito acarcelinio ma fi pop petrunes ce f hecupa`

| Faliscan | Latin | Changes needed |
|---|---|---|
| tito | Titus | **-o → -us** |
| acarcelinio | Acarcelinius | **-o → -us** |
| petrunes | Petronia? | *different ending or form* |
| hecupa | hic cubant | e → i elsewhere, *add final c*, **p → b**, *add final t* |

### LF 228-229

`_marcio cesula tiperilia tef`

| Faliscan | Latin | Changes needed |
|---|---|---|
| marcio | Marcius | **-o → -us** |
| cesula | Caesula | **e → ae** |
| tiperilia | Tiberilia | **p → b** |

### LF 242

`-a protacio m f macistratu keset cuestod pi pretod pis cauia uxo a f`

| Faliscan | Latin | Changes needed |
|---|---|---|
| protacio | Protacius | **-o → -us** |
| macistratu | magistratum | *c/k/q → g*, add final m |
| keset | gessit | *c/k/q → g*, *double the consonant*, e → i elsewhere |
| cuestod | quaestor | **cu → qu**, **e → ae**, *final d → r* |
| pi | bis | **p → b**, add final s |
| pretod | praetor | **e → ae**, *final d → r* |
| pis | bis | **p → b** |
| cauia | Gavia | *c/k/q → g* |
| uxo | uxor | *add final r* |

### LF 330

`uoltio folcozeo zextoi fi`

| Faliscan | Latin | Changes needed |
|---|---|---|
| uoltio | Voltius | **-o → -us** |
| folcozeo | Folcosius | **-o → -us**, *z → s*, e → i before a vowel |
| zextoi | Sexti | *z → s*, *different ending or form* |

### LF 332

`celio-olcuzeo ---io poplia e uelcei f`

| Faliscan | Latin | Changes needed |
|---|---|---|
| celio | Caelius | **e → ae**, **-o → -us** |
| -olcuzeo | Folcosius | **-o → -us**, *z → s*, e → i before a vowel |
| ---io | -ius | **-o → -us** |
| poplia | Publia | ou/o → u, **p → b** |

### LF/Lat 214

`menerua sacru la cotena la f pretod de zenatuo sententiad uootum dedet cuando datu rected cuncaptum`

| Faliscan | Latin | Changes needed |
|---|---|---|
| menerua | Minervae | e → i elsewhere, *different ending or form* |
| sacru | sacrum | add final m |
| pretod | praetor | **e → ae**, *final d → r* |
| zenatuo | senatus | *z → s*, *different ending or form* |
| sententiad | sententia | drop final d |
| uootum | votum | *other vowel difference* |
| dedet | dedit | e → i elsewhere |
| cuando | quando | **cu → qu** |
| datu | datum | add final m |
| rected | recte | drop final d |
| cuncaptum | conceptum | *other vowel difference* |

### LtF 232

`harisp sor - anco ma censo`

| Faliscan | Latin | Changes needed |
|---|---|---|
| censo | censor | *add final r* |

### LtF 341

`m aco nio ia - rutil ce ilia co-`

| Faliscan | Latin | Changes needed |
|---|---|---|
| aco..nio | Aconius | **-o → -us** |
| ce..ilia | Caelia | **e → ae** |

### LtF 377

`-muniorecena- numesio marte ddlm`

| Faliscan | Latin | Changes needed |
|---|---|---|
| munio | Munius | **-o → -us** |
| marte | Marti | e → i elsewhere |

### MF 11-12

`uolti teti cauio paui ceo locies cela`

| Faliscan | Latin | Changes needed |
|---|---|---|
| cauio | Gavius | *c/k/q → g*, **-o → -us** |
| pauiceo | Pavicius | **-o → -us**, e → i before a vowel |
| locies | Lucii | ou/o → u, *different ending or form* |
| cela | cella | *double the consonant* |

### MF 146

`cauio leuelio caui hileo ianta --lnia hec cupat ----ta`

| Faliscan | Latin | Changes needed |
|---|---|---|
| cauio | Gavius | *c/k/q → g*, **-o → -us** |
| leuelio | Levelius | **-o → -us** |
| caui | Gavi | *c/k/q → g* |
| hileo | filius | initial h → f, e → i before a vowel, **-o → -us** |
| hec | hic | e → i elsewhere |
| cupat | cubant | **p → b** |

### MF 265

`poplia calitenes aronto cesies lartio uxor`

| Faliscan | Latin | Changes needed |
|---|---|---|
| poplia | Publia | ou/o → u, **p → b** |
| calitenes | Calitenes | *different ending or form* |
| aronto | Arruntis | *different ending or form* |
| cesies | Caesii | **e → ae**, *different ending or form* |
| lartio | Lartis | *different ending or form* |

### MF 272

`cauio nomes ina maxomo zeruatronia`

| Faliscan | Latin | Changes needed |
|---|---|---|
| cauio | Gavius | *c/k/q → g*, **-o → -us** |
| maxomo | Maximus | **-o → -us**, *other vowel difference* |
| zeruatronia | Servatronia | *z → s* |

### MF 41

`fasies caisia louria louci teti uxor loifirta`

| Faliscan | Latin | Changes needed |
|---|---|---|
| fasies | ? | *different ending or form* |
| caisia | Caesia | ai → ae |
| louria | Luria | ou/o → u |
| louci | Luci | ou/o → u |
| loifirta | liberta | oi/o → i, medial f → b |

### MF 42

`cauia satelie caui felicinate uxor`

| Faliscan | Latin | Changes needed |
|---|---|---|
| cauia | Gavia | *c/k/q → g* |
| satelie | Satelies | *different ending or form* |
| caui | Gavi | *c/k/q → g* |
| felicinate | Felicinatis | *different ending or form* |

### MF 59-60

`foied uino pipafo cra carefo`

| Faliscan | Latin | Changes needed |
|---|---|---|
| foied | hodie | initial f → h, -ied → -die |
| uino | vinum | **-o → -um** |
| pipafo | bibam | **p → b**, medial f → b, *different ending or form* |
| cra | cras | add final s |
| carefo | carebo | medial f → b |

### MF 62

`canumede dies pater cupido menerua`

| Faliscan | Latin | Changes needed |
|---|---|---|
| canumede | Ganymedes | *c/k/q → g*, add final s, *other vowel difference* |
| menerua | Minerva | e → i elsewhere |

### MF 80

`marco pleina marcio manomo cauiacue ueculia uoltilia uentarc------ hec cupant`

| Faliscan | Latin | Changes needed |
|---|---|---|
| marco | Marcus | **-o → -us** |
| marcio | Marcius | **-o → -us** |
| manomo | Manumus? | **-o → -us**, *other vowel difference* |
| cauiacue | Gaviaque | *c/k/q → g*, **cu → qu** |
| hec | hic | e → i elsewhere |
| cupant | cubant | **p → b** |

### MLF 305

`tito uelmineo titoi fecupa`

| Faliscan | Latin | Changes needed |
|---|---|---|
| tito | Titus | **-o → -us** |
| uelmineo | Velminius | **-o → -us**, e → i before a vowel |
| titoi | Titi | *different ending or form* |
| fecupa | hic cubat | initial f → h, e → i elsewhere, *add final c*, **p → b**, *add final t* |

### MLF 308

`cauiouelmineo popliaifile`

| Faliscan | Latin | Changes needed |
|---|---|---|
| cauio | Gavius | *c/k/q → g*, **-o → -us** |
| uelmineo | Velminius | **-o → -us**, e → i before a vowel |
| popliai | Publiae | ou/o → u, **p → b**, ai → ae |
| file | filius? | e → i before a vowel, *meaning unclear* |
| (whole text) |  | *no word division* |

### MLF 310

`cuicto uelmineo _uoxie-eai`

| Faliscan | Latin | Changes needed |
|---|---|---|
| cuicto | Quinctus | **cu → qu**, add n before consonant, **-o → -us** |
| uelmineo | Velminius | **-o → -us**, e → i before a vowel |

### MLF 312

`uoltio uelmineo titio sceua`

| Faliscan | Latin | Changes needed |
|---|---|---|
| uoltio | Voltius | **-o → -us** |
| uelmineo | Velminius | **-o → -us**, e → i before a vowel |
| titio | Titi (f.) | *different ending or form* |
| sceua | Scaeva | **e → ae** |

### MLF 313

`uolta uelmineo fuloniacue`

| Faliscan | Latin | Changes needed |
|---|---|---|
| uelmineo | Velminius | **-o → -us**, e → i before a vowel |
| fuloniacue | Fulloniaque | *double the consonant*, **cu → qu** |

### MLF 346

`m tito tulio uoltilio hescuna`

| Faliscan | Latin | Changes needed |
|---|---|---|
| tito | Titus | **-o → -us** |
| tulio | Tullius | **-o → -us**, *double the consonant* |
| uoltilio | Voltili (f.) | *different ending or form* |

### MF 470

`oufilo clipeaio letei fileo met facet`

| Faliscan | Latin | Changes needed |
|---|---|---|
| oufilo | Aufilus | **-o → -us**, *other vowel difference* |
| clipeaio | Clipearius | **-o → -us**, *r/l left out inside the word* |
| letei | Leti | e → i elsewhere |
| fileo | filius | e → i before a vowel, **-o → -us** |
| met | me | drop final d |
| facet | fecit | e → i elsewhere, *different ending or form* |
