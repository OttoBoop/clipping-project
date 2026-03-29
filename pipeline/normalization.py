552:    def get_materia(self, materia_id: str) -> Optional[Materia]:
749:    def get_turma(self, turma_id: str) -> Optional[Turma]:
869:    def listar_alunos(self, turma_id: str = None) -> List[Aluno]:
1055:    def get_turmas_do_aluno(self, aluno_id: str, apenas_ativas: bool = True) -> List[Dict[str, Any]]:
1486:    def listar_documentos(self, atividade_id: str, aluno_id: str = None,
1751:    def get_estatisticas_gerais_fast(self) -> Dict[str, Any]:
1809:    def get_arvore_navegacao_fast(self) -> Dict[str, Any]:
1919:    def listar_documentos_com_contexto_fast(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
2114:        return self.get_arvore_navegacao_fast()
"},{