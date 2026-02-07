(function(){
  var t = localStorage.getItem('hb-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', t);
  document.addEventListener('DOMContentLoaded', function() {
    var btn = document.getElementById('theme-toggle');
    if (!btn) return;
    function update() {
      var t = document.documentElement.getAttribute('data-theme');
      btn.textContent = t === 'dark' ? 'Light Mode' : 'Dark Mode';
    }
    btn.addEventListener('click', function() {
      var cur = document.documentElement.getAttribute('data-theme');
      var next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('hb-theme', next);
      update();
    });
    update();
  });
})();
