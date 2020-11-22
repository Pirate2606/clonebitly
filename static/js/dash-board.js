function open_create_url() {
    document.getElementById("create-short-url").style.width = "300px";
    document.getElementById("main-body").style.opacity = 0.7;
    document.getElementById("create-short-url").style.opacity = 1;
}

function close_create_url() {
    document.getElementById("create-short-url").style.width = "0";
    document.getElementById("main-body").style.opacity = 1;
    document.getElementById("create-short-url").style.opacity = 1;
}

function close_edit_url() {
    document.getElementById("edit-short-url").style.width = "0";
    document.getElementById("main-body").style.opacity = 1;
    document.getElementById("edit-short-url").style.opacity = 1;
}

function edit() {
    const readOnlyLength = $("#page_name_field_hidden").val().length;
    $("#page_name_field").on("keypress, keydown", function (event) {
        if (
            event.which !== 37 &&
            event.which !== 39 &&
            (this.selectionStart < readOnlyLength ||
                (this.selectionStart === readOnlyLength &&
                    event.which === 8))
        ) {
            return false;
        }
    });
}