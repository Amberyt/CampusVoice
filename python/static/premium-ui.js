(() => {
  'use strict';
  const path = location.pathname;
  const isStudent = path === '/student';
  const isTeacher = path === '/teacher';
  const isCollegeAdmin = path === '/college/portal';
  const isCollegeRegister = path === '/college';
  const isAssistant = !isStudent && !isTeacher && !isCollegeAdmin && !isCollegeRegister;
  const body = document.body;
  body.classList.add(isStudent ? 'cv-student' : isTeacher ? 'cv-teacher' : isCollegeAdmin ? 'cv-college-admin' : isCollegeRegister ? 'cv-college-register' : 'cv-assistant');

  const icons = {
    home: '<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z"/>',
    mic: '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10a7 7 0 0 0 14 0M12 17v5m-4 0h8"/>',
    book: '<path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v18H6.5A2.5 2.5 0 0 0 4 22Z"/><path d="M4 4v18M8 6h8m-8 4h8"/>',
    calendar: '<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M16 2v4M8 2v4M3 9h18M8 13h2m4 0h2m-8 4h2"/>',
    bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9m-8 12h4"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2m6-10a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm10 10v-2a4 4 0 0 0-3-3.87m-1-11.86a4 4 0 0 1 0 7.75"/>',
    building: '<path d="M3 21h18M5 21V6l7-3 7 3v15M9 9h1m4 0h1m-6 4h1m4 0h1m-4 8v-4h4v4"/>',
    upload: '<path d="M12 16V4m-5 5 5-5 5 5M4 16v4h16v-4"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.6a8 8 0 0 1-1.5.9l-.3 1.8h-2.8l-.3-1.8a8 8 0 0 1-1.5-.9l-1.7.6-1.4-2.4 1.4-1.1a8 8 0 0 1 0-1.8l-1.4-1.1 1.4-2.4 1.7.6a8 8 0 0 1 1.5-.9l.3-1.8h2.8l.3 1.8a8 8 0 0 1 1.5.9l1.7-.6 1.4 2.4-1.4 1.1a8 8 0 0 1 0 1.8Z"/>',
    logout: '<path d="M10 17l5-5-5-5m5 5H3m10-9h5a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-5"/>',
    chart: '<path d="M3 3v18h18M8 15l4-4 3 3 6-7"/>'
  };
  const svg = name => `<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${icons[name] || icons.home}</svg>`;

  function createSidebar(items, subtitle) {
    if (document.querySelector('.cv-sidebar')) return;
    const aside = document.createElement('aside');
    aside.className = 'cv-sidebar';
    aside.innerHTML = `
      <a class="cv-side-brand" href="/" aria-label="CampusVoice home"><span class="cv-brand-mark">C</span><span class="cv-brand-words"><b>CampusVoice</b><small>${subtitle}</small></span></a>
      <div class="cv-side-label">WORKSPACE</div>
      <nav class="cv-side-nav" aria-label="Portal navigation">${items.map((item,i)=>`<a href="${item.href}" class="${i===0?'active':''}" ${item.action?`data-action="${item.action}"`:''}>${svg(item.icon)}<span>${item.label}</span></a>`).join('')}</nav>
      <div class="cv-side-bottom"><div class="cv-side-campus"><span class="cv-side-campus-dot"></span><span><b>Campus connected</b><small>Academic workspace</small></span></div><button class="cv-side-theme" type="button">Appearance <span class="cv-side-theme-state">Light</span></button></div>`;
    document.body.prepend(aside);
    aside.querySelectorAll('a[data-action]').forEach(a => a.addEventListener('click', e => {
      const action = a.dataset.action;
      const target = document.querySelector(`.tabs button[data-tab="${action}"]`);
      if (target) { e.preventDefault(); target.click(); }
    }));
    aside.querySelector('.cv-side-theme').addEventListener('click', () => {
      const toggle = document.querySelector('.cv-theme-toggle');
      if (toggle) toggle.click();
      updateThemeLabel();
    });
    updateThemeLabel();
    window.addEventListener('storage', updateThemeLabel);
    const observer = new MutationObserver(updateThemeLabel);
    observer.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
  }
  function updateThemeLabel(){
    const label=document.querySelector('.cv-side-theme-state');
    if(label) label.textContent=document.documentElement.getAttribute('data-theme')==='dark'?'Dark':'Light';
  }
  function hero(title, description, eyebrow) {
    const node = document.createElement('section');
    node.className = 'cv-page-hero';
    node.innerHTML = `<div><span class="cv-hero-eyebrow">${eyebrow}</span><h2>${title}</h2><p>${description}</p></div><div class="cv-hero-seal"><span>✦</span><small>LEARN · CONNECT<br>THRIVE</small></div>`;
    return node;
  }

  if (isStudent) {
    createSidebar([
      {label:'Overview',href:'#cv-student-overview',icon:'home'},
      {label:'My courses',href:'#cv-courses',icon:'book'},
      {label:'Timetable',href:'#cv-timetable',icon:'calendar'},
      {label:'Notices',href:'#cv-notices',icon:'bell'},
      {label:'Campus events',href:'#cv-events',icon:'calendar'},
      {label:'Faculty',href:'#cv-faculty',icon:'users'},
      {label:'Rooms & facilities',href:'#cv-rooms',icon:'building'},
      {label:'AURA assistant',href:'/',icon:'mic'}
    ], 'STUDENT PORTAL');
    const wrap=document.querySelector('.wrap');
    if(wrap){wrap.classList.add('cv-dashboard-wrap'); const top=wrap.querySelector('.top'); if(top){top.insertAdjacentElement('afterend',hero('Your campus, at a glance.','A clear view of your courses, timetable and everything happening around campus.','STUDENT EXPERIENCE'));}
      const dashboard=wrap.querySelector('#dashboard')||wrap;
      const directSections=[...dashboard.querySelectorAll(':scope > section')];
      directSections.forEach(section=>{
        const h=section.querySelector('h3'); if(!h)return; const t=h.textContent.toLowerCase();
        if(t.includes('course'))section.id='cv-courses'; else if(t.includes('timetable'))section.id='cv-timetable';
      });
      const panels=[...dashboard.querySelectorAll(':scope > .two')];
      panels.forEach(group=>group.querySelectorAll(':scope > section').forEach(section=>{const t=section.querySelector('h3')?.textContent.toLowerCase()||''; if(t.includes('notice'))section.id='cv-notices'; else if(t.includes('event'))section.id='cv-events'; else if(t.includes('faculty'))section.id='cv-faculty'; else if(t.includes('room'))section.id='cv-rooms';}));
      const stats=wrap.querySelector('.stats'); if(stats)stats.classList.add('cv-stats');
      const heroEl=wrap.querySelector('.cv-page-hero'); if(heroEl)heroEl.id='cv-student-overview';
    }
  } else if (isTeacher || isCollegeAdmin) {
    const isTeacherPage=isTeacher;
    createSidebar(isTeacherPage?[
      {label:'Overview',href:'#cv-ops-overview',icon:'home'},
      {label:'Upload studio',href:'#sec-upload',icon:'upload',action:'upload'},
      {label:'Notice operations',href:'#sec-notices',icon:'bell',action:'notices'},
      {label:'Open AURA assistant',href:'/',icon:'mic'}
    ]:[
      {label:'Overview',href:'#cv-ops-overview',icon:'home'},
      {label:'Campus data',href:'#sec-upload',icon:'upload',action:'upload'},
      {label:'Notice board',href:'#sec-notices',icon:'bell',action:'notices'},
      {label:'Student portal',href:'/student',icon:'book'},
      {label:'Faculty portal',href:'/teacher',icon:'users'}
    ],isTeacherPage?'FACULTY WORKSPACE':'INSTITUTION ADMIN');
    const app=document.querySelector('.app');
    if(app){app.classList.add('cv-dashboard-app');const header=app.querySelector('header');if(header){header.insertAdjacentElement('afterend',hero(isTeacherPage?'Good work starts with good information.':'Your institution. One connected campus.',isTeacherPage?'Manage campus information, publish updates and keep student answers accurate.':'Manage campus data, invite your community and keep every campus service in sync.',isTeacherPage?'FACULTY WORKSPACE':'COLLEGE ADMINISTRATION'));}
      const h=app.querySelector('.cv-page-hero');if(h)h.id='cv-ops-overview';
      const stats=app.querySelector('#stats'); if(stats)stats.classList.add('cv-stats');
      const tabs=app.querySelector('.tabs'); if(tabs)tabs.classList.add('cv-tabs');
      app.querySelectorAll('.section').forEach(s=>s.classList.add('cv-work-section'));
    }
  } else if (isCollegeRegister) {
    const wrap=document.querySelector('.wrap'); if(wrap)wrap.classList.add('cv-onboarding-wrap');
  } else if (isAssistant) {
    const app=document.querySelector('.app');
    if(app){
      createSidebar([
        {label:'AURA assistant',href:'#assistant',icon:'mic'},
        {label:'Student dashboard',href:'/student',icon:'book'},
        {label:'Faculty workspace',href:'/teacher',icon:'users'},
        {label:'College portal',href:'/college',icon:'building'}
      ],'AI CAMPUS ASSISTANT');
      app.classList.add('cv-assistant-app');
      const main=app.querySelector('main'); if(main)main.id='assistant';
      const intro=app.querySelector('.assistant-intro');
      if(intro){const eyebrow=intro.querySelector('span');if(eyebrow)eyebrow.textContent='YOUR ALWAYS-ON CAMPUS COMPANION';}
      const stage=app.querySelector('.stage'); if(stage){const badge=document.createElement('div');badge.className='cv-ai-badge';badge.innerHTML='<span class="cv-ai-pulse"></span> AURA INTELLIGENCE · ONLINE';stage.insertBefore(badge,stage.querySelector('.assistant-intro'));}
      const consoleHead=app.querySelector('.console-head'); if(consoleHead){const title=consoleHead.querySelector('p');if(title)title.innerHTML='<span class="cv-console-live"></span> Conversation';}
      const gate=document.querySelector('#gate .gate-card');if(gate)gate.classList.add('cv-login-card');
    }
  }

  // Make the theme toggle and top actions consistent while preserving all existing IDs/listeners.
  document.querySelectorAll('.cv-theme-toggle').forEach(button=>button.setAttribute('title','Switch appearance'));
})();
