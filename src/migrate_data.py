import os
import sys
import json
from datetime import datetime, date

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.main import app
from src.models.user import db
from src.models.obra import Obra, Etapa, Mobiliario

def migrate_sample_data():
    """Migra dados de exemplo para o banco de dados"""
    with app.app_context():
        # Limpar dados existentes
        db.drop_all()
        db.create_all()
        
        # Dados de exemplo das obras
        obras_data = [
            {
                'nome': 'CENTRO POP COHAB',
                'localizacao': 'Rua das Flores, 123 - Cohab',
                'valor': 850000.0,
                'status': 'Em Andamento',
                'progresso': 80,
                'data_inicio': date(2024, 1, 15)
            },
            {
                'nome': 'CENTRO POP CENTRO',
                'localizacao': 'Av. Principal, 456 - Centro',
                'valor': 1200000.0,
                'status': 'Em Andamento',
                'progresso': 20,
                'data_inicio': date(2024, 3, 10)
            }
        ]
        
        # Criar obras
        obras_criadas = []
        for obra_data in obras_data:
            obra = Obra(**obra_data)
            db.session.add(obra)
            db.session.flush()  # Para obter o ID
            obras_criadas.append(obra)
        
        # Dados de exemplo das etapas
        etapas_data = [
            {
                'obra_id': obras_criadas[0].id,
                'titulo': 'Fundação Concluída',
                'descricao': 'Estrutura em andamento, fundação concluída',
                'data_etapa': date(2024, 2, 15),
                'fotos': json.dumps([
                    {'url': 'https://via.placeholder.com/800x600/4CAF50/white?text=Fundacao+1', 'name': 'Fundação - Vista 1'},
                    {'url': 'https://via.placeholder.com/800x600/2196F3/white?text=Fundacao+2', 'name': 'Fundação - Vista 2'},
                    {'url': 'https://via.placeholder.com/800x600/FF9800/white?text=Fundacao+3', 'name': 'Fundação - Vista 3'}
                ])
            },
            {
                'obra_id': obras_criadas[0].id,
                'titulo': 'Estrutura em Andamento',
                'descricao': 'Pilares e vigas sendo executados',
                'data_etapa': date(2024, 4, 20),
                'fotos': json.dumps([
                    {'url': 'https://via.placeholder.com/800x600/9C27B0/white?text=Estrutura+1', 'name': 'Estrutura - Pilares'},
                    {'url': 'https://via.placeholder.com/800x600/F44336/white?text=Estrutura+2', 'name': 'Estrutura - Vigas'}
                ])
            },
            {
                'obra_id': obras_criadas[1].id,
                'titulo': 'Projeto Aprovado',
                'descricao': 'Licenças obtidas, início das obras autorizado',
                'data_etapa': date(2024, 3, 25),
                'fotos': json.dumps([
                    {'url': 'https://via.placeholder.com/800x600/607D8B/white?text=Projeto+Aprovado', 'name': 'Documentação do Projeto'}
                ])
            }
        ]
        
        # Criar etapas
        for etapa_data in etapas_data:
            etapa = Etapa(**etapa_data)
            db.session.add(etapa)
        
        # Dados de exemplo do mobiliário
        mobiliario_data = [
            {
                'obra_id': obras_criadas[0].id,
                'tipo': 'Sofá',
                'comodo': 'sala',
                'status': 'existente',
                'posicao_x': 50.0,
                'posicao_y': 30.0
            },
            {
                'obra_id': obras_criadas[0].id,
                'tipo': 'Mesa',
                'comodo': 'sala',
                'status': 'novo',
                'posicao_x': 80.0,
                'posicao_y': 60.0
            },
            {
                'obra_id': obras_criadas[1].id,
                'tipo': 'Cama',
                'comodo': 'quarto1',
                'status': 'novo',
                'posicao_x': 40.0,
                'posicao_y': 25.0
            }
        ]
        
        # Criar mobiliário
        for mob_data in mobiliario_data:
            mobiliario = Mobiliario(**mob_data)
            db.session.add(mobiliario)
        
        # Salvar todas as alterações
        db.session.commit()
        
        print("✅ Dados migrados com sucesso!")
        print(f"📊 {len(obras_criadas)} obras criadas")
        print(f"📋 {len(etapas_data)} etapas criadas")
        print(f"🪑 {len(mobiliario_data)} itens de mobiliário criados")

if __name__ == '__main__':
    migrate_sample_data()

