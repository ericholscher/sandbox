"""
YAML serializer with foreignkey following.

Requires PyYaml (http://pyyaml.org/), but that's checked for in __init__.

Add this to your settings.
SERIALIZATION_MODULES = {
    "yamlfk" : "sandbox.ctyaml",
}

Then use it with dumpdata and loaddata --format=yamlfk
"""

from StringIO import StringIO
import yaml

from django.conf import settings
from django.core.serializers import base
from django.db import models
from django.core.serializers.pyyaml import Serializer as YAMLSerializer
from django.core.serializers.python import _get_model

from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_unicode


class Serializer(YAMLSerializer):
    """
    Convert a queryset to YAML.
    """
    def handle_fk_field(self, obj, field):
        related = getattr(obj, field.name)
        if related is not None:
            unique_fields = get_unique_fields(related)
            if unique_fields:
                lookup_dict = {}
                for inner_field in unique_fields:
                    lookup_dict[inner_field.name] = getattr(related, inner_field.get_attname())
                related = lookup_dict
            elif field.rel.field_name == related._meta.pk.name:
                # Related to remote object via primary key
                related = related._get_pk_val()
            else:
                # Related to remote object via other field
                related = getattr(related, field.rel.field_name)

        if isinstance(related, dict):
            self._current[field.name] = related
        else:
            self._current[field.name] = smart_unicode(related, strings_only=True)

def Deserializer(stream_or_string, **options):
    """
    Deserialize a stream or string of YAML data.

    ********
    All this is copied from the python base deserializer but for 2 lines
    ********
    """
    if isinstance(stream_or_string, basestring):
        stream = StringIO(stream_or_string)
    else:
        stream = stream_or_string
    object_list = yaml.load(stream)

    models.get_apps()
    for d in object_list:
        # Look up the model and starting build a dict of data for it.
        Model = _get_model(d["model"])
        data = {Model._meta.pk.attname : Model._meta.pk.to_python(d["pk"])}
        m2m_data = {}

        # Handle each field
        for (field_name, field_value) in d["fields"].iteritems():
            if isinstance(field_value, str):
                field_value = smart_unicode(field_value, options.get("encoding", settings.DEFAULT_CHARSET), strings_only=True)

            field = Model._meta.get_field(field_name)

            # Handle M2M relations
            if field.rel and isinstance(field.rel, models.ManyToManyRel):
                m2m_convert = field.rel.to._meta.pk.to_python
                m2m_data[field.name] = [m2m_convert(smart_unicode(pk)) for pk in field_value]

            # Handle FK fields
            elif field.rel and isinstance(field.rel, models.ManyToOneRel):
                if field_value is not None:
                    #These are those 2 lines ******
                    if isinstance(field_value, dict):
                        field_value = field.rel.to._default_manager.get(**field_value).pk
                    data[field.attname] = field.rel.to._meta.get_field(field.rel.field_name).to_python(field_value)
                else:
                    data[field.attname] = None

            # Handle all other fields
            else:
                data[field.name] = field.to_python(field_value)

        yield base.DeserializedObject(Model(**data), m2m_data)

def get_unique_fields(model):
    unique_fields = []
    for check in model._meta.unique_together:
        fields = [model._meta.get_field(f) for f in check]
        if len(fields) == len([f for f in fields if getattr(model, f.get_attname()) is not None]):
            unique_fields.extend(fields)

    # Gather a list of checks for fields declared as unique and add them to
    # the list of checks. Again, skip empty fields and any that did not validate.
    for f in model._meta.fields:
        if f.unique and getattr(model, f.get_attname()) is not None and not isinstance(f, models.AutoField):
            unique_fields.append(f)

    return unique_fields
