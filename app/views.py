import calendar
from typing import List
from flask import render_template, redirect,request
from flask.helpers import flash
from flask_appbuilder.models.sqla.interface import SQLAInterface as _SQLAInterface,log
from flask_appbuilder.widgets import ListThumbnail, ListWidget, \
    ListItem, ListBlock, ShowBlockWidget, ListLinkWidget
from flask_appbuilder.actions import action
from flask_appbuilder.models.group import aggregate_count, aggregate_avg, aggregate_sum
from flask_appbuilder.views import MasterDetailView, ModelView as _ModelView
from flask_appbuilder.baseviews import expose, BaseView
from flask_appbuilder.charts.views import DirectByChartView, GroupByChartView
from flask_babel import lazy_gettext as _
from werkzeug.exceptions import abort

from . import db, appbuilder
from .models import ContactGroup, Gender, Contact, CountryStats, Country
import time,re
from flask_appbuilder import Model
from flask_appbuilder._compat import as_unicode

from sqlalchemy.exc import IntegrityError
from flask_appbuilder.const import LOGMSG_ERR_DBI_DEL_GENERIC, LOGMSG_WAR_DBI_DEL_INTEGRITY

class SQLAInterface(_SQLAInterface):
    def before_delete(self, items: List[Model]) -> bool:
        try:
            for item in items:
                # self._delete_files(item)
                # self.session.delete(item)
                item.deleted_time = time.time()
            self.session.commit()
            self.message = (as_unicode(self.delete_row_message), "success")
            return True
        except IntegrityError as e:
            self.message = (as_unicode(self.delete_integrity_error_message), "warning")
            log.warning(LOGMSG_WAR_DBI_DEL_INTEGRITY.format(str(e)))
            self.session.rollback()
            return False
        except Exception as e:
            self.message = (
                as_unicode(self.general_error_message + " " + str(sys.exc_info()[0])),
                "danger",
            )
            log.exception(LOGMSG_ERR_DBI_DEL_GENERIC.format(str(e)))
            self.session.rollback()
            return False    
    def delete_all(self, items: List[Model]) -> bool:
        try:
            for item in items:
                # self._delete_files(item)
                # self.session.delete(item)
                item.deleted_time = time.time()
            self.session.commit()
            self.message = (as_unicode(self.delete_row_message), "success")
            return True
        except IntegrityError as e:
            self.message = (as_unicode(self.delete_integrity_error_message), "warning")
            log.warning(LOGMSG_WAR_DBI_DEL_INTEGRITY.format(str(e)))
            self.session.rollback()
            return False
        except Exception as e:
            self.message = (
                as_unicode(self.general_error_message + " " + str(sys.exc_info()[0])),
                "danger",
            )
            log.exception(LOGMSG_ERR_DBI_DEL_GENERIC.format(str(e)))
            self.session.rollback()
            return False
    def delete(self, item: Model, raise_exception: bool = False) -> bool:
        try:
            # self._delete_files(item)
            # self.session.delete(item)
            item.deleted_time = time.time()
            self.session.commit()
            self.message = (as_unicode(self.delete_row_message), "success")
            return True
        except IntegrityError as e:
            self.message = (as_unicode(self.delete_integrity_error_message), "warning")
            log.warning(LOGMSG_WAR_DBI_DEL_INTEGRITY.format(str(e)))
            self.session.rollback()
            if raise_exception:
                raise e
            return False
        except Exception as e:
            self.message = (
                as_unicode(self.general_error_message + " " + str(sys.exc_info()[0])),
                "danger",
            )
            log.exception(LOGMSG_ERR_DBI_DEL_GENERIC.format(str(e)))
            self.session.rollback()
            if raise_exception:
                raise e
            return False

class ModelView(_ModelView):
    def __init__(self,**kwargs):
        model = self.datamodel
        list_columns=model.get_columns_list()
        # print(list_columns)
        self.list_columns=[x for x in list_columns if not (x in ['deleted_time','id']  or x.endswith('_id'))]
        self.add_exclude_columns = [
        "deleted_time"]
        self.edit_exclude_columns = self.add_exclude_columns        
        super(ModelView, self).__init__(**kwargs)

    
    def _list(self):
        match=False
        for arg in request.args:
            re_match = re.findall("_flt_(\d)_(deleted_time)", arg)
            if re_match:
                match= True
                break
        query_cls =self.datamodel.session.session_factory.kw['query_cls']
        if match:
            query_cls._with_deleted=True
        else:
            query_cls._with_deleted=False
        return super()._list()


class ContactModelView(ModelView):
    datamodel = SQLAInterface(Contact)

    label_columns = {'contact_group.name': 'Contacts Group'}
    list_columns = ['name', 'personal_celphone', 'birthday', 'contact_group.name']
    list_template = 'contact.html'
    base_order = ('name', 'asc')

    show_fieldsets = [
        ('Summary', {'fields': ['name', 'gender', 'contact_group']}),
        (
            'Personal Info',
            {'fields': [
                'address',
                'birthday',
                'personal_phone',
                'personal_celphone'
            ], 'expanded': False}),
    ]

    add_fieldsets = show_fieldsets

    edit_fieldsets = show_fieldsets

    @action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False)
    def muldelete(self, items):
        self.datamodel.delete_all(items)
        self.update_redirect()
        return redirect(self.get_redirect())


class ContactItemModelView(ContactModelView):
    list_title = 'List Contact (Items)'
    list_widget = ListItem
    list_template = 'contact_item.html'


class ContactThumbnailModelView(ContactModelView):
    list_title = 'List Contact (Thumbnails)'
    list_widget = ListThumbnail
    list_template = 'contact_thumbnail.html'


class ContactBlockModelView(ContactModelView):
    list_title = 'List Contact (Blocks)'
    list_widget = ListBlock
    show_widget = ShowBlockWidget
    list_template = 'contact_block.html'


class ContactLinkModelView(ContactModelView):
    list_title = 'List Contact (Links)'
    list_widget = ListLinkWidget
    list_template = 'contact_link.html'


class GroupModelView(ModelView):
    datamodel = SQLAInterface(ContactGroup)
    related_views = [
        ContactModelView,
        ContactItemModelView,
        ContactThumbnailModelView,
        ContactBlockModelView
    ]
    list_template = 'contact_group.html'
    add_template = 'contact_group_add.html'
    edit_template = 'contact_group_edit.html'
    show_template = 'contact_group_show.html'

    def pre_delete(self, item):
        data = db.session.query(Contact).filter(Contact.contact_group_id==item.id)
        self.datamodel.delete_all(data)
        return super().pre_delete(item)


class ContactChartView(GroupByChartView):
    datamodel = SQLAInterface(Contact)
    chart_title = 'Grouped contacts'
    label_columns = ContactModelView.label_columns
    chart_type = 'PieChart'

    definitions = [
        {
            'group' : 'contact_group.name',
            'series' : [(aggregate_count,'contact_group')]
        },
        {
            'group' : 'gender.name',
            'series' : [(aggregate_count,'contact_group')]
        }
    ]


def pretty_month_year(value):
    return calendar.month_name[value.month] + ' ' + str(value.year)


def pretty_year(value):
    return str(value.year)


class ContactTimeChartView(GroupByChartView):
    datamodel = SQLAInterface(Contact)

    chart_title = 'Grouped Birth contacts'
    chart_type = 'AreaChart'
    label_columns = ContactModelView.label_columns
    definitions = [
        {
            'group' : 'month_year',
            'formatter': pretty_month_year,
            'series': [(aggregate_count,'contact_group')]
        },
        {
            'group': 'year',
            'formatter': pretty_year,
            'series': [(aggregate_count,'contact_group')]
        }
    ]


class GroupMasterView(MasterDetailView):
    datamodel = SQLAInterface(ContactGroup)
    related_views = [ContactModelView]

#-----------------------------------------------------
#-----------------------------------------------------


def pretty_month_year(value):
    return calendar.month_name[value.month] + ' ' + str(value.year)


def pretty_year(value):
    return str(value.year)


class CountryStatsModelView(ModelView):
    datamodel = SQLAInterface(CountryStats)
    list_columns = ['country', 'stat_date', 'population', 'unemployed', 'college']
    base_permissions = ['can_list', 'can_show']


class CountryDirectChartView(DirectByChartView):
    datamodel = SQLAInterface(CountryStats)
    chart_title = 'Direct Data Chart Example'

    definitions = [
        {
            'group': 'stat_date',
            'series': ['unemployed', 'college']
        }
    ]


class CountryGroupByChartView(GroupByChartView):
    datamodel = SQLAInterface(CountryStats)
    chart_title = 'Grouped Data Example'

    definitions = [
        {
            'label': 'Country Stat',
            'group': 'country.name',
            'series': [(aggregate_sum, 'unemployed'),
                       (aggregate_sum, 'population'),
                       (aggregate_sum, 'college')
            ]
        },
        {
            'label': 'Monthly',
            'group': 'month_year',
            'formatter': pretty_month_year,
            'series': [(aggregate_sum, 'unemployed'),
                       (aggregate_sum, 'population'),
                       (aggregate_sum, 'college')
            ]
        },
        {
            'label': 'Yearly',
            'group': 'year',
            'formatter': pretty_year,
            'series': [(aggregate_sum, 'unemployed'),
                       (aggregate_sum, 'population'),
                       (aggregate_sum, 'college')
            ]
        }
    ]


class CountryPieGroupByChartView(GroupByChartView):
    datamodel = SQLAInterface(CountryStats)
    chart_title = 'Grouped Data Example (Pie)'
    chart_type = 'PieChart'

    definitions = [
        {
            'label': 'Country Stat',
            'group': 'country.name',
            'series': [(aggregate_sum, 'unemployed')
            ]
        }
    ]


class MasterGroupByChartView(MasterDetailView):
    datamodel = SQLAInterface(Country)
    base_order = ('name','asc')
    related_views = [CountryDirectChartView]


appbuilder.add_view(GroupModelView, "List Groups", icon="fa-folder-open-o", label=_('List Groups'),
                category="Contacts", category_icon='fa-envelope', category_label=_('Contacts'))
appbuilder.add_view(GroupMasterView, "Master Detail Groups", icon="fa-folder-open-o",
                label=_("Master Detail Groups"), category="Contacts")
appbuilder.add_view(ContactModelView, "List Contacts", icon="fa-envelope",
                label=_('List Contacts'), category="Contacts")

appbuilder.add_view(ContactLinkModelView, "List Links Contacts", icon="fa-envelope", category="Contacts")
appbuilder.add_view(ContactItemModelView, "List Item Contacts", icon="fa-envelope", category="Contacts")
appbuilder.add_view(ContactBlockModelView, "List Block Contacts", icon="fa-envelope", category="Contacts")
appbuilder.add_view(ContactThumbnailModelView, "List Thumb Contacts", icon="fa-envelope", category="Contacts")

appbuilder.add_separator("Contacts")
appbuilder.add_view(ContactChartView, "Contacts Chart", icon="fa-dashboard",
                label=_('Contacts Chart'), category="Contacts")
appbuilder.add_view(ContactTimeChartView, "Contacts Birth Chart", icon="fa-dashboard",
                label=_('Contacts Birth Chart'), category="Contacts")

appbuilder.add_view(CountryStatsModelView, "Chart Data (Country)", icon="fa-globe",
                label=_('Chart Data (Country)'), category_icon="fa-dashboard", category="Chart Examples")
appbuilder.add_view(CountryDirectChartView, "Direct Chart Example", icon="fa-bar-chart-o",
                label=_('Direct Chart Example'), category="Chart Examples")
appbuilder.add_view(MasterGroupByChartView, "Master Chart Example", icon="fa-bar-chart-o",
                label=_('Master Detail Chart Example'), category="Chart Examples")
appbuilder.add_view(CountryGroupByChartView, "Group By Chart Example", icon="fa-bar-chart-o",
                label=_('Group By Chart Example'), category="Chart Examples")
appbuilder.add_view(CountryPieGroupByChartView, "Group By Pie Chart Example", icon="fa-bar-chart-o",
                label=_('Group By Pie Chart Example'), category="Chart Examples")


if appbuilder.app.config['FAB_API_SWAGGER_UI'] :
    appbuilder.add_link("swagger","/swagger/v1",icon="fas fa-code")

# adjust security menu to the last.
from flask_appbuilder.menu import Menu


def adjust_menu(self):
    old_menu = self.menu
    new_menu = old_menu[1:]
    new_menu.append(old_menu[0])
    self.menu = new_menu


Menu.adjust_menu = adjust_menu
appbuilder.menu.adjust_menu()

# add active status of menu items.
from flask_appbuilder.menu import MenuItem
def is_active(self):
    
    if self.childs:
        for c in self.childs:
            if c.is_active():
                return True
    else:        
        if request.path == self.get_url():
            return True
        else :
            if self.baseview :
                if request.blueprint == self.baseview.blueprint.name:
                    return True

    return False


MenuItem.is_active = is_active    