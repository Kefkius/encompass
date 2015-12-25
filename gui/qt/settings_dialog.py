from PyQt4.QtGui import *
from PyQt4.QtCore import *

from encompass.i18n import _
from encompass import chainparams
from encompass import paymentrequest
from encompass.util_coin import block_explorer_info, block_explorer

from amountedit import BTCkBEdit
from util import HelpLabel, Buttons, CloseButton

class ChainOptions(QWidget):
    def __init__(self, main_window, parent=None):
        super(ChainOptions, self).__init__(parent)
        self.gui = gui = main_window
        self.config = self.gui.config
        form = QFormLayout()

        nz_help = _('Number of zeros displayed after the decimal point. For example, if this is set to 2, "1." will be displayed as "1.00"')
        nz_label = HelpLabel(_('Zeros after decimal point') + ':', nz_help)
        nz = QSpinBox()
        nz.setRange(0, gui.decimal_point)
        nz.setValue(gui.num_zeros)
        if not self.config.is_modifiable('num_zeros'):
            for w in [nz, nz_label]: w.setEnabled(False)
        def on_nz():
            value = nz.value()
            if gui.num_zeros != value:
                gui.num_zeros = value
                self.config.set_key('num_zeros', value, True)
                gui.history_list.update()
                gui.address_list.update()
        nz.valueChanged.connect(on_nz)
        form.addRow(nz_label, nz)

        msg = _('Fee per kilobyte of transaction.') + '\n' \
              + _('If you enable dynamic fees, this parameter will be used as upper bound.')
        fee_label = HelpLabel(_('Transaction fee per kb') + ':', msg)
        fee_e = BTCkBEdit(gui.get_decimal_point, gui.base_unit)
        fee_e.setAmount(self.config.get('fee_per_kb', gui.wallet_chain().RECOMMENDED_FEE))
        def on_fee(is_done):
            if self.config.get('dynamic_fees'):
                return
            v = fee_e.get_amount() or 0
            self.config.set_key('fee_per_kb', v, is_done)
            gui.update_fee()
        fee_e.editingFinished.connect(lambda: on_fee(True))
        fee_e.textEdited.connect(lambda: on_fee(False))
        form.addRow(fee_label, fee_e)

        dynfee_cb = QCheckBox(_('Dynamic fees'))
        dynfee_cb.setChecked(self.config.get('dynamic_fees', False))
        dynfee_cb.setToolTip(_("Use a fee per kB value recommended by the server."))
        dynfee_sl = QSlider(Qt.Horizontal, self)
        dynfee_sl.setValue(self.config.get('fee_factor', 50))
        dynfee_sl.setToolTip("Fee Multiplier. Min = 50%, Max = 150%")
        form.addRow(dynfee_cb)
        form.addRow(_("Fee Multiplier"), dynfee_sl)

        def update_feeperkb():
            fee_e.setAmount(gui.wallet.fee_per_kb(self.config))
            b = self.config.get('dynamic_fees')
            dynfee_sl.setHidden(not b)
            form.labelForField(dynfee_sl).setHidden(not b)
            fee_e.setEnabled(not b)
        def fee_factor_changed(b):
            self.config.set_key('fee_factor', b, False)
            update_feeperkb()
        def on_dynfee(x):
            dynfee = x == Qt.Checked
            self.config.set_key('dynamic_fees', dynfee)
            update_feeperkb()
        dynfee_cb.stateChanged.connect(on_dynfee)
        dynfee_sl.valueChanged[int].connect(fee_factor_changed)
        update_feeperkb()

        msg = _('OpenAlias record, used to receive coins and to sign payment requests.') + '\n\n'\
              + _('The following alias providers are available:') + '\n'\
              + '\n'.join(['https://cryptoname.co/', 'http://xmr.link']) + '\n\n'\
              + 'For more information, see http://openalias.org'
        alias_label = HelpLabel(_('OpenAlias') + ':', msg)
        alias = self.config.get('alias','')
        self.alias_e = alias_e = QLineEdit(alias)
        def on_alias_edit():
            alias_e.setStyleSheet("")
            alias = str(alias_e.text())
            self.config.set_key('alias', alias, True)
            if alias:
                gui.fetch_alias()
        self.set_alias_color()
        self.connect(gui, SIGNAL('alias_received'), self.set_alias_color)
        alias_e.editingFinished.connect(on_alias_edit)
        form.addRow(alias_label, alias_e)

        # SSL certificate
        msg = ' '.join([
            _('SSL certificate used to sign payment requests.'),
            _('Use setconfig to set ssl_chain and ssl_privkey.'),
        ])
        if self.config.get('ssl_privkey') or self.config.get('ssl_chain'):
            try:
                SSL_identity = paymentrequest.check_ssl_config(self.config)
                SSL_error = None
            except BaseException as e:
                SSL_identity = "error"
                SSL_error = str(e)
        else:
            SSL_identity = ""
            SSL_error = None
        SSL_id_label = HelpLabel(_('SSL certificate') + ':', msg)
        SSL_id_e = QLineEdit(SSL_identity)
        SSL_id_e.setStyleSheet(RED_BG if SSL_error else GREEN_BG if SSL_identity else '')
        if SSL_error:
            SSL_id_e.setToolTip(SSL_error)
        SSL_id_e.setReadOnly(True)
        form.addRow(SSL_id_label, SSL_id_e)

        units = gui.wallet_chain().base_units.keys()
        msg = _('Base unit of your wallet.')\
              + '\n' \
              + _(' These settings affects the fields in the Send tab')+' '
        unit_label = HelpLabel(_('Base unit') + ':', msg)
        unit_combo = QComboBox()
        unit_combo.addItems(units)
        unit_combo.setCurrentIndex(units.index(gui.base_unit()))
        def on_unit(x):
            unit_result = units[unit_combo.currentIndex()]
            if gui.base_unit() == unit_result:
                return
            gui.decimal_point = gui.wallet_chain().base_units[unit_result]
            self.config.set_key('decimal_point', gui.decimal_point, True)
            gui.history_list.update()
            gui.receive_list.update()
            gui.address_list.update()
            fee_e.setAmount(gui.wallet.fee_per_kb(self.config))
            gui.update_status()
        unit_combo.currentIndexChanged.connect(on_unit)
        form.addRow(unit_label, unit_combo)

        block_explorers = sorted(block_explorer_info().keys())
        msg = _('Choose which online block explorer to use for functions that open a web browser')
        block_ex_label = HelpLabel(_('Online Block Explorer') + ':', msg)
        block_ex_combo = QComboBox()
        block_ex_combo.addItems(block_explorers)
        block_ex_combo.setCurrentIndex(block_explorers.index(block_explorer(self.config)))
        def on_be(x):
            be_result = block_explorers[block_ex_combo.currentIndex()]
            self.config.set_key('block_explorer', be_result, True)
        block_ex_combo.currentIndexChanged.connect(on_be)
        form.addRow(block_ex_label, block_ex_combo)

        usechange_cb = QCheckBox(_('Use change addresses'))
        usechange_cb.setChecked(gui.wallet.use_change)
        if not self.config.is_modifiable('use_change'): usechange_cb.setEnabled(False)
        def on_usechange(x):
            usechange_result = x == Qt.Checked
            if gui.wallet.use_change != usechange_result:
                gui.wallet.use_change = usechange_result
                gui.wallet.storage.put('use_change', gui.wallet.use_change)
        usechange_cb.stateChanged.connect(on_usechange)
        usechange_cb.setToolTip(_('Using change addresses makes it more difficult for other people to track your transactions.'))
        form.addRow(usechange_cb)

        can_edit_fees_cb = QCheckBox(_('Set transaction fees manually'))
        can_edit_fees_cb.setChecked(self.config.get('can_edit_fees', False))
        def on_editfees(x):
            self.config.set_key('can_edit_fees', x == Qt.Checked)
            gui.update_fee_edit()
        can_edit_fees_cb.stateChanged.connect(on_editfees)
        can_edit_fees_cb.setToolTip(_('This option lets you edit fees in the send tab.'))
        form.addRow(can_edit_fees_cb)


        self.setLayout(form)

    def set_alias_color(self):
        if not self.config.get('alias'):
            self.alias_e.setStyleSheet("")
            return
        if gui.alias_info:
            alias_addr, alias_name, validated = gui.alias_info
            self.alias_e.setStyleSheet(GREEN_BG if validated else RED_BG)
        else:
            self.alias_e.setStyleSheet(RED_BG)

class GlobalOptions(QWidget):
    def __init__(self, main_window, parent=None):
        super(GlobalOptions, self).__init__(parent)
        self.gui = gui = main_window
        self.config = self.gui.config
        form = QFormLayout()

        # language
        lang_help = _('Select which language is used in the GUI (after restart).')
        lang_label = HelpLabel(_('Language') + ':', lang_help)
        lang_combo = QComboBox()
        from encompass.i18n import languages
        lang_combo.addItems(languages.values())
        try:
            index = languages.keys().index(self.config.get_above_chain("language",''))
        except Exception:
            index = 0
        lang_combo.setCurrentIndex(index)
        if not self.config.is_modifiable('language'):
            for w in [lang_combo, lang_label]: w.setEnabled(False)
        def on_lang(x):
            lang_request = languages.keys()[lang_combo.currentIndex()]
            if lang_request != self.config.get_above_chain('language'):
                self.config.set_key_above_chain("language", lang_request, True)
                gui.need_restart = True
        lang_combo.currentIndexChanged.connect(on_lang)
        form.addRow(lang_label, lang_combo)

        from encompass import qrscanner
        system_cameras = qrscanner._find_system_cameras()
        qr_combo = QComboBox()
        qr_combo.addItem("Default","default")
        for camera, device in system_cameras.items():
            qr_combo.addItem(camera, device)
        #combo.addItem("Manually specify a device", config.get("video_device"))
        index = qr_combo.findData(self.config.get_above_chain("video_device"))
        qr_combo.setCurrentIndex(index)
        msg = _("Install the zbar package to enable this.\nOn linux, type: 'apt-get install python-zbar'")
        qr_label = HelpLabel(_('Video Device') + ':', msg)
        qr_combo.setEnabled(qrscanner.zbar is not None)
        on_video_device = lambda x: self.config.set_key_above_chain("video_device", str(qr_combo.itemData(x).toString()), True)
        qr_combo.currentIndexChanged.connect(on_video_device)
        form.addRow(qr_label, qr_combo)

        showtx_cb = QCheckBox(_('View transaction before signing'))
        showtx_cb.setChecked(gui.show_before_broadcast())
        showtx_cb.stateChanged.connect(lambda x: gui.set_show_before_broadcast(showtx_cb.isChecked()))
        showtx_cb.setToolTip(_('Display the details of your transactions before signing it.'))
        form.addRow(showtx_cb)

        verbose_cur_dialog = QCheckBox(_('Verbose Currency Dialog'))
        verbose_cur_dialog.setChecked(gui.verbose_currency_dialog())
        verbose_cur_dialog.stateChanged.connect(lambda x: gui.set_currency_dialog_verbosity(verbose_cur_dialog.isChecked()))
        verbose_cur_dialog.setToolTip(_('Display additional information about currencies in the Currency Dialog.'))
        form.addRow(verbose_cur_dialog)

        self.setLayout(form)


class SettingsDialog(QDialog):
    def __init__(self, main_window, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle(_('Preferences'))
        self.gui = main_window

        self.tabs = QTabWidget()
        self.global_options = GlobalOptions(self.gui)
        self.chain_options = ChainOptions(self.gui)
        self.tabs.addTab(self.global_options, _('General'))
        self.tabs.addTab(self.chain_options, self.gui.wallet_chain().coin_name)

        vbox = QVBoxLayout()
        vbox.addWidget(self.tabs)
        vbox.addStretch(1)
        vbox.addLayout(Buttons(CloseButton(self)))
        self.setLayout(vbox)

