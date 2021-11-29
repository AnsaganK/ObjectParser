from email.headerregistry import Group

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.shortcuts import render, redirect, reverse, get_object_or_404
from pytils.translit import slugify
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from app.forms import UserForm, UserCreateForm, UserDetailForm, QueryForm, ReviewForm, PlaceForm, TagForm, \
    QueryContentForm, ReviewTypeForm
from app.models import Query, Place, Review, Tag, ReviewType, ReviewPart
from django.contrib import messages

from app.parser_selenium import selenium_query_detail
from app.serializers import QuerySerializer, QueryPlaceSerializer, PlaceSerializer, PlaceMinSerializer, TagSerializer, \
    ReviewSerializer, ReviewTypeSerializer
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
            not_all = cd['not_all']

            if not_all:
                query_page = cd['page']
                try:
                    query_page = int(query_page)
                except:
                    query_page = 1
            else:
                query_page = None

            print(query_name, not_all, query_page)

            query = Query(user=request.user, name=query_name, page=query_page, status='wait')
            query.save()
            query_id = query.id

            slug = slugify(query_name + '-' + str(query_id))
            query.slug = slug
            query.save()

            try:
                startParsing.delay(query_name=query_name, query_id=query_id, pages=query_page)
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
def query_edit(request, slug):
    query = get_object_or_404(Query, slug=slug)
    if request.method == 'POST':
        form = QueryContentForm(request.POST, instance=query)
        if form.is_valid():
            query = form.save()
            messages.success(request, 'Описание изменено')
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('app:places', args=[query.slug]))
    tags = Tag.objects.all()
    return render(request, 'app/query/edit.html', {'query': query, 'tags': tags})


@login_required()
def query_all(request):
    if not has_group(request.user, 'Суперадминистратор'):
        return redirect('app:index')
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
    return render(request, 'app/query/all.html', {'queries': queries, 'users': users, 'selected_user': selected_user})


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
    slug = query.slug
    print(slug)
    file = generate_file(slug, places)
    return file


def queries(request):
    queries = Query.objects.all()
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
        pass
    queries = get_paginator(request, queries, 16)
    tags = Tag.objects.all()
    return render(request, 'app/query/queries.html', {'queries': queries, 'tags': tags, 'search': search, 'tags_checked': tags_checked})


def add_slug_for_tag(form, tag):
    cd = form.cleaned_data
    name = cd['name']
    slug = slugify(name)
    tag.slug = slug
    tag.save()


@login_required()
def tags(request):
    tags = Tag.objects.all()
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save(commit=False)
            add_slug_for_tag(form, tag)
            messages.success(request, 'Тэг создан')
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('app:tags'))
    return render(request, 'app/tag/list.html', {'tags': tags})


@login_required()
def tag_edit(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            tag = form.save(commit=False)
            add_slug_for_tag(form, tag)
            tag.save()
            messages.success(request, 'Тэг изменен')
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('app:tags'))
    return render(request, 'app/tag/edit.html', {'tag': tag})


@login_required()
def tag_delete(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    tag.delete()
    messages.success(request, 'Тэг удален')
    return redirect(reverse('app:tags'))


def review_types(request):
    review_types = ReviewType.objects.all()
    if request.method == 'POST':
        form = ReviewTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тип отзыва создан')
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('app:review_types'))
    return render(request, 'app/admin_dashboard/review_type/list.html', {'review_types': review_types})


def review_type_edit(request, pk):
    review_type = get_object_or_404(ReviewType, pk=pk)
    if request.method == 'POST':
        form = ReviewTypeForm(request.POST, instance=review_type)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тип отзыва изменен')
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('app:review_types'))
    return render(request, 'app/admin_dashboard/review_type/edit.html', {'review_type': review_type})


def places(request, slug):
    places_letter = {

    }
    query = Query.objects.filter(slug=slug).first()
    if not query:
        return redirect('app:index')
    places = Place.objects.filter(queries__query=query).all().order_by('-rating', '-rating_user_count')
    top_places = places.exclude(address=None)[:20]
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
    return render(request, 'app/query/places.html', {'query': query,
                                                     'top_places': top_places,
                                                     'places': places,
                                                     'places_letter': places_letter,
                                                     'letters': letters})


def create_or_update_review_types(post, review):
    for i in post:
        if 'review_type' in i:
            review_type_id = int(i.split('_')[-1])
            review_type = ReviewType.objects.filter(pk=review_type_id).first()
            review_part = ReviewPart.objects.update_or_create(review_type=review_type, review=review)[0]
            review_part.rating = int(post[i])
            review_part.save()


@login_required()
def place_detail(request, slug):
    place = get_object_or_404(Place, slug=slug)
    if request.method == 'POST':
        if Review.objects.filter(user=request.user).filter(place=place).first():
            messages.error(request, 'Вы не можете оставить более одного отзыва')
            return redirect(place.get_absolute_url())
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.place = place
            review.save()
            create_or_update_review_types(request.POST, review)
            messages.success(request, 'Ваш отзыв сохранен')
        else:
            show_form_errors(request, form.errors)
        return redirect(place.get_absolute_url())

    reviews = place.reviews.all()
    reviews = get_paginator(request, reviews, 10)
    review_types = ReviewType.objects.all()
    my_review = Review.objects.filter(place=place).filter(user=request.user).first()
    return render(request, 'app/place/detail.html', {'place': place, 'reviews': reviews, 'my_review': my_review,
                                                     'review_types': review_types})


@login_required()
def place_edit(request, cid):
    place = get_object_or_404(Place, cid=cid)
    if request.method == 'POST':
        form = PlaceForm(request.POST, instance=place)
        if form.is_valid():
            form.save()
            messages.success(request, 'Объект изменен')
        else:
            show_form_errors(request, form.errors)
        return redirect(place.get_absolute_url())
    return render(request, 'app/place/edit.html', {'place': place})


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
            messages.success(request, 'Данные успешно изменены')
            form.save()
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('app:profile'))
    return render(request, 'app/user/profile.html', {'user': user})


@login_required()
def public_cabinet(request, username):
    user = get_object_or_404(User, username=username)
    return render(request, 'app/user/public_cabinet.html', {'user': user})


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
            create_or_update_review_types(request.POST, review)
            messages.success(request, 'Отзыв успешно отредактирован')
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('app:my_review_edit', args=[review.id]))

    review_types = ReviewType.objects.filter(reviews__review=review)
    review_parts = ReviewPart.objects.values('review_type', 'rating').filter(review=review)
    print(review_parts)
    return render(request, 'app/reviews/review_edit.html',
                  {'review': review, 'review_types': review_types, 'review_parts': review_parts})


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
    return render(request, 'app/admin_dashboard/group/list.html',
                  {'groups': groups, 'groups_not_count': groups_not_count})


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


class QueryAdd(APIView):
    def get(self, request, format=None):
        username = request.GET.get('username')
        query_name = request.GET.get('query_name')
        query_page = request.GET.get('query_page')

        user = User.objects.filter(username=username).first()
        if not user:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        try:
            query_page = int(query_page)
        except:
            query_page = 1
        if query_page == 0:
            query_page = None
        query = Query(user=user, name=query_name, page=query_page, status='wait')
        query.save()
        query_id = query.id
        slug = slugify(query_name + '-' + str(query_id))
        query.slug = slug
        query.save()
        try:
            print(query_name)
            startParsing.delay(query_name=query_name, query_id=query_id, pages=query_page)
        except Exception as e:
            print(e.__class__.__name__)
            query.status = 'error'
            query.save()

        return Response({"message": "Парсинг начат"}, status=status.HTTP_200_OK)


class QueryUser(APIView):
    def get(self, request, username, format=None):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        queries = user.queries.all()
        tags = Tag.objects.filter(queries__in=queries).distinct()
        query_serializer_data = QuerySerializer(queries, many=True).data
        tags_serializer_data = TagSerializer(tags, many=True).data
        return Response({'queries': query_serializer_data, 'tags': tags_serializer_data}, status=status.HTTP_200_OK)


class QueryPlaces(APIView):
    def get(self, request, slug, format=None):
        query = Query.objects.filter(slug=slug).first()
        if not query:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        places_letter = {

        }
        query = Query.objects.filter(slug=slug).first()
        if not query:
            return redirect('app:index')
        places = Place.objects.filter(queries__query=query).all().order_by('-rating', '-rating_user_count')
        for i in places:
            first_letter = i.name[0]
            i = PlaceMinSerializer(i).data
            if first_letter in places_letter:
                places_letter[first_letter]['places'].append(i)
            else:
                places_letter[first_letter] = {
                    'letter': first_letter,
                    'places': [i]
                }
        letters = list(places_letter.keys())
        letters = sorted(letters)

        serializer = PlaceSerializer(places, many=True)
        places_data = serializer.data
        query_serializer = QuerySerializer(query, many=False)
        query_data = query_serializer.data
        data = {
            'places': places_data,
            'letters': letters,
            'places_letter': places_letter,
            'query': query_data,
        }
        return Response(data, status.HTTP_200_OK)


class QueryDetail(RetrieveAPIView):
    model = Query
    serializer_class = QuerySerializer
    queryset = model.objects.all()
    lookup_field = 'slug'


class PlaceDetail(APIView):
    def get(self, request, slug, format=None):
        place = Place.objects.filter(slug=slug).first()
        if not place:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        query_serializer_data = {}
        query_place = place.queries.first()
        if query_place:
            query = query_place.query
            query_serializer_data = QuerySerializer(query, many=False).data

        serializer = PlaceSerializer(place)
        serializer_data = serializer.data
        serializer_data['query'] = query_serializer_data
        return Response(serializer_data, status=status.HTTP_200_OK)

    def post(self, request, slug, format=None):
        place = Place.objects.filter(slug=slug).first()
        if not place:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        data = request.data
        form = PlaceForm(data, instance=place)
        if form.is_valid():
            form.save()
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        return Response({'status': 'error'}, status=status.HTTP_400_BAD_REQUEST)


class QueryEdit(APIView):
    def post(self, request, slug, format=None):
        query = Query.objects.filter(slug=slug).first()
        if not query:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        data = request.data
        form = QueryContentForm(data, instance=query)
        if form.is_valid():
            form.save()
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        return Response({'status': 'error'}, status=status.HTTP_400_BAD_REQUEST)


class TagList(ListAPIView):
    model = Tag
    serializer_class = TagSerializer
    queryset = model.objects.all()


class ReviewDetail(RetrieveAPIView):
    model = Review
    serializer_class = ReviewSerializer
    queryset = model.objects.all()


class ReviewTypeList(ListAPIView):
    model = ReviewType
    serializer_class = ReviewTypeSerializer
    queryset = model.objects.all()

    def get_queryset(self):
        return self.queryset.filter(
            reviews__review_id=self.kwargs['pk']
        ).distinct()