from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret_key_for_flash_messages"

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/scan')
def scan():
    return render_template('index.html')

# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://e62_db_user:fTF5XkXkGkjzPstAeF7QshFauMMDiQo5@dpg-d10vb2ali9vc7387et60-a/e62_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de SQLAlchemy
db = SQLAlchemy(app)

# Modèle pour la table Produits
class Produit(db.Model):
    __tablename__ = 'Produits'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    prix = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    fournisseur = db.Column(db.String(255), nullable=False, default='Inconnu')
    unite = db.Column(db.String(255), nullable=False, default='pièce')

    def __repr__(self):
        return f"<Produit {self.nom}>"

# Modèle pour l'historique des modifications
class Historique(db.Model):
    __tablename__ = 'Historique'
    id = db.Column(db.Integer, primary_key=True)
    produit_id = db.Column(db.Integer, nullable=False)
    nom = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # "Ajout" ou "Retrait"
    quantite = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Historique {self.nom} - {self.type}>"

# Route pour le tableau de bord
@app.route('/dashboard')
def dashboard():
    try:
        historique = Historique.query.order_by(Historique.date.desc()).limit(5).all()
        return render_template('dashboard.html', historique=historique)
    except Exception as e:
        flash(f"⚠️ Erreur lors du chargement du tableau de bord : {e}", "error")
        return render_template('dashboard.html')

# Route pour gérer les produits (ajouter, modifier)
@app.route('/gestion_produits', methods=['GET', 'POST'])
def gestion_produits():
    try:
        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'ajouter':
                nom = request.form.get('nom')
                description = request.form.get('description')
                prix = request.form.get('prix')
                stock = request.form.get('stock')
                fournisseur = request.form.get('fournisseur')
                unite = request.form.get('unite')

                if not nom or not description or not prix or not stock or not fournisseur or not unite:
                    flash("⚠️ Tous les champs sont obligatoires pour ajouter un produit.", "error")
                else:
                    produit = Produit(
                        nom=nom,
                        description=description,
                        prix=float(prix),
                        stock=int(stock),
                        fournisseur=fournisseur,
                        unite=unite
                    )
                    db.session.add(produit)
                    db.session.commit()

                    historique = Historique(
                        produit_id=produit.id,
                        nom=nom,
                        type="Ajout",
                        quantite=int(stock)
                    )
                    db.session.add(historique)
                    db.session.commit()

                    flash(f"✅ Produit '{nom}' ajouté avec succès !", "success")

            elif action == 'modifier':
                produit_id = int(request.form.get('produit_id'))
                increment = int(request.form.get('increment'))
                operation = request.form.get('operation')

                if operation == 'remove':
                    increment = -abs(increment)
                else:
                    increment = abs(increment)

                produit = Produit.query.get(produit_id)
                if produit:
                    produit.stock += increment
                    db.session.commit()

                    type_operation = "Ajout" if increment > 0 else "Retrait"

                    historique = Historique(
                        produit_id=produit.id,
                        nom=produit.nom,
                        type=type_operation,
                        quantite=abs(increment)
                    )
                    db.session.add(historique)
                    db.session.commit()

                    flash(f"✅ Stock mis à jour pour '{produit.nom}' : {produit.stock} {produit.unite}.", "success")
                else:
                    flash("⚠️ Produit non trouvé.", "error")

        produits = Produit.query.all()
        return render_template('gestion_produits.html', produits=produits)
    except Exception as e:
        flash(f"⚠️ Erreur : {e}", "error")
        return redirect(url_for('gestion_produits'))

@app.route('/historique')
def historique():
    try:
        historique = Historique.query.order_by(Historique.date.desc()).all()
        return render_template('historique.html', historique=historique)
    except Exception as e:
        flash(f"⚠️ Erreur lors de l'accès à l'historique : {e}", "error")
        return redirect(url_for('dashboard'))

import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
