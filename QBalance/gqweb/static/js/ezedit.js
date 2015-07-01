/******************************************************************************
 * Global Variables
 *****************************************************************************/
var $sliders = $('.slider');
var $boxes = $('.ckbx');

/******************************************************************************
 * Utility functions for use in event handlers
 *****************************************************************************/
/* Display live quota updates in row as slider changes */
function update_quotadisp() {
    $sliders.each(function() {
        get_quota(this.name).innerHTML = Math.round(this.value);
        max = get_max_disp(this.name);
        if($(this).is( ":visible" ))    {
            max.innerHTML = Math.round(this.max);
        }
    });

    $('#debugsum').text($sliders.sumValues());
}

/* On page (re)load run actions for already checked boxes */
function check_checked()    {
    $boxes.each(function() {
        if(this.checked)    {
            checked_actions(this);
        }
    });
}

/* Actions when checkbox is clicked */
function checked_actions(box)  {
    $(get_slider(box)).toggle();
    $(get_max_disp(box.name.split('+')[0])).toggle();
    $(get_quota_from_checkbox(box)).toggleClass('fnt-bold');

    var $unchecked_sliders = $sliders.filter(function(idx, elem) {
            return !get_checkbox(this.name).checked;
        });
    $unchecked_sliders.attr('max', $unchecked_sliders.sumValues());
    update_quotadisp();
}


/******************************************************************************
 * Event Handlers for form elements
 *****************************************************************************/
/* Handle checked box or warn on too many checkboxes */
$boxes.change(function(event)   {
    var warning = 'Cannot leave fewer than 2 free sliders';

    // Magic to make alert pop up and fade away
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
    } else {
        checked_actions(this);
    }
});

/* Main algorithm for proportionally changing other sliders */
$sliders.on('input', function(event) {
    if(this.oldval === this.valueAsNumber) {
        return;
    }

    var change = this.valueAsNumber - this.oldval;
    var len = $sliders.length - 1;

    // All other non-checked sliders
    var $othersliders = $sliders.not(this).filter(function(idx, elem) {
        return !get_checkbox(this.name).checked;
    });
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



/******************************************************************************
 * Actions to take on page load/reload
 *****************************************************************************/

$sliders.each(function() { this.oldval = this.valueAsNumber; });

// This syntax is same as $(document).ready(fn);
$(update_quotadisp);
$(check_checked);
