var $sliders = $('.slider');
var $boxes = $('.ckbx');

/* Display live quota updates in row as slider changes */
function update_quotadisp() {
    $sliders.each(function() {
        get_quota(this.name).innerHTML = Math.round(this.value);
    });
    $('#debugsum').text($sliders.sumValues());
}

/* Update total-quota on RHS of sliders from hidden element */
function total_quota() {
    $('.tqdisp').text($('#totalQuota').text());
}

/* On page load dissapear sliders for checked boxes */
function check_checked()    {
    $boxes.each(function() {
        if(this.checked)    {
            $(get_slider(this)).toggle();
        }
    });
}

/* This syntax is same as $(document).ready(fn); */
$(update_quotadisp);
$(total_quota);
$(check_checked);

$sliders.each(function() { this.oldval = this.valueAsNumber; });

$boxes.change(function(event)   {
    var warning = 'Cannot leave fewer than 2 free sliders';
    if($('input[type="checkbox"]:checked').length >= $sliders.length - 1)    {
        $('<div class="alert alert-danger" role="alert">' +
            warning +
            '</div>')
            .insertAfter( $('.form-inline'))
            .fadeIn('slow')
            .animate({opacity: 1.0}, 2000)
            .fadeOut('slow', function() { $(this).remove(); })
            ;
        this.checked = false;
        return;
    }
    $(get_slider(this)).toggle();
    console.log(get_slider(this));
});

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
