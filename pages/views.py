from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic import ListView
from django.db.models.functions import ExtractYear, ExtractMonth
from django.db.models import Count
from .models import Judgement
from django.db.models import Q
import calendar


from django.shortcuts import render
from .forms import JudgementsFilterForm, JudgementsSearchForm, JudgementsPDFForm

from . import bm25
import json

from django.conf import settings

# Create your views here.

pos_inv_ind_path = settings.BASE_DIR / "pos_inv_ind.json"


class HomePageView(TemplateView):
    model = Judgement
    template_name = "home.html"
    context_object_name = "search_judgements_list"

    with open(pos_inv_ind_path, "r") as f:
        data = json.load(f)
        dlt = bm25.createDocTable(data)
        # print("dlt", dlt)

    def get(self, request, *args, **kwargs):
        query = request.GET.get("search_query")
        if query:
            print("query", query)
            results = bm25.search_main_func(query, self.data, self.dlt)
            queryset = Judgement.objects.defer("judgement_text").filter(
                Q(primary_key__in=results)
            )
            # re order queryset by results
            queryset = sorted(queryset, key=lambda x: results.index(x.primary_key))[:30]

        else:
            queryset = Judgement.objects.none()

        return render(
            request,
            "home.html",
            {
                "query": query,
                "results": queryset,
                "search_form": JudgementsSearchForm(),
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = kwargs.get("search_form", JudgementsSearchForm())
        return context


class AboutPageView(TemplateView):
    template_name = "about.html"


class JudgementListView(ListView):
    model = Judgement
    template_name = "judgements_list.html"
    context_object_name = "all_judgements_list"

    def get(self, request, *args, **kwargs):
        year_ = request.GET.get("year")
        month_ = request.GET.get("month")
        if month_ == "":
            month_ = None
        search_link = request.GET.get("search_link")

        if year_ and not month_:
            queryset = (
                self.get_queryset()
                .annotate(year=ExtractYear("date"), month=ExtractMonth("date"))
                .filter(year=year_)
                .order_by("-date")
            )
        elif year_ and month_:
            queryset = (
                self.get_queryset()
                .annotate(year=ExtractYear("date"), month=ExtractMonth("date"))
                .filter(year=year_, month=month_)
                .order_by("-date")
            )
        else:
            queryset = self.get_queryset().order_by("-date")

        if search_link:
            queryset = self.get_queryset().filter(link__icontains=search_link)

        self.object_list = queryset
        context = self.get_context_data(
            object_list=queryset,
            filter_form=JudgementsFilterForm(),
            year=year_ if year_ != None else None,
            month=calendar.month_name[int(month_)] if month_ != None else None,
            search_link_form=JudgementsPDFForm(),
            search_link=search_link if search_link != None else None,
        )
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = kwargs.get("filter_form", JudgementsFilterForm())
        context["search_link_form"] = kwargs.get(
            "search_link_form", JudgementsPDFForm()
        )
        return context
