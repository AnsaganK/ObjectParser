from email.headerregistry import Group

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, reverse
from pytils.translit import slugify

from app.forms import UserForm, UserCreateForm, UserDetailForm, QueryForm, ReviewForm
from app.models import Query, Place, Review
from django.contrib import messages

from app.parser_selenium import selenium_query_detail
from app.tasks import startParsing, generate_file
from app.templatetags.app_tags import GROUPS


def show_form_errors(request, errors):
    for error in errors:
        messages.error(request, errors[error])

def get_paginator(request, queryset, count):
    paginator = Paginator(queryset, count)
    page = request.GET.get('page')
    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:
        queryset = paginator.page(1)
    except EmptyPage:
        queryset = paginator.page(paginator.num_pages)
    return queryset


def has_group(user, group_name):
    group = user.groups.first()
    if not group:
        return False
    current_index = GROUPS[group.name]
    recommended_index = GROUPS[group_name]
    if current_index < recommended_index:
        return False
    return True


def index(request):
    user = request.user
    if user.is_authenticated:
        queries = Query.objects.filter(user=user)
        places = Place.objects.filter(queries__query__user=user)
        return render(request, 'app/index.html', {'user': user, 'queries': queries, 'places': places})
    return render(request, 'app/index.html')

@login_required()
def query_add(request):
    if request.method == 'POST':
        form = QueryForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            query_name = cd['name']
            query_not_all = cd['all_pages']

            if query_not_all:
                query_page = cd['page']
            else:
                query_page = None


            print(query_name, query_all, query_page)

            query = Query(user=request.user, name=query_name, page=query_page, status='wait')
            query.save()
            query_id = query.id

            slug = slugify(query_name+'-'+str(query_id))
            query.slug = slug
            query.save()

            try:
                startParsing.delay(query_name=query_name, query_id=query_id, pages=int(query_page))
            except Exception as e:
                print(e.__class__.__name__)
                query.status = 'error'
                query.save()
            # for q in queries:
            #     if detail:
            #         place = Query.objects.filter(place_id=q['place_id']).first()
            #         if place:
            #             place.data = q
            #             place.save()
            #         else:
            #             place = Query(place_id=q['place_id'], type=query, data=q)
            #             place.save()
            #     else:
            #         place = Query(place_id=q['place_id'], type=query, data=q)
            #         place.save()
            return redirect('/')
        else:
            show_form_errors(request, form.errors)
            return render(request, 'app/query/add.html')
    return render(request, 'app/query/add.html')

@login_required()
def query_all(request):
    user = request.user
    if not has_group(user, 'Суперадминистратор'):
        return redirect('app:index')
    queries = Query.objects.all()
    queries = get_paginator(request, queries, 20)
    return render(request, 'app/query/all.html', {'queries': queries})

@login_required()
def query_list(request):
    user = request.user
    if not has_group(user, 'Администратор'):
        return redirect('app:index')

    queries = Query.objects.filter(user=user)
    queries = get_paginator(request, queries, 20)
    return render(request, 'app/query/list.html', {'queries': queries})

# def rating_sorted(query):
#     return query.get_rating

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
    return render(request, 'app/query/detail.html', {'query': query, 'places': places, 'sort_type': sort_type})

@login_required()
def query_delete(request, pk):
    query = Query.objects.filter(pk=pk).first()
    if query and query.user == request.user or has_group(request.user, 'Суперадминистратор'):
        query.delete()
        messages.success(request, f'Запрос "{query.name}" успешно удален')
    return redirect('app:query_list')


@login_required()
def query_file_generate(request, pk):
    query = Query.objects.filter(pk=pk).first()
    if not query:
        return redirect(query.get_absolute_url)
    # places = query.places.all()
    places = Place.objects.filter(queries__query=query).all()
    name = query.name
    file = generate_file(name, places)
    return file

def queries(request):
    queries = Query.objects.all()
    queries = get_paginator(request, queries, 16)
    return render(request, 'app/query/queries.html', {'queries': queries})

def places(request, slug):
    places_letter = {

    }
    query = Query.objects.filter(slug=slug).first()
    if not query:
        return redirect('app:index')
    places = Place.objects.filter(queries__query=query).all().order_by('-rating')
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
    return render(request, 'app/query/places.html', {'query': query, 'places': places, 'places_letter': places_letter, 'letters': letters})

@login_required()
def place_detail(request, cid):
    place = Place.objects.filter(cid=cid).first()
    reviews = place.reviews.all()
    reviews = get_paginator(request, reviews, 10)
    my_review = Review.objects.filter(place=place).filter(user=request.user).first()
    return render(request, 'app/place/detail.html', {'place': place, 'reviews': reviews, 'my_review': my_review})

@login_required()
def review_add(request, cid):
    place = Place.objects.filter(cid=cid).first()
    if Review.objects.filter(user=request.user).filter(place=place).first():
        messages.error(request, 'Вы не можете оставить более одного отзыва')
        return redirect(place.get_absolute_url())
    if not place:
        return render(request, '404.html')
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.place = place
            review.save()
            messages.success(request, 'Ваш отзыв сохранен')
        else:
            show_form_errors(request, form.errors)
    return redirect(place.get_absolute_url())


@login_required()
def place_update(request, pk):
    place = Place.objects.filter(pk=pk).first()
    #selenium_query_detail(place_id=place.place_id)
    # updateDetail(place.pk)
    return redirect(place.get_absolute_url())


@login_required()
def profile(request):
    user = request.user
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            messages.success(request, 'Данные успешно изменены')
            form.save()
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('app:profile'))
    return render(request, 'app/user/profile.html', {'user': user})

@login_required()
def all_reviews(request):
    if not has_group(request.user, 'Редактор'):
        return redirect('app:index')
    reviews = Review.objects.all()
    reviews = get_paginator(request, reviews, 10)
    return render(request, 'app/reviews/all.html', {'reviews': reviews})

@login_required()
def my_reviews(request):
    user = request.user
    reviews = user.reviews.all()
    reviews = get_paginator(request, reviews, 10)
    return render(request, 'app/reviews/reviews.html', {'reviews': reviews})


@login_required()
def my_review_edit(request, pk):
    review = Review.objects.filter(pk=pk).first()
    if (not review or request.user != review.user) and not has_group(request.user, 'Редактор'):
        return redirect('app:my_reviews')
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            review.is_edit = True
            review.save()
            messages.success(request, 'Отзыв успешно отредактирован')
        else:
            show_form_errors(request, form.errors)
        return redirect('app:my_reviews')
    return render(request, 'app/reviews/review_edit.html', {'review': review})



def registration(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            group = Group.objects.filter(name='Пользователь').first()
            if group:
                user.groups.add(group)
            login(request, user)
            return redirect(reverse('app:profile'))
        else:
            show_form_errors(request, form.errors)
    return render(request, 'app/user/add.html')


@login_required()
def group_list(request):
    groups = Group.objects.all()
    groups_not_count = User.objects.filter(groups=None).count()
    return render(request, 'app/admin_dashboard/group/list.html', {'groups': groups, 'groups_not_count': groups_not_count})


@login_required()
def group_detail(request, pk):
    group = Group.objects.filter(pk=pk).first()
    if group:
        return render(request, 'app/admin_dashboard/group/detail.html', {'group': group})
    return redirect('group_list')


@login_required()
def group_not(request):
    users = User.objects.filter(groups=None)
    return render(request, 'app/admin_dashboard/group/not.html', {'users': users})


@login_required()
def admin_dashboard(request):
    user = request.user
    if user.is_superuser:
        return render(request, 'app/admin_dashboard/dashboard.html')
    return redirect('/')


@login_required()
def user_list(request):
    users = User.objects.all().order_by('-pk')
    users = get_paginator(request, users, 10)
    return render(request, 'app/user/list.html', {'users': users})


@login_required()
def user_detail(request, pk):
    if not has_group(request.user, 'Администратор'):
        return redirect('app:index')
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
            messages.success(request, 'Данные успешно изменены')
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('app:user_detail', args=[user.id]))

    groups = Group.objects.all()
    if user:
        return render(request, 'app/user/detail.html', {'user': user, 'groups': groups})
    return redirect('/')