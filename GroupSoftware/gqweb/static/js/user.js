/**********************************************************/
/* Handle AJAX calls for the live-updating user-edit form */
/**********************************************************/

/* Remove a user if the 'x' is clicked, after confirmation box */
$('.aj_rmuser').click(function (e) {
    var $jqthis = $(this);
    var user = $jqthis.attr('name');
    var prompt = "Are you sure you want to remove " + user + "?";
    bootbox.confirm(prompt, function(result) {
        if(!result) { return; }

        $.postjson('/user/api/remove', {user: user})
            .done(function(data) {
                $('#ur_' + user).remove();
                flash(data, 'warning');
            })
            .fail(function(result) {
                flash(result.responseText, 'danger');
            });
        return true;
    });
});


/* Activate / De-activate a user if the switch is toggled */
$('.aj_active').on('switchChange.bootstrapSwitch', function(event, state) {
    var $jqthis = $(this);
    var user = $jqthis.attr('user');
    var data = {'user': user, 'active': state ? 'on' : 'off'};
    $.postjson('/user/api/activate', data)
        .fail(function(result) {
            flash(result.responseText, 'danger');
            $jqthis.bootstrapSwitch('toggleState', true);
        })
        .done(function() {
            var msg = (state ? "Activated" : "Deactivated") + ' user ' + user;
            flash(msg, state? 'success' : 'warning');
        });
});


/* Add/Remove a role from a user on checkbox-toggle */
$('.aj_rolecheck').change(function(e) {
    var action = this.checked;

    var $t = $(this);

    var user = $t.attr('user');
    var role = $t.attr('role');

    $.postjson('/user/api/rolechange', {user: user, role: role, 'action': action})
        .fail(function(result)    {
            $t.prop("checked", !$t.prop("checked"));
            flash(result.responseText, 'danger');
        })
        .done(function(data)    {
            console.log(data);
            flash(data, action ? 'success' : 'warning');
        });
});

/* Equalize checkboxes so they wrap nicely */
$('.checkbox-inline').equalwidth();
