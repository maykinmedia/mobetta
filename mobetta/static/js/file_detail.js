/*
 * @constructor
 */
function FileDetailView() {
    "use strict";

    this.$comment_buttons = $('.add-comment');

    this.construct = function() {
        this.setUpCommentButtons();
    };

    this.postComment = function(e) {
        e.preventDefault();
        var submiturl = $(e.target).data('submiturl');
        var data = $(e.target).serialize();
        $.ajax({
            url: submiturl,
            type: 'POST',
            data: data,
            success: function(data) {
                if (data['status'] === 'success') {
                    // Hide form and show success message
                    console.log("Success!");
                    var commentcounter = $(e.target).siblings('.comment-count');
                    commentcounter.empty();
                    commentcounter.append(data['new_comment_count']);
                    $(e.target).hide();
                }
                else if (data['status'] === 'invalid') {
                    // Show form errors
                    var errorbox = $(e.target).find('.errorlist');
                    errorbox.empty();

                    for (var i=0; i < data['errors']['body'].length; i++) {
                        errorbox.append(data['errors']['body'][i]);
                    }
                }
            }
        });
    };

    this.setUpOneCommentButton = function(i, btn) {
        var commentform_id = $(btn).data('formid');
        var commentform = $('#' + commentform_id);
        commentform.on('submit', $.proxy(this.postComment, this));

        $(btn).on('click', $.proxy(function(e) {
            commentform.toggle();
        }, this));
    }

    this.setUpCommentButtons = function() {
        this.$comment_buttons.each($.proxy(this.setUpOneCommentButton, this));
    };


    this.construct();
}

function fileDetailMain() {
    "use strict";
    new FileDetailView()
}

(function ($, undefined) {
    $(function() {
        fileDetailMain();
    });
})(window.jQuery);
