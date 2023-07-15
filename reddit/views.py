from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponseBadRequest, Http404, \
    HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.template.defaulttags import register
from django.urls import reverse

from reddit.forms import SubmissionForm
from reddit.models import Submission, Comment, Vote
from reddit.utils.helpers import post_only
from users.models import RedditUser



@register.filter
def get_item(dictionary, key):  # pragma: no cover
    """
    Needed because there's no built in .get in django templates
    when working with dictionaries.

    :param dictionary: python dictionary
    :param key: valid dictionary key type
    :return: value of that key or None
    """
    return dictionary.get(key)


def frontpage(request):
    """
    Serves frontpage and all additional submission listings
    with maximum of 25 submissions per page.
    """
    # TODO: Serve user votes on submissions too.

    all_submissions = Submission.objects.order_by('-score').all()
    paginator = Paginator(all_submissions, 25)

    page = request.GET.get('page', 1)
    try:
        submissions = paginator.page(page)
    except PageNotAnInteger:
        raise Http404
    except EmptyPage:
        submissions = paginator.page(paginator.num_pages)

    submission_votes = {}

    if request.user.is_authenticated:
        for submission in submissions:
            try:
                vote = Vote.objects.get(
                    vote_object_type=submission.get_content_type(),
                    vote_object_id=submission.id,
                    user=RedditUser.objects.get(user=request.user))
                submission_votes[submission.id] = vote.value
            except Vote.DoesNotExist:
                pass

    return render(request, 'public/frontpage.html', {'submissions'     : submissions,
                                                     'submission_votes': submission_votes})


def comments(request, thread_id=None):

    this_submission = get_object_or_404(Submission, id=thread_id)

    thread_comments = Comment.objects.filter(submission=this_submission)
    
    sub_vote_value = None
    comment_votes = {}


    if request.user.is_authenticated and request.user == this_submission.author.user:
        context = {
          'submission': this_submission,
          'comments': thread_comments,
          'comment_votes': comment_votes,
          'sub_vote': sub_vote_value,
          'can_edit': True,
        }
    else:
        context = {
          'submission': this_submission,
          'comments': thread_comments,
          'comment_votes': comment_votes,
          'sub_vote': sub_vote_value,
          'can_edit': False,
        }

    return render(request, 'public/comments.html', context)

def edit_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

    # Check if the user is the author of the submission
    if request.user != submission.author.user:
        return redirect('public:comments', thread_id=submission.id)
    
    if request.method == 'POST':
        form = SubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            form.save()
            messages.success(request, "Submission edited successfully")
            return redirect('thread', thread_id=submission_id)
    else:
        form = SubmissionForm(instance=submission)

    context = {
        'form': form,
        'submission': submission,
    }

    return render(request, 'private/edit_post.html', context)

@post_only
def post_comment(request):
    if not isinstance(request.user, User):
        return JsonResponse({'msg': "You need to log in to post new comments."})

    parent_type = request.POST.get('parentType', None)
    parent_id = request.POST.get('parentId', None)
    raw_comment = request.POST.get('commentContent', None)

    if not all([parent_id, parent_type]) or \
            parent_type not in ['comment', 'submission'] or \
        not parent_id.isdigit():
        return HttpResponseBadRequest()

    if not raw_comment:
        return JsonResponse({'msg': "You have to write something."})
    author = RedditUser.objects.get(user=request.user)
    parent_object = None
    try:  # try and get comment or submission we're voting on
        if parent_type == 'comment':
            parent_object = Comment.objects.get(id=parent_id)
        elif parent_type == 'submission':
            parent_object = Submission.objects.get(id=parent_id)

    except (Comment.DoesNotExist, Submission.DoesNotExist):
        return HttpResponseBadRequest()

    comment = Comment.create(author=author,
                             raw_comment=raw_comment,
                             parent=parent_object)

    comment.save()
    return JsonResponse({'msg': "Your comment has been posted."})


@post_only
def vote(request):
    # The type of object we're voting on, can be 'submission' or 'comment'
    vote_object_type = request.POST.get('what', None)

    # The ID of that object as it's stored in the database, positive int
    vote_object_id = request.POST.get('what_id', None)

    # The value of the vote we're writing to that object, -1 or 1
    # Passing the same value twice will cancel the vote i.e. set it to 0
    new_vote_value = request.POST.get('vote_value', None)

    # By how much we'll change the score, used to modify score on the fly
    # client side by the javascript instead of waiting for a refresh.
    vote_diff = 0

    if not isinstance(request.user, User):
        return HttpResponseForbidden()
    else:
        user = RedditUser.objects.get(user=request.user)

    try:  # If the vote value isn't an integer that's equal to -1 or 1
        # the request is bad and we can not continue.
        new_vote_value = int(new_vote_value)

        if new_vote_value not in [-1, 1]:
            raise ValueError("Wrong value for the vote!")

    except (ValueError, TypeError):
        return HttpResponseBadRequest()

    # if one of the objects is None, 0 or some other bool(value) == False value
    # or if the object type isn't 'comment' or 'submission' it's a bad request
    if not all([vote_object_type, vote_object_id, new_vote_value]) or \
            vote_object_type not in ['comment', 'submission']:
        return HttpResponseBadRequest()

    # Try and get the actual object we're voting on.
    try:
        if vote_object_type == "comment":
            vote_object = Comment.objects.get(id=vote_object_id)

        elif vote_object_type == "submission":
            vote_object = Submission.objects.get(id=vote_object_id)
        else:
            return HttpResponseBadRequest()  # should never happen

    except (Comment.DoesNotExist, Submission.DoesNotExist):
        return HttpResponseBadRequest()

    # Try and get the existing vote for this object, if it exists.
    try:
        vote = Vote.objects.get(vote_object_type=vote_object.get_content_type(),
                                vote_object_id=vote_object.id,
                                user=user)

    except Vote.DoesNotExist:
        # Create a new vote and that's it.
        vote = Vote.create(user=user,
                           vote_object=vote_object,
                           vote_value=new_vote_value)
        vote.save()
        vote_diff = new_vote_value
        return JsonResponse({'error'   : None,
                             'voteDiff': vote_diff})

    # User already voted on this item, this means the vote is either
    # being canceled (same value) or changed (different new_vote_value)
    if vote.value == new_vote_value:
        # canceling vote
        vote_diff = vote.cancel_vote()
        if not vote_diff:
            return HttpResponseBadRequest(
                'Something went wrong while canceling the vote')
    else:
        # changing vote
        vote_diff = vote.change_vote(new_vote_value)
        if not vote_diff:
            return HttpResponseBadRequest(
                'Wrong values for old/new vote combination')

    return JsonResponse({'error'   : None,
                         'voteDiff': vote_diff})


@login_required
def submit(request):
    """
    Handles new submission.. submission.
    """
    submission_form = SubmissionForm()

    if request.method == 'POST':
        submission_form = SubmissionForm(request.POST)
        if submission_form.is_valid():
            submission = submission_form.save(commit=False)
            submission.generate_html()

            # Check if the user is logged in
            if request.user.is_authenticated:
                user = request.user
                
                # Check if the username is in the database
                try:
                    redditUser = RedditUser.objects.get_or_create(user=user)
                except RedditUser.DoesNotExist:
                    user = User.objects.create_user(
                        username=submission.author_name,
                        password='password'
                    )
                    redditUser = RedditUser.objects.create(user=user)

                submission.author = redditUser[0]
                submission.author_name = user.username

            submission.save()
            messages.success(request, 'Submission created')
            return redirect('/comments/{}'.format(submission.id))

    return render(request, 'public/submit.html', {'form': submission_form})
