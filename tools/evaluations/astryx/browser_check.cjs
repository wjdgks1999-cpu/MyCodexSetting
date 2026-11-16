// Independent browser checks of synthetic local React fixtures.
const fs = require('node:fs');
const path = require('node:path');
async function main(){
  const [runtime,url,out] = process.argv.slice(2);
  fs.mkdirSync(out,{recursive:true});
  const puppeteer = require(path.join(runtime,'node_modules/puppeteer-core'));
  const browser = await puppeteer.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  const report={browser:await browser.version(),viewports:[],errors:[],httpErrors:[],externalRequests:[],checks:{},imeMode:'synthetic DOM composition/keydown; OS IME NOT_RUN'};
  const page=await browser.newPage();
  page.on('pageerror',e=>report.errors.push(String(e)));
  page.on('response',r=>{if(r.status()>=400)report.httpErrors.push({url:r.url(),status:r.status()})});
  page.on('console',m=>{if(m.type()==='error')report.errors.push(m.text())});
  await page.setRequestInterception(true);
  page.on('request',r=>{if(r.url().startsWith(url)||/^(data:|about:)/.test(r.url()))r.continue();else{report.externalRequests.push(r.url());r.abort()}});
  try{
    for(const width of [360,768,1280,1920]){
      await page.setViewport({width,height:900});
      await page.goto(url,{waitUntil:'networkidle0',timeout:60000});
      await page.waitForSelector('input[type="search"]');
      const v=await page.evaluate(()=>({scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth,
        brand:getComputedStyle(document.querySelector('#brand')).color,logo:document.querySelector('svg rect').getAttribute('fill'),
        tailwindWeight:getComputedStyle(document.querySelector('#tailwind-canary')).fontWeight,
        tailwindColor:getComputedStyle(document.querySelector('#tailwind-canary')).color,
        requiredText:['공공데이터 길잡이','자료 · 검색','공개 자료의 출처와 기준일을 확인하세요.'].every(x=>document.body.innerText.includes(x)),
        astryxButton:!!document.querySelector('.astryx-button'),astryxInput:!!document.querySelector('.astryx-text-input'),
        searchName:document.querySelector('input[type="search"]').labels?.[0]?.textContent,
        buttonColor:getComputedStyle(document.querySelector('#search')).backgroundColor,
        buttonHeight:document.querySelector('#search').getBoundingClientRect().height,
        nativeEmailBorder:getComputedStyle(document.querySelector('#email')).borderTopWidth+' '+getComputedStyle(document.querySelector('#email')).borderTopStyle,
        nativeEmailHeight:document.querySelector('#email').getBoundingClientRect().height,
        paragraphMargin:getComputedStyle(document.querySelector('#brand')).marginTop
      }));
      report.viewports.push({width,...v,noOverflow:v.scrollWidth<=v.clientWidth+1});
      await page.screenshot({path:path.join(out,`${width}.png`),fullPage:true});
    }
    await page.type('input[type="search"]','하천'); await page.click('#search');
    report.checks.koreanSearch=JSON.stringify(await page.$$eval('#results li',els=>els.map(x=>x.textContent)))===JSON.stringify(['하천 수질 자료']);
    await page.focus('input[type="search"]'); await page.keyboard.down('Control');await page.keyboard.press('KeyA');await page.keyboard.up('Control');await page.keyboard.press('Backspace');
    await page.select('#category','transport');await page.click('#search');
    report.checks.categoryFilter=JSON.stringify(await page.$$eval('#results li',els=>els.map(x=>x.textContent)))===JSON.stringify(['대중교통 자료']);
    await page.type('#email','invalid'); await page.click('#contact button');
    report.checks.invalidEmailBlocked=await page.$eval('#status',x=>x.textContent==='');
    await page.focus('#email');await page.keyboard.down('Control');await page.keyboard.press('KeyA');await page.keyboard.up('Control');await page.type('#email','fixture@example.test');await page.click('#contact button');
    report.checks.contact=await page.$eval('#status',x=>x.textContent==='입력 형식 확인: 전송하지 않았습니다.');
    await page.focus('input[type="search"]');await page.keyboard.press('Tab');
    report.checks.keyboardToButton=await page.evaluate(()=>document.activeElement.id==='search');
    report.checks.visibleFocus=await page.evaluate(()=>{let s=getComputedStyle(document.activeElement);return s.outlineStyle!=='none'&&parseFloat(s.outlineWidth)>0});
    await page.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'reduce'}]);
    report.checks.reducedMotionMedia=await page.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches);
    const ime=await page.$('section input');
    await ime.evaluate(el=>{
      el.dispatchEvent(new CompositionEvent('compositionstart',{bubbles:true,data:'ㅎ'}));
      el.dispatchEvent(new KeyboardEvent('keydown',{bubbles:true,key:'Enter',code:'Enter',keyCode:229,isComposing:true}));
    });
    report.checks.compositionEnterSuppressed=await page.$eval('#enter-count',x=>x.textContent==='0');
    await ime.evaluate(el=>{
      el.dispatchEvent(new CompositionEvent('compositionend',{bubbles:true,data:'한'}));
      el.dispatchEvent(new KeyboardEvent('keydown',{bubbles:true,key:'Enter',code:'Enter',keyCode:229,isComposing:false}));
    });
    report.checks.key229Suppressed=await page.$eval('#enter-count',x=>x.textContent==='0');
    await ime.focus();await page.keyboard.press('Enter');
    report.checks.normalEnterOnce=await page.$eval('#enter-count',x=>x.textContent==='1');
    await page.addScriptTag({path:path.join(runtime,'node_modules/axe-core/axe.min.js')});
    report.accessibility=await page.evaluate(async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}});return {violations:r.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>n.target)})),incomplete:r.incomplete.map(v=>v.id)}});
    report.checks.automatedA11y=report.accessibility.violations.length===0;
    report.checks.runtimeErrors=report.errors.length===0;
    report.checks.noExternalRequests=report.externalRequests.length===0;
    report.checks.allWidths=report.viewports.every(v=>v.noOverflow&&v.requiredText&&v.brand==='rgb(109, 40, 217)'&&v.logo==='#6d28d9');
  }catch(e){report.exception=String(e)}finally{await browser.close()}
  report.status=!report.exception&&Object.values(report.checks).every(Boolean)?'PASS':'FAIL';
  fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2),{flag:'wx'});
  console.log(JSON.stringify(report));
  if(report.status!=='PASS')process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1});
