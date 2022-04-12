import json
from django.utils.translation import gettext_lazy as _
from arches.app.models.system_settings import settings
from django.contrib.postgres.fields import JSONField
from django.db.models.sql.compiler import SQLInsertCompiler, SQLUpdateCompiler
from django.utils.translation import get_language


class I18n_String(object):
    def __init__(self, value=None, lang=None, use_nulls=False, attname=None):
        self.attname = attname
        self.value = value
        self.raw_value = {}
        self.value_is_primitive = False
        self.lang = get_language() if lang is None else lang

        self._parse(self.value, self.lang, use_nulls)

    def _parse(self, value, lang, use_nulls):
        ret = {}

        if isinstance(value, str):
            try:
                ret = json.loads(value)
            except:
                ret[lang] = value
                self.value_is_primitive = True
        elif value is None:
            ret[lang] = None if use_nulls else ""
        elif isinstance(value, I18n_String):
            ret = value.raw_value
        elif isinstance(value, dict):
            ret = value
        self.raw_value = ret

    def as_sql(self, compiler, connection):
        """
        The "as_sql" method of this class is called by Django when the sql statement
        for each field in a model instance is being generated.
        If we're inserting a new value then we can just set the localzed column to the json object.
        If we're updating a value for a specific language, then use the postgres "jsonb_set" command to do that
        https://www.postgresql.org/docs/9.5/functions-json.html
        """

        if (self.value_is_primitive or self.value is None) and not isinstance(compiler, SQLInsertCompiler):
            self.sql = "jsonb_set(" + self.attname + ", %s, %s)"
            params = (f"{{{self.lang}}}", json.dumps(self.value))
        else:
            params = [json.dumps(self.raw_value)]
            self.sql = "%s"

        return self.sql, params

    # need this to avoid a Django error when setting
    # the default value on the i18n_TextField
    def __call__(self):
        return self

    def __str__(self):
        ret = None
        try:
            ret = self.raw_value[get_language()]
        except KeyError as e:
            try:
                # if you can't return the requested language because the value doesn't exist then
                # return the default language.
                # the reasoning is that for display in the UI, we want to show what the user initially entered
                ret = self.raw_value[settings.LANGUAGE_CODE]
            except KeyError as e:
                try:
                    # if the default language doesn't exist then return the first language available
                    ret = list(self.raw_value.values())[0]
                except:
                    # if there are no languages available return an empty string
                    ret = ""
        return json.dumps(ret) if ret is None else ret

    def serialize(self):
        return str(self)


class I18n_TextField(JSONField):
    description = _("A I18n_TextField object")

    def __init__(self, *args, **kwargs):
        use_nulls = kwargs.get("null", False)
        kwargs["default"] = I18n_String(use_nulls=use_nulls)
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        print("in from_db_value")
        if value is not None:
            return I18n_String(value)
        return None

    def to_python(self, value):
        print("in to_python")
        if isinstance(value, I18n_String):
            return value
        if value is None:
            return value
        value = super().to_python(value)
        return I18n_String(value)

    def get_prep_value(self, value):
        print(type(value))
        print(f"in get_prep_value, value={value}")
        """
        If the value was set to a string, then check to see if it's 
        a json object like {"en": "boat", "es": "barco"}, or just a simple string like "boat".
        If it's a json object then use the I18n_String.as_sql method to insert it directly to the database.
        If it's just a simple string then use the I18n_String.as_sql method to update one language value
        out of potentially several previously stored languages using the currently active language.
        See I18n_String.as_sql to see how this magic happens.  :)
        """

        return I18n_String(value, attname=self.attname)
