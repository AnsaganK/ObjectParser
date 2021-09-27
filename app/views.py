from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse, redirect

from app.forms import QueryTypeForm
from app.models import QueryType, Query
from app.parser import searchQuery
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required()
def index(request):
    user = request.user
    query_types = QueryType.objects.filter(user=user)
    quesries = Query.objects.filter(type__user = user)
    return render(request, 'app/index.html', {'user': user ,'query_types': query_types, 'queries': quesries})


@login_required()
def query_type_add(request):
    if request.method == 'POST':
        form = QueryTypeForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            query_type_name = cd['name']
            query_type_page = cd['page']
            query_type = QueryType(user=request.user, name=query_type_name, page=query_type_page)
            query_type.save()
            queries = searchQuery(name=query_type_name, page=query_type_page)
            for q in queries:
                query = Query(place_id=q['place_id'], type=query_type, data=q)
                query.save()
            return redirect('/')
        else:
            print(form.errors)
            #Тут надо сделать message
            return render(request, 'app/query_type/add.html')
    return render(request, 'app/query_type/add.html')


def query_type_list(request):
    user = request.user
    query_types = QueryType.objects.filter(user=user)
    return render(request, 'app/query_type/list.html', {'query_types': query_types})


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


def query_detail(request, pk):
    query = Query.objects.filter(pk=pk).first()
    return render(request, 'app/query/detail.html', {'query': query})


def profile(request):
    user = request.user
    return render(request, 'app/user/profile.html', {'user': user})