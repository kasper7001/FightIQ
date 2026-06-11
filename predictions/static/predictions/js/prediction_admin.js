document.addEventListener("DOMContentLoaded", function () {
    const fightSelect = document.getElementById("id_fight");
    const winnerSelect = document.getElementById("id_predicted_winner");

    if (!fightSelect || !winnerSelect) {
        return;
    }

    function clearWinnerOptions(message) {
        winnerSelect.innerHTML = "";

        const emptyOption = document.createElement("option");
        emptyOption.value = "";
        emptyOption.textContent = message || "---------";
        winnerSelect.appendChild(emptyOption);
    }

    function loadFightersForFight(fightId, selectedWinnerId) {
        if (!fightId) {
            clearWinnerOptions("Select a fight first");
            return;
        }

        fetch(`/api/fights/${fightId}/fighters/`, {
            credentials: "same-origin"
        })
        .then(function (response) {
            if (!response.ok) {
                throw new Error("Could not load fighters");
            }
            return response.json();
        })
        .then(function (data) {
            clearWinnerOptions("---------");

            data.fighters.forEach(function (fighter) {
                const option = document.createElement("option");
                option.value = fighter.id;
                option.textContent = fighter.name;

                if (selectedWinnerId && String(fighter.id) === String(selectedWinnerId)) {
                    option.selected = true;
                }

                winnerSelect.appendChild(option);
            });
        })
        .catch(function () {
            clearWinnerOptions("Could not load fighters");
        });
    }

    const initialFightId = fightSelect.value;
    const initialWinnerId = winnerSelect.value;

    if (initialFightId) {
        loadFightersForFight(initialFightId, initialWinnerId);
    } else {
        clearWinnerOptions("Select a fight first");
    }

    fightSelect.addEventListener("change", function () {
        loadFightersForFight(fightSelect.value, null);
    });

    if (window.django && window.django.jQuery) {
        window.django.jQuery(fightSelect).on("select2:select", function () {
            loadFightersForFight(fightSelect.value, null);
        });

        window.django.jQuery(fightSelect).on("select2:clear", function () {
            clearWinnerOptions("Select a fight first");
        });
    }
});
