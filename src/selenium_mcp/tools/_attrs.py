"""
Shared accessibility-relevant attribute snapshot.

Both element interactions and assertions capture the same set of attributes at
interaction time, so codegen can prefer accessibility-first Selenium Boot
locators (getByRole / getByLabel / getByTestId / getByPlaceholder / ...) no
matter which raw selector was used to reach the element. One JS round-trip;
best-effort — never raises.
"""

# NOTE: braces are doubled where literal because this is a plain string (not an
# f-string); it is passed verbatim to execute_script.
SEMANTIC_ATTRS_JS = r"""
const e = arguments[0];
if (!e || !e.getAttribute) return {};
// Associated <label> text — the strongest accessibility-first locator for form
// controls. Prefers aria-labelledby, then label[for=id] / wrapping <label>,
// then the .labels collection.
let labelText = '';
try {
  const lb = e.getAttribute('aria-labelledby');
  if (lb) {
    labelText = lb.split(/\s+/)
      .map(function(id){var r=document.getElementById(id);return r?r.textContent:'';})
      .join(' ').trim();
  }
  if (!labelText && e.id) {
    var forLab = document.querySelector('label[for="' + (window.CSS && CSS.escape ? CSS.escape(e.id) : e.id) + '"]');
    if (forLab) labelText = forLab.textContent.trim();
  }
  if (!labelText && e.closest) {
    var wrap = e.closest('label');
    if (wrap) labelText = wrap.textContent.trim();
  }
  if (!labelText && e.labels && e.labels.length) {
    labelText = Array.prototype.map.call(e.labels, function(l){return l.textContent;}).join(' ').trim();
  }
} catch (x) {}
return {
  tag: e.tagName ? e.tagName.toLowerCase() : '',
  type: (e.getAttribute('type') || '').toLowerCase(),
  testid: e.getAttribute('data-testid') || e.getAttribute('data-test-id')
          || e.getAttribute('data-test') || e.getAttribute('data-cy') || '',
  role: e.getAttribute('role') || '',
  ariaLabel: e.getAttribute('aria-label') || '',
  label: (labelText || '').replace(/\s+/g, ' ').trim().slice(0, 80),
  placeholder: e.getAttribute('placeholder') || '',
  alt: e.getAttribute('alt') || '',
  title: e.getAttribute('title') || '',
  idAttr: e.getAttribute('id') || '',
  nameAttr: e.getAttribute('name') || '',
  text: (e.textContent || '').trim().slice(0, 80)
};
"""


def semantic_attrs(driver, el) -> dict:
    """Snapshot an element's accessibility-relevant attributes. Best-effort."""
    try:
        return driver.execute_script(SEMANTIC_ATTRS_JS, el) or {}
    except Exception:
        return {}
