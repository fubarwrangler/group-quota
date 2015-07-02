/******************************************************************************
 * Global Variables
 *****************************************************************************/
var $sliders = $('.slider');
var $boxes = $('.ckbx');
var MIN_VAL = 0.00001;

/******************************************************************************
 * Utility functions for use in event handlers
 *****************************************************************************/
/* Display live quota updates in row as slider changes */
function update_quotadisp() {
    $sliders.each(function() {
        get_quota(this.name).innerHTML = Math.round(this.value);

        max = get_max_disp(this.name);

        if(this.className.indexOf('noseeme') < 0)    {
            max.innerHTML = Math.round(this.max);
        }

        get_children_inputs_from_slider(this).each(function() {
            get_quota(this.name).innerHTML = Math.round(this.value);
        });
    });

    $('#debugsum').text($sliders.sumValues());
    $('#quotasum').text(Math.round($sliders.sumValues()));
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
    $(get_slider(box)).toggleClass('noseeme');
    $(get_max_disp(box.name.split('+')[0])).toggleClass('noseeme');
    $(get_quota_from_checkbox(box)).toggleClass('fnt-bold');

    var $unchecked_sliders = $sliders.filter(function(idx, elem) {
            return !get_checkbox(this.name).checked;
        });
    $unchecked_sliders.attr('max', $unchecked_sliders.sumValues());
    update_quotadisp();
}

function adjust_children(slider) {
    var pq = slider.valueAsNumber;  // parent quota

    get_children_inputs_from_slider(slider)
        .each(function() {
            var proportion = this.getAttribute('proportion');
            console.log("....child", this.name, proportion, '*', pq);
            this.valueAsNumber = proportion * pq;
        });
}

/******************************************************************************
 * Event Handlers for form elements
 *****************************************************************************/
/* Handle checked box or warn on too many checkboxes */
$boxes.change(function(event)   {
    var warning = '&nbsp;Can\'t leave fewer than 2 free sliders';

    // Magic to make alert pop up and fade away
    if($('input[type="checkbox"]:checked').length >= $sliders.length - 1)    {
        $('<div class="alert alert-danger my-popup-warn" role="alert">' +
            '<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>' +
            '<span class="sr-only"></span>' + warning + '</div>')
            .insertAfter( $(this).parent())
            .animate({opacity: 1.0}, 1450)
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

    this.valueAsNumber = Math.max(MIN_VAL, this.valueAsNumber);

    var change = this.valueAsNumber - this.oldval;
    var len = $sliders.length - 1;

    // All other non-checked sliders
    var $othersliders = $sliders.not(this).filter(function(idx, elem) {
        return !get_checkbox(this.name).checked;
    });
    var othersum = $othersliders.sumValues();

    console.log(this.name, this.oldval, this.valueAsNumber, change, othersum);

    this.last_proportion = (this.valueAsNumber / this.oldval);
    adjust_children(this);

    $othersliders.each(function() {
        var max = Number(this.max);
        var proportion = (1 - change / othersum);

        console.log("..Adjust", this.name, this.valueAsNumber, '-*=>', proportion);

        // Avoid too small so we don't approach a div-by-zero jump
        newval = Math.max(MIN_VAL, this.valueAsNumber * proportion);

        this.valueAsNumber = newval;
        this.oldval = this.valueAsNumber;
        this.last_proportion = proportion;
        adjust_children(this);
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
