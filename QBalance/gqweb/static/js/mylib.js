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

function get_checkbox(groupname)    {
    return document.getElementById(groupname + "+take");
}

function get_quota(groupname)    {
    return document.getElementById(groupname + "+disp_quota");
}

function get_slider(elem)	{
	return document.getElementById(elem.name.split('+', 1)[0]);
}
