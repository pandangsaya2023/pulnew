document.addEventListener('DOMContentLoaded', async () => {

    const currentSlug = window.location.pathname.split('/').pop().replace('.html','');

    try {
        const res = await fetch('/posts/index.json');
        const posts = await res.json();

        // 1. CARI POSTINGAN YG SEDANG DIBUKA
        const post = posts.find(p => p.slug === currentSlug);
        if(!post) return;

        // 2. ISI META TAG DI HEAD
        document.getElementById('meta-title').innerText = post.title + " | PULNEW.com";
        document.getElementById('meta-description').setAttribute("content", post.description || "");
        document.getElementById('og-title').setAttribute("content", post.title);
        document.getElementById('og-description').setAttribute("content", post.description || "");
        document.getElementById('og-image').setAttribute("content", post.image);

        // 3. ISI KONTEN BERITA
        document.getElementById('judul-berita').innerText = post.title;
        document.getElementById('gambar-berita').src = post.image;
        document.getElementById('gambar-berita').alt = post.title;
        document.getElementById('isi-berita').innerHTML = post.body; // isi dari markdown

        // 4. KODE "BERITA LAINNYA"  PUNYAMU

        const container = document.getElementById('berita-lainnya'); // kasih id ini di div "BERITA LAINNYA"
        if(!container) return;

        const currentSlug = window.location.pathname.split('/').pop().replace('.html','');

        try {
            const res = await fetch('/posts/index.json'); // <--- Cuma fetch 1 file
            const posts = await res.json();

            // Filter berita yg bukan yg sedang dibuka
            const lainnya = posts.filter(p => p.slug!== currentSlug).slice(0, 3);

            let html = '';
            lainnya.forEach(p => {
                html += `
                <a href="/berita/${p.slug}.html" class="card-lainnya">
                    <img src="${p.image}" loading="lazy">
                    <h3>${p.title}</h3>
                </a>`;
            });
            container.innerHTML = html;

        } catch(e) {
            container.innerHTML = 'Gagal memuat';
        }
    });
