/**
 * Bộ máy phân tích chạy ngay trong trình duyệt — bản JavaScript của Module 1–3.
 *
 * Vì sao cần? Bản demo trên GitHub Pages là trang tĩnh, không có máy chủ Python.
 * Toàn bộ luật, ngưỡng, nội dung giáo dục được nạp từ `engine-data.json`
 * (do scripts/build_static_site.py xuất ra từ chính mã nguồn Python), nên hai
 * phiên bản luôn dùng chung một nguồn dữ liệu duy nhất.
 *
 * Dùng được ở cả trình duyệt (window.ScamEngine) lẫn Node (module.exports) để kiểm thử đối chiếu.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.ScamEngine = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const COMBINING = /[̀-ͯ]/g;
  const LEET = { '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '@': 'a', '$': 's' };

  /** Bỏ dấu 1 ký tự tiếng Việt, giữ độ dài 0 hoặc 1 (giống app/text_utils.py). */
  function foldChar(ch) {
    if (ch === 'đ' || ch === 'Đ') return 'd';
    return ch.normalize('NFD').replace(COMBINING, '').toLowerCase();
  }

  /** Trả về [chuỗi đã bỏ dấu, bảng ánh xạ vị trí về văn bản gốc]. */
  function foldWithMap(text) {
    const out = [];
    const map = [];
    let pendingSpace = false;
    for (let i = 0; i < text.length; i++) {
      const ch = text[i];
      if (/\s/.test(ch)) { pendingSpace = out.length > 0; continue; }
      const folded = foldChar(ch);
      if (!folded) continue;
      if (pendingSpace) { out.push(' '); map.push(i); pendingSpace = false; }
      for (const sub of folded) { out.push(sub); map.push(i); }
    }
    return [out.join(''), map];
  }

  function shouldDeleet(token) {
    if (/[:/@]/.test(token)) return false;
    const letters = (token.match(/[a-z]/g) || []).length;
    const digits = (token.match(/\d/g) || []).length;
    if (!letters || !digits || letters < digits) return false;
    return (token.match(/\d+/g) || []).every((run) => run.length === 1);
  }

  /** Khử "teen-code" (0tp → otp) nhưng giữ nguyên độ dài chuỗi. */
  function deleet(folded) {
    return folded.split(/(\s+)/).map((token) => {
      if (token.trim() && shouldDeleet(token)) {
        return token.split('').map((c) => LEET[c] || c).join('');
      }
      return token;
    }).join('');
  }

  /** Lấy lại đoạn văn bản gốc ứng với khoảng [start, end) trên bản đã bỏ dấu. */
  function mapSpan(folded, map, start, end, original) {
    end = Math.min(end, map.length, folded.length);
    while (start < end && /\s/.test(folded[start])) start++;
    while (end > start && /\s/.test(folded[end - 1])) end--;
    if (start >= end || start >= map.length) return '';
    return original.slice(map[start], map[end - 1] + 1).trim();
  }

  function noisyOr(weights) {
    let acc = 1;
    for (const w of weights) acc *= 1 - Math.max(0, Math.min(1, w));
    return 1 - acc;
  }

  // ---------------------------------------------------------------- tên miền
  function hostOf(url) {
    let host = url.trim().replace(/^[a-z]+:\/\//i, '');
    host = host.split('/')[0].split('?')[0].split('#')[0];
    host = host.split('@').pop().split(':')[0];
    return host.toLowerCase().replace(/^\.+|\.+$/g, '');
  }

  function registrableDomain(host, multiSuffixes) {
    const labels = host.split('.').filter(Boolean);
    if (labels.length <= 2) return labels.join('.');
    const lastTwo = labels.slice(-2).join('.');
    if (multiSuffixes.indexOf(lastTwo) !== -1 && labels.length >= 3) return labels.slice(-3).join('.');
    return lastTwo;
  }

  function isOfficial(host, data) {
    if (!host) return false;
    for (const official of data.domains.official) {
      if (host === official || host.endsWith('.' + official)) return true;
    }
    return data.domains.official.indexOf(registrableDomain(host, data.domains.multiSuffixes)) !== -1;
  }

  function brandsIn(host, data) {
    const flat = host.toLowerCase().replace(/[^a-z0-9]/g, '');
    return data.domains.brands.filter((brand) => flat.indexOf(brand) !== -1);
  }

  function looksRandom(host, data) {
    const label = registrableDomain(host, data.domains.multiSuffixes).split('.')[0];
    if (label.length < 5 || !/^[a-z]+$/.test(label)) return false;
    const vowels = (label.match(/[aeiouy]/g) || []).length;
    const runs = label.split(/[aeiouy]+/).map((r) => r.length);
    return vowels / label.length < 0.3 || Math.max(0, ...runs) >= 4;
  }

  function editDistanceAtMost(a, b, limit) {
    if (Math.abs(a.length - b.length) > limit) return false;
    let previous = Array.from({ length: b.length + 1 }, (_, i) => i);
    for (let i = 1; i <= a.length; i++) {
      const current = [i];
      for (let j = 1; j <= b.length; j++) {
        current.push(Math.min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (a[i - 1] !== b[j - 1] ? 1 : 0)));
      }
      if (Math.min.apply(null, current) > limit) return false;
      previous = current;
    }
    return previous[b.length] <= limit;
  }

  function typoOfBrand(host, data) {
    const label = registrableDomain(host, data.domains.multiSuffixes).split('.')[0].replace(/[^a-z0-9]/g, '');
    if (label.length < 5) return null;
    for (const brand of data.domains.brands) {
      if (brand.length < 5 || label.indexOf(brand) !== -1) continue;
      if (Math.abs(label.length - brand.length) <= 2 && editDistanceAtMost(label, brand, 2)) return [label, brand];
    }
    return null;
  }

  /** Tên miền có nằm trong danh sách đen cộng đồng không. */
  function isBlocklisted(host, data) {
    const list = data.domains.blocklist;
    if (!list || !list.length) return false;
    if (!data._blockset) data._blockset = new Set(list);
    host = host.toLowerCase().replace(/^\.+|\.+$/g, '');
    if (data._blockset.has(host) || data._blockset.has(registrableDomain(host, data.domains.multiSuffixes))) return true;
    const parts = host.split('.');
    for (let i = 1; i < parts.length - 1; i++) {
      if (data._blockset.has(parts.slice(i).join('.'))) return true;
    }
    return false;
  }

  function isIpHost(host) {
    const parts = host.split('.');
    return parts.length === 4 && parts.every((p) => /^\d+$/.test(p) && +p >= 0 && +p <= 255);
  }

  /** Chấm điểm rủi ro cho mọi đường link trong tin nhắn (bản JS của app/link_analyzer.py). */
  function analyzeLinks(text, data) {
    const hits = [];
    const seen = new Set();
    const urlRe = new RegExp(data.urlPattern, 'gi');
    let match;
    while ((match = urlRe.exec(text)) !== null) {
      const url = match[0].replace(/[.,;:!?)]+$/, '');
      if (seen.has(url.toLowerCase())) continue;
      seen.add(url.toLowerCase());
      const host = hostOf(url);
      if (!host || host.indexOf('.') === -1) continue;

      const push = (id, reason, weight, hard, standalone) => hits.push({
        id, phrase: url, reason, weight,
        hardDanger: !!hard, standalone: !!standalone, amplifier: false,
        signal: 'LINK', category: 'PHISHING_LINK',
      });

      if (isBlocklisted(host, data)) {
        push('LINK_BLOCKLISTED',
          'Địa chỉ `' + host + '` nằm trong danh sách đen các trang lừa đảo/độc hại do cộng đồng an ninh mạng công bố.',
          0.9, true, true);
        continue;
      }
      if (isIpHost(host)) {
        push('LINK_IP_ADDRESS', 'Đường dẫn trỏ thẳng tới địa chỉ IP — gần như chắc chắn không phải trang chính thống.', 0.55, false, true);
        continue;
      }
      if (isOfficial(host, data)) continue;

      const domain = registrableDomain(host, data.domains.multiSuffixes);
      const tld = host.split('.').pop();
      const brands = brandsIn(host, data);
      const typo = typoOfBrand(host, data);
      const risky = data.domains.riskyTlds.indexOf(tld) !== -1;

      if (brands.length) {
        const blatant = risky || host.indexOf('-') !== -1;
        push(blatant ? 'LINK_BRAND_IMPERSONATION' : 'LINK_BRAND_UNVERIFIED',
          blatant
            ? 'Địa chỉ `' + host + '` mượn tên thương hiệu "' + brands[0] + '" nhưng KHÔNG phải trang chính thức — đây là trang giả mạo để lừa đăng nhập.'
            : 'Địa chỉ `' + host + '` có tên thương hiệu "' + brands[0] + '" nhưng không nằm trong danh sách trang chính thức đã biết — cần kiểm chứng trước khi bấm.',
          blatant ? 0.7 : 0.45, blatant, true);
      } else if (typo) {
        push('LINK_BRAND_TYPO', 'Địa chỉ `' + host + '` viết sai một chữ so với thương hiệu thật "' + typo[1] + '" — chiêu đánh lừa mắt người đọc.', 0.7, true, true);
      } else if (data.domains.shorteners.indexOf(domain) !== -1) {
        push('LINK_SHORTENER', 'Link rút gọn che giấu địa chỉ thật của trang web.', 0.4, false, false);
      } else if (risky) {
        push('LINK_SUSPICIOUS_TLD', 'Tên miền lạ đuôi `.' + tld + '` — hiếm khi được tổ chức chính thống sử dụng.', 0.5, false, true);
      } else if (looksRandom(host, data)) {
        push('LINK_RANDOM_DOMAIN', 'Tên miền `' + domain + '` trông như chuỗi ký tự ngẫu nhiên — dấu hiệu trang dùng một lần.', 0.45, false, true);
      } else {
        push('LINK_UNKNOWN_DOMAIN', 'Trang `' + domain + '` không nằm trong danh sách trang chính thống quen thuộc.', 0.2, false, false);
      }

      const lowered = url.toLowerCase();
      if (/\.(apk|exe)(\?|$)/.test(lowered)) {
        push('LINK_FILE_DOWNLOAD', 'Link tải thẳng tệp cài đặt (.apk/.exe) — thường là phần mềm theo dõi hoặc chiếm tài khoản.', 0.6, false, true);
      }
    }
    return hits;
  }

  // ------------------------------------------------------------- bộ máy chính
  /**
   * @param data    nội dung engine-data.json
   * @param models  (tùy chọn) { tfidf: ScamModels.createTfidf(...) } — lớp TF-IDF chạy đồng bộ.
   *                Điểm PhoBERT (bất đồng bộ) được truyền vào qua analyze(text, { transformerScores }).
   */
  function createEngine(data, models) {
    models = models || {};
    const compiled = data.rules.map((rule) => ({
      rule,
      regexes: rule.patterns.map((p) => new RegExp(p, 'g')),
    }));

    function collectHits(matchText, map, original) {
      const hits = [];
      for (const entry of compiled) {
        const phrases = [];
        for (const regex of entry.regexes) {
          regex.lastIndex = 0;
          let m;
          while ((m = regex.exec(matchText)) !== null) {
            if (m[0] === '') { regex.lastIndex++; continue; }
            const phrase = mapSpan(matchText, map, m.index, m.index + m[0].length, original);
            if (phrase && !phrases.some((p) => p.toLowerCase() === phrase.toLowerCase())) phrases.push(phrase);
          }
        }
        if (phrases.length) {
          hits.push(Object.assign({}, entry.rule, { phrase: phrases[0], phrases: phrases }));
        }
      }
      return hits;
    }

    function pickCategory(riskHits, comboHits) {
      const hard = comboHits.filter((c) => c.hardDanger && c.definesCategory).map((c) => c.category)
        .concat(riskHits.filter((h) => h.hardDanger).map((h) => h.category));
      if (hard.length) {
        return hard.sort((a, b) => (data.categoryPriority[b] || 0) - (data.categoryPriority[a] || 0))[0];
      }
      const scores = {};
      for (const hit of riskHits) {
        if (hit.category === 'SAFE') continue;
        scores[hit.category] = (scores[hit.category] || 0) + hit.weight;
      }
      for (const combo of comboHits) {
        if (combo.definesCategory) scores[combo.category] = (scores[combo.category] || 0) + combo.boost;
      }
      const entries = Object.keys(scores);
      if (!entries.length) return 'SAFE';
      entries.sort((a, b) => (scores[b] - scores[a]) || ((data.categoryPriority[b] || 0) - (data.categoryPriority[a] || 0)));
      return entries[0];
    }

    function confidence(level, score, hasHard, evidenceCount) {
      const TD = data.thresholds.dangerous, TS = data.thresholds.suspicious;
      let base;
      if (level === 'DANGEROUS') {
        base = 0.75 + 0.2 * Math.min(1, (score - TD) / Math.max(1e-6, 1 - TD));
        if (hasHard) base = Math.max(base, 0.9);
        base += 0.01 * Math.min(4, evidenceCount);
      } else if (level === 'SUSPICIOUS') {
        const mid = (TD + TS) / 2;
        base = Math.max(0.55, 0.72 - 0.25 * Math.abs(score - mid) / Math.max(1e-6, (TD - TS) / 2));
      } else {
        base = 0.7 + 0.29 * (1 - score / Math.max(1e-6, TS));
      }
      return Math.round(Math.max(0.5, Math.min(0.99, base)) * 100) / 100;
    }

    /** Hàm băm đơn giản để chọn quiz ổn định theo nội dung tin nhắn. */
    function hashString(text) {
      let h = 2166136261;
      for (let i = 0; i < text.length; i++) { h ^= text.charCodeAt(i); h = Math.imul(h, 16777619); }
      return Math.abs(h);
    }

    function analyze(text, options) {
      const opts = options || {};
      const started = (typeof performance !== 'undefined' ? performance.now() : Date.now());
      const original = String(text || '').trim();
      const [folded, map] = foldWithMap(original);
      const matchText = deleet(folded);

      let hits = collectHits(matchText, map, original).concat(analyzeLinks(original, data));

      const matchedIds = new Set(hits.map((h) => h.id));
      const suppressed = new Set();
      Object.keys(data.suppressions).forEach((trigger) => {
        if (matchedIds.has(trigger)) data.suppressions[trigger].forEach((t) => suppressed.add(t));
      });
      if (suppressed.size) hits = hits.filter((h) => !suppressed.has(h.id));

      const safeHits = hits.filter((h) => h.signal === 'SAFE');
      let riskHits = hits.filter((h) => data.riskSignals.indexOf(h.signal) !== -1);
      if (!riskHits.some((h) => !h.amplifier)) riskHits = [];
      const activeSignals = new Set(riskHits.map((h) => h.signal));

      const comboHits = data.combos.filter((combo) =>
        combo.requires.every((group) => group.some((sig) => activeSignals.has(sig))));

      let ruleScore = noisyOr(riskHits.map((h) => h.weight).concat(comboHits.map((c) => c.boost)));
      const canConcludeAlone = riskHits.some((h) => h.standalone) ||
        data.standaloneSignals.some((s) => activeSignals.has(s));
      if (!comboHits.length && !canConcludeAlone) {
        ruleScore = Math.min(ruleScore, data.thresholds.dangerous - 0.05);
      }

      const hasHard = riskHits.some((h) => h.hardDanger) || comboHits.some((c) => c.hardDanger);
      const safeScore = noisyOr(safeHits.map((h) => h.weight));
      if (safeScore && !hasHard) {
        ruleScore *= 1 - 0.5 * Math.min(0.6, safeScore);
        if (safeScore >= 0.4) ruleScore = Math.min(ruleScore, data.thresholds.dangerous - 0.02);
        const identityOnly = data.identityOnlySignals || [];
        if (!comboHits.length && activeSignals.size &&
            Array.from(activeSignals).every((s) => identityOnly.indexOf(s) !== -1)) {
          ruleScore = Math.min(ruleScore, data.thresholds.suspicious - 0.02);
        }
      }
      // --- Trộn với các lớp mô hình (giống app/classifier.py) ---
      const mlScores = opts.mlScores ||
        (models.tfidf && matchText ? models.tfidf.predict(deleet(foldWithMap(matchText)[0])) : null);
      const trScores = opts.transformerScores || null;
      const riskOf = (s) => (s.DANGEROUS || 0) + 0.45 * (s.SUSPICIOUS || 0);
      const components = [[data.modelWeights.rule, ruleScore]];
      if (mlScores) components.push([data.modelWeights.ml, riskOf(mlScores)]);
      if (trScores) components.push([data.modelWeights.transformer, riskOf(trScores)]);
      const totalWeight = components.reduce((a, c) => a + c[0], 0);
      let score = components.reduce((a, c) => a + c[0] * c[1], 0) / totalWeight;

      // Ưu tiên Recall: mô hình rất chắc chắn thì không để tin nhắn rơi về mức An toàn.
      [mlScores, trScores].forEach((s) => {
        if (!s) return;
        if ((s.DANGEROUS || 0) >= 0.8) score = Math.max(score, data.thresholds.suspicious + 0.05);
        else if ((s.SUSPICIOUS || 0) >= 0.6) score = Math.max(score, data.thresholds.suspicious);
      });
      // Mô hình rất chắc chắn là an toàn thì được kéo điểm xuống (khi luật không có bằng chứng chắc chắn).
      if (data.modelSafeVeto && !hasHard) {
        const modelSafe = [mlScores, trScores].filter(Boolean).map((s) => s.SAFE || 0);
        if (modelSafe.length && Math.min.apply(null, modelSafe) >= data.modelSafeVeto) {
          score *= data.modelSafeVetoFactor;
        }
      }
      if (hasHard) score = Math.max(score, 0.85);
      score = Math.round(Math.max(0, Math.min(1, score)) * 10000) / 10000;

      const level = score >= data.thresholds.dangerous ? 'DANGEROUS'
        : score >= data.thresholds.suspicious ? 'SUSPICIOUS' : 'SAFE';
      const category = level === 'SAFE' ? 'SAFE' : pickCategory(riskHits, comboHits);

      let evidence = [];
      if (level !== 'SAFE') {
        const ordered = riskHits.slice().sort((a, b) =>
          ((b.category === category) - (a.category === category)) ||
          ((b.hardDanger ? 1 : 0) - (a.hardDanger ? 1 : 0)) || (b.weight - a.weight));
        const seen = new Set();
        for (const hit of ordered) {
          const key = (hit.phrase || '').toLowerCase();
          if (!key || seen.has(key)) continue;
          seen.add(key);
          evidence.push({ phrase: hit.phrase, reason: hit.reason, rule_id: hit.id });
          if (evidence.length >= 5) break;
        }
        comboHits.forEach((combo) => {
          if (evidence.length < 6) evidence.push({ phrase: '', reason: combo.reason, rule_id: combo.id });
        });
      }

      let explanation = data.explanations[category] || data.explanations.SAFE;
      if (level !== 'SAFE' && category === 'SAFE' && (mlScores || trScores)) {
        explanation = 'Mô hình AI thấy cách viết của tin nhắn này khá giống các tin nhắn lừa đảo đã gặp, ' +
          'dù chưa tìm được từ khóa cụ thể. Em hãy cẩn thận và hỏi người lớn trước khi làm theo.';
      } else if (level !== 'SAFE' && category === 'SAFE') {
        explanation = 'Tin nhắn có vài điểm đáng ngờ dù chưa tìm được từ khóa cụ thể. Em hãy cẩn thận và hỏi người lớn trước khi làm theo.';
      } else if (level === 'SUSPICIOUS' && category !== 'SAFE') {
        explanation = 'Chưa đủ căn cứ khẳng định là lừa đảo, nhưng tin nhắn có điểm đáng ngờ. ' + explanation;
      }

      // ----- Module 3: hành động + flashcard + mini-quiz -----
      const blockKey = (level !== 'SAFE' && category === 'SAFE') ? 'GENERIC_CAUTION'
        : (data.education[category] ? category : 'SAFE');
      const block = data.education[blockKey];
      const steps = block.steps.slice();
      if (level === 'DANGEROUS') steps.push((steps.length + 1) + '. Ghi nhớ: ' + data.goldenRules.join(' '));
      const quiz = block.quizzes[hashString(folded || category) % block.quizzes.length];
      let warning = block.primary_warning;
      if (level === 'SUSPICIOUS' && blockKey !== 'GENERIC_CAUTION') warning = 'HÃY CẨN THẬN: ' + warning;

      const theme = data.theme[level];
      const badge = (level === 'SAFE' || category === 'SAFE')
        ? theme.badge_title
        : (level === 'DANGEROUS' ? 'Cực kỳ nguy hiểm' : 'Nghi vấn') + ' - ' + (data.categoryTitles[category] || category);
      let summary = data.summaries[category] || data.summaries.SAFE;
      if (level === 'SUSPICIOUS') summary = 'Cần thận trọng: ' + summary.charAt(0).toLowerCase() + summary.slice(1);

      const elapsed = (typeof performance !== 'undefined' ? performance.now() : Date.now()) - started;
      return {
        verdict: {
          level: level,
          badge_title: badge,
          theme_color: theme.hex,
          emoji: theme.emoji,
          headline: theme.headline,
          confidence_score: confidence(level, score, hasHard, evidence.length),
        },
        summary: summary,
        explanation: explanation,
        highlight_words: evidence.filter((e) => e.phrase).map((e) => e.phrase),
        trigger_evidence: evidence,
        immediate_actions: steps,
        primary_warning: warning,
        flashcard: block.flashcard,
        interactive_quiz: {
          quiz_id: quiz.quiz_id, question: quiz.question, options: quiz.options,
          correct: quiz.correct_option, explanation: quiz.explanation,
        },
        meta: {
          channel: null, scam_category: category, risk_score: score,
          engine: ['rules'].concat(mlScores ? ['tfidf'] : [], trScores ? ['phobert'] : []).join('+'),
          ml_scores: mlScores, transformer_scores: trScores, process_time_ms: Math.round(elapsed * 100) / 100,
          matched_rules: riskHits.map((h) => h.id).concat(comboHits.map((c) => c.id)),
        },
      };
    }

    return { analyze: analyze, data: data };
  }

  return { create: createEngine, foldWithMap: foldWithMap, deleet: deleet };
});