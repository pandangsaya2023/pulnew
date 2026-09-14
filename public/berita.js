document.addEventListener('DOMContentLoaded', async () => {
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
