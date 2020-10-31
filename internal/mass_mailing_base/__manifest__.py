{
    'name': 'Mass Mailing Base',
    'summary': 'Base for mass mailing sms messages',
    'description': '',
    'version': '13.0.0.2.1',
    'author': 'SUNNIT',
    'category': 'Marketing/Email Marketing',
    'contributors': [
        'Hendrix Costa <hendrix@sunnit.com.br>',
    ],
    'depends': [
        'mass_mailing_sms', 'utm'
    ],
    'data': [
        'wizard/sms_composer_views.xml',
        'views/sms_sms_views.xml',
        'views/utm_campaign_views.xml',
        'views/mailing_mailing_view.xml',
        'data/utm_data.xml',
    ],
    'demo': [
    ],
    'application': True,
}
