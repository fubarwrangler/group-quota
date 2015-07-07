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

function validQuotaKey(event) {
	if (event.key == "ArrowUp")	{
		this.value++;
		$(this).trigger('change');
	} else if (event.key == "ArrowDown")	{
		this.value--;
		$(this).trigger('change');
	// Non control (<31) and non-numeric (outside ASCII [48-57] are rejected)
	} else if (event.charCode < 31 || (event.charCode >= 48 && event.charCode <= 57))	{
		return;
	} else {
		event.preventDefault();
	}
}

function manualQuotaEdit(txtbox)	{
	var myslider = get_slider(txtbox);
	var newval = parseInt(txtbox.value);
	var oldval = myslider.valueAsNumber;

	if(newval > myslider.max)	{
		newval = myslider.max;
		txtbox.value = newval;
	}
	myslider.valueAsNumber = newval;
	$(myslider).trigger('change');
}
