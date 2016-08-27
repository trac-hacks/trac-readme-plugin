jQuery(document).ready(function($) {
  $('#preview').each(function() {
    $(this).html(marked( $(this).children('pre').first().text() ));
  });
  $('.markdown').each(function() {
    $(this).html(marked( $(this).children('pre').first().html() ));
  });
});
