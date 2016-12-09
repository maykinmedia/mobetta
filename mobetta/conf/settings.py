from django.conf import settings

###############################
#                             #
# Settings for access control #
#                             #
###############################

# Function to use for determining whether a user can access Mobetta
ACCESS_CONTROL_FUNCTION = getattr(
    settings, 'MOBETTA_ACCESS_CONTROL_FUNCTION', None)

# Require users to be authenticated (and Superusers or in group "translators").
# Set this to False at your own risk
MOBETTA_REQUIRES_AUTH = getattr(settings, 'MOBETTA_REQUIRES_AUTH', True)

# Set to True to enable language-specific groups, which can be used to give
# different translators access to different languages. Instead of creating a
# 'translators` group, create individual per-language groups, e.g.
# 'translators-de', 'translators-fr', ...
MOBETTA_LANGUAGE_GROUPS = getattr(settings, 'MOBETTA_LANGUAGE_GROUPS', False)

##################################
#                                #
# Settings for optional features #
#                                #
##################################

USE_EDIT_LOGGING = getattr(settings, 'MOBETTA_USE_EDIT_LOGGING', True)

# Whether to use Microsoft Translate to offer suggestions. This requires
# installing `microsofttranslate` from PyPI, and also uses the settings
# `MS_TRANSLATE_CLIENT_ID` and `MS_TRANSLATE_CLIENT_SECRET`
USE_MS_TRANSLATE = getattr(settings, 'MOBETTA_USE_MS_TRANSLATE', False)

MOBETTA_PO_FILENAMES = getattr(settings, 'MOBETTA_PO_FILENAMES', ['django.po', 'djangojs.po'])
