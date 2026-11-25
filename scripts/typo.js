// Привязывает предлоги, союзы и частицы к следующему слову неразрывным пробелом,
// чтобы «на», «в», «и» не висели в конце строки. Работает и с тем, что дорисовывает JS.
// Тот же список — в scripts/typo.py для страниц, которые собирает Python.
(() => {
  const WORDS = [
    // ru
    'а','без','в','во','да','для','до','за','и','из','изо','или','к','ко','на','над','не','ни','но',
    'о','об','обо','от','ото','по','под','при','про','с','со','у','через','перед','между','как','что',
    // uz
    'va','u','bu','har','bir','eng',
    // en
    'a','an','the','and','or','but','of','in','on','at','to','by','for','with','from','vs','no','not',
  ];
  const RE = new RegExp(`(?<![\\p{L}\\d'’‘\`-])(${WORDS.join('|')}) +(?=[\\p{L}\\d«„"(])`, 'giu');
  const SKIP = /^(SCRIPT|STYLE|TEXTAREA|INPUT|CODE|PRE)$/;
  const fix = node => {
    const t = node.nodeValue;
    if (!t || t.indexOf(' ') < 0) return;
    const n = t.replace(RE, '$1 ');
    if (n !== t) node.nodeValue = n;
  };
  const walk = root => {
    if (root.nodeType === 3) { if (!SKIP.test(root.parentNode?.nodeName || '')) fix(root); return; }
    if (root.nodeType !== 1 || SKIP.test(root.nodeName)) return;
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: n => SKIP.test(n.parentNode.nodeName) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT,
    });
    for (let n; (n = w.nextNode());) fix(n);
  };
  const start = () => {
    walk(document.body);
    new MutationObserver(list => {
      for (const m of list) {
        if (m.type === 'characterData') walk(m.target);
        else m.addedNodes.forEach(walk);
      }
    }).observe(document.body, { childList: true, subtree: true, characterData: true });
  };
  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', start) : start();
})();
