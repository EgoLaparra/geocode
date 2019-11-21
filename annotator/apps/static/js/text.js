function createNew(id, newchild_id, color){
    var el = document.getElementById(id + "_links");
    var form = document.getElementById(id + "_newchild");
    var div = document.createElement('div');
    div.id = newchild_id + "_hrefs";

    var wikipedia = document.getElementById("wikipedia")
    if (wikipedia != ""){
        var wikipedias = wikipedia.value.split(" ")
        for (i = 0; i < wikipedias.length; i++) {
            var ahref = document.createElement("a");
            ahref.href = wikipedias[i];
            var textfields = wikipedias[i].split("/");
            ahref.innerHTML = textfields[textfields.length - 1];
            ahref.style.color = color;
            ahref.style.paddingRight = "0.5em";
            ahref.classList.add("wikipedia");
            div.appendChild(ahref);
        }
     }

    var into_osm_script = ""
    var osm = document.getElementById("osm")
    if (osm.value != "") {
        var osms = osm.value.split(" ")
        for (i = 0; i < osms.length; i++) {
            var ahref = document.createElement("a");
            ahref.href = osms[i];
            var textfields = osms[i].split("/");
            var type = textfields[textfields.length - 2];
            var ref = textfields[textfields.length - 1];
            ahref.innerHTML =  type + "/" + ref
            ahref.style.color = color;
            ahref.style.paddingRight = "0.5em";
            ahref.classList.add("osm");
            div.appendChild(ahref);
            into_osm_script = into_osm_script + "<id-query type=\"" + type + "\" ref=\"" + ref + "\"/>"
        }
     }

    var del_button = document.createElement("button")
    del_button
    del_button.type = "button";
    del_button.classList.add("small-button");
    del_button.innerHTML= "x";
    var keydown = function(e){
        deleteAnnotation(id, newchild_id);
    };
    del_button.addEventListener('click', keydown);
    div.appendChild(del_button);

    el.removeChild(form);
    el.appendChild(div);

    var osm_script = document.getElementById(id + "_script");
    osm_script.innerText = osm_script.innerText.replace("</union>", into_osm_script + "</union>")

    var modified = document.getElementById(id + "_modified");
    modified.value = "yes"
}


function selectChanged(id) {
    var modified = document.getElementById(id + "_modified");
    modified.value = "yes";
}


function createForm(id, newchild_id, color) {
    var form = document.createElement("form");
    form.id = id + "_newchild";

    form.appendChild(document.createElement("hr"));
    form.appendChild(document.createTextNode("Wikipedia:"));
    form.appendChild(document.createElement("br"));
    var textarea = document.createElement("textarea");
    textarea.id = "wikipedia";
    textarea.style.width = "100%"
    form.appendChild(textarea);
    form.appendChild(document.createElement("br"));

    form.appendChild(document.createTextNode("OSM:"));
    form.appendChild(document.createElement("br"));
    var textarea = document.createElement("textarea");
    textarea.id = "osm";
    textarea.style.width = "100%"
    form.appendChild(textarea);
    form.appendChild(document.createElement("br"));

    var button = document.createElement("button");
    button.type = "button";
    button.classList.add("button");
    button.innerHTML= "Done";
    var keydown = function(e){
        createNew(id, newchild_id, color);
    };
    button.addEventListener('click', keydown);
    form.appendChild(button);
    form.appendChild(document.createElement("hr"));

    return form;
}


function randInt(min, max) {
	return parseInt((Math.random() * (max - min + 1)), 10) + min;
}


function addAnnotation(id) {
    var range = window.getSelection().getRangeAt(0);
    var parent_p = range.commonAncestorContainer.parentNode;
    var parent_p_id = parent_p.id;
    var newchild_id = parent_p_id + "_" + String(parent_p.childElementCount).padStart(3, '0');
    var selectionContents = range.extractContents();
    var font = document.createElement("font");
    var r = randInt(80,220);
    var b = randInt(80,220);
    var g = randInt(80,220);
    var color = "rgb(" + r + "," + g + "," + b + ")";
    font.style.backgroundColor = color;
    font.id = newchild_id + "_text";
    font.appendChild(selectionContents);
    range.insertNode(font);

    var el = document.getElementById(id + "_links");
    var form = createForm(id, newchild_id, color);
    el.appendChild(form);
}


function hideAnnotation(id) {
    var el = document.getElementById(id + "_text");
    el.removeAttribute("style");
    el.classList.add("removed");
}


function deleteAnnotation(entity_id, id) {
    var el = document.getElementById(id + "_hrefs");
    var parent_p = el.parentNode;
    parent_p.removeChild(el);
    hideAnnotation(id);
    var modified = document.getElementById(entity_id + "_modified");
    modified.value = "yes"
}


function submitForm(id, file_name) {
    var data = '<data>';
    var form = document.getElementById(id);
    var action = form.action;
    var entity_tables = form.getElementsByTagName("table");
    for (i = 0; i < entity_tables.length; i++) {
        var entity_table = entity_tables[i];
        var status = entity_table.querySelectorAll("select")[0];
        var modified = document.getElementById(status.name + "_modified");
        if (modified.value == "yes") {
            var status_value = status.options[status.selectedIndex].value;
            data = data + '<entity name=\"' + status.name + '\" value=\"' + status_value + '\">';
            var entity_tds = entity_table.querySelectorAll("td");
            var text = entity_tds[0].innerHTML.replace(/\r?\n|\r/g, "").replace(/\s+/g, " ");
            data = data + "<text>" + text + "</text>";
            var links = entity_tds[1].innerHTML.replace(/\r?\n|\r/g, "").replace(/\s+/g, " ");
            data = data + "<links>" + links + "</links>";
            data = data + '</entity>';
         }
    }
    data = data + '</data>';

    var form_submit = document.createElement("form");
    form_submit.action = action;
    form_submit.method = "post";
    var hidden = document.createElement("input");
    hidden.type = "hidden"
    hidden.name = "submission";
    hidden.value = data;
    form_submit.appendChild(hidden);
    var hidden_file_name = document.createElement("input");
    hidden_file_name.type = "hidden";
    hidden_file_name.name = "file_name";
    hidden_file_name.value = file_name;
    form_submit.appendChild(hidden_file_name);
    document.body.appendChild(form_submit);
    form_submit.submit();
}
