from PyQt4.QtGui import *
from PyQt4.QtCore import *

from encompass.i18n import _
from encompass import chainparams

from util import Buttons, CloseButton, OkButton

class CurrenciesModel(QAbstractTableModel):
    def __init__(self, main_window, parent=None):
        super(CurrenciesModel, self).__init__(parent)
        self.gui = main_window
        self.chains = chainparams.known_chains

    def columnCount(self, parent=QModelIndex()):
        return 3

    def rowCount(self, parent=QModelIndex()):
        return len(self.chains)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation != Qt.Horizontal:
            return None

        headers = [
                {Qt.DisplayRole: _('Code'), Qt.ToolTipRole: _('Currency Code')},
                {Qt.DisplayRole: _('Currency'), Qt.ToolTipRole: _('Currency Name')},
                {Qt.DisplayRole: _('Initialized'), Qt.ToolTipRole: _('Whether the currency has been used')}
        ]

        try:
            data = headers[section][role]
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
        if col == 0:
            if role in [Qt.DisplayRole, Qt.ToolTipRole]:
                data = chain.code
        elif col == 1:
            if role in [Qt.DisplayRole, Qt.ToolTipRole]:
                data = chain.coin_name
        elif col == 2:
            if role in [Qt.DisplayRole, Qt.ToolTipRole]:
                is_initialized = True
                if not self.gui.wallet.storage.get_above_chain(chain.code):
                    is_initialized = False
                data = y_or_n(is_initialized)

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
        self.view.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        self.view.verticalHeader().setDefaultSectionSize(22)
        self.view.verticalHeader().setVisible(False)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.view.sortByColumn(0, Qt.AscendingOrder)
        self.view.setMinimumWidth(400)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.view)
        self.main_layout.addLayout(Buttons(CloseButton(self), OkButton(self)))
        self.setLayout(self.main_layout)

        self.setWindowTitle(_('Change Currency'))

    def selected_chain(self):
        idx = self.proxy_model.mapToSource(self.view.selectedIndexes()[0])
        return self.model.chaincode_for_index(idx)
