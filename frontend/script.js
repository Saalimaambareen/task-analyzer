const apiBase = "/api/tasks";

let taskList = [];

function el(q){return document.querySelector(q)}

function renderResults(results){
  const container = el("#results");
  container.innerHTML = "";
  results.forEach(r=>{
    const t = r.task;
    const score = r.score;
    const div = document.createElement("div");
    div.className = "result-card";
    const left = document.createElement("div");
    left.innerHTML = `<div><strong>${t.title}</strong> <span class="meta">(${t.estimated_hours}h · imp ${t.importance})</span></div>
      <div class="meta">${t.due_date ? 'Due: '+t.due_date : ''} ${t.dependencies && t.dependencies.length ? '· deps:'+t.dependencies.join(",") : ''}</div>`;
    const right = document.createElement("div");
    const scoreEl = document.createElement("div");
    scoreEl.className = "score";
    let cls="low";
    if(score>=70) cls="high";
    else if(score>=40) cls="med";
    scoreEl.classList.add(cls);
    scoreEl.innerText = score;
    right.appendChild(scoreEl);
    div.appendChild(left);
    div.appendChild(right);
    container.appendChild(div);
  })
}

function renderSuggestions(suggestions){
  const c = el("#suggestions");
  c.innerHTML = "";
  suggestions.forEach(s=>{
    const card = document.createElement("div");
    card.className = "result-card";
    const left = document.createElement("div");
    left.innerHTML = `<strong>${s.task.title}</strong><div class="meta">${s.explanation || (s.why && s.why.join(', ')) || ''}</div>`;
    const right = document.createElement("div");
    const scoreEl = document.createElement("div");
    scoreEl.className = "score";
    let cls="low";
    if(s.score>=70) cls="high";
    else if(s.score>=40) cls="med";
    scoreEl.classList.add(cls);
    scoreEl.innerText = s.score;
    right.appendChild(scoreEl);
    card.appendChild(left); card.appendChild(right);
    c.appendChild(card);
  })
}

document.getElementById("task-form").addEventListener("submit", (e)=>{
  e.preventDefault();
  const t = {
    title: el("#title").value.trim(),
    due_date: el("#due_date").value.trim() || null,
    estimated_hours: parseFloat(el("#estimated_hours").value) || 1.0,
    importance: parseInt(el("#importance").value) || 5,
    dependencies: el("#dependencies").value ? el("#dependencies").value.split(",").map(s=>s.trim()).filter(Boolean) : []
  };
  taskList.push(t);
  el("#title").value = el("#due_date").value = el("#estimated_hours").value = el("#importance").value = el("#dependencies").value = "";
  alert("Task added to local list. Click Analyze to evaluate.");
});

document.getElementById("analyze-btn").addEventListener("click", async ()=>{
  let tasks = [];
  const bulk = el("#bulk-json").value.trim();
  if(bulk){
    try{
      tasks = JSON.parse(bulk);
      if(!Array.isArray(tasks)) throw "Expecting JSON array";
    }catch(err){
      alert("Invalid JSON in bulk input. Please fix.");
      return;
    }
  } else {
    if(taskList.length === 0){
      alert("No tasks to analyze. Add tasks or paste JSON.");
      return;
    }
    tasks = taskList;
  }

  const strategy = el("#strategy").value;

  try{
    const res = await fetch(`${apiBase}/analyze/?strategy=${strategy}`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(tasks)
    });
    if(!res.ok){
      const err = await res.json();
      alert("Server error: " + JSON.stringify(err));
      return;
    }
    const data = await res.json();
    renderResults(data.results);

    const top3 = data.results.slice(0,3).map(r => ({task:r.task, score:r.score, explanation: r.breakdown.method || ''}));
    renderSuggestions(top3);
  }catch(e){
    console.error(e);
    alert("Network error. Ensure backend is running and accessible at " + apiBase);
  }
});
