# Retina Cannon

> _"What if I took the live camera feed and ran it through a shader that makes everything look like a 1970s vector art fever dream?"_
> — someone who had clearly seen too many Rutt-Etra videos at 2am.

**Retina Cannon** è un motore visuale real-time per Raspberry Pi. Cattura il feed live dalla Pi Camera, lo spara in una pipeline GLSL e lo ridisegna su schermo tramite DRM/KMS + OpenGL ES — senza X11, senza Wayland, senza scuse. Direttamente sul framebuffer, come i veri duri.

Il risultato? L'immagine reale del mondo filtrata attraverso l'estetica di una macchina grafica degli anni '70 che ha bevuto acido. O resa in ASCII. Dipende dall'umore.

---

## Cosa fa

Ci sono due effetti principali, selezionabili al volo:

### Rutt-Etra CRT
Ispirato al [Rutt/Etra Scan Processor](https://en.wikipedia.org/wiki/Rutt/Etra_Video_Synthesizer) — un sintetizzatore video analogico del 1973 che defleggeva le scanline in base alla luminanza del segnale. Qui lo stesso concetto, in GLSL, su un Pi, a 20 FPS. La luminanza del frame live deforma le righe di scansione, aggiunge curvatura CRT, vignette, grain. Il tuo volto diventa un oscilloscopio.

### ASCII Cam
Prende ogni pixel della camera e lo mappa su un glifo di un font 8×8 hardcoded nel shader. La luminanza decide il carattere. Il risultato è quella cosa che guardavi affascinato su YouTube nel 2007 e che ora gira in tempo reale su un hardware che costa 40€.

---

## Stack tecnico (per chi vuole sapere come è fatto)

```
Pi Camera (BGR888, 1640×1232)
    │
    │  Picamera2 + libcamera
    ▼
camera capture thread  ──(threading.Lock)──▶  frame buffer
                                                  │
                                        render callback (C)
                                                  │
                                          glTexSubImage2D
                                                  │
                                        GLSL fragment shader
                                                  │
                                        DRM/KMS output (fullscreen)
```

- **Cattura** — thread daemon che gira in continuo e aggiorna l'ultimo frame dietro un lock. Il render loop legge sempre il frame più fresco disponibile, mai blocca.
- **Render** — il loop C di `kms-glsl` chiama una callback Python ad ogni frame. Lì si carica la texture e si passano i uniform (modo colore, wave, densità, effetto, aspect ratio camera).
- **Shader** — tutta la logica visuale è in `rutt_etra.frag`. Il Python passa parametri, la GPU fa il lavoro vero.
- **Tastiera** — thread separato su `/dev/tty` in raw mode, con `ICANON`, `ECHO` e `ISIG` spenti. Ctrl+C arriva come `\x03` invece di SIGINT: questo permette shutdown pulito senza far incazzare il loop C.
- **stdin** — sostituito con una pipe silenziosa all'avvio, così `kms-glsl` non interpreta l'attività su stdin come "utente che ha premuto qualcosa di strano".

---

## Requisiti

- Raspberry Pi con camera abilitata
- `python3`, `libcamera`, `picamera2`
- [`kms-glsl`](https://github.com/keithzg/kms-glsl) in una di queste posizioni:
  - `KMS_GLSL_DIR` (variabile d'ambiente)
  - `../kms-glsl` (directory sorella — layout consigliato)
  - `~/kms-glsl`

Layout consigliato:
```
~/kms-glsl/       ← dipendenza esterna
~/retinacannon/   ← questa repo
```

---

## Avvio

```bash
./start_cannon.sh
```

Con shader specifico:
```bash
./run_rutt.sh     # Rutt-Etra (default)
./run_base.sh     # passthrough camera nuda
```

Con kms-glsl in posizione non standard:
```bash
KMS_GLSL_DIR=/dove/sta/kms-glsl ./start_cannon.sh
```

---

## Controlli runtime

| Tasto | Effetto |
|---|---|
| `↑` / `↓` | Cicla il modo colore |
| `←` / `→` | Rutt-Etra: wave intensity — ASCII: densità caratteri |
| `Spazio` | Alterna effetto (Rutt-Etra ↔ ASCII Cam) |
| `V` | Cicla view mode (16:9 → 4:3 → Fisheye) |
| `F` | Toggle FPS log sul terminale |
| `Ctrl+C` | Shutdown pulito |

---

## Modi colore

**Rutt-Etra** — `B/W` · `Colors` · `Prism Warp` · `Acid Melt`

**ASCII Cam** — `Color symbols` · `Monochrome symbols` · `Inverted mono` · `Inverted color`

Defaults all'avvio: Rutt parte su `Prism Warp`, ASCII su `Color symbols`. Entrambe scelte da qualcuno con un certo senso del dramma visivo.

---

## Performance

~20 FPS sull'hardware target. Stabile, verificato. Non è 60 FPS, ma nemmeno il Rutt-Etra originale girava a 60 FPS — e quello costava quanto un'utilitaria.

---

## Note per chi sviluppa

- I float passati a OpenGL via ctypes **vanno wrappati con `c_float()`**. Se l'immagine diventa un mosaico di glitch cosmici, probabilmente hai dimenticato questo.
- Il parser dei tasti freccia gestisce sia `ESC [` che `ESC O` — perché i terminali sono un ecosistema caotico e nessun standard è mai veramente standard.
- I globali (`current_rutt_wave`, `current_effect_mode`, ecc.) vengono scritti dal thread tastiera e letti dal render callback senza lock aggiuntivi. Il GIL di CPython rende queste letture atomicamente sicure. Non è un bug, è una feature deliberata.

---

## Test

Senza hardware Pi (camera + display DRM/KMS) il progetto non si avvia. È previsto.

Su qualunque macchina funziona:
```bash
python3 -m py_compile retina_cannon.py  # check sintattico
bash -n start_cannon.sh                 # check shell
```

Su Pi, avvia e verifica ~20 FPS con tutti i controlli.

---

## Licenza

MIT — [Netmilk Studio sagl](https://netmilk.studio)

Fai quello che vuoi. Attribuisci se puoi. Non rompere niente di importante.
