function switch_input_mode(field_name){
    $("#edit_"+field_name+"_div").show();
    $("#show_"+field_name+"_div").hide();
    $("#approve_button, #unapprove_button, #reject_button, #unreject_button").addClass("disabled");
    $("#update_button").removeClass("disabled");
};

function show_form_field(){
    var field_name = this.id.replace("edit_","").replace("_button","");
    switch_input_mode(field_name);
};

$(function() {
    var form_fields_to_show = JSON.parse($("#form_fields_to_show").text());
    var form_fields = JSON.parse($("#form_fields").text());
    for (let field_name of form_fields_to_show){
        switch_input_mode(field_name);
    }
    for (let field_name of form_fields){
        $("#edit_"+field_name+"_button").on("click",show_form_field);
    }
});
