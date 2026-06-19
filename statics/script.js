/* ===== IMAGE PREVIEW ===== */
document.addEventListener("DOMContentLoaded", function() {

    const upload = document.getElementById("imageUpload");
    const preview = document.getElementById("preview");

    if (upload) {
        upload.onchange = function(evt) {
            const [file] = evt.target.files;
            if (file) {
                preview.src = URL.createObjectURL(file);
                preview.style.width = "200px";
                preview.style.marginTop = "20px";
            }
        };
    }

    /* ===== FADE IN EFFECT ===== */
    document.body.style.opacity = 0;
    setTimeout(() => {
        document.body.style.transition = "1s";
        document.body.style.opacity = 1;
    }, 200);

});


function togglePassword() {
    const pass = document.getElementById("password");
    pass.type = pass.type === "password" ? "text" : "password";
}

function showLoading(btn) {
    btn.innerHTML = "Logging in...";
}

/* ===== IMAGE ZOOM FULLSCREEN ===== */
function openFullscreen(imgElement) {
    const overlay = document.createElement("div");
    overlay.classList.add("fullscreen");

    const img = document.createElement("img");
    img.src = imgElement.src;

    overlay.appendChild(img);
    document.body.appendChild(overlay);

    overlay.onclick = function() {
        document.body.removeChild(overlay);
    };
}


/* ===== DARK / LIGHT MODE TOGGLE ===== */
function toggleTheme() {
    document.body.classList.toggle("dark-mode");
}


/* ===== SMOOTH SCROLL (Optional) ===== */
document.querySelectorAll("a[href^='#']").forEach(anchor => {
    anchor.addEventListener("click", function(e) {
        e.preventDefault();
        document.querySelector(this.getAttribute("href")).scrollIntoView({
            behavior: "smooth"
        });
    });
});