const API_URL = "http://localhost:5000"; // Change to your Azure backend URL

document.addEventListener("DOMContentLoaded", function () {
    // ✅ Register Form
    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
        registerForm.addEventListener("submit", async function(event) {
            event.preventDefault();

            let username = document.getElementById("username").value.trim();
            let password = document.getElementById("password").value.trim();
            let role = document.getElementById("role").value;
            let messageBox = document.getElementById("message");

            if (username.length < 3) {
                showMessage("❌ Username must be at least 3 characters!", "red");
                return;
            }

            if (password.length < 6) {
                showMessage("❌ Password must be at least 6 characters!", "red");
                return;
            }

            // Send request to backend
            try {
                const response = await fetch(`${API_URL}/register`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password, role })
                });

                const data = await response.json();
                if (response.ok) {
                    showMessage("✅ Account created successfully!", "lightgreen");
                    setTimeout(() => window.location.href = "login.html", 2000);
                } else {
                    showMessage(`❌ ${data.error}`, "red");
                }
            } catch (error) {
                showMessage("❌ Server error! Try again.", "red");
            }
        });
    }

    // ✅ Login Form
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", async function(event) {
            event.preventDefault();

            let username = document.getElementById("username").value.trim();
            let password = document.getElementById("password").value.trim();
            let messageBox = document.getElementById("message");

            if (!username || !password) {
                showMessage("❌ Please fill in all fields!", "red");
                return;
            }

            try {
                const response = await fetch(`${API_URL}/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });

                const data = await response.json();
                if (response.ok) {
                    localStorage.setItem("token", data.token);
                    localStorage.setItem("user", JSON.stringify(data.user));
                    showMessage("✅ Login successful!", "lightgreen");
                    setTimeout(() => window.location.href = "home.html", 2000);
                } else {
                    showMessage("❌ Invalid credentials! Try again.", "red");
                }
            } catch (error) {
                showMessage("❌ Server error! Try again.", "red");
            }
        });
    }

    // ✅ Logout
    const logoutButton = document.getElementById("logout");
    if (logoutButton) {
        logoutButton.addEventListener("click", () => {
            localStorage.removeItem("token");
            localStorage.removeItem("user");
            alert("You have been logged out.");
            window.location.href = "login.html";
        });
    }

    // ✅ Fetch Images
    async function fetchImages() {
        try {
            const response = await fetch(`${API_URL}/images`);
            const images = await response.json();
            const imageFeed = document.getElementById("imageFeed");
            const user = JSON.parse(localStorage.getItem("user"));

            if (imageFeed) {
                imageFeed.innerHTML = "";
                for (const img of images) {
                    let deleteButton = user && user.username === img.uploader 
                        ? `<button onclick="deleteImage(${img.id})">🗑️ Delete</button>` 
                        : "";

                    let comments = await fetchComments(img.id);
                    let commentHTML = comments.map(c => `<p><b>${c.commenter}:</b> ${c.text}</p>`).join("");

                    imageFeed.innerHTML += `
                        <div class="image-card">
                            <img src="${API_URL}/static/uploads/${img.filename}" alt="Image">
                            <p>Uploaded by: ${img.uploader}</p>
                            ${deleteButton}
                            <div class="comments">
                                <h4>Comments</h4>
                                ${commentHTML}
                                <input type="text" id="comment-${img.id}" placeholder="Write a comment...">
                                <button onclick="postComment(${img.id})">Post</button>
                            </div>
                        </div>`;
                }
            }
        } catch (error) {
            console.error("Error fetching images:", error);
        }
    }

    // ✅ Fetch Comments
    async function fetchComments(imageId) {
        const response = await fetch(`${API_URL}/comments/${imageId}`);
        return await response.json();
    }

    // ✅ Post a Comment
    async function postComment(imageId) {
        const token = localStorage.getItem("token");
        const commentInput = document.getElementById(`comment-${imageId}`);
        const commentText = commentInput.value.trim();

        if (!commentText) {
            alert("Comment cannot be empty!");
            return;
        }

        const response = await fetch(`${API_URL}/comment`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify({ image_id: imageId, text: commentText })
        });

        const data = await response.json();
        alert(data.message);
        commentInput.value = "";
        fetchImages();
    }

    // ✅ Delete Image
    async function deleteImage(imageId) {
        const token = localStorage.getItem("token");

        const response = await fetch(`${API_URL}/delete/${imageId}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${token}` }
        });

        const data = await response.json();
        alert(data.message);
        fetchImages();
    }

    // ✅ Image Upload Logic
    const imageFileInput = document.getElementById("imageFile");
    const previewImage = document.getElementById("previewImage");
    const fileNameDisplay = document.getElementById("fileName");
    const uploadButton = document.getElementById("uploadButton");

    if (imageFileInput) {
        imageFileInput.addEventListener("change", function () {
            const file = imageFileInput.files[0];
            if (file) displayPreview(file);
        });

        function displayPreview(file) {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = function (event) {
                previewImage.src = event.target.result;
                fileNameDisplay.textContent = file.name;
                uploadButton.disabled = false;
            };
        }
    }

    // ✅ Call fetchImages when the page loads
    if (document.getElementById("imageFeed")) fetchImages();
});

// ✅ Helper function to show messages
function showMessage(msg, color) {
    let messageBox = document.getElementById("message");
    if (messageBox) {
        messageBox.innerHTML = msg;
        messageBox.style.color = color;
    }
}
