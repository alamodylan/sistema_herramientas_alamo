// Mantener sesión activa mientras se usa la app
document.addEventListener("mousemove", keepAlive);
document.addEventListener("keydown", keepAlive);

function keepAlive() {
    fetch("/ping", {method: "GET"});  
}