import time
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from encompass_gui.qt.util import *
from encompass_gui.qt.amountedit import AmountEdit


from encompass.bitcoin import COIN
from encompass.i18n import _
from decimal import Decimal
from functools import partial
from encompass.plugins import hook
from exchange_rate import FxPlugin
from encompass.util import timestamp_to_datetime

class Plugin(FxPlugin, QObject):

    def __init__(self, parent, config, name):
        QObject.__init__(self)
        FxPlugin.__init__(self, parent, config, name)

    def connect_fields(self, window, btc_e, fiat_e, fee_e):

        def edit_changed(edit):
            edit.setStyleSheet(BLACK_FG)
            fiat_e.is_last_edited = (edit == fiat_e)
            amount = edit.get_amount()
            rate = self.exchange_rate(window.wallet_chain().code)
            if rate is None or amount is None:
                if edit is fiat_e:
                    btc_e.setText("")
                    if fee_e:
                        fee_e.setText("")
                else:
                    fiat_e.setText("")
            else:
                if edit is fiat_e:
                    btc_e.setAmount(int(amount / Decimal(rate) * COIN))
                    if fee_e: window.update_fee()
                    btc_e.setStyleSheet(BLUE_FG)
                else:
                    fiat_e.setText(self.ccy_amount_str(
                        amount * Decimal(rate) / COIN, False))
                    fiat_e.setStyleSheet(BLUE_FG)

        fiat_e.textEdited.connect(partial(edit_changed, fiat_e))
        btc_e.textEdited.connect(partial(edit_changed, btc_e))
        fiat_e.is_last_edited = False

    @hook
    def init_qt(self, gui):
        for window in gui.windows:
            self.on_new_window(window)

    @hook
    def do_clear(self, window):
        window.fiat_send_e.setText('')

    def on_close(self):
        self.emit(SIGNAL('close_fx_plugin'))

    def restore_window(self, window):
        window.update_status()
        window.history_list.refresh_headers()
        window.fiat_send_e.hide()
        window.fiat_receive_e.hide()

    def on_quotes(self):
        self.emit(SIGNAL('new_fx_quotes'))

    def on_history(self):
        self.emit(SIGNAL('new_fx_history'))

    def on_fx_history(self, window):
        '''Called when historical fx quotes are updated'''
        window.history_list.update()

    def on_fx_quotes(self, window):
        '''Called when fresh spot fx quotes come in'''
        window.update_status()
        self.populate_ccy_combo(window.wallet_chain().code)
        # Refresh edits with the new rate
        edit = window.fiat_send_e if window.fiat_send_e.is_last_edited else window.amount_e
        edit.textEdited.emit(edit.text())
        edit = window.fiat_receive_e if window.fiat_receive_e.is_last_edited else window.receive_amount_e
        edit.textEdited.emit(edit.text())
        # History tab needs updating if it used spot
        if self.history_used_spot:
            self.on_fx_history(window)

    def on_ccy_combo_change(self, chaincode):
        '''Called when the chosen currency changes'''
        ccy = str(self.ccy_combo.currentText())
        if ccy and ccy != self.ccy:
            self.set_currency(ccy)
            self.hist_checkbox_update(chaincode)

    def hist_checkbox_update(self, chaincode):
        if self.hist_checkbox and self.exchange.get(chaincode):
            self.hist_checkbox.setEnabled(self.ccy in self.exchange[chaincode].history_ccys())
            self.hist_checkbox.setChecked(self.config_history())

    def populate_ccy_combo(self, chaincode):
        # There should be at most one instance of the settings dialog
        combo = self.ccy_combo
        # NOTE: bool(combo) is False if it is empty.  Nuts.
        if combo is not None and self.exchange.get(chaincode):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(sorted(self.exchange[chaincode].quotes.get(chaincode, {}).keys()))
            combo.blockSignals(False)
            combo.setCurrentIndex(combo.findText(self.ccy))

    @hook
    def on_new_window(self, window):
        # Additional send and receive edit boxes
        if not hasattr(window, 'fiat_send_e'):
            send_e = AmountEdit(self.get_currency)
            window.send_grid.addWidget(send_e, 4, 2, Qt.AlignLeft)
            window.amount_e.frozen.connect(
                lambda: send_e.setFrozen(window.amount_e.isReadOnly()))
            receive_e = AmountEdit(self.get_currency)
            window.receive_grid.addWidget(receive_e, 2, 2, Qt.AlignLeft)
            window.fiat_send_e = send_e
            window.fiat_receive_e = receive_e
            self.connect_fields(window, window.amount_e, send_e, window.fee_e)
            self.connect_fields(window, window.receive_amount_e, receive_e, None)
        else:
            window.fiat_send_e.show()
            window.fiat_receive_e.show()
        window.history_list.refresh_headers()
        window.update_status()
        window.connect(self, SIGNAL('new_fx_quotes'), lambda: self.on_fx_quotes(window))
        window.connect(self, SIGNAL('new_fx_history'), lambda: self.on_fx_history(window))
        window.connect(self, SIGNAL('close_fx_plugin'), lambda: self.restore_window(window))
        window.connect(self, SIGNAL('refresh_headers'), window.history_list.refresh_headers)

    def settings_widget(self, window):
        if not self.exchanges.get(window.wallet_chain().code):
            return None
        return EnterButton(_('Settings'), partial(self.settings_dialog, window))

    def settings_dialog(self, window):
        d = WindowModalDialog(window, _("Exchange Rate Settings"))
        layout = QGridLayout(d)
        layout.addWidget(QLabel(_('Settings for Chain: ')), 0, 0)
        layout.addWidget(QLabel(_('Exchange rate API: ')), 1, 0)
        layout.addWidget(QLabel(_('Currency: ')), 2, 0)
        layout.addWidget(QLabel(_('History Rates: ')), 3, 0)

        # Currency list
        self.ccy_combo = QComboBox()
        self.ccy_combo.currentIndexChanged.connect(lambda: self.on_ccy_combo_change(window.wallet_chain().code))
        self.populate_ccy_combo(window.wallet_chain().code)

        def on_change_ex(idx):
            if idx < 0:
                return
            exchange = str(combo_ex.currentText())
            chaincode = window.wallet_chain().code
            if exchange != self.exchange[chaincode].name():
                self.set_exchange(chaincode, exchange)
                self.hist_checkbox_update(chaincode)

        def on_change_hist(checked):
            if checked:
                self.config.set_key_above_chain('history_rates', 'checked')
                self.get_historical_rates()
            else:
                self.config.set_key_above_chain('history_rates', 'unchecked')
            self.emit(SIGNAL('refresh_headers'))

        def ok_clicked():
            self.timeout = 0
            self.ccy_combo = None
            d.accept()

        label_chain = QLabel()
        label_chain.setText(window.wallet_chain().coin_name)

        combo_ex = QComboBox()
        combo_ex.addItems(sorted(self.exchanges[window.wallet_chain().code].keys()))
        combo_ex.setCurrentIndex(combo_ex.findText(self.config_exchange(window.wallet_chain().code)))
        combo_ex.currentIndexChanged.connect(on_change_ex)

        self.hist_checkbox = QCheckBox()
        self.hist_checkbox.stateChanged.connect(on_change_hist)
        self.hist_checkbox_update(window.wallet_chain().code)

        ok_button = QPushButton(_("OK"))
        ok_button.clicked.connect(lambda: ok_clicked())

        layout.addWidget(label_chain,0,1)
        layout.addWidget(combo_ex,1,1)
        layout.addWidget(self.ccy_combo,2,1)
        layout.addWidget(self.hist_checkbox,3,1)
        layout.addWidget(ok_button,4,1)

        return d.exec_()


    def config_history(self):
        return self.config.get_above_chain('history_rates', 'unchecked') != 'unchecked'

    def show_history(self, chaincode):
        return self.config_history() and super(Plugin, self).show_history(chaincode)

    @hook
    def history_tab_headers(self, headers, chaincode):
        if chaincode is None:
            return
        if self.show_history(chaincode):
            headers.extend(['%s '%self.ccy + _('Amount'), '%s '%self.ccy + _('Balance')])

    @hook
    def history_tab_update_begin(self):
        self.history_used_spot = False

    @hook
    def history_tab_update(self, tx, entry, chaincode):
        if not self.show_history(chaincode):
            return
        tx_hash, conf, value, timestamp, balance = tx
        if conf <= 0:
            date = timestamp_to_datetime(time.time())
        else:
            date = timestamp_to_datetime(timestamp)
        for amount in [value, balance]:
            text = self.historical_value_str(chaincode, amount, date)
            entry.append(text)
