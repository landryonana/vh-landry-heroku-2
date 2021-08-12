import datetime

from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from weasyprint import HTML
import tempfile


from remplissages.models import Evangelisation, Person, Site, Suivie



def month_name (number):
    if number == 1:
        return "Janvier"
    elif number == 2:
        return "Févier"
    elif number == 3:
        return "Mars"
    elif number == 4:
        return "Avril"
    elif number == 5:
        return "Mai"
    elif number == 6:
        return "Juin"
    elif number == 7:
        return "Juillet"
    elif number == 8:
        return "Aout"
    elif number == 9:
        return "Septembre"
    elif number == 10:
        return "Octobre"
    elif number == 11:
        return "Novembre"
    elif number == 12:
        return "Décembre"



@login_required
def index_rapport(request):
    active = 'rapport'
    context = dict()
    sites_person = []
    #======================STAT PAR SITE==============================================================
    site = None
    sites = Site.objects.all()
    for st in sites:
        site = {
            'nom': st.nom_site_evangelisation,
            'count_oui': st.personnes_evangelise.filter(accepte_jesus='oui'),
            'count_non': st.personnes_evangelise.filter(accepte_jesus='non'),
            'count_deja': st.personnes_evangelise.filter(accepte_jesus='déjà'),
            'count_indecis': st.personnes_evangelise.filter(accepte_jesus='ras'),
            'total': st.personnes_evangelise.all()
        }
        sites_person.append(site)

    #======================RAPPORT MENSUEL==============================================================
    all_evang = []
    evang = None
    prc_oui_JESUS = None
    evangs = Evangelisation.objects.all()

    
    for evang in evangs:
        try:
            prc_oui_JESUS = (Person.objects.filter(date__month=evang.day.month).filter(accepte_jesus='oui').count())/(Person.objects.all().count())
        except (ZeroDivisionError, Person.DoesNotExist):
            prc_oui_JESUS = "Pas de personnes évangelisées"
        evan = {
            'id': evang.id,
            'mois': month_name(evang.day.month),
            'count_sortie': evangs.filter(day__month=evang.day.month),
            'count_boss': evang.boss.all(),
            'count_femme': len([elt.profile.sexe for elt in evang.boss.all() if elt.profile.sexe=='féminin']),
            'count_homme': len([elt.profile.sexe for elt in evang.boss.all() if elt.profile.sexe=='masculin']),
            'oui_JESUS': Person.objects.filter(date__month=evang.day.month).filter(accepte_jesus='oui'),
            'rester': len([ps.suivie.choix_person for ps in Person.objects.filter(date__month=evang.day.month) if ps.suivie.choix_person=='rester']),
            'prc_oui_JESUS': prc_oui_JESUS,
            'ps_evg': Person.objects.filter(date__month=evang.day.month),
            'observation':evang.observation
        }

        all_evang.append(evan)
    #======================PIE ET CHRT BAR============================================================================
    personne_oui = None
    personne_non = None
    personne_deja = None
    personne_indecis = None
    personnes = None
    month_req = None

    personnes = Person.objects.all()
    personne_oui = personnes.filter(accepte_jesus='oui')
    personne_non = personnes.filter(accepte_jesus='non')
    personne_deja = personnes.filter(accepte_jesus='déjà')
    personne_indecis = personnes.filter(accepte_jesus='ras')
    #======================TABLE PERSONNE============================================================================
    if request.method == 'POST':
        month_req = request.POST.get('month')
        month_split = month_req.split('-')
        year = month_split[0]
        month = month_split[1]
        personnes = Person.objects.filter(date__year=year, date__month=month)

    context['personne_oui'] = personne_oui
    context['personne_non'] = personne_non
    context['personne_deja'] = personne_deja
    context['personne_indecis'] = personne_indecis
    context['personnes'] = personnes
    context['active'] = active
    context['sites_person'] = sites_person
    context['all_evang'] = all_evang
    context['evangs'] = evangs
    context['sites'] = sites
    return render(request, 'rapport/index_rapport.html', context)


@login_required
def rapport_evang_detail_sortie(request, pk):
    evg = None
    evg = get_object_or_404(Evangelisation, pk=pk)
    data = dict()
    evangs = Evangelisation.objects.all()
    personnes = Person.objects.all()
    evang = {
            'id': evg.id,
            'mois': month_name(evg.day.month),
            'count_sortie': evangs.filter(day__month=evg.day.month),
            'count_boss': evg.boss.all(),
            'count_femme': len([elt.profile.sexe for elt in evg.boss.all() if elt.profile.sexe=='féminin']),
            'count_homme': len([elt.profile.sexe for elt in evg.boss.all() if elt.profile.sexe=='masculin']),
            'oui_JESUS': Person.objects.filter(date__month=evg.day.month).filter(accepte_jesus='oui'),
            'personnes':personnes,
        }
    context = {'evang': evang}
    data['detail_info'] = render_to_string('rapport/modal/evang-detail.html', context, request=request)
    return JsonResponse(data)



def rapport_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment;filename=Évangelisation'+\
        str(datetime.datetime.now())+'.pdf'
    response['Content-Transfer-Encoding'] = 'binary'
    html_string = render_to_string('rapport/pdf_output.html', {'personnes':Person.objects.all()})
    html = HTML(string=html_string)
    result = html.write_pdf()

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()
        output=open(output.name, 'rb')
        response.write(output.read())
    return response


def rapport_excel(request):
    return