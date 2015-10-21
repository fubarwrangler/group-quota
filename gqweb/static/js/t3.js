/**************************************************************/
/* Handle Form Populating and AJAX calls for modal T3 Editing */
/**************************************************************/

$('#editInst').on('show.bs.modal', function (event) {
  var button = $(event.relatedTarget);
  var modal = $(this);

  modal.find('#in-fullname').val(button.data('fullname'));
  modal.find('#in-name').val(button.data('name'));
  modal.find('#in-origname').val(button.data('name'));
  modal.find('#defaultgroup').val(button.data('group')).text(button.data('group'));
  $('.selectpicker').selectpicker('refresh');
});
