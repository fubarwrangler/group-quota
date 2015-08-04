// Extend jquery with sum function -- applied to sliders
$.fn.sumValues = function() {
	var sum = 0;
	this.each(function() {
		sum += this.valueAsNumber;
	});
	return sum;
};

// Function to force redraw of sliders because of a bug in Chrome, when max
// property changes no redraw happens, see SO link here: http://goo.gl/WOHlnX
$.fn.redraw = function(){
    $(this).each(function(){
        if (this.value && ! isNaN(parseInt(this.value, 10))) {
            this.value++;
            this.value--;
        }
    });
};

$.postjson = function (url, data) {
	return $.ajax($SCRIPT_ROOT + url, {
		url: JSON.stringify(data),
		contentType: 'application/json',
		type: 'POST',
		data: JSON.stringify(data),
	});
};


function flash(message,category) {
    $('<div class="alert alert-'+category+' flash closeme">!'+ message +'</div>')
        .prependTo('#mainContent')
        .delay(1500)
        .fadeOut(200, function() {
            $(this).alert('close');
        });
}


// Escape selector string for jquery
function jq( myid ) {
    return myid.replace( /(:|\.|\[|\]|,|\+)/g, "\\$1" );
}

function get_checkbox(groupname) 		{ return document.getElementsByName(groupname + "+take")[0]; }
function get_quota(groupname) 			{ return document.getElementById(groupname + "+disp_quota"); }
function get_max_disp(groupname) 		{ return document.getElementById(groupname + "+tq"); }
function get_slider(elem) 				{ return document.getElementById(elem.name.split('+', 1)[0]); }
function get_quota_from_checkbox(box) 	{ return get_quota(box.name.split('+', 1)[0]); }
// function get_children_inputs_from_slider(slider) { return $("input[parent='" + jq(slider.name)  + "']"); }
function get_children_inputs_from_slider(slider) {
	return $(document.getElementsByClassName(slider.getAttribute('hash') + '_chld'));
}
