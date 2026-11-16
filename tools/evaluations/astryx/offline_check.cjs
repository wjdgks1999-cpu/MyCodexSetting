const fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
async function main(){
  const [root]=process.argv.slice(2);
  const p=require(path.join(root,'runtime/node_modules/puppeteer-core'));
  const browser=await p.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  const rows=[];
  try{
    for(const variant of ['S','SA']){
      const folder=path.join(root,'runs',variant,'A05-html/1/project/.human-docs');
      const files=fs.readdirSync(folder).filter(n=>n.endsWith('.html'));
      for(const file of files){
        const page=await browser.newPage(),external=[],errors=[];
        await page.setRequestInterception(true);
        await page.setOfflineMode(true);
        page.on('request',r=>{if(/^(file:|data:|about:)/.test(r.url()))r.continue();else{external.push(r.url());r.abort()}});
        page.on('pageerror',e=>errors.push(String(e)));
        const views=[];
        for(const width of [360,1280]){
          await page.setViewport({width,height:900});
          await page.goto(pathToFileURL(path.join(folder,file)).href,{waitUntil:'load'});
          views.push(await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
            allLabels:Array.from({length:30},(_,i)=>String(i+1).padStart(3,'0')).every(n=>document.body.innerText.includes(n)),
            offline:!navigator.onLine})));
        }
        rows.push({variant,file,views,externalRequests:external,errors,status:external.length===0&&errors.length===0&&views.every(v=>v.allLabels&&v.scrollWidth<=v.width+1)?'PASS':'FAIL'});
        await page.close();
      }
    }
  }finally{await browser.close()}
  fs.writeFileSync(path.join(root,'evidence/offline-browser-r2.json'),JSON.stringify(rows,null,2),{flag:'wx'});
  console.log(JSON.stringify(rows));
}
main().catch(e=>{console.error(e);process.exitCode=1});
