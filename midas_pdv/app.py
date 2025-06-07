from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload # Import for eager loading
import os
# Ensure datetime, timedelta, time are imported if not already (they are used in api_create_agendamento)
from datetime import datetime, timedelta, time


app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your_very_secret_key_here'  # Change this in a real application!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads', 'profile_pics')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create the SQLAlchemy db instance
db = SQLAlchemy(app)

# --- Models (Copied from previous step, ensure they are up-to-date) ---
servico_profissionais = db.Table('servico_profissionais',
    db.Column('servico_id', db.Integer, db.ForeignKey('servico.id'), primary_key=True),
    db.Column('profissional_id', db.Integer, db.ForeignKey('profissional.id'), primary_key=True)
)

class Empresa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_loja = db.Column(db.String, nullable=False)
    nome_proprietario = db.Column(db.String, nullable=False)
    nome_usuario = db.Column(db.String, unique=True, nullable=False)
    senha = db.Column(db.String, nullable=False)  # Will be hashed
    imagem_perfil = db.Column(db.String, nullable=True) # Path to image
    dominio = db.Column(db.String, unique=True, nullable=False)

    profissionais = db.relationship('Profissional', backref='empresa', lazy=True)
    servicos = db.relationship('Servico', backref='empresa', lazy=True)
    clientes = db.relationship('Cliente', backref='empresa', lazy=True)
    agendamentos = db.relationship('Agendamento', backref='empresa', lazy=True)

    def __repr__(self):
        return f'<Empresa {self.nome_loja}>'

class Profissional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    nome_profissional = db.Column(db.String, nullable=False)
    telefone = db.Column(db.String, nullable=True)
    nome_usuario = db.Column(db.String, unique=True, nullable=False)
    senha = db.Column(db.String, nullable=False)  # Will be hashed
    tipo_comissao = db.Column(db.String, nullable=True)  # 'fixo' or 'porcentagem'
    valor_fixo = db.Column(db.Float, nullable=True)
    porcentagem_comissao = db.Column(db.Float, nullable=True)

    horarios = db.relationship('Horario', backref='profissional', lazy=True)
    agendamentos = db.relationship('Agendamento', backref='profissional', lazy=True)

    def __repr__(self):
        return f'<Profissional {self.nome_profissional}>'

class Servico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    nome_servico = db.Column(db.String, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    duracao = db.Column(db.Integer, nullable=False)  # in minutes
    preco = db.Column(db.Float, nullable=False)
    sinal = db.Column(db.Boolean, default=False)
    porcentagem_sinal = db.Column(db.Float, nullable=True)

    profissionais = db.relationship('Profissional', secondary=servico_profissionais,
                                    backref=db.backref('servicos', lazy='dynamic'), lazy='dynamic')
    agendamentos = db.relationship('Agendamento', backref='servico', lazy=True)

    def __repr__(self):
        return f'<Servico {self.nome_servico}>'

class Horario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissional.id'), nullable=False)
    dia_semana = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    horario_inicio_trabalho = db.Column(db.Time, nullable=True)
    horario_termino_trabalho = db.Column(db.Time, nullable=True)
    horario_inicio_almoco = db.Column(db.Time, nullable=True)
    horario_termino_almoco = db.Column(db.Time, nullable=True)
    pausa_entre_atendimentos = db.Column(db.Integer, nullable=True)  # in minutes
    dia_folga = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Horario P:{self.profissional_id} Dia:{self.dia_semana}>'

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    nome_cliente = db.Column(db.String, nullable=False)
    telefone = db.Column(db.String, unique=True, nullable=False)
    valor_gasto = db.Column(db.Float, default=0.0)

    agendamentos = db.relationship('Agendamento', backref='cliente', lazy=True)

    def __repr__(self):
        return f'<Cliente {self.nome_cliente}>'

class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey('servico.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissional.id'), nullable=False)
    data_agendamento = db.Column(db.Date, nullable=False)
    horario_inicio = db.Column(db.Time, nullable=False)
    horario_fim = db.Column(db.Time, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String, nullable=False, default='Pendente')

    def __repr__(self):
        return f'<Agendamento ID:{self.id} Cliente:{self.cliente_id} Dia:{self.data_agendamento} Hora:{self.horario_inicio}>'
# --- End of Models ---

@app.route('/', methods=['GET'])
def root_route():
    if 'empresa_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        store_name = request.form.get('store_name')
        owner_name = request.form.get('owner_name')
        username = request.form.get('register_username')
        password = request.form.get('register_password')
        domain = request.form.get('domain')
        photo = request.files.get('photo')

        # Basic validation
        if not all([store_name, owner_name, username, password, domain]):
            flash('Todos os campos obrigatórios devem ser preenchidos.', 'danger')
            return redirect(url_for('root_route'))

        # Check if username or domain already exists
        # Enhanced Validations for register route
        error_messages = []
        if len(store_name) > 100: error_messages.append("Nome da loja não deve exceder 100 caracteres.")
        if len(owner_name) > 100: error_messages.append("Nome do proprietário não deve exceder 100 caracteres.")
        if len(username) > 50: error_messages.append("Nome de usuário não deve exceder 50 caracteres.")
        if len(username) < 3: error_messages.append("Nome de usuário deve ter pelo menos 3 caracteres.")
        if len(password) < 6: error_messages.append("Senha deve ter pelo menos 6 caracteres.")
        if len(domain) > 50: error_messages.append("Domínio não deve exceder 50 caracteres.")
        # Basic domain format check (alphanumeric and -)
        if not domain.isalnum() and '-' not in domain and '.' not in domain:
             if not all(c.isalnum() or c == '-' for c in domain):
                error_messages.append("Domínio pode conter apenas letras, números e hífen.")


        if error_messages:
            for msg in error_messages:
                flash(msg, 'danger')
            # Re-render with form data. Assume login.html handles 'register' tab and form data.
            # This part might need template adjustment if not already handled.
            return render_template('login.html', form_type='register', form_data=request.form)


        # Check if username or domain already exists (moved after length checks)
        if Empresa.query.filter_by(nome_usuario=username).first():
            flash('Nome de usuário já existe.', 'danger')
            return render_template('login.html', form_type='register', form_data=request.form)
        if Empresa.query.filter_by(dominio=domain).first():
            flash('Domínio já registrado.', 'danger')
            return render_template('login.html', form_type='register', form_data=request.form)

        hashed_password = generate_password_hash(password)

        filename = None
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            try:
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except Exception as e:
                flash(f'Erro ao salvar imagem: {str(e)}', 'danger')
                return redirect(url_for('root_route'))

        new_empresa = Empresa(
            nome_loja=store_name,
            nome_proprietario=owner_name,
            nome_usuario=username,
            senha=hashed_password,
            imagem_perfil=filename, # Store filename or path
            dominio=domain
        )
        try:
            db.session.add(new_empresa)
            db.session.commit()
            # Store info in session after successful commit
            session['empresa_id'] = new_empresa.id
            session['nome_proprietario'] = new_empresa.nome_proprietario
            session['nome_da_loja'] = new_empresa.nome_loja
            session['imagem_perfil'] = new_empresa.imagem_perfil
            flash('Cadastro realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        except IntegrityError as e: # Catching unique constraint violations specifically
            db.session.rollback()
            # This typically means username or domain already exists, handled above, but good for other potential unique fields.
            flash('Erro de integridade de dados. Nome de usuário ou domínio pode já existir.', 'danger')
            return render_template('login.html', form_type='register', form_data=request.form)
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar empresa: {str(e)}', 'danger')
            # Potentially delete uploaded file if commit fails
            if filename and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                 try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                 except OSError:
                    pass # ignore if deletion fails, but log it ideally
            return render_template('login.html', form_type='register', form_data=request.form) # Show form again

    return redirect(url_for('root_route')) # Should not be reached via GET, or handle as error

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('login_username')
        password = request.form.get('login_password')

        error_messages = []
        if not username: error_messages.append("Nome de usuário é obrigatório.")
        if not password: error_messages.append("Senha é obrigatória.")
        if len(username) > 50 : error_messages.append("Nome de usuário excede o limite de caracteres.")

        if error_messages:
            for msg in error_messages:
                flash(msg, 'danger')
            return render_template('login.html', form_type='login', form_data=request.form)


        empresa = Empresa.query.filter_by(nome_usuario=username).first()

        if empresa and check_password_hash(empresa.senha, password):
            session['empresa_id'] = empresa.id
            session['nome_proprietario'] = empresa.nome_proprietario
            session['nome_da_loja'] = empresa.nome_loja
            session['imagem_perfil'] = empresa.imagem_perfil
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Nome de usuário ou senha inválidos.', 'danger')
            return render_template('login.html', form_type='login', form_data=request.form) # Show form again

    return redirect(url_for('root_route')) # Should not be reached via GET, or handle as error

@app.route('/dashboard')
def dashboard():
    if 'empresa_id' not in session:
        flash('Você precisa estar logado para acessar o dashboard.', 'warning')
        return redirect(url_for('root_route'))

    # Pass session data to the template
    return render_template(
        'dashboard.html',
        nome_da_loja=session.get('nome_da_loja'),
        nome_do_proprietario=session.get('nome_proprietario'),
        imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None
    )

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('root_route'))

# --- Profissionais Routes ---
@app.route('/profissionais/add', methods=['GET', 'POST'])
def add_profissionais():
    if 'empresa_id' not in session:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('root_route'))

    empresa_id = session['empresa_id']

    if request.method == 'POST':
        nome_profissional = request.form.get('professionalName')
        telefone = request.form.get('phone')
        nome_usuario = request.form.get('username')
        senha = request.form.get('password')

        commission_toggle = request.form.get('commissionToggle') == 'on' # Checkbox value is 'on' if checked
        tipo_comissao = request.form.get('commissionType') if commission_toggle else None
        valor_fixo_str = request.form.get('fixedValue') if commission_toggle and tipo_comissao == 'fixed' else None
        porcentagem_comissao_str = request.form.get('percentage') if commission_toggle and tipo_comissao == 'percentage' else None

        # Enhanced Validation for add_profissionais
        error_messages = []
        if not nome_profissional: error_messages.append('Nome do profissional é obrigatório.')
        if len(nome_profissional) > 100: error_messages.append('Nome do profissional excede 100 caracteres.')

        if not nome_usuario: error_messages.append('Nome de usuário é obrigatório.')
        if len(nome_usuario) > 50: error_messages.append('Nome de usuário excede 50 caracteres.')
        if len(nome_usuario) < 3: error_messages.append('Nome de usuário deve ter pelo menos 3 caracteres.')

        if not senha: error_messages.append('Senha é obrigatória.')
        if len(senha) < 6: error_messages.append('Senha deve ter pelo menos 6 caracteres.')

        if telefone and not telefone.replace("(", "").replace(")", "").replace("-", "").replace(" ", "").isdigit():
             error_messages.append('Telefone parece ter um formato inválido.')
        if telefone and len(telefone) > 20: error_messages.append('Telefone excede 20 caracteres.')

        valor_fixo = None
        if valor_fixo_str:
            try:
                valor_fixo = float(valor_fixo_str)
                if valor_fixo < 0: error_messages.append('Valor fixo da comissão não pode ser negativo.')
            except ValueError:
                error_messages.append('Valor fixo da comissão inválido.')

        porcentagem_comissao = None
        if porcentagem_comissao_str:
            try:
                porcentagem_comissao = float(porcentagem_comissao_str)
                if porcentagem_comissao < 0: error_messages.append('Porcentagem da comissão não pode ser negativa.')
            except ValueError:
                error_messages.append('Valor da porcentagem da comissão inválido.')

        if error_messages:
            for msg in error_messages: flash(msg, 'danger')
            return render_template('add_profissionais.html',
                                   nome_da_loja=session.get('nome_da_loja'),
                                   nome_do_proprietario=session.get('nome_proprietario'),
                                   imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None,
                                   form_data=request.form)

        # Check if username already exists for this empresa (after other validations)
        existing_professional = Profissional.query.filter_by(empresa_id=empresa_id, nome_usuario=nome_usuario).first()
        if existing_professional:
            flash('Este nome de usuário já está em uso por outro profissional nesta empresa.', 'danger')
            return render_template('add_profissionais.html',
                                   nome_da_loja=session.get('nome_da_loja'),
                                   nome_do_proprietario=session.get('nome_proprietario'),
                                   imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None,
                                   form_data=request.form)

        hashed_password = generate_password_hash(senha)

        new_professional = Profissional(
            empresa_id=empresa_id,
            nome_profissional=nome_profissional,
            telefone=telefone,
            nome_usuario=nome_usuario,
            senha=hashed_password,
            tipo_comissao=tipo_comissao if commission_toggle else None,
            valor_fixo=valor_fixo if commission_toggle and tipo_comissao == 'fixed' else None,
            porcentagem_comissao=porcentagem_comissao if commission_toggle and tipo_comissao == 'percentage' else None
        )

        try:
            db.session.add(new_professional)
            db.session.commit()
            flash('Profissional adicionado com sucesso!', 'success')
            return redirect(url_for('all_profissionais'))
        except IntegrityError: # Usually for nome_usuario unique constraint if not caught above
            db.session.rollback()
            flash('Nome de usuário para profissional já existe nesta empresa.', 'danger')
            return render_template('add_profissionais.html',
                                   nome_da_loja=session.get('nome_da_loja'),
                                   nome_do_proprietario=session.get('nome_proprietario'),
                                   imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None,
                                   form_data=request.form)
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar profissional: {str(e)}', 'danger')
            return render_template('add_profissionais.html',
                                   nome_da_loja=session.get('nome_da_loja'),
                                   nome_do_proprietario=session.get('nome_proprietario'),
                                   imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None,
                                   form_data=request.form)

    # GET request
    return render_template('add_profissionais.html',
                           nome_da_loja=session.get('nome_da_loja'),
                           nome_do_proprietario=session.get('nome_proprietario'),
                           imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None)

@app.route('/profissionais/all')
def all_profissionais():
    if 'empresa_id' not in session:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('root_route'))

    empresa_id = session['empresa_id']
    profissionais = Profissional.query.filter_by(empresa_id=empresa_id).all()

    return render_template('all_profissionais.html',
                           profissionais=profissionais,
                           nome_da_loja=session.get('nome_da_loja'),
                           nome_do_proprietario=session.get('nome_proprietario'),
                           imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None)

# --- End Profissionais Routes ---

# --- Servicos Routes ---
@app.route('/servicos/add', methods=['GET', 'POST'])
def add_servico():
    if 'empresa_id' not in session:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('root_route'))

    empresa_id = session['empresa_id']
    # Always fetch professionals for the form, regardless of GET or POST (in case of validation error on POST)
    profissionais_empresa = Profissional.query.filter_by(empresa_id=empresa_id).order_by(Profissional.nome_profissional).all()

    if request.method == 'POST':
        service_name = request.form.get('serviceName')
        description = request.form.get('description')
        duration_str = request.form.get('duration')
        price_str = request.form.get('price')
        selected_professional_ids = request.form.getlist('professionals') # For multi-select
        require_signal = request.form.get('requireSignal') == 'on'
        signal_percentage_str = request.form.get('signalPercentage') if require_signal else None

        # Enhanced Validation for add_servico
        error_messages = []
        if not service_name: error_messages.append('Nome do serviço é obrigatório.')
        if len(service_name) > 100: error_messages.append('Nome do serviço excede 100 caracteres.')
        if not selected_professional_ids: error_messages.append('Pelo menos um profissional deve ser selecionado.')

        duration = None
        if not duration_str:
            error_messages.append('Duração é obrigatória.')
        else:
            try:
                duration = int(duration_str)
                if duration <= 0: error_messages.append('Duração deve ser um número positivo.')
            except ValueError:
                error_messages.append('Duração deve ser um número.')

        price = None
        if not price_str:
            error_messages.append('Preço é obrigatório.')
        else:
            try:
                price = float(price_str)
                if price < 0: error_messages.append('Preço não pode ser negativo.') # Price can be 0 for free service
            except ValueError:
                error_messages.append('Preço deve ser um número.')

        signal_percentage = None
        if require_signal:
            if not signal_percentage_str:
                error_messages.append('Porcentagem do sinal é obrigatória quando "Exigir Sinal" está marcado.')
            else:
                try:
                    signal_percentage = float(signal_percentage_str)
                    if not (0 <= signal_percentage <= 100):
                        error_messages.append('Porcentagem do sinal deve ser entre 0 e 100.')
                except ValueError:
                    error_messages.append('Porcentagem do sinal deve ser um número.')

        if error_messages:
            for msg in error_messages: flash(msg, 'danger')
            return render_template('add_servico.html',
                                   profissionais=profissionais_empresa,
                                   nome_da_loja=session.get('nome_da_loja'),
                                   nome_do_proprietario=session.get('nome_proprietario'),
                                   imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None,
                                   form_data=request.form) # Pass back form_data


        new_service = Servico(
            empresa_id=empresa_id,
            nome_servico=service_name,
            descricao=description,
            duracao=duration,
            preco=price,
            sinal=require_signal,
            porcentagem_sinal=signal_percentage if require_signal else None
        )

        # Add professionals to the service
        valid_professionals_selected = False
        for prof_id_str in selected_professional_ids:
            try:
                prof_id = int(prof_id_str)
                professional = Profissional.query.get(prof_id)
                # Security check: ensure professional belongs to the current empresa_id
                if professional and professional.empresa_id == empresa_id:
                    new_service.profissionais.append(professional)
                    valid_professionals_selected = True
                else:
                    flash(f'Profissional com ID {prof_id} inválido ou não pertence à sua empresa.', 'warning')
            except ValueError:
                flash(f'ID de profissional inválido: {prof_id_str}.', 'warning')

        if not valid_professionals_selected and selected_professional_ids: # only error if some were attempted but all failed
             flash('Nenhum profissional válido foi processado para o serviço. Verifique os avisos.', 'danger')
             return render_template('add_servico.html',
                                   profissionais=profissionais_empresa,
                                   nome_da_loja=session.get('nome_da_loja'),
                                   nome_do_proprietario=session.get('nome_proprietario'),
                                   imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None,
                                   form_data=request.form)
        elif not selected_professional_ids: # This case is already caught by the initial 'all' check
            pass


        try:
            db.session.add(new_service)
            db.session.commit()
            flash('Serviço adicionado com sucesso!', 'success')
            return redirect(url_for('all_servicos'))
        except IntegrityError: # Catch if a unique constraint on Servico fails (e.g. name for same company if made unique)
            db.session.rollback()
            flash('Erro de integridade ao salvar o serviço. Verifique se já não existe um com o mesmo nome.', 'danger')
            return render_template('add_servico.html',
                                   profissionais=profissionais_empresa,
                                   nome_da_loja=session.get('nome_da_loja'),
                                   nome_do_proprietario=session.get('nome_proprietario'),
                                   imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None,
                                   form_data=request.form)
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar serviço: {str(e)}', 'danger')
            # Log the exception e for debugging
            return render_template('add_servico.html',
                                   profissionais=profissionais_empresa,
                                   nome_da_loja=session.get('nome_da_loja'),
                                   nome_do_proprietario=session.get('nome_proprietario'),
                                   imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None,
                                   form_data=request.form)

    # GET request
    return render_template('add_servico.html',
                           profissionais=profissionais_empresa,
                           nome_da_loja=session.get('nome_da_loja'),
                           nome_do_proprietario=session.get('nome_proprietario'),
                           imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None)


@app.route('/servicos/all')
def all_servicos():
    if 'empresa_id' not in session:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('root_route'))

    empresa_id = session['empresa_id']
    # Eager load professionals for each service using joinedload
    servicos = Servico.query.filter_by(empresa_id=empresa_id).options(joinedload(Servico.profissionais)).all()

    return render_template('all_servicos.html',
                           servicos=servicos,
                           nome_da_loja=session.get('nome_da_loja'),
                           nome_do_proprietario=session.get('nome_proprietario'),
                           imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None)

# --- End Servicos Routes ---

# --- Horarios Route ---
from datetime import datetime, timedelta, time # Ensure timedelta and time are imported

def time_from_string(time_str):
    if not time_str:
        return None
    try:
        return datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        return None # Or raise an error to be caught by the route

@app.route('/horarios', methods=['GET', 'POST'])
def horarios():
    if 'empresa_id' not in session:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('root_route'))

    empresa_id = session['empresa_id']
    profissionais_empresa = Profissional.query.filter_by(empresa_id=empresa_id).order_by(Profissional.nome_profissional).all()

    selected_profissional_id = request.form.get('profissional_id') if request.method == 'POST' and 'profissional_id' in request.form and not request.form.get('action') else request.args.get('profissional_id')

    horarios_profissional_dict = {}

    # If a professional is selected (either by POSTing the dropdown or GET param)
    if selected_profissional_id:
        try:
            # Validate selected_profissional_id is an int and belongs to the company
            prof_id_int = int(selected_profissional_id)
            selected_prof = Profissional.query.filter_by(id=prof_id_int, empresa_id=empresa_id).first()
            if not selected_prof:
                flash('Profissional selecionado inválido.', 'danger')
                selected_profissional_id = None # Reset
            else:
                selected_profissional_id = str(prof_id_int) # Keep it as string for consistency in template
                horarios_db = Horario.query.filter_by(profissional_id=selected_prof.id).all()
                for h in horarios_db:
                    horarios_profissional_dict[str(h.dia_semana)] = h
        except ValueError:
            flash('ID de profissional inválido.', 'danger')
            selected_profissional_id = None


    if request.method == 'POST' and request.form.get('action') == 'save_horarios':
        profissional_id_to_save_str = request.form.get('selected_profissional_id_hidden_field')

        if not profissional_id_to_save_str:
            flash('Nenhum profissional selecionado para salvar horários.', 'warning')
            # Re-render with current context, it will likely show no professional selected
            return render_template('horarios.html',
                                   profissionais=profissionais_empresa,
                                   selected_profissional_id=None,
                                   horarios_profissional=horarios_profissional_dict,
                                   nome_da_loja=session.get('nome_da_loja'),
                                   nome_do_proprietario=session.get('nome_proprietario'),
                                   imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None)

        try:
            profissional_id_to_save = int(profissional_id_to_save_str)
            # Verify this professional belongs to the company again for security
            prof_to_save = Profissional.query.filter_by(id=profissional_id_to_save, empresa_id=empresa_id).first()
            if not prof_to_save:
                flash('Profissional para salvar horários é inválido.', 'danger')
                # Reset selected_profissional_id to force re-selection or clear state
                selected_profissional_id = None
                horarios_profissional_dict.clear()
            else:
                # If validation passed, ensure selected_profissional_id is set to the one we are saving for
                selected_profissional_id = str(prof_to_save.id)

                for i in range(7): # 0=Monday, ..., 6=Sunday
                    dia_semana_val = str(request.form.get(f'dia_semana_{i}')) # Should be '0' through '6'
                    dia_folga = request.form.get(f'dia_folga_{i}') == 'true' # Checkbox value

                    h_inicio_trabalho_str = request.form.get(f'horario_inicio_trabalho_{i}')
                    h_termino_trabalho_str = request.form.get(f'horario_termino_trabalho_{i}')
                    h_inicio_almoco_str = request.form.get(f'horario_inicio_almoco_{i}')
                    h_termino_almoco_str = request.form.get(f'horario_termino_almoco_{i}')
                    pausa_str = request.form.get(f'pausa_entre_atendimentos_{i}')

                    horario_existente = Horario.query.filter_by(profissional_id=prof_to_save.id, dia_semana=int(dia_semana_val)).first()
                    if not horario_existente:
                        horario_existente = Horario(profissional_id=prof_to_save.id, dia_semana=int(dia_semana_val))
                        db.session.add(horario_existente)

                    horario_existente.dia_folga = dia_folga
                    if dia_folga:
                        horario_existente.horario_inicio_trabalho = None
                        horario_existente.horario_termino_trabalho = None
                        horario_existente.horario_inicio_almoco = None
                        horario_existente.horario_termino_almoco = None
                        horario_existente.pausa_entre_atendimentos = None
                    else:
                        # Input validation for times and pause
                        valid_times = True
                        h_inicio_trabalho_obj = time_from_string(h_inicio_trabalho_str)
                        h_termino_trabalho_obj = time_from_string(h_termino_trabalho_str)
                        h_inicio_almoco_obj = time_from_string(h_inicio_almoco_str)
                        h_termino_almoco_obj = time_from_string(h_termino_almoco_str)

                        if not dia_folga: # This inner check for dia_folga is redundant due to outer if/else
                            if not h_inicio_trabalho_obj or not h_termino_trabalho_obj:
                                flash(f'Dia {i+1}: Horário de início e término de trabalho são obrigatórios se não for dia de folga.', 'danger')
                                valid_times = False
                            elif h_inicio_trabalho_obj >= h_termino_trabalho_obj:
                                flash(f'Dia {i+1}: Horário de término do trabalho deve ser após o início.', 'danger')
                                valid_times = False

                            if h_inicio_almoco_obj and not h_termino_almoco_obj:
                                flash(f'Dia {i+1}: Horário de término do almoço é obrigatório se o início do almoço for preenchido.', 'danger')
                                valid_times = False
                            if not h_inicio_almoco_obj and h_termino_almoco_obj:
                                flash(f'Dia {i+1}: Horário de início do almoço é obrigatório se o término do almoço for preenchido.', 'danger')
                                valid_times = False
                            if h_inicio_almoco_obj and h_termino_almoco_obj: # Check if h_inicio_trabalho_obj is not None
                                if not (h_inicio_trabalho_obj and h_termino_trabalho_obj and h_inicio_trabalho_obj <= h_inicio_almoco_obj < h_termino_almoco_obj <= h_termino_trabalho_obj):
                                    flash(f'Dia {i+1}: Horários de almoço devem estar dentro do expediente e o término após o início.', 'danger')
                                    valid_times = False

                        pausa_int = None
                        if pausa_str:
                            if not pausa_str.isdigit() or int(pausa_str) < 0:
                                flash(f'Dia {i+1}: Pausa entre atendimentos deve ser um número inteiro não negativo.', 'danger')
                                valid_times = False
                            else:
                                pausa_int = int(pausa_str)

                        if not valid_times: # If any validation for this day failed
                            db.session.rollback() # Rollback to avoid partial save for this day at least
                            # Re-fetch original data to display
                            horarios_db_orig = Horario.query.filter_by(profissional_id=prof_to_save.id).all()
                            horarios_profissional_dict.clear()
                            for h_orig in horarios_db_orig: horarios_profissional_dict[str(h_orig.dia_semana)] = h_orig
                            return render_template('horarios.html', profissionais=profissionais_empresa, selected_profissional_id=selected_profissional_id, horarios_profissional=horarios_profissional_dict, nome_da_loja=session.get('nome_da_loja'), nome_do_proprietario=session.get('nome_proprietario'), imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None)


                        horario_existente.horario_inicio_trabalho = h_inicio_trabalho_obj
                        horario_existente.horario_termino_trabalho = h_termino_trabalho_obj
                        horario_existente.horario_inicio_almoco = h_inicio_almoco_obj
                        horario_existente.horario_termino_almoco = h_termino_almoco_obj
                        horario_existente.pausa_entre_atendimentos = pausa_int

                try:
                    db.session.commit()
                    flash('Horários salvos com sucesso!', 'success')
                    # Refresh horarios_profissional_dict after saving
                    horarios_db_updated = Horario.query.filter_by(profissional_id=prof_to_save.id).all()
                    horarios_profissional_dict.clear() # Clear before repopulating
                    for h_upd in horarios_db_updated:
                        horarios_profissional_dict[str(h_upd.dia_semana)] = h_upd
                except Exception as e:
                    db.session.rollback()
                    flash(f'Erro ao salvar horários: {str(e)}', 'danger')

        except ValueError: # For int(profissional_id_to_save_str)
            flash('ID do profissional para salvar é inválido.', 'danger')
            selected_profissional_id = None
            horarios_profissional_dict.clear()


    return render_template('horarios.html',
                           profissionais=profissionais_empresa,
                           selected_profissional_id=selected_profissional_id,
                           horarios_profissional=horarios_profissional_dict,
                           nome_da_loja=session.get('nome_da_loja'),
                           nome_do_proprietario=session.get('nome_proprietario'),
                           imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None)

# --- End Horarios Route ---

# --- Clientes Route ---
@app.route('/clientes', methods=['GET'])
def clientes():
    if 'empresa_id' not in session:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('root_route'))

    empresa_id = session['empresa_id']
    lista_clientes = Cliente.query.filter_by(empresa_id=empresa_id).order_by(Cliente.nome_cliente).all()

    return render_template('clientes.html',
                           clientes=lista_clientes,
                           nome_da_loja=session.get('nome_da_loja'),
                           nome_do_proprietario=session.get('nome_proprietario'),
                           imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None)
# --- End Clientes Route ---

# --- Agendamentos Route ---
@app.route('/agendamentos', methods=['GET'])
def agendamentos():
    if 'empresa_id' not in session:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('root_route'))

    empresa_id = session['empresa_id']

    lista_agendamentos = Agendamento.query.filter_by(empresa_id=empresa_id)\
        .options(
            joinedload(Agendamento.servico),
            joinedload(Agendamento.cliente),
            joinedload(Agendamento.profissional)
        )\
        .order_by(Agendamento.data_agendamento, Agendamento.horario_inicio)\
        .all()

    return render_template('agendamentos.html',
                           agendamentos=lista_agendamentos,
                           nome_da_loja=session.get('nome_da_loja'),
                           nome_do_proprietario=session.get('nome_proprietario'),
                           imagem_perfil=url_for('static', filename=f'uploads/profile_pics/{session.get("imagem_perfil")}') if session.get("imagem_perfil") else None)
# --- End Agendamentos Route ---

# --- API Endpoints ---
from functools import wraps
from flask import jsonify
# Ensure timedelta and time are available for API endpoints too (already imported at top for Horarios route)

def empresa_required_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'empresa_id' not in session:
            return jsonify({'error': 'Unauthorized', 'message': 'Empresa não autenticada.'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/servicos', methods=['GET'])
@empresa_required_api
def api_list_servicos():
    empresa_id = session['empresa_id']
    servicos_db = Servico.query.filter_by(empresa_id=empresa_id)\
                              .options(joinedload(Servico.profissionais))\
                              .order_by(Servico.nome_servico).all()

    output = []
    for servico in servicos_db:
        profissionais_data = []
        for prof in servico.profissionais:
            profissionais_data.append({
                'id': prof.id,
                'nome_profissional': prof.nome_profissional
            })
        output.append({
            'id': servico.id,
            'nome_servico': servico.nome_servico,
            'descricao': servico.descricao,
            'duracao': servico.duracao, # in minutes
            'preco': servico.preco,
            'sinal': servico.sinal,
            'porcentagem_sinal': servico.porcentagem_sinal,
            'profissionais': profissionais_data
        })
    return jsonify(output)

@app.route('/api/disponibilidade', methods=['GET'])
@empresa_required_api
def api_get_disponibilidade():
    empresa_id = session['empresa_id']

    profissional_id_str = request.args.get('profissional_id')
    data_str = request.args.get('data') # YYYY-MM-DD
    servico_id_str = request.args.get('servico_id')

    error_messages = []
    if not profissional_id_str: error_messages.append("profissional_id é obrigatório.")
    if not data_str: error_messages.append("data (YYYY-MM-DD) é obrigatória.")
    if not servico_id_str: error_messages.append("servico_id é obrigatório.")

    if error_messages:
        return jsonify({'error': 'Missing required parameters', 'messages': error_messages}), 400

    try:
        profissional_id = int(profissional_id_str)
    except ValueError:
        return jsonify({'error': 'Invalid parameter format', 'message': 'profissional_id deve ser um número inteiro.'}), 400

    try:
        servico_id = int(servico_id_str)
    except ValueError:
        return jsonify({'error': 'Invalid parameter format', 'message': 'servico_id deve ser um número inteiro.'}), 400

    try:
        data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format', 'message': 'data deve estar no formato YYYY-MM-DD.'}), 400

    professional = Profissional.query.filter_by(id=profissional_id, empresa_id=empresa_id).first()
    if not professional:
        return jsonify({'error': 'Not found', 'message': f'Profissional com id {profissional_id} não encontrado ou não pertence à empresa.'}), 404

    servico = Servico.query.filter_by(id=servico_id, empresa_id=empresa_id).first()
    if not servico:
        return jsonify({'error': 'Not found', 'message': f'Serviço com id {servico_id} não encontrado ou não pertence à empresa.'}), 404

    dia_semana = data_obj.weekday() # Monday is 0 and Sunday is 6
    horario_profissional = Horario.query.filter_by(profissional_id=profissional_id, dia_semana=dia_semana).first()

    if not horario_profissional or horario_profissional.dia_folga or not horario_profissional.horario_inicio_trabalho or not horario_profissional.horario_termino_trabalho:
        return jsonify([]) # No working hours or day off

    agendamentos_existentes = Agendamento.query.filter_by(profissional_id=profissional_id, data_agendamento=data_obj).all()

    available_slots = []

    # Slot generation parameters
    slot_step = timedelta(minutes=horario_profissional.pausa_entre_atendimentos if horario_profissional.pausa_entre_atendimentos else 15)
    servico_duracao_delta = timedelta(minutes=servico.duracao)

    current_time = datetime.combine(data_obj, horario_profissional.horario_inicio_trabalho)
    horario_termino_trabalho_dt = datetime.combine(data_obj, horario_profissional.horario_termino_trabalho)

    horario_inicio_almoco_dt = None
    horario_termino_almoco_dt = None
    if horario_profissional.horario_inicio_almoco and horario_profissional.horario_termino_almoco:
        horario_inicio_almoco_dt = datetime.combine(data_obj, horario_profissional.horario_inicio_almoco)
        horario_termino_almoco_dt = datetime.combine(data_obj, horario_profissional.horario_termino_almoco)

    while current_time < horario_termino_trabalho_dt:
        slot_inicio = current_time
        slot_fim = current_time + servico_duracao_delta

        if slot_fim > horario_termino_trabalho_dt:
            break # Slot would end after work hours

        # Check for lunch break
        is_in_lunch = False
        if horario_inicio_almoco_dt and horario_termino_almoco_dt:
            if not (slot_fim <= horario_inicio_almoco_dt or slot_inicio >= horario_termino_almoco_dt):
                is_in_lunch = True

        if is_in_lunch:
            current_time = horario_termino_almoco_dt # Jump to end of lunch for next possible slot
            continue

        # Check for conflicts with existing appointments
        is_conflict = False
        for ag in agendamentos_existentes:
            ag_inicio_dt = datetime.combine(data_obj, ag.horario_inicio)
            ag_fim_dt = datetime.combine(data_obj, ag.horario_fim)
            if not (slot_fim <= ag_inicio_dt or slot_inicio >= ag_fim_dt): # Check for overlap
                is_conflict = True
                break

        if not is_conflict:
            available_slots.append(slot_inicio.strftime('%H:%M'))

        current_time += slot_step

    return jsonify(available_slots)

@app.route('/api/clientes', methods=['POST'])
@empresa_required_api
def api_register_cliente():
    empresa_id = session['empresa_id']
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json(silent=True) # Use silent=True to handle None data manually
    if not data:
        return jsonify({"error": "Invalid JSON", "message": "Corpo da requisição não é um JSON válido."}), 400


    nome_cliente = data.get('nome_cliente')
    telefone = data.get('telefone')

    if not nome_cliente or not isinstance(nome_cliente, str) or \
       not telefone or not isinstance(telefone, str):
        return jsonify({'error': 'Missing or invalid data type', 'message': 'nome_cliente (string) e telefone (string) são obrigatórios.'}), 400

    if len(nome_cliente) > 120: return jsonify({'error': 'Validation error', 'message': 'Nome do cliente excede 120 caracteres.'}), 400
    if len(telefone) > 20: return jsonify({'error': 'Validation error', 'message': 'Telefone excede 20 caracteres.'}), 400
    # Add more specific phone validation if needed, e.g., regex

    # Optional: Validate phone format more strictly if needed

    existing_cliente = Cliente.query.filter_by(empresa_id=empresa_id, telefone=telefone).first()
    if existing_cliente:
        return jsonify({'error': 'Conflict', 'message': 'Cliente com este telefone já cadastrado para esta empresa.'}), 409 # 409 Conflict

    new_cliente = Cliente(
        empresa_id=empresa_id,
        nome_cliente=nome_cliente,
        telefone=telefone
        # valor_gasto will default to 0.0
    )

    try:
        db.session.add(new_cliente)
        db.session.commit()
        # Return the created client data, including its new ID
        return jsonify({
            'id': new_cliente.id,
            'empresa_id': new_cliente.empresa_id,
            'nome_cliente': new_cliente.nome_cliente,
            'telefone': new_cliente.telefone,
            'valor_gasto': new_cliente.valor_gasto
        }), 201 # 201 Created
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Conflict', 'message': 'Erro de integridade. Telefone pode já existir para esta empresa ou outro valor único violado.'}), 409
    except Exception as e:
        db.session.rollback()
        # Log error e
        return jsonify({'error': 'Database error', 'message': f'Erro ao cadastrar cliente: {str(e)}'}), 500

@app.route('/api/clientes/buscar', methods=['GET'])
@empresa_required_api
def api_search_cliente():
    empresa_id = session['empresa_id']
    telefone_query = request.args.get('telefone')

    if not telefone_query or not isinstance(telefone_query, str): # Ensure it's a string
        return jsonify({'error': 'Missing or invalid query parameter', 'message': 'Parâmetro "telefone" (string) é obrigatório.'}), 400

    if len(telefone_query) > 20 : # Align with model or desired max length for a phone number query
        return jsonify({'error': 'Invalid parameter value', 'message': 'Parâmetro "telefone" excede o comprimento máximo.'}), 400


    cliente_found = Cliente.query.filter_by(empresa_id=empresa_id, telefone=telefone_query).first()

    if cliente_found:
        return jsonify({
            'id': cliente_found.id,
            'empresa_id': cliente_found.empresa_id,
            'nome_cliente': cliente_found.nome_cliente,
            'telefone': cliente_found.telefone,
            'valor_gasto': cliente_found.valor_gasto
        }), 200
    else:
        return jsonify({'message': 'Cliente não encontrado.'}), 404 # Not Found

@app.route('/api/agendamentos', methods=['POST'])
@empresa_required_api
def api_create_agendamento():
    empresa_id = session['empresa_id']
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON", "message": "Corpo da requisição não é um JSON válido."}), 400

    servico_id = data.get('servico_id')
    cliente_id = data.get('cliente_id')
    profissional_id = data.get('profissional_id')
    data_agendamento_str = data.get('data_agendamento') # YYYY-MM-DD
    horario_inicio_str = data.get('horario_inicio') # HH:MM

    error_messages = []
    if not servico_id: error_messages.append("servico_id é obrigatório.")
    if not cliente_id: error_messages.append("cliente_id é obrigatório.")
    if not profissional_id: error_messages.append("profissional_id é obrigatório.")
    if not data_agendamento_str: error_messages.append("data_agendamento é obrigatória.")
    if not horario_inicio_str: error_messages.append("horario_inicio é obrigatório.")

    if error_messages:
        return jsonify({'error': 'Missing data', 'messages': error_messages}), 400

    try:
        servico_id = int(servico_id)
        cliente_id = int(cliente_id)
        profissional_id = int(profissional_id)
    except (ValueError, TypeError): # TypeError if None was passed to int()
        return jsonify({'error': 'Invalid ID format', 'message': 'IDs de serviço, cliente e profissional devem ser números inteiros.'}), 400

    try:
        data_agendamento_obj = datetime.strptime(data_agendamento_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format', 'message': 'data_agendamento deve estar no formato YYYY-MM-DD.'}), 400

    horario_inicio_obj = time_from_string(horario_inicio_str)
    if not horario_inicio_obj:
        return jsonify({'error': 'Invalid time format', 'message': 'horario_inicio deve estar no formato HH:MM.'}), 400

    # Validate entities belong to the company
    servico = Servico.query.filter_by(id=servico_id, empresa_id=empresa_id).first()
    if not servico: return jsonify({'error': 'Not found', 'message': 'Serviço não encontrado ou não pertence à empresa.'}), 404

    cliente = Cliente.query.filter_by(id=cliente_id, empresa_id=empresa_id).first()
    if not cliente: return jsonify({'error': 'Not found', 'message': 'Cliente não encontrado ou não pertence à empresa.'}), 404

    profissional = Profissional.query.filter_by(id=profissional_id, empresa_id=empresa_id).first()
    if not profissional: return jsonify({'error': 'Not found', 'message': 'Profissional não encontrado ou não pertence à empresa.'}), 404

    # Availability Check (Simplified - reusing logic from /api/disponibilidade would be better DRY, but for now, a direct check)
    # This check should be robust and identical to the one in /api/disponibilidade for consistency.
    # For brevity, this is a simplified conceptual check. A real implementation should factor out the availability logic.

    dia_semana = data_agendamento_obj.weekday()
    horario_profissional = Horario.query.filter_by(profissional_id=profissional_id, dia_semana=dia_semana).first()

    if not horario_profissional or horario_profissional.dia_folga or not horario_profissional.horario_inicio_trabalho or not horario_profissional.horario_termino_trabalho:
        return jsonify({'error': 'Unavailable', 'message': 'Profissional não trabalha neste dia.'}), 409 # Conflict

    horario_inicio_dt = datetime.combine(data_agendamento_obj, horario_inicio_obj)
    horario_fim_dt = horario_inicio_dt + timedelta(minutes=servico.duracao)

    if horario_inicio_dt.time() < horario_profissional.horario_inicio_trabalho or horario_fim_dt.time() > horario_profissional.horario_termino_trabalho:
         return jsonify({'error': 'Unavailable', 'message': 'Horário fora do expediente de trabalho.'}), 409

    if horario_profissional.horario_inicio_almoco and horario_profissional.horario_termino_almoco:
        almoco_inicio_dt = datetime.combine(data_agendamento_obj, horario_profissional.horario_inicio_almoco)
        almoco_fim_dt = datetime.combine(data_agendamento_obj, horario_profissional.horario_termino_almoco)
        if not (horario_fim_dt <= almoco_inicio_dt or horario_inicio_dt >= almoco_fim_dt):
            return jsonify({'error': 'Unavailable', 'message': 'Horário coincide com o almoço.'}), 409

    agendamentos_conflitantes = Agendamento.query.filter(
        Agendamento.profissional_id == profissional_id,
        Agendamento.data_agendamento == data_agendamento_obj,
        Agendamento.horario_inicio < horario_fim_dt.time(),
        Agendamento.horario_fim > horario_inicio_obj
    ).all()

    if agendamentos_conflitantes:
        return jsonify({'error': 'Unavailable', 'message': 'Horário já reservado ou conflitante.'}), 409

    # Create Agendamento
    novo_agendamento = Agendamento(
        empresa_id=empresa_id,
        servico_id=servico_id,
        cliente_id=cliente_id,
        profissional_id=profissional_id,
        data_agendamento=data_agendamento_obj,
        horario_inicio=horario_inicio_obj,
        horario_fim=horario_fim_dt.time(),
        valor_total=servico.preco, # Assuming full price, adjust if deposit/signal logic is part of API
        status='Confirmado' # Or 'Pendente' depending on workflow
    )

    try:
        db.session.add(novo_agendamento)
        db.session.commit()
        return jsonify({
            'id': novo_agendamento.id,
            'servico_id': novo_agendamento.servico_id,
            'cliente_id': novo_agendamento.cliente_id,
            'profissional_id': novo_agendamento.profissional_id,
            'data_agendamento': novo_agendamento.data_agendamento.isoformat(),
            'horario_inicio': novo_agendamento.horario_inicio.strftime('%H:%M'),
            'horario_fim': novo_agendamento.horario_fim.strftime('%H:%M'),
            'valor_total': novo_agendamento.valor_total,
            'status': novo_agendamento.status
        }), 201
    except IntegrityError: # Should not happen if availability check is robust, but good for other constraints
        db.session.rollback()
        return jsonify({'error': 'Conflict', 'message': 'Erro de integridade de dados ao salvar agendamento.'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Database error', 'message': f'Erro ao criar agendamento: {str(e)}'}), 500

@app.route('/api/agendamentos/<int:agendamento_id>/status', methods=['PUT'])
@empresa_required_api
def api_update_agendamento_status(agendamento_id):
    empresa_id = session['empresa_id']
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON", "message": "Corpo da requisição não é um JSON válido."}), 400

    new_status = data.get('status')
    if not new_status or not isinstance(new_status, str):
        return jsonify({'error': 'Missing or invalid data type', 'message': 'Campo "status" (string) é obrigatório.'}), 400

    allowed_statuses = ['Pendente', 'Confirmado', 'Cancelado', 'Concluído', 'Não Compareceu']
    if new_status not in allowed_statuses:
        return jsonify({'error': 'Invalid status value', 'message': f'Status inválido. Permitidos: {", ".join(allowed_statuses)}'}), 400

    agendamento = Agendamento.query.filter_by(id=agendamento_id, empresa_id=empresa_id).first()

    if not agendamento:
        return jsonify({'error': 'Not found', 'message': 'Agendamento não encontrado ou não pertence à empresa.'}), 404

    agendamento.status = new_status
    try:
        db.session.commit()
        return jsonify({
            'id': agendamento.id,
            'status': agendamento.status,
            'message': 'Status do agendamento atualizado com sucesso.'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Database error', 'message': f'Erro ao atualizar status: {str(e)}'}), 500

@app.route('/api/agendamentos/data', methods=['GET'])
@empresa_required_api
def api_list_agendamentos_por_data():
    empresa_id = session['empresa_id']
    data_query_str = request.args.get('data') # YYYY-MM-DD

    if not data_query_str or not isinstance(data_query_str, str):
        return jsonify({'error': 'Missing or invalid query parameter', 'message': 'Parâmetro "data" (string, YYYY-MM-DD) é obrigatório.'}), 400

    try:
        data_query_obj = datetime.strptime(data_query_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format', 'message': 'Formato da data deve ser YYYY-MM-DD.'}), 400

    agendamentos_db = Agendamento.query.filter_by(empresa_id=empresa_id, data_agendamento=data_query_obj)\
        .options(
            joinedload(Agendamento.servico),
            joinedload(Agendamento.cliente),
            joinedload(Agendamento.profissional)
        )\
        .order_by(Agendamento.horario_inicio)\
        .all()

    output = []
    for ag in agendamentos_db:
        output.append({
            'id': ag.id,
            'servico': {'id': ag.servico.id, 'nome_servico': ag.servico.nome_servico} if ag.servico else None,
            'cliente': {'id': ag.cliente.id, 'nome_cliente': ag.cliente.nome_cliente, 'telefone': ag.cliente.telefone} if ag.cliente else None,
            'profissional': {'id': ag.profissional.id, 'nome_profissional': ag.profissional.nome_profissional} if ag.profissional else None,
            'data_agendamento': ag.data_agendamento.isoformat(),
            'horario_inicio': ag.horario_inicio.strftime('%H:%M'),
            'horario_fim': ag.horario_fim.strftime('%H:%M'),
            'valor_total': ag.valor_total,
            'status': ag.status
        })
    return jsonify(output)

# --- End API Endpoints ---

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Create sql tables for our data models if they don't already exist
    app.run(debug=True, port=5000)

[end of midas_pdv/app.py]
