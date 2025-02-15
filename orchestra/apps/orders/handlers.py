import calendar
import datetime

from dateutil import relativedelta
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from orchestra.utils import plugins
from orchestra.utils.python import AttributeDict

from . import settings
from .helpers import get_register_or_cancel_events, get_register_or_renew_events


class ServiceHandler(plugins.Plugin):
    """
    Separates all the logic of billing handling from the model allowing to better
    customize its behaviout
    """
    
    model = None
    
    __metaclass__ = plugins.PluginMount
    
    def __init__(self, service):
        self.service = service
    
    def __getattr__(self, attr):
        return getattr(self.service, attr)
    
    @classmethod
    def get_plugin_choices(cls):
        choices = super(ServiceHandler, cls).get_plugin_choices()
        return [('', _("Default"))] + choices
    
    def get_content_type(self):
        if not self.model:
            return self.content_type
        app_label, model = self.model.split('.')
        return ContentType.objects.get_by_natural_key(app_label, model.lower())
    
    def matches(self, instance):
        safe_locals = {
            instance._meta.model_name: instance
        }
        return eval(self.match, safe_locals)
    
    def get_metric(self, instance):
        if self.metric:
            safe_locals = {
                instance._meta.model_name: instance
            }
            return eval(self.metric, safe_locals)
    
    def get_billing_point(self, order, bp=None, **options):
        not_cachable = self.billing_point == self.FIXED_DATE and options.get('fixed_point')
        if not_cachable or bp is None:
            bp = options.get('billing_point', timezone.now().date())
            if not options.get('fixed_point'):
                msg = ("Support for '%s' period and '%s' point is not implemented"
                    % (self.get_billing_period_display(), self.get_billing_point_display()))
                if self.billing_period == self.MONTHLY:
                    date = bp
                    if self.payment_style == self.PREPAY:
                        date += relativedelta.relativedelta(months=1)
                    if self.billing_point == self.ON_REGISTER:
                        day = order.registered_on.day
                    elif self.billing_point == self.FIXED_DATE:
                        day = 1
                    else:
                        raise NotImplementedError(msg)
                    bp = datetime.datetime(year=date.year, month=date.month, day=day,
                        tzinfo=timezone.get_current_timezone())
                elif self.billing_period == self.ANUAL:
                    if self.billing_point == self.ON_REGISTER:
                        month = order.registered_on.month
                        day = order.registered_on.day
                    elif self.billing_point == self.FIXED_DATE:
                        month = settings.ORDERS_SERVICE_ANUAL_BILLING_MONTH
                        day = 1
                    else:
                        raise NotImplementedError(msg)
                    year = bp.year
                    if self.payment_style == self.POSTPAY:
                        year = bo.year - relativedelta.relativedelta(years=1)
                    if bp.month >= month:
                        year = bp.year + 1
                    bp = datetime.datetime(year=year, month=month, day=day,
                        tzinfo=timezone.get_current_timezone())
                elif self.billing_period == self.NEVER:
                    bp = order.registered_on
                else:
                    raise NotImplementedError(msg)
        if self.on_cancel != self.NOTHING and order.cancelled_on and order.cancelled_on < bp:
            return order.cancelled_on
        return bp
    
    def get_pricing_size(self, ini, end):
        rdelta = relativedelta.relativedelta(end, ini)
        if self.get_pricing_period() == self.MONTHLY:
            size = rdelta.months
            days = calendar.monthrange(end.year, end.month)[1]
            size += float(rdelta.days)/days
        elif self.get_pricing_period() == self.ANUAL:
            size = rdelta.years
            days = 366 if calendar.isleap(end.year) else 365
            size += float((end-ini).days)/days
        elif self.get_pricing_period() == self.NEVER:
            size = 1
        else:
            raise NotImplementedError
        return size
    
    def get_pricing_slots(self, ini, end):
        period = self.get_pricing_period()
        if period == self.MONTHLY:
            rdelta = relativedelta.relativedelta(months=1)
        elif period == self.ANUAL:
            rdelta = relativedelta.relativedelta(years=1)
        elif period == self.NEVER:
            yield ini, end
            raise StopIteration
        else:
            raise NotImplementedError
        while True:
            next = ini + rdelta
            if next >= end:
                yield ini, end
                break
            yield ini, next
            ini = next
    
    def get_price_with_orders(self, order, size, ini, end):
        porders = self.orders.filter(account=order.account).filter(
            Q(cancelled_on__isnull=True) | Q(cancelled_on__gt=ini)
            ).filter(registered_on__lt=end).order_by('registered_on')
        price = 0
        if self.orders_effect == self.REGISTER_OR_RENEW:
            events = get_register_or_renew_events(porders, order, ini, end)
        elif self.orders_effect == self.CONCURRENT:
            events = get_register_or_cancel_events(porders, order, ini, end)
        else:
            raise NotImplementedError
        for metric, position, ratio in events:
            price += self.get_price(order, metric, position=position) * size * ratio
        return price
    
    def get_price_with_metric(self, order, size, ini, end):
        metric = order.get_metric(ini, end)
        price = self.get_price(order, metric) * size
        return price
    
    def generate_line(self, order, price, size, ini, end):
        subtotal = float(self.nominal_price) * size
        discounts = []
        if subtotal > price:
            discounts.append(AttributeDict(**{
                'type': 'volume',
                'total': price-subtotal
            }))
        elif subtotal < price:
            raise ValueError("Something is wrong!")
        return AttributeDict(**{
            'order': order,
            'subtotal': subtotal,
            'size': size,
            'ini': ini,
            'end': end,
            'discounts': discounts,
        })
    
    def generate_bill_lines(self, orders, **options):
        # For the "boundary conditions" just think that:
        #   date(2011, 1, 1) is equivalent to datetime(2011, 1, 1, 0, 0, 0)
        #   In most cases:
        #       ini >= registered_date, end < registered_date
        
        # TODO Perform compensations on cancelled services
        if self.on_cancel in (self.COMPENSATE, self.REFOUND):
            pass
            # TODO compensations with commit=False, fuck commit or just fuck the transaction?
            # compensate(orders, **options)
            # TODO create discount per compensation
        bp = None
        lines = []
        commit = options.get('commit', True)
        for order in orders:
            bp = self.get_billing_point(order, bp=bp, **options)
            ini = order.billed_until or order.registered_on
            if bp <= ini:
                continue
            if not self.metric:
                # Number of orders metric; bill line per order
                size = self.get_pricing_size(ini, bp)
                price = self.get_price_with_orders(order, size, ini, bp)
                lines.append(self.generate_line(order, price, size, ini, bp))
            else:
                # weighted metric; bill line per pricing period
                for ini, end in self.get_pricing_slots(ini, bp):
                    size = self.get_pricing_size(ini, end)
                    price = self.get_price_with_metric(order, size, ini, end)
                    lines.append(self.generate_line(order, price, size, ini, end))
            order.billed_until = bp
            if commit:
                order.save()
        return lines
    
    def compensate(self, orders):
        # TODO this compensation is a bit hard to write it propertly
        #      don't forget to think about weighted and num order prices.
        # Greedy algorithm for maximizing discount (non-deterministic)
        # Reduce and break orders in donors and receivers
        donors = []
        receivers = []
        for order in orders:
            if order.cancelled_on and order.billed_until > order.cancelled_on:
                donors.append(order)
            elif not order.cancelled_on or order.cancelled_on > order.billed_until:
                receivers.append(order)
        
        # Assign weights to every donor-receiver combination
        weights = []
        for donor in donors:
            for receiver in receivers:
                if receiver.cancelled_on:
                    if not receiver.cancelled_on or receiver.cancelled_on < donor.billed_until:
                        end = receiver.cancelled_on
                    else:
                        end = donor.billed_until
                else:
                    end = donor.billed_until
                ini = donor.billed_until or donor.registered_on
                if donor.cancelled_on > ini:
                    ini = donor.cancelled_on
                weight = (end-ini).days
                weights.append((weight, ini, end, donor, receiver))
        
        # Choose weightest pairs
        choosen = []
        weights.sort(key=lambda n: n[0])
        for weight, ini, end, donor, receiver in weigths:
            if donor not in choosen and receiver not in choosen:
                choosen += [donor, receiver]
                donor.billed_until = end
                donor.save()
                price = self.get_price()#TODO
                receiver.__discount_per_compensation =None
