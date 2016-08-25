/*
 * @constructor
 */
function FileDetailView() {
    "use strict";

    this.$add_comment_buttons = $('.add-comment');
    this.$view_comments_buttons = $('.view-comments');
    this.$view_comments_modal = $('#modal-view-comments');

    /*
     * Constructor
     */
    this.construct = function() {
        this.setUpAddCommentButtons();

        this.setUpViewCommentsModal();
        this.setUpViewCommentsButtons();
    };

    /*
     * Get the data from the form and send an AJAX request
     * to post the comment.
     */
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

    /*
     * Open up the comment list modal.
     */
    this.openModalForComments = function(msgid, data) {
        // Populate msgid header
        var comment_msgid = this.$view_comments_modal.find('.comment-msgid');
        comment_msgid.empty();
        comment_msgid.append(msgid);
        // Populate comments list
        var comments_list = this.$view_comments_modal.find('.comments-list');
        comments_list.empty();

        if (data.length > 0) {
            for (var i=0; i < data.length; i++) {
                comments_list.append('<li>'+data[i]['body']+'</li>');
            }
        }
        else {
            comments_list.append('<li>No comments found for this message</li>');
        }

        this.$view_comments_modal.show();

        $(window).on('click', function(e) {
            if (e.target == this.$view_comments_modal) {
                this.$view_comments_modal.style.display = 'none';
            }
        });
    };

    /*
     * Sets up the 'view comments' modal
     */
    this.setUpViewCommentsModal = function() {
        var closeButton = this.$view_comments_modal.find('.close');
        closeButton.on('click', $.proxy(function() {
            this.$view_comments_modal.hide();
            //this.$view_comments_modal.style.display = "none";
        }, this));
    };

    /*
     * Set up a single instance of an 'add comment' button with its form.
     */
    this.setUpOneAddCommentButton = function(i, btn) {
        var commentform_id = $(btn).data('formid');
        var commentform = $('#' + commentform_id);
        commentform.on('submit', $.proxy(this.postComment, this));

        $(btn).on('click', $.proxy(function(e) {
            commentform.toggle();
        }, this));
    };

    /*
     * Set up all 'add comment' buttons.
     */
    this.setUpAddCommentButtons = function() {
        this.$add_comment_buttons.each($.proxy(this.setUpOneAddCommentButton, this));
    };

    this.fetchComments = function(url, msgid) {
        $.ajax({
            url: url,
            type: 'GET',
            success: $.proxy(function(data) {
                this.openModalForComments(msgid, data);
                //$.proxy(this.openModalForComments, this, data);
            }, this),
            error: $.proxy(function(data) {
                console.log("Error!");
                console.log(data);
            }, this)
        });
    };

    /*
     * Set up a single instance of a 'view comment' button.
     */
    this.setUpOneViewCommentsButton = function(i, btn) {
        var url = $(btn).data('url');
        var msgid = $(btn).data('msgid');

        $(btn).on('click', $.proxy(this.fetchComments, this, url, msgid));
    };

    /*
     * Set up all 'view comments' buttons.
     */
    this.setUpViewCommentsButtons = function() {
        this.$view_comments_buttons.each($.proxy(this.setUpOneViewCommentsButton, this));
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
