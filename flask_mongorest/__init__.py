from flask import Blueprint
from flask_mongorest.methods import Create, BulkUpdate, List


class MongoRest(object):
    def __init__(self, app=None, **kwargs):
        self.app = app
        self.url_prefix = kwargs.pop('url_prefix', '')
        if app:
            app.register_blueprint(Blueprint(self.url_prefix, __name__, template_folder='templates'))
        else:
            self.url_rules = []

    def register(self, **kwargs):
        def decorator(klass):

            # Construct a url based on a 'name' kwarg with a fallback to a Mongo document's name
            document_name = klass.resource.document.__name__.lower()
            name = kwargs.pop('name', document_name)
            url = kwargs.pop('url', '/%s/' % document_name)

            # Insert the url prefix, if it exists
            if self.url_prefix:
                url = '%s%s' % (self.url_prefix, url)

            # Add url rules or store for init_app
            pk_type = kwargs.pop('pk_type', 'string')
            view_func = klass.as_view(name)
            if List in klass.methods:
                list_kwa = dict(defaults={'pk': None}, view_func=view_func, methods=[List.method])
                list_kwa.update(**kwargs)
                if self.app:
                    self.app.add_url_rule(url, list_kwa)
                else:
                    self.url_rules.append((url, list_kwa))
            if Create in klass.methods or BulkUpdate in klass.methods:
                create_kwa = dict(view_func=view_func, methods=[x.method for x in klass.methods if x in (Create, BulkUpdate)])
                create_kwa.update(**kwargs)
                if self.app:
                    self.app.add_url_rule(url, create_kwa)
                else:
                    self.url_rules.append((url, create_kwa))

                kwa = dict(view_func=view_func, methods=[x.method for x in klass.methods if x not in (List, BulkUpdate)])
                kwa.update(kwargs)
                url = '%s<%s:%s>/' % (url, pk_type, 'pk')
            if self.app:
                self.app.add_url_rule(**kwa)
            else:
                self.url_rules.append((url, kwa))
            return klass

        return decorator

    def init_app(self, app):
        self.app = app
        app.register_blueprint(Blueprint(self.url_prefix, __name__, template_folder='templates'))
        for url, kwa in self.url_rules:
            self.app.add_url_rule(url, **kwa)
