__doc__ = """
>>> from django.template import Token, TOKEN_TEXT
>>> from test_utils.templatetags.utils import parse_ttag
>>> parse_ttag('super_cool_tag for my_object as bob', ['as'])
{'tag_name': 'super_cool_tag', 'as': 'bob'}
>>> parse_ttag('super_cool_tag for my_object as bob', ['as', 'for'])
{'tag_name': 'super_cool_tag', 'as': 'bob', 'for': 'my_object'}
"""
