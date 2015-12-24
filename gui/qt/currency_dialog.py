from PyQt4.QtGui import *
from PyQt4.QtCore import *

from encompass.i18n import _
from encompass import chainparams

from util import Buttons, CloseButton, OkButton

ResizeModeRole = Qt.UserRole + 1

class CurrenciesModel(QAbstractTableModel):
    def __init__(self, main_window, parent=None):
        super(CurrenciesModel, self).__init__(parent)
        self.gui = main_window
        self.chains = chainparams.known_chains

        self.simple_header_list = [
                {Qt.DisplayRole: _('Code'), Qt.ToolTipRole: _('Currency Code')},
                {Qt.DisplayRole: _('Currency'), Qt.ToolTipRole: _('Currency Name'), ResizeModeRole: QHeaderView.Stretch},
                {Qt.DisplayRole: _('Initialized'), Qt.ToolTipRole: _('Whether the currency has been used')},
                {Qt.DisplayRole: _('Txs'), Qt.ToolTipRole: _('Transactions'), ResizeModeRole: QHeaderView.ResizeToContents}
        ]
        self.verbose_header_list = list(self.simple_header_list)
        self.verbose_header_list.extend([
                {Qt.DisplayRole: _('Index'), Qt.ToolTipRole: _('BIP 44 Chain Index'), ResizeModeRole: QHeaderView.ResizeToContents}
        ])

        self.header_list = self.verbose_header_list if self.is_verbose() else self.simple_header_list

    def is_verbose(self):
        return self.gui.config.get_above_chain('verbose_currency_dialog', False)

    def set_verbosity(self, verbose):
        old = self.is_verbose()
        self.gui.config.set_key_above_chain('verbose_currency_dialog', verbose)
        verbose = self.is_verbose()
        if old == verbose:
            return

        self.beginResetModel()
        self.header_list = self.verbose_header_list if verbose else self.simple_header_list
        self.endResetModel()

    def columnCount(self, parent=QModelIndex()):
        return 5 if self.is_verbose() else 4

    def rowCount(self, parent=QModelIndex()):
        return len(self.chains)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation != Qt.Horizontal:
            return None

        try:
            data = self.header_list[section][role]
            return data
        except (IndexError, KeyError):
            return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        y_or_n = lambda x: _('Yes') if x == True else _('No')
        data = None
        chain = self.chains[index.row()]
        col = index.column()

        is_initialized = False
        if self.gui.wallet and self.gui.wallet.storage.get_above_chain(chain.code):
            is_initialized = True

        if col == 0:
            if role in [Qt.DisplayRole, Qt.ToolTipRole]:
                data = chain.code
        elif col == 1:
            if role in [Qt.DisplayRole, Qt.ToolTipRole]:
                data = chain.coin_name
        elif col == 2:
            if role in [Qt.DisplayRole, Qt.ToolTipRole]:
                data = y_or_n(is_initialized)
        elif col == 3:
            if role in [Qt.DisplayRole, Qt.ToolTipRole]:
                data = 0
                if is_initialized:
                    data = len(self.gui.wallet.storage.get_for_chain(chain.code, 'transactions', []))
        elif col == 4:
            if role in [Qt.DisplayRole, Qt.ToolTipRole]:
                data = chain.cls.chain_index

        return data

    def chaincode_for_index(self, index):
        idx = self.createIndex(index.row(), 0)
        return str(self.data(idx))

class ChangeCurrencyDialog(QDialog):
    def __init__(self, main_window):
        super(ChangeCurrencyDialog, self).__init__(main_window)
        self.gui = main_window
        self.model = CurrenciesModel(self.gui)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)

        self.view = QTableView()
        self.view.setModel(self.proxy_model)
        self.view.setSortingEnabled(True)
        self.view.setAlternatingRowColors(True)
        self.view.setWordWrap(True)
        self.view.horizontalHeader().setHighlightSections(False)
        self.view.verticalHeader().setDefaultSectionSize(22)
        self.view.verticalHeader().setVisible(False)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.view.sortByColumn(0, Qt.AscendingOrder)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.view)
        self.main_layout.addLayout(Buttons(CloseButton(self), OkButton(self)))
        self.setLayout(self.main_layout)

        self.setMinimumWidth(450)
        self.setWindowTitle(_('Change Currency'))

        # Resize columns
        self.set_verbosity(self.is_verbose())

    def selected_chain(self):
        idx = self.proxy_model.mapToSource(self.view.selectedIndexes()[0])
        return self.model.chaincode_for_index(idx)

    def is_verbose(self):
        return self.model.is_verbose()

    def set_verbosity(self, verbose):
        self.model.set_verbosity(verbose)
        for i in range(self.model.columnCount()):
            resize_mode = self.model.headerData(i, Qt.Horizontal, ResizeModeRole)
            if resize_mode:
                self.view.horizontalHeader().setResizeMode(i, resize_mode)
