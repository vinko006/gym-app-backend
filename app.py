from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from models import db, Clan, Trener, Paket, Uplata, Dolazak
from datetime import datetime, date, time
from sqlalchemy import func

app = Flask(__name__)
app.json.ensure_ascii = False
CORS(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/teretana'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def index():
    return "Gym Hub API radi!"

# --- TRENERI ---
@app.route('/treneri', methods=['GET'])
def dohvati_trenere():
    stranica = request.args.get('page', default=1, type=int)
    po_stranici = request.args.get('per_page', default=10, type=int)
    pretraga = request.args.get('search', default='', type=str).strip()

    tip_filtera = request.args.get('tip_filtera', default='Sve', type=str)

    upit = Trener.query

    if pretraga:
        if tip_filtera == 'Ime i prezime':
            upit = upit.filter(
                (Trener.ime.ilike(f"%{pretraga}%")) |
                (Trener.prezime.ilike(f"%{pretraga}%"))
            )
        elif tip_filtera == 'Specijalnost':
            upit = upit.filter(
                Trener.specijalnost.ilike(f"%{pretraga}%")
            )
        else:
            upit = upit.filter(
                (Trener.ime.ilike(f"%{pretraga}%")) |
                (Trener.prezime.ilike(f"%{pretraga}%")) |
                (Trener.specijalnost.ilike(f"%{pretraga}%"))
            )

    pagnacija = upit.paginate(page=stranica, per_page=po_stranici, error_out=False)

    lista_trenera = [{
        'id': t.id,
        'ime': t.ime,
        'prezime': t.prezime,
        'specijalnost': t.specijalnost
    } for t in pagnacija.items]

    return jsonify({
        "treneri": lista_trenera,
        "ukupnoStranica": pagnacija.pages
    })

@app.route('/treneri', methods=['POST'])
def dodaj_trenera():
    podaci = request.get_json()
    novi = Trener(
        ime=podaci['ime'],
        prezime=podaci['prezime'],
        specijalnost=podaci.get('specijalnost')
    )
    db.session.add(novi)
    db.session.commit()
    return jsonify({"poruka": "Trener dodan!"})

@app.route('/treneri/<int:id>', methods=['PUT'])
def uredi_trenera(id):
    trener = Trener.query.get(id)
    if not trener:
        return jsonify({"poruka": "Trener nije pronađen"}), 404

    podaci = request.get_json()
    trener.ime = podaci.get('ime', trener.ime)
    trener.prezime = podaci.get('prezime', trener.prezime)
    trener.specijalnost = podaci.get('specijalnost', trener.specijalnost)
    db.session.commit()
    return jsonify({"poruka": "Ažurirano"})

@app.route('/treneri/<int:id>', methods=['DELETE'])
def obrisi_trenera(id):
    trener = Trener.query.get(id)
    if not trener:
        return jsonify({"poruka": "Trener nije pronađen"}), 404

    try:
        db.session.delete(trener)
        db.session.commit()
        return jsonify({"poruka": "Obrisano"})
    except:
        return jsonify({"error": "Trener ima aktivne članove!"}), 400

# --- CLANOVI ---
@app.route('/clanovi', methods=['GET'])
def dohvati_clanove():
    stranica = request.args.get('page', default=1, type=int)
    po_stranici = request.args.get('per_page', default=10, type=int)
    pretraga = request.args.get('search', default='', type=str).strip()

    tip_filtera = request.args.get('tip_filtera', default='Sve', type=str)

    upit = db.session.query(Clan).outerjoin(Trener).outerjoin(Paket)

    if pretraga:
        if tip_filtera == 'Ime člana':
            upit = upit.filter(
                (Clan.ime.ilike(f"%{pretraga}%")) |
                (Clan.prezime.ilike(f"%{pretraga}%"))
            )
        elif tip_filtera == 'Trener':
            upit = upit.filter(
                (Trener.ime.ilike(f"%{pretraga}%")) |
                (Trener.prezime.ilike(f"%{pretraga}%"))
            )
        elif tip_filtera == 'Paket':
            upit = upit.filter(
                Paket.naziv.ilike(f"%{pretraga}%")
            )
        else:
            upit = upit.filter(
                (Clan.ime.ilike(f"%{pretraga}%")) |
                (Clan.prezime.ilike(f"%{pretraga}%")) |
                (Trener.ime.ilike(f"%{pretraga}%")) |
                (Trener.prezime.ilike(f"%{pretraga}%")) |
                (Paket.naziv.ilike(f"%{pretraga}%"))
            )

    pagnacija = upit.paginate(page=stranica, per_page=po_stranici, error_out=False)

    lista_clanova = []
    for c in pagnacija.items:
        trener_info = f"{c.trener.ime} {c.trener.prezime}" if c.trener else "Nema trenera"
        naziv_paketa = c.paket.naziv if c.paket else "Bez paketa"

        lista_clanova.append({
            'id': c.id,
            'ime': c.ime,
            'prezime': c.prezime,
            'email': c.email,
            'paket': naziv_paketa,
            'trener': trener_info,
            'paket_id': c.paket_id,
            'trener_id': c.trener_id
        })

    return jsonify({
        "clanovi": lista_clanova,
        "ukupnoStranica": pagnacija.pages
    })


@app.route('/clanovi', methods=['POST'])
def dodaj_clana():
    podaci = request.get_json()
    novi = Clan(
        ime=podaci['ime'],
        prezime=podaci['prezime'],
        email=podaci.get('email'),
        paket_id=podaci.get('paket_id'),
        trener_id=podaci.get('trener_id')
    )
    db.session.add(novi)
    db.session.commit()

    #Stvara novu uplatu unutar baze podataka
    if novi.paket_id:
        automatska_uplata = Uplata(
            clan_id=novi.id,
            paket_id=novi.paket_id,
            datum_uplate=datetime.now()
        )
        db.session.add(automatska_uplata)
        db.session.commit()

    return jsonify({"poruka": "Član je uspješno dodan!"})


@app.route('/clanovi/<int:id>', methods=['PUT'])
def uredi_clana(id):
    clan = Clan.query.get(id)
    if not clan:
        return jsonify({"message": "Član nije pronađen"}), 404
    podaci = request.get_json()
    clan.ime = podaci.get('ime', clan.ime)
    clan.prezime = podaci.get('prezime', clan.prezime)
    clan.email = podaci.get('email', clan.email)
    clan.trener_id = podaci.get('trener_id', clan.trener_id)
    clan.paket_id = podaci.get('paket_id', clan.paket_id)
    db.session.commit()
    return jsonify({"message": "Podaci uspješno ažurirani"})

@app.route('/clanovi/<int:id>', methods=['DELETE'])
def obrisi_clana(id):
    clan = Clan.query.get(id)
    db.session.delete(clan)
    db.session.commit()
    return jsonify({"message": "Obrisano"})

# --- DOLASCI ---
@app.route('/dolasci', methods=['GET'])
def dohvati_dolasce():
    try:
        svi_dolasci = db.session.query(Dolazak, Clan).join(Clan).all()
        return jsonify([{
            'id': d.id,
            'datum_vrijeme': d.datum_vrijeme.strftime('%Y-%m-%d %H:%M:%S'),
            'napomena': d.napomena,
            'clan_ime': f"{c.ime} {c.prezime}"
        } for d, c in svi_dolasci]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/dolasci', methods=['POST'])
def dodaj_dolazak():
    podaci = request.get_json()
    if not podaci or 'clan_id' not in podaci:
        return jsonify({"error": "Nedostaje ID člana"}), 400
    novi_dolazak = Dolazak(
        clan_id=podaci['clan_id'],
        napomena=podaci.get('napomena', ''),
        datum_vrijeme=datetime.utcnow()
    )
    db.session.add(novi_dolazak)
    db.session.commit()
    return jsonify({"message": "Dolazak uspješno evidentiran"}), 201


@app.route('/dolasci/<int:id>', methods=['DELETE'])
def obrisi_dolazak(id):
    try:
        zapis = Dolazak.query.get(id)
        if not zapis:
            return jsonify({"error": "Zapis nije pronađen"}), 404

        db.session.delete(zapis)
        db.session.commit()
        return jsonify({"message": "Zapis uspješno obrisan"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/dolasci/<int:id>', methods=['PUT'])
def dodavanje_dolazaka(id):
    try:
        zapis = Dolazak.query.get(id)

        if not zapis:
            return jsonify({"error": "Zapis nije pronađen"}), 404

        podaci = request.get_json()

        if 'datum_vrijeme' in podaci:
            zapis.datum_vrijeme = podaci['datum_vrijeme']
        if 'napomena' in podaci:
            zapis.napomena = podaci['napomena']
        if 'clan_id' in podaci:
            zapis.clan_id = podaci['clan_id']

        db.session.commit()
        return jsonify({"message": "Zapis uspješno ažuriran", "id": zapis.id}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# --- PAKETI ---
@app.route('/paketi', methods=['GET'])
def dohvati_pakete():
    svi = Paket.query.all()
    return jsonify([{'id': p.id, 'naziv': p.naziv, 'cijena': p.cijena} for p in svi])


# --- UPLATE ---
@app.route('/uplate', methods=['GET'])
def dohvati_uplate():
    try:
        rezultati = db.session.query(Uplata, Clan, Paket)\
            .select_from(Uplata)\
            .join(Clan, Uplata.clan_id == Clan.id)\
            .join(Paket, Uplata.paket_id == Paket.id)\
            .all()

        lista = []
        for uplata, clan, paket in rezultati:
            lista.append({
                'id': uplata.id,
                'clan_ime': f"{clan.ime} {clan.prezime}",
                'paket_naziv': paket.naziv,
                'iznos': paket.cijena,
                'datum': uplata.datum_uplate.strftime('%Y-%m-%d %H:%M:%S') if uplata.datum_uplate else "-"
            })
        return jsonify(lista), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/uplate', methods=['POST'])
def dodaj_uplatu():
    podaci = request.get_json()
    nova = Uplata(
        clan_id=podaci['clan_id'],
        paket_id=podaci['paket_id'],
        datum_uplate=datetime.now()
    )
    db.session.add(nova)
    db.session.commit()
    return jsonify({"message": "Uplata uspješna"}), 201

@app.route('/uplate/<int:id>', methods=['DELETE'])
def obrisi_uplatu(id):
    u = Uplata.query.get(id)
    db.session.delete(u)
    db.session.commit()
    return jsonify({"message": "Obrisano"})


#--- Statistika ----
@app.route('/dashboard-statistika', methods=['GET'])
def dashboard_statistika():
    try:
        broj_clanova = Clan.query.count()
        broj_trenera = Trener.query.count()

        zarada = db.session.query(func.sum(Paket.cijena)) \
                     .select_from(Uplata) \
                     .join(Paket, Uplata.paket_id == Paket.id) \
                     .scalar() or 0

        danas_pocetak = datetime.combine(date.today(), time.min)
        danas_kraj = datetime.combine(date.today(), time.max)

        broj_dolazaka_danas = Dolazak.query.filter(
            Dolazak.datum_vrijeme >= danas_pocetak,
            Dolazak.datum_vrijeme <= danas_kraj
        ).count()

        return jsonify({
            "broj_clanova": broj_clanova,
            "broj_trenera": broj_trenera,
            "ukupna_zarada": float(zarada),
            "dolasci_danas": broj_dolazaka_danas
        }), 200

    except Exception as e:
        print(f"Greška u dashboardu: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)