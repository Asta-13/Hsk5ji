/* Google Fonts-ийг render-ийг хаалгүйгээр ачаална (inline onload нь CSP-д хориотой тул энд). */
(function(){var l=document.querySelector('link[data-async-css]');if(!l)return;function on(){l.media='all'}if(l.sheet)on();else l.addEventListener('load',on);setTimeout(on,4000)})();
if('serviceWorker' in navigator&&location.protocol.indexOf('http')===0){window.addEventListener('load',function(){navigator.serviceWorker.register('sw.js').catch(function(){})})}
