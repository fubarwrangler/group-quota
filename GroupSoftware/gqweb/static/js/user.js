
$('.aj_rmuser').click(function (e) {
    var $jqthis = $(this);
    var prompt = "Are you sure you want to remove " + $jqthis.attr('name') + "?";
    bootbox.confirm(prompt, function(result) {
        if(!result) { return; }
        var uid = $jqthis.attr('uid');

        $.postjson('/user/api/remove', {userid: uid})
            .done(function() {
                $('#ur_' + uid).remove();
                flash('Removed user ' + uid, 'warning');
            })
            .fail(function() {
                flash("Failed to delete uid=" + uid, 'danger');
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


$('.aj_rolecheck').change(function(e) {
    var action = this.checked;

    var $t = $(this);

    var user = $t.attr('user');
    var role = $t.attr('role');

    $.postjson('/user/api/rolechange', {user: user, role: role, 'action': action})
        .fail(function()    {
            var verb = action ? "adding" : "removing";
            flash('Server error '+verb+' '+role+' for '+user, 'danger');
            $t.prop("checked", !$t.prop("checked"));
        })
        .done(function()    {
            var msg = (action ? "Added role " + role + ' to' : "Removed role " + role + ' from') +
                        ' user ' + user;
            flash(msg, action ? 'success' : 'info');
        });
});

$('.checkbox-inline').equalwidth();
