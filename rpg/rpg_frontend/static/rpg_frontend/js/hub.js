const audioContext=typeof AudioContext!=="undefined"?new AudioContext():null;
const soundCache={};
let pendingSound=null;

function resumeAudioContext(){
if(!audioContext || audioContext.state!=="suspended") return;
audioContext.resume().then(function(){
if(pendingSound){
const s=pendingSound;
pendingSound=null;
playSound(s);
}
});
}
document.addEventListener("click",resumeAudioContext,{capture:true});
document.addEventListener("keydown",resumeAudioContext,{capture:true});

function playSound(soundId){
if(!audioContext) return;
if(audioContext.state==="suspended"){
pendingSound=soundId;
return;
}
if(soundCache[soundId]){
const source=audioContext.createBufferSource();
source.buffer=soundCache[soundId];
source.connect(audioContext.destination);
source.start(0);
return;
}
fetch("/rpg/sounds/"+soundId+"/",{credentials:"same-origin"})
.then(function(response){
if(!response.ok) return;
return response.arrayBuffer();
})
.then(function(buffer){
if(!buffer) return;
audioContext.decodeAudioData(buffer,function(decoded){
soundCache[soundId]=decoded;
const source=audioContext.createBufferSource();
source.buffer=decoded;
source.connect(audioContext.destination);
source.start(0);
});
})
.catch(function(){});
}

const historyElement=document.getElementById("history");
const historyAnnouncements=document.getElementById("historyAnnouncements");
const actionsMenu=document.getElementById("actionsMenu");
const connectionStatus=document.getElementById("connectionStatus");
const chatArea=document.getElementById("chatArea");
const chatBox=document.getElementById("chatBox");

let historyValue="";
let inputMode=null;
let activeMessages={};
let activeSocket=null;
let activeMode=null;

function addHistory(message){
if(!message) return;
const previousValue=historyValue;
const separator=previousValue?"\n":"";
const isReadingHistory=document.activeElement===historyElement;
const wasAtEnd=historyElement.scrollTop+historyElement.clientHeight>=historyElement.scrollHeight-1;
const selectionStart=historyElement.selectionStart;
const selectionEnd=historyElement.selectionEnd;
const scrollTop=historyElement.scrollTop;
historyValue=previousValue+separator+message;
historyElement.value=historyValue;
if(isReadingHistory){
historyElement.selectionStart=selectionStart;
historyElement.selectionEnd=selectionEnd;
historyElement.scrollTop=scrollTop;
}else{
historyElement.selectionStart=historyElement.value.length;
historyElement.selectionEnd=historyElement.value.length;
}
if(wasAtEnd && !isReadingHistory){
historyElement.scrollTop=historyElement.scrollHeight;
}
historyAnnouncements.textContent="";
window.setTimeout(function(){
historyAnnouncements.textContent=message;
},10);
}

function restoreHistoryValue(){
if(historyElement.value===historyValue) return;
const selectionStart=Math.min(historyElement.selectionStart,historyValue.length);
const selectionEnd=Math.min(historyElement.selectionEnd,historyValue.length);
historyElement.value=historyValue;
historyElement.selectionStart=selectionStart;
historyElement.selectionEnd=selectionEnd;
}

function renderActions(actions){
actionsMenu.replaceChildren();
actions.forEach(function(action,index){
if(!action.type || !action.label) return;
const button=document.createElement("button");
button.type="button";
button.textContent=action.label;
button.tabIndex=index===0?0:-1;
button.addEventListener("click",function(){ handleAction(action); });
button.addEventListener("keydown",handleActionKeydown);
actionsMenu.appendChild(button);
});
}

function getActionButtons(){
return Array.from(actionsMenu.querySelectorAll("button"));
}

function focusActionButton(index){
const buttons=getActionButtons();
if(!buttons.length) return;
const targetIndex=(index+buttons.length)%buttons.length;
buttons.forEach(function(button,buttonIndex){
button.tabIndex=buttonIndex===targetIndex?0:-1;
});
buttons[targetIndex].focus();
}

function handleActionKeydown(event){
const buttons=getActionButtons();
const currentIndex=buttons.indexOf(event.currentTarget);
if(event.key==="ArrowRight"||event.key==="ArrowDown"){
event.preventDefault();
focusActionButton(currentIndex+1);
return;
}
if(event.key==="ArrowLeft"||event.key==="ArrowUp"){
event.preventDefault();
focusActionButton(currentIndex-1);
return;
}
if(event.key==="Home"){ event.preventDefault(); focusActionButton(0); return; }
if(event.key==="End"){ event.preventDefault(); focusActionButton(buttons.length-1); }
}

function handleAction(action){
if(action.type==="hub.exit"){
try{
if(activeSocket && activeSocket.readyState===WebSocket.OPEN){
activeSocket.send(JSON.stringify({type:"hub.exit"}));
}
}catch(e){}
window.location.href=action.logout_url;
return;
}
if(action.type==="table.leave"){
connectHub();
return;
}
if(action.type==="table.join.select"){
if(activeSocket && activeSocket.readyState===WebSocket.OPEN){
activeSocket.send(JSON.stringify({type:"table.join",table_id:action.table_id}));
}
return;
}
if(activeSocket && activeSocket.readyState===WebSocket.OPEN){
const msg={};
for(const k in action){ if(k!=="label") msg[k]=action[k]; }
activeSocket.send(JSON.stringify(msg));
}
}

function handleMessage(event){
let data;
try{ data=JSON.parse(event.data); }
catch(e){ addHistory(activeMessages.client_invalid_message||""); return; }
if(data.sound) playSound(data.sound);
if(data.type==="hub.history"||data.type==="message.private"){
addHistory(data.message);
return;
}
if(data.type==="hub.input"){
addHistory(data.prompt);
inputMode={action:data.action};
chatBox.focus();
return;
}
if(data.type==="player.connected"||data.type==="player.disconnected"){
return;
}
if(activeMode==="hub") handleHubPayload(data);
else handleTablePayload(data);
}

function handleHubPayload(data){
if(data.type==="hub.connected"){
activeMessages=data.messages||{};
connectionStatus.textContent=data.message;
addHistory(data.message);
renderActions(data.actions||[]);
return;
}
if(data.type==="hub.menu"){
if(data.message) addHistory(data.message);
renderActions(data.actions||[]);
return;
}
if(data.type==="hub.table_list"){
if(!data.tables||!data.tables.length){
addHistory(data.empty_message||"");
return;
}
const listActions=data.tables.map(function(t){
return {type:"table.join.select",table_id:t.id,label:t.label};
});
listActions.push({type:"hub.main",label:data.cancel_label});
renderActions(listActions);
return;
}
if(data.type==="table.created"||data.type==="table.joined"){
addHistory(data.message);
connectTable(data.table_id);
return;
}
if(data.type==="player.connected"||data.type==="player.disconnected"){
return;
}
if(data.type==="error") addHistory(data.message);
}

function handleTablePayload(data){
if(data.type==="table.connected"){
activeMessages=data.messages||{};
connectionStatus.textContent=data.message;
addHistory(data.message);
renderActions(data.actions||[]);
return;
}
if(data.type==="chat.message"||data.type==="player.left"){
addHistory(data.message);
return;
}
if(data.type==="error") addHistory(data.message);
}

function buildSocket(url){
const protocol=window.location.protocol==="https:"?"wss":"ws";
return new WebSocket(protocol+"://"+window.location.host+url);
}

function connectHub(){
if(activeSocket){
activeSocket.onclose=null;
activeSocket.close();
activeSocket=null;
}
inputMode=null;
activeMode="hub";
const socket=buildSocket("/ws/rpg/hub/");
activeSocket=socket;
socket.addEventListener("message",handleMessage);
socket.addEventListener("close",function(){
if(activeSocket!==socket) return;
addHistory(activeMessages.connection_closed||"");
});
history.pushState(null,"","/rpg/");
}

function connectTable(tableId){
if(activeSocket){
activeSocket.onclose=null;
activeSocket.close();
activeSocket=null;
}
inputMode=null;
activeMode="table";
const socket=buildSocket("/ws/rpg/table/"+tableId+"/");
activeSocket=socket;
socket.addEventListener("message",handleMessage);
socket.addEventListener("close",function(){
if(activeSocket!==socket) return;
addHistory(activeMessages.connection_closed||"");
connectHub();
});
history.pushState(null,"","/rpg/table/"+tableId+"/");
}

historyElement.addEventListener("beforeinput",function(e){ e.preventDefault(); });
historyElement.addEventListener("paste",function(e){ e.preventDefault(); });
historyElement.addEventListener("cut",function(e){ e.preventDefault(); });
historyElement.addEventListener("drop",function(e){ e.preventDefault(); });
historyElement.addEventListener("input",restoreHistoryValue);

chatBox.addEventListener("keydown",function(event){
if(event.key==="Escape" && inputMode){
inputMode=null;
chatBox.value="";
}
});

chatArea.addEventListener("submit",function(event){
event.preventDefault();
const message=chatBox.value.trim();
chatBox.value="";
if(!message) return;
if(!activeSocket || activeSocket.readyState!==WebSocket.OPEN) return;
if(inputMode){
activeSocket.send(JSON.stringify({type:inputMode.action,value:message}));
inputMode=null;
return;
}
const type=activeMode==="table"?"chat.send":"hub.chat";
activeSocket.send(JSON.stringify({type:type,message:message}));
});

(function init(){
const pathMatch=window.location.pathname.match(/^\/rpg\/table\/(\d+)\//);
if(pathMatch){
connectTable(parseInt(pathMatch[1]));
}else{
const hubPayloadElement=document.getElementById("hubPayload");
connectHub();
if(hubPayloadElement){
handleHubPayload(JSON.parse(hubPayloadElement.textContent));
}
}
})();
