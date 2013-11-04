import os.path

from django import forms
from django import http
from django import template
from django.conf import settings
from django.template import loader
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.web import resource
from twisted.web import server
from twisted.web import static

BASE_DIR = os.path.dirname(__file__)
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
settings.configure(
    TEMPLATE_DIRS=(TEMPLATE_DIR,),
)

class ConfigForm(forms.Form):
  name = forms.CharField(max_length=1)
  azimuth_lower_bound = forms.IntegerField(max_value=1000, min_value=-1000)
  azimuth_upper_bound = forms.IntegerField(max_value=1000, min_value=-1000)
  elevation_lower_bound = forms.IntegerField(max_value=1000, min_value=-1000)
  elevation_upper_bound = forms.IntegerField(max_value=1000, min_value=-1000)


class SendCommandForm(forms.Form):
  name = forms.CharField(max_length=1)
  commands = forms.CharField(widget=forms.Textarea)


class ViewLogsForm(forms.Form):
  num_lines = forms.IntegerField(min_value=1, initial=1000)


class TailLogProtocol(protocol.ProcessProtocol):
  def __init__(self, request, callback):
    self.request = request
    self.callback = callback
    self.contents = []

  def outReceived(self, data):
    self.contents.append(data)

  def processEnded(self, status):
    self.callback(self.request, ''.join(self.contents))


def request_to_query_dict(twisted_request):
  query_dict = http.QueryDict('', mutable=True)
  for key, value_list in twisted_request.args.iteritems():
    query_dict.setlist(key, value_list)
  return query_dict


class _BaseResource(resource.Resource):
  TEMPLATE_NAME = None

  def __init__(self, searchlights=None):
    if searchlights:
      self.searchlights = searchlights
      self.name_to_searchlight = dict((s.name, s) for s in self.searchlights)
    assert self.TEMPLATE_NAME, 'Missing template'
    self.template = loader.get_template(self.TEMPLATE_NAME)

  def render_to_string(self, **context_kwargs):
    context = template.Context(context_kwargs)
    return str(self.template.render(context))


class ConfigurationResource(_BaseResource):
  isLeaf = True
  TEMPLATE_NAME = 'configuration.html'

  def render_GET(self, request):
    form = ConfigForm(request_to_query_dict(request))
    if form.is_valid():
      searchlight = self.name_to_searchlight[form.cleaned_data['name']]
      searchlight.config.azimuth_lower_bound = form.cleaned_data['azimuth_lower_bound'] / 1000.0
      searchlight.config.azimuth_upper_bound = form.cleaned_data['azimuth_upper_bound'] / 1000.0
      searchlight.config.elevation_lower_bound = form.cleaned_data['elevation_lower_bound'] / 1000.0
      searchlight.config.elevation_upper_bound = form.cleaned_data['elevation_upper_bound'] / 1000.0
      searchlight.config_store.commit()  # ugh
    return self.render_to_string(form=form)

  render_POST = render_GET


class SendCommandResource(_BaseResource):
  isLeaf = True
  TEMPLATE_NAME = 'send_command.html'

  def render_GET(self, request):
    form = SendCommandForm(request_to_query_dict(request))
    if form.is_valid():
      searchlight = self.name_to_searchlight[form.cleaned_data['name']]
      commands = form.cleaned_data['commands'].split('\n')
      for command in commands:
        # TODO callback
        searchlight.motor_controller.sendCommand(str(command))
    return self.render_to_string(form=form)
    
  render_POST = render_GET


class ViewLogsResource(_BaseResource):
  isLeaf = True
  TEMPLATE_NAME = 'view_logs.html'

  def render_GET(self, request):
    form = ViewLogsForm(request_to_query_dict(request))
    if form.is_valid():
      process_protocol = TailLogProtocol(request, self.render_with_log_contents)
      reactor.spawnProcess(process_protocol, 'tail', ['tail', '-%d' % form.cleaned_data['num_lines'], '/tmp/searchlight.log'])
      return server.NOT_DONE_YET
    else:
      return self.render_to_string(form=form)
  
  def render_with_log_contents(self, request, log_contents):
    request.write(self.render_to_string(form=ViewLogsForm(), log_contents=log_contents))
    request.finish()

  render_POST = render_GET


class AdminServer(server.Site):
  def __init__(self, searchlights):
    root = resource.Resource()
    root.putChild('config', ConfigurationResource(searchlights))
    root.putChild('send_command', SendCommandResource(searchlights))
    root.putChild('view_logs', ViewLogsResource())
    root.putChild('static', static.File(STATIC_DIR))
    server.Site.__init__(self, root)
  