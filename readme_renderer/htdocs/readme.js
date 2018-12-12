jQuery(function($) {
  $('#preview.searchable').each(function() {
    $(this).html(marked( $(this).children('pre').first().text() ));
  });
  $('.markdown').each(function() {
    $(this).html(marked( $(this).children('pre').first().text() ));
  });
});
