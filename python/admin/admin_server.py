import os.path

from django import forms
from django import http
from django import template
from django.conf import settings
from django.template import loader
from twisted.web import resource
from twisted.web import server
from twisted.web import static

settings.configure(
    TEMPLATE_DIRS=(
        os.path.join(os.path.dirname(__file__), 'templates'),
    ),
)

class ConfigForm(forms.Form):
  name = forms.CharField(max_length=1)
  azimuth_lower_bound = forms.IntegerField(max_value=1000, min_value=-1000)
  azimuth_upper_bound = forms.IntegerField(max_value=1000, min_value=-1000)
  elevation_lower_bound = forms.IntegerField(max_value=1000, min_value=-1000)
  elevation_upper_bound = forms.IntegerField(max_value=1000, min_value=-1000)



def request_to_query_dict(twisted_request):
  query_dict = http.QueryDict('', mutable=True)
  for key, value_list in twisted_request.args.iteritems():
    query_dict.setlist(key, value_list)
  return query_dict


class ConfigurationResource(resource.Resource):
  isLeaf = True

  def __init__(self, searchlights):
    self.searchlights = searchlights
    self.name_to_searchlight = dict((s.name, s) for s in self.searchlights)
    self.template = loader.get_template('configuration.html')

  def render_GET(self, request):
    form = ConfigForm(request_to_query_dict(request))
    if form.is_valid():
      searchlight = self.name_to_searchlight[form.cleaned_data['name']]
      searchlight.config.azimuth_lower_bound = form.cleaned_data['azimuth_lower_bound'] / 1000.0
      searchlight.config.azimuth_upper_bound = form.cleaned_data['azimuth_upper_bound'] / 1000.0
      searchlight.config.elevation_lower_bound = form.cleaned_data['elevation_lower_bound'] / 1000.0
      searchlight.config.elevation_upper_bound = form.cleaned_data['elevation_upper_bound'] / 1000.0
      searchlight.config_store.commit()  # ugh
    context = template.Context({'config_form': form})
    return str(self.template.render(context))

  render_POST = render_GET


class AdminServer(server.Site):
  def __init__(self, searchlights):
    root = resource.Resource()
    root.putChild('config', ConfigurationResource(searchlights))
    server.Site.__init__(self, root)
  