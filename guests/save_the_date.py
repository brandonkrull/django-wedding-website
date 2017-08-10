from __future__ import unicode_literals
from copy import copy
from email.mime.image import MIMEImage
import os
from datetime import datetime
import random
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.template.loader import render_to_string
from guests.models import Party

SAVE_THE_DATE_TEMPLATE = 'guests/email_templates/save_the_date.html'
SAVE_THE_DATE_CONTEXT_MAP = {
    'default': {
        'title': "Crescent Bay",
        'header_filename': 'hearts.png',
        'main_image': 'ab.jpg',
        'main_color': '#fff',
        'font_color': '#000',
    }
}


def send_all_save_the_dates(test_only=False, mark_as_sent=False):
    to_send_to = Party.in_default_order().filter(
        is_invited=True, save_the_date_sent=None)
    for party in to_send_to:
        send_save_the_date_to_party(party, test_only=test_only)
        if mark_as_sent:
            party.save_the_date_sent = datetime.now()
            party.save()


def send_save_the_date_to_party(party, test_only=False):
    context = get_save_the_date_context(get_template_id_from_party(party))
    recipients = party.guest_emails
    if not recipients:
        print '===== WARNING: no valid email addresses found for {} ====='.format(
            party)
    else:
        send_save_the_date_email(context, recipients, test_only=test_only)


def get_template_id_from_party(party):

    return 'default' 
def get_save_the_date_context(template_id):
    template_id = (template_id or '').lower()
    if template_id not in SAVE_THE_DATE_CONTEXT_MAP:
        template_id = 'lions-head'
    context = copy(SAVE_THE_DATE_CONTEXT_MAP[template_id])
    context['name'] = template_id
    context['page_title'] = 'Alysa and Brandon -- Save the date!'
    context['preheader_text'] = (
            "We're getting married and we hope you can join us! "
        )
    return context


def send_save_the_date_email(context, recipients, test_only=False):
    context['email_mode'] = True
    template_html = render_to_string(SAVE_THE_DATE_TEMPLATE, context=context)
    template_text = 'Save the date for Alysa and Brandon\'s wedding! March 30th, 2018. Anaheim, California. (e)Invitation to follow.'
    subject = 'Save the date!'
    # https://www.vlent.nl/weblog/2014/01/15/sending-emails-with-embedded-images-in-django/
    msg = EmailMultiAlternatives(subject, template_text,
                                 'Alysa and Brandon <hi@afbk.love>', recipients)
    msg.attach_alternative(template_html, "text/html")
    msg.mixed_subtype = 'related'
    for filename in (context['header_filename'], context['main_image']):
        attachment_path = os.path.join(
            os.path.dirname(__file__), 'static', 'save-the-date', 'images',
            filename)
        with open(attachment_path, "rb") as image_file:
            msg_img = MIMEImage(image_file.read())
            msg_img.add_header('Content-ID', '<{}>'.format(filename))
            msg.attach(msg_img)

    print 'sending {} to {}'.format(context['name'], ', '.join(recipients))
    if not test_only:
        msg.send()


def clear_all_save_the_dates():
    for party in Party.objects.exclude(save_the_date_sent=None):
        party.save_the_date_sent = None
        party.save()
