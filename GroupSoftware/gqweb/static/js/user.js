
$('.aj_rmuser').click(function (e) {
    var $jqthis = $(this);
    var prompt = "Are you sure you want to remove " + $jqthis.attr('name') + "?";
    bootbox.confirm(prompt, function(result) {
        if(!result) { return; }
        var uid = $jqthis.attr('uid');

        $.post($SCRIPT_ROOT + '/user/api/remove', { userid: uid })
            .done(function() {
                $('#ur_' + uid).remove();
                flash('Removed user ' + uid, 'warning');
            })
            .fail(function() {
                alert("Failed to delete uid=" + uid);
            });
        return true;
    });
});


$('.aj_active').on('switchChange.bootstrapSwitch', function(event, state) {
    var $jqthis = $(this);
    var user = $jqthis.attr('user');
    var data = {'user': user, 'active': state ? 'on' : 'off'};
    $.postjson('/user/api/activate', data)
        .fail(function() {
            flash('Server error for user ' + user, 'danger');
            $jqthis.bootstrapSwitch('toggleState', true);
        })
        .done(function() {
            var msg = (state ? "Activated" : "Deactivated") + ' user ' + user;
            flash(msg, state? 'success' : 'warning');
        });
});
