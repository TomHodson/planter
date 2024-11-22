const iconContainer = document.getElementById("icon-container");
const photoInput = document.getElementById("photo-input");

// Handle photo upload
photoInput.addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (file) {
    const formData = new FormData();
    formData.append("photo", file);

    const response = await fetch("/api/create", {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      const data = await response.json(); // Extract JSON response
      const id = data.id; // Get the photo ID
      window.location.href = `/api/modify/${id}`; // Redirect to modify page
    } else {
      console.error("Failed to upload photo");
    }
  }
  photoInput.value = ""; // Reset input
});

async function fetchPhotos() {
  const response = await fetch("/api/list");
  const photos = await response.json();

  // Clear existing icons (except the add-icon)
  Array.from(iconContainer.children)
    .filter((child) => !child.classList.contains("add-icon"))
    .forEach((child) => child.remove());

  // Add photos to the container
  photos.forEach((photo) => {
    const { id, name, days_since_watered } = photo;

    // Create photo container
    const photoContainer = document.createElement("div");
    photoContainer.className = "photo-container";

    // Add name and watering info
    const overlay = document.createElement("div");
    overlay.className = "photo-overlay";
    overlay.innerHTML = `
            <p class="photo-name">${name || "Unnamed Plant"}</p>
            <p class="photo-watered">
                ${
                  days_since_watered !== null
                    ? `${days_since_watered} day${
                        days_since_watered !== 1 ? "s" : ""
                      }`
                    : "Never"
                }
            </p>
        `;

    // Add icon
    const photoIcon = document.createElement("div");
    photoIcon.className = "icon";
    photoIcon.innerHTML = `<img src="/uploads/${id}" alt="photo">`;
    photoIcon.addEventListener("click", () => {
      window.location.href = `/api/modify/${id}`;
    });

    // Combine elements
    photoContainer.appendChild(overlay);
    photoContainer.appendChild(photoIcon);
    iconContainer.appendChild(photoContainer);
  });
}

// Load photos on page load
fetchPhotos();
