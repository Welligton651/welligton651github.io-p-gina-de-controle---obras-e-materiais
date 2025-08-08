from src.models.user import db
from datetime import datetime

class Produto(db.Model):
    __tablename__ = 'produtos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(100), unique=True, nullable=False)
    estoque = db.Column(db.Integer, default=0)
    estoque_minimo = db.Column(db.Integer, default=0)
    preco = db.Column(db.Float, nullable=False)
    unidade = db.Column(db.String(20), default='unidade')
    descricao = db.Column(db.Text)
    foto = db.Column(db.String(500))  # Caminho para a foto do produto
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    movimentacoes = db.relationship('MovimentacaoEstoque', backref='produto', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'categoria': self.categoria,
            'codigo': self.codigo,
            'estoque': self.estoque,
            'estoqueMinimo': self.estoque_minimo,
            'preco': self.preco,
            'unidade': self.unidade,
            'descricao': self.descricao,
            'foto': self.foto,
            'ativo': self.ativo,
            'valorTotal': self.estoque * self.preco,
            'dataCriacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'dataAtualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }

class MovimentacaoEstoque(db.Model):
    __tablename__ = 'movimentacoes_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'entrada', 'saida', 'ajuste'
    quantidade = db.Column(db.Integer, nullable=False)
    quantidade_anterior = db.Column(db.Integer, nullable=False)
    quantidade_atual = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(200))
    observacoes = db.Column(db.Text)
    usuario = db.Column(db.String(100))
    data_movimentacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'produtoId': self.produto_id,
            'tipo': self.tipo,
            'quantidade': self.quantidade,
            'quantidadeAnterior': self.quantidade_anterior,
            'quantidadeAtual': self.quantidade_atual,
            'motivo': self.motivo,
            'observacoes': self.observacoes,
            'usuario': self.usuario,
            'dataMovimentacao': self.data_movimentacao.isoformat() if self.data_movimentacao else None,
            'produto': self.produto.to_dict() if self.produto else None
        }

class Categoria(db.Model):
    __tablename__ = 'categorias'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    descricao = db.Column(db.Text)
    cor = db.Column(db.String(7), default='#3B82F6')  # Cor em hex
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'cor': self.cor,
            'ativo': self.ativo,
            'dataCriacao': self.data_criacao.isoformat() if self.data_criacao else None
        }

