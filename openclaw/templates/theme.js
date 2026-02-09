(function(){
  var t = localStorage.getItem('hb-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', t);
  document.addEventListener('DOMContentLoaded', function() {
    var btn = document.querySelector('.theme-btn');
    if (!btn) return;
    function update() {
      var t = document.documentElement.getAttribute('data-theme');
      btn.textContent = t === 'dark' ? '☀' : '☾';
      btn.setAttribute('aria-label', t === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
    }
    btn.addEventListener('click', function() {
      var cur = document.documentElement.getAttribute('data-theme');
      var next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('hb-theme', next);
      update();
    });
    update();
    var path = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-links a').forEach(function(a) {
      a.classList.toggle('active', a.getAttribute('href') === path);
    });
  });
})();
