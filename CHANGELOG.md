# Changelog

Catatan rinci setiap perubahan di repo ini, urut dari yang terbaru.
Format per entri: **tanggal — minggu/tahap roadmap**, lalu *Ditambahkan / Diubah / Diperbaiki / Diverifikasi / Catatan*.

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
