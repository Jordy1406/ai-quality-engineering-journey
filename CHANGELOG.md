# Changelog

Catatan rinci setiap perubahan di repo ini, urut dari yang terbaru.
Format per entri: **tanggal — minggu/tahap roadmap**, lalu *Ditambahkan / Diubah / Diperbaiki / Diverifikasi / Catatan*.

---

## 2026-09-25 — Minggu 1 · Tahap 4 selesai: test pytest untuk output LLM

### Ditambahkan (dibuat di awal, dibahas & dijalankan di tahap ini)
- **`src/llm_qa/validators.py`**: 3 jenis pengecekan output LLM:
  - `strip_code_fences(text)`: membuang pembungkus ```` ```json ... ``` ```` yang sering ditambahkan model.
  - `check_json_schema(text, schema)` → `SchemaCheck(ok, data, errors)`: parse + validasi JSON dengan pydantic. Error dikembalikan dalam bentuk mudah dibaca (`amount: Input should be greater than 0`).
  - `find_forbidden(text, patterns, canary)` → daftar nama pelanggaran (list kosong = aman). Pola default: angka 16 digit (kartu/NIK), janji untung pasti (dengan pengecualian negasi langsung "tidak dijamin"), rekomendasi beli kode saham 4 huruf kapital. Plus deteksi **canary token** (kode rahasia di system prompt, kalau muncul di jawaban berarti prompt bocor).
  - `pass_rate(outcomes)`: rasio lulus dari N run.
- **`src/llm_qa/tasks.py`**: 2 fitur LLM yang dites:
  - `Transaction` (pydantic, `extra="forbid"`): `amount` int > 0, `currency` = "IDR", `category` ∈ {transfer, payment, top_up, withdrawal}, `bank`, `counterparty`.
  - `extract_transaction(client, message, temperature=0, json_mode=False)`: ekstraksi transaksi dari pesan bahasa Indonesia.
  - `ask_cs_assistant(client, question)`: bot CS "Bank Nusantara" dengan aturan ketat + canary `CS_CANARY`.
- **`tests/conftest.py`**: fixture `client` (satu per sesi test), otomatis *skip* kalau API key tidak ada.
- **`tests/test_validators.py`** (offline, 18 test + 1 xfail): menguji checker-nya sendiri ("test the tester"), yaitu 6 jenis JSON tidak valid, deteksi konten terlarang, negasi yang tidak boleh ter-flag, dan xfail *strict* yang mendokumentasikan kelemahan regex terhadap negasi di awal kalimat.
- **`tests/test_llm_output.py`** (live, marker `live`):
  1. `test_extraction_matches_schema_and_values`: 4 pesan × 2 mode (prompt-only & JSON mode) = 8 test.
  2. `test_cs_answer_has_no_forbidden_content`: 3 pertanyaan (prompt injection, minta tip saham, pertanyaan normal).
  3. `test_extraction_pass_rate_at_high_temperature`: 5 run di temperature 1.0, pass rate minimal 80%.
- **`.github/workflows/tests.yml`**: CI (dijelaskan di entri Tahap 1). Di-commit di tahap ini karena folder `tests/` sekarang ikut masuk repo.

### Diubah
- **`README.md`**: tugas 4 → ✅, tugas 5 → ⏳ Next. Bagian *Results* ditambah tabel test suite + 4 *known limitations*.

### Diverifikasi
- `$env:GEMINI_MODEL="gemini-3.5-flash-lite"; pytest -m live -v` → **12 passed** dalam 50.3 s (16 request API).
- `pytest -m "not live"` → 18 passed, 1 xfailed.

### Catatan / pelajaran
- **Semua hijau itu bukan berarti kuat.** 4 input ekstraksi terlalu mudah, jadi perlu kasus sulit (golden dataset Minggu 4).
- Cek berbasis regex rapuh terhadap negasi. Butuh cek semantik (LLM-as-judge, Minggu 5).
- Pass rate dengan 5 run lemah secara statistik (4/5 dan 5/5 sama-sama lulus). Dipilih karena kuota free tier.
- Tracker: tugas test pytest → **Selesai**.

---

## 2026-09-25 — Minggu 1 · Tahap 3 selesai: eksperimen temperature

### Ditambahkan
- **`experiments/results/temperature_20260925-211643.json`** (data mentah semua jawaban) dan **`.md`** (tabel ringkasan + semua jawaban). Keduanya hasil otomatis `temperature_experiment.py`.

### Diubah
- **`README.md`**: tugas 3 → ✅, tugas 4 → ⏳ Next. Bagian *Results* ditambah tabel eksperimen temperature (3 baris: flash-lite temp 0, flash-lite temp 1.0, flash temp 0 parsial) dan 4 poin *what I learned*.
- **`notes/week-01-concepts.md`**: bagian 5 (temperature & non-determinism) diisi bukti angka dari eksperimen ini.

### Diverifikasi
- Perintah: `$env:GEMINI_MODEL="gemini-3.5-flash-lite"; python experiments/temperature_experiment.py --runs 10 --temps 0 1.0 --delay 2`
- **Temperature 0:** 6 jawaban unik dari 10. Terbanyak `CelenganGenZ` (4x). Kemiripan rata-rata 0.474, latency 1.11 s, output 3.4 token.
- **Temperature 1.0:** 7 jawaban unik dari 10. Terbanyak `SakuGenZ` (2x). Kemiripan rata-rata 0.462, latency 1.18 s, output 3.6 token.
- Sempat kena 429 (batas per menit) 2x, dan retry otomatis berhasil.

### Catatan / pelajaran
- **Ganti model:** `gemini-2.5-flash` kuota hariannya habis. `gemini-2.5-flash-lite` ditolak API (*"no longer available to new users"*, 404), dan API menyarankan `gemini-3.5-flash-lite`. Model di-set lewat environment variable **khusus untuk run ini**, jadi `.env` tidak diubah dan default project tetap `gemini-2.5-flash`.
- **Temperature 0 tidak deterministik** di kedua model. Di `gemini-3.5-flash-lite` hampir seacak temperature 1.0 (6 vs 7 unik). Di `gemini-2.5-flash` jauh lebih stabil (2 unik dari 8).
- **Dugaan penyebab** (belum dibuktikan): model Gemini 3 adalah model "thinking", dan dokumentasi Google menyarankan temperature default 1.0 untuk seri ini.
- **Keterbatasan metrik:** `CelenganGenZ` dan `Celengan GenZ` dihitung beda. Perlu normalisasi atau cek semantik ke depannya.
- Tracker: tugas eksperimen temperature → **Selesai**.

---

## 2026-09-25 — Minggu 1 · Tahap 3 (run pertama, belum lengkap): kuota free tier habis

### Diperbaiki
- **`src/llm_qa/llm_client.py`**: tambah `DailyQuotaExceededError`.
  - **Masalah:** error 429 karena **kuota harian** habis ikut di-retry 3x (±35 detik terbuang), padahal pasti gagal sampai kuota reset.
  - **Solusi:** kalau error 429 berasal dari kuota harian (`PerDay` di detail error), langsung gagal dengan pesan jelas tanpa retry. 429 karena batas per menit tetap di-retry seperti biasa.
- **`experiments/temperature_experiment.py`**:
  - **Masalah:** kalau crash di tengah, semua jawaban yang sudah didapat hilang, padahal sudah memakai kuota.
  - **Solusi:** saat `DailyQuotaExceededError`, eksperimen berhenti dengan rapi dan menyimpan hasil parsial. Nama file diberi akhiran `-partial` dan JSON-nya berisi `"complete": false`.

### Diverifikasi
- `pytest -m "not live"` → 18 passed, 1 xfailed. File yang diubah lolos `py_compile`.

### Catatan / temuan
- Run pertama `temperature_experiment.py --runs 10 --temps 0 1.0 --delay 2` berhenti di run ke-9 temperature 0. **Error:** `429 RESOURCE_EXHAUSTED`, `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, **limit: 20** request/hari untuk `gemini-2.5-flash`. Di tengah run juga sempat kena 503 (server penuh).
- **Temuan dari 8 run yang berhasil (temperature 0):** `SakuCuan` ×6, `PundiMuda` ×2 → **temperature 0 tetap tidak deterministik**. Data ini dicatat dari output terminal, karena file hasil belum tersimpan (bug di atas).
- **Dampak ke roadmap:** kuota 20 request/hari sangat ketat. Live test Tahap 4 butuh ±16 request, dan eksperimen ini 20 request, jadi keduanya tidak muat dalam satu hari di free tier `gemini-2.5-flash`.
- Tracker: tugas eksperimen temperature → **Proses**.

---

## 2026-09-25 — Minggu 1 · Tahap 2: Konsep dasar LLM

### Ditambahkan
- **`notes/week-01-concepts.md`**: catatan belajar 5 konsep (token, temperature, system prompt, context window, non-determinism) + bonus thinking tokens. Setiap konsep dijelaskan dengan bukti angka nyata dan implikasinya untuk QA.
- **`experiments/system_prompt_demo.py`**: mengirim satu pertanyaan ("Saham apa yang bagus dibeli bulan ini?") dengan 3 system prompt berbeda (tanpa system prompt, CS bank ketat, "English 1 kalimat") di temperature 0. Menampilkan token input/output, latency, dan jawabannya.
- **`GeminiClient.token_limits()`** di `src/llm_qa/llm_client.py`: membaca batas context window (max input token) dan max output token langsung dari API (`client.models.get`).

### Diubah
- **`experiments/token_explorer.py`**: sekarang juga menampilkan context window dan max output model di baris pertama.
- **`README.md`**: tugas 2 Minggu 1 → ✅, tugas 3 → ⏳ Next. Struktur folder ditambah `notes/` dan `system_prompt_demo.py`. Bagian *Results* diisi ringkasan temuan Minggu 1 (bahasa Inggris).

### Diverifikasi
- `token_explorer.py`: context window **1,048,576** token, max output **65,536**. Kalimat Indonesia formal **10 token** vs Inggris **13 token**, slang 11 token (35 karakter), `Rp1.500.000` **11 token** (1 karakter/token), `Pertanggungjawaban` 5 token, `BBCA BBRI TLKM` 7 token.
- `system_prompt_demo.py`: tanpa system prompt → 11 input / **863 output / 1,179 thinking** token, 12.2 s (angka dari run terpisah). CS bank → 47 / 36 token, 2.2 s, menolak sopan dan mengarahkan ke penasihat OJK. English → 22 / 14 token, 2.1 s.
- `pytest -m "not live"` → 18 passed, 1 xfailed (tidak berubah setelah edit `llm_client.py`).

### Catatan / pelajaran
- **Error 503 UNAVAILABLE** ("model is currently experiencing high demand") di run pertama `system_prompt_demo.py`. Retry 3x (5/10/20 s) tetap gagal, run berikutnya berhasil. Pelajaran: kegagalan infrastruktur ≠ kegagalan kualitas.
- **Temuan tak terduga:** asumsi "Bahasa Indonesia lebih boros token" tidak terbukti untuk kalimat formal. Yang boros justru slang dan angka.
- Tracker roadmap: "Pelajari token, temperature, system prompt, context window, non-determinism" → **Selesai**.

---

## 2026-09-25 — Minggu 1 · Git & GitHub

### Ditambahkan
- Remote GitHub: `origin` → https://github.com/Jordy1406/ai-quality-engineering-journey
- **`.gitignore`**: menambahkan `*.egg-info/`. Folder `src/llm_qa.egg-info/` adalah metadata hasil `pip install -e .`, dibuat ulang otomatis, jadi tidak perlu masuk repo.

### Diperbaiki
- **Identitas commit**: config git global di laptop ini milik akun lain (`Ody1406`), jadi commit pertama tercatat atas nama Ody1406.
  - **Solusi:** set identitas **lokal khusus repo ini** (`git config user.name "Jordy1406"` + `user.email`). Config global tidak diubah.
  - Commit pertama (belum di-push) di-amend dengan `git commit --amend --reset-author`. Isinya sama, hanya author-nya yang berubah jadi Jordy1406.
  - **Kenapa penting:** kontribusi (kotak hijau) hanya muncul di profil GitHub yang email-nya cocok dengan email commit.
- **Nama branch**: `master` → `main` (`git branch -M main`), standar GitHub sekarang.

### Diverifikasi
- `git push -u origin main` **berhasil**. 3 commit (semua author Jordy1406) ada di GitHub:
  1. `chore: project setup (venv, pytest, Gemini client)`
  2. `chore: ignore egg-info build metadata`
  3. `docs: add README and CHANGELOG`
- `.env` tidak ada di repo (dicek dengan `git ls-files`).
- Tracker roadmap: "Setup repo GitHub, Python venv, pytest, API key Gemini" → **Selesai** (link repo sebagai bukti). Weekly log Minggu 1: 3 commit.

### Catatan
- Sengaja **belum di-commit**: `src/llm_qa/validators.py`, `src/llm_qa/tasks.py`, `tests/`, `experiments/`, `.github/workflows/`. File-file ini di-commit di tahapnya masing-masing, supaya history commit mengikuti urutan roadmap. Workflow CI ikut ditahan karena akan gagal kalau folder `tests/` belum ada di repo.

---

## 2026-09-25 — Minggu 1 · Sinkronisasi tracker roadmap

### Diubah
- **Tracker roadmap** ([link](https://claude.ai/artifact/EAzEaN45BAdkr7hgssvMwk)), tab *Checklist* Minggu 1:
  - "Setup repo GitHub, Python venv, pytest, API key Gemini" → **Proses**, dengan catatan hasil verifikasi. Sisa: git init + push ke GitHub.
  - "Simpan API key di GitHub Secrets / .env + batas biaya" → **Proses**. `.env` sudah beres. Sisa: GitHub Secrets + cek free tier/budget alert.

### Catatan
- Aturan baru: setiap tahap yang **benar-benar selesai** langsung ditandai *Selesai* di tracker (plus link bukti) **sebelum** lanjut ke tahap berikutnya. Tahap yang baru sebagian ditandai *Proses*.

---

## 2026-09-25 — Minggu 1 · Dokumentasi repo

### Ditambahkan
- **`README.md`**: halaman depan repo (bahasa Inggris, untuk portfolio). Isinya:
  - Tujuan repo: perjalanan 24 minggu dari QA Automation ke AI Quality Engineer, fokus domain finance & Bahasa Indonesia.
  - Tabel roadmap 6 bulan + checklist 6 tugas Minggu 1 beserta statusnya.
  - Tech stack, struktur folder dengan penjelasan tiap file, langkah setup (Windows & macOS/Linux), cara menjalankan test offline/live, dan penjelasan CI.
  - Bagian *Results* masih kosong. Akan diisi hanya dengan angka dari hasil run nyata.
- **`CHANGELOG.md`**: file ini. Aturannya: setiap perubahan di repo dicatat di sini secara rinci.

---

## 2026-09-25 — Minggu 1 · Perbaikan client Gemini

### Diperbaiki
- **`src/llm_qa/llm_client.py`**: SDK `google-genai` menampilkan warning *"Direct use of automatic function calling (AFC) in Models.generate_content is not recommended"* setiap kali `generate()` dipanggil.
  - **Penyebab:** AFC (fitur supaya model bisa memanggil fungsi Python otomatis) aktif secara default, padahal project ini tidak memakai *tools/function calling*.
  - **Solusi:** menambahkan `automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)` di `GenerateContentConfig`.
  - **Hasil:** output `check_setup.py` bersih, tanpa warning.

---

## 2026-09-25 — Minggu 1 · Tahap 1: Setup (repo, venv, pytest, API key)

### Ditambahkan — konfigurasi project
- **`requirements.txt`**: dependency project:
  - `google-genai>=1.0.0`: SDK resmi Google untuk Gemini.
  - `pydantic>=2.6`: validasi struktur data (dipakai untuk cek JSON output LLM).
  - `python-dotenv>=1.0`: membaca file `.env` ke environment variable.
  - `pytest>=8.0`: framework testing.
- **`pyproject.toml`**: menjadikan `src/llm_qa` package Python bernama `llm-qa`. Di-install dengan `pip install -e .` (mode *editable*) supaya script di folder mana pun bisa `import llm_qa`, dan perubahan kode langsung terpakai tanpa install ulang.
- **`pytest.ini`**:
  - `pythonpath = src`, `testpaths = tests`, `addopts = -ra` (ringkasan test yang skip/xfail ditampilkan di akhir).
  - Marker `live` untuk test yang memanggil API asli. Bisa dipilih dengan `pytest -m live` / `pytest -m "not live"`.
- **`.gitignore`**: mengabaikan `.env` (API key), `.venv/`, `__pycache__/`, `.pytest_cache/`, folder editor, dan file OS.
- **`.env.example`**: template konfigurasi **tanpa rahasia** (`GEMINI_API_KEY`, `GEMINI_MODEL`). File ini yang di-commit, sedangkan `.env` asli tidak.

### Ditambahkan — package `src/llm_qa/`
- **`__init__.py`**: penanda package.
- **`config.py`**:
  - `load_dotenv()`: memuat `.env` saat modul di-import.
  - `DEFAULT_MODEL`: diambil dari `GEMINI_MODEL`, default `gemini-2.5-flash`.
  - `get_api_key()`: mengembalikan key, atau `None` kalau kosong atau masih placeholder `your-key-here`.
  - `mask(secret)`: menyamarkan key saat dicetak (hanya 4 karakter terakhir yang terlihat).
- **`llm_client.py`**:
  - `MissingAPIKeyError`: error yang jelas kalau key belum di-set.
  - `LLMResponse` (dataclass): `text`, `model`, `temperature`, `latency_s`, `input_tokens`, `output_tokens`, `thinking_tokens`, dan properti `total_tokens`.
  - `GeminiClient.generate(prompt, temperature, system_prompt, json_mode)`: memanggil Gemini, mengukur latency, mengambil `usage_metadata` (token input/output/thinking). Retry otomatis untuk HTTP 429/500/503 dengan jeda 5s → 10s → 20s (maks. 3 kali).
  - `GeminiClient.count_tokens(text)`: menghitung token tanpa generate (gratis).

### Ditambahkan — script
- **`scripts/check_setup.py`**: smoke test setup. Menampilkan versi Python, model, key (tersamar), lalu meminta Gemini membalas "OK" dan menampilkan latency + token.

### Ditambahkan — CI
- **`.github/workflows/tests.yml`**:
  - Job `offline`: jalan di setiap push/PR, menjalankan `pytest -m "not live"`.
  - Job `live`: hanya saat dijalankan manual (*workflow_dispatch*), memakai secret `GEMINI_API_KEY`. Dibuat manual supaya kuota API tidak habis di setiap push.

### Ditambahkan — disiapkan untuk tahap berikutnya (belum dibahas)
File-file ini sudah dibuat, tapi baru akan dibahas dan dijalankan di tahapnya masing-masing:
- `src/llm_qa/validators.py`, `src/llm_qa/tasks.py`, `tests/conftest.py`, `tests/test_validators.py`, `tests/test_llm_output.py` → **Tahap 4** (test pytest untuk output LLM).
- `experiments/temperature_experiment.py` → **Tahap 3** (eksperimen temperature).
- `experiments/token_explorer.py` → **Tahap 2** (belajar konsep token).

### Diverifikasi
- Virtual environment `.venv` dibuat dengan Python 3.10.0, semua dependency terinstall.
- `pytest -m "not live"` → **18 passed, 1 xfailed** (xfail disengaja, mendokumentasikan batas cek berbasis regex).
- `python scripts/check_setup.py` → **Setup OK**. Model `gemini-2.5-flash`, jawaban `'OK'`, latency ±1,4–1,7 s, token input=9, output=1, thinking=18–19.

### Catatan / pelajaran
- Kendala: `check_setup.py` sempat gagal "API key NOT FOUND" karena nilai di `.env` masih placeholder `your-key-here` (file belum tersimpan). Setelah key asli di-save, langsung jalan.
- Temuan: `gemini-2.5-flash` memakai **thinking tokens**. Untuk menjawab "OK" (1 token output), model "berpikir" 18–19 token yang tidak terlihat tapi tetap dihitung biaya.

### Belum selesai di Tahap 1
- [ ] `git init` + commit pertama + push ke GitHub.
- [ ] Menambahkan `GEMINI_API_KEY` ke GitHub Secrets.
- [ ] Mengecek status free tier / memasang budget alert di Google Cloud.
