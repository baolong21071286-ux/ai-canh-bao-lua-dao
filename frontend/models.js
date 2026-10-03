/**
 * Các lớp mô hình học máy chạy ngay trong trình duyệt (bản demo GitHub Pages).
 *
 *  - TF-IDF + Logistic Regression: tính lại đúng công thức của scikit-learn từ
 *    `tfidf-model.json` (do app/model_export.py xuất ra), nên khớp với bản Python.
 *  - PhoBERT: mô hình ONNX (lượng tử hóa int8) chạy bằng onnxruntime-web; bộ tách từ
 *    BPE của PhoBERT được viết lại ở đây, đối chiếu với `PhobertTokenizer` của Python.
 *
 * Dùng được ở cả trình duyệt (window.ScamModels) lẫn Node (module.exports) để kiểm thử.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.ScamModels = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const LEVELS = { 0: 'SAFE', 1: 'SUSPICIOUS', 2: 'DANGEROUS' };

  function softmax(logits) {
    const max = Math.max.apply(null, logits);
    const exps = logits.map((v) => Math.exp(v - max));
    const sum = exps.reduce((a, b) => a + b, 0);
    return exps.map((v) => v / sum);
  }

  function toLevels(classes, probs) {
    const out = {};
    classes.forEach((cls, i) => { out[LEVELS[cls]] = probs[i]; });
    return out;
  }

  // ------------------------------------------------------------ TF-IDF + LR
  const TOKEN_RE = /[\p{L}\p{N}_]+/gu; // tương đương (?u)\b\w\w+\b khi lọc độ dài >= 2

  /** sklearn `_word_ngrams` với token_pattern mặc định. */
  function wordNgrams(text, minN, maxN) {
    const tokens = (text.toLowerCase().match(TOKEN_RE) || []).filter((t) => Array.from(t).length >= 2);
    const out = minN === 1 ? tokens.slice() : [];
    for (let n = Math.max(minN, 2); n <= Math.min(maxN, tokens.length); n++) {
      for (let i = 0; i + n <= tokens.length; i++) out.push(tokens.slice(i, i + n).join(' '));
    }
    return out;
  }

  /** sklearn `_char_wb_ngrams`. */
  function charWbNgrams(text, minN, maxN) {
    const out = [];
    const words = text.toLowerCase().replace(/\s\s+/g, ' ').split(/\s+/).filter(Boolean);
    for (const word of words) {
      const w = Array.from(' ' + word + ' ');
      for (let n = minN; n <= maxN; n++) {
        let offset = 0;
        out.push(w.slice(offset, offset + n).join(''));
        while (offset + n < w.length) {
          offset += 1;
          out.push(w.slice(offset, offset + n).join(''));
        }
        if (offset === 0) break; // từ ngắn hơn n chỉ đếm một lần
      }
    }
    return out;
  }

  function createTfidf(model) {
    const vectorizers = model.vectorizers.map((v) => {
      const index = new Map();
      v.terms.forEach((term, i) => index.set(term, i));
      return Object.assign({}, v, { index });
    });

    /** Vector đặc trưng thưa: Map<cột, giá trị> (đã chuẩn hóa L2 theo từng bộ vector hóa). */
    function features(text) {
      const out = new Map();
      for (const v of vectorizers) {
        const grams = v.analyzer === 'word'
          ? wordNgrams(text, v.ngramRange[0], v.ngramRange[1])
          : charWbNgrams(text, v.ngramRange[0], v.ngramRange[1]);
        const counts = new Map();
        for (const g of grams) {
          const i = v.index.get(g);
          if (i !== undefined) counts.set(i, (counts.get(i) || 0) + 1);
        }
        let norm = 0;
        const values = [];
        counts.forEach((tf, i) => {
          const value = (v.sublinearTf ? 1 + Math.log(tf) : tf) * v.idf[i];
          values.push([i, value]);
          norm += value * value;
        });
        norm = Math.sqrt(norm) || 1;
        for (const [i, value] of values) out.set(v.offset + i, value / norm);
      }
      return out;
    }

    function predict(normalizedText) {
      const x = features(normalizedText);
      const logits = model.coef.map((row, k) => {
        let z = model.intercept[k];
        x.forEach((value, col) => { z += row[col] * value; });
        return z;
      });
      let probs;
      if (logits.length === 1) {
        const p = 1 / (1 + Math.exp(-logits[0]));
        probs = [1 - p, p];
      } else {
        probs = softmax(logits);
      }
      return toLevels(model.classes, probs);
    }

    return { predict, features };
  }

  // ------------------------------------------------------- PhoBERT tokenizer
  /** Bản JS của `PhobertTokenizer` (fastBPE, hậu tố "@@" cho mảnh chưa hết từ). */
  function createPhobertTokenizer(spec) {
    const vocab = new Map(Object.entries(spec.vocab));
    const ranks = new Map();
    spec.merges.forEach((pair, i) => ranks.set(pair, i));
    const cache = new Map();
    const unk = spec.unkId, bos = spec.bosId, eos = spec.eosId;

    function bpe(token) {
      if (cache.has(token)) return cache.get(token);
      let word = Array.from(token);
      word[word.length - 1] += '</w>';
      if (word.length === 1) { cache.set(token, [token]); return [token]; }
      while (word.length > 1) {
        let best = null, bestRank = Infinity;
        for (let i = 0; i < word.length - 1; i++) {
          const r = ranks.get(word[i] + ' ' + word[i + 1]);
          if (r !== undefined && r < bestRank) { bestRank = r; best = [word[i], word[i + 1]]; }
        }
        if (!best) break;
        const merged = [];
        for (let i = 0; i < word.length;) {
          if (i < word.length - 1 && word[i] === best[0] && word[i + 1] === best[1]) {
            merged.push(best[0] + best[1]); i += 2;
          } else {
            merged.push(word[i]); i += 1;
          }
        }
        word = merged;
      }
      // "@@ ".join(word)[:-4]: mảnh giữa từ có "@@", mảnh cuối bỏ "</w>"
      const pieces = word.map((p, i) => (i < word.length - 1 ? p + '@@' : p.slice(0, -4)));
      cache.set(token, pieces);
      return pieces;
    }

    function tokenize(text) {
      const words = String(text).match(/\S+\n?/gu) || [];
      const out = [];
      for (const w of words) out.push.apply(out, bpe(w));
      return out;
    }

    function encode(text, maxLength) {
      const ids = tokenize(text).map((t) => (vocab.has(t) ? vocab.get(t) : unk));
      return [bos].concat(ids.slice(0, (maxLength || spec.maxLength) - 2), [eos]);
    }

    return { tokenize, encode };
  }

  // ---------------------------------------------------------- PhoBERT (ONNX)
  /**
   * @param ort       đối tượng onnxruntime-web (window.ort)
   * @param modelData ArrayBuffer/Uint8Array của model.onnx
   * @param spec      nội dung phobert/tokenizer.json
   */
  async function createPhobert(ort, modelData, spec) {
    const tokenizer = createPhobertTokenizer(spec);
    const session = await ort.InferenceSession.create(modelData, { executionProviders: ['wasm'] });

    async function predict(text) {
      const ids = tokenizer.encode(text);
      const toTensor = (arr) => new ort.Tensor('int64', BigInt64Array.from(arr.map((v) => BigInt(v))), [1, arr.length]);
      const feeds = { input_ids: toTensor(ids), attention_mask: toTensor(ids.map(() => 1)) };
      const output = await session.run(feeds);
      const logits = Array.from(output.logits.data, Number);
      return toLevels(spec.labels, softmax(logits));
    }

    return { predict, tokenizer };
  }

  /**
   * Tải tệp theo từng mảnh (mỗi tệp trên GitHub Pages đều nhỏ), có báo tiến độ.
   * Nếu trình duyệt hỗ trợ Cache Storage thì lưu lại để lần sau mở trang không phải tải lại.
   */
  async function fetchChunks(baseUrl, parts, onProgress, cacheName) {
    let cache = null;
    try { if (cacheName && typeof caches !== 'undefined') cache = await caches.open(cacheName); } catch (_) { cache = null; }
    const buffers = [];
    let loaded = 0;
    const total = parts.reduce((a, p) => a + p.size, 0);
    for (const part of parts) {
      const url = baseUrl + part.file;
      let res = null;
      try { res = cache ? await cache.match(url) : null; } catch (_) { res = null; }
      if (!res) {
        res = await fetch(url);
        if (!res.ok) throw new Error('không tải được ' + part.file);
        if (cache) { try { await cache.put(url, res.clone()); } catch (_) { /* hết dung lượng: bỏ qua */ } }
      }
      const buf = new Uint8Array(await res.arrayBuffer());
      buffers.push(buf);
      loaded += buf.length;
      if (onProgress) onProgress(loaded, total);
    }
    const out = new Uint8Array(loaded);
    let pos = 0;
    for (const b of buffers) { out.set(b, pos); pos += b.length; }
    return out;
  }

  return { createTfidf, createPhobertTokenizer, createPhobert, fetchChunks, wordNgrams, charWbNgrams };
});