import json
from email.headerregistry import Group

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import DetailView
from pytils.translit import slugify
from rest_framework import status, generics
from rest_framework.generics import ListAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from constants import SERVER_NAME
from parsing.forms import UserForm, UserCreateForm, UserDetailForm, QueryForm, ReviewForm, PlaceForm, TagForm, \
    QueryContentForm, ReviewTypeForm, CityForm, ServiceForm
from parsing.models import Query, Place, Review, Tag, ReviewType, ReviewPart, FAQ, FAQQuestion, UniqueReview, City, \
    Service, CityService
from parsing.serializers import QuerySerializer, PlaceSerializer, PlaceMinSerializer, \
    TagSerializer, \
    ReviewSerializer, ReviewTypeSerializer
from parsing.tasks import startParsing, generate_file, uniqueize_place_reviews_task, uniqueize_query_reviews_task, \
    uniqueize_text_task, cities_img_parser
from parsing.utils import show_form_errors, has_group, get_paginator, sumextract, uniqueize_text


def index(request):
    user = request.user
    if user.is_authenticated:
        queries = Query.objects.filter(user=user)
        places = Place.objects.filter(queries__query__user=user)
        return render(request, 'parsing/index.html', {'user': user, 'queries': queries, 'places': places})
    return render(request, 'parsing/index.html')


@login_required()
def start_parser(request, city_slug, service_slug):
    city_service = CityService.objects.filter(city__slug=city_slug, service__slug=service_slug).first()
    return redirect(city_service.get_absolute_url())


@login_required()
def start_custom_parser(request, city_slug, service_slug):
    city_service = get_object_or_404(CityService, city__slug=city_slug, service__slug=service_slug)
    if request.method == 'POST':
        form = QueryForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            search_text = cd['name']
            not_all = cd['not_all']

            if not_all:
                query_page = cd['page']
                try:
                    query_page = int(query_page)
                except:
                    query_page = 1
            else:
                query_page = None
            try:
                if CityService.objects.filter(status='wait').exists():
                    messages.warning(request, 'Please wait, there are tasks in the queue')
                else:
                    city_service.search_text = search_text
                    city_service.page = query_page
                    city_service.status = 'wait'
                    city_service.save()
                    messages.success(request, 'Parsing started')
                    startParsing.delay(query_name=search_text, city_service_id=city_service.id, pages=query_page)
            except Exception as e:
                print(e.__class__.__name__)
                city_service.status = 'error'
                city_service.save()
        return redirect(city_service.get_absolute_url())
    return render(request, 'parsing/city_service/start_parser.html', {
        'city_service': city_service
    })


#
# @login_required()
# def query_add(request):
#     if request.method == 'POST':
#         form = QueryForm(request.POST)
#         if form.is_valid():
#             cd = form.cleaned_data
#             query_name = cd['name']
#             not_all = cd['not_all']
#
#             if not_all:
#                 query_page = cd['page']
#                 try:
#                     query_page = int(query_page)
#                 except:
#                     query_page = 1
#             else:
#                 query_page = None
#
#             print(query_name, not_all, query_page)
#
#             query = Query(user=request.user, name=query_name, page=query_page, status='wait')
#             query.save()
#             query_id = query.id
#
#             slug = slugify(query_name + '-' + str(query_id))
#             query.slug = slug
#             query.save()
#
#             try:
#                 startParsing.delay(query_name=query_name, query_id=query_id, pages=query_page)
#             except Exception as e:
#                 print(e.__class__.__name__)
#                 query.status = 'error'
#                 query.save()
#             return redirect('/')
#         else:
#             show_form_errors(request, form.errors)
#             return render(request, 'parsing/query/add.html')
#     return render(request, 'parsing/query/add.html')


def get_sorted_places(city_service):
    places = Place.objects.filter(city_service=city_service)
    if city_service.sorted:
        places = places.order_by('position')
    else:
        places = places.order_by('-rating', '-rating_user_count')
    return places


def update_place_position(place_id, position):
    place = get_object_or_404(Place, id=place_id)
    place.position = position
    place.save()


@login_required()
def query_rating_edit(request, slug):
    query = get_object_or_404(Query, slug=slug)
    # query.sorted = False
    # query.save()
    # places = get_sorted_places(query).update(position=None)
    places = get_sorted_places(query)
    if request.method == 'POST':
        query.sorted = True
        query.save()
        places.update(position=None)
        data = json.loads(request.body.decode('utf-8'))['data']
        for i in data:
            place_id = i['place_id']
            position = i['index']
            update_place_position(place_id, position)
        messages.success(request, 'Success')
        return JsonResponse({'message': 'succcess'})
    return render(request, 'parsing/query/edit_rating.html', {'query': query, 'places': places})


@login_required()
def query_all(request):
    if not has_group(request.user, 'SuperAdmin'):
        return redirect('parsing:index')
    users = User.objects.exclude(queries=None)
    selected_user = None
    try:
        username = request.GET.get('user')
        user = get_object_or_404(User, username=username)
        queries = Query.objects.filter(user=user)
        selected_user = user
    except:
        queries = Query.objects.all()
    queries = get_paginator(request, queries, 20)
    return render(request, 'parsing/query/all.html',
                  {'queries': queries, 'users': users, 'selected_user': selected_user})


@login_required()
def query_list(request):
    user = request.user
    if not has_group(user, 'Admin'):
        return redirect('parsing:index')

    queries = Query.objects.filter(user=user)
    queries = get_paginator(request, queries, 20)
    return render(request, 'parsing/query/list.html', {'queries': queries})


@login_required()
def city_service_list(request):
    city_services = CityService.objects.exclude(places=None)
    city_services = get_paginator(request, city_services)
    return render(request, 'parsing/city_service/list.html', {
        'city_services': city_services,
    })


@login_required()
def query_detail(request, slug):
    query = Query.objects.filter(slug=slug).first()
    # places = query.places.all()
    places = Place.objects.filter(queries__query=query).all()
    # print(places)
    sort_type = None
    if request.GET:
        sort_type = request.GET.get('sorted')
        if sort_type == 'rating_gt':
            places = places.order_by('rating')
        elif sort_type == 'rating_lt':
            places = places.order_by('-rating')
    places = get_paginator(request, places, 20)
    return render(request, 'parsing/query/detail.html', {'query': query, 'places': places, 'sort_type': sort_type})


@login_required()
def query_edit(request, slug):
    query = get_object_or_404(Query, slug=slug)
    if request.method == 'POST':
        form = QueryContentForm(request.POST, instance=query)
        if form.is_valid():
            query = form.save()
            messages.success(request, 'Description changed')
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('parsing:places', args=[query.slug]))
    tags = Tag.objects.all()
    return render(request, 'parsing/query/edit.html', {'query': query, 'tags': tags})


@login_required()
def query_edit_access(request, slug):
    query = get_object_or_404(Query, slug=slug)
    query.access = not (query.access)
    query.save()
    return redirect(reverse('parsing:queries'))


def get_faq_questions(query_or_place):
    faq = query_or_place.faq
    if not faq:
        faq = FAQ()
        faq.save()
        query_or_place.faq = faq
        query_or_place.save()
    questions = query_or_place.faq.questions.all()
    return questions


def save_questions(query_or_place, questions_and_answers):
    faq = query_or_place.faq
    faq.questions.all().delete()
    for q in questions_and_answers:
        question = FAQQuestion(question=q, answer=questions_and_answers[q])
        question.save()
        faq.questions.add(question)
    faq.save()


@login_required()
def query_edit_faq(request, slug):
    query = get_object_or_404(Query, slug=slug)
    if request.method == 'POST':
        post = dict(request.POST)
        questions_and_answers = dict(zip(post['questions'], post['answers']))
        questions = get_faq_questions(query)
        save_questions(query, questions_and_answers)
        messages.success(request, 'FAQ updated')
        return redirect(reverse('parsing:places', args=[query.slug]))
    return render(request, 'parsing/query/edit_faq.html', {'query': query})


@login_required()
def query_delete(request, pk):
    query = Query.objects.filter(pk=pk).first()
    if query and query.user == request.user or has_group(request.user, 'SuperAdmin'):
        query.delete()
        messages.success(request, f'Query "{query.name}" deleted')
    return redirect('parsing:query_list')


@login_required()
def query_file_generate(request, pk):
    query = Query.objects.filter(pk=pk).first()
    if not query:
        return redirect(query.get_absolute_url)
    # places = query.places.all()
    places = Place.objects.filter(queries__query=query).all()
    slug = query.slug
    print(slug)
    file = generate_file(slug, places)
    return file


def queries(request):
    if has_group(request.user, 'Redactor'):
        queries = Query.objects.all()
    else:
        queries = Query.objects.filter(access=True)
    try:
        search = request.GET.get('search')
        if search != '':
            queries = queries.filter(name__icontains=search)
    except:
        search = None
    try:
        tags_checked = request.GET.getlist('tags')
        if tags_checked:
            tags_checked = [int(i) for i in tags_checked]
            queries = queries.filter(tags__id__in=tags_checked).distinct()
    except:
        tags_checked = []
    queries = get_paginator(request, queries, 16)
    tags = Tag.objects.all()
    return render(request, 'parsing/query/queries.html',
                  {'queries': queries, 'tags': tags, 'search': search, 'tags_checked': tags_checked})


@login_required()
def tag_queries(request, pk):
    tag = get_object_or_404(Tag, id=pk)
    queries = tag.queries.all().distinct()
    queries = get_paginator(request, queries, 16)
    return render(request, 'parsing/tag/queries.html', {'tag': tag, 'queries': queries})


def add_path_for_tag(request, form, tag):
    cd = form.cleaned_data
    name = cd['name']
    path = slugify(name)
    if not Tag.objects.filter(path=path).exists():
        tag.path = path
        tag.save()
        return True
    messages.error(request, 'A tag with this path already exists')
    return False


@login_required()
def tags(request):
    tags = Tag.objects.all()
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save(commit=False)
            if add_path_for_tag(request, form, tag):
                messages.success(request, 'Tag created')
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('parsing:tags'))
    return render(request, 'parsing/tag/list.html', {'tags': tags})


@login_required()
def tag_edit(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            tag = form.save(commit=False)
            tag.save()
            messages.success(request, 'Tag changed')
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('parsing:tags'))
    return render(request, 'parsing/tag/edit.html', {'tag': tag})


@login_required()
def tag_delete(request, path):
    tag = get_object_or_404(Tag, path=path)
    tag.delete()
    messages.success(request, 'Tag deleted')
    return redirect(reverse('parsing:tags'))


def review_types(request):
    review_types = ReviewType.objects.all()
    if request.method == 'POST':
        form = ReviewTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Review type created')
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('parsing:review_types'))
    return render(request, 'parsing/admin_dashboard/review_type/list.html', {'review_types': review_types})


def review_type_edit(request, pk):
    review_type = get_object_or_404(ReviewType, pk=pk)
    if request.method == 'POST':
        form = ReviewTypeForm(request.POST, instance=review_type)
        if form.is_valid():
            form.save()
            messages.success(request, 'Review type changed')
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('parsing:review_types'))
    return render(request, 'parsing/admin_dashboard/review_type/edit.html', {'review_type': review_type})


def places_to_sorted_letters(places):
    places_letter = {

    }
    for i in places:
        first_letter = i.name[0]
        if first_letter in places_letter:
            places_letter[first_letter]['places'].append(i)
        else:
            places_letter[first_letter] = {
                'letter': first_letter,
                'places': [i]
            }
    letters = list(places_letter.keys())
    letters = sorted(letters)
    return {
        'places_letter': places_letter,
        'letters': letters
    }


def places(request, slug):
    query = Query.objects.filter(slug=slug).first()
    if not query:
        return redirect('parsing:index')
    places = get_sorted_places(query)
    top_places = places[:20]
    places_and_letters = places_to_sorted_letters(places)
    return render(request, 'parsing/query/places.html', {'query': query,
                                                         'top_places': top_places,
                                                         'places': places,
                                                         'places_letter': places_and_letters['places_letter'],
                                                         'letters': places_and_letters['letters']})


@login_required()
def places_copy_code(request, slug):
    query = get_object_or_404(Query, slug=slug)
    places = get_sorted_places(query)
    top_places = places[:20]
    places_and_letters = places_to_sorted_letters(places)
    return render(request, 'parsing/query/places_copy_code.html', {'query': query,
                                                                   'top_places': top_places,
                                                                   'places': places,
                                                                   'places_letter': places_and_letters['places_letter'],
                                                                   'letters': places_and_letters['letters']})


@login_required()
def places_copy(request, slug):
    query = Query.objects.filter(slug=slug).first()
    if not query:
        return redirect('parsing:index')
    places = get_sorted_places(query)
    top_places = places[:20]
    places_and_letters = places_to_sorted_letters(places)
    return render(request, 'parsing/query/places_copy.html', {'query': query,
                                                              'top_places': top_places,
                                                              'places': places,
                                                              'places_letter': places_and_letters['places_letter'],
                                                              'letters': places_and_letters['letters']})


# @login_required()
# def places_copy_code(request, slug):
#     query = Query.objects.filter(slug=slug).first()
#     if not query:
#         return redirect('parsing:index')
#     places = get_sorted_places(query)
#     top_places = places[:20]
#     places_and_letters = places_to_sorted_letters(places)
#
#     return render(request, 'parsing/query/places_copy_code.html', {'query': query,
#                                                               'top_places': top_places,
#                                                               'places': places,
#                                                               'places_letter': places_and_letters['places_letter'],
#                                                               'letters': places_and_letters['letters']})

def create_or_update_review_types(post, review):
    for i in post:
        if 'review_type' in i:
            review_type_id = int(i.split('_')[-1])
            review_type = ReviewType.objects.filter(pk=review_type_id).first()
            review_part = ReviewPart.objects.update_or_create(review_type=review_type, review=review)[0]
            review_part.rating = int(post[i])
            review_part.save()


def get_place_reviews(request, place):
    my_review = False
    if request.user.is_authenticated:
        reviews = place.reviews.exclude(user=request.user)
        my_review = Review.objects.filter(place=place).filter(user=request.user).first()
    else:
        reviews = place.reviews.all()
    reviews = get_paginator(request, reviews, 10)
    return {'my_review': my_review, 'reviews': reviews}


def query_place_detail(request, query_slug, place_slug):
    query = get_object_or_404(Query, slug=query_slug)
    place = get_object_or_404(Place, slug=place_slug)
    if place.is_redirect and not has_group(request.user, 'Redactor'):
        return redirect(place.redirect)
    reviews = get_place_reviews(request, place)
    return render(request, 'parsing/place/detail.html',
                  {'query': query, 'place': place, 'reviews': reviews['reviews'], 'my_review': reviews['my_review']})


def place_detail(request, slug):
    place = get_object_or_404(Place, slug=slug)
    reviews = get_place_reviews(request, place)
    return render(request, 'parsing/place/detail.html',
                  {'place': place, 'reviews': reviews['reviews'], 'my_review': reviews['my_review']})


@login_required()
def review_create(request, place_slug):
    place = get_object_or_404(Place, slug=place_slug)
    user = request.user
    review_types = ReviewType.objects.all()
    if Review.objects.filter(user=request.user).filter(place=place).first():
        messages.error(request, 'You cannot leave more than one review.')
        return redirect(place.get_absolute_url())
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.place = place
            review.original_text = request.POST['text']
            review.save()
            create_or_update_review_types(request.POST, review)
            messages.success(request, 'Your review has been saved')
        else:
            show_form_errors(request, form.errors)
        return redirect(place.get_absolute_url())
    return render(request, 'parsing/reviews/create.html',
                  {'place': place, 'user': user, 'review_types': review_types})


@login_required()
def place_edit(request, pk):
    place = get_object_or_404(Place, pk=pk)
    if request.method == 'POST':
        form = PlaceForm(request.POST, instance=place)
        if form.is_valid():
            form.save()
            messages.success(request, 'Place changed')
        else:
            show_form_errors(request, form.errors)
        return redirect(place.get_absolute_url())
    return render(request, 'parsing/place/edit.html', {'place': place})


def place_set_description(place):
    reviews = place.reviews.all()[:20]
    text = ''
    for review in reviews:
        text += review.text
    description = sumextract(text, 5)
    place.description = place.name + ' - ' + description
    place.save()


@login_required()
def place_generate_description(request, place_slug):
    place = get_object_or_404(Place, slug=place_slug)
    place_set_description(place)
    messages.success(request, "Description generated")
    return redirect(place.get_absolute_url())


@login_required()
def query_places_generate_description(request, slug):
    query = get_object_or_404(Query, slug=slug)
    places = Place.objects.filter(queries__query=query)
    for place in places:
        place_set_description(place)
    return redirect(reverse('parsing:places', args=[slug]))


@login_required()
def place_edit_faq(request, pk):
    place = get_object_or_404(Place, pk=pk)
    if request.method == 'POST':
        post = dict(request.POST)
        questions_and_answers = dict(zip(post['questions'], post['answers']))
        questions = get_faq_questions(place)
        save_questions(place, questions_and_answers)
        messages.success(request, 'FAQ updated')
        return redirect(place.get_absolute_url())
    return render(request, 'parsing/place/edit_faq.html', {'place': place})


@login_required()
def place_update(request, pk):
    place = Place.objects.filter(pk=pk).first()
    # selenium_query_detail(place_id=place.place_id)
    # updateDetail(place.pk)
    return redirect(place.get_absolute_url())


def generate_slug():
    places = Place.objects.all()
    for place in places:
        place.slug = slugify(f'{place.name}-{str(place.id)}')
        place.save()


@login_required()
def profile(request):
    user = request.user
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            messages.success(request, 'Data changed')
            form.save()
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('parsing:profile'))
    return render(request, 'parsing/user/profile.html', {'user': user})


@login_required()
def public_cabinet(request, username):
    user = get_object_or_404(User, username=username)
    return render(request, 'parsing/user/public_cabinet.html', {'user': user})


@login_required()
def all_reviews(request):
    if not has_group(request.user, 'Redactor'):
        return redirect('parsing:index')
    reviews = Review.objects.all()
    reviews = get_paginator(request, reviews, 10)
    return render(request, 'parsing/reviews/all.html', {'reviews': reviews})


@login_required()
def user_reviews(request, username):
    user = get_object_or_404(User, username=username)
    reviews = user.reviews.all()
    reviews = get_paginator(request, reviews, 12)
    return render(request, 'parsing/user/reviews.html', {'user': user, 'reviews': reviews})


@login_required()
def my_reviews(request):
    user = request.user
    reviews = user.reviews.all()
    reviews = get_paginator(request, reviews, 10)
    return render(request, 'parsing/reviews/reviews.html', {'reviews': reviews})


@login_required()
def review_edit(request, pk):
    review = Review.objects.filter(pk=pk).first()
    if (not review or request.user != review.user) and not has_group(request.user, 'Redactor'):
        return redirect('parsing:my_reviews')
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            review.is_edit = True
            review.original_text = request.POST['text']
            review.save()
            create_or_update_review_types(request.POST, review)
            messages.success(request, 'Review changed')
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('parsing:review_edit', args=[review.id]))

    review_types = ReviewType.objects.filter(reviews__review=review)
    review_parts = ReviewPart.objects.values('review_type', 'rating').filter(review=review)
    print(review_parts)
    return render(request, 'parsing/reviews/review_edit.html',
                  {'review': review, 'review_types': review_types, 'review_parts': review_parts})


@login_required()
def review_uniqueize(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.text = uniqueize_text(review.text)
    review.save()
    return redirect(reverse('parsing:review_edit', args=[review.id]))


@login_required()
def place_reviews_uniqueize(request, pk):
    place = get_object_or_404(Place, pk=pk)
    uniqueize_text_task.delay(place_id=place.id)
    messages.success(request, 'Reviews uniqueize started')
    return redirect(place.get_absolute_url())


@login_required()
def query_reviews_uniqueize(request, slug):
    query = get_object_or_404(Query, slug=slug)
    # uniqueize_text_task.delay(city_service_id=query.id)
    messages.success(request, 'Reviews uniqueize started')
    return redirect(reverse('parsing:places', args=[slug]))


@login_required()
def unique_reviews_list(request):
    unique_reviews = UniqueReview.objects.all().order_by('-pk')
    unique_reviews = get_paginator(request, unique_reviews)
    return render(request, 'parsing/unique_reviews/list.html', {
        'unique_reviews': unique_reviews
    })


def registration(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            group = Group.objects.filter(name='User').first()
            if group:
                user.groups.add(group)
            login(request, user)
            return redirect(reverse('parsing:profile'))
        else:
            show_form_errors(request, form.errors)
    return render(request, 'parsing/user/add.html')


@login_required()
def group_list(request):
    groups = Group.objects.all()
    groups_not_count = User.objects.filter(groups=None).count()
    return render(request, 'parsing/admin_dashboard/group/list.html',
                  {'groups': groups, 'groups_not_count': groups_not_count})


@login_required()
def group_detail(request, pk):
    group = Group.objects.filter(pk=pk).first()
    if group:
        users = group.user_set.all()
        users = get_paginator(request, users, count=12)
        return render(request, 'parsing/admin_dashboard/group/detail.html', {'group': group, 'users': users})
    return redirect('group_list')


@login_required()
def group_not(request):
    users = User.objects.filter(groups=None)
    return render(request, 'parsing/admin_dashboard/group/not.html', {'users': users})


@login_required()
def admin_dashboard(request):
    user = request.user
    if user.is_superuser:
        return render(request, 'parsing/admin_dashboard/dashboard.html')
    return redirect('/')


@login_required()
def user_list(request):
    users = User.objects.all().order_by('-pk')
    users = get_paginator(request, users, 10)
    return render(request, 'parsing/user/list.html', {'users': users})


@login_required()
def user_detail(request, pk):
    if not has_group(request.user, 'Admin'):
        return redirect('parsing:index')
    user = User.objects.filter(pk=pk).first()
    if request.method == 'POST':
        form = UserDetailForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            cd = form.cleaned_data
            group_id = cd['groups']
            group = Group.objects.filter(id__in=group_id).first()
            if group:
                user.groups.clear()
                user.groups.add(group)
            user.save()
            messages.success(request, 'Data changed')
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('parsing:user_detail', args=[user.id]))

    groups = Group.objects.all()
    if user:
        return render(request, 'parsing/user/detail.html', {'user': user, 'groups': groups})
    return redirect('/')


def city_service_create(city=None, service=None):
    cities_and_services = []
    if city:
        services = Service.objects.all()
        if services:
            for service in services:
                if not CityService.objects.filter(city=city, service=service).exists():
                    city_service = CityService(city=city, service=service)
                    cities_and_services.append(city_service)
    elif service:
        cities = City.objects.all()
        if cities:
            for city in cities:
                if not CityService.objects.filter(city=city, service=service).exists():
                    city_service = CityService(city=city, service=service)
                    cities_and_services.append(city_service)
    CityService.objects.bulk_create(cities_and_services)


@login_required()
def city_autocreate(request):
    cities = ['Accomack', 'Albemarle', 'Alexandria', 'Alleghany', 'Amelia', 'Amherst', 'Appomattox', 'Arlington',
              'Augusta', 'Bath', 'Bedford', 'Bedford', 'Bland', 'Botetourt', 'Bristol', 'Brunswick', 'Buchanan',
              'Buckingham', 'Buena_Vista', 'Campbell', 'Caroline', 'Carroll', 'Charles', 'Charlotte', 'Charlottesville',
              'Chesapeake', 'Chesterfield', 'Clarke', 'Colonial_Heights', 'Covington', 'Craig', 'Culpeper',
              'Cumberland', 'Danville', 'Dickenson', 'Dinwiddie', 'Emporia', 'Essex', 'Fairfax', 'Fairfax',
              'Falls_Church', 'Fauquier', 'Floyd', 'Fluvanna', 'Franklin', 'Franklin', 'Frederick', 'Fredericksburg',
              'Galax', 'Giles', 'Gloucester', 'Goochland', 'Grayson', 'Greene', 'Greensville', 'Halifax', 'Hampton',
              'Hanover', 'Harrisonburg', 'Henrico', 'Henry', 'Highland', 'Hopewell', 'Isle_of_Wight', 'James',
              'King_George', 'King_William', 'King_and_Queen', 'Lancaster', 'Lee', 'Lexington', 'Loudoun', 'Louisa',
              'Lunenburg', 'Lynchburg', 'Madison', 'Manassas', 'Manassas_Park', 'Martinsville', 'Mathews',
              'Mecklenburg', 'Middlesex', 'Montgomery', 'Nelson', 'New_Kent', 'Newport_News', 'Norfolk', 'Northampton',
              'Northumberland', 'Norton', 'Nottoway', 'Orange', 'Page', 'Patrick', 'Petersburg', 'Pittsylvania',
              'Poquoson', 'Portsmouth', 'Powhatan', 'Prince_Edward', 'Prince_George', 'Prince_William', 'Pulaski',
              'Radford', 'Rappahannock', 'Richmond', 'Richmond', 'Roanoke', 'Roanoke', 'Rockbridge', 'Rockingham',
              'Russell', 'Salem', 'Scott', 'Shenandoah', 'Smyth', 'Southampton', 'Spotsylvania', 'Stafford', 'Staunton',
              'Suffolk', 'Surry', 'Sussex', 'Tazewell', 'Virginia_Beach', 'Warren', 'Washington', 'Waynesboro',
              'Westmoreland', 'Williamsburg', 'Winchester', 'Wise', 'Wythe', 'York']
    for map_name in cities:
        name = map_name.replace('_', ' ')
        slug = map_name.replace('_', '-')
        city = City.objects.get_or_create(name=name, slug=slug, map_name=map_name)
        if city[1]:
            city[0].save()
            city_service_create(city=city[0])
        else:
            print(f'City repeated: {name}')
    return redirect(reverse('parsing:city_list'))


@login_required()
def city_img_autocreate(request):
    cities_img_parser.delay()
    messages.success(request, 'Parsing started')
    return redirect(reverse('parsing:city_list'))


def city_list(request):
    cities = City.objects.all()
    if request.method == 'POST' and has_group(request.user, 'Redactor'):
        form = CityForm(request.POST)
        if form.is_valid():
            city = form.save(commit=False)
            city.slug = slugify(request.POST['name'])
            city.map_name = slugify(request.POST['name'])
            city.save()
            city_service_create(city=city)
        return redirect(reverse('parsing:city_list'))
    return render(request, 'parsing/city/list.html', {
        'cities': cities
    })


def city_detail(request, slug):
    city = get_object_or_404(City, slug=slug)
    city_services = CityService.objects.filter(city=city)
    if not has_group(request.user, 'Redactor'):
        city_services = city_services.filter(access=True)

    return render(request, 'parsing/city/detail.html', {
        'city': city,
        'city_services': city_services
    })


@login_required()
def service_list(request):
    services = Service.objects.all()
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        service = form.save(commit=False)
        service.slug = slugify(request.POST['name'])
        service.save()
        city_service_create(service=service)
        return redirect(reverse('parsing:service_list'))
    return render(request, 'parsing/service/list.html', {
        'services': services
    })


def city_service_detail(request, city_slug, service_slug):
    city_service = CityService.objects.filter(city__slug=city_slug, service__slug=service_slug).first()
    places = get_sorted_places(city_service)
    top_places = places[:20]
    places_and_letters = places_to_sorted_letters(places)

    return render(request, 'parsing/city_service/places.html', {
        'city_service': city_service,
        'top_places': top_places,
        'places': places,
        'places_letter': places_and_letters['places_letter'],
        'letters': places_and_letters['letters']
    })


@login_required()
def city_service_access(request, pk):
    city_service = CityService.objects.filter(pk=pk).first()
    if city_service:
        city_service.access = not city_service.access
        city_service.save()
    return redirect(city_service.city.get_absolute_url())


def city_service_place_detail(request, service_slug, place_slug):
    place = get_object_or_404(Place, slug=place_slug)
    if place.is_redirect and not has_group(request.user, 'Redactor'):
        return redirect(place.redirect)
    reviews = get_place_reviews(request, place)
    return render(request, 'parsing/place/detail.html',
                  {'place': place, 'reviews': reviews['reviews'], 'my_review': reviews['my_review']})

#
# class QueryAdd(APIView):
#     def get(self, request, format=None):
#         username = request.GET.get('username')
#         query_name = request.GET.get('query_name')
#         query_page = request.GET.get('query_page')
#
#         user = User.objects.filter(username=username).first()
#         if not user:
#             return Response({}, status=status.HTTP_400_BAD_REQUEST)
#         try:
#             query_page = int(query_page)
#         except:
#             query_page = 1
#         if query_page == 0:
#             query_page = None
#         query = Query(user=user, name=query_name, page=query_page, status='wait')
#         query.save()
#         query_id = query.id
#         slug = slugify(query_name + '-' + str(query_id))
#         query.slug = slug
#         query.save()
#         try:
#             print(query_name)
#             startParsing.delay(query_name=query_name, query_id=query_id, pages=query_page)
#         except Exception as e:
#             print(e.__class__.__name__)
#             query.status = 'error'
#             query.save()
#
#         return Response({"message": "Парсинг начат"}, status=status.HTTP_200_OK)
#
#
# class QueryUser(APIView):
#     def get(self, request, username, format=None):
#         user = User.objects.filter(username=username).first()
#         if not user:
#             return Response({}, status=status.HTTP_400_BAD_REQUEST)
#         queries = user.queries.all()
#         tags = Tag.objects.filter(queries__in=queries).distinct()
#         query_serializer_data = QuerySerializer(queries, many=True).data
#         tags_serializer_data = TagSerializer(tags, many=True).data
#         return Response({'queries': query_serializer_data, 'tags': tags_serializer_data}, status=status.HTTP_200_OK)
#
#
# class QueryPlaces(APIView):
#     def get(self, request, slug, format=None):
#         query = Query.objects.filter(slug=slug).first()
#         if not query:
#             return Response({}, status=status.HTTP_400_BAD_REQUEST)
#
#         places_letter = {
#
#         }
#         query = Query.objects.filter(slug=slug).first()
#         if not query:
#             return redirect('parsing:index')
#         places = get_sorted_places(query)
#         for i in places:
#             first_letter = i.name[0]
#             i = PlaceMinSerializer(i).data
#             if first_letter in places_letter:
#                 places_letter[first_letter]['places'].append(i)
#             else:
#                 places_letter[first_letter] = {
#                     'letter': first_letter,
#                     'places': [i]
#                 }
#         letters = list(places_letter.keys())
#         letters = sorted(letters)
#
#         serializer = PlaceSerializer(places, many=True)
#         places_data = serializer.data
#         query_serializer = QuerySerializer(query, many=False)
#         query_data = query_serializer.data
#         data = {
#             'places': places_data,
#             'letters': letters,
#             'places_letter': places_letter,
#             'query': query_data,
#         }
#         return Response(data, status.HTTP_200_OK)
#
#
# class QueryDetail(RetrieveAPIView):
#     model = Query
#     serializer_class = QuerySerializer
#     queryset = model.objects.all()
#     lookup_field = 'slug'
#
#
# @method_decorator(xframe_options_exempt, name='dispatch')
# class PlaceHTML(DetailView):
#     model = Place
#     queryset = model.objects.all()
#     slug_field = 'cid'
#     slug_url_kwarg = 'cid'
#     template_name = 'parsing/place/copy.html'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['server_name'] = SERVER_NAME
#         return context
#
#
# class PlaceDetail(APIView):
#     def get(self, request, slug, format=None):
#         place = Place.objects.filter(slug=slug).first()
#         if not place:
#             return Response({}, status=status.HTTP_400_BAD_REQUEST)
#
#         query_serializer_data = {}
#         query_place = place.queries.first()
#         if query_place:
#             query = query_place.query
#             query_serializer_data = QuerySerializer(query, many=False).data
#
#         serializer = PlaceSerializer(place)
#         serializer_data = serializer.data
#         serializer_data['query'] = query_serializer_data
#         return Response(serializer_data, status=status.HTTP_200_OK)
#
#     def post(self, request, slug, format=None):
#         place = Place.objects.filter(slug=slug).first()
#         if not place:
#             return Response({}, status=status.HTTP_400_BAD_REQUEST)
#         data = request.data
#         form = PlaceForm(data, instance=place)
#         if form.is_valid():
#             form.save()
#             return Response({'status': 'success'}, status=status.HTTP_200_OK)
#         return Response({'status': 'error'}, status=status.HTTP_400_BAD_REQUEST)
#
#
# class QueryEdit(APIView):
#     def post(self, request, slug, format=None):
#         query = generics.get_object_or_404(Query, slug=slug)
#         print(request.POST)
#         form = QueryContentForm(request.POST, instance=query)
#         if form.is_valid():
#             form.save()
#             return Response({'status': 'success'}, status=status.HTTP_200_OK)
#         return Response({'status': 'error'}, status=status.HTTP_400_BAD_REQUEST)
#
#
# class TagList(ListAPIView):
#     model = Tag
#     serializer_class = TagSerializer
#     queryset = model.objects.all()
#
#
# class ReviewCreate(APIView):
#     def post(self, request, format=None):
#         post = request.POST
#         form = ReviewForm(post)
#         if form.is_valid():
#             review = form.save(commit=False)
#             review.dependent_user_id = post['user_id']
#             review.place = Place.objects.filter(slug=post['place_slug']).first()
#             review.dependent_site = post['site']
#             review.is_dependent = True
#             review.author_name = post['author_name']
#             review.save()
#             create_or_update_review_types(request.POST, review)
#             return Response({'message': 'success'}, status=status.HTTP_200_OK)
#
#         return Response({'message': 'error'}, status=status.HTTP_400_BAD_REQUEST)
#
#
# class ReviewDetail(RetrieveAPIView):
#     model = Review
#     serializer_class = ReviewSerializer
#     queryset = model.objects.all()
#
#
# class ReviewUpdateAPIView(APIView):
#     def post(self, request, pk, format=None):
#         review = generics.get_object_or_404(Review, pk=pk)
#         form = ReviewForm(request.data, instance=review)
#         if form.is_valid():
#             review = form.save(commit=False)
#             review.is_edit = True
#             review.save()
#             create_or_update_review_types(request.data, review)
#         else:
#             print(form.errors)
#
#
# class ReviewTypeList(ListAPIView):
#     model = ReviewType
#     serializer_class = ReviewTypeSerializer
#     queryset = model.objects.all()
#
#     def get_queryset(self):
#         if 'pk' in self.kwargs:
#             return self.queryset.filter(
#                 reviews__review_id=self.kwargs['pk']
#             ).distinct()
#         return self.queryset.all()
