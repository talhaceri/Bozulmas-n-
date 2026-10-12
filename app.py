from datetime import datetime, date
import streamlit as st
import qrcode
from io import BytesIO
import cv2
import numpy as np

# Sayfa Yapılandırması
st.set_page_config(page_title="SKT & QR Takip Sistemi", page_icon="📦", layout="centered")

# Oturum Durumu Tanımlamaları
if "dolaplar" not in st.session_state:
    st.session_state.dolaplar = {
        "Mutfak Buzdolabı": [],
        "Kiler Dolabı": []
    }

if "aktif_dolap" not in st.session_state:
    st.session_state.aktif_dolap = None

if "son_uretilen_qr" not in st.session_state:
    st.session_state.son_uretilen_qr = None
    st.session_state.son_uretilen_ad = ""

# QR Kod Üretme Yardımcı Fonksiyonu
def qr_kod_uret(veri_metni):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=2,
    )
    qr.add_data(veri_metni)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

# QR Kod Okuma Yardımcı Fonksiyonu (OpenCV ile)
def qr_kod_oku(image_bytes):
    try:
        file_bytes = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(img)
        return data
    except Exception:
        return None

# Sidebar Menü
st.sidebar.title("🧭 Menü")
sayfa = st.sidebar.radio("Gitmek İstediğiniz Sayfa:", [
    "🚪 Dolaplarım", 
    "➕ Ürün Ekle", 
    "📷 QR Tara", 
    "🖨️ QR Oluştur & Paylaş", 
    "🚨 7 Gün Kalanlar (Kritik)"
])

# ---------------------------------------------------------
# 1. SAYFA: DOLAPLARIM VE DETAYLARI
# ---------------------------------------------------------
if sayfa == "🚪 Dolaplarım":
    st.title("🚪 Dolap Yönetimi")
    st.markdown("---")
    
    if st.session_state.aktif_dolap is None:
        st.subheader("Mevcut Dolaplarınız")
        
        if not st.session_state.dolaplar:
            st.info("Henüz hiç dolap eklemediniz.")
        else:
            for dolap_adi in list(st.session_state.dolaplar.keys()):
                col_b1, col_b2 = st.columns([4, 1])
                with col_b1:
                    if st.button(f"🚪 {dolap_adi} ({len(st.session_state.dolaplar[dolap_adi])} Ürün)", key=f"btn_detay_{dolap_adi}", use_container_width=True):
                        st.session_state.aktif_dolap = dolap_adi
                        st.rerun()
                with col_b2:
                    if st.button("🗑️ Sil", key=f"sil_dolap_{dolap_adi}"):
                        del st.session_state.dolaplar[dolap_adi]
                        st.rerun()

        st.markdown("---")
        st.subheader("➕ Yeni Dolap Ekle")
        with st.form("yeni_dolap_formu", clear_on_submit=True):
            yeni_dolap_adi = st.text_input("Dolap Adı (Örn: Derin Dondurucu)")
            dolap_ekle_btn = st.form_submit_button("Dolabı Oluştur")
            
            if dolap_ekle_btn:
                yeni_dolap_adi = yeni_dolap_adi.strip()
                if yeni_dolap_adi and yeni_dolap_adi not in st.session_state.dolaplar:
                    st.session_state.dolaplar[yeni_dolap_adi] = []
                    st.success(f"'{yeni_dolap_adi}' başarıyla eklendi!")
                    st.rerun()
                elif yeni_dolap_adi in st.session_state.dolaplar:
                    st.warning("Bu isimde bir dolap zaten var.")
                else:
                    st.warning("Lütfen geçerli bir dolap adı girin.")
    else:
        secilen = st.session_state.aktif_dolap
        if st.button("⬅️ Tüm Dolaplara Geri Dön"):
            st.session_state.aktif_dolap = None
            st.rerun()
            
        st.markdown(f"## 📦 {secilen} İçeriği")
        st.markdown("---")
        
        urunler = st.session_state.dolaplar[secilen]
        if not urunler:
            st.info("Bu dolapta henüz kayıtlı ürün bulunmuyor.")
        else:
            for index, urun in enumerate(urunler):
                kalan_gun = (urun["skt"] - date.today()).days
                
                if kalan_gun < 0:
                    durum = "🔴 SÜRESİ GEÇTİ!"
                elif kalan_gun <= 7:
                    durum = f"🟠 Kritik ({kalan_gun} gün kaldı)"
                else:
                    durum = f"🟢 Taze ({kalan_gun} gün kaldı)"
                    
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.write(f"**{urun['ad']}**")
                        st.caption(f"Etiket: {urun['etiket']} | Durum: {durum}")
                    with col2:
                        st.write(f"SKT: {urun['skt']}")
                        qr_metni = f"Ürün: {urun['ad']}\nSKT: {urun['skt']}\nKategori: {urun['etiket']}"
                        qr_bytes = qr_kod_uret(qr_metni)
                        with st.popover("📱 QR Kod"):
                            st.image(qr_bytes, width=150)
                            st.download_button("📥 QR İndir / Paylaş", data=qr_bytes, file_name=f"{urun['ad']}_qr.png", mime="image/png", key=f"dl_{secilen}_{index}")
                    with col3:
                        if st.button("🗑️ Sil", key=f"urun_sil_{secilen}_{index}"):
                            st.session_state.dolaplar[secilen].pop(index)
                            st.rerun()
                st.markdown("---")

# ---------------------------------------------------------
# 2. SAYFA: ÜRÜN EKLE
# ---------------------------------------------------------
elif sayfa == "➕ Ürün Ekle":
    st.title("➕ Ürün Ekleme Sayfası")
    st.markdown("---")
    
    if not st.session_state.dolaplar:
        st.warning("Önce 'Dolaplarım' sayfasından en az bir dolap oluşturmalısınız!")
    else:
        hedef_dolap = st.selectbox("Hangi Dolaba Eklenecek?", list(st.session_state.dolaplar.keys()))
        
        with st.form("urun_ekleme_formu", clear_on_submit=True):
            urun_adi = st.text_input("Ürün Adı (Örn: Süt)")
            etiket = st.text_input("Etiket / Kategori (Örn: Süt Ürünleri)")
            skt = st.date_input("Son Kullanma Tarihi", min_value=date.today())
            kaydet_btn = st.form_submit_button("Ürünü Kaydet")
            
            if kaydet_btn:
                urun_adi = urun_adi.strip()
                if urun_adi:
                    yeni_urun = {
                        "ad": urun_adi,
                        "etiket": etiket.strip() if etiket.strip() else "Genel",
                        "skt": skt
                    }
                    st.session_state.dolaplar[hedef_dolap].append(yeni_urun)
                    st.success(f"'{urun_adi}' başarıyla '{hedef_dolap}' dolabına eklendi! Form sıfırlandı.")
                else:
                    st.warning("Lütfen ürün adını boş bırakmayın.")

# ---------------------------------------------------------
# 3. SAYFA: QR TARA (KAMERA VEYA DOSYA)
# ---------------------------------------------------------
elif sayfa == "📷 QR Tara":
    st.title("📷 QR Kod Tarama ve Okutma")
    st.markdown("Telefon veya bilgisayar kameranızı kullanarak ya da görsel yükleyerek QR kod taratın.")
    st.markdown("---")
    
    if not st.session_state.dolaplar:
        st.warning("Önce bir dolap oluşturmalısınız!")
    else:
        hedef_dolap_qr = st.selectbox("Taranan Ürün Hangi Dolaba Eklenecek?", list(st.session_state.dolaplar.keys()))
        
        secenek = st.radio("Tarama Yöntemi:", ["Kamera ile Canlı Çek", "Cihazdan QR Görseli Yükle"])
        
        taranan_veri = None
        
        if secenek == "Kamera ile Canlı Çek":
            kamera_foto = st.camera_input("Kameraya QR Kodu Gösterin")
            if kamera_foto is not None:
                taranan_veri = qr_kod_oku(kamera_foto.read())
        else:
            yuklenen_dosya = st.file_uploader("QR Kod Görseli Seçin", type=["png", "jpg", "jpeg"])
            if yuklenen_dosya is not None:
                st.image(yuklenen_dosya, width=200)
                taranan_veri = qr_kod_oku(yuklenen_dosya.read())
                
        if taranan_veri:
            st.success(f"**QR Kod Başarıyla Okundu!**\n\nİçerik: `{taranan_veri}`")
            
            with st.form("qr_sonuc_formu", clear_on_submit=True):
                p_ad = st.text_input("Ürün Adı", value=taranan_veri.split("\n")[0])
                p_skt = st.date_input("Son Kullanma Tarihi", min_value=date.today())
                p_kaydet = st.form_submit_button("Dolaba Kaydet")
                
                if p_kaydet:
                    st.session_state.dolaplar[hedef_dolap_qr].append({
                        "ad": p_ad,
                        "etiket": "QR Tarandı",
                        "skt": p_skt
                    })
                    st.success(f"'{p_ad}' başarıyla dolaba eklendi!")

# ---------------------------------------------------------
# 4. SAYFA: QR OLUŞTUR & PAYLAŞ
# ---------------------------------------------------------
elif sayfa == "🖨️ QR Oluştur & Paylaş":
    st.title("🖨️ Özel QR Kod Oluştur ve Paylaş")
    st.markdown("İstediğiniz ürün adı ve son kullanma tarihini girerek anında yeni bir QR kod oluşturun ve cihazınıza indirin/paylaşın.")
    st.markdown("---")
    
    with st.form("ozel_qr_formu"):
         olustur_ad = st.text_input("Ürün Adı (Örn: Kaşar Peyniri)")
         olustur_skt = st.date_input("Son Kullanma Tarihi", min_value=date.today())
         olustur_btn = st.form_submit_button("QR Kod Oluştur")
         
         if olustur_btn:
             if olustur_ad:
                 metin = f"Ürün: {olustur_ad}\nSKT: {olustur_skt}\nKategori: Özel Üretim"
                 st.session_state.son_uretilen_qr = qr_kod_uret(metin)
                 st.session_state.son_uretilen_ad = olustur_ad
                 st.success(f"'{olustur_ad}' için QR kod başarıyla oluşturuldu!")
             else:
                 st.warning("Lütfen ürün adını boş bırakmayın.")

    # İndirme ve paylaşma butonu formun dışına taşındı
    if st.session_state.son_uretilen_qr is not None:
        st.markdown("---")
        st.image(st.session_state.son_uretilen_qr, caption=f"{st.session_state.son_uretilen_ad} QR Kodu", width=200)
        st.download_button(
            label="📥 QR Kodu İndir / Paylaş",
            data=st.session_state.son_uretilen_qr,
            file_name=f"{st.session_state.son_uretilen_ad}_qr.png",
            mime="image/png"
        )

# ---------------------------------------------------------
# 5. SAYFA: 7 GÜN KALANLAR (KRİTİK)
# ---------------------------------------------------------
elif sayfa == "🚨 7 Gün Kalanlar (Kritik)":
    st.title("🚨 Kritik Ürünler (7 Gün ve Daha Az Kalanlar)")
    st.markdown("Tüm dolaplarınızda son kullanma tarihine 7 gün veya daha az kalan ürünler aşağıda listelenmiştir.")
    st.markdown("---")
    
    kritik_varmi = False
    for dolap_adi, urunler in st.session_state.dolaplar.items():
        for index, urun in enumerate(urunler):
            kalan_gun = (urun["skt"] - date.today()).days
            if kalan_gun <= 7:
                kritik_varmi = True
                durum_metni = f"🔴 Süresi geçmiş!" if kalan_gun < 0 else f"🟠 Kritik: {kalan_gun} gün kaldı"
                
                with st.container():
                    col_k1, col_k2, col_k3 = st.columns([3, 2, 1])
                    with col_k1:
                        st.write(f"**{urun['ad']}**")
                        st.caption(f"Dolap: {dolap_adi} | {durum_metni}")
                    with col_k2:
                        st.write(f"SKT: {urun['skt']}")
                    with col_k3:
                        if st.button("🗑️ Tüket/Sil", key=f"kritik_sil_{dolap_adi}_{index}"):
                            st.session_state.dolaplar[dolap_adi].pop(index)
                            st.rerun()
                st.markdown("---")
                
    if not kritik_varmi:
        st.success("Harika! Süresi yaklaşan kritik bir ürününüz bulunmuyor. 🎉")