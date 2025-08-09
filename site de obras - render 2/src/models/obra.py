from src.models.user import db
from datetime import datetime
import json

class Obra(db.Model):
    __tablename__ = 'obras'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    localizacao = db.Column(db.String(300), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    progresso = db.Column(db.Integer, default=0)
    data_inicio = db.Column(db.Date, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    etapas = db.relationship('Etapa', backref='obra', lazy=True, cascade='all, delete-orphan')
    mobiliario = db.relationship('Mobiliario', backref='obra', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'localizacao': self.localizacao,
            'valor': self.valor,
            'status': self.status,
            'progresso': self.progresso,
            'dataInicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'dataCriacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'dataAtualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'etapas': [etapa.to_dict() for etapa in self.etapas if not etapa.deletado],
            'furniture': [mob.to_dict() for mob in self.mobiliario]
        }

class Etapa(db.Model):
    __tablename__ = 'etapas'
    
    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey('obras.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    data_etapa = db.Column(db.Date, nullable=False)
    fotos = db.Column(db.Text)  # JSON string com URLs das fotos
    deletado = db.Column(db.Boolean, default=False)  # Soft delete
    data_exclusao = db.Column(db.DateTime)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        fotos_list = []
        if self.fotos:
            try:
                fotos_list = json.loads(self.fotos)
            except:
                fotos_list = []
                
        return {
            'id': self.id,
            'obraId': self.obra_id,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'dataEtapa': self.data_etapa.isoformat() if self.data_etapa else None,
            'fotos': fotos_list,
            'deletado': self.deletado,
            'dataExclusao': self.data_exclusao.isoformat() if self.data_exclusao else None,
            'dataCriacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'dataAtualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }
    
    def soft_delete(self):
        """Marca a etapa como deletada (soft delete)"""
        self.deletado = True
        self.data_exclusao = datetime.utcnow()
        db.session.commit()
    
    def restore(self):
        """Restaura uma etapa deletada"""
        self.deletado = False
        self.data_exclusao = None
        db.session.commit()

class Mobiliario(db.Model):
    __tablename__ = 'mobiliario'
    
    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey('obras.id'), nullable=False)
    tipo = db.Column(db.String(100), nullable=False)
    comodo = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # 'existente' ou 'novo'
    posicao_x = db.Column(db.Float)
    posicao_y = db.Column(db.Float)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.tipo,
            'room': self.comodo,
            'status': self.status,
            'x': self.posicao_x,
            'y': self.posicao_y
        }

class Lixeira(db.Model):
    __tablename__ = 'lixeira'
    
    id = db.Column(db.Integer, primary_key=True)
    etapa_id = db.Column(db.Integer, db.ForeignKey('etapas.id'), nullable=False)
    data_exclusao = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_exclusao = db.Column(db.String(100))
    
    # Relacionamento
    etapa = db.relationship('Etapa', backref='lixeira_entry')
    
    def to_dict(self):
        return {
            'id': self.id,
            'etapaId': self.etapa_id,
            'dataExclusao': self.data_exclusao.isoformat() if self.data_exclusao else None,
            'usuarioExclusao': self.usuario_exclusao,
            'etapa': self.etapa.to_dict() if self.etapa else None
        }

