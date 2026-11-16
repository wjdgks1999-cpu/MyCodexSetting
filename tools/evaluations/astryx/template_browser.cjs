const fs=require('node:fs'),path=require('node:path');
async function main(){
  const [runtime,url,out]=process.argv.slice(2);
  fs.mkdirSync(out,{recursive:true});
  const p=require(path.join(runtime,'node_modules/puppeteer-core'));
  const browser=await p.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  const result={views:[],errors:[],externalRequests:[],checks:{}};
  try{
    const page=await browser.newPage();
    await page.setRequestInterception(true);
    page.on('request',r=>{if(r.url().startsWith(url)||r.url().startsWith('data:'))r.continue();else{result.externalRequests.push(r.url());r.abort()}});
    page.on('pageerror',e=>result.errors.push(String(e)));
    page.on('console',m=>{if(m.type()==='error')result.errors.push(m.text())});
    for(const width of [360,768,1280,1920]){
      await page.setViewport({width,height:900});await page.goto(url,{waitUntil:'networkidle0'});
      result.views.push(await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,title:document.querySelector('h1')?.textContent,cards:document.querySelectorAll('h3').length})));
      await page.screenshot({path:path.join(out,`${width}.png`),fullPage:true});
    }
    const initial=await page.$$eval('h3',e=>e.map(x=>x.textContent));
    await page.type('input[placeholder="Search..."]','Stack');
    const filtered=await page.$$eval('h3',e=>e.map(x=>x.textContent));
    result.checks.search=filtered.includes('Stack')&&filtered.length<initial.length;
    await page.focus('input');await page.keyboard.down('Control');await page.keyboard.press('KeyA');await page.keyboard.up('Control');await page.type('input','NO_MATCH_9173');
    result.checks.empty=await page.$$eval('h3',e=>e.length===0);
    result.emptyText=await page.evaluate(()=>document.body.innerText.slice(-500));
    await page.focus('input');await page.keyboard.down('Control');await page.keyboard.press('KeyA');await page.keyboard.up('Control');await page.keyboard.press('Backspace');
    await page.evaluate(()=>{
      const target=[...document.querySelectorAll('button,[role="radio"],[role="button"]')].find(b=>b.getAttribute('aria-label')==='Forms'||b.textContent.trim()==='Forms');
      if(!target)throw new Error('Forms control not found: '+[...document.querySelectorAll('[role],button')].map(x=>`${x.tagName}/${x.getAttribute('role')}/${x.getAttribute('aria-label')}/${x.textContent.slice(0,40)}`).join(';'));
      target.click();
    });
    const forms=await page.$$eval('h3',e=>e.map(x=>x.textContent));
    result.checks.filter=forms.includes('TextInput')&&!forms.includes('Stack')&&forms.length>0;
    result.checks.responsive=result.views.every(v=>v.title==='Library'&&v.cards>0&&v.scrollWidth<=v.width+1);
    result.checks.noRuntimeErrors=result.errors.length===0;
    result.checks.noExternalRequests=result.externalRequests.length===0;
  }catch(e){result.exception=String(e)}finally{await browser.close()}
  result.status=!result.exception&&Object.values(result.checks).every(Boolean)?'PASS':'FAIL';
  fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(result,null,2),{flag:'wx'});
  console.log(JSON.stringify(result));
  if(result.status!=='PASS')process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1});
