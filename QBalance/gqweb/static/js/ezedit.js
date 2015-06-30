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

function jqsumval($elements)  {
    var sum = 0;
    $elements.each(function() {
        sum += this.valueAsNumber;
    });
    return sum;
}

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

    var change = this.oldval - this.valueAsNumber;
    var len = $sliders.length - 1;
    var extra = 0;

    console.log(this.name, this.oldval, this.valueAsNumber, change);

    var $othersliders = $sliders.not(this);

    $othersliders.each(function() {
        var max = Number(this.max);
        var diff = (change + extra) / len;

        newval = this.valueAsNumber + diff;
        console.log("..Adjust", this.name, 'by', diff, ':',
                    this.valueAsNumber, '-->', newval);

        // If would over/under-shoot
        if (newval > max)  {
            extra += newval - max;
            console.log("....too large, extra for next is", extra);
            this.valueAsNumber = max;
        } else if (newval < 0) {
            extra = newval - this.valueAsNumber;
            console.log("....too small, extra for next is", extra);
            this.valueAsNumber = 0;
        } else {
            extra = 0;
            this.valueAsNumber = newval;
        }

        // this.valueAsNumber += (diff / ($sliders.length - 1));
        this.oldval = this.valueAsNumber;

    });
    var othersum = jqsumval($sliders);
    this.oldval = this.valueAsNumber;
    update_quotadisp();
});
