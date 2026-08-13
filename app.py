
from flask import Flask, render_template, request
import sqlite3
import networkx as nx

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('altinyuva.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS urunler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isim TEXT NOT NULL,
            kategori TEXT NOT NULL,
            materyal TEXT,
            fiyat REAL,
            gorsel_isim TEXT
        )
    ''')
    
    c.execute('SELECT COUNT(*) FROM urunler')
    if c.fetchone()[0] == 0:
        ornek_urunler = [
            
            ('Pırlanta Baget Yüzük', 'Pırlanta', '18 Ayar Beyaz Altın', 15000.0, 'https://picsum.photos/seed/altinyuva1/600/800'),
            ('Pırlanta Tektaş Yüzük', 'Pırlanta', '18 Ayar Beyaz Altın', 25000.0, 'https://picsum.photos/seed/altinyuva2/600/800'),
            ('Zümrüt Damla Kolye', 'Özel Tasarım', '14 Ayar Altın', 12500.0, 'https://picsum.photos/seed/altinyuva3/600/800'),
            ('Safir Pırlanta Kolye', 'Özel Tasarım', '18 Ayar Beyaz Altın', 18000.0, 'https://picsum.photos/seed/altinyuva4/600/800'),
            ('Su Yolu Bileklik', 'Altın Koleksiyonu', '22 Ayar Altın', 22000.0, 'https://picsum.photos/seed/altinyuva5/600/800'),
            ('22 Ayar Burma Bilezik', 'Altın Koleksiyonu', '22 Ayar Altın', 35000.0, 'https://picsum.photos/seed/altinyuva6/600/800'),
            ('Klasik Alyans', 'Evlilik & Nişan', '14 Ayar Altın', 8000.0, 'https://picsum.photos/seed/altinyuva7/600/800'),
            ('Rose Altın Çift Alyans', 'Evlilik & Nişan', 'Rose Altın', 14000.0, 'https://picsum.photos/seed/altinyuva8/600/800'),
            ('İncili Altın Küpe', 'Altın Koleksiyonu', '14 Ayar Altın', 6500.0, 'https://picsum.photos/seed/altinyuva9/600/800'),
            ('Pırlanta Halka Küpe', 'Pırlanta', '18 Ayar Beyaz Altın', 19000.0, 'https://picsum.photos/seed/altinyuva10/600/800')
        
        ]
        c.executemany('INSERT INTO urunler (isim, kategori, materyal, fiyat, gorsel_isim) VALUES (?, ?, ?, ?, ?)', ornek_urunler)
    
    conn.commit()
    conn.close()

# Ağ Analizi: Ürün Grafını Oluşturma
def olustur_oneri_grafi():
    conn = sqlite3.connect('altinyuva.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM urunler')
    urunler = c.fetchall()
    conn.close()

    G = nx.Graph()

    # Düğümleri (Nodes) grafiğe ekle
    for urun in urunler:
        G.add_node(urun['id'], data=dict(urun))

    # Ağırlıklı kenarları (Edges) oluştur
    urun_listesi = list(G.nodes(data=True))
    for i in range(len(urun_listesi)):
        for j in range(i + 1, len(urun_listesi)):
            id1, veri1 = urun_listesi[i]
            id2, veri2 = urun_listesi[j]
            
            benzerlik_skoru = 0.0
            
            # Kategori eşleşmesi: Yüksek Ağırlık (0.8)
            if veri1['data']['kategori'] == veri2['data']['kategori']:
                benzerlik_skoru += 0.8
            
            # Materyal eşleşmesi: Düşük Ağırlık (0.2)
            if veri1['data']['materyal'] == veri2['data']['materyal']:
                benzerlik_skoru += 0.2
                
            # Bağlantı varsa kenar olarak ekle
            if benzerlik_skoru > 0:
                G.add_edge(id1, id2, weight=benzerlik_skoru)
                
    return G, urunler

@app.route('/')
def anasayfa():
    return render_template('index.html')

@app.route('/koleksiyon')
def koleksiyon():
    G, tum_urunler = olustur_oneri_grafi()
    
    # Kullanıcı ana sayfadan bir arama yaptıysa onu yakalıyoruz
    arama_sorgusu = request.args.get('q', '').lower()
    
    if arama_sorgusu:
        # Sadece isminde veya kategorisinde aranan kelime geçenleri listele
        urunler = [u for u in tum_urunler if arama_sorgusu in u['isim'].lower() or arama_sorgusu in u['kategori'].lower()]
    else:
        urunler = tum_urunler
        
    return render_template('koleksiyon.html', urunler=urunler, arama_sorgusu=arama_sorgusu)

# Ürün Detay ve Tavsiye Rotası
@app.route('/urun/<int:urun_id>')
def urun_detay(urun_id):
    G, tum_urunler = olustur_oneri_grafi()
    
    # Seçilen ürünü bul
    secilen_urun = G.nodes[urun_id]['data']
    
    # Seçilen ürünün komşularını benzerlik (weight) skoruna göre sırala
    onerilenler = []
    if urun_id in G:
        komsular = G[urun_id]
        sirali_komsular = sorted(komsular.items(), key=lambda x: x[1]['weight'], reverse=True)
        
        # En benzer 3 ürünü al
        for komsu_id, bag in sirali_komsular[:3]:
            onerilenler.append(G.nodes[komsu_id]['data'])

    return render_template('urun_detay.html', urun=secilen_urun, onerilenler=onerilenler)
# Gizli Yönetici Paneli Rotası
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    mesaj = ""
    if request.method == 'POST':
        # Formdan gelen verileri al
        sifre = request.form.get('sifre')
        
        # Basit şifre koruması (Dükkan sahibi için)
        if sifre == "Altinyuva2026":
            isim = request.form.get('isim')
            kategori = request.form.get('kategori')
            materyal = request.form.get('materyal')
            fiyat = request.form.get('fiyat')
            gorsel_isim = request.form.get('gorsel_isim')
            
            # Veritabanına yeni ürünü ekle
            try:
                conn = sqlite3.connect('altinyuva.db')
                c = conn.cursor()
                c.execute('INSERT INTO urunler (isim, kategori, materyal, fiyat, gorsel_isim) VALUES (?, ?, ?, ?, ?)', 
                          (isim, kategori, materyal, float(fiyat), gorsel_isim))
                conn.commit()
                conn.close()
                mesaj = "Başarılı: Yeni ürün vitrine eklendi!"
            except Exception as e:
                mesaj = f"Bir hata oluştu: {str(e)}"
        else:
            mesaj = "Hata: Yanlış yönetici şifresi!"
            
    return render_template('admin.html', mesaj=mesaj)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)