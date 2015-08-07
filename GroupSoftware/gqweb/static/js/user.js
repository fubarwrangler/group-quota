
$('.aj_rmuser').click(function (e) {
    var $jqthis = $(this);
    var user = $jqthis.attr('name');
    var prompt = "Are you sure you want to remove " + user + "?";
    bootbox.confirm(prompt, function(result) {
        if(!result) { return; }

        $.postjson('/user/api/remove', {user: user})
            .done(function(result) {
                $('#ur_' + user).remove();
                flash(result.responseText, 'warning');
            })
            .fail(function(result) {
                flash(result.responseText, 'danger');
            });
        return true;
    });
});


$('.aj_active').on('switchChange.bootstrapSwitch', function(event, state) {
    var $jqthis = $(this);
    var user = $jqthis.attr('user');
    var data = {'user': user, 'active': state ? 'on' : 'off'};
    $.postjson('/user/api/activate', data)
        .fail(function(response) {
            flash(response.responseText, 'danger');
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
        .fail(function(result)    {
            var verb = action ? "adding" : "removing";
            flash('Server error '+verb+' '+role+' for '+user, 'danger');
            console.log(result);
            $t.prop("checked", !$t.prop("checked"));
        })
        .done(function()    {
            var msg = (action ? "Added role " + role + ' to' : "Removed role " + role + ' from') +
                        ' user ' + user;
            flash(msg, action ? 'success' : 'warning');
        });
});

$('.checkbox-inline').equalwidth();
