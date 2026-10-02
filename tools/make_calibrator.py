# -*- coding: utf-8 -*-
r"""
生成字幕校准器.py (v2) —— 全部可点按钮 + 点完立刻显示 + 可输入 + 撤销 + 改动清单
==================================================================
v1 的问题（先生反馈）：只有键盘快捷键 ✗；且在前奏段（t=0）没有"当前句" ⇒ 点了没反应 ✗
v2 改进：
  · 起/止各 4 个按钮（-0.5 / -0.1 / +0.1 / +0.5）× 步长选择
  · 起止时间可直接输入数字
  · 选中的句子 = 点列表 / 自动跟随播放（可开关）
  · 改动立刻显示（时间栏 + 高亮闪一下 + 底部改动清单）
  · 撤销 / 重做 / 恢复本句原值 / 全部恢复
  · 逐字时间随起止**等比缩放**（不是硬截断 ✗）
产物：字幕校准器.html
用法：python 生成字幕校准器.py
"""

import io
import json
import os

import argparse
ap = argparse.ArgumentParser(description="生成单文件字幕校准器")
ap.add_argument("--timing", default="sample/demo_timing.json", help="时间表 JSON")
ap.add_argument("--audio", default="audio.mp3", help="音频路径（写进 HTML 的相对路径）")
ap.add_argument("--out", default="index.html", help="输出的 HTML")
ap.add_argument("--offset", type=float, default=0.0, help="相对时间基准偏移（视频预览用，一般 0）")
A = ap.parse_args()
TIMING, OUT, AUDIO = A.timing, A.out, A.audio
OFFSET_V = A.offset

with io.open(TIMING, encoding="utf-8") as f:
    data = json.load(f)
subs = [{"t": ln["text"], "s": round(ln["start"], 3), "e": round(ln["end"], 3),
         "o": [round(ln["start"], 3), round(ln["end"], 3)],
         "c": [[c["c"], round(c["start"], 3), round(c["end"], 3)] for c in ln.get("chars", [])]}
        for ln in data["lines"]]

HTML = r"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>字幕校准器 v2 · 单位距离</title>
<style>
 :root{--ink:#0a0a0b;--bone:#eee9df;--sig:#ff4d12;--ash:#9c978f;--pnl:#151517}
 *{box-sizing:border-box}
 body{margin:0;background:var(--ink);color:var(--bone);font-family:"Microsoft YaHei",system-ui,sans-serif;font-size:15px}
 .bar{display:flex;gap:10px;align-items:center;padding:9px 14px;border-bottom:1px solid #22252b;flex-wrap:wrap}
 button{background:var(--pnl);color:var(--bone);border:1px solid #3a3f47;border-radius:6px;padding:6px 12px;cursor:pointer;font-size:15px}
 button:hover{border-color:var(--sig);color:var(--sig)}
 button.hot{border-color:var(--sig);color:var(--sig)}
 input[type=number]{background:#0f1012;color:var(--bone);border:1px solid #3a3f47;border-radius:5px;padding:5px 7px;font-family:Consolas,monospace;font-size:15px}
 select{background:var(--pnl);color:var(--bone);border:1px solid #3a3f47;border-radius:5px;padding:5px}
 #stage{padding:14px 16px 4px}
 #karaoke{font-size:60px;font-weight:700;min-height:84px;line-height:1.25;letter-spacing:2px}
 #sel{margin-top:10px;background:var(--pnl);border:1px solid #2a2d33;border-radius:8px;padding:10px 12px}
 #sel .lab{color:var(--ash);font-size:13px;margin-bottom:6px}
 .grp{display:flex;gap:8px;align-items:center;margin:6px 0;flex-wrap:wrap}
 .grp .tag{color:var(--ash);min-width:44px}
 .val{font-family:Consolas,monospace;font-size:20px;color:var(--sig);min-width:104px;text-align:center}
 #msg{color:var(--sig);font-size:13px;min-height:18px}
 .ctx{padding:2px 16px;color:#5c5f66;font-size:19px;height:28px;overflow:hidden}
 #tlbox{padding:8px 16px}
 #tl{width:100%;height:32px;background:var(--pnl);border:1px solid #2a2d33;border-radius:4px;position:relative;cursor:pointer}
 .mk{position:absolute;top:0;bottom:0;width:1px;background:#3a3f47}
 .cur{position:absolute;top:-3px;bottom:-3px;width:2px;background:var(--sig);pointer-events:none}
 #list{max-height:30vh;overflow:auto;padding:4px 16px 8px;font-size:14px}
 .row{display:flex;gap:10px;padding:3px 6px;border-radius:4px;cursor:pointer;font-family:Consolas,monospace}
 .row:hover{background:var(--pnl)} .row.on{background:#241206;color:var(--sig)}
 .row.chg .tm{color:#3fa34d}
 #log{padding:4px 16px 22px;color:var(--ash);font-size:13px;font-family:Consolas,monospace;max-height:14vh;overflow:auto}
 #foot{padding:2px 16px 16px;color:#5c5f66;font-size:12.5px;line-height:1.7}
 kbd{background:var(--pnl);border:1px solid #3a3f47;border-radius:4px;padding:1px 5px;color:var(--bone)}
</style></head><body>
<div class="bar">
  <b id="tc">0.00</b><span>/ <span id="dur">—</span> s</span>
  <button id="pp">▶ 播放</button><button id="b-">« 5s</button><button id="b+">5s »</button>
  <span>步长</span><select id="step"><option>0.02</option><option>0.05</option><option selected>0.10</option><option>0.25</option><option>0.50</option></select>
  <button id="lp">循环本句：关</button>
  <button id="rl">连带顺延：开</button>
  <button id="fl">跟随播放：开</button>
  <button id="exp">⬇ 导出时间表</button>
  <button id="cp">复制</button>
  <span id="msg"></span>
  <span id="status" style="color:#9c978f">音频：加载中…</span>
  <button id="pickBtn">📂 选择音频文件</button>
  <input type="file" id="pick" accept="audio/*" style="display:none">
</div>

<div id="stage">
  <div id="karaoke">（前奏）</div>
  <div id="sel">
    <div class="lab">当前选中的句子（点下方列表可切换）</div>
    <div class="grp"><span class="tag">起</span>
      <button data-act="s-" data-d="-0.5">−0.5</button><button data-act="s-" data-d="-0.1">−0.1</button>
      <input type="number" id="is" step="0.01"><span style="color:var(--ash)">s</span>
      <button data-act="s+" data-d="0.1">+0.1</button><button data-act="s+" data-d="0.5">+0.5</button>
      <span class="val" id="vs">—</span></div>
    <div class="grp"><span class="tag">止</span>
      <button data-act="e-" data-d="-0.5">−0.5</button><button data-act="e-" data-d="-0.1">−0.1</button>
      <input type="number" id="ie" step="0.01"><span style="color:var(--ash)">s</span>
      <button data-act="e+" data-d="0.1">+0.1</button><button data-act="e+" data-d="0.5">+0.5</button>
      <span class="val" id="ve">—</span></div>
    <div class="grp">
      <button id="goto">⏱ 定位到这句</button>
      <button id="loopOne">🔁 只循环这句</button>
      <button id="undo">↶ 撤销</button><button id="redo">↷ 重做</button>
      <button id="resetOne">恢复本句原值</button><button id="resetAll">全部恢复</button>
    </div>
    <div id="act" style="margin-top:8px;font-family:Consolas,monospace;font-size:15px;color:var(--sig);min-height:22px">最近操作：（点一下上面任意按钮，这里会显示结果）</div>
  </div>
</div>
<div class="ctx" id="prev"></div><div class="ctx" id="next"></div>
<div id="tlbox"><div id="tl"></div></div>
<div id="list"></div>
<div id="log"></div>
<div id="foot">
  键盘（需先点一下页面）：<kbd>空格</kbd>播放 ｜ <kbd>←</kbd><kbd>→</kbd>±0.5s ｜ <kbd>a</kbd><kbd>d</kbd>起点 ∓ ｜ <kbd>w</kbd><kbd>s</kbd>终点 ∓ ｜ <kbd>,</kbd><kbd>.</kbd>换句 ｜ <kbd>L</kbd>循环 ｜
  改完点「导出时间表」把文件给我 ✓
</div>
<audio id="au" src="__AUDIO__" preload="auto"></audio>
<script>
const LINES = __DATA__;
const au = document.getElementById('au');
const $ = id => document.getElementById(id);
let cur = 0, loop = false, ripple = true, follow = true, step = 0.10;
let DUR = 221.93;                       // 音频未就绪时用已知歌曲时长兜底
window.onerror=(m,src,l)=>{const e=$('status'); if(e){e.textContent='⚠ JS 错误：'+m+' @行'+l; e.style.color='#ff4d12';}};
const hist = [], undone = [];

function fmt(x){ const m=Math.floor(x/60), s=x-m*60; return String(m).padStart(2,'0')+':'+s.toFixed(2).padStart(5,'0'); }
function idxAt(t){ for(let i=0;i<LINES.length;i++){ if(t>=LINES[i].s&&t<=LINES[i].e) return i; }
  let k=0; for(let i=0;i<LINES.length;i++){ if(LINES[i].s<=t) k=i; } return k; }        // 前奏段也给"最近的一句"

function msg(s){ $('msg').textContent = s; clearTimeout(msg._t); msg._t=setTimeout(()=>$('msg').textContent='',1600); }
function act(s){ $('act').textContent = s; }
function flash(el){ el.style.transition='none'; el.style.color='#fff'; setTimeout(()=>{ el.style.transition='color .5s'; el.style.color='var(--sig)'; }, 60); }
function logline(s){ const d=document.createElement('div'); d.textContent=s; $('log').prepend(d);
  while($('log').childNodes.length>60) $('log').lastChild.remove(); }
function stopFollow(why){ if(follow){ follow=false; $('fl').textContent='跟随播放：关'; act('已自动关闭「跟随播放」以便你调 '+why); } }

function rescaleChars(L){                 // 逐字时间随起止**等比缩放**（不硬截断）
  const os=L.o[0], oe=L.o[1], ns=L.s, ne=L.e, k=(ne-ns)/Math.max(1e-6,oe-os);
  L.c.forEach(c=>{ c[1]=+(ns+(c[1]-os)*k).toFixed(3); c[2]=+(ns+(c[2]-os)*k).toFixed(3); });
}
function setLine(i, ns, ne, why){
  const L=LINES[i]; if(!L) return;
  ns=Math.max(0,Math.min(ns, DUR)); ne=Math.max(ns+0.05, Math.min(ne, DUR));
  hist.push({i, s:L.s, e:L.e}); undone.length=0;
  L.s=+ns.toFixed(3); L.e=+ne.toFixed(3); rescaleChars(L);
  if(ripple){ if(i>0 && LINES[i-1].e>L.s) { LINES[i-1].e=L.s; } if(i<LINES.length-1 && LINES[i+1].s<L.e) { LINES[i+1].s=L.e; } }
  refresh(); logline('第'+(i+1)+'句 '+(why||'')+' → '+fmt(L.s)+' ~ '+fmt(L.e)+'  「'+L.t+'」');
}
function nudge(which, d, big){
  const L=LINES[cur]; if(!L) return;
  if(au.paused===false){ au.pause(); $('pp').textContent='▶ 播放'; }   // 微调时自动暂停
  stopFollow('这一句');
  const k = big?5:1, dd = d*k;
  const before = (which==='s')? L.s : L.e;
  if(which==='s') setLine(cur, L.s+dd, L.e, (dd>0?'起点 +':'起点 ')+dd);
  else            setLine(cur, L.s, L.e+dd, (dd>0?'止点 +':'止点 ')+dd);
  const after = (which==='s')? LINES[cur].s : LINES[cur].e;
  act('第 '+(cur+1)+' 句「'+L.t+'」'+(which==='s'?'起':'止')+'：'+fmt(before)+' → '+fmt(after)+(Math.abs(after-before)<1e-6?'（没变，可能已到边界）':'  ✓'));
  flash(which==='s'?$('vs'):$('ve'));
}
function refresh(){
  const L=LINES[cur]; if(!L) return;
  $('is').value=L.s.toFixed(2); $('ie').value=L.e.toFixed(2);
  $('vs').textContent='起 '+fmt(L.s); $('ve').textContent='止 '+fmt(L.e);
  $('karaoke').style.filter='none'; setTimeout(()=>{},0);
  renderList(); paintList();
}
function paintList(){
  document.querySelectorAll('#list .row').forEach((r,i)=>{
    r.classList.toggle('on', i===cur);
    r.classList.toggle('chg', LINES[i].s!==LINES[i].o[0] || LINES[i].e!==LINES[i].o[1]);
  });
  const on=document.querySelector('#list .row.on'); if(on) on.scrollIntoView({block:'nearest'});
}
function renderList(){
  if(renderList._done) return; renderList._done=true;
  $('list').innerHTML = LINES.map((L,i)=>'<div class="row" data-i="'+i+'"><span class="tm">'+fmt(L.s)+' → '+fmt(L.e)+'</span><span>'+L.t+'</span></div>').join('');
  document.querySelectorAll('#list .row').forEach(r=>{ r.onclick=()=>{ cur=+r.dataset.i; follow=false; $('fl').textContent='跟随播放：关'; au.currentTime=LINES[cur].s+0.01; refresh(); }; });
}
function loopDraw(){
  const t=au.currentTime; $('tc').textContent=t.toFixed(2);
  if(follow){ const i=idxAt(t); if(i!==cur){ cur=i; refresh(); } }
  const L=LINES[cur];
  if(L){
    let html='';
    for(const c of L.c){
      const col=(t>=c[2])?'var(--bone)':((t>=c[1])?'var(--sig)':'rgba(238,233,223,0.22)');
      const ul=(t>=c[1]&&t<c[2])?'border-bottom:4px solid var(--sig);':'';
      html+='<span style="color:'+col+';'+ul+'">'+c[0]+'</span>';
    }
    $('karaoke').innerHTML=html;
    const p=LINES[cur-1], n=LINES[cur+1];
    $('prev').textContent=p?('上一句 '+fmt(p.s)+'  '+p.t):'';
    $('next').textContent=n?('下一句 '+fmt(n.s)+'  '+n.t):'';
  }
  const c=$('tl').querySelector('.cur'); if(c) c.style.left=(100*t/DUR)+'%';
  requestAnimationFrame(loopDraw);
}
function timeline(){
  $('tl').innerHTML = LINES.map(L=>'<div class="mk" style="left:'+(100*L.s/DUR)+'%"></div>').join('')+'<div class="cur" style="left:0%"></div>';
  $('tl').onclick=e=>{ const r=$('tl').getBoundingClientRect(); au.currentTime=DUR*(e.clientX-r.left)/r.width; };
}
// —— 按钮（不依赖键盘焦点）——
document.querySelectorAll('button[data-act]').forEach(b=>{
  b.onclick=()=>{ const act=b.dataset.act, d=parseFloat(b.dataset.d); nudge(act[0], d, false); };
});
$('is').onchange=()=>{ const v=parseFloat($('is').value); if(!isNaN(v)) setLine(cur, v, LINES[cur].e, '起点输入'); };
$('ie').onchange=()=>{ const v=parseFloat($('ie').value); if(!isNaN(v)) setLine(cur, LINES[cur].s, v, '止点输入'); };
$('pp').onclick=()=>{ if(au.paused){ au.play(); $('pp').textContent='⏸ 暂停'; } else { au.pause(); $('pp').textContent='▶ 播放'; } };
$('b-').onclick=()=>{ au.currentTime=Math.max(0,au.currentTime-5); };
$('b+').onclick=()=>{ au.currentTime=Math.min(DUR,au.currentTime+5); };
$('step').onchange=e=>{ step=parseFloat(e.target.value); };
$('lp').onclick=e=>{ loop=!loop; e.target.textContent='循环本句：'+(loop?'开':'关'); };
$('rl').onclick=e=>{ ripple=!ripple; e.target.textContent='连带顺延：'+(ripple?'开':'关'); };
$('fl').onclick=e=>{ follow=!follow; e.target.textContent='跟随播放：'+(follow?'开':'关'); };
$('goto').onclick=()=>{ au.currentTime=LINES[cur].s+0.01; };
$('loopOne').onclick=()=>{ loop=true; $('lp').textContent='循环本句：开'; au.currentTime=LINES[cur].s+0.01; au.play(); $('pp').textContent='⏸ 暂停'; };
$('undo').onclick=()=>{ const h=hist.pop(); if(!h){ msg('没有可撤销的改动'); return; }
  undone.push({i:h.i,s:LINES[h.i].s,e:LINES[h.i].e}); LINES[h.i].s=h.s; LINES[h.i].e=h.e; rescaleChars(LINES[h.i]);
  cur=h.i; refresh(); logline('撤销 第'+(h.i+1)+'句 → '+fmt(h.s)+' ~ '+fmt(h.e)); };
$('redo').onclick=()=>{ const h=undone.pop(); if(!h){ msg('没有可重做的改动'); return; }
  hist.push({i:h.i,s:LINES[h.i].s,e:LINES[h.i].e}); LINES[h.i].s=h.s; LINES[h.i].e=h.e; rescaleChars(LINES[h.i]);
  cur=h.i; refresh(); logline('重做 第'+(h.i+1)+'句 → '+fmt(h.s)+' ~ '+fmt(h.e)); };
$('resetOne').onclick=()=>{ setLine(cur, LINES[cur].o[0], LINES[cur].o[1], '恢复原值'); };
$('resetAll').onclick=()=>{ hist.length=0; LINES.forEach(L=>{ L.s=L.o[0]; L.e=L.o[1]; rescaleChars(L); }); refresh(); logline('已全部恢复原值'); };
function text(){ return LINES.map(L=>fmt(L.s)+' → '+fmt(L.e)+'  '+L.t).join('\n')+'\n'; }
$('exp').onclick=()=>{ const b=new Blob([text()],{type:'text/plain;charset=utf-8'});
  const a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download='字幕校准_导出.txt'; a.click(); };
$('cp').onclick=async e=>{ try{ await navigator.clipboard.writeText(text()); e.target.textContent='已复制 ✓'; setTimeout(()=>e.target.textContent='复制',1200);}catch(_){ e.target.textContent='用导出'; } };
addEventListener('keydown',e=>{
  const big=e.shiftKey;
  if(e.code==='Space'){ e.preventDefault(); $('pp').click(); }
  else if(e.key==='ArrowLeft'){ au.currentTime-=0.5; } else if(e.key==='ArrowRight'){ au.currentTime+=0.5; }
  else if(e.key==='a') nudge('s',-step,big); else if(e.key==='d') nudge('s',step,big);
  else if(e.key==='w') nudge('e',-step,big); else if(e.key==='s') nudge('e',step,big);
  else if(e.key===','){ cur=Math.max(0,cur-1); refresh(); } else if(e.key==='.'){ cur=Math.min(LINES.length-1,cur+1); refresh(); }
  else if(e.key==='l'||e.key==='L'){ $('lp').click(); }
});
au.addEventListener('timeupdate',()=>{ if(loop && au.currentTime>LINES[cur].e) au.currentTime=LINES[cur].s; });
function initAll(){ $('dur').textContent=DUR.toFixed(2); timeline(); renderList(); refresh(); loopDraw(); }
document.addEventListener('DOMContentLoaded', initAll);   // 不等音频，先让界面可用
au.addEventListener('error',()=>{ const e=$('status'); e.textContent='⚠ 音频加载失败 —— 点右边「选择音频文件」手动指定'; e.style.color='#ff4d12'; });
$('pickBtn').onclick=()=>$('pick').click();
$('pick').onchange=ev=>{ const f=ev.target.files[0]; if(f){ au.src=URL.createObjectURL(f); au.play(); const e=$('status'); e.textContent='已加载：'+f.name; e.style.color='#9c978f'; } };
au.addEventListener('loadedmetadata',()=>{ DUR=au.duration||DUR; $('dur').textContent=DUR.toFixed(2); const e=$('status'); e.textContent='音频已就绪 '+DUR.toFixed(2)+'s'; e.style.color='#9c978f'; timeline();
  if(location.search.indexOf('selftest')>=0){                        // 自检模式：自动点一次按钮并显示结果
    setTimeout(()=>{
      const L=LINES[cur];
      const b4={s:L.s,e:L.e};
      document.querySelector('button[data-act="s-"]').click();
      document.querySelector('button[data-act="e-"]').click();
      const af={s:LINES[cur].s,e:LINES[cur].e};
      const okS=Math.abs((b4.s-af.s)-0.1)<1e-6, okE=Math.abs((b4.e-af.e)-0.1)<1e-6;
      const d=document.createElement('div');
      d.style.cssText='position:fixed;left:0;top:0;right:0;z-index:9;background:#000;color:#ff4d12;font:700 30px Consolas,monospace;padding:16px;line-height:1.6';
      d.textContent='SELFTEST 前 起'+b4.s.toFixed(2)+' 止'+b4.e.toFixed(2)+' → 后 起'+af.s.toFixed(2)+' 止'+af.e.toFixed(2)
        +' ｜ 起点'+(okS?'OK':'FAIL')+' 止点'+(okE?'OK':'FAIL');
      document.body.appendChild(d);
    }, 400);
  }
});
</script></body></html>
"""

html = HTML.replace("__DATA__", json.dumps(subs, ensure_ascii=False)).replace("__AUDIO__", AUDIO)
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("已生成：%s（%.0f KB）｜ 内嵌 %d 行" % (OUT, os.path.getsize(OUT) / 1024, len(subs)))
