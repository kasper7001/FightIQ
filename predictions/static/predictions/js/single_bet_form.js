document.addEventListener("DOMContentLoaded", function () {
    const fightSelect = document.getElementById("id_fight");
    const fighterSelect = document.getElementById("id_fighter");
    const marketSelect = document.getElementById("id_market");
    const fighterField = document.getElementById("fighter-field");
    const methodField = document.getElementById("method-field");
    const distanceField = document.getElementById("distance-field");

    function updateMarketFields() {
        if (!marketSelect) {
            return;
        }

        const market = marketSelect.value;

        fighterField.style.display = "none";
        methodField.style.display = "none";
        distanceField.style.display = "none";

        if (market === "MONEYLINE") {
            fighterField.style.display = "block";
        }

        if (market === "METHOD") {
            fighterField.style.display = "block";
            methodField.style.display = "block";
        }

        if (market === "DISTANCE") {
            distanceField.style.display = "block";
        }
    }

    marketSelect.addEventListener("change", updateMarketFields);

    updateMarketFields();

    if (!fightSelect || !fighterSelect) {
        return;
    }

    function clearFighters(message) {
        fighterSelect.innerHTML = "";

        const option = document.createElement("option");

        option.value = "";
        option.textContent = message;

        fighterSelect.appendChild(option);
    }

    function loadFighters(fightId) {
        if (!fightId) {
            clearFighters("Select a fight first");
            return;
        }

        fetch(`/api/fights/${fightId}/fighters/`, {
            credentials: "same-origin",
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("Could not load fighters.");
                }

                return response.json();
            })
            .then(function (data) {
                clearFighters("---------");

                data.fighters.forEach(function (fighter) {
                    const option = document.createElement("option");

                    option.value = fighter.id;
                    option.textContent = fighter.name;

                    fighterSelect.appendChild(option);
                });
            })
            .catch(function () {
                clearFighters("Could not load fighters");
            });
    }

    if (fightSelect.value) {
        loadFighters(fightSelect.value);
    } else {
        clearFighters("Select a fight first");
    }

    fightSelect.addEventListener("change", function () {
        loadFighters(fightSelect.value);
    });
});