"""Estilos compartidos entre vistas."""

TABLE_STYLE = """
QTableWidget {
    gridline-color: #c8c8c8;
    border: 1px solid #c0c0c0;
    background-color: #ffffff;
    alternate-background-color: #f7f7f7;
}
QTableWidget::item {
    padding: 3px 6px;
    border: none;
}
QTableWidget::item:selected {
    background-color: #dce8f7;
    color: #000000;
}
QHeaderView::section {
    background-color: #f0f0f0;
    border: none;
    border-right: 1px solid #c8c8c8;
    border-bottom: 1px solid #c8c8c8;
    padding: 4px 6px;
    font-weight: bold;
}
"""
