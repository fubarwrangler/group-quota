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
    var diff = this.oldval - this.valueAsNumber;
    console.log(this.name, this.oldval, this.valueAsNumber, diff);
    $sliders.not(this).each(function() {
        var change = diff / $sliders.length;
        // console.log($('#' + this.name + "+disp_quota"));
        console.log("Adjust", this.name, 'by', change )
        this.valueAsNumber += (diff / ($sliders.length - 1));
        this.oldval = this.valueAsNumber;
    });
    this.oldval = this.valueAsNumber;
    update_quotadisp();
});
