from hermes.connectors.ocm import OCMClient

from .interface import Action


class EmailShopper(Action):
    """
    Actions required when emailing a shopper
    """
    MESSAGE_FAIL = 'Email failed for {}: {}'
    MESSAGE_ID = 'messageId'
    MESSAGE_SUCCESS = 'Email sent for {}: {}'
    RUN_ENV = 'prod'  # We ONLY run this script for production
    TEMPLATE_NAMESPACE = 'templateNamespaceKey'
    TEMPLATE_TYPE = 'templateTypeKey'
    _my_action = 'email'

    def __init__(self, _config):
        """
        :param _config: object containing required cert path and api url
        """
        _cert = (_config.get('PATH_TO_OCM_SSL_CRT'), _config.get('PATH_TO_OCM_SSL_KEY'))
        self._hermes_client = OCMClient(self.RUN_ENV, _cert)

    def confirm(self):
        self._confirm = self._inquire(self._question.format(self._my_action))

    def get_message(self):
        return '{} Shoppers (MUST use shopper ids ONLY!): {}'.format(self._my_action.upper(), self._confirm)

    def perform(self, _list_of_shoppers):
        """
        Sends OM templated email to shoppers.  Needs user to provide templateNamespaceKey and templateTypeKey
        :param _list_of_shoppers: list of shopper users to perform an action for
        :return: Boolean, String
        """
        _run_log = []
        _tmpl_name = self._inquire('Enter the {}: '.format(self.TEMPLATE_NAMESPACE))
        _tmpl_type = self._inquire('Enter the {}: '.format(self.TEMPLATE_TYPE))
        for _shopper in _list_of_shoppers:
            _params = {self.TEMPLATE_NAMESPACE: _tmpl_name,
                       self.TEMPLATE_TYPE: _tmpl_type,
                       'substitutionValues': {'ACCOUNT_NUMBER': _shopper}}
            try:
                _response = self._hermes_client.send_shopper_email(_params)
                # Successful response looks like: {'messageId': '9f7dead8-8f59-4fe1-805f-142d24ff331a'}
                if self.MESSAGE_ID in _response:
                    _run_log.append(self.MESSAGE_SUCCESS.format(_shopper, _response.get(self.MESSAGE_ID)))
                else:
                    _run_log.append(self.MESSAGE_FAIL.format(_shopper, _response))
            except Exception as e:
                _run_log.append(self.MESSAGE_FAIL.format(_shopper, e))

        return True, _run_log
