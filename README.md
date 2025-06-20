# 🧭 Kadıköy Turistik Rota Planlayıcı

**Kadıköy Turistik Rota Planlayıcı**,  kullanıcının seçtiği otelden başlayarak görmek istediği turistik noktaları geri oteline dönecek şekilde en verimli sırayla gezmesi için geliştirilmiş bir web uygulamasıdır. Uygulama, gerçek yol ağları üzerinde en kısa toplam mesafeyi sağlayacak optimum gezi rotasını, ziyaret sırasını ve toplam rota uzunluğunu hesaplar.

### 🚀 Özellikler

Kullanıcılar uygulama üzerinden:
- Başlangıç noktası olarak konakladıkları oteli seçebilir,  
- Gezmek istedikleri turistik noktaları (müze, park, galeri vb.) belirleyebilir,  
- Ulaşım türü olarak **yürüyüş** ya da **araç** modunu seçebilir,  
- Rota oluştur butonu ile seçilen noktalara uğrayarak **başladığı otele geri dönecek şekilde** en kısa rotayı oluşturabilir,  
- Oluşturulan rota için toplam mesafeyi ve ziyaret sıralamasını görüntüleyebilir.

Ek olarak:
- Yan paneldeki kategorize edilmiş turistik yerler harita üzerinde incelenebilir,  
- Her bir yer üzerine tıklandığında konumu harita üzerinde otomatik olarak görüntülenir,  
- "Seçimi Temizle" butonu ile geçici olarak işaretlenen yerler sıfırlanabilir,  
- Rota oluşturulduktan sonra "Rotayı Temizle" butonu ile rota ve bilgiler temizlenebilir.


## 🛠️ Teknik Detaylar

### 📍 Coğrafi Veri İşleme
- **GeoPandas** Mekansal verilerin okunması ve yönetilmesi işlemlerinde kullanıldı. 
- **OSMnx**: OpenStreetMap'ten Kadıköy ilçesine ait turistik noktalar ve otel noktaları ile yol ağı verisi çekildi. Otel ve turistik noktalar, gerçek yol ağı üzerindeki en yakın düğümlere eşlendi.
- **NetworkX**: Gerçek yol ağı üzerinden en kısa mesafeler hesaplanarak, gerçek Rota (Yol) çizgisi Oluşturuldu. Ayrıca toplam rota Uzunluğu hesaplandı.
- **Folium** & **streamlit-folium**: Harita üzerinde rota ve yer işaretlerinin görsel olarak gösterimi sağlandı.

### 🚏 Rota Optimizasyonu
- **OR-Tools**: Kullanıcının belirlediği noktalar için **Gezgin Satıcı Problemi (TSP)** çözülerek **başlangıç noktasına geri dönen** en kısa rota hesaplandı.

### 🗃️ Veritabanı Süreci
- **SQLAlchemy** ile osmnx ile çekilmiş veriler PostgreSQL/PostGIS veritabanına aktarıldı.  
- **PostgreSQL/PostGIS** ile veriler düzenlendi ve temizlendi.  
- **psycopg2** aracılığıyla güncellenen veriler Python ortamına yeniden aktarıldı.

### 🖥️ Web Uygulama Arayüzü
- **Streamlit** ile geliştirilmiştir.
- Uygulama **Streamlit Cloud** platformunda dağıtılmıştır.


## 📂 Veri Kaynakları ve Hazırlık

- Kadıköy ilçesine ait otel ve turistik noktaların koordinatları OSMnx kütüphanesi kullanılarak OpenStreetMap üzerinden çekilmiştir.
- Veriler SQLAlchemy aracılığıyla PostgreSQL/PostGIS veritabanına aktarılmış, burada mekansal düzenlemeler yapılmış ve  psycopg2 aracılığıyla düzenlenen veriler Python ortamına yeniden aktarılmıştır.
- [veri_toplama.ipynb](./veri_toplama.ipynb)


## 🚀 Uygulamaya Erişim 

🔗 **Uygulama Linki**  
Uygulamayı çevrimiçi olarak Streamlit Cloud üzerinden deneyimlemek için:  
👉 [https://kadikoyturistikrotaolusturucu.streamlit.app/](https://kadikoyturistikrotaolusturucu.streamlit.app/)

💻 **Uygulama Kodu**  
[kadikoy_turistik_rota_olusturucu.py](./kadikoy_turistik_rota_olusturucu.py)


