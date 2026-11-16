'use strict';
const $ = id => document.getElementById(id);
const canvas = $('canvas'), ctx = canvas.getContext('2d');
let photo = null, stream = null, running = false, busy = false, ready = false, generation = 0;
const status = msg => { $('status').textContent = msg; };
function controls() {
  $('analyze').disabled = !ready || !photo || busy || running;
  $('camera').disabled = !ready || busy || running;
  $('file').disabled = busy || running;
  $('stop').hidden = !running;
}
let lastFrame = null, lastDetections = [];
function draw(source, detections = []) {
  lastFrame = source; lastDetections = detections;
  canvas.style.display = 'block'; $('placeholder').hidden = true;
  const width = Math.max(1, Math.round(canvas.parentElement.clientWidth));
  const height = Math.max(1, Math.round(width * source.height / source.width));
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  const scaleX = width / source.width, scaleY = height / source.height;
  const fontSize = width < 400 ? 12 : 14, badgeHeight = fontSize + 10, gap = 4;
  ctx.font = `600 ${fontSize}px sans-serif`;
  const occupied = [], badges = [];
  let overflowX = gap, overflowY = height + gap, extraHeight = 0;
  const overlaps = (a,b) => a.x < b.x+b.w+gap && a.x+a.w+gap > b.x && a.y < b.y+b.h+gap && a.y+a.h+gap > b.y;
  detections.forEach((d,index) => {
    const text = `#${index+1} · ${Math.round(d.confidence*100)}%`;
    const w = Math.min(width, Math.ceil(ctx.measureText(text).width) + 12), h = badgeHeight;
    const [x1,y1,x2,y2] = d.bbox;
    const x = Math.max(0,Math.min(width-w,x1*scaleX));
    const candidates = [y1*scaleY-h-gap,y1*scaleY+gap,y2*scaleY-h-gap];
    for (let y=gap;y+h<=height;y+=h+gap) candidates.push(y);
    let spot = null;
    for (const cy of candidates) {
      const a = {x,y:Math.max(0,Math.min(height-h,cy)),w,h};
      if (height>=h && !occupied.some(b=>overlaps(a,b))) { spot=a; break; }
    }
    if (!spot) {
      if (overflowX+w>width) {overflowX=0;overflowY+=h+gap;}
      spot={x:overflowX,y:overflowY,w,h}; overflowX+=w+gap;
      extraHeight=Math.max(extraHeight,overflowY+h+gap-height);
    }
    occupied.push(spot); badges.push({...spot,text,index,box:[x1*scaleX,y1*scaleY,x2*scaleX,y2*scaleY],color:d.class_id===0?'#128257':'#b55c08'});
  });
  canvas.width = Math.round(width*ratio); canvas.height = Math.round((height+extraHeight)*ratio);
  ctx.setTransform(ratio,0,0,ratio,0,0);
  ctx.fillStyle='#edf2eb';ctx.fillRect(0,0,width,height+extraHeight);
  ctx.drawImage(source,0,0,width,height);
  ctx.lineWidth=2;ctx.font=`600 ${fontSize}px sans-serif`;ctx.textBaseline='middle';
  for (const b of badges) {
    const [x1,y1,x2,y2]=b.box;
    ctx.strokeStyle=b.color;ctx.strokeRect(x1,y1,x2-x1,y2-y1);
    // Connect displaced badges to their corresponding box, keeping text unobstructed.
    ctx.beginPath();ctx.moveTo(b.x+b.w/2,b.y+b.h/2);ctx.lineTo(x1,y1);ctx.stroke();
  }
  for (const b of badges) {
    ctx.fillStyle=b.color;ctx.fillRect(b.x,b.y,b.w,b.h);
    ctx.fillStyle='#fff';ctx.fillText(b.text,b.x+6,b.y+b.h/2);
  }
  canvas.setAttribute('aria-label',`${detections.length} detecções numeradas. Descrições completas na lista de resultados.`);
}
let resizeFrame = 0;
new ResizeObserver(() => {
  cancelAnimationFrame(resizeFrame);
  resizeFrame = requestAnimationFrame(() => {if(lastFrame)draw(lastFrame,lastDetections);});
}).observe(canvas.parentElement);
function show(data, elapsed) {
  $('result-title').textContent = data.detections.length ? `${data.detections.length} folha(s) detectada(s)` : 'Resultado inconclusivo';
  $('timing').textContent = `Servidor: ${data.latency_ms} ms · ciclo completo: ${Math.round(elapsed)} ms`;
  $('results').replaceChildren();
  for (const [index,d] of data.detections.entries()) {
    const li = document.createElement('li'), label = document.createElement('strong'), score = document.createElement('span');
    label.textContent = `#${index+1} — ${d.label}`; score.textContent = `Confiança do modelo: ${(d.confidence*100).toFixed(1)}%`;
    li.append(label,score); $('results').append(li);
  }
}
async function analyze(source, token) {
  busy = true; controls(); const start = performance.now();
  const frame = document.createElement('canvas'); frame.width = source.width; frame.height = source.height;
  frame.getContext('2d').drawImage(source,0,0);
  try {
    const blob = await new Promise(resolve => frame.toBlob(resolve,'image/jpeg',.9));
    if (!blob) throw new Error('Não foi possível ler a imagem.');
    const form = new FormData(); form.append('file',blob,'frame.jpg');
    const response = await fetch(`./api/predict?confidence=${$('confidence').value/100}`,{method:'POST',body:form,signal:AbortSignal.timeout(30000)});
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Falha na análise.');
    if (token !== generation) return;
    draw(source,data.detections); show(data,performance.now()-start);
    status(running ? 'Câmera ativa. Analisando um quadro por vez.' : 'Análise concluída.');
  } finally { busy = false; controls(); }
}
$('confidence').oninput = () => { $('threshold-value').textContent = `${$('confidence').value}%`; };
$('file').onchange = async () => {
  const file = $('file').files[0]; if (!file) return;
  photo = null; controls(); $('results').replaceChildren(); $('result-title').textContent='Aguardando análise'; $('timing').textContent='';
  if (file.size > 8*1024*1024) { status('Escolha uma foto de até 8 MB.'); return; }
  try {
    const bitmap = await createImageBitmap(file,{imageOrientation:'from-image'});
    // Resize in browser to reduce upload and memory; both drawing and API use this frame.
    const factor = Math.min(1,1280/Math.max(bitmap.width,bitmap.height));
    photo = document.createElement('canvas'); photo.width = Math.round(bitmap.width*factor); photo.height = Math.round(bitmap.height*factor);
    photo.getContext('2d').drawImage(bitmap,0,0,photo.width,photo.height); bitmap.close();
    draw(photo); status('Foto pronta. Clique em Analisar foto.'); controls();
  } catch { status('Não foi possível abrir essa imagem.'); }
};
$('analyze').onclick = async () => {
  status('Analisando…');
  try { await analyze(photo,++generation); } catch(e) { status(e.message); }
};
function stop() {
  running = false; generation++;
  if (stream) stream.getTracks().forEach(t => t.stop());
  stream = null; $('video').srcObject = null; controls();
}
$('stop').onclick = () => { stop(); status('Câmera encerrada.'); };
$('camera').onclick = async () => {
  busy = true; controls();
  try {
    if (!navigator.mediaDevices?.getUserMedia) throw new Error('A câmera exige localhost ou HTTPS e permissão do navegador.');
    stream = await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment',width:{ideal:640}},audio:false});
    const video = $('video'); video.srcObject = stream; await video.play();
    running = true; busy = false; const token = ++generation; controls();
    while (running && token === generation) {
      const frame = document.createElement('canvas'); frame.width = video.videoWidth; frame.height = video.videoHeight;
      frame.getContext('2d').drawImage(video,0,0);
      await analyze(frame,token);
      await new Promise(resolve => setTimeout(resolve,120));
    }
  } catch(e) { stop(); status(e.message); }
  finally { busy = false; controls(); }
};
window.addEventListener('pagehide',stop);
fetch('./health').then(r=>r.json()).then(data=>{
  ready = data.model_ready; controls();
  status(ready ? 'Modelo disponível. Escolha uma foto ou inicie a câmera.' : 'Modelo indisponível. Treine o modelo e reinicie o servidor.');
}).catch(()=>status('Não foi possível conectar ao servidor.'));
