import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Bot, Upload, ShieldCheck, Sparkles, CreditCard, Lock, FileText} from 'lucide-react';
import './style.css';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const CONSENT_TEXT = 'This meeting will be recorded by ASYNCPROOF AI Assistant.';

function App(){
  const [token,setToken]=useState(localStorage.getItem('token')||'');
  const [mode,setMode]=useState('login');
  const [form,setForm]=useState({name:'',email:'',password:''});
  const [meeting,setMeeting]=useState({title:'Marketing AI Meeting',meeting_link:'',consent_confirmed:false});
  const [meetings,setMeetings]=useState([]);
  const [report,setReport]=useState(null);
  const [plans,setPlans]=useState({});
  const [message,setMessage]=useState('');
  const [legal,setLegal]=useState(null);
  const authHeaders = token ? {Authorization:`Bearer ${token}`} : {};

  const [feedbackOpen,setFeedbackOpen]=useState(false);
  const [feedbackForm,setFeedbackForm]=useState({rating:5,category:'general',message:'',email:''});


  useEffect(()=>{ fetch(API+'/api/plans').then(r=>r.json()).then(d=>setPlans(d.plans||{})).catch(()=>{}); if(token) loadMeetings(token); },[]);

  async function auth(){
    const url = mode==='login' ? '/api/auth/login' : '/api/auth/register';
    const body = mode==='login' ? {email:form.email,password:form.password} : form;
    const res = await fetch(API+url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data = await res.json();
    if(!res.ok){setMessage(data.detail||'Auth failed'); return;}
    localStorage.setItem('token',data.token); setToken(data.token); setMessage('Login success'); loadMeetings(data.token);
  }

  async function loadMeetings(t=token){
    const res = await fetch(API+'/api/meetings',{headers:{Authorization:`Bearer ${t}`}});
    const data = await res.json(); setMeetings(Array.isArray(data)?data:[]);
  }

  async function createMeeting(){
    if(!meeting.consent_confirmed){ setMessage('Consent required: '+CONSENT_TEXT); return; }
    const res = await fetch(API+'/api/meetings',{method:'POST',headers:{'Content-Type':'application/json',...authHeaders},body:JSON.stringify(meeting)});
    const data = await res.json(); setMessage(data.detail||data.message||JSON.stringify(data)); loadMeetings();
  }

  async function startBot(id){
    const res = await fetch(API+`/api/meetings/${id}/start-bot`,{method:'POST',headers:authHeaders});
    const data = await res.json(); setMessage(data.message||JSON.stringify(data)); loadMeetings();
  }

  async function uploadRecording(id, file){
    if(!file) return;
    const fd = new FormData(); fd.append('file',file);
    const res = await fetch(API+`/api/meetings/${id}/recording`,{method:'POST',headers:authHeaders,body:fd});
    const data = await res.json(); setMessage(data.detail||data.message||JSON.stringify(data)); getReport(id);
  }

  async function getReport(id){
    const res = await fetch(API+`/api/meetings/${id}/report`,{headers:authHeaders});
    const data = await res.json(); setReport(data.report);
  }

  function openFeedback(prefill){
    setFeedbackForm(prev=>({
      ...prev,
      rating: prefill?.rating ?? prev.rating,
      category: prefill?.category ?? prev.category,
      message: prefill?.message ?? ''
    }));
    setFeedbackOpen(true);
  }

  async function submitFeedback(){
    const fd = new FormData();
    fd.append('rating', String(feedbackForm.rating));
    fd.append('category', feedbackForm.category);
    fd.append('message', feedbackForm.message);
    fd.append('email', feedbackForm.email || '');
    const res = await fetch(API+'/api/feedback',{method:'POST',headers:authHeaders,body:fd});
    const data = await res.json();
    if(!res.ok){ setMessage(data.detail||'Feedback failed'); return; }
    setFeedbackOpen(false);
    setMessage('Feedback submitted');
  }

  async function checkout(plan, provider='razorpay'){

    const res = await fetch(API+'/api/payments/checkout',{method:'POST',headers:{'Content-Type':'application/json',...authHeaders},body:JSON.stringify({plan,provider})});
    const data = await res.json();
    if(data.checkout_url){ window.open(data.checkout_url,'_blank'); setMessage('Payment page opened for '+plan); }
    else setMessage(data.message||data.detail||'Payment gateway not configured yet');
  }

  async function loadLegal(type){
    const res = await fetch(API+`/api/legal/${type}`); const data = await res.json(); setLegal(data);
  }

  if(!token){
    return <div className="page center">
      <div className="card auth">
        <h1><Sparkles/> ASYNCPROOF</h1>
        <p>AI meeting bot with recording consent, summaries, action items, translation, analytics, and premium playback.</p>
        {mode==='register' && <input value={form.name} onChange={e=>setForm({...form,name:e.target.value})} placeholder="Name"/>}
        <input value={form.email} onChange={e=>setForm({...form,email:e.target.value})} placeholder="Email"/>
        <input value={form.password} onChange={e=>setForm({...form,password:e.target.value})} placeholder="Password" type="password"/>
        <button onClick={auth}>{mode==='login'?'Login':'Register'}</button>
        <button className="ghost" onClick={()=>setMode(mode==='login'?'register':'login')}>{mode==='login'?'Create account':'Have account? Login'}</button>
        <p className="msg">{message}</p>
      </div>
    </div>
  }

  return <div className="page">
    <header>
      <h1><Bot/> ASYNCPROOF AI Bot</h1>
      <button onClick={()=>{localStorage.removeItem('token');setToken('')}}>Logout</button>
    </header>

    <section className="grid">
      <div className="card">
        <h2>Start Meeting Bot</h2>
        <p className="safe"><ShieldCheck/> {CONSENT_TEXT}</p>
        <input value={meeting.title} onChange={e=>setMeeting({...meeting,title:e.target.value})} placeholder="Meeting title"/>
        <input value={meeting.meeting_link} onChange={e=>setMeeting({...meeting,meeting_link:e.target.value})} placeholder="Google Meet link"/>
        <label className="check"><input type="checkbox" checked={meeting.consent_confirmed} onChange={e=>setMeeting({...meeting,consent_confirmed:e.target.checked})}/> I confirm recording consent and participant notice.</label>
        <button onClick={createMeeting}>Create Meeting</button>
      </div>

      <div className="card">
        <h2>Meetings</h2>
        <button className="ghost" onClick={()=>loadMeetings()}>Refresh</button>
        {meetings.map(m=><div className="meeting" key={m.id}>
          <b>{m.title}</b><span>{m.status}</span>
          <button onClick={()=>startBot(m.id)}>Start Bot</button>
          <label className="upload"><Upload/> Upload Recording<input type="file" accept="audio/*,video/*" onChange={e=>uploadRecording(m.id,e.target.files[0])}/></label>
          <button className="ghost" onClick={()=>getReport(m.id)}>View Report</button>
        </div>)}
      </div>
    </section>

    <section className="card pricing">
      <h2><CreditCard/> Plans & Monetization</h2>
      <div className="plans">
        {Object.entries(plans).map(([key,p])=><div className="plan" key={key}>
          <h3>{p.name}</h3>
          <p className="price">{key==='free'?'₹0':key==='premium'?'₹199–₹499/month':'₹999+/month'}</p>
          <ul>{(p.features||[]).map(f=><li key={f}>{f}</li>)}</ul>
          {key!=='free' && <button onClick={()=>checkout(key,'razorpay')}>Pay with Razorpay</button>}
          {key!=='free' && <button className="ghost" onClick={()=>checkout(key,'stripe')}>Stripe</button>}
        </div>)}
      </div>
    </section>

    <section className="card report">
      <h2>AI Report</h2>
      {report ? <>
        <button className="ghost" onClick={()=>openFeedback({category:'summary_issue',message:'Please fix the incorrect/poor summary:'})}>Report Problem</button>
        <h3>Summary</h3><p>{report.summary}</p>
        <h3>Action Items</h3><pre>{report.action_items}</pre>
        <h3>Deadlines</h3><pre>{report.deadlines}</pre>
        <h3>Decisions</h3><pre>{report.decisions}</pre>
        <h3>Translation</h3><pre>{JSON.stringify(report.translation,null,2)}</pre>
        <h3>Productivity Score: {report.productivity_score} | Waste Score: {report.waste_score}</h3>
      </> : <p>No report yet. Upload a recording to generate one.</p>}
    </section>

    {feedbackOpen && (
      <div className="modal">
        <div className="modal-card">
          <h2>Help & Feedback</h2>
          <div className="row">
            <label>Rating</label>
            <select value={feedbackForm.rating} onChange={e=>setFeedbackForm({...feedbackForm,rating: Number(e.target.value)})}>
              {[1,2,3,4,5].map(n=><option key={n} value={n}>{n}</option>)}
            </select>
          </div>
          <div className="row">
            <label>Category</label>
            <select value={feedbackForm.category} onChange={e=>setFeedbackForm({...feedbackForm,category:e.target.value})}>
              {['general','bug','feature_request','payment_issue','meeting_issue','ai_issue','recording_problem','login_issue','storage_issue','transcription_issue','summary_issue','translation_issue'].map(c=><option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <textarea value={feedbackForm.message} onChange={e=>setFeedbackForm({...feedbackForm,message:e.target.value})} placeholder="Tell us what went wrong / what to improve" />
          <div className="actions">
            <button onClick={submitFeedback}>Submit</button>
            <button className="ghost" onClick={()=>setFeedbackOpen(false)}>Cancel</button>
          </div>
        </div>
      </div>
    )}


    <section className="card legal">
      <h2><Lock/> Legal & Trust</h2>
      <button className="ghost" onClick={()=>loadLegal('privacy')}><FileText/> Privacy Policy</button>
      <button className="ghost" onClick={()=>loadLegal('terms')}><FileText/> Terms</button>
      {legal && <pre>{legal.content}</pre>}
    </section>

    <p className="msg">{message}</p>
  </div>
}

createRoot(document.getElementById('root')).render(<App/>);
