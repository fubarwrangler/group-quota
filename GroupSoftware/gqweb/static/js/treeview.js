/* Toggle correct classes for highlight event on hover-over link */
$('div.parent').hover(function(event)    {
    $(this).children('span').toggleClass('fnt-bold').toggleClass('text-muted');
    $(this.nextElementSibling).find('div.treediv').andSelf().toggleClass('sel');
    $(this.nextElementSibling).find('div:not(.treediv)').toggleClass('childedit');
    $(this.nextElementSibling).children('div.nonparent,div.parent').toggleClass('willedit').toggleClass('childedit');
    $(this).toggleClass('editparent');
    $('#colorkey').toggleClass('noseeme');
});


/* Equalize the widths of the divs on the same level for the tree on pageload */
$(function()    {
    $('div.treediv').each(function() {
        var $direct_children = $(this).children('.parent,.nonparent');
        $direct_children.equalwidth(20);
    });
});
