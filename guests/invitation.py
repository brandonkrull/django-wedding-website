from email.mime.image import MIMEImage
import os
import time
import tqdm
import pickle
from datetime import datetime
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.http import Http404
from django.template.loader import render_to_string
from guests.models import Party, MEALS

INVITATION_TEMPLATE = 'guests/email_templates/invitation.html'

'''
in the case of needing to add new parties and send invites to them, 
use the django admin web interface to create party and add guests, 
making sure check the 'is invited' box and change their party type
to 'dimagi'. the send all invitations function filters out everybody except 
those parties, making it easy to send to only a specific set of parties.
'''

def guess_party_by_invite_id_or_404(invite_id):
    try:
        return Party.objects.get(invitation_id=invite_id)
    except Party.DoesNotExist:
        if settings.DEBUG:
            # in debug mode allow access by ID
            return Party.objects.get(id=int(invite_id))
        else:
            raise Http404()


def get_invitation_context(party):
    return {
        'title': "Crescent Bay",
        'header_filename': 'hearts.png',
        'main_image': 'ab.jpg',
        'main_color': '#fff',
        'font_color': '#000',
        'page_title': "Alysa and Brandon's Wedding - You're Invited!",
        'preheader_text': "You are invited!",
        'invitation_id': party.invitation_id,
        'party': party,
        'meals': MEALS,
    }


def send_invitation_email(party, test_only=False, recipients=None):
    if recipients is None:
        recipients = party.guest_emails
    if not recipients:
        print '===== WARNING: no valid email addresses found for {} ====='.format(party)
        return

    print party.guest_emails
    context = get_invitation_context(party)
    context['email_mode'] = True
    template_html = render_to_string(INVITATION_TEMPLATE, context=context)
    template_text = "You're invited to Alysa and Brandon's wedding. To view this invitation, visit {} in any browser.".format(
        reverse('invitation', args=[context['invitation_id']])
    )
    #subject = "You're invited! RSVP Reminder!"
    subject = "You're invited! Please RSVP by Feb. 25!"
    # https://www.vlent.nl/weblog/2014/01/15/sending-emails-with-embedded-images-in-django/
    msg = EmailMultiAlternatives(subject, template_text,
                                 'Alysa and Brandon <hi@afbk.love>', recipients)
    msg.attach_alternative(template_html, "text/html")
    msg.mixed_subtype = 'related'
    for filename in (context['header_filename'], context['main_image']):
        attachment_path = os.path.join(os.path.dirname(__file__), 'static', 'invitation', 'images', filename)
        with open(attachment_path, "rb") as image_file:
            msg_img = MIMEImage(image_file.read())
            msg_img.add_header('Content-ID', '<{}>'.format(filename))
            msg.attach(msg_img)

    print 'sending invitation to {} ({})'.format(party.name, ', '.join(recipients))
    if not test_only:
        msg.send()


def send_all_invitations(test_only, mark_as_sent):
    to_send_to = Party.in_default_order().filter(type='dimagi')
    sent_invites = []
    k = 0
    for party in tqdm.tqdm(to_send_to):
	print party.name
        send_invitation_email(party, test_only=test_only)
        if mark_as_sent:
            party.invitation_sent = datetime.now()
            party.save()
        sent_invites.append(party.name)
        time.sleep(10)

#    with open('sent_invites.pkl', 'wb') as pkl:
#    	pickle.dump(sent_invites, pkl)
