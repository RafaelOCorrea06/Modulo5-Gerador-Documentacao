def __init__(self) -> None:
    self.adaptador_markdown = AdaptadorMarkdownNativo()
    self.adaptador_docx = AdaptadorPythonDocx()
    self.adaptador_pdf = AdaptadorReportLab()