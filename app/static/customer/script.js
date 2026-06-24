function toggleUserDropdown() {
    event.stopPropagation();
  const dropdown = document.getElementById("userDropdown");
  dropdown.classList.toggle("show");
}

$(document).ready(function () {
  document.addEventListener("click", function (event) {
    const userDropdown = document.getElementById("userDropdown");
    const userButton = document.querySelector(".user-dropdown button");

     if (
      userDropdown.classList.contains("show") &&
      !userButton.contains(event.target) &&
      !userDropdown.contains(event.target)
    ) {
      userDropdown.classList.remove("show");
    }
  });

  // const userDropdownContainer = document.querySelector(".user-dropdown");
  // const userDropdownMenu = document.getElementById("userDropdown");

  // userDropdownContainer.addEventListener("mouseenter", () => {
  //   userDropdownMenu.classList.add("show");
  // });

  // userDropdownContainer.addEventListener("mouseleave", () => {
  //   userDropdownMenu.classList.remove("show");
  // });
});
