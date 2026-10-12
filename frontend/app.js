const app=document.getElementById("app"),statusEl=document.getElementById("status");
async function api(path,options={}){const r=await fetch("/api"+path,{headers:{"Content-Type":"application/json"},...options});const d=await r.json();if(!r.ok)throw Error(d.detail||"Erro na API");return d}
const esc=v=>String(v??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[m]));
const money=v=>Number(v||0).toLocaleString("pt-BR",{style:"currency",currency:"BRL"});

async function home(){const d=await api("/dashboard");app.innerHTML=`<div class="container"><section class="hero"><p class="muted">Projeto demonstrativo • Plataforma de streaming</p><h1>Seu banco virou uma plataforma.</h1><p class="muted">Explore o catálogo e veja como os dados se conectam por meio de uma API e um banco MySQL.</p><div class="actions"><button class="primary" onclick="page('catalogo')">Explorar catálogo</button><button onclick="page('admin')">Painel admin</button><button onclick="page('analytics')">Analytics</button></div></section><div class="grid">${Object.entries(d).map(([k,v])=>`<div class="card"><div class="muted">${k}</div><div class="metric">${v}</div></div>`).join("")}</div></div>`}

async function catalogo(){const [items,genres]=await Promise.all([api("/conteudos"),api("/generos")]);app.innerHTML=`<div class="container"><h1>Catálogo</h1><p class="muted">Dados reais da tabela conteudo.</p><div class="filters"><select id="tipo"><option value="">Todos</option><option>FILME</option><option>SERIE</option></select><select id="genero"><option value="">Todos os gêneros</option>${genres.map(g=>`<option>${esc(g.nome_genero)}</option>`).join("")}</select><button onclick="filterCatalog()">Filtrar</button></div><div id="catalog" class="grid">${cards(items)}</div></div>`}
function cards(items){return items.length?items.map(c=>`<article class="card"><div class="poster">${esc(c.titulo)}</div><div class="actions"><span class="tag">${c.tipo}</span><span class="tag">${c.ano_lancamento}</span><span class="tag">${c.classificacao_indicativa}</span></div><p class="muted">${esc(c.sinopse||"")}</p><button onclick="details(${c.id_conteudo})">Ver detalhes</button></article>`).join(""):'<div class="empty">Nenhum conteúdo.</div>'}
async function filterCatalog(){const t=document.getElementById("tipo").value,g=document.getElementById("genero").value;document.getElementById("catalog").innerHTML=cards(await api(`/conteudos?tipo=${encodeURIComponent(t)}&genero=${encodeURIComponent(g)}`))}
async function details(id){const c=await api("/conteudos/"+id);const eps=(c.episodios||[]).map(e=>`<div class="episode"><b>T${e.numero_temporada}E${e.numero_episodio} — ${esc(e.titulo_episodio)}</b> <span class="muted">${e.duracao_min} min</span><span class="tag">Episódio</span></div>`).join("");app.innerHTML=`<div class="container"><button onclick="page('catalogo')">← Catálogo</button><section class="hero"><span class="tag">${c.tipo}</span><h1>${esc(c.titulo)}</h1><p>${esc(c.sinopse||"")}</p><p class="muted">Ano ${c.ano_lancamento} • ${c.classificacao_indicativa} • ${c.duracao_min?c.duracao_min+" min":""}</p></section><h2>Gêneros</h2><p>${esc(c.generos||"")}</p>${c.tipo==="SERIE"?`<h2>Episódios</h2><div class="card">${eps}</div>`:`<p class="muted">Modo demonstração: catálogo em somente leitura.</p>`}</div>`}

function chartBars(items,labelKey,valueKey,formatValue=v=>v){
  if(!items.length)return '<p class="muted">Sem dados para os filtros selecionados.</p>';
  const max=Math.max(...items.map(y=>Number(y[valueKey]||0)),1);
  return items.map(x=>{
    const width=Math.max(2,Number(x[valueKey]||0)/max*100);
    return '<div class="bar-row"><div class="bar-label">'+esc(x[labelKey])+'</div><div class="bar-track"><div class="bar-fill" style="width:'+width+'%"></div></div><div class="bar-value">'+esc(formatValue(x[valueKey]))+'</div></div>';
  }).join('');
}
async function analytics(){
  app.innerHTML='<div class="container"><h1>Analytics</h1><p class="muted">Indicadores calculados a partir do histórico de visualizações e das assinaturas ativas.</p>'+
  '<div class="filters analytics-filters"><select id="an-tipo"><option value="">Todos os tipos</option><option value="FILME">Filmes</option><option value="SERIE">Séries</option></select>'+
  '<select id="an-genero"><option value="">Todos os gêneros</option></select>'+
  '<label>De <input id="an-inicio" type="date"></label><label>Até <input id="an-fim" type="date"></label>'+
  '<button class="primary" onclick="loadAnalytics()">Aplicar filtros</button><button onclick="clearAnalytics()">Limpar</button></div>'+
  '<div id="an-status" class="muted"></div><div id="an-kpis" class="grid analytics-kpis"></div>'+
  '<div class="grid analytics-charts"><section class="card"><h2>Visualizações por mês</h2><p class="muted">Quantidade de registros no histórico.</p><div id="an-tempo"></div></section>'+
  '<section class="card"><h2>Visualizações por gênero</h2><p class="muted">Um registro pode contar em mais de um gênero.</p><div id="an-generos"></div></section></div>'+
  '<p class="analytics-note">A receita mensal é uma estimativa: soma dos preços dos planos associados a assinaturas com status ATIVA. Os dados são demonstrativos, não representam faturamento real.</p></div>';
  const genres=await api('/generos');
  document.getElementById('an-genero').innerHTML='<option value="">Todos os gêneros</option>'+genres.map(g=>'<option value="'+esc(g.nome_genero)+'">'+esc(g.nome_genero)+'</option>').join('');
  await loadAnalytics();
}
function analyticsParams(){
  const p=new URLSearchParams();
  const fields={tipo:'an-tipo',genero:'an-genero',data_inicio:'an-inicio',data_fim:'an-fim'};
  for(const [key,id] of Object.entries(fields)){const value=document.getElementById(id)?.value;if(value)p.set(key,value)}
  return p.toString()?('?'+p.toString()):'';
}
async function loadAnalytics(){
  const params=analyticsParams();
  const status=document.getElementById('an-status');
  status.textContent='Atualizando indicadores...';
  try{
    const [k,t,g]=await Promise.all([api('/analytics/resumo'+params),api('/analytics/visualizacoes'+params),api('/analytics/generos'+params)]);
    document.getElementById('an-kpis').innerHTML=[
      ['Visualizações',Number(k.total_visualizacoes||0).toLocaleString('pt-BR')],
      ['Horas assistidas',Number(k.horas_assistidas||0).toLocaleString('pt-BR')+' h'],
      ['Taxa de conclusão',Number(k.taxa_conclusao||0).toLocaleString('pt-BR')+'%'],
      ['Conteúdos assistidos',Number(k.conteudos_assistidos||0).toLocaleString('pt-BR')],
      ['Receita mensal estimada',money(k.receita_mensal_estimada)]
    ].map(([label,value])=>'<div class="card"><div class="muted">'+label+'</div><div class="metric">'+value+'</div></div>').join('');
    document.getElementById('an-tempo').innerHTML=chartBars(t,'periodo','visualizacoes',v=>Number(v).toLocaleString('pt-BR'));
    document.getElementById('an-generos').innerHTML=chartBars(g,'genero','visualizacoes',v=>Number(v).toLocaleString('pt-BR'));
    status.textContent='Dados atualizados • '+t.length+' período(s) encontrados';
  }catch(e){status.textContent='Não foi possível carregar as análises: '+e.message}
}
function clearAnalytics(){
  ['an-tipo','an-genero','an-inicio','an-fim'].forEach(id=>{const el=document.getElementById(id);if(el)el.value=''});
  loadAnalytics();
}

async function historico(){const h=await api("/historico");app.innerHTML=`<div class="container"><h1>Histórico</h1><p class="muted">JOIN entre usuário, perfil, conteúdo e episódio.</p><div class="table-wrap"><table><thead><tr><th>Usuário</th><th>Perfil</th><th>Conteúdo</th><th>Episódio</th><th>Data</th><th>Tempo</th><th>Status</th></tr></thead><tbody>${h.map(x=>`<tr><td>${esc(x.usuario)}</td><td>${esc(x.nome_perfil)}</td><td>${esc(x.titulo)}</td><td>${x.titulo_episodio?`T${x.numero_temporada}E${x.numero_episodio} - ${esc(x.titulo_episodio)}`:"Filme"}</td><td>${esc(x.data_hora_inicio)}</td><td>${x.tempo_assistido_min} min</td><td>${x.concluido?"✓ concluído":"Em andamento"}</td></tr>`).join("")}</tbody></table></div></div>`}
async function admin(){const [u,a,r,p]=await Promise.all([api("/usuarios"),api("/assinaturas"),api("/receita"),api("/planos")]);app.innerHTML=`<div class="container"><h1>Painel administrativo</h1><div class="grid"><div class="card"><div class="muted">Usuários</div><div class="metric">${u.length}</div></div><div class="card"><div class="muted">Assinaturas</div><div class="metric">${a.length}</div></div><div class="card"><div class="muted">Receita ativa</div><div class="metric">${money(r.reduce((s,x)=>s+Number(x.receita_mensal||0),0))}</div></div></div><h2>Planos</h2><div class="grid">${p.map(x=>`<div class="card"><b>${esc(x.nome_plano)}</b><div class="metric">${money(x.preco_mensal)}</div><p class="muted">${x.qualidade_maxima} • ${x.telas_simultaneas} tela(s)<br>${x.permite_download?"✓ Download":"✗ Download"}</p></div>`).join("")}</div><h2>Assinaturas</h2><div class="table-wrap"><table><thead><tr><th>Usuário</th><th>Plano</th><th>Preço</th><th>Status</th><th>Pagamento</th></tr></thead><tbody>${a.map(x=>`<tr><td>${esc(x.usuario)}</td><td>${esc(x.nome_plano)}</td><td>${money(x.preco_mensal)}</td><td>${x.status}</td><td>${x.forma_pagamento}</td></tr>`).join("")}</tbody></table></div><h2>Usuários</h2><p class="muted">Dados fictícios para demonstração. A criação de usuários está desativada nesta versão pública.</p><div class="table-wrap" style="margin-top:15px"><table><thead><tr><th>ID</th><th>Nome</th><th>País</th></tr></thead><tbody>${u.map(x=>`<tr><td>${x.id_usuario}</td><td>${esc(x.nome)}</td><td>${esc(x.pais)}</td></tr>`).join("")}</tbody></table></div></div>`}
function page(p){({home,catalogo,historico,admin,analytics}[p]||home)()}
document.querySelectorAll("nav button").forEach(b=>b.onclick=()=>page(b.dataset.page));
(async()=>{try{await api("/health");statusEl.textContent="● banco conectado";statusEl.style.color="#86efac"}catch(e){statusEl.textContent="● banco offline";statusEl.style.color="#f87171"}home()})();
