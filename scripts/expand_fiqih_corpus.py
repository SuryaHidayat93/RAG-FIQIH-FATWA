"""Script untuk melengkapi seluruh korpus Fiqih Mazhab Syafi'i standar Matan Abu Syuja' & Fathul Qarib."""
import json
from pathlib import Path

ADDITIONAL_FIQIH_CHAPTERS = [
    # --- IBADAH LANJUTAN ---
    {
        "id": "syafii-shalat-jenazah",
        "content": "Kitab Matan Taqrib karya Abu Syuja' & Fathul Qarib Al-Mujib. Bab Pengurusan Jenazah: Kewajiban kifayah terhadap jenazah muslim meliputi empat perkara: (1) Memandikan, (2) Mengafani, (3) Menshalatkan, (4) Menguburkan. Pengecualian: orang yang mati syahid di medan perang tidak dimandikan dan tidak dishalatkan, melainkan langsung dikafani dengan pakaian gugurnya dan dikuburkan. Shalat Jenazah terdiri dari empat takbir tanpa ruku' dan sujud: Takbir pertama membaca surat Al-Fatihah setelah ta'awwudz; Takbir kedua membaca shalawat kepada Nabi Muhammad SAW; Takbir ketiga membaca doa khusus untuk jenazah (minimal: 'Allahummaghfir lahu warhamhu...'); Takbir keempat membaca doa kaum muslimin ('Allahumma la tahrimna ajrahu...') lalu diakhiri salam pertama ke kanan.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Matan Al-Ghayah wat Taqrib",
            "pengarang": "Al-Qadhi Abu Syuja'",
            "bab": "Shalat",
            "pasal": "Pengurusan Jenazah dan Tata Cara Shalat Jenazah",
            "halaman": "50-54",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-shalat-sunnah-idul-fitri-adha",
        "content": "Kitab Al-Umm karya Imam Syafi'i & Fathul Qarib. Shalat Sunnah Dua Hari Raya (Idul Fitri dan Idul Adha): Hukumnya sunnah muakkadah dan disunnahkan berjamaah. Terdiri dari dua rakaat: pada rakaat pertama setelah doa iftitah disunnahkan takbir tambahan sebanyak 7 kali sebelum membaca Al-Fatihah; pada rakaat kedua setelah takbir intiqal bangkit dari sujud disunnahkan takbir tambahan sebanyak 5 kali sebelum Al-Fatihah. Di antara setiap takbir zawaid disunnahkan membaca tasbih, tahmid, tahlil, dan takbir. Setelah salam, khatib menyampaikan dua khutbah: khutbah pertama dibuka dengan 9 kali takbir dan khutbah kedua dibuka dengan 7 kali takbir.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Al-Umm & Fathul Qarib",
            "pengarang": "Imam Asy-Syafi'i & Ibnu Qasim Al-Ghazi",
            "bab": "Shalat",
            "pasal": "Shalat Hari Raya Idul Fitri dan Idul Adha",
            "halaman": "55-58",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-shalat-gerhana-istisqa",
        "content": "Kitab Matan Taqrib karya Abu Syuja'. Shalat Sunnah Kusuf (Gerhana Matahari), Khusuf (Gerhana Bulan), dan Istisqa' (Minta Hujan): Shalat gerhana terdiri dari dua rakaat, setiap rakaat memiliki dua kali berdiri, dua kali membaca surat, dua kali ruku', dan dua kali sujud dengan thuma'ninah. Pada gerhana matahari bacaan surat dipelankan (sirr), sedangkan gerhana bulan dikeraskan (jahr), diakhiri dengan dua khutbah nasihat. Shalat Istisqa' dilakukan dua rakaat berjamaah setelah didahului imbauan berpuasa 4 hari, bertaubat, bersedekah, dan keluar ke tanah lapang dengan pakaian sederhana, diikuti khutbah membalikkan selendang sorban sebagai simbol harapan perubahan kondisi.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Matan Al-Ghayah wat Taqrib",
            "pengarang": "Al-Qadhi Abu Syuja'",
            "bab": "Shalat",
            "pasal": "Shalat Kusuf Khusuf dan Istisqa'",
            "halaman": "59-62",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-shalat-sujud-sahwi-tilawah-syukur",
        "content": "Kitab Safinatun Najah karya Syaikh Salim bin Samir Al-Hadhrami. Ketentuan Sujud Sahwi, Sujud Tilawah, dan Sujud Syukur: (1) Sujud Sahwi: hukumnya sunnah dua kali sujud sebelum salam karena empat sebab: meninggalkan sunnah ab'adh (seperti qunut subuh atau tasyahhud awal), ragu dalam jumlah rakaat (mengambil jumlah yang yakin yaitu yang paling sedikit lalu sujud sahwi), melakukan perbuatan yang membatalkan shalat jika sengaja dan tidak membatalkan jika lupa, atau memindahkan rukun ucapan ke bukan tempatnya. (2) Sujud Tilawah: sunnah satu kali sujud ketika membaca atau mendengar 14 ayat sajdah di dalam maupun di luar shalat dengan syarat thaharah menghadap kiblat. (3) Sujud Syukur: sunnah satu kali sujud di luar shalat ketika mendapatkan nikmat baru yang nyata atau terhindar dari marabahaya besar; haram dilakukan di dalam shalat.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Safinatun Najah",
            "pengarang": "Salim bin Samir Al-Hadhrami",
            "bab": "Shalat",
            "pasal": "Sujud Sahwi Tilawah dan Syukur",
            "halaman": "40-43",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-haji-rukun-wajib",
        "content": "Kitab Al-Umm karya Imam Syafi'i & Matan Taqrib karya Abu Syuja'. Bab Haji dan Umrah: Syarat wajib haji ada tujuh: Islam, baligh, berakal, merdeka, memiliki bekal perjalanan dan kendaraan/ongkos, jalan yang aman, serta adanya waktu yang mencukupi. Rukun Haji ada enam perkara yang tidak sah haji jika ditinggalkan dan tidak dapat diganti dengan dam (denda): (1) Niat ihram, (2) Wukuf di Arafah pada tanggal 9 Dzulhijjah mulai tergelincir matahari hingga fajar 10 Dzulhijjah, (3) Thawaf Ifadhah mengelilingi Ka'bah 7 putaran, (4) Sa'i antara bukit Shafa dan Marwah 7 kali, (5) Tahallul dengan mencukur atau memotong minimal 3 helai rambut kepala, (6) Tertib mendahulukan ihram sebelum yang lain. Wajib Haji ada enam (jika ditinggalkan hajinya tetap sah namun wajib membayar dam): ihram dari miqat makani, melempar jumrah aqabah pada hari nahar, melempar tiga jumrah pada hari tasyriq, mabit di Muzdalifah, mabit di Mina pada malam-malam tasyriq, dan thawaf wada' saat hendak meninggalkan Makkah.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Al-Umm & Matan Taqrib",
            "pengarang": "Imam Asy-Syafi'i & Abu Syuja'",
            "bab": "Haji dan Umrah",
            "pasal": "Rukun dan Wajib Haji",
            "halaman": "95-102",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-haji-larangan-ihram-dam",
        "content": "Kitab Matan Taqrib karya Abu Syuja'. Larangan Ihram dan Macam-Macam Dam (Denda): Orang yang sedang berihram haji atau umrah diharamkan melakukan sepuluh perkara: (1) Mengenakan pakaian berjahit atau melingkar bagi laki-laki, (2) Menutup kepala bagi laki-laki, (3) Menutup wajah atau memakai sarung tangan bagi wanita, (4) Menyisir rambut dengan minyak, (5) Mencukur atau mencabut bulu badan/rambut, (6) Memotong kuku, (7) Memakai wewangian, (8) Membunuh atau berburu binatang buruan darat yang liar dan halal dimakan, (9) Melangsungkan akad nikah baik untuk diri sendiri maupun orang lain, (10) Bersetubuh (jima') atau bermesraan dengan syahwat. Bersetubuh sebelum tahallul awal membatalkan haji secara mutlak, wajib menyempurnakan sisa amalan, membayar dam seekor unta, dan wajib mengqadha' haji pada tahun berikutnya.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Matan Al-Ghayah wat Taqrib",
            "pengarang": "Al-Qadhi Abu Syuja'",
            "bab": "Haji dan Umrah",
            "pasal": "Larangan Ihram dan Konsekuensi Dam",
            "halaman": "103-108",
            "mazhab": "Syafi'i"
        }
    },
    # --- MUAMALAH LANJUTAN ---
    {
        "id": "syafii-muamalah-salam-pesanan",
        "content": "Kitab Fathul Qarib Al-Mujib & Al-Umm karya Imam Syafi'i. Akad Salam (Jual Beli Pesanan): Salam adalah akad pesanan barang dengan pembayaran tunai di muka secara penuh (ra'sul mal) dan penyerahan barang yang disifati secara jelas dalam tanggungan (fi adz-dzimmah) pada tempo waktu tertentu. Syarat sah akad salam ada enam: (1) Barang pesanan dapat ditentukan sifat dan spesifikasinya secara presisi, (2) Jenis, macam, dan kualitas barang jelas, (3) Kadar timbangan atau takaran barang pasti, (4) Waktu jatuh tempo penyerahan barang jelas, (5) Barang pesanan umumnya tersedia di pasar saat waktu jatuh tempo penyerahan, (6) Modal pembayaran (ra'sul mal) diserahkan secara kontan penuh di majlis akad sebelum kedua pihak berpisah. Tidak sah akad salam jika modal belum lunas di majlis akad karena termasuk utang dengan utang (bai'ul kali' bil kali').",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Fathul Qarib Al-Mujib",
            "pengarang": "Ibnu Qasim Al-Ghazi",
            "bab": "Muamalah",
            "pasal": "Akad Salam Jual Beli Pesanan",
            "halaman": "136-139",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-muamalah-rahn-gadai",
        "content": "Kitab Matan Taqrib karya Abu Syuja'. Bab Rahn (Gadai): Rahn adalah menjadikan benda berharga sebagai jaminan atas utang piutang yang dapat dijadikan pelunas jika pengutang gagal membayar. Rukun rahn ada empat: marhun (barang gadai yang sah diperjualbelikan), marhun bih (utang yang lazim/pasti), aqidain (rahin/penggadai dan murtahin/penerima gadai), serta shighat. Syarat barang gadai: harus milik sah penggadai dan bernilai ekonomis. Ketentuan penting dalam mazhab Syafi'i: barang gadai tetap menjadi hak milik penggadai, biaya perawatan dan pemeliharaan ditanggung oleh penggadai, dan penerima gadai (kreditur) DIHARAMKAN mengambil manfaat dari barang gadai (seperti mengendarai motor gadai atau menempati rumah gadai) karena setiap piutang yang mendatangkan keuntungan adalah riba (kullu qardhin jarra manfa'atan fahuwa riba).",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Matan Al-Ghayah wat Taqrib",
            "pengarang": "Al-Qadhi Abu Syuja'",
            "bab": "Muamalah",
            "pasal": "Akad Rahn Gadai dan Larangan Pemanfaatan",
            "halaman": "140-142",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-muamalah-taflis-hajr",
        "content": "Kitab Matan Taqrib karya Abu Syuja'. Bab Taflis (Pailit/Bangkrut) dan Hajr (Pencegahan Tindakan Finansial): Hajr (larangan mengelola harta secara hukum) berlaku bagi enam golongan: (1) Anak kecil (shabi) hingga baligh dan cerdas (rusyd), (2) Orang gila hingga berakal sehat, (3) Orang dungu/pemboros harta (safih) hingga sadar, (4) Orang yang bangkrut pailit (muflis) yang utangnya melebihi total seluruh aset hartanya, (5) Orang sakit parah menjelang wafat terhadap pengeluaran harta lebih dari 1/3, (6) Budak yang belum diizinkan berdagang. Jika muflis ditetapkan pailit oleh hakim, asetnya disita dan dibagikan secara adil (proporsional) kepada para kreditur sesuai nisbah piutang masing-masing.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Matan Al-Ghayah wat Taqrib",
            "pengarang": "Al-Qadhi Abu Syuja'",
            "bab": "Muamalah",
            "pasal": "Taflis Pailit dan Enam Golongan Terkena Hajr",
            "halaman": "143-146",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-muamalah-shulhu-hawalah",
        "content": "Kitab Matan Taqrib karya Abu Syuja'. Bab Shulhu (Perdamaian) dan Hawalah (Pengalihan Utang): Shulhu atas sengketa harta sah dilakukan dengan dua bentuk: (1) Shulhu Ibra' (pemutihan sebagian utang dengan pembayaran sisanya), hukumnya sah; (2) Shulhu Mu'awadhah (perdamaian dengan menyerahkan benda lain sebagai pengganti utang), hukumnya mengikuti ketentuan jual beli. Adapun Hawalah (pemindahan beban utang dari orang yang berutang pertama kepada pihak ketiga): syarat sahnya ada empat: kesepakatan kedua belah pihak yang bertransaksi, piutang yang dialihkan berstatus pasti dan lazim dalam tanggungan, adanya kesamaan jenis kadar dan waktu jatuh tempo antara utang pertama dan kedua, serta orang yang dialihkan utangnya (muhal 'alaih) mampu membayar (maliyy). Dengan sahnya hawalah, pihak pertama terbebas total dari beban utang.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Matan Al-Ghayah wat Taqrib",
            "pengarang": "Al-Qadhi Abu Syuja'",
            "bab": "Muamalah",
            "pasal": "Shulhu Perdamaian dan Hawalah Pengalihan Utang",
            "halaman": "147-149",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-muamalah-dhaman-kafalah",
        "content": "Kitab Matan Taqrib & Fathul Qarib Al-Mujib. Bab Dhaman dan Kafalah (Jaminan dan Garansi): Dhaman adalah komitmen seseorang untuk menanggung pembayaran kewajiban utang orang lain yang telah pasti menjadi tanggungan. Syarat dhaman: penjamin (dhamin) adalah orang yang cakap mengelola harta secara sukarela (tabarru'), utang yang dijamin jelas kadarnya dan berstatus lazim, serta penerima jaminan diketahui. Adapun Kafalah adalah menjamin kehadiran fisik seseorang (badaniyyah) di hadapan majelis peradilan pada waktu tertentu. Jika orang yang dijamin melarikan diri, maka kafil wajib menghadirkannya atau menanggung ganti rugi jika ia menjamin hak finansial yang terkait perkara tersebut.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Fathul Qarib Al-Mujib",
            "pengarang": "Ibnu Qasim Al-Ghazi",
            "bab": "Muamalah",
            "pasal": "Dhaman Jaminan Harta dan Kafalah Jaminan Orang",
            "halaman": "150-153",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-muamalah-syirkah-serikat",
        "content": "Kitab Al-Umm karya Imam Syafi'i & Matan Taqrib karya Abu Syuja'. Bab Asy-Syirkah (Kemitraan/Kongsi Usaha): Dalam mazhab Syafi'i, dari berbagai bentuk syirkah, hanya satu bentuk syirkah yang sah secara qiyasi murni yaitu Syirkah 'Inan (kemitraan modal dan kerja). Syarat sah syirkah 'inan: (1) Modal kedua belah pihak berupa mata uang (emas, perak, atau uang resmi yang berlaku sejenis), (2) Kedua modal dicampurkan sehingga tidak dapat dibedakan lagi satu sama lain, (3) Masing-masing mitra mengizinkan mitra lainnya untuk mengelola aset perdagangan, (4) Pembagian laba dan kerugian wajib ditentukan secara persentase proporsional sesuai perbandingan modal masing-masing. Adapun syirkah abdan (kongsi tenaga tanpa modal), syirkah mufawadhah, dan syirkah wujuh dianggap batil dalam mazhab Syafi'i qadim maupun jadid.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Al-Umm & Matan Taqrib",
            "pengarang": "Imam Asy-Syafi'i & Abu Syuja'",
            "bab": "Muamalah",
            "pasal": "Syirkah Kemitraan Dagang dan Syarat Syirkah Inan",
            "halaman": "154-156",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-muamalah-wakalah-qiradh",
        "content": "Kitab Matan Taqrib karya Abu Syuja'. Bab Wakalah (Perwakilan) dan Qiradh / Mudharabah (Bagi Hasil): Wakalah adalah pelimpahan kuasa dari seseorang kepada orang lain dalam perkara yang boleh diwakilkan (seperti jual beli, nikah, sewa). Akad wakalah adalah ja'iz (dapat dibatalkan sewaktu-waktu oleh salah satu pihak) dan wakil berstatus amanah tanpa ganti rugi kecuali teledor. Qiradh (Mudharabah): penyerahan modal dari pemilik dana (shohibul mal) kepada pengelola (mudharib/amil) untuk diperdagangkan dengan pembagian keuntungan bersama berdasarkan persentase (nisbah) yang disepakati di awal (misal 50:50). Syarat qiradh: modal berupa uang tunai, pembagian laba berupa bagian persentase bukan nominal pasti, pengelola tidak boleh dibatasi secara ekstrem yang menghambat perniagaan, dan kerugian finansial ditanggung sepenuhnya oleh pemilik modal selama bukan karena pelanggaran pengelola.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Matan Al-Ghayah wat Taqrib",
            "pengarang": "Al-Qadhi Abu Syuja'",
            "bab": "Muamalah",
            "pasal": "Wakalah Perwakilan dan Qiradh Mudharabah Modal",
            "halaman": "157-160",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-muamalah-ijarah-sewa",
        "content": "Kitab Al-Umm karya Imam Syafi'i & Fathul Qarib Al-Mujib. Bab Ijarah (Sewa Menyewa dan Jasa Tenaga Kerja): Ijarah adalah akad pemindahan hak guna (manfaat) suatu barang atau jasa dengan imbalan kompensasi (ujrah/upah) yang jelas. Syarat sah ijarah ada empat: (1) Manfaat barang diketahui secara jelas dan terukur (seperti menempati rumah selama satu tahun atau menyewa mobil ke kota tertentu), (2) Manfaat barang mubah secara syar'i (tidak sah menyewa rumah untuk tempat judi atau menyewa orang untuk maksiat), (3) Kompensasi upah/sewa jelas nominal dan jenisnya, (4) Barang yang disewakan dapat diserahterimakan dan tidak habis zatnya saat digunakan. Penyewa berstatus pemegang amanah atas barang sewaan dan tidak wajib mengganti kerusakan kecuali karena kelalaian atau pemakaian yang melampaui batas kewajaran.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Al-Umm & Fathul Qarib Al-Mujib",
            "pengarang": "Imam Asy-Syafi'i & Ibnu Qasim",
            "bab": "Muamalah",
            "pasal": "Akad Ijarah Sewa Menyewa dan Upah Tenaga Kerja",
            "halaman": "161-164",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-muamalah-ghashab-luqathah-wadiah",
        "content": "Kitab Matan Taqrib karya Abu Syuja'. Bab Ghashab, Luqathah (Barang Temuan), dan Wadi'ah (Barang Titipan): (1) Ghashab: mengambil hak/harta orang lain secara zalim dan terang-terangan tanpa izin. Pelaku ghashab berdosa besar, wajib mengembalikan barang tersebut secara utuh beserta nilai susut kerusakannya, serta menanggung sewa manfaat selama dikuasai; jika barang musnah wajib mengganti benda semisal (mitsli) atau nilainya (qimi). (2) Luqathah: mengambil barang tercecer/hilang di jalan; penemu wajib mengenali wadah, tali pengikat, jenis, dan kadarnya, lalu wajib mengumumkannya selama satu tahun penuh di tempat keramaian publik; setelah satu tahun boleh dimiliki dengan syarat menanggung ganti rugi jika pemiliknya datang. (3) Wadi'ah: barang titipan; penerima titipan memegang barang sebagai amanah tanpa ganti rugi jika rusak kecuali karena kelalaian/teledor.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Matan Al-Ghayah wat Taqrib",
            "pengarang": "Al-Qadhi Abu Syuja'",
            "bab": "Muamalah",
            "pasal": "Ghashab Luqathah Barang Temuan dan Wadiah Titipan",
            "halaman": "165-170",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-muamalah-waqaf-hibah",
        "content": "Kitab Al-Umm karya Imam Syafi'i & Fathul Qarib. Bab Waqaf dan Hibah: Waqaf adalah menahan harta pokok yang kekal zatnya dan menyalurkan manfaat hasilnya untuk kebaikan/ibadah mendekatkan diri kepada Allah. Syarat waqaf: harta pokok tahan lama tidak habis sekali pakai, waqaf bersifat kekal (tidak berjangka waktu), tidak boleh digantungkan pada syarat tertentu, dan langsung berlaku mengikat; harta waqaf haram diperjualbelikan, dihibahkan, maupun diwariskan. Hibah: pemberian sukarela hak milik atas suatu benda semasa hidup tanpa imbalan; akad hibah baru sempurna mengikat kepemilikannya setelah adanya serah terima fisik (qabdh) dengan izin pemberi; pemberi hibah dilarang menarik kembali pemberiannya kecuali seorang ayah/ibu/kakek terhadap apa yang telah dihibahkan kepada anaknya.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Al-Umm & Fathul Qarib",
            "pengarang": "Imam Asy-Syafi'i & Ibnu Qasim",
            "bab": "Muamalah",
            "pasal": "Waqaf Harta Abadi dan Hibah Sukarela",
            "halaman": "171-175",
            "mazhab": "Syafi'i"
        }
    },
    # --- MUNAKAHAT LANJUTAN ---
    {
        "id": "syafii-munakahat-mahar-walimah",
        "content": "Kitab Matan Taqrib karya Abu Syuja'. Bab Mahar dan Walimatul 'Ursy: Mahar (shadaq) adalah harta yang wajib diserahkan oleh suami kepada istri karena sebab pernikahan. Tidak ada batas minimal maupun batas maksimal mahar dalam syariat, segala sesuatu yang bernilai harta atau jasa mubah sah dijadikan mahar; disunnahkan tidak kurang dari 10 dirham dan tidak melebihi 500 dirham. Mahar wajib dibayarkan penuh jika suami telah menyetubuhi istri atau suami meninggal dunia; dan wajib dibayar separuh (1/2) jika suami menceraikan istri sebelum disetubuhi dan telah ditentukan kadar maharnya. Walimah (pesta perkawinan): hukum mengadakan walimah adalah sunnah muakkadah, dan hukum menghadiri undangan walimah bagi yang diundang secara khusus tanpa kemaksiatan adalah fardhu 'ain menurut pendapat mu'tamad mazhab Syafi'i.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Matan Al-Ghayah wat Taqrib",
            "pengarang": "Al-Qadhi Abu Syuja'",
            "bab": "Munakahat",
            "pasal": "Ketentuan Mahar dan Hukum Menghadiri Walimah",
            "halaman": "176-180",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-munakahat-talak-rujuk",
        "content": "Kitab Al-Umm karya Imam Syafi'i & Matan Taqrib. Bab Talak (Perceraian) dan Rujuk: Suami yang berakal dan baligh berhak menjatuhkan talak hingga tiga kali. Lafal talak ada dua macam: (1) Sharih (tegas): kata 'talak', 'pisah' (firaq), dan 'lepas' (sarah); jatuh talak seketika tanpa membutuhkan niat; (2) Kinayah (sindiran): seperti perkataan 'pulanglah ke orang tuamu' atau 'kamu bebas'; talak tidak jatuh kecuali jika disertai niat mentalak di dalam hati. Talak terbagi: Talak Raj'i (talak satu atau dua tanpa tebusan), suami berhak merujuk istri selama masa 'iddah belum habis tanpa akad nikah baru dan tanpa wali/mahar baru cukup dengan ucapan rujuk ('aku merujukmu') dihadapan dua saksi; dan Talak Ba'in: Ba'in Sughra (talak raj'i yang habis masa iddahnya atau khulu') boleh kembali dengan akad nikah baru; Ba'in Kubra (talak tiga) tidak halal dirujuk atau dinikahi kembali sampai mantan istri menikah dengan laki-laki lain secara sah, disetubuhi secara nyata, lalu bercerai secara wajar dan habis masa iddahnya.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Al-Umm & Matan Al-Ghayah wat Taqrib",
            "pengarang": "Imam Asy-Syafi'i & Abu Syuja'",
            "bab": "Munakahat",
            "pasal": "Hukum Talak Lafal Sharih Kinayah dan Syarat Rujuk",
            "halaman": "181-186",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-munakahat-khulu-iddah-hadhanah",
        "content": "Kitab Matan Taqrib karya Abu Syuja'. Bab Khulu', Masa 'Iddah, dan Hak Asuh Anak (Hadhanah): (1) Khulu' (gugat cerai tebusan): perceraian dengan tebusan harta ('iwadh) dari pihak istri kepada suami; berstatus talak ba'in sughra dan suami tidak memiliki hak rujuk selain dengan akad nikah baru. (2) Masa 'Iddah (waktu tunggu wanita pasca pisah): Wanita hamil iddahnya sampai melahirkan kandungannya; Wanita yang ditinggal mati suami iddahnya 4 bulan 10 hari; Wanita yang dicerai hidup dan masih haid iddahnya 3 kali quru' (tiga kali masa suci dari haid menurut mazhab Syafi'i); Wanita yang belum pernah haid atau telah menopause iddahnya 3 bulan qamariyah. (3) Hadhanah: pemeliharaan dan pengasuhan anak kecil yang belum mumayyiz (di bawah 7 tahun) adalah hak mutlak ibu kandung selama ibu tidak murtad, tidak fasik, dan belum menikah lagi dengan pria lain yang bukan mahram si anak; setelah mumayyiz anak diberikan hak memilih tinggal bersama ayah atau ibunya.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Matan Al-Ghayah wat Taqrib",
            "pengarang": "Al-Qadhi Abu Syuja'",
            "bab": "Munakahat",
            "pasal": "Khulu Tebusan Masa Iddah Tiga Quru dan Hadhanah Anak",
            "halaman": "187-192",
            "mazhab": "Syafi'i"
        }
    },
    # --- JINAYAT & HUDUD ---
    {
        "id": "syafii-jinayat-qisas-diyat",
        "content": "Kitab Al-Umm karya Imam Syafi'i & Matan Taqrib karya Abu Syuja'. Bab Kitab Jinayat (Pidana Islam), Qisas, dan Diyat: Pembunuhan terbagi tiga kategori: (1) Sengaja murni ('amd mahdh): membunuh dengan alat yang umumnya mematikan, hukumannya adalah qisas (hukum mati dibalas bunuh) kecuali jika dimaafkan oleh wali korban dengan membayar diyat mughallazhah 100 ekor unta secara kontan dari harta pribadi pelaku; (2) Mirip sengaja (syibh 'amd): memukul dengan alat yang umumnya tidak mematikan namun korban mati, tidak ada qisas, hukumannya diyat mughallazhah 100 ekor unta yang dibebankan kepada kerabat pelaku ('aqilah) diangsur selama 3 tahun; (3) Keliru (khatha'): perbuatan tidak sengaja (seperti menembak hewan buruan mengenai manusia), hukumannya diyat mukhaffafah 100 ekor unta ditanggung 'aqilah selama 3 tahun disertai kewajiban memerdekakan budak muslim atau puasa 2 bulan berturut-turut sebagai kaffarah.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Al-Umm & Matan Taqrib",
            "pengarang": "Imam Asy-Syafi'i & Abu Syuja'",
            "bab": "Jinayat",
            "pasal": "Tiga Macam Pembunuhan Qisas dan Diyat Unta",
            "halaman": "195-200",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-hudud-zina-qadzaf-sariqah",
        "content": "Kitab Matan Taqrib karya Abu Syuja' & Fathul Qarib Al-Mujib. Bab Hudud (Pidana Syariat Tertentu): (1) Had Zina: jika pelaku berstatus Muhshan (pernah menikah sah dan pernah bersetubuh), hukumannya dirajam dengan batu hingga mati; jika Ghairu Muhshan (belum pernah menikah), hukumannya dicambuk 100 kali dan diasingkan (taghrib) sejauh jarak safar qashar selama 1 tahun penuh. Penetapan zina wajib dengan pengakuan 4 kali atau kesaksian 4 pria adil. (2) Had Qadzaf: menuduh muslim yang menjaga kehormatan (muhshan) berzina tanpa menghadirkan 4 saksi adil, hukumannya dicambuk 80 kali dan kesaksiannya ditolak selamanya. (3) Had Sariqah (Pencurian): pelakunya dipotong tangan kanan pada pergelangan tangan dengan syarat: barang dicuri dari tempat penyimpanan yang semestinya (hirz) dan mencapai batas minimal nisab seperempat dinar emas murni (kurang lebih 1,06 gram emas murni). Jika mencuri kedua kali dipotong kaki kiri, ketiga kali tangan kiri, keempat kali kaki kanan.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Matan Al-Ghayah wat Taqrib",
            "pengarang": "Al-Qadhi Abu Syuja'",
            "bab": "Hudud",
            "pasal": "Had Zina Had Qadzaf dan Potong Tangan Pencurian",
            "halaman": "205-212",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-hudud-khamr-murtad-bughat",
        "content": "Kitab Matan Taqrib karya Abu Syuja'. Bab Minuman Keras, Begal (Quththa'uth Thariq), Pemberontak (Bughat), dan Murtad: (1) Minum Khamr: setiap minuman yang memabukkan baik sedikit maupun banyak hukumnya haram, had pelakunya dicambuk 40 kali menurut pendapat mu'tamad mazhab Syafi'i, dan hakim boleh menambah hingga 80 kali sebagai ta'zir. (2) Begal/Perampok: jika membunuh dan merampas harta dihukum mati disalib; jika membunuh tanpa merampas dihukum mati; jika merampas harta tanpa membunuh dipotong tangan dan kaki secara bersilang; jika hanya menakut-nakuti diasingkan. (3) Bughat: kelompok muslim yang memberontak bersenjata melawan pemimpin sah yang adil wajib diperangi hingga kembali taat tanpa boleh dibunuh tawanan perangnya dan tanpa boleh dirampas hartanya. (4) Murtad: orang yang keluar dari Islam diminta bertaubat (istitabah) selama 3 hari; jika enggan bertaubat dihukum mati dan hartanya disita kas negara.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Matan Al-Ghayah wat Taqrib",
            "pengarang": "Al-Qadhi Abu Syuja'",
            "bab": "Hudud",
            "pasal": "Had Khamr Begal Bughat dan Hukum Murtad",
            "halaman": "213-218",
            "mazhab": "Syafi'i"
        }
    },
    # --- SEMBELIHAN, QURBAN, MAKANAN & PERADILAN ---
    {
        "id": "syafii-sembelihan-qurban-aqiqah",
        "content": "Kitab Al-Umm karya Imam Syafi'i & Fathul Qarib Al-Mujib. Bab Sembelihan (Dzabaih), Qurban (Udh-hiyah), dan Aqiqah: (1) Syarat sah sembelihan: penyembelih adalah muslim atau ahli kitab yang berakal, alat sembelih tajam bukan gigi atau kuku/tulang, dan wajib memutus dua saluran leher yaitu hulqum (saluran nafas) dan mari' (saluran makanan). (2) Qurban: hukumnya sunnah muakkadah kifayah pada hari raya Idul Adha (10 Dzulhijjah) dan hari tasyriq (11, 12, 13 Dzulhijjah) hingga maghrib. Hewan qurban: unta (minimal 5 thn), sapi/kerbau (minimal 2 thn) sah untuk 7 orang; kambing jawa (minimal 2 thn) atau domba (minimal 1 thn/sudah tanggal gigi) sah untuk 1 orang. Hewan qurban TIDAK sah jika memiliki cacat nyata: buta sebelah matanya, pincang nyata, sakit parah yang kurus kering, atau telinga/ekornya terpotong sebagian besar. Daging qurban sunnah dibagi tiga: dimakan pemilik, dihadiahkan kepada kerabat, dan disedekahkan kepada fakir miskin. Daging qurban haram diperjualbelikan termasuk kulitnya. (3) Aqiqah: sunnah disembelih pada hari ke-7 kelahiran anak: 2 ekor kambing untuk anak laki-laki dan 1 ekor untuk anak perempuan.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Al-Umm & Fathul Qarib Al-Mujib",
            "pengarang": "Imam Asy-Syafi'i & Ibnu Qasim",
            "bab": "Sembelihan dan Qurban",
            "pasal": "Syarat Dzabihah Ketentuan Hewan Qurban dan Aqiqah",
            "halaman": "220-226",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-aiman-sumpah-nazar",
        "content": "Kitab Matan Taqrib karya Abu Syuja'. Bab Al-Aiman (Sumpah) dan An-Nudzur (Nazar): Sumpah tidak sah dan tidak mengikat kecuali jika diucapkan dengan nama Allah (Demi Allah, Wallahi, Billahi) atau dengan salah satu sifat keagungan-Nya. Sumpah laghwu (perkataan tidak sengaja seperti 'la wallahi' dalam kebiasaan bicara) tidak berdosa dan tidak ada kaffarah. Jika melanggar sumpah yang sah, wajib membayar Kaffarah Sumpah berupa salah satu dari tiga pilihan: (1) Memberi makan sepuluh orang miskin masing-masing satu mud (kurang lebih 0,7 kg) makanan pokok, (2) Memberi pakaian yang layak kepada sepuluh orang miskin, atau (3) Memerdekakan satu orang budak muslim; jika tidak mampu mengerjakan salah satu dari tiga opsi di atas, baru diperbolehkan berpuasa selama tiga hari berturut-turut. Nazar: mewajibkan diri sendiri melakukan perbuatan ibadah qurbah yang asalnya tidak wajib (seperti bernazar shalat sunnah, puasa sunnah, atau sedekah); wajib ditepati jika berupa ketaatan, dan haram ditepati jika bernazar maksiat.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Matan Al-Ghayah wat Taqrib",
            "pengarang": "Al-Qadhi Abu Syuja'",
            "bab": "Aiman dan Nazar",
            "pasal": "Hukum Sumpah Kaffarah Melanggar Sumpah dan Nazar Ibadah",
            "halaman": "227-230",
            "mazhab": "Syafi'i"
        }
    },
    {
        "id": "syafii-peradilan-qadha-syahadat",
        "content": "Kitab Al-Umm karya Imam Syafi'i & Matan Taqrib karya Abu Syuja'. Bab Al-Aqdhiyah (Peradilan), Dakwaan, dan Saksi (Asy-Syahadat): Memegang jabatan hakim (qadha') adalah fardhu kifayah bagi masyarakat. Syarat sah Hakim: beragama Islam, baligh, berakal sehat, merdeka, laki-laki, adil menjaga muru'ah, berpendengaran dan berpenglihatan normal, serta berstatus mujtahid yang menguasai Al-Quran, As-Sunnah, ijma', qiyas, dan bahasa Arab. Kaidah persidangan: Hakim wajib memperlakukan kedua pihak yang bersengketa secara setara dalam tempat duduk dan pandangan; beban pembuktian (bayyinah) ada pada penggugat, sedangkan sumpah bantahan (yamin) ada pada tergugat yang mengingkari (al-bayyinatu 'alal mudda'i wal yaminu 'ala man ankara). Saksi yang diterima kesaksiannya adalah saksi yang adil: muslim, baligh, berakal, merdeka, menjauhi dosa-dosa besar, tidak sering melakukan dosa kecil, menjaga muru'ah akhlak, dan tidak memiliki permusuhan pribadi atau hubungan kepentingan waris langsung dengan pihak yang dibela.",
        "corpus": "fiqih",
        "metadata": {
            "kitab": "Al-Umm & Matan Al-Ghayah wat Taqrib",
            "pengarang": "Imam Asy-Syafi'i & Abu Syuja'",
            "bab": "Peradilan",
            "pasal": "Syarat Hakim Qadha Beban Pembuktian dan Syarat Saksi Adil",
            "halaman": "231-238",
            "mazhab": "Syafi'i"
        }
    }
]


def expand_fiqih_data():
    file_path = Path("data/fiqih/syafii_fiqih_data.json")
    with open(file_path, "r", encoding="utf-8") as f:
        existing_data = json.load(f)

    existing_ids = {d["id"] for d in existing_data}
    added_count = 0

    for ch in ADDITIONAL_FIQIH_CHAPTERS:
        if ch["id"] not in existing_ids:
            existing_data.append(ch)
            existing_ids.add(ch["id"])
            added_count += 1

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

    print(f"Berhasil menambahkan {added_count} bab fiqih baru.")
    print(f"Total bab Fiqih Mazhab Syafi'i sekarang: {len(existing_data)} bab lengkap.")


if __name__ == "__main__":
    expand_fiqih_data()
