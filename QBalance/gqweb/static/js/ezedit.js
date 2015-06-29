var $sliders = $('.slider');

/* Escape selector string for jquery */
function jq( myid ) {
    return myid.replace( /(:|\.|\[|\]|,|\+)/g, "\\$1" );
}

function update_quotadisp() {
    $sliders.each(function() {
        var mysel = this.name + "+disp_quota";
        $(document.getElementById(mysel)).text(this.valueAsNumber);
        // console.log("Would update ", mydisp);
    });
};

$(window).load(update_quotadisp);

$sliders.on('input documentready', function(event) {

    console.log(this.name, this.valueAsNumber);

    update_quotadisp();

    $sliders.not(this).each(function() {
        // console.log($('#' + this.name + "+disp_quota"));
    });
});
