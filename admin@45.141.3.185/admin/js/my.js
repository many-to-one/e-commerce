document.addEventListener("change", function(e) {
    if (e.target.classList.contains("vendor-toggle")) {
        console.log("kliknięto checkbox", e.target.dataset);
    }
});

console.log("my.js załadowany");