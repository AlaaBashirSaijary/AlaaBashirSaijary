// Generates assets/*.png (social cards + touch icon) with Playwright. Run: node tools/og.cjs
const {chromium}=require('playwright');const path=require('path');
const cards={
 'og-home-en':{dir:'ltr',lang:'en',k:'ALAA SAIJARY',t:'Flutter & Laravel Developer',s:'Mobile apps · Web solutions · Syria',mark:'A.S'},
 'og-home-ar':{dir:'rtl',lang:'ar',k:'ألاء سيجري',t:'مطوّرة Flutter وLaravel',s:'تطبيقات موبايل · حلول ويب · سوريا',mark:'A.S'},
 'og-clinic-en':{dir:'ltr',lang:'en',k:'AAYADATI',t:'Clinic management app that works offline',s:'iPad & Android · Arabic interface · 14-day free trial',mark:'℞'},
 'og-school-en':{dir:'ltr',lang:'en',k:'EDUCATION ERP',t:'School management system',s:'QR attendance · Fees · Parent alerts · Arabic & English',mark:'ERP'},
 'og-school-ar':{dir:'rtl',lang:'ar',k:'Education ERP',t:'نظام إدارة المدارس',s:'حضور QR · أقساط · إشعارات للأهل · عربي وإنجليزي',mark:'ERP'},
 'og-clinic-ar':{dir:'rtl',lang:'ar',k:'عيادتي',t:'تطبيق إدارة عيادات يعمل بلا إنترنت',s:'آيباد وأندرويد · واجهة عربية · تجربة مجانية 14 يوماً',mark:'℞'},
};
const page=(c)=>`<!doctype html><html lang="${c.lang}" dir="${c.dir}"><head><meta charset="utf-8"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fira+Sans:wght@600;800&family=Cairo:wght@600;800&display=swap"><style>
*{box-sizing:border-box;margin:0}body{width:1200px;height:630px;font-family:'Fira Sans','Cairo',sans-serif;color:#fff;background:linear-gradient(115deg,#2e0f2a,#4a1942 55%,#7a2f6b);position:relative;overflow:hidden;display:flex;align-items:center;padding:0 90px}
body::before{content:"";position:absolute;inset:0;background:radial-gradient(520px circle at 85% 30%,rgba(231,169,195,.35),transparent 60%),repeating-linear-gradient(135deg,rgba(255,255,255,.03) 0 2px,transparent 2px 46px)}
.in{position:relative;max-width:700px}.k{color:#f0c6d8;font-weight:600;letter-spacing:.14em;font-size:26px;margin-bottom:22px}
h1{font-weight:800;font-size:${c.lang==='ar'?'72px':'74px'};line-height:${c.lang==='ar'?'1.3':'1.1'}}.s{margin-top:26px;font-size:30px;color:#f3dce8;font-weight:600}
.m{position:absolute;inset-inline-end:90px;top:50%;transform:translateY(-50%) rotate(-6deg);width:250px;height:250px;border-radius:64px;background:#e7a9c3;color:#4a1942;font:800 ${c.mark.length>1?'104px':'150px'}/250px Georgia,serif;text-align:center;box-shadow:0 40px 80px rgba(0,0,0,.35)}
.u{position:absolute;bottom:34px;inset-inline-start:90px;font-size:22px;color:#e7a9c3;font-weight:600;direction:ltr}
</style></head><body><div class="in"><div class="k">${c.k}</div><h1>${c.t}</h1><div class="s">${c.s}</div></div><div class="m">${c.mark}</div><div class="u">alaabashirsaijary.github.io/AlaaBashirSaijary</div></body></html>`;
(async()=>{const b=await chromium.launch();const out=path.resolve(__dirname,'..','assets');
 for(const [n,c] of Object.entries(cards)){const p=await b.newPage({viewport:{width:1200,height:630}});await p.setContent(page(c),{waitUntil:'networkidle'});await p.screenshot({path:path.join(out,n+'.png')});await p.close();}
 const svg=require('fs').readFileSync(path.join(out,'favicon.svg'),'utf8').replace('rx="16"','rx="0"').replace('<svg ','<svg width="180" height="180" ');
 const p=await b.newPage({viewport:{width:180,height:180}});await p.setContent('<body style="margin:0">'+svg+'</body>');await p.screenshot({path:path.join(out,'apple-touch-icon.png')});
 await b.close();})();
