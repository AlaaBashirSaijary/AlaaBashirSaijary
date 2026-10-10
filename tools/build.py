#!/usr/bin/env python3
"""Builds the static, SEO-ready site into _site/ (English at /, Arabic at /ar/).

    pip install beautifulsoup4
    python3 tools/build.py

Page content lives in src/*.html with data-en / data-ar attributes holding the text
for each language; this script writes one crawlable HTML file per language and page,
adds metadata (canonical, hreflang, Open Graph, JSON-LD), a sitemap and robots.txt.
"""
import datetime, hashlib, json, shutil, subprocess
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / 'src', ROOT / '_site'
SITE = 'https://alaabashirsaijary.github.io/AlaaBashirSaijary/'
LINKEDIN = 'https://www.linkedin.com/in/alaa-basher-saijary-b48002378/'
GITHUB = 'https://github.com/AlaaBashirSaijary'
MANHAJ = 'https://alaabashirsaijary.github.io/manhaj-hayah/'
CLINIC_SITE = 'https://alaabashirsaijary.github.io/ClinicManagerFlutter/'
LANGS = ('en', 'ar')

PAGES = {
    'home': {'path': '', 'src': 'home.html', 'og': 'og-home', 'meta': {
        'en': ('Alaa Saijary | Flutter & Laravel Developer in Syria',
               'Computer engineer and mobile app developer in Syria. Flutter apps and Laravel web solutions: Lirati, Manhaj Hayah and Aayadati. See my work and download my CV.'),
        'ar': ('ألاء سيجري | مطوّرة تطبيقات Flutter وLaravel في سوريا',
               'ألاء سيجري مهندسة حاسوب ومطوّرة تطبيقات موبايل من سوريا. أبني تطبيقات Flutter وحلول ويب بـ Laravel مثل Lirati ومنهج حياة وعيادتي. اطّلع على أعمالي وسيرتي الذاتية.')}},
    'clinic': {'path': 'clinic-manager/', 'src': 'clinic.html', 'og': 'og-clinic', 'meta': {
        'en': ('Aayadati: Offline Clinic Management App for Doctors',
               'Aayadati is a clinic management app that works fully offline: patient records, appointments, prescriptions and reports in Arabic. One-time payment, 14-day free trial.'),
        'ar': ('عيادتي: تطبيق إدارة عيادات طبية يعمل بلا إنترنت',
               'عيادتي تطبيق لإدارة العيادات الطبية يعمل بلا إنترنت: سجلات المرضى والمواعيد والوصفات والتقارير بواجهة عربية. دفعة واحدة بلا اشتراك وتجربة مجانية 14 يوماً.')}},
}
CRUMB = {'en': 'Home', 'ar': 'الرئيسية'}
CLINIC_NAME = {'en': 'Aayadati: clinic management app', 'ar': 'عيادتي: تطبيق إدارة العيادات'}
ROLE = {'en': 'Mobile & Web Developer', 'ar': 'مطوّرة تطبيقات موبايل وويب'}
LOCALE = {'en': 'en_US', 'ar': 'ar_AR'}


def out_dir(lang, page):
    return ('' if lang == 'en' else 'ar/') + PAGES[page]['path']


def page_url(lang, page):
    return SITE + out_dir(lang, page)


def rel_links(lang, page):
    """Relative links valid from the page's own directory (works on any host path)."""
    depth = len([p for p in out_dir(lang, page).split('/') if p])
    root = '../' * depth
    lang_depth = len([p for p in PAGES[page]['path'].split('/') if p])
    home = '../' * lang_depth or './'
    other = 'ar' if lang == 'en' else 'en'
    return {
        '{{root}}': root, '{{home}}': home, '{{clinic}}': home + 'clinic-manager/' if page != 'clinic' else './',
        '{{other}}': (root + out_dir(other, page)) or './',
        '{{other_lang}}': other,
        '{{cv}}': root + ('cv/Alaa-Saijary-CV.pdf' if lang == 'en' else 'cv/Alaa-Saijary-CV-ar.pdf'),
    }


def fingerprint(path):
    return hashlib.sha1(path.read_bytes()).hexdigest()[:8]


def localize(html, lang):
    soup = BeautifulSoup(html, 'html.parser')
    for el in soup.find_all(attrs={'data-' + lang: True}):
        value = el['data-' + lang]
        el.clear()
        for node in list(BeautifulSoup(value, 'html.parser').contents):
            el.append(node)
    for el in soup.find_all(attrs={'data-href-' + lang: True}):
        el['href'] = el['data-href-' + lang]
    for el in soup.find_all(True):
        for attr in [a for a in el.attrs if a in ('data-en', 'data-ar') or a.startswith('data-href-')]:
            del el.attrs[attr]
    return soup


def text(el):
    return ' '.join(el.get_text(' ', strip=True).split())


def json_ld(soup, lang, page):
    url = page_url(lang, page)
    title, desc = PAGES[page]['meta'][lang]
    person = {'@id': SITE + '#person'}
    graph = []
    faq = [{'@type': 'Question', 'name': text(d.summary), 'acceptedAnswer': {'@type': 'Answer', 'text': text(d.p)}}
           for d in soup.select('.faq details')]
    if page == 'home':
        graph += [
            {'@type': 'WebSite', '@id': SITE + '#website', 'url': SITE, 'name': 'Alaa Saijary',
             'inLanguage': ['en', 'ar'], 'publisher': person},
            {'@type': 'Person', '@id': SITE + '#person', 'name': 'Alaa Bashir Saijary', 'alternateName': 'ألاء بشير سيجري',
             'jobTitle': ROLE[lang], 'url': SITE, 'description': desc,
             'sameAs': [LINKEDIN, GITHUB, MANHAJ, CLINIC_SITE],
             'knowsAbout': ['Flutter', 'Dart', 'Laravel', 'PHP', 'Angular', 'React', 'Python', 'Firebase', 'REST APIs',
                            'Cybersecurity', 'Mobile app development'],
             'knowsLanguage': ['Arabic', 'English', 'Turkish'],
             'alumniOf': {'@type': 'CollegeOrUniversity', 'name': 'University of Aleppo'},
             'address': {'@type': 'PostalAddress', 'addressCountry': 'SY'}},
            {'@type': 'ProfilePage', '@id': url + '#page', 'url': url, 'name': title, 'inLanguage': lang,
             'mainEntity': person, 'isPartOf': {'@id': SITE + '#website'}},
            {'@type': 'MobileApplication', 'name': 'Lirati', 'url': 'https://lirati.app/invite',
             'applicationCategory': 'FinanceApplication', 'operatingSystem': 'iOS, Android', 'author': person},
            {'@type': 'MobileApplication', 'name': 'Manhaj Hayah', 'alternateName': 'منهج حياة', 'url': MANHAJ,
             'applicationCategory': 'ReferenceApplication', 'operatingSystem': 'Android 7.0+', 'inLanguage': ['ar', 'en'],
             'author': person},
        ]
    else:
        feats = [text(h) for h in soup.select('#features .fcard h3')]
        graph += [
            {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': CRUMB[lang], 'item': page_url(lang, 'home')},
                {'@type': 'ListItem', 'position': 2, 'name': CLINIC_NAME[lang], 'item': url}]},
            {'@type': 'WebPage', '@id': url + '#page', 'url': url, 'name': title, 'description': desc, 'inLanguage': lang,
             'isPartOf': {'@id': SITE + '#website'}, 'about': {'@id': url + '#app'}},
            {'@type': 'SoftwareApplication', '@id': url + '#app', 'name': 'Aayadati', 'alternateName': ['عيادتي', 'Clinic Manager'],
             'applicationCategory': 'HealthApplication', 'operatingSystem': 'iPadOS, Android', 'inLanguage': 'ar',
             'description': desc, 'url': url, 'featureList': feats, 'author': {'@type': 'Person', '@id': SITE + '#person',
                                                                             'name': 'Alaa Bashir Saijary'}},
        ]
    if faq:
        graph.append({'@type': 'FAQPage', 'mainEntity': faq})
    return {'@context': 'https://schema.org', '@graph': graph}


LAYOUT = '''<!doctype html>
<html lang="{lang}" dir="{dir}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
{alternates}
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="author" content="Alaa Bashir Saijary">
<meta name="theme-color" content="#4a1942">
<link rel="icon" href="{{{{root}}}}assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{{{{root}}}}assets/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Alaa Saijary">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="{locale}">
<meta property="og:locale:alternate" content="{locale_alt}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{title}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{og}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Fira+Sans:wght@600;700;800&family=Cairo:wght@400;600;700;800&family=Fraunces:ital,wght@1,300&display=swap">
<link rel="stylesheet" href="{{{{root}}}}style.css?v={css_v}">
<script>document.documentElement.classList.add('js')</script>
<script type="application/ld+json">{jsonld}</script>
</head>
<body>
<a class="skip" href="#top" data-en="Skip to content" data-ar="تخطَّ إلى المحتوى">Skip to content</a>
<div class="progress" id="progress"></div>
{topbar}
{header}
{body}
{footer}
<script src="{{{{root}}}}site.js?v={js_v}" defer></script>
</body>
</html>
'''


def build_page(lang, page, css_v, js_v):
    title, desc = PAGES[page]['meta'][lang]
    other = 'ar' if lang == 'en' else 'en'
    partial = lambda n: (SRC / 'partials' / n).read_text(encoding='utf-8')
    body = (SRC / PAGES[page]['src']).read_text(encoding='utf-8')
    alts = ''.join('<link rel="alternate" hreflang="%s" href="%s">\n' % (l, page_url(l, page)) for l in LANGS)
    alts += '<link rel="alternate" hreflang="x-default" href="%s">' % page_url('en', page)
    esc = lambda v: v.replace('&', '&amp;').replace('"', '&quot;')
    html = LAYOUT.format(
        lang=lang, dir='rtl' if lang == 'ar' else 'ltr', title=esc(title), desc=esc(desc), url=page_url(lang, page),
        alternates=alts, locale=LOCALE[lang], locale_alt=LOCALE[other], css_v=css_v, js_v=js_v,
        og=SITE + 'assets/%s-%s.png' % (PAGES[page]['og'], lang), jsonld='@@JSONLD@@',
        topbar=partial('topbar.html'), header=partial('header.html'), body=body, footer=partial('footer.html'))
    for token, value in rel_links(lang, page).items():
        html = html.replace(token, value)
    soup = localize(html, lang)
    ld = json.dumps(json_ld(soup, lang, page), ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    result = str(soup).replace('@@JSONLD@@', ld)
    assert '{{' not in result, 'unreplaced token in %s/%s' % (lang, page)
    dest = OUT / out_dir(lang, page)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'index.html').write_text(result, encoding='utf-8')


def lastmod():
    try:
        return subprocess.check_output(['git', 'log', '-1', '--format=%cs'], cwd=ROOT, text=True).strip()
    except Exception:
        return datetime.date.today().isoformat()


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    css_v, js_v = fingerprint(SRC / 'style.css'), fingerprint(SRC / 'site.js')
    shutil.copy(SRC / 'style.css', OUT / 'style.css')
    shutil.copy(SRC / 'site.js', OUT / 'site.js')
    shutil.copytree(ROOT / 'assets', OUT / 'assets')
    (OUT / 'cv').mkdir()
    for pdf in (ROOT / 'cv').glob('*.pdf'):
        shutil.copy(pdf, OUT / 'cv' / pdf.name)
    (OUT / '.nojekyll').write_text('')
    for f in ROOT.glob('google*.html'):  # Search Console ownership verification files
        shutil.copy(f, OUT / f.name)
    for page in PAGES:
        for lang in LANGS:
            build_page(lang, page, css_v, js_v)

    day = lastmod()
    urls = []
    for page in PAGES:
        for lang in LANGS:
            alts = ''.join('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>\n' % (l, page_url(l, page)) for l in LANGS)
            alts += '    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>\n' % page_url('en', page)
            prio = '1.0' if page == 'home' and lang == 'en' else '0.9' if page == 'home' else '0.8'
            urls.append('  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n    <priority>%s</priority>\n%s  </url>' % (page_url(lang, page), day, prio, alts))
    (OUT / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n%s\n</urlset>\n' % '\n'.join(urls), encoding='utf-8')
    (OUT / 'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n' % SITE)
    (OUT / '404.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="robots" content="noindex"><title>Page not found | Alaa Saijary</title>'
        '<link rel="stylesheet" href="%sstyle.css"></head><body><main class="wrap" style="padding-block:20vh;text-align:center">'
        '<h1 style="font-size:3rem;color:var(--deep)">404</h1><p style="margin:12px 0 28px;color:var(--mute)">This page does not exist.</p>'
        '<a class="btn" href="%s">Home</a> <a class="btn outline" href="%sar/">العربية</a></main></body></html>' % (SITE, SITE, SITE), encoding='utf-8')
    print('built %d pages into %s' % (len(PAGES) * len(LANGS), OUT))


if __name__ == '__main__':
    main()
