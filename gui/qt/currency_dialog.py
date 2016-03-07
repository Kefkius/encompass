import copy
import functools
import operator

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from encompass.i18n import _
from encompass import chainparams
from encompass.util import print_error

from util import Buttons, CloseButton, OkButton

class CurrenciesCheckboxDialog(QDialog):
    def __init__(self, parent):
        super(CurrenciesCheckboxDialog, self).__init__(parent)
        self.parent = parent
        known_chains = chainparams.known_chains

        self.scroll_area = scroll = QScrollArea()
        scroll.setEnabled(True)
        scroll.setWidgetResizable(True)
        scroll.setMinimumSize(25, 100)

        self.coin_scroll_widget = scroll_widget = QWidget()
        scroll_widget.setMinimumHeight(len(known_chains) * 35)

        # layout containing the checkboxes
        self.coin_boxes_layout = coin_vbox = QVBoxLayout()
        # Contains the scrollarea, including coin_boxes_layout
        self.scroll_layout = scroll_layout = QVBoxLayout()

        self.coin_checkboxes = []
        for coin in sorted(known_chains, key=operator.attrgetter('code')):
            box_label = ''.join([ coin.code, " (", coin.coin_name, ")" ])
            checkbox = QCheckBox(box_label)
            checkbox.stateChanged.connect(functools.partial(self.change_coin_state, checkbox))
            self.coin_checkboxes.append(checkbox)
            coin_vbox.addWidget(checkbox)

        scroll_widget.setLayout(coin_vbox)
        scroll.setWidget(scroll_widget)
        scroll_layout.addWidget(scroll)

    def change_coin_state(self, checkbox):
        pass

class FavoriteCurrenciesDialog(CurrenciesCheckboxDialog):
    def __init__(self, parent):
        CurrenciesCheckboxDialog.__init__(self, parent)
        self.setWindowTitle(_('Favorite Coins'))
        self.favorites = copy.deepcopy(self.parent.config.get_above_chain('favorite_chains', []))
        # sanity check, just in case. Main window should have already done this
        if len(self.favorites) > 3: self.favorites = self.favorites[:3]

        self.main_layout = vbox = QVBoxLayout()
        limit_label = QLabel(_('\n'.join([
            'Up to three coins may be selected as "favorites."',
            '\nHolding down the coin icon in the wallet status bar will show you your favorite coins and allow you to quickly switch between them.',
            'They will also be listed before other coins in the currency selection dialog.'])))
        limit_label.setWordWrap(True)
        vbox.addWidget(limit_label)

        for cbox in self.coin_checkboxes:
            cbox.setChecked(str(cbox.text()).split()[0] in self.favorites)
        vbox.addLayout(self.scroll_layout)

        vbox.addLayout(Buttons(CloseButton(self), OkButton(self)))
        self.accepted.connect(self.save_favorites)
        self.setLayout(vbox)
        self.enforce_limit()

    def enforce_limit(self):
        """Enforce limit on list of favorite chains."""
        if not self.coin_checkboxes: return
        if len(self.favorites) < 3:
            for box in self.coin_checkboxes:
                box.setEnabled(True)
        else:
            for box in self.coin_checkboxes:
                if not box.isChecked():
                    box.setEnabled(False)

    def change_coin_state(self, checkbox):
        code = str(checkbox.text()).split()[0]
        is_favorite = checkbox.isChecked()
        if is_favorite and code not in self.favorites:
            self.favorites.append(code)
        elif not is_favorite and code in self.favorites:
            self.favorites.remove(code)
        self.enforce_limit()

    def save_favorites(self):
        print_error("Saving new favorite chains: {}".format(map(lambda x: x.encode('ascii', 'ignore'), self.favorites)))
        self.parent.config.set_key_above_chain('favorite_chains', self.favorites, True)



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
                {Qt.DisplayRole: _('Favorite'), Qt.ToolTipRole: _('Whether the currency is a favorite coin')},
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
        return len(self.verbose_header_list) if self.is_verbose() else len(self.simple_header_list)

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
            elif role == Qt.CheckStateRole:
                data = Qt.Checked if is_initialized else Qt.Unchecked
        elif col == 3:
            is_favorite = chain.code in self.gui.config.get_above_chain('favorite_chains', [])
            if role in [Qt.DisplayRole, Qt.ToolTipRole]:
                data = y_or_n(is_favorite)
            elif role == Qt.CheckStateRole:
                data = Qt.Checked if is_favorite else Qt.Unchecked
        elif col == 4:
            if role in [Qt.DisplayRole, Qt.ToolTipRole]:
                data = 0
                if is_initialized:
                    data = len(self.gui.wallet.storage.get_for_chain(chain.code, 'transactions', []))
        elif col == 5:
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
        # Sort by favorite chains, then by name.
        self.view.sortByColumn(0, Qt.AscendingOrder)
        self.view.sortByColumn(3, Qt.DescendingOrder)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.view)
        self.main_layout.addLayout(Buttons(CloseButton(self), OkButton(self)))
        self.setLayout(self.main_layout)

        self.setWindowTitle(_('Change Currency'))

        # Resize columns
        self.set_verbosity(self.is_verbose())

    def sizeHint(self):
        return QSize(550, 400)

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
