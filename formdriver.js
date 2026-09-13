/* formdriver.js — inject into an application page via javascript_tool.
 *
 * Why: clicking ATS forms field-by-field is slow and error-prone (coordinates
 * go stale when the page re-lays-out). This reads and writes the whole form
 * programmatically in one round trip.
 *
 * Usage:
 *   1) paste this whole file as the javascript_tool `text`  -> returns field dump
 *   2) __fd.set('name','value')            set one field (React-safe)
 *   3) __fd.fill({name1:v1, name2:v2})     set many at once
 *   4) __fd.dump()                         re-read state
 *   5) __fd.audit()                        list required fields still EMPTY
 *   6) __fd.proxyFile() / __fd.xfer(name)  upload into a same-origin iframe
 */
(() => {
  // iCIMS and others nest the real form in a same-origin iframe.
  const f = document.querySelector('iframe#icims_content_iframe, iframe[src*="icims"], iframe');
  let D = document;
  try { if (f && f.contentDocument && f.contentDocument.querySelectorAll('input,select').length > 2) D = f.contentDocument; } catch (e) {}

  const label = el => {
    let t = '';
    if (el.id) { const l = D.querySelector(`label[for="${CSS.escape(el.id)}"]`); if (l) t = l.innerText; }
    if (!t) { const l = el.closest('label'); if (l) t = l.innerText; }
    if (!t) { let n = el.parentElement; for (let k = 0; k < 5 && n && !t; k++) { const c = n.querySelector('label'); if (c) t = c.innerText; n = n.parentElement; } }
    return (t || el.getAttribute('aria-label') || el.name || el.id || '').replace(/\s+/g, ' ').trim().slice(0, 75);
  };

  const nativeSet = (el, v) => {
    const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype
                : el.tagName === 'SELECT'   ? HTMLSelectElement.prototype
                :                             HTMLInputElement.prototype;
    // React overrides .value; go through the native setter or the change is ignored.
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, v);
    ['input', 'change', 'blur'].forEach(e => el.dispatchEvent(new Event(e, { bubbles: true })));
    return el.value;
  };

  window.__D = D;
  window.__fd = {
    D,
    find: n => D.querySelector(`[name="${CSS.escape(n)}"]`) || D.getElementById(n),

    dump() {
      const out = [];
      D.querySelectorAll('input,select,textarea').forEach(el => {
        if (el.type === 'hidden') return;
        const r = el.getBoundingClientRect();
        const lb = label(el);
        const o = { n: el.name || el.id, l: lb, t: el.tagName[0] + (el.type || ''),
                    v: (el.type === 'checkbox' || el.type === 'radio') ? el.checked : el.value,
                    req: el.required || /\*/.test(lb), y: Math.round(r.y), vis: r.width > 0 };
        if (el.tagName === 'SELECT') o.opts = [...el.options].map(x => ({ t: x.text, v: x.value })).slice(0, 30);
        out.push(o);
      });
      return out;
    },

    set(n, v) { const el = this.find(n); return el ? nativeSet(el, v) : 'MISS:' + n; },
    fill(obj) { const r = {}; for (const k in obj) r[k] = this.set(k, obj[k]); return r; },

    // Required fields that are still blank — run before every submit.
    audit() { return this.dump().filter(f => f.vis && f.req && (f.v === '' || f.v === false || f.v === '-999')); },

    errs() {
      return [...D.querySelectorAll('[class*="rror"],[role="alert"]')]
        .map(e => ({ t: e.innerText.trim().slice(0, 120), vis: e.getBoundingClientRect().width > 0 }))
        .filter(x => x.t && x.vis).slice(0, 10);
    },

    // --- file upload into a same-origin iframe -------------------------------
    // The file_upload tool needs a ref, and find/read_page can't see into
    // iframes. So: make a visible proxy input at top level, upload to that,
    // then hand the FileList across. FileList transfers fine same-origin.
    proxyFile() {
      let p = document.getElementById('__proxyfile');
      if (!p) {
        p = document.createElement('input');
        p.type = 'file'; p.id = p.name = '__proxyfile';
        p.setAttribute('aria-label', 'proxy resume upload');
        p.style.cssText = 'position:fixed;top:200px;left:20px;z-index:2147483647;width:300px;height:40px';
        document.body.appendChild(p);
      }
      return 'proxy ready — file_upload to it, then __fd.xfer("<target name>")';
    },
    xfer(target) {
      const src = document.getElementById('__proxyfile');
      if (!src || !src.files.length) return 'proxy empty';
      const t = this.find(target);
      if (!t) return 'target missing: ' + target;
      const dt = new DataTransfer();
      for (const file of src.files) dt.items.add(file);
      t.files = dt.files;
      ['input', 'change'].forEach(e => t.dispatchEvent(new Event(e, { bubbles: true })));
      src.remove();
      return { name: t.files[0]?.name, size: t.files[0]?.size };
    },
  };

  const all = window.__fd.dump();
  return { doc: D === document ? 'top' : 'iframe', visible: all.filter(f => f.vis).length, fields: all.filter(f => f.vis) };
})();
