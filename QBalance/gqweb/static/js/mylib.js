// Extend jquery with sum function -- applied to sliders
$.fn.sumValues = function() {
	var sum = 0;
	this.each(function() {
		sum += this.valueAsNumber;
	});
	return sum;
};

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
