$(document).ready(function() {

    // Print the current table of guesses, insert into HTML Element "tbody"
    table("tbody");

    // When the guess form is submitted (as by pressing the guess button)
    $("#guess").submit(function() {

        // Run the guess function, wait 750ms for some animation
        setTimeout(guess(), 750);
        // Prevent the form from actually being submitted to the server
        event.preventDefault();

    });

    // Prompt user to confirm they actually want to start a new game
    // $(".confirmation").on("click", function () {
    //
    //     if(confirm("Are you sure you want to start a new game?"))
    //     {
    //         // new_game function is called
    //         new_game();
    //         // Re-enable the input box
    //         $("#word").prop("disabled", false);
    //     }
    //
    // });

    // Before the page reloads, save the values currently in the notes area
    // Uses localStorage in the browser to persist this data
    window.onbeforeunload = function() {
        localStorage.setItem("notes1", $("#notes1").val());
        localStorage.setItem("notes2", $("#notes2").val());
        localStorage.setItem("notes3", $("#notes3").val());
    };

    // Load the data from localStorage back into notes area
    // If values are not blank, restore them to the fields
    var notes1 = localStorage.getItem("notes1");
    if (notes1 !== null) $("#notes1").val(notes1);

    var notes2 = localStorage.getItem("notes2");
    if (notes2 !== null) $("#notes2").val(notes2);

    var notes3 = localStorage.getItem("notes3");
    if (notes3 !== null) $("#notes3").val(notes3);

});

/**
 * Validates a guess with some front-end work
 * Submits to server for more information
 */
function guess()
{
    // Stop here if nothing has been entered in the input
    if ($("#word").val() == '') return false;

    // Use the validate method to check length and isAlpha
    if (!validate($("#word").val()))
    {
        // Calls modal (defined below)
        modal("Try Again!", "Not a valid 5 letter word");
        // Empties the text box (defined below)
        clear();
        return false;
    }

    /**
     * Makes a getJSON request to get the score/validity of the guess
     */
    var parameters = {
        // Send the guess as a parameter
        guess: $("#word").val(),
    };
    $.getJSON(Flask.url_for("guess"), parameters)
    .done(function(data, textStatus, jqXHR) {

        // Depending on the score received, use the modal to prompt as appropriate

        // Indicates an invalid word
        if (data.score == -2) {
            modal("Game Finished!", "This game has already been finished. Please get a new mystery word by using the 'New Game' button above.");
            clear();
        }
        else if (data.score == -1)
        {
            modal("Try Again!", "That's not in the dictionary! Please try again.");
            clear();
        }
        // Indicates a winning word (score = 6)
        else if (data.score == 6)
        {
            // Disable the input box if the game is won, so no guesses are erroneously put in
            $("#word").prop("disabled", true);
            highscore_modal("Winner!", "You win! The word was " + $("#word").val() + "! Enter your name for the Highscores table!");
            $("#word").val("Click \"New Game\"");
        }
        // All letters are right, but not in correct order
        else if (data.score == 5)
        {
            modal("Almost There!", "Those are the right letters! Now just solve the anagram.");
            clear();
        }
        // Otherwise notify user of the score
        else
        {
            clear();
        }

        // Update the table with the new guess
        table("tbody");

    })
    .fail(function(jqXHR, textStatus, errorThrown) {

        // Log error to browser's console
        console.log(errorThrown.toString());

    });
}

/**
 * Generate HTML for the table of guesses
 */
function table(tbody)
{
    // Use getJSON promise interface to query /table with a GET request
    $.getJSON(Flask.url_for("table"))
    .done(function(data, textStatus, jqXHR) {

        // Initialize a string for the HTML
        var myTable = "";
        // Loop over the data returned by getJSON
        for (var i = 0; i < data.length; i++)
        {
            // Assign different colors based on the score of each word
            if (data[i].score == 0) var color = "red";

            else if (data[i].score <= 3) color = "blue";

            else color = "green";

            // highlight the most recent guess in green
            if (i == data.length - 1) var cl = "success";

            // Add a new row with attempt number, word, and score
            myTable += "<tr class='" + cl + "'><td>" + (i+1) + "</td>";
            myTable += "<td style='color:black'>" + data[i]["guess"] + "</td>";
            myTable += "<td style='color:" + color +"'><b>" + data[i]["score"] + "</b></td></tr>";
        }
        // Set the HTML of the tbody element to this HTML
        $("#" + tbody).html(myTable);
    })
    .fail(function(jqXHR, textStatus, errorThrown) {

        // Log error to browser's console
        console.log(errorThrown.toString());

    });

}

/**
 * Quickly checks the guess to try to avoid unnecessary server calls
 */
function validate(word)
{
    // Easy check for length
    if (word.length != 5)
    {
        return false;
    }
    // Check for all alphabetical characters using a regualar expression
    if (word.search(/[^A-Za-z]/) != -1)
    {
        return false;
    }
    // Preliminarily valid
    return true;
}

/**
 * Starts a new game, requesting the new game_id from the server
 */
function new_game()
{
    // Set the values in the notes area to default starting values
    $("#notes3").val("\tA B C D E F G H\n\tI J K L M N O P\n\tQ R S T U V W X\n\t\t   Y Z");
    $("#notes2").val("");
    $("#notes1").val("");

    // Request server to start a new game
    $.getJSON(Flask.url_for("game_id"))
    .done(function(data) {

        // Record the game_id returned in localStorage
        // localStorage.game_id = data.id;
        // Do nothing, python should redirect to index
        table("tbody");

    })
    .fail(function(jqXHR, textStatus, errorThrown) {

        // Log error to browser's console
        console.log(errorThrown.toString());

    });
}

/**
 * Calls a '#myModal' with title and content
 */
function modal(title, content)
{
    // Set HTML of myModal in index.html
    $("#modal_title").html(title);
    $("#modal_text").html(content);
    // Actually show the modal
    $("#myModal").modal();
}

function highscore_modal(title, content)
{
  // Set HTML of myModal in index.html
  $("#modal_title_form").html(title);
  $("#modal_text_form").html(content);
  // Actually show the modal
  $("#highscoreForm").modal();
}

/**
 * Shorter way to clear the guess text box
 */
function clear()
{
    $("#word").val("");
}
