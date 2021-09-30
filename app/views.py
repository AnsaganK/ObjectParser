from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, reverse

from app.forms import QueryTypeForm, UserForm, UserCreateForm
from app.models import QueryType, Query
from app.parser import searchQuery, updateDetail
from django.contrib import messages

from app.parser_selenium import selenium_query_detail
from app.tasks import celery_parser


def show_form_errors(request, errors):
    for error in errors:
        messages.error(request, errors[error])


def index(request):
    user = request.user
    if user.is_authenticated:
        query_types = QueryType.objects.filter(user=user)
        quesries = Query.objects.filter(type__user = user)
        return render(request, 'app/index.html', {'user': user, 'query_types': query_types, 'queries': quesries})
    return render(request, 'app/index.html')

@login_required()
def query_type_add(request):
    if request.method == 'POST':
        form = QueryTypeForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            query_type_name = cd['name']
            query_type_page = cd['page']
            detail = cd['detail']
            query_type = QueryType(user=request.user, name=query_type_name, page=query_type_page, status='wait')
            query_type.save()
            query_type_id = query_type.id
            try:
                celery_parser.delay(name=query_type_name, page=query_type_page, detail=detail, query_type_id=query_type_id)
            except:
                query_type.status = 'error'
                query_type.save()
            # for q in queries:
            #     if detail:
            #         query = Query.objects.filter(place_id=q['place_id']).first()
            #         if query:
            #             query.data = q
            #             query.save()
            #         else:
            #             query = Query(place_id=q['place_id'], type=query_type, data=q)
            #             query.save()
            #     else:
            #         query = Query(place_id=q['place_id'], type=query_type, data=q)
            #         query.save()
            return redirect('/')
        else:
            show_form_errors(request, form.errors)
            #Тут надо сделать message
            return render(request, 'app/query_type/add.html')
    return render(request, 'app/query_type/add.html')


@login_required()
def query_type_list(request):
    user = request.user
    query_types = QueryType.objects.filter(user=user)
    paginator = Paginator(query_types, 20)
    page = request.GET.get('page')
    try:
        query_types = paginator.page(page)
    except PageNotAnInteger:
        query_types = paginator.page(1)
    except EmptyPage:
        query_types = paginator.page(paginator.num_pages)
    return render(request, 'app/query_type/list.html', {'query_types': query_types})

def rating_sorted(query):
    return query.get_rating

@login_required()
def query_type_detail(request, pk):
    query_type = QueryType.objects.filter(pk=pk).first()
    queries = query_type.queries.all()
    sort_type = None
    if request.GET:
        sort_type = request.GET.get('sorted')
        if sort_type == 'rating_gt':
            queries = sorted(queries, key=rating_sorted)
        elif sort_type == 'rating_lt':
            queries = sorted(queries, key=rating_sorted, reverse=True)
    paginator = Paginator(queries, 20)
    page = request.GET.get('page')
    try:
        queries = paginator.page(page)
    except PageNotAnInteger:
        queries = paginator.page(1)
    except EmptyPage:
        queries = paginator.page(paginator.num_pages)
    return render(request, 'app/query_type/detail.html', {'query_type': query_type, 'queries': queries, 'sort_type': sort_type})


@login_required()
def query_detail(request, pk):
    query = Query.objects.filter(pk=pk).first()
    return render(request, 'app/query/detail.html', {'query': query})


@login_required()
def query_update(request, pk):
    query = Query.objects.filter(pk=pk).first()
    #selenium_query_detail(place_id=query.place_id)
    updateDetail(query.pk)
    return redirect(query.get_absolute_url())


@login_required()
def profile(request):
    user = request.user
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
        else:
            show_form_errors(request, form.errors)
        return redirect(reverse('profile'))
    return render(request, 'app/user/profile.html', {'user': user})


def registration(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse('profile'))
        else:
            show_form_errors(request, form.errors)
    return render(request, 'app/user/add.html')