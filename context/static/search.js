let form = document.querySelector("#search-form");

const botSelect = $("#collection-select").select2();
const spinner = document.querySelector("#spinner");

form.addEventListener("submit", (e) => {
  e.preventDefault();
  spinner.classList.remove("hidden");

  fetch(
    "/context/search/?" + new URLSearchParams(new FormData(form)).toString(),
  )
    .then((response) => response.json())
    .then((data) => {
      document.querySelector("#sources").innerHTML = data
        .map(renderSource)
        .join("\n");
    })
    .finally(() => spinner.classList.add("hidden"));
});
