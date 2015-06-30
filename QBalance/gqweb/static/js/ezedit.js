var $sliders = $('.slider');

function update_quotadisp() {
    var sum = 0;
    $sliders.each(function() {
        document.getElementById(this.name + "+disp_quota").innerHTML = Math.round(this.value);
        sum += this.valueAsNumber;
    });
    $('#debugsum').text(sum);
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
        newval = this.valueAsNumber * proportion;

        // Avoid too small so we don't approach a div-by-zero jump
        if(Math.abs(newval) < 0.00001)    {
            newval = 0.00001;
        }
        this.valueAsNumber = newval;

        this.oldval = this.valueAsNumber;

    });
    this.oldval = this.valueAsNumber;
    update_quotadisp();
});
