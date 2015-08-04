
$('.aj_rmuser').click(function (e) {
    var $jqthis = $(this);
    var prompt = "Are you sure you want to remove " + $jqthis.attr('name') + "?";
    bootbox.confirm(prompt, function(result) {
        if(!result) { return; }
        var uid = $jqthis.attr('uid');

        $.post($SCRIPT_ROOT + '/user/api/remove', { userid: uid })
            .done(function() {
                $('#ur_' + uid).remove();
            })
            .fail(function() {
                alert("Failed to delete uid=" + uid)
            });
        return true;
    });
});
