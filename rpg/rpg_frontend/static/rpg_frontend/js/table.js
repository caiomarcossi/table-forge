const audioContext=typeof AudioContext!=="undefined"?new AudioContext():null;
const soundCache={};
function playSound(soundId){
if(!audioContext){
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
if(!response.ok){
return;
}
return response.arrayBuffer();
})
.then(function(buffer){
if(!buffer){
return;
}
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

const appElement=document.getElementById("app");
const tableId=appElement?appElement.getAttribute("data-table-id"):"";
const historyElement=document.getElementById("history");
const historyAnnouncements=document.getElementById("historyAnnouncements");
const actionsMenu=document.getElementById("actionsMenu");
const connectionStatus=document.getElementById("connectionStatus");
const chatArea=document.getElementById("chatArea");
const chatBox=document.getElementById("chatBox");
const socketProtocol=window.location.protocol==="https:"?"wss":"ws";
const socket=new WebSocket(socketProtocol+"://"+window.location.host+"/ws/rpg/table/"+tableId+"/");
let tableMessages={};
let historyValue="";

function addHistory(message){
if(!message){
return;
}
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
if(historyElement.value===historyValue){
return;
}
const selectionStart=Math.min(historyElement.selectionStart,historyValue.length);
const selectionEnd=Math.min(historyElement.selectionEnd,historyValue.length);
historyElement.value=historyValue;
historyElement.selectionStart=selectionStart;
historyElement.selectionEnd=selectionEnd;
}

function renderActions(actions){
actionsMenu.replaceChildren();
actions.forEach(function(action,index){
if(!action.type || !action.label){
return;
}
const button=document.createElement("button");
button.type="button";
button.textContent=action.label;
button.tabIndex=index===0?0:-1;
button.addEventListener("click",function(){
handleAction(action);
});
button.addEventListener("keydown",function(event){
handleActionKeydown(event);
});
actionsMenu.appendChild(button);
});
}

function getActionButtons(){
return Array.from(actionsMenu.querySelectorAll("button"));
}

function focusActionButton(index){
const buttons=getActionButtons();
if(!buttons.length){
return;
}
const targetIndex=(index+buttons.length)%buttons.length;
buttons.forEach(function(button,buttonIndex){
button.tabIndex=buttonIndex===targetIndex?0:-1;
});
buttons[targetIndex].focus();
}

function handleActionKeydown(event){
const buttons=getActionButtons();
const currentIndex=buttons.indexOf(event.currentTarget);
if(event.key==="ArrowRight" || event.key==="ArrowDown"){
event.preventDefault();
focusActionButton(currentIndex+1);
return;
}
if(event.key==="ArrowLeft" || event.key==="ArrowUp"){
event.preventDefault();
focusActionButton(currentIndex-1);
return;
}
if(event.key==="Home"){
event.preventDefault();
focusActionButton(0);
return;
}
if(event.key==="End"){
event.preventDefault();
focusActionButton(buttons.length-1);
}
}

function handleAction(action){
if(action.type==="table.leave"){
try{
if(socket.readyState===WebSocket.OPEN){
socket.send(JSON.stringify({"type":action.type}));
}
}catch(error){
}
window.location.href=action.hub_url;
return;
}
if(socket.readyState!==WebSocket.OPEN){
return;
}
socket.send(JSON.stringify({"type":action.type}));
}

function handleTablePayload(data){
if(data.sound){
playSound(data.sound);
}
if(data.type==="table.connected"){
tableMessages=data.messages || {};
connectionStatus.textContent=data.message;
addHistory(data.message);
renderActions(data.actions || []);
return;
}
if(data.type==="chat.message"){
addHistory(data.message);
return;
}
if(data.type==="player.left"){
addHistory(data.message);
return;
}
if(data.type==="message.private"){
addHistory(data.message);
return;
}
if(data.type==="error"){
addHistory(data.message);
}
}

historyElement.addEventListener("beforeinput",function(event){
event.preventDefault();
});

historyElement.addEventListener("paste",function(event){
event.preventDefault();
});

historyElement.addEventListener("cut",function(event){
event.preventDefault();
});

historyElement.addEventListener("drop",function(event){
event.preventDefault();
});

historyElement.addEventListener("input",function(){
restoreHistoryValue();
});

socket.addEventListener("message",function(event){
let data;
try{
data=JSON.parse(event.data);
}catch(error){
addHistory(tableMessages.client_invalid_message);
return;
}
handleTablePayload(data);
});

socket.addEventListener("close",function(){
addHistory(tableMessages.connection_closed);
});

chatArea.addEventListener("submit",function(event){
event.preventDefault();
const message=chatBox.value.trim();
chatBox.value="";
if(!message){
return;
}
if(socket.readyState!==WebSocket.OPEN){
return;
}
socket.send(JSON.stringify({"type":"chat.send","message":message}));
});
