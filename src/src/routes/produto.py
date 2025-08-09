from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.produto import Produto, MovimentacaoEstoque, Categoria
from datetime import datetime
import json
import csv
import io
import os
try:
    import openpyxl
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

produto_bp = Blueprint('produto', __name__)

# CORS headers
@produto_bp.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@produto_bp.route('/produtos', methods=['OPTIONS'])
def handle_options():
    return '', 200

# PRODUTOS CRUD
@produto_bp.route('/produtos', methods=['GET'])
def get_produtos():
    try:
        produtos = Produto.query.filter_by(ativo=True).all()
        return jsonify([produto.to_dict() for produto in produtos]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@produto_bp.route('/produtos', methods=['POST'])
def create_produto():
    try:
        data = request.get_json()
        
        produto = Produto(
            nome=data['nome'],
            categoria=data['categoria'],
            codigo=data['codigo'],
            estoque=int(data.get('estoque', 0)),
            estoque_minimo=int(data.get('estoqueMinimo', 0)),
            preco=float(data['preco']),
            unidade=data.get('unidade', 'unidade'),
            descricao=data.get('descricao', '')
        )
        
        db.session.add(produto)
        db.session.flush()  # Para obter o ID
        
        # Registrar movimentação inicial se houver estoque
        if produto.estoque > 0:
            movimentacao = MovimentacaoEstoque(
                produto_id=produto.id,
                tipo='entrada',
                quantidade=produto.estoque,
                quantidade_anterior=0,
                quantidade_atual=produto.estoque,
                motivo='Estoque inicial',
                usuario=data.get('usuario', 'Sistema')
            )
            db.session.add(movimentacao)
        
        # Registrar no histórico de acesso
        from src.models.sistema import HistoricoAcesso
        historico = HistoricoAcesso(
            usuario=data.get('usuario', 'Sistema'),
            acao='create',
            entidade='produto',
            entidade_id=produto.id,
            descricao=f'Produto criado: {produto.nome}',
            status='success'
        )
        db.session.add(historico)
        
        db.session.commit()
        
        return jsonify(produto.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# UPLOAD DE PLANILHA
# DISPENSAÇÃO DE PRODUTOS
@produto_bp.route('/produtos/<int:produto_id>/dispensar', methods=['POST'])
def dispensar_produto(produto_id):
    try:
        data = request.get_json()
        produto = Produto.query.get_or_404(produto_id)
        
        quantidade = int(data['quantidade'])
        local_uso = data['local_uso']
        solicitante = data['solicitante']
        data_dispensacao = data.get('data_dispensacao')
        
        if isinstance(data_dispensacao, str):
            data_dispensacao = datetime.strptime(data_dispensacao, '%Y-%m-%d').date()
        else:
            data_dispensacao = datetime.utcnow().date()
        
        # Verificar se há estoque suficiente
        if produto.estoque < quantidade:
            return jsonify({'error': 'Estoque insuficiente'}), 400
        
        # Atualizar estoque
        estoque_anterior = produto.estoque
        produto.estoque -= quantidade
        produto.data_atualizacao = datetime.utcnow()
        
        # Registrar movimentação
        movimentacao = MovimentacaoEstoque(
            produto_id=produto_id,
            tipo='saida',
            quantidade=quantidade,
            quantidade_anterior=estoque_anterior,
            quantidade_atual=produto.estoque,
            motivo=f'Dispensação para {local_uso}',
            usuario=solicitante,
            data_movimentacao=data_dispensacao
        )
        db.session.add(movimentacao)
        db.session.commit()
        
        return jsonify({
            'message': 'Produto dispensado com sucesso',
            'produto': produto.to_dict(),
            'movimentacao': movimentacao.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# EDIÇÃO DE PRODUTOS
@produto_bp.route('/produtos/<int:produto_id>', methods=['PUT'])
def update_produto(produto_id):
    try:
        data = request.get_json()
        produto = Produto.query.get_or_404(produto_id)
        
        # Salvar estoque anterior para registrar movimentação se necessário
        estoque_anterior = produto.estoque
        
        # Atualizar campos
        produto.nome = data.get('nome', produto.nome)
        produto.categoria = data.get('categoria', produto.categoria)
        produto.codigo = data.get('codigo', produto.codigo)
        produto.preco = float(data.get('preco', produto.preco))
        produto.unidade = data.get('unidade', produto.unidade)
        produto.descricao = data.get('descricao', produto.descricao)
        produto.estoque_minimo = int(data.get('estoque_minimo', produto.estoque_minimo))
        produto.data_atualizacao = datetime.utcnow()
        
        # Se o estoque foi alterado, registrar movimentação
        if 'estoque' in data:
            novo_estoque = int(data['estoque'])
            if novo_estoque != estoque_anterior:
                diferenca = novo_estoque - estoque_anterior
                tipo_movimentacao = 'entrada' if diferenca > 0 else 'saida'
                
                movimentacao = MovimentacaoEstoque(
                    produto_id=produto_id,
                    tipo=tipo_movimentacao,
                    quantidade=abs(diferenca),
                    quantidade_anterior=estoque_anterior,
                    quantidade_atual=novo_estoque,
                    motivo='Ajuste manual via edição',
                    usuario=data.get('usuario', 'Sistema')
                )
                db.session.add(movimentacao)
                produto.estoque = novo_estoque
        
        db.session.commit()
        
        return jsonify(produto.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# UPLOAD DE FOTO DO PRODUTO
@produto_bp.route('/produtos/<int:produto_id>/foto', methods=['POST'])
def upload_foto_produto(produto_id):
    try:
        produto = Produto.query.get_or_404(produto_id)
        
        if 'foto' not in request.files:
            return jsonify({'error': 'Nenhuma foto enviada'}), 400
        
        file = request.files['foto']
        if file.filename == '':
            return jsonify({'error': 'Nenhuma foto selecionada'}), 400
        
        # Validar se é uma imagem PNG
        if not file.filename.lower().endswith('.png'):
            return jsonify({'error': 'Apenas arquivos PNG são aceitos'}), 400
        
        # Criar diretório para fotos se não existir
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads', 'produtos')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Gerar nome único para o arquivo
        filename = f"produto_{produto_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(upload_dir, filename)
        
        # Salvar arquivo
        file.save(filepath)
        
        # Atualizar produto com caminho da foto
        produto.foto = f"/uploads/produtos/{filename}"
        produto.data_atualizacao = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Foto enviada com sucesso',
            'foto_url': produto.foto,
            'produto': produto.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@produto_bp.route('/produtos/upload', methods=['POST'])
def upload_planilha():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        # Validar extensão do arquivo (CSV, Excel)
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        file_extension = None
        for ext in allowed_extensions:
            if file.filename.lower().endswith(ext):
                file_extension = ext
                break
        
        if not file_extension:
            return jsonify({'error': 'Apenas arquivos CSV (.csv), Excel (.xlsx, .xls) são suportados'}), 400
        
        print(f"[DEBUG] File extension: {file_extension}")
        print(f"[DEBUG] File filename: {file.filename}")
        print(f"[DEBUG] Request form data: {request.form}")
        print(f"[DEBUG] Request files data: {request.files}")
        # Opções de validação
        validate_duplicates = request.form.get('validateDuplicates', 'false').lower() == 'true'
        validate_prices = request.form.get('validatePrices', 'false').lower() == 'true'
        validate_stock = request.form.get('validateStock', 'false').lower() == 'true'
        update_existing = request.form.get('updateExisting', 'false').lower() == 'true'
        
        # Ler arquivo com suporte a CSV e Excel
        try:
            if file_extension == '.csv':
                # Para CSV, tentar diferentes encodings e delimitadores
                file_content = file.read()
                content = None
                
                # Lista de encodings para tentar
                encodings = ["iso-8859-1", "utf-8", "latin-1", "cp1252", "utf-8-sig"]
                
                for encoding in encodings:
                    try:
                        content = file_content.decode(encoding)
                        # Tentar diferentes delimitadores
                        for delimiter in [';', ',', '\t']:
                            try:
                                csv_reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
                                fieldnames = csv_reader.fieldnames or []
                                if len(fieldnames) > 1:  # Se tem mais de uma coluna, provavelmente é o delimitador correto
                                    break
                            except:
                                continue
                        if len(fieldnames) > 1:
                            break
                    except UnicodeDecodeError:
                        continue
                
                if content is None or len(fieldnames) <= 1:
                    return jsonify({'error': 'Não foi possível decodificar o arquivo CSV. Verifique o formato e a codificação.'}), 400
            
            elif file_extension in ['.xlsx', '.xls']:
                if not EXCEL_SUPPORT:
                    return jsonify({'error': 'Suporte a Excel não disponível. Use arquivos CSV.'}), 400
                
                file.seek(0)  # Reset file pointer
                workbook = openpyxl.load_workbook(file, read_only=True)
                worksheet = workbook.active
                
                # Converter para formato similar ao CSV
                rows = list(worksheet.iter_rows(values_only=True))
                if not rows:
                    return jsonify({'error': 'Planilha Excel está vazia.'}), 400
                
                # Primeira linha como cabeçalho
                fieldnames = [str(cell) if cell is not None else '' for cell in rows[0]]
                
                # Criar um leitor CSV simulado
                csv_data = []
                for row in rows[1:]:  # Pular cabeçalho
                    row_dict = {}
                    for i, cell in enumerate(row):
                        if i < len(fieldnames):
                            row_dict[fieldnames[i]] = str(cell) if cell is not None else ''
                    csv_data.append(row_dict)
                
                # Simular csv_reader para compatibilidade
                class ExcelReader:
                    def __init__(self, data, fieldnames):
                        self.data = data
                        self.fieldnames = fieldnames
                    
                    def __iter__(self):
                        return iter(self.data)
                
                csv_reader = ExcelReader(csv_data, fieldnames)
            
            else:
                return jsonify({'error': 'Formato de arquivo não suportado.'}), 400
        
        except Exception as e:
            return jsonify({'error': f'Erro ao ler arquivo: {str(e)}'}), 400
        
        # Validar colunas obrigatórias
        required_columns = ['nome', 'categoria', 'codigo', 'estoque', 'estoque_minimo', 'preco']
        missing_columns = [col for col in required_columns if col not in fieldnames]
        if missing_columns:
            return jsonify({
                'error': f'Colunas obrigatórias ausentes: {", ".join(missing_columns)}',
                'required_columns': required_columns,
                'found_columns': fieldnames
            }), 400
        
        # Validar dados linha por linha
        errors = []
        warnings = []
        valid_rows = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 because row 1 is header
            row_errors = []
            row_warnings = []
            
            # Validar campos obrigatórios
            if not str(row.get('nome', '')).strip():
                row_errors.append('Nome é obrigatório')
            
            if not str(row.get('categoria', '')).strip():
                row_errors.append('Categoria é obrigatória')
            
            if not str(row.get('codigo', '')).strip():
                row_errors.append('Código é obrigatório')
            
            # Validar tipos de dados
            try:
                estoque = int(float(row.get('estoque', 0)))
                if validate_stock and estoque < 0:
                    row_errors.append('Estoque deve ser um número positivo')
            except (ValueError, TypeError):
                row_errors.append('Estoque deve ser um número válido')
                estoque = 0
            
            try:
                estoque_minimo = int(float(row.get('estoque_minimo', 0)))
                if estoque_minimo < 0:
                    row_errors.append('Estoque mínimo deve ser um número positivo')
            except (ValueError, TypeError):
                row_errors.append('Estoque mínimo deve ser um número válido')
                estoque_minimo = 0
            
            try:
                preco = float(row.get('preco', 0))
                if validate_prices and preco <= 0:
                    row_errors.append('Preço deve ser maior que zero')
            except (ValueError, TypeError):
                row_errors.append('Preço deve ser um número válido')
                preco = 0.0
            
            # Validar duplicatas por código
            if validate_duplicates:
                codigo = str(row.get('codigo', '')).strip()
                existing_product = Produto.query.filter_by(codigo=codigo, ativo=True).first()
                if existing_product:
                    if update_existing:
                        row_warnings.append(f'Produto com código {codigo} será atualizado')
                    else:
                        row_errors.append(f'Produto com código {codigo} já existe')
            
            # Se há erros, adicionar à lista de erros
            if row_errors:
                errors.append({
                    'linha': row_num,
                    'erros': row_errors
                })
            else:
                # Adicionar warnings se houver
                if row_warnings:
                    warnings.append({
                        'linha': row_num,
                        'avisos': row_warnings
                    })
                
                # Adicionar à lista de linhas válidas
                valid_rows.append({
                    'nome': str(row.get('nome', '')).strip(),
                    'categoria': str(row.get('categoria', '')).strip(),
                    'codigo': str(row.get('codigo', '')).strip(),
                    'estoque': estoque,
                    'estoque_minimo': estoque_minimo,
                    'preco': preco,
                    'unidade': str(row.get('unidade', 'unidade')).strip() or 'unidade',
                    'descricao': str(row.get('descricao', '')).strip()
                })
        
        # Se há erros críticos, retornar sem processar
        if errors:
            return jsonify({
                'error': 'Erros encontrados na planilha',
                'details': errors
            }), 400
        # Processar linhas válidas
        created_count = 0
        updated_count = 0
        
        for row_data in valid_rows:
            existing_product = Produto.query.filter_by(codigo=row_data['codigo'], ativo=True).first()
            
            if existing_product and update_existing:
                # Atualizar produto existente
                estoque_anterior = existing_product.estoque
                
                existing_product.nome = row_data['nome']
                existing_product.categoria = row_data['categoria']
                existing_product.estoque_minimo = row_data['estoque_minimo']
                existing_product.preco = row_data['preco']
                existing_product.unidade = row_data['unidade']
                existing_product.descricao = row_data['descricao']
                existing_product.data_atualizacao = datetime.utcnow()
                
                # Se o estoque foi alterado, registrar movimentação
                if row_data['estoque'] != estoque_anterior:
                    diferenca = row_data['estoque'] - estoque_anterior
                    tipo_movimentacao = 'entrada' if diferenca > 0 else 'saida'
                    
                    movimentacao = MovimentacaoEstoque(
                        produto_id=existing_product.id,
                        tipo=tipo_movimentacao,
                        quantidade=abs(diferenca),
                        quantidade_anterior=estoque_anterior,
                        quantidade_atual=row_data['estoque'],
                        motivo='Atualização via planilha',
                        usuario='Sistema'
                    )
                    db.session.add(movimentacao)
                    existing_product.estoque = row_data['estoque']
                
                updated_count += 1
            
            elif not existing_product:
                # Criar novo produto
                produto = Produto(
                    nome=row_data['nome'],
                    categoria=row_data['categoria'],
                    codigo=row_data['codigo'],
                    estoque=row_data['estoque'],
                    estoque_minimo=row_data['estoque_minimo'],
                    preco=row_data['preco'],
                    unidade=row_data['unidade'],
                    descricao=row_data['descricao']
                )
                
                db.session.add(produto)
                db.session.flush()  # Para obter o ID
                
                # Registrar movimentação inicial se houver estoque
                if produto.estoque > 0:
                    movimentacao = MovimentacaoEstoque(
                        produto_id=produto.id,
                        tipo='entrada',
                        quantidade=produto.estoque,
                        quantidade_anterior=0,
                        quantidade_atual=produto.estoque,
                        motivo='Estoque inicial via planilha',
                        usuario='Sistema'
                    )
                    db.session.add(movimentacao)
                
                created_count += 1
        
        # Salvar todas as alterações
        db.session.commit()
        
        return jsonify({
            'message': 'Planilha processada com sucesso',
            'created': created_count,
            'updated': updated_count,
            'warnings': warnings,
            'total_processed': created_count + updated_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500



# ENDPOINT PARA HISTÓRICO DE MOVIMENTAÇÕES
@produto_bp.route('/produtos/movimentacoes', methods=['GET'])
def get_movimentacoes():
    try:
        # Buscar todas as movimentações ordenadas por data (mais recentes primeiro)
        movimentacoes = MovimentacaoEstoque.query.order_by(MovimentacaoEstoque.data_movimentacao.desc()).all()
        
        # Converter para dict incluindo dados do produto
        result = []
        for mov in movimentacoes:
            mov_dict = mov.to_dict()
            if mov.produto:
                mov_dict['produto'] = {
                    'id': mov.produto.id,
                    'nome': mov.produto.nome,
                    'categoria': mov.produto.categoria,
                    'codigo': mov.produto.codigo
                }
            result.append(mov_dict)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@produto_bp.route('/produtos/movimentacoes/<int:produto_id>', methods=['GET'])
def get_movimentacoes_produto(produto_id):
    try:
        # Buscar movimentações de um produto específico
        movimentacoes = MovimentacaoEstoque.query.filter_by(produto_id=produto_id).order_by(MovimentacaoEstoque.data_movimentacao.desc()).all()
        
        result = []
        for mov in movimentacoes:
            mov_dict = mov.to_dict()
            if mov.produto:
                mov_dict['produto'] = {
                    'id': mov.produto.id,
                    'nome': mov.produto.nome,
                    'categoria': mov.produto.categoria,
                    'codigo': mov.produto.codigo
                }
            result.append(mov_dict)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

