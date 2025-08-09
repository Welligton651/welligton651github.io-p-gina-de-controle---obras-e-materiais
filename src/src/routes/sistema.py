from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.sistema import HistoricoAcesso, ConfiguracaoSistema, Feed, ComentarioFeed
from datetime import datetime, timedelta
import json

sistema_bp = Blueprint('sistema', __name__)

# CORS headers
@sistema_bp.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@sistema_bp.route('/sistema', methods=['OPTIONS'])
def handle_options():
    return '', 200

# LOGIN
@sistema_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        nome = data.get('nome', '')
        senha = data.get('senha', '')
        tipo = data.get('tipo', '')
        
        # Validação simples - senha Master123 para administradores
        if senha == 'Master123' and tipo == 'Administrador':
            # Registrar no histórico de acesso
            historico = HistoricoAcesso(
                usuario=nome,
                acao='login',
                descricao=f'Login realizado com sucesso - {tipo}',
                status='success',
                ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')),
                user_agent=request.environ.get('HTTP_USER_AGENT')
            )
            db.session.add(historico)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Login realizado com sucesso',
                'usuario': {
                    'nome': nome,
                    'tipo': tipo
                }
            }), 200
        else:
            # Registrar tentativa de login falhada
            historico = HistoricoAcesso(
                usuario=nome or 'Desconhecido',
                acao='login_failed',
                descricao=f'Tentativa de login falhada - {tipo}',
                status='error',
                ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')),
                user_agent=request.environ.get('HTTP_USER_AGENT')
            )
            db.session.add(historico)
            db.session.commit()
            
            return jsonify({
                'success': False,
                'message': 'Credenciais inválidas'
            }), 401
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# HISTÓRICO DE ACESSO
@sistema_bp.route('/historico-acesso', methods=['GET'])
def get_historico_acesso():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        usuario = request.args.get('usuario')
        acao = request.args.get('acao')
        
        query = HistoricoAcesso.query
        
        if usuario:
            query = query.filter(HistoricoAcesso.usuario.ilike(f'%{usuario}%'))
        if acao:
            query = query.filter_by(acao=acao)
        
        historico = query.order_by(HistoricoAcesso.data_acao.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'items': [item.to_dict() for item in historico.items],
            'total': historico.total,
            'pages': historico.pages,
            'currentPage': page,
            'perPage': per_page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sistema_bp.route('/historico-acesso', methods=['POST'])
def create_historico_acesso():
    try:
        data = request.get_json()
        
        # Capturar informações da requisição
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        user_agent = request.environ.get('HTTP_USER_AGENT')
        
        historico = HistoricoAcesso(
            usuario=data['usuario'],
            acao=data['acao'],
            entidade=data.get('entidade'),
            entidade_id=data.get('entidadeId'),
            descricao=data['descricao'],
            detalhes=json.dumps(data.get('detalhes', {})),
            status=data.get('status', 'success'),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(historico)
        db.session.commit()
        
        return jsonify(historico.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sistema_bp.route('/historico-acesso/<int:historico_id>', methods=['DELETE'])
def delete_historico_acesso(historico_id):
    try:
        historico = HistoricoAcesso.query.get_or_404(historico_id)
        db.session.delete(historico)
        db.session.commit()
        
        return jsonify({'message': 'Registro de histórico deletado com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sistema_bp.route('/historico-acesso/limpar', methods=['DELETE'])
def limpar_historico_acesso():
    try:
        dias = request.args.get('dias', 30, type=int)
        data_limite = datetime.utcnow() - timedelta(days=dias)
        
        registros_deletados = HistoricoAcesso.query.filter(
            HistoricoAcesso.data_acao < data_limite
        ).delete()
        
        db.session.commit()
        
        return jsonify({
            'message': f'Histórico limpo com sucesso',
            'registrosDeletados': registros_deletados
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# CONFIGURAÇÕES DO SISTEMA
@sistema_bp.route('/configuracoes', methods=['GET'])
def get_configuracoes():
    try:
        categoria = request.args.get('categoria')
        
        query = ConfiguracaoSistema.query
        if categoria:
            query = query.filter_by(categoria=categoria)
        
        configuracoes = query.all()
        
        # Organizar por categoria
        resultado = {}
        for config in configuracoes:
            if config.categoria not in resultado:
                resultado[config.categoria] = {}
            resultado[config.categoria][config.chave] = config.to_dict()
        
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sistema_bp.route('/configuracoes', methods=['POST'])
def create_configuracao():
    try:
        data = request.get_json()
        
        configuracao = ConfiguracaoSistema(
            chave=data['chave'],
            valor=str(data['valor']),
            tipo=data.get('tipo', 'string'),
            descricao=data.get('descricao', ''),
            categoria=data.get('categoria', 'geral'),
            editavel=data.get('editavel', True)
        )
        
        db.session.add(configuracao)
        db.session.commit()
        
        return jsonify(configuracao.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sistema_bp.route('/configuracoes/<int:config_id>', methods=['PUT'])
def update_configuracao(config_id):
    try:
        configuracao = ConfiguracaoSistema.query.get_or_404(config_id)
        data = request.get_json()
        
        if not configuracao.editavel:
            return jsonify({'error': 'Esta configuração não pode ser editada'}), 403
        
        configuracao.valor = str(data.get('valor', configuracao.valor))
        configuracao.descricao = data.get('descricao', configuracao.descricao)
        configuracao.data_atualizacao = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(configuracao.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# FEED
@sistema_bp.route('/feed', methods=['GET'])
def get_feed():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        obra_id = request.args.get('obra_id', type=int)
        tipo = request.args.get('tipo')
        
        query = Feed.query.filter_by(publico=True)
        
        if obra_id:
            query = query.filter_by(obra_id=obra_id)
        if tipo:
            query = query.filter_by(tipo=tipo)
        
        feed = query.order_by(Feed.data_publicacao.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'items': [item.to_dict() for item in feed.items],
            'total': feed.total,
            'pages': feed.pages,
            'currentPage': page,
            'perPage': per_page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sistema_bp.route('/feed', methods=['POST'])
def create_feed():
    try:
        data = request.get_json()
        
        feed = Feed(
            usuario=data['usuario'],
            titulo=data['titulo'],
            conteudo=data['conteudo'],
            tipo=data.get('tipo', 'post'),
            obra_id=data.get('obraId'),
            imagens=json.dumps(data.get('imagens', [])),
            tags=json.dumps(data.get('tags', [])),
            publico=data.get('publico', True)
        )
        
        db.session.add(feed)
        db.session.commit()
        
        return jsonify(feed.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sistema_bp.route('/feed/<int:feed_id>', methods=['PUT'])
def update_feed(feed_id):
    try:
        feed = Feed.query.get_or_404(feed_id)
        data = request.get_json()
        
        feed.titulo = data.get('titulo', feed.titulo)
        feed.conteudo = data.get('conteudo', feed.conteudo)
        feed.tipo = data.get('tipo', feed.tipo)
        
        if 'imagens' in data:
            feed.imagens = json.dumps(data['imagens'])
        if 'tags' in data:
            feed.tags = json.dumps(data['tags'])
        
        feed.publico = data.get('publico', feed.publico)
        feed.data_atualizacao = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(feed.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sistema_bp.route('/feed/<int:feed_id>', methods=['DELETE'])
def delete_feed(feed_id):
    try:
        feed = Feed.query.get_or_404(feed_id)
        db.session.delete(feed)
        db.session.commit()
        
        return jsonify({'message': 'Post deletado com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sistema_bp.route('/feed/<int:feed_id>/curtir', methods=['POST'])
def curtir_feed(feed_id):
    try:
        feed = Feed.query.get_or_404(feed_id)
        feed.curtidas += 1
        
        db.session.commit()
        
        return jsonify({'curtidas': feed.curtidas}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# COMENTÁRIOS DO FEED
@sistema_bp.route('/feed/<int:feed_id>/comentarios', methods=['GET'])
def get_comentarios_feed(feed_id):
    try:
        comentarios = ComentarioFeed.query.filter_by(feed_id=feed_id).order_by(ComentarioFeed.data_comentario.asc()).all()
        return jsonify([comentario.to_dict() for comentario in comentarios]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sistema_bp.route('/feed/<int:feed_id>/comentarios', methods=['POST'])
def create_comentario_feed(feed_id):
    try:
        data = request.get_json()
        
        comentario = ComentarioFeed(
            feed_id=feed_id,
            usuario=data['usuario'],
            conteudo=data['conteudo']
        )
        
        # Atualizar contador de comentários
        feed = Feed.query.get_or_404(feed_id)
        feed.comentarios_count += 1
        
        db.session.add(comentario)
        db.session.commit()
        
        return jsonify(comentario.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sistema_bp.route('/comentarios/<int:comentario_id>', methods=['DELETE'])
def delete_comentario_feed(comentario_id):
    try:
        comentario = ComentarioFeed.query.get_or_404(comentario_id)
        
        # Atualizar contador de comentários
        feed = Feed.query.get_or_404(comentario.feed_id)
        feed.comentarios_count = max(0, feed.comentarios_count - 1)
        
        db.session.delete(comentario)
        db.session.commit()
        
        return jsonify({'message': 'Comentário deletado com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

