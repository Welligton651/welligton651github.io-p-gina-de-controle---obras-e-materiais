from src.models.user import db
from datetime import datetime
import json

class HistoricoAcesso(db.Model):
    __tablename__ = 'historico_acesso'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), nullable=False)
    acao = db.Column(db.String(100), nullable=False)  # 'login', 'logout', 'create', 'update', 'delete', etc.
    entidade = db.Column(db.String(100))  # 'obra', 'produto', 'etapa', etc.
    entidade_id = db.Column(db.Integer)
    descricao = db.Column(db.Text)
    detalhes = db.Column(db.Text)  # JSON com detalhes adicionais
    status = db.Column(db.String(20), default='success')  # 'success', 'error', 'warning', 'info'
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    data_acao = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        detalhes_dict = {}
        if self.detalhes:
            try:
                detalhes_dict = json.loads(self.detalhes)
            except:
                detalhes_dict = {}
                
        return {
            'id': self.id,
            'usuario': self.usuario,
            'acao': self.acao,
            'entidade': self.entidade,
            'entidadeId': self.entidade_id,
            'descricao': self.descricao,
            'detalhes': detalhes_dict,
            'status': self.status,
            'ipAddress': self.ip_address,
            'userAgent': self.user_agent,
            'dataAcao': self.data_acao.isoformat() if self.data_acao else None,
            'tempo': self._calcular_tempo_relativo()
        }
    
    def _calcular_tempo_relativo(self):
        """Calcula o tempo relativo da ação"""
        if not self.data_acao:
            return 'Desconhecido'
        
        agora = datetime.utcnow()
        diferenca = agora - self.data_acao
        
        if diferenca.days > 0:
            return f'Há {diferenca.days} dia{"s" if diferenca.days > 1 else ""}'
        elif diferenca.seconds > 3600:
            horas = diferenca.seconds // 3600
            return f'Há {horas} hora{"s" if horas > 1 else ""}'
        elif diferenca.seconds > 60:
            minutos = diferenca.seconds // 60
            return f'Há {minutos} minuto{"s" if minutos > 1 else ""}'
        else:
            return 'Agora mesmo'

class ConfiguracaoSistema(db.Model):
    __tablename__ = 'configuracoes_sistema'
    
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text)
    tipo = db.Column(db.String(20), default='string')  # 'string', 'number', 'boolean', 'json'
    descricao = db.Column(db.Text)
    categoria = db.Column(db.String(50), default='geral')
    editavel = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        valor_processado = self.valor
        
        # Processar valor baseado no tipo
        if self.tipo == 'number':
            try:
                valor_processado = float(self.valor) if '.' in str(self.valor) else int(self.valor)
            except:
                valor_processado = 0
        elif self.tipo == 'boolean':
            valor_processado = str(self.valor).lower() in ['true', '1', 'yes', 'sim']
        elif self.tipo == 'json':
            try:
                valor_processado = json.loads(self.valor)
            except:
                valor_processado = {}
        
        return {
            'id': self.id,
            'chave': self.chave,
            'valor': valor_processado,
            'tipo': self.tipo,
            'descricao': self.descricao,
            'categoria': self.categoria,
            'editavel': self.editavel,
            'dataCriacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'dataAtualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }

class Feed(db.Model):
    __tablename__ = 'feed'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(50), default='post')  # 'post', 'update', 'milestone', 'alert'
    obra_id = db.Column(db.Integer, db.ForeignKey('obras.id'))
    imagens = db.Column(db.Text)  # JSON array com URLs das imagens
    tags = db.Column(db.Text)  # JSON array com tags
    curtidas = db.Column(db.Integer, default=0)
    comentarios_count = db.Column(db.Integer, default=0)
    publico = db.Column(db.Boolean, default=True)
    data_publicacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    obra = db.relationship('Obra', backref='posts_feed')
    comentarios = db.relationship('ComentarioFeed', backref='post', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        imagens_list = []
        tags_list = []
        
        if self.imagens:
            try:
                imagens_list = json.loads(self.imagens)
            except:
                imagens_list = []
        
        if self.tags:
            try:
                tags_list = json.loads(self.tags)
            except:
                tags_list = []
        
        return {
            'id': self.id,
            'usuario': self.usuario,
            'titulo': self.titulo,
            'conteudo': self.conteudo,
            'tipo': self.tipo,
            'obraId': self.obra_id,
            'obra': self.obra.to_dict() if self.obra else None,
            'imagens': imagens_list,
            'tags': tags_list,
            'curtidas': self.curtidas,
            'comentariosCount': self.comentarios_count,
            'publico': self.publico,
            'dataPublicacao': self.data_publicacao.isoformat() if self.data_publicacao else None,
            'dataAtualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'comentarios': [comentario.to_dict() for comentario in self.comentarios]
        }

class ComentarioFeed(db.Model):
    __tablename__ = 'comentarios_feed'
    
    id = db.Column(db.Integer, primary_key=True)
    feed_id = db.Column(db.Integer, db.ForeignKey('feed.id'), nullable=False)
    usuario = db.Column(db.String(100), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_comentario = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'feedId': self.feed_id,
            'usuario': self.usuario,
            'conteudo': self.conteudo,
            'dataComentario': self.data_comentario.isoformat() if self.data_comentario else None
        }

