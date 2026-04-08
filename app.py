import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from supabase import create_client, Client

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.after_request
def add_header(response):
    # Enable caching for static content and JSON results to save bandwidth
    if request.method == 'GET':
        response.cache_control.max_age = 3600 # Cache for 1 hour
    return response

@app.errorhandler(500)
def handle_500(e):
    return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

@app.errorhandler(404)
def handle_404(e):
    if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
        return jsonify({"error": "Not Found"}), 404
    return e

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or "sqlite:///local_fallback.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from sqlalchemy import text

# Lookup Table Models
class FamilyName(db.Model):
    __tablename__ = 'family_names'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name}

class PrayerGroup(db.Model):
    __tablename__ = 'prayer_groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name}

class HeroImage(db.Model):
    __tablename__ = 'hero_images'
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "image_url": self.image_url, "order": self.order}

class HigherHead(db.Model):
    __tablename__ = 'higher_heads'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    photo_url = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "photo_url": self.photo_url,
            "order": self.order
        }

class ParishProperty(db.Model):
    __tablename__ = 'parish_properties'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    photo_url = db.Column(db.Text, nullable=True)
    location_url = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "photo_url": self.photo_url,
            "location_url": self.location_url
        }

class CommitteeMember(db.Model):
    __tablename__ = 'committee_members'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    position = db.Column(db.String(150), nullable=False)
    mobile = db.Column(db.String(50), nullable=True)
    photo_url = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "mobile": self.mobile,
            "photo_url": self.photo_url,
            "order": self.order
        }

class ChurchMember(db.Model):
    __tablename__ = 'church_members'
    id = db.Column(db.BigInteger, primary_key=True)
    family_name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=True)
    is_head = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    role = db.Column(db.String(50), default='Member')
    prayer_group = db.Column(db.String(100), nullable=True)
    is_deceased = db.Column(db.Boolean, default=False)
    head_id = db.Column(db.BigInteger, db.ForeignKey('church_members.id'), nullable=True)
    photo_url = db.Column(db.Text, nullable=True)
    family_photo_url = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "family_name": self.family_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_head": self.is_head,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "prayer_group": self.prayer_group,
            "is_deceased": self.is_deceased,
            "head_id": self.head_id,
            "photo_url": self.photo_url,
            "family_photo_url": self.family_photo_url,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

with app.app_context():
    db.create_all()
    try:
        db.session.execute(text("ALTER TABLE church_members ADD COLUMN prayer_group VARCHAR(100);"))
        db.session.commit()
    except:
        db.session.rollback()
        
    try:
        db.session.execute(text("ALTER TABLE church_members ADD COLUMN is_deceased BOOLEAN DEFAULT FALSE;"))
        db.session.commit()
    except:
        db.session.rollback()

    try:
        db.session.execute(text("ALTER TABLE church_members ADD COLUMN head_id BIGINT;"))
        db.session.commit()
    except:
        db.session.rollback()

    try:
        db.session.execute(text("ALTER TABLE church_members ADD COLUMN photo_url TEXT;"))
        db.session.commit()
    except:
        db.session.rollback()

    try:
        db.session.execute(text("ALTER TABLE church_members ADD COLUMN family_photo_url TEXT;"))
        db.session.commit()
    except:
        db.session.rollback()

    try:
        db.session.execute(text("ALTER TABLE hero_images ADD COLUMN \"order\" INTEGER DEFAULT 0;"))
        db.session.commit()
    except:
        db.session.rollback()

    # Create higher_heads table if it doesn't exist
    with app.app_context():
        db.create_all()
        try:
            db.session.execute(text("SELECT 1 FROM higher_heads LIMIT 1"))
        except Exception as e:
            db.session.rollback()
            # Use SERIAL for PostgreSQL, AUTOINCREMENT for SQLite
            is_postgres = "postgresql" in str(app.config['SQLALCHEMY_DATABASE_URI'])
            id_col = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
            db.session.execute(text(f"CREATE TABLE IF NOT EXISTS higher_heads (id {id_col}, name VARCHAR(150) NOT NULL, title VARCHAR(150) NOT NULL, photo_url TEXT, \"order\" INTEGER DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"))
            db.session.commit()
            
        try:
            db.session.execute(text("SELECT 1 FROM parish_properties LIMIT 1"))
        except Exception:
            db.session.rollback()
            is_postgres = "postgresql" in str(app.config['SQLALCHEMY_DATABASE_URI'])
            id_col = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
            db.session.execute(text(f"CREATE TABLE IF NOT EXISTS parish_properties (id {id_col}, name VARCHAR(150) NOT NULL, photo_url TEXT, location_url TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"))
            db.session.commit()
            
        try:
            db.session.execute(text("SELECT 1 FROM committee_members LIMIT 1"))
        except Exception:
            db.session.rollback()
            is_postgres = "postgresql" in str(app.config['SQLALCHEMY_DATABASE_URI'])
            id_col = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
            db.session.execute(text(f"CREATE TABLE IF NOT EXISTS committee_members (id {id_col}, name VARCHAR(150) NOT NULL, position VARCHAR(150) NOT NULL, mobile VARCHAR(50), photo_url TEXT, \"order\" INTEGER DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"))
            db.session.commit()

base_dir = os.path.dirname(os.path.abspath(__file__))
frontends_dir = os.path.abspath(os.path.join(base_dir, 'frontends'))

@app.route('/', methods=['GET'])
def index():
    return send_from_directory(os.path.join(frontends_dir, 'user_portal'), 'index.html')

@app.route('/logo.png')
def serve_logo():
    return send_from_directory(base_dir, 'Screenshot 2026-04-06 175257.png')

@app.route('/favicon.ico')
def serve_favicon():
    return send_from_directory(base_dir, 'Screenshot 2026-04-06 175257.png')

@app.route('/admin', methods=['GET'])
def admin():
    return send_from_directory(os.path.join(frontends_dir, 'admin_portal'), 'index.html')

@app.route('/directory', methods=['GET'])
def directory():
    return send_from_directory(os.path.join(frontends_dir, 'user_portal'), 'directory.html')

@app.route('/members', methods=['GET'])
def get_members():
    try:
        members = ChurchMember.query.filter_by(is_deceased=False).order_by(
            ChurchMember.family_name.asc(),
            ChurchMember.is_head.desc(),
            ChurchMember.first_name.asc()
        ).all()
        return jsonify([m.to_dict() for m in members]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/members/deceased', methods=['GET'])
def get_deceased_members():
    try:
        members = ChurchMember.query.filter_by(is_deceased=True).order_by(
            ChurchMember.family_name.asc(),
            ChurchMember.first_name.asc()
        ).all()
        return jsonify([m.to_dict() for m in members]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/upload', methods=['POST'])
def upload_file():
    if not supabase:
        return jsonify({"error": "Supabase not configured"}), 500
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Optional folder param: 'members' or 'families'
    folder = request.form.get('folder', 'members')
    
    try:
        filename = secure_filename(file.filename)
        path_on_supabase = f"{folder}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        
        file_data = file.read()
        res = supabase.storage.from_("story-frames").upload(
            path=path_on_supabase,
            file=file_data,
            file_options={"content-type": file.content_type}
        )
        url = supabase.storage.from_("story-frames").get_public_url(path_on_supabase)
        return jsonify({"url": url}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/members', methods=['POST'])
def add_member():
    try:
        data = request.json
        new_member = ChurchMember(
            family_name=data.get('family_name'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            is_head=data.get('is_head', False),
            email=data.get('email'),
            phone=data.get('phone'),
            role=data.get('role', 'Member'),
            prayer_group=data.get('prayer_group'),
            is_deceased=data.get('is_deceased', False),
            head_id=data.get('head_id'),
            photo_url=data.get('photo_url'),
            family_photo_url=data.get('family_photo_url')
        )
        db.session.add(new_member)
        db.session.commit()
        return jsonify(new_member.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/members/<int:id>', methods=['PUT', 'DELETE'])
def manage_member(id):
    try:
        member = ChurchMember.query.get(id)
        if not member:
            return jsonify({"error": "Member not found"}), 404

        if request.method == 'PUT':
            data = request.json
            if 'family_name' in data: member.family_name = data['family_name']
            if 'first_name' in data: member.first_name = data['first_name']
            if 'last_name' in data: member.last_name = data['last_name']
            if 'is_head' in data: member.is_head = data['is_head']
            if 'email' in data: member.email = data['email']
            if 'phone' in data: member.phone = data['phone']
            if 'role' in data: member.role = data['role']
            if 'prayer_group' in data: member.prayer_group = data['prayer_group']
            if 'is_deceased' in data: member.is_deceased = data['is_deceased']
            if 'head_id' in data: member.head_id = data['head_id']
            if 'photo_url' in data: member.photo_url = data['photo_url']
            if 'family_photo_url' in data: member.family_photo_url = data['family_photo_url']
            db.session.commit()
            return jsonify(member.to_dict()), 200

        elif request.method == 'DELETE':
            db.session.delete(member)
            db.session.commit()
            return jsonify({"message": "Deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# Form Options Endpoints
@app.route('/family-names', methods=['GET', 'POST'])
def manage_family_names():
    try:
        if request.method == 'GET':
            names = FamilyName.query.order_by(FamilyName.name).all()
            return jsonify([n.to_dict() for n in names]), 200
        
        name_str = request.json.get('name')
        new_name = FamilyName(name=name_str)
        db.session.add(new_name)
        db.session.commit()
        return jsonify(new_name.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/family-names/<int:id>', methods=['DELETE'])
def delete_family_name(id):
    obj = FamilyName.query.get(id)
    if obj:
        db.session.delete(obj)
        db.session.commit()
    return jsonify({"success": True}), 200

@app.route('/prayer-groups', methods=['GET', 'POST'])
def manage_prayer_groups():
    try:
        if request.method == 'GET':
            groups = PrayerGroup.query.order_by(PrayerGroup.name).all()
            return jsonify([g.to_dict() for g in groups]), 200
        
        name_str = request.json.get('name')
        new_group = PrayerGroup(name=name_str)
        db.session.add(new_group)
        db.session.commit()
        return jsonify(new_group.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/prayer-groups/<int:id>', methods=['DELETE'])
def delete_prayer_group(id):
    obj = PrayerGroup.query.get(id)
    if obj:
        db.session.delete(obj)
        db.session.commit()
    return jsonify({"success": True}), 200

# Hero Images Endpoints
@app.route('/hero-images', methods=['GET', 'POST'])
def manage_hero_images():
    try:
        if request.method == 'GET':
            images = HeroImage.query.order_by(HeroImage.order.asc(), HeroImage.id.asc()).all()
            return jsonify([img.to_dict() for img in images]), 200
        
        url = request.json.get('image_url')
        order = request.json.get('order', 0)
        if not url:
            return jsonify({"error": "No image URL provided"}), 400
            
        new_img = HeroImage(image_url=url, order=order)
        db.session.add(new_img)
        db.session.commit()
        return jsonify(new_img.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/hero-images/<int:id>', methods=['DELETE'])
def delete_hero_image(id):
    try:
        img = HeroImage.query.get(id)
        if img:
            db.session.delete(img)
            db.session.commit()
            return jsonify({"message": "Hero image deleted"}), 200
        return jsonify({"error": "Image not found"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400



# Higher Heads Endpoints
@app.route('/higher-heads', methods=['GET', 'POST'])
def manage_higher_heads():
    try:
        if request.method == 'GET':
            heads = HigherHead.query.order_by(HigherHead.order.asc()).all()
            return jsonify([h.to_dict() for h in heads]), 200
        
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        new_head = HigherHead(
            name=data.get('name'),
            title=data.get('title'),
            photo_url=data.get('photo_url'),
            order=data.get('order', 0)
        )
        db.session.add(new_head)
        db.session.commit()
        return jsonify(new_head.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/higher-heads/<int:id>', methods=['DELETE'])
def delete_higher_head(id):
    try:
        head = db.session.get(HigherHead, id)
        if head:
            db.session.delete(head)
            db.session.commit()
            return jsonify({"message": "Head deleted"}), 200
        return jsonify({"error": "Head not found"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# Parish Properties Endpoints
@app.route('/parish-properties', methods=['GET', 'POST'])
def manage_parish_properties():
    try:
        if request.method == 'GET':
            props = ParishProperty.query.order_by(ParishProperty.id.asc()).all()
            return jsonify([p.to_dict() for p in props]), 200
        
        data = request.json
        new_prop = ParishProperty(
            name=data.get('name'),
            photo_url=data.get('photo_url'),
            location_url=data.get('location_url')
        )
        db.session.add(new_prop)
        db.session.commit()
        return jsonify(new_prop.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/parish-properties/<int:id>', methods=['DELETE'])
def delete_parish_property(id):
    try:
        prop = db.session.get(ParishProperty, id)
        if prop:
            db.session.delete(prop)
            db.session.commit()
            return jsonify({"message": "Property deleted"}), 200
        return jsonify({"error": "Property not found"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# Committee Members Endpoints
@app.route('/committee-members', methods=['GET', 'POST'])
def manage_committee_members():
    try:
        if request.method == 'GET':
            mems = CommitteeMember.query.order_by(CommitteeMember.order.asc()).all()
            return jsonify([m.to_dict() for m in mems]), 200
        
        data = request.json
        new_mem = CommitteeMember(
            name=data.get('name'),
            position=data.get('position'),
            mobile=data.get('mobile'),
            photo_url=data.get('photo_url'),
            order=data.get('order', 0)
        )
        db.session.add(new_mem)
        db.session.commit()
        return jsonify(new_mem.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/committee-members/<int:id>', methods=['DELETE'])
def delete_committee_member(id):
    try:
        mem = db.session.get(CommitteeMember, id)
        if mem:
            db.session.delete(mem)
            db.session.commit()
            return jsonify({"message": "Member deleted"}), 200
        return jsonify({"error": "Member not found"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    # Use host 0.0.0.0 and port from environment for Render deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
