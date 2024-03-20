$(document).ready(function () {
  const botSelect = $("#bot-select").select2();
  const spinner = document.querySelector("#spinner");

  function loadSlug() {
    const slug = botSelect.val();
    fetch(`/${slug}/fields/`)
      .then((resp) => resp.text())
      .then((text) => {
        document.querySelector("#bot-fields").innerHTML = text;
      });
  }

  botSelect.on("change", () => {
    loadSlug();
  });
  const form = document.querySelector("#bot-form");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    spinner.classList.remove("hidden");
    const data = new FormData(form);

    fetch(`/${botSelect.val()}/`, {
      method: "POST",
      body: data,
    })
      .then((resp) => resp.json())
      .then((data) => {
        document.querySelector("#answer-field").value = data["answer"];
        document.querySelector("#sources").innerHTML = data.docs
          .map(renderSource)
          .join("\n");
      })
      .catch(() =>
        alert("Fehler bei der Bearbeitung der Frage, erneut versuchen!")
      )
      .finally(() => spinner.classList.add("hidden"));
  });
  loadSlug();
});
