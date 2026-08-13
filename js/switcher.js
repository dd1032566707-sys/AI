/*
 * Model Switcher —— 多模型自由切换器（Cubism 2 / live2d.js）
 * 用法: <script src="js/live2d.js"></script><script src="js/switcher.js"></script>
 *       然后在页面里调用 window.initModelSwitcher('live2d');
 *
 * 模型清单解析顺序（三层兜底，保证「服务器」与「双击 html」都能用）:
 *   1) 服务端 /models        （serve.py 自动扫描 model/ 目录，丢新模型即生效）
 *   2) model_manifest.json   （随仓库提供的清单）
 *   3) 内置 BUILTIN 清单      （离线 / file:// 时也能切换）
 *
 * 每个模型条目: { name, folder, defs:[描述文件名...] }
 *   加载路径 = "model/" + folder + "/" + defs[skinIndex]
 */
(function () {
  'use strict';

  // 内置清单（与 model_manifest.json 保持一致；离线兜底用）
  var BUILTIN = [
    { name: '结月ゆかり',        folder: 'yukari_model', defs: ['yukari_model.model.json'] },
    { name: '琪亚娜·卡斯兰娜',   folder: 'kiana',        defs: ['model.json'] },
    { name: '雷电芽衣',          folder: 'mei',          defs: ['model.json'] },
    { name: '布洛妮娅',          folder: 'bronya',       defs: ['model.json'] },
    { name: '雷姆',              folder: 'rem',          defs: ['model.json'] },
    { name: '樱',                folder: 'sakura',       defs: ['model.json'] },
    { name: '春',                folder: 'haru',         defs: ['haru_01.model.json', 'haru_02.model.json'] },
    { name: '初音未来',          folder: 'miku',         defs: ['miku.model.json'] },
    { name: 'Unity娘',           folder: 'unitychan',    defs: ['unitychan.model.json'] },
    { name: '姬子',              folder: 'himeko',       defs: ['model.json'] },
    { name: '希儿',              folder: 'seele',        defs: ['model.json'] },
    { name: '德丽莎',            folder: 'theresa',      defs: ['model.json'] },
    { name: '辛',                folder: 'sin',          defs: ['model.json'] },
    { name: '狐娘',              folder: 'fox',          defs: ['model.json'] }
  ];

  var MODELS = BUILTIN;
  var curMi = 0, curSi = 0;
  var els = {};

  function pathFor(mi, si) {
    var m = MODELS[mi];
    var def = m.defs[si] || m.defs[0];
    return 'model/' + m.folder + '/' + def;
  }

  function loadModelList(cb) {
    var use = function (list) { cb((list && list.length) ? list : BUILTIN); };
    fetch('/models')
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (d) { use(d); })
      .catch(function () {
        fetch('model_manifest.json')
          .then(function (r) { if (!r.ok) throw 0; return r.json(); })
          .then(function (d) { use(d); })
          .catch(function () { use(BUILTIN); });
      });
  }

  function saveSel() {
    try { localStorage.setItem('lm_sel', JSON.stringify({ mi: curMi, si: curSi })); } catch (e) {}
  }

  function renderModel(mi, si, silent) {
    mi = Math.max(0, Math.min(mi, MODELS.length - 1));
    var m = MODELS[mi];
    si = Math.max(0, Math.min(si, m.defs.length - 1));
    curMi = mi; curSi = si;

    els.modelSelect.value = String(mi);
    // 皮肤（同一模型多个描述文件）下拉
    if (m.defs.length > 1) {
      els.skinRow.style.display = '';
      els.skinSelect.innerHTML = '';
      for (var i = 0; i < m.defs.length; i++) {
        var o = document.createElement('option');
        o.value = String(i);
        o.textContent = '皮肤 ' + (i + 1);
        els.skinSelect.appendChild(o);
      }
      els.skinSelect.value = String(si);
    } else {
      els.skinRow.style.display = 'none';
    }
    els.cur.textContent = m.name + (m.defs.length > 1 ? ' · 皮肤' + (si + 1) : '');

    if (typeof loadlive2d === 'function') {
      loadlive2d('live2d', pathFor(mi, si));
    }
    saveSel();
  }

  function buildUI() {
    var panel = document.createElement('div');
    panel.id = 'lm-panel';
    panel.innerHTML =
      '<div class="lm-title">模型切换</div>' +
      '<div class="lm-row">' +
      '  <button id="lm-prev" title="上一个">‹</button>' +
      '  <select id="lm-model"></select>' +
      '  <button id="lm-next" title="下一个">›</button>' +
      '</div>' +
      '<div class="lm-row" id="lm-skin-row" style="display:none">' +
      '  <select id="lm-skin" style="width:100%"></select>' +
      '</div>' +
      '<div class="lm-cur" id="lm-cur"></div>';

    (document.head || document.documentElement).appendChild(
      (function () {
        var s = document.createElement('style');
        s.textContent =
          '#lm-panel{position:fixed;top:14px;left:14px;z-index:60;' +
          'background:rgba(18,20,32,.74);backdrop-filter:blur(8px);' +
          '-webkit-backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,.10);' +
          'border-radius:12px;padding:10px 12px;color:#e8e8f0;' +
          'font:13px -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;' +
          'box-shadow:0 8px 24px rgba(0,0,0,.35);user-select:none;}' +
          '#lm-panel .lm-title{font-size:12px;opacity:.6;letter-spacing:1px;margin-bottom:8px;}' +
          '#lm-panel .lm-row{display:flex;align-items:center;gap:6px;margin-bottom:6px;}' +
          '#lm-panel select{flex:1;min-width:120px;background:#2a2d44;color:#e8e8f0;' +
          'border:1px solid rgba(255,255,255,.14);border-radius:8px;padding:5px 8px;' +
          'outline:none;cursor:pointer;}' +
          '#lm-panel button{width:30px;height:30px;border:none;border-radius:8px;' +
          'background:#3a3f63;color:#e8e8f0;font-size:16px;line-height:1;cursor:pointer;' +
          'transition:background .15s;}' +
          '#lm-panel button:hover{background:#4a507e;}' +
          '#lm-panel .lm-cur{font-size:12px;opacity:.8;margin-top:2px;}';
        return s;
      })()
    );
    document.body.appendChild(panel);

    els.modelSelect = document.getElementById('lm-model');
    els.skinSelect = document.getElementById('lm-skin');
    els.skinRow = document.getElementById('lm-skin-row');
    els.cur = document.getElementById('lm-cur');
    els.prev = document.getElementById('lm-prev');
    els.next = document.getElementById('lm-next');

    els.modelSelect.innerHTML = '';
    for (var i = 0; i < MODELS.length; i++) {
      var o = document.createElement('option');
      o.value = String(i);
      o.textContent = MODELS[i].name;
      els.modelSelect.appendChild(o);
    }
  }

  function wireEvents() {
    els.modelSelect.addEventListener('change', function () {
      renderModel(parseInt(this.value, 10), 0);
    });
    els.skinSelect.addEventListener('change', function () {
      renderModel(curMi, parseInt(this.value, 10));
    });
    els.prev.addEventListener('click', function () {
      renderModel((curMi - 1 + MODELS.length) % MODELS.length, 0);
    });
    els.next.addEventListener('click', function () {
      renderModel((curMi + 1) % MODELS.length, 0);
    });
  }

  window.initModelSwitcher = function (canvasId) {
    if (typeof loadlive2d !== 'function') {
      console.warn('[switcher] loadlive2d 未定义，无法加载模型');
      return;
    }
    loadModelList(function (list) {
      MODELS = list;
      buildUI();
      var sel = {};
      try { sel = JSON.parse(localStorage.getItem('lm_sel') || '{}'); } catch (e) {}
      var mi = Math.max(0, Math.min(sel.mi || 0, MODELS.length - 1));
      renderModel(mi, sel.si || 0);
      wireEvents();
    });
  };
})();
