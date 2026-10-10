// Renders cv/src/*.html to PDF with Playwright (node cv/render.cjs). Run from repo root.
const {chromium}=require('playwright');const path=require('path');
(async()=>{const b=await chromium.launch();
 for(const [src,out] of [['cv-en','Alaa-Saijary-CV.pdf'],['cv-ar','Alaa-Saijary-CV-ar.pdf']]){
  const pg=await b.newPage();await pg.goto('file://'+path.resolve(__dirname,'src',src+'.html'),{waitUntil:'networkidle'});
  await pg.pdf({path:path.resolve(__dirname,out),format:'A4',printBackground:true,preferCSSPageSize:true});await pg.close();}
 await b.close();})();
