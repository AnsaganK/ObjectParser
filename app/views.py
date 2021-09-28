from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, reverse

from app.forms import QueryTypeForm, UserForm, UserCreateForm
from app.models import QueryType, Query
from app.parser import searchQuery
from django.contrib import messages

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
            query_type = QueryType(user=request.user, name=query_type_name, page=query_type_page)
            query_type.save()
            query_type_id = query_type.id

            queries = searchQuery(name=query_type_name, page=query_type_page, detail=detail, query_type_id=query_type_id)
            for q in queries:
                if detail:
                    query = Query.objects.filter(place_id=q['place_id']).first()
                    if query:
                        query.data = q
                        query.save()
                    else:
                        query = Query(place_id=q['place_id'], type=query_type, data=q)
                        query.save()
                else:
                    query = Query(place_id=q['place_id'], type=query_type, data=q)
                    query.save()
            return redirect('/')
        else:
            print(form.errors)
            #Тут надо сделать message
            return render(request, 'app/query_type/add.html')
    return render(request, 'app/query_type/add.html')


@login_required()
def query_type_list(request):
    user = request.user
    query_types = QueryType.objects.filter(user=user)
    return render(request, 'app/query_type/list.html', {'query_types': query_types})

@login_required()
def query_type_detail(request, pk):
    query_type = QueryType.objects.filter(pk=pk).first()
    queries = query_type.queries.all()
    paginator = Paginator(queries, 20)
    page = request.GET.get('page')
    try:
        queries = paginator.page(page)
    except PageNotAnInteger:
        queries = paginator.page(1)
    except EmptyPage:
        queries = paginator.page(paginator.num_pages)
    return render(request, 'app/query_type/detail.html', {'query_type': query_type, 'queries': queries})

@login_required()
def query_detail(request, pk):
    query = Query.objects.filter(pk=pk).first()
    return render(request, 'app/query/detail.html', {'query': query})

@login_required()
def profile(request):
    user = request.user
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
        else:
            for error in form.errors:
                messages.error(request, form.errors[error])
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
            for error in form.errors:
                messages.error(request, form.errors[error])

    return render(request, 'app/user/add.html')