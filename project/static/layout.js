$(document).ready(function() {

    // Prompt user to confirm they actually want to start a new game
    $(".confirmation").on("click", function () {

        if(confirm("Are you sure you want to start a new game?"))
        {
            // new_game function is called
            new_game();
            // Re-enable the input box
            $("#word").prop("disabled", false);
        }

    });
});
