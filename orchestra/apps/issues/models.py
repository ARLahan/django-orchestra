from django.conf import settings as djsettings
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from orchestra.apps.contacts import settings as contacts_settings
from orchestra.apps.contacts.models import Contact
from orchestra.models.fields import MultiSelectField
from orchestra.utils import send_email_template

from . import settings


class Queue(models.Model):
    name = models.CharField(_("name"), max_length=128, unique=True)
    default = models.BooleanField(_("default"), default=False)
    notify = MultiSelectField(_("notify"), max_length=256, blank=True,
            choices=Contact.EMAIL_USAGES,
            default=contacts_settings.CONTACTS_DEFAULT_EMAIL_USAGES,
            help_text=_("Contacts to notify by email"))
    
    def __unicode__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """ mark as default queue if needed """
        existing_default = Queue.objects.filter(default=True)
        if self.default:
            existing_default.update(default=False)
        elif not existing_default:
            self.default = True
        super(Queue, self).save(*args, **kwargs)


class Ticket(models.Model):
    HIGH = 'HIGH'
    MEDIUM = 'MEDIUM'
    LOW = 'LOW'
    PRIORITIES = (
        (HIGH, 'High'),
        (MEDIUM, 'Medium'),
        (LOW, 'Low'),
    )
    
    NEW = 'NEW'
    IN_PROGRESS = 'IN_PROGRESS'
    RESOLVED = 'RESOLVED'
    FEEDBACK = 'FEEDBACK'
    REJECTED = 'REJECTED'
    CLOSED = 'CLOSED'
    STATES = (
        (NEW, 'New'),
        (IN_PROGRESS, 'In Progress'),
        (RESOLVED, 'Resolved'),
        (FEEDBACK, 'Feedback'),
        (REJECTED, 'Rejected'),
        (CLOSED, 'Closed'),
    )
    
    creator = models.ForeignKey(djsettings.AUTH_USER_MODEL, verbose_name=_("created by"),
            related_name='tickets_created', null=True)
    creator_name = models.CharField(_("creator name"), max_length=256, blank=True)
    owner = models.ForeignKey(djsettings.AUTH_USER_MODEL, null=True, blank=True,
            related_name='tickets_owned', verbose_name=_("assigned to"))
    queue = models.ForeignKey(Queue, related_name='tickets', null=True, blank=True)
    subject = models.CharField(_("subject"), max_length=256)
    description = models.TextField(_("description"))
    priority = models.CharField(_("priority"), max_length=32, choices=PRIORITIES,
            default=MEDIUM)
    state = models.CharField(_("state"), max_length=32, choices=STATES, default=NEW)
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    last_modified_on = models.DateTimeField(_("last modified on"), auto_now=True)
    cc = models.TextField("CC", help_text=_("emails to send a carbon copy to"),
            blank=True)
    
    class Meta:
        ordering = ["-last_modified_on"]
    
    def __unicode__(self):
        return unicode(self.pk)
    
    def get_notification_emails(self):
        """ Get emails of the users related to the ticket """
        emails = list(settings.ISSUES_SUPPORT_EMAILS)
        emails.append(self.creator.email)
        if self.owner:
            emails.append(self.owner.email)
        for contact in self.creator.account.contacts.all():
            if self.queue and set(contact.email_usage).union(set(self.queue.notify)):
                emails.append(contact.email)
        for message in self.messages.distinct('author'):
            emails.append(message.author.email)
        return set(emails + self.get_cc_emails())
        
    def notify(self, message=None, content=None):
        """ Send an email to ticket stakeholders notifying an state update """
        emails = self.get_notification_emails()
        template = 'issues/ticket_notification.mail'
        html_template = 'issues/ticket_notification_html.mail'
        context = {
            'ticket': self,
            'ticket_message': message
        }
        send_email_template(template, context, emails, html=html_template)
    
    def save(self, *args, **kwargs):
        """ notify stakeholders of new ticket """
        new_issue = not self.pk
        if not self.creator_name and self.creator:
            self.creator_name = self.creator.get_full_name()
        super(Ticket, self).save(*args, **kwargs)
        if new_issue:
            # PK should be available for rendering the template
            self.notify()
    
    def is_involved_by(self, user):
        """ returns whether user has participated or is referenced on the ticket
            as owner or member of the group
        """
        return Ticket.objects.filter(pk=self.pk).involved_by(user).exists()
    
    def get_cc_emails(self):
        return self.cc.split(',') if self.cc else []
    
    def mark_as_read_by(self, user):
        self.trackers.get_or_create(user=user)
    
    def mark_as_unread_by(self, user):
        self.trackers.filter(user=user).delete()
    
    def mark_as_unread(self):
        self.trackers.all().delete()
    
    def is_read_by(self, user):
        return self.trackers.filter(user=user).exists()
    
    def reject(self):
        self.state = Ticket.REJECTED
        self.save()
    
    def resolve(self):
        self.state = Ticket.RESOLVED
        self.save()
    
    def close(self):
        self.state = Ticket.CLOSED
        self.save()
    
    def take(self, user):
        self.owner = user
        self.save()


class Message(models.Model):
    ticket = models.ForeignKey('issues.Ticket', verbose_name=_("ticket"),
            related_name='messages')
    author = models.ForeignKey(djsettings.AUTH_USER_MODEL, verbose_name=_("author"),
            related_name='ticket_messages')
    author_name = models.CharField(_("author name"), max_length=256, blank=True)
    content = models.TextField(_("content"))
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    
    class Meta:
        get_latest_by = "created_on"
    
    def __unicode__(self):
        return u"#%i" % self.id
    
    def save(self, *args, **kwargs):
        """ notify stakeholders of ticket update """
        if not self.pk:
            self.ticket.mark_as_unread()
            self.ticket.mark_as_read_by(self.author)
            self.ticket.notify(message=self)
            self.author_name = self.author.get_full_name()
        super(Message, self).save(*args, **kwargs)
    
    @property
    def number(self):
        return self.ticket.messages.filter(id__lte=self.id).count()


class TicketTracker(models.Model):
    """ Keeps track of user read tickets """
    ticket = models.ForeignKey(Ticket, verbose_name=_("ticket"),
            related_name='trackers')
    user = models.ForeignKey(djsettings.AUTH_USER_MODEL, verbose_name=_("user"),
            related_name='ticket_trackers')
    
    class Meta:
        unique_together = (('ticket', 'user'),)
