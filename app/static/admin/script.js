// Sidebar Toggle Functionality
document.addEventListener("DOMContentLoaded", function () {
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("adminSidebar");
  const mainContent = document.getElementById("adminMain");

  // Set active navigation item based on current URL
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll(".nav-link");

  navLinks.forEach((link) => {
    link.classList.remove("active");
    if (link.getAttribute("href") === currentPath) {
      link.classList.add("active");
    }
  });

  // File upload change
  const imageInput = document.getElementById("image");
  if (imageInput) {
    imageInput.addEventListener("change", function (e) {
      const file = e.target.files[0];
      const preview = document.getElementById("imagePreview");
      const previewImg = document.getElementById("previewImg");

      if (file) {
        const allowedTypes = [
          "image/jpeg",
          "image/jpg",
          "image/png",
          "image/gif",
          "image/webp",
        ];
        if (!allowedTypes.includes(file.type)) {
          alert("Please select a valid image file (JPG, JPEG, PNG, GIF, WEBP)");
          e.target.value = "";
          preview.style.display = "none";
          return;
        }

        if (file.size > 5 * 1024 * 1024) {
          alert("File size must be less than 5MB");
          e.target.value = "";
          preview.style.display = "none";
          return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
          previewImg.src = e.target.result;
          preview.style.display = "block";
        };
        reader.readAsDataURL(file);
      } else {
        preview.style.display = "none";
      }
    });
  }

  // Close sidebar on mobile when clicking outside
  document.addEventListener("click", function (e) {
    if (window.innerWidth <= 768) {
      if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove("show");
      }
    }
  });

  // Handle window resize
  window.addEventListener("resize", function () {
    if (window.innerWidth > 768) {
      sidebar.classList.remove("show");
    } else {
      sidebar.classList.remove("collapsed");
      mainContent.classList.remove("sidebar-collapsed");
    }
  });

  const dropdown = document.querySelector(".admin-user.dropdown");

  dropdown.addEventListener("mouseenter", () => {
    const menu = dropdown.querySelector(".dropdown-menu");
    menu.classList.add("show");
  });

  dropdown.addEventListener("mouseleave", () => {
    const menu = dropdown.querySelector(".dropdown-menu");
    menu.classList.remove("show");
  });
});
