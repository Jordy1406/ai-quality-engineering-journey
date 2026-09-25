# Minggu 1 — Konsep Dasar LLM (dari sudut pandang QA)

Semua angka di catatan ini berasal dari run nyata di repo ini, 25 Sep 2026, model `gemini-2.5-flash`.
Script: [`experiments/token_explorer.py`](../experiments/token_explorer.py), [`experiments/system_prompt_demo.py`](../experiments/system_prompt_demo.py), [`scripts/check_setup.py`](../scripts/check_setup.py).

---

## 1. Token

**Apa itu:** LLM tidak membaca huruf atau kata, tapi **token**, yaitu potongan teks (bisa satu kata utuh, sebagian kata, angka, atau tanda baca). Semua hal di LLM dihitung dalam token: **biaya**, **batas panjang input**, dan **batas panjang jawaban**.

**Hasil `token_explorer.py`:**

| Teks | Karakter | Token | Karakter/token |
|---|---|---|---|
| Saya ingin transfer uang ke rekening teman saya. | 48 | 10 | 4.8 |
| I want to transfer money to my friend's account. | 48 | 13 | 3.7 |
| gw mau tf duit ke rek temen gw dong | 35 | 11 | 3.2 |
| Rp1.500.000 | 11 | 11 | 1.0 |
| Pertanggungjawaban | 18 | 5 | 3.6 |
| BBCA BBRI TLKM | 14 | 7 | 2.0 |

**Temuan:**
- 🤔 **Di luar dugaan:** kalimat Indonesia formal (10 token) justru **lebih hemat** daripada padanan Inggrisnya (13 token). Anggapan umum "bahasa non-Inggris selalu lebih boros token" tidak berlaku untuk kalimat ini di tokenizer Gemini. Satu contoh belum cukup buat generalisasi, jadi perlu dites dengan lebih banyak kalimat.
- **Bahasa gaul lebih boros:** "gw mau tf duit..." cuma 35 karakter tapi 11 token (3.2 karakter/token). Singkatan dan slang jarang muncul di data latih, jadi dipecah lebih kecil.
- **Angka sangat boros:** `Rp1.500.000` = **1 token per karakter**. Ini relevan untuk domain finance yang penuh nominal, dan salah satu alasan LLM kadang salah menghitung angka.
- **Kode saham** (`BBCA BBRI TLKM`) juga dipecah-pecah, karena bagi tokenizer itu bukan kata umum.

**Kenapa penting untuk QA:** test yang mengirim banyak data angka atau slang akan lebih mahal. Perilaku model juga bisa berbeda antara bahasa formal, bahasa campur, dan bahasa Inggris. Ini akan diuji di Minggu 4–5 (golden dataset formal vs informal).

---

## 2. Thinking tokens (bonus temuan)

`gemini-2.5-flash` adalah model yang **"berpikir" dulu** sebelum menjawab. Token berpikir ini **tidak terlihat di jawaban, tapi tetap dihitung** (dan ditagih).

| Prompt | Output token | Thinking token |
|---|---|---|
| "Balas hanya dengan satu kata: OK" | 1 | 18–19 |
| "Saham apa yang bagus dibeli bulan ini?" (tanpa system prompt) | 863 | **1,179** |

**Kenapa penting untuk QA:** kalau biaya dihitung dari output token saja, perkiraan bisa **meleset lebih dari 2x**. Biaya dan latency harus diukur dari `usage_metadata`, bukan ditebak dari panjang jawaban.

---

## 3. System prompt

**Apa itu:** instruksi "di belakang layar" yang menentukan peran, gaya, dan aturan model. User tidak melihatnya, tapi model memprioritaskannya.

**Hasil `system_prompt_demo.py`** (pertanyaan sama: *"Saham apa yang bagus dibeli bulan ini?"*, temperature 0):

| System prompt | Input token | Output token | Latency | Perilaku |
|---|---|---|---|---|
| Tidak ada | 11 | 863 | 12.2 s | Jawaban panjang ±3.600 karakter: tips riset fundamental, daftar sektor, disclaimer di akhir |
| CS bank (maks. 2 kalimat, dilarang rekomendasi saham) | 47 | 36 | 2.2 s | Menolak sopan + arahkan ke penasihat berizin OJK, persis 2 kalimat |
| "English, exactly one sentence" | 22 | 14 | 2.1 s | *"As an AI, I cannot provide financial advice or specific stock recommendations."* |

*Baris "Tidak ada" berasal dari run terpisah, karena run pertama kena error 503 (lihat Catatan).*

**Temuan:**
- System prompt **menambah input token** (11 → 47), tapi dalam kasus ini **memangkas output token 96%** (863 → 36) dan latency dari 12 s ke 2 s. Instruksi yang jelas justru bisa menghemat biaya.
- System prompt adalah **spesifikasi** perilaku bot, jadi bisa dijadikan dasar test case: "maks. 2 kalimat", "tidak menyebut kode saham", "selalu arahkan ke OJK".
- System prompt **bukan pengaman yang absolut**. User bisa mencoba membongkarnya (*prompt injection*). Ini diuji di `tests/test_llm_output.py` (canary token, Tahap 4) dan dibahas mendalam di Minggu 11 (red-teaming).

---

## 4. Context window

**Apa itu:** jumlah token maksimum yang bisa "dilihat" model dalam satu request, yaitu system prompt + riwayat chat + dokumen + pertanyaan. Selain itu ada batas terpisah untuk panjang jawaban.

**Dari API (`client.models.get`):**
- Context window `gemini-2.5-flash`: **1,048,576 token input**
- Maks. output: **65,536 token** (thinking token ikut memakan jatah ini)

**Kenapa penting untuk QA:**
- Besar bukan berarti sempurna. Informasi di tengah konteks yang sangat panjang bisa "terlewat" (*lost in the middle*). Ini akan relevan di RAG (Minggu 3): lebih baik mengambil potongan dokumen yang relevan daripada memasukkan semua dokumen.
- Makin panjang input, makin mahal dan lambat. Test perlu memantau ukuran prompt.
- Kalau output kepotong karena batas token, JSON bisa jadi tidak valid. Ini salah satu hal yang ditangkap oleh cek schema.

---

## 5. Temperature & non-determinism

**Temperature** mengatur seberapa "acak" model memilih token berikutnya:
- **0** → hampir selalu memilih token paling mungkin. Cocok untuk ekstraksi data dan klasifikasi.
- **1.0** → lebih bervariasi dan kreatif. Cocok untuk brainstorming.

**Non-determinism:** input yang sama bisa menghasilkan output berbeda. Bahkan di temperature 0, output **tidak dijamin 100% identik**, karena ada faktor server (batching, floating point, pembaruan model).

**Implikasi terbesar untuk QA:**

| Test tradisional | Test LLM |
|---|---|
| `assert output == "expected"` | Cek **properti**: format JSON valid, nilai kunci benar, tidak ada konten terlarang |
| 1 run lulus = lulus | Jalankan N kali, ukur **pass rate** (mirip menangani flaky test) |
| Gagal = bug | Gagal bisa berarti bug, variasi normal, atau server error |

**Bukti dari Tahap 3** (prompt yang sama 10x per temperature, [hasil lengkap](../experiments/results/temperature_20260925-211643.md)):

| Model | Temperature | Jawaban unik dari 10 |
|---|---|---|
| `gemini-3.5-flash-lite` | 0 | **6** |
| `gemini-3.5-flash-lite` | 1.0 | **7** |
| `gemini-2.5-flash` | 0 | **2** (dari 8 run, kuota habis) |

- Temperature 0 **terbukti tidak deterministik** di kedua model.
- Di `gemini-3.5-flash-lite`, temperature 0 hampir seacak 1.0. **Dugaan** (belum dibuktikan): model generasi baru ini "berpikir" dulu sebelum menjawab, dan dokumentasi Google untuk Gemini 3 menyarankan temperature dibiarkan di default 1.0. Jadi temperature mungkin tidak berpengaruh seperti di model lama.
- Tiap model beda perilakunya. Setiap kali **ganti model**, pass rate harus **diukur ulang**. Ini bentuk *regression testing* di dunia LLM.
- `CelenganGenZ` vs `Celengan GenZ` dihitung sebagai 2 jawaban berbeda. Perbandingan string mentah terlalu kaku, jadi perlu normalisasi atau cek semantik.

---

## Catatan: error 503 saat eksperimen

Saat menjalankan `system_prompt_demo.py`, Gemini membalas **503 UNAVAILABLE** (*"This model is currently experiencing high demand"*). Retry otomatis di `llm_client.py` jalan 3x (jeda 5 s, 10 s, 20 s) tapi masih gagal. Run berikutnya beberapa saat kemudian berhasil.

**Pelajaran:** API LLM bisa gagal karena **beban server**, bukan karena kode kita. Test suite LLM harus membedakan *kegagalan kualitas* dari *kegagalan infrastruktur*. Ide ini akan dipakai lagi di Project 2 (AI failure triage: bug vs flaky vs environment).
