var $sliders = $('.slider');

/* Escape selector string for jquery */
function jq( myid ) {
    return myid.replace( /(:|\.|\[|\]|,|\+)/g, "\\$1" );
}

function update_quotadisp() {
    var sum = 0;
    $sliders.each(function() {
        document.getElementById(this.name + "+disp_quota").innerHTML = Math.round(this.value);
        sum += this.valueAsNumber;
    });
    $('#debugsum').text(sum);
}

// Extend jquery with sum function -- applied to sliders
$.fn.sumValues = function() {
	var sum = 0;
	this.each(function() {
		sum += this.valueAsNumber;
	});
	return sum;
};

function total_quota() {
    $('.tqdisp').text($('#totalQuota').text());
}

$(document).ready(update_quotadisp);
$(document).ready(total_quota);

$sliders.each(function() { this.oldval = this.valueAsNumber; });

$sliders.on('input', function(event) {
    if(this.oldval === this.valueAsNumber) {
        return;
    }

    var change = this.valueAsNumber - this.oldval;
    var len = $sliders.length - 1;
    var extra = 0;

    var $othersliders = $sliders.not(this);
    var othersum = $othersliders.sumValues();

    console.log(this.name, this.oldval, this.valueAsNumber, change, othersum);

    $othersliders.each(function() {
        var max = Number(this.max);
        var proportion = (1 - change / othersum);

        console.log("..Adjust", this.name, this.valueAsNumber, '-*=>', proportion);
        this.valueAsNumber *= proportion;
        // this.valueAsNumber += (diff / ($sliders.length - 1));
        this.oldval = this.valueAsNumber;

    });
    this.oldval = this.valueAsNumber;
    update_quotadisp();
});
