import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.main import app, db
from src.models.obra import Obra, Etapa, Mobiliario
from src.models.produto import Produto, Categoria, MovimentacaoEstoque
from src.models.sistema import HistoricoAcesso, ConfiguracaoSistema, Feed
from datetime import datetime, date
import json

def initialize_empty_database():
    """Inicializa o banco de dados vazio, apenas com as configurações básicas do sistema"""
    with app.app_context():
        print("Inicializando banco de dados vazio...")
        
        # Criar tabelas se não existirem
        db.create_all()
        
        # Verificar se já existem configurações básicas
        existing_configs = ConfiguracaoSistema.query.count()
        if existing_configs == 0:
            # Criar apenas configurações básicas do sistema
            configuracoes_basicas = [
                {
                    'chave': 'nome_empresa',
                    'valor': 'SEMCAS',
                    'tipo': 'string',
                    'descricao': 'Nome da empresa/organização',
                    'categoria': 'geral'
                },
                {
                    'chave': 'meta_obras_mes',
                    'valor': '10',
                    'tipo': 'number',
                    'descricao': 'Meta de obras por mês',
                    'categoria': 'metas'
                },
                {
                    'chave': 'meta_progresso_obras',
                    'valor': '100',
                    'tipo': 'number',
                    'descricao': 'Meta de progresso das obras (%)',
                    'categoria': 'metas'
                },
                {
                    'chave': 'backup_automatico',
                    'valor': 'true',
                    'tipo': 'boolean',
                    'descricao': 'Realizar backup automático dos dados',
                    'categoria': 'sistema'
                }
            ]
            
            for config_data in configuracoes_basicas:
                config = ConfiguracaoSistema(**config_data)
                db.session.add(config)
            
            # Criar histórico de inicialização
            historico_init = HistoricoAcesso(
                usuario='Sistema',
                acao='inicializacao',
                descricao='Sistema inicializado - banco de dados vazio',
                status='success',
                data_acao=datetime.utcnow()
            )
            db.session.add(historico_init)
            
            db.session.commit()
            print("✅ Banco de dados inicializado vazio com configurações básicas")
        else:
            print("✅ Banco de dados já inicializado")

def populate_database_with_examples():
    """Popula o banco de dados com dados de exemplo (opcional)"""
    with app.app_context():
        print("Populando banco de dados com dados de exemplo...")
        
        # Limpar dados existentes (opcional)
        db.drop_all()
        db.create_all()
        
        # 1. Criar categorias de produtos
        categorias = [
            {'nome': 'Cimento', 'descricao': 'Materiais cimentícios', 'cor': '#8B5CF6'},
            {'nome': 'Alvenaria', 'descricao': 'Materiais para alvenaria', 'cor': '#F59E0B'},
            {'nome': 'Agregados', 'descricao': 'Areia, brita e similares', 'cor': '#10B981'},
            {'nome': 'Ferragens', 'descricao': 'Pregos, parafusos, etc.', 'cor': '#EF4444'},
            {'nome': 'Elétrica', 'descricao': 'Materiais elétricos', 'cor': '#3B82F6'}
        ]
        
        for cat_data in categorias:
            categoria = Categoria(**cat_data)
            db.session.add(categoria)
        
        db.session.commit()
        
        # 2. Criar produtos
        produtos = [
            {
                'nome': 'Cimento Portland',
                'categoria': 'Cimento',
                'codigo': 'CIM001',
                'estoque': 150,
                'estoque_minimo': 20,
                'preco': 32.50,
                'unidade': 'saco',
                'descricao': 'Cimento Portland CPII-E-32'
            },
            {
                'nome': 'Tijolo Cerâmico',
                'categoria': 'Alvenaria',
                'codigo': 'TIJ001',
                'estoque': 5000,
                'estoque_minimo': 500,
                'preco': 0.85,
                'unidade': 'unidade',
                'descricao': 'Tijolo cerâmico 6 furos'
            },
            {
                'nome': 'Areia Média',
                'categoria': 'Agregados',
                'codigo': 'ARE001',
                'estoque': 25,
                'estoque_minimo': 5,
                'preco': 45.00,
                'unidade': 'm³',
                'descricao': 'Areia média lavada'
            }
        ]
        
        for prod_data in produtos:
            produto = Produto(**prod_data)
            db.session.add(produto)
            db.session.flush()
            
            # Criar movimentação inicial
            if produto.estoque > 0:
                movimentacao = MovimentacaoEstoque(
                    produto_id=produto.id,
                    tipo='entrada',
                    quantidade=produto.estoque,
                    quantidade_anterior=0,
                    quantidade_atual=produto.estoque,
                    motivo='Estoque inicial',
                    usuario='Sistema'
                )
                db.session.add(movimentacao)
        
        db.session.commit()
        print("✅ Dados de exemplo adicionados com sucesso!")

if __name__ == '__main__':
    # Por padrão, inicializar banco vazio
    initialize_empty_database()
    
    # Para adicionar dados de exemplo, descomente a linha abaixo:
    # populate_database_with_examples()

