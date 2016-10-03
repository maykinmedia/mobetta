/*
 * @constructor
 */
function FileDetailView() {
    "use strict";

    this.$add_comment_buttons = $('.add-comment');
    this.$add_comment_modal = $('#modal-add-comment');

    this.$view_comments_buttons = $('.view-comments');
    this.$view_comments_modal = $('#modal-view-comments');

    this.$show_suggestion_buttons = $('.show-suggestion');

    /*
     * Constructor
     */
    this.construct = function() {
        this.setUpAddCommentButtons();
        this.setUpAddCommentModal();

        this.setUpViewCommentsModal();
        this.setUpViewCommentsButtons();

        this.setUpShowSuggestionButtons();
    };

    /*
     * Get the data from the form and send an AJAX request
     * to post the comment.
     */
    this.postComment = function(e) {
        e.preventDefault();
        var submiturl = $(e.target).data('submiturl');
        var formprefix = $(e.target).data('form-prefix');
        var data = $(e.target).serialize();

        $.ajax({
            url: submiturl,
            type: 'POST',
            data: data,
            success: $.proxy(function(data) {
                // Hide modal and show success message
                var commentcounter = $('#id_'+formprefix+'-comment-count');
                commentcounter.empty();
                commentcounter.append(data['comment_count']);

                this.$add_comment_modal.hide();
            }, this),

            error: $.proxy(function(data) {
                // Show form errors
                var errorbox = $(e.target).find('.errorlist');
                errorbox.empty();

                for (var i=0; i < data.responseJSON['body'].length; i++) {
                    errorbox.append(data.responseJSON['body'][i]);
                }
            }, this),
        });
    };

    /*
     * Open up the comment list modal.
     */
    this.openViewCommentsModal = function(msgid, msghash, data) {
        // Populate msgid header
        var comment_msgid = this.$view_comments_modal.find('.comment-msgid');
        comment_msgid.empty();
        comment_msgid.append(msgid);

        // Populate comments list
        var comments_list = this.$view_comments_modal.find('.comments-list');
        comments_list.empty();

        if (data.length > 0) {
            for (var i=0; i < data.length; i++) {
                comments_list.append('<li><span class="comment-author">['+data[i]['user_name']+']</span> '+data[i]['body']+'</li>');
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


    this.openAddCommentModal = function(file_pk, msgid, msghash, formprefix) {
        // Clear the message body
        var body_input = this.$add_comment_modal.find('textarea[name="body"]')
        body_input.val('');

        // Add the form prefix to the form data
        this.$add_comment_modal.find('.comment-form').data('form-prefix', formprefix);

        // Populate the hidden fields with file_pk and msghash
        var msghashfield = this.$add_comment_modal.find('input[name="msghash"]');

        msghashfield.val(msghash);

        this.$add_comment_modal.show();
    };

    /*
     * Sets up the 'add comment' modal
     */
    this.setUpAddCommentModal = function() {
        var closeButton = this.$add_comment_modal.find('.close');
        closeButton.on('click', $.proxy(function() {
            this.$add_comment_modal.hide();
        }, this));

        var commentform = this.$add_comment_modal.find('.comment-form');
        commentform.on('submit', $.proxy(this.postComment, this));
    };

    /*
     * Sets up the 'view comments' modal
     */
    this.setUpViewCommentsModal = function() {
        var closeButton = this.$view_comments_modal.find('.close');
        closeButton.on('click', $.proxy(function() {
            this.$view_comments_modal.hide();
        }, this));
    };


    /*
     * Set up a single instance of an 'add comment' button with its form.
     */
    this.setUpOneAddCommentButton = function(i, btn) {
        var file_pk = $(btn).data('filepk');
        var msgid = $(btn).data('msgid');
        var msghash = $(btn).data('msghash');
        var formprefix = $(btn).data('form-prefix');

        $(btn).on('click', $.proxy(function(e) {
            this.openAddCommentModal(file_pk, msgid, msghash, formprefix);
        }, this));
    };

    /*
     * Set up all 'add comment' buttons.
     */
    this.setUpAddCommentButtons = function() {
        this.$add_comment_buttons.each($.proxy(this.setUpOneAddCommentButton, this));
    };

    this.fetchComments = function(url, msgid, msghash) {
        $.ajax({
            url: url,
            type: 'GET',
            success: $.proxy(function(data) {
                this.openViewCommentsModal(msgid, msghash, data);
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
        var msghash = $(btn).data('msghash');
        var msgid = $(btn).data('msgid');

        $(btn).on('click', $.proxy(this.fetchComments, this, url, msgid, msghash));
    };

    /*
     * Set up all 'view comments' buttons.
     */
    this.setUpViewCommentsButtons = function() {
        this.$view_comments_buttons.each($.proxy(this.setUpOneViewCommentsButton, this));
    };

    /*
     * Fetch a translation suggestion from the API.
     */
    this.fetchSuggestion = function(url, formprefix) {
        var suggest_button = $('button.show-suggestion[data-form-prefix="'+formprefix+'"]')
        suggest_button.empty();
        suggest_button.append("Fetching...");

        $.ajax({
            url: url,
            type: 'GET',
            success: $.proxy(function(data) {
                var suggestion_span = $('#id_'+formprefix+'-auto-suggestion')
                suggestion_span.empty();
                suggestion_span.append(data['suggestion']);
                suggest_button.hide();
            }, this),
            error: $.proxy(function(data) {
                var suggestion_error_span = $('#id_'+formprefix+'-auto-suggestion-error')
                suggestion_error_span.empty();
                suggestion_error_span.append("An error occurred.");
                suggest_button.hide();
            }, this),
        });
    };

    /*
     * Set up a 'show suggestion' button.
     */
    this.setUpOneShowSuggestionButton = function(i, btn) {
        var url = $(btn).data('url');
        var formprefix = $(btn).data('form-prefix');

        $(btn).on('click', $.proxy(this.fetchSuggestion, this, url, formprefix));
    };

    /*
     * Set up all 'show suggestion' buttons.
     */
    this.setUpShowSuggestionButtons = function() {
        this.$show_suggestion_buttons.each($.proxy(this.setUpOneShowSuggestionButton, this));
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
