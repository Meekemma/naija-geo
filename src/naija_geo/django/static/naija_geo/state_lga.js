/* naija-geo: show only the LGAs of the chosen state in a StateLGAWidget <select>. */
(function () {
  "use strict";

  function link(lgaSelect) {
    if (lgaSelect.dataset.naijaGeoLinked) {
      return;
    }
    var stateName = lgaSelect.dataset.stateField;
    var stateSelect = lgaSelect.form
      ? lgaSelect.form.elements.namedItem(stateName)
      : document.querySelector('[name="' + stateName + '"]');
    if (!stateSelect) {
      return;
    }
    lgaSelect.dataset.naijaGeoLinked = "true";

    function filter() {
      var chosen = stateSelect.value;
      Array.prototype.forEach.call(lgaSelect.options, function (option) {
        if (!option.value) {
          return; // the empty "Select an LGA" option stays visible
        }
        var visible = chosen !== "" && option.dataset.state === chosen;
        option.hidden = !visible;
        option.disabled = !visible;
        if (!visible && option.selected) {
          lgaSelect.value = "";
        }
      });
    }

    stateSelect.addEventListener("change", filter);
    filter();
  }

  function init() {
    document.querySelectorAll("select[data-naija-geo-lga]").forEach(link);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
