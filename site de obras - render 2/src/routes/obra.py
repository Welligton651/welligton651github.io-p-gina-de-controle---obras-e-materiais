from flask import Blueprint, request, jsonify, send_from_directory
from src.models.user import db
from src.models.obra import Obra, Etapa, Mobiliario, Lixeira
from datetime import datetime, date
import json
import os
import uuid
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

obra_bp = Blueprint("obra", __name__)

# CORS headers
@obra_bp.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@obra_bp.route('/obras', methods=['OPTIONS'])
def handle_options():
    return '', 200

# OBRAS CRUD
@obra_bp.route('/obras', methods=['GET'])
def get_obras():
    try:
        obras = Obra.query.all()
        return jsonify([obra.to_dict() for obra in obras]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@obra_bp.route('/obras', methods=['POST'])
def create_obra():
    try:
        data = request.get_json()
        
        # Converter data_inicio se for string
        data_inicio = data.get('dataInicio')
        if isinstance(data_inicio, str):
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        
        obra = Obra(
            nome=data['nome'],
            localizacao=data['localizacao'],
            valor=float(data['valor']),
            status=data['status'],
            progresso=int(data.get('progresso', 0)),
            data_inicio=data_inicio
        )
        
        db.session.add(obra)
        db.session.flush()  # Para obter o ID
        
        # Registrar no histórico de acesso
        from src.models.sistema import HistoricoAcesso
        historico = HistoricoAcesso(
            usuario=data.get('usuario', 'Sistema'),
            acao='create',
            entidade='obra',
            entidade_id=obra.id,
            descricao=f'Obra criada: {obra.nome}',
            status='success'
        )
        db.session.add(historico)
        
        db.session.commit()
        
        return jsonify(obra.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@obra_bp.route('/obras/<int:obra_id>', methods=['PUT'])
def update_obra(obra_id):
    try:
        obra = Obra.query.get_or_404(obra_id)
        data = request.get_json()
        
        obra.nome = data.get('nome', obra.nome)
        obra.localizacao = data.get('localizacao', obra.localizacao)
        obra.valor = float(data.get('valor', obra.valor))
        obra.status = data.get('status', obra.status)
        obra.progresso = int(data.get('progresso', obra.progresso))
        
        if 'dataInicio' in data:
            data_inicio = data['dataInicio']
            if isinstance(data_inicio, str):
                obra.data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        
        obra.data_atualizacao = datetime.utcnow()
        db.session.commit()
        
        return jsonify(obra.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@obra_bp.route('/obras/<int:obra_id>', methods=['DELETE'])
def delete_obra(obra_id):
    try:
        obra = Obra.query.get_or_404(obra_id)
        db.session.delete(obra)
        db.session.commit()
        
        return jsonify({'message': 'Obra deletada com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ETAPAS CRUD
@obra_bp.route('/obras/<int:obra_id>/etapas', methods=['GET'])
def get_etapas(obra_id):
    try:
        etapas = Etapa.query.filter_by(obra_id=obra_id, deletado=False).all()
        return jsonify([etapa.to_dict() for etapa in etapas]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@obra_bp.route('/obras/<int:obra_id>/etapas', methods=['POST'])
def create_etapa(obra_id):
    try:
        data = request.get_json()
        
        # Converter data_etapa se for string
        data_etapa = data.get('dataEtapa')
        if isinstance(data_etapa, str):
            data_etapa = datetime.strptime(data_etapa, '%Y-%m-%d').date()
        
        # Converter fotos para JSON string
        fotos_json = json.dumps(data.get('fotos', []))
        
        etapa = Etapa(
            obra_id=obra_id,
            titulo=data['titulo'],
            descricao=data.get('descricao', ''),
            data_etapa=data_etapa,
            fotos=fotos_json
        )
        
        db.session.add(etapa)
        db.session.commit()
        
        return jsonify(etapa.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@obra_bp.route('/etapas/<int:etapa_id>', methods=['PUT'])
def update_etapa(etapa_id):
    try:
        etapa = Etapa.query.get_or_404(etapa_id)
        data = request.get_json()
        
        etapa.titulo = data.get('titulo', etapa.titulo)
        etapa.descricao = data.get('descricao', etapa.descricao)
        
        if 'dataEtapa' in data:
            data_etapa = data['dataEtapa']
            if isinstance(data_etapa, str):
                etapa.data_etapa = datetime.strptime(data_etapa, '%Y-%m-%d').date()
        
        if 'fotos' in data:
            etapa.fotos = json.dumps(data['fotos'])
        
        etapa.data_atualizacao = datetime.utcnow()
        db.session.commit()
        
        return jsonify(etapa.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@obra_bp.route('/etapas/<int:etapa_id>/soft-delete', methods=['DELETE'])
def soft_delete_etapa(etapa_id):
    try:
        etapa = Etapa.query.get_or_404(etapa_id)
        usuario = request.get_json().get('usuario', 'Sistema')
        
        # Soft delete da etapa
        etapa.soft_delete()
        
        # Adicionar à lixeira
        lixeira_entry = Lixeira(
            etapa_id=etapa_id,
            usuario_exclusao=usuario
        )
        db.session.add(lixeira_entry)
        db.session.commit()
        
        return jsonify({'message': 'Etapa movida para a lixeira'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@obra_bp.route('/etapas/<int:etapa_id>/restore', methods=['POST'])
def restore_etapa(etapa_id):
    try:
        etapa = Etapa.query.get_or_404(etapa_id)
        
        # Restaurar etapa
        etapa.restore()
        
        # Remover da lixeira
        lixeira_entry = Lixeira.query.filter_by(etapa_id=etapa_id).first()
        if lixeira_entry:
            db.session.delete(lixeira_entry)
        
        db.session.commit()
        
        return jsonify({'message': 'Etapa restaurada com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@obra_bp.route('/etapas/<int:etapa_id>', methods=['DELETE'])
def permanent_delete_etapa(etapa_id):
    try:
        etapa = Etapa.query.get_or_404(etapa_id)
        
        # Remover da lixeira se existir
        lixeira_entry = Lixeira.query.filter_by(etapa_id=etapa_id).first()
        if lixeira_entry:
            db.session.delete(lixeira_entry)
        
        # Deletar permanentemente
        db.session.delete(etapa)
        db.session.commit()
        
        return jsonify({'message': 'Etapa deletada permanentemente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# LIXEIRA
@obra_bp.route('/lixeira', methods=['GET'])
def get_lixeira():
    try:
        lixeira_items = Lixeira.query.all()
        return jsonify([item.to_dict() for item in lixeira_items]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@obra_bp.route('/lixeira/limpar', methods=['DELETE'])
def limpar_lixeira():
    try:
        # Deletar permanentemente todas as etapas na lixeira
        lixeira_items = Lixeira.query.all()
        for item in lixeira_items:
            etapa = Etapa.query.get(item.etapa_id)
            if etapa:
                db.session.delete(etapa)
            db.session.delete(item)
        
        db.session.commit()
        
        return jsonify({'message': 'Lixeira limpa com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# MOBILIÁRIO
@obra_bp.route('/obras/<int:obra_id>/mobiliario', methods=['GET'])
def get_mobiliario(obra_id):
    try:
        mobiliario = Mobiliario.query.filter_by(obra_id=obra_id).all()
        return jsonify([mob.to_dict() for mob in mobiliario]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@obra_bp.route('/obras/<int:obra_id>/mobiliario', methods=['POST'])
def create_mobiliario(obra_id):
    try:
        data = request.get_json()
        
        mobiliario = Mobiliario(
            obra_id=obra_id,
            tipo=data['type'],
            comodo=data['room'],
            status=data['status'],
            posicao_x=data.get('x'),
            posicao_y=data.get('y')
        )
        
        db.session.add(mobiliario)
        db.session.commit()
        
        return jsonify(mobiliario.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@obra_bp.route('/mobiliario/<int:mobiliario_id>', methods=['DELETE'])
def delete_mobiliario(mobiliario_id):
    try:
        mobiliario = Mobiliario.query.get_or_404(mobiliario_id)
        db.session.delete(mobiliario)
        db.session.commit()
        
        return jsonify({'message': 'Mobiliário deletado com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



@obra_bp.route("/upload-foto", methods=["POST"])
def upload_foto():
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + "_" + filename
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        # Retorna a URL relativa para o frontend
        return jsonify({"url": f"/static/uploads/{unique_filename}"}), 200
    else:
        return jsonify({"error": "Tipo de arquivo não permitido"}), 400


