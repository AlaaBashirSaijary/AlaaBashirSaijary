#!/usr/bin/env python3
"""Builds the static, SEO-ready site into _site/ (English at /, Arabic at /ar/).

    pip install beautifulsoup4
    python3 tools/build.py

Page content lives in src/*.html with data-en / data-ar attributes holding the text
for each language; this script writes one crawlable HTML file per language and page,
adds metadata (canonical, hreflang, Open Graph, JSON-LD), a sitemap and robots.txt.
"""
import datetime, hashlib, json, re, shutil, subprocess
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

from urllib.parse import quote
WA_NUMBER = '963984668063'
PRICING = json.loads((Path(__file__).resolve().parent.parent / 'src' / 'pricing.json').read_text(encoding='utf-8'))
ANALYTICS = json.loads((Path(__file__).resolve().parent.parent / 'src' / 'analytics.json').read_text(encoding='utf-8'))
DEFAULT_WA = {'en': 'Hello Alaa, I visited your website and would like to talk.',
              'ar': 'مرحباً ألاء، زرت موقعك وأود التحدث معك.'}
PAGES = {
    'home': {'path': '', 'src': 'home.html', 'og': 'og-home', 'meta': {
        'en': ('Alaa Saijary | Flutter & Laravel Developer in Syria',
               'Computer engineer and mobile app developer in Syria. Flutter apps and Laravel web solutions: Lirati, Manhaj Hayah and Aayadati. See my work and download my CV.'),
        'ar': ('ألاء سيجري | مطوّرة تطبيقات Flutter وLaravel في سوريا',
               'ألاء سيجري مهندسة حاسوب ومطوّرة تطبيقات موبايل من سوريا. أبني تطبيقات Flutter وحلول ويب بـ Laravel مثل Lirati ومنهج حياة وعيادتي. اطّلع على أعمالي وسيرتي الذاتية.')}},
    'clinic': {'path': 'clinic-manager/', 'src': 'clinic.html', 'og': 'og-clinic', 'kind': 'product',
               'wa': {'en': "Hello, I'd like to know more about the Aayadati clinic app and try the free version.",
                      'ar': 'مرحباً، أريد معرفة المزيد عن تطبيق عيادتي وتجربة النسخة المجانية.'}, 'meta': {
        'en': ('Aayadati: Offline Clinic Management App for Doctors',
               'Aayadati is a clinic management app that works fully offline: patient records, appointments, prescriptions and reports in Arabic. One-time payment, 14-day free trial.'),
        'ar': ('عيادتي: تطبيق إدارة عيادات طبية يعمل بلا إنترنت',
               'عيادتي تطبيق لإدارة العيادات الطبية يعمل بلا إنترنت: سجلات المرضى والمواعيد والوصفات والتقارير بواجهة عربية. دفعة واحدة بلا اشتراك وتجربة مجانية 14 يوماً.')}},
}
PAGES['school'] = {'path': 'school-management-system/', 'src': 'school.html', 'og': 'og-school', 'kind': 'product',
                   'wa': {'en': 'Hello, I would like a quote for the Education ERP school management system.',
                          'ar': 'مرحباً، أريد عرض سعر لنظام Education ERP لإدارة المدارس.'}, 'meta': {
    'en': ('Education ERP: School Management System with QR Attendance and Fees',
           'Education ERP is a school management system: QR attendance, grades and report cards, fees and receipts, WhatsApp/SMS parent alerts and timetables. Arabic and English, with a mobile app and live demo.'),
    'ar': ('Education ERP: نظام إدارة مدارس بحضور QR وأقساط وإشعارات للأهل',
           'Education ERP نظام لإدارة المدارس: حضور بالـ QR، علامات وشهادات، أقساط وإيصالات، إشعارات واتساب/SMS لأولياء الأمور وجداول حصص. عربي وإنجليزي مع تطبيق موبايل وعرض تفاعلي.')}}
PAGES['legal'] = {'path': 'privacy/', 'src': 'legal.html', 'og': 'og-home', 'meta': {
    'en': ('Privacy Policy & Terms of Use | Alaa Saijary',
           'How this website and the Aayadati, Education ERP and Manhaj Hayah apps handle data, plus the terms of use and licence for my software.'),
    'ar': ('سياسة الخصوصية وشروط الاستخدام | ألاء سيجري',
           'كيف يتعامل هذا الموقع وتطبيقات عيادتي وEducation ERP ومنهج حياة مع البيانات، مع شروط الاستخدام والترخيص لبرامجي.')}}
CRUMB = {'en': 'Home', 'ar': 'الرئيسية'}
CLINIC_NAME = {'en': 'Aayadati: clinic management app', 'ar': 'عيادتي: تطبيق إدارة العيادات'}
PAGE_NAME = {'clinic': CLINIC_NAME, 'school': {'en': 'Education ERP: school management system', 'ar': 'نظام Education ERP لإدارة المدارس'}}
ROLE = {'en': 'Mobile & Web Developer', 'ar': 'مطوّرة تطبيقات موبايل وويب'}
APPS = {
    'clinic': {'name': 'Aayadati', 'alternateName': ['عيادتي', 'Clinic Manager'], 'applicationCategory': 'HealthApplication',
               'operatingSystem': 'iPadOS, Android', 'inLanguage': 'ar'},
    'school': {'name': 'Education ERP System', 'alternateName': ['نظام إدارة المدارس', 'School Management System'],
               'applicationCategory': 'EducationalApplication', 'operatingSystem': 'Web (PWA)', 'inLanguage': ['ar', 'en']},
}
LOCALE = {'en': 'en_US', 'ar': 'ar_AR'}


def analytics_html():
    """Provider script + a tiny config for site.js. Empty when analytics.json has no provider/id."""
    provider = (ANALYTICS.get('provider') or '').strip()
    ident = (ANALYTICS.get('id') or '').strip()
    if not provider or not ident:
        return ''
    if not re.fullmatch(r'[A-Za-z0-9._-]+', ident):
        raise ValueError('analytics id contains unexpected characters')
    cfg = '<script>window.__ANALYTICS={"provider":"%s"}</script>' % provider
    if provider == 'goatcounter':
        tag = '<script data-goatcounter="https://%s.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>' % ident
    elif provider == 'plausible':
        tag = '<script defer data-domain="%s" src="https://plausible.io/js/script.js"></script>' % ident
    elif provider == 'ga4':
        tag = ('<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script><script>window.dataLayer=window.dataLayer||[];'
               'function gtag(){dataLayer.push(arguments)}gtag("js",new Date());gtag("config","%s",{anonymize_ip:true});</script>' % (ident, ident))
    else:
        raise ValueError('unknown analytics provider: %s' % provider)
    return cfg + tag


def analytics_note():
    provider = (ANALYTICS.get('provider') or '').strip()
    if not provider or not (ANALYTICS.get('id') or '').strip():
        return ''
    if provider == 'ga4':
        return ('<span class="anote" data-en="This site uses Google Analytics to count visits." '
                'data-ar="يستخدم هذا الموقع Google Analytics لإحصاء الزيارات.">This site uses Google Analytics to count visits.</span>')
    return ('<span class="anote" data-en="Visits are counted anonymously, without cookies." '
            'data-ar="تُحصى الزيارات بشكل مجهول وبلا ملفات تعريف ارتباط.">Visits are counted anonymously, without cookies.</span>')


def price_html(group, key, lang):
    entry = PRICING.get(group, {}).get(key, {})
    shown = (entry.get('display_' + lang) or '').strip()
    if shown:
        return '<span class="amount">%s</span>' % shown
    return '<span class="amount ask" data-en="Ask for a quote" data-ar="اطلب عرض سعر">Ask for a quote</span>'


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
        '{{school}}': home + 'school-management-system/' if page != 'school' else './',
        '{{school}}': home + 'school-management-system/' if page != 'school' else './',
        '{{privacy}}': home + 'privacy/' if page != 'legal' else './',
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
    for el in soup.find_all(attrs={'data-alt-' + lang: True}):
        el['alt'] = el['data-alt-' + lang]
    for el in soup.find_all(True):
        for attr in [a for a in el.attrs if a in ('data-en', 'data-ar') or a.startswith('data-href-') or a.startswith('data-alt-')]:
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
            {'@type': 'SoftwareApplication', 'name': 'Education ERP System', 'url': page_url(lang, 'school'),
             'applicationCategory': 'EducationalApplication', 'operatingSystem': 'Web', 'inLanguage': ['ar', 'en'],
             'author': person},
            {'@type': 'MobileApplication', 'name': 'Manhaj Hayah', 'alternateName': 'منهج حياة', 'url': MANHAJ,
             'applicationCategory': 'ReferenceApplication', 'operatingSystem': 'Android 7.0+', 'inLanguage': ['ar', 'en'],
             'author': person},
        ]
    elif page == 'legal':
        graph += [
            {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': CRUMB[lang], 'item': page_url(lang, 'home')},
                {'@type': 'ListItem', 'position': 2, 'name': title.split(' | ')[0], 'item': url}]},
            {'@type': 'WebPage', '@id': url + '#page', 'url': url, 'name': title, 'description': desc, 'inLanguage': lang,
             'isPartOf': {'@id': SITE + '#website'}}]
    else:
        feats = [text(h) for h in soup.select('#features .fcard h3')]
        app = dict(APPS[page])
        usd = [e['usd'] for e in PRICING.get('clinic' if page == 'clinic' else 'school', {}).values() if e.get('usd')]
        if usd:
            app['offers'] = {'@type': 'Offer', 'price': str(min(usd)), 'priceCurrency': 'USD', 'url': url + '#pricing'}
        graph += [
            {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': CRUMB[lang], 'item': page_url(lang, 'home')},
                {'@type': 'ListItem', 'position': 2, 'name': PAGE_NAME[page][lang], 'item': url}]},
            {'@type': 'WebPage', '@id': url + '#page', 'url': url, 'name': title, 'description': desc, 'inLanguage': lang,
             'isPartOf': {'@id': SITE + '#website'}, 'about': {'@id': url + '#app'}},
            dict({'@type': 'SoftwareApplication', '@id': url + '#app', 'description': desc, 'url': url, 'featureList': feats,
                  'author': {'@type': 'Person', '@id': SITE + '#person', 'name': 'Alaa Bashir Saijary'}}, **app),
        ]
    if page == 'school':
        graph.append({'@type': 'VideoObject', 'name': 'Education ERP: school management system demo' if lang == 'en' else 'عرض نظام Education ERP لإدارة المدارس',
                      'description': 'A two-minute screen recording of the Education ERP interactive demo with Arabic voice-over.' if lang == 'en' else 'تسجيل شاشة مدته دقيقتان للعرض التفاعلي لنظام Education ERP بتعليق صوتي عربي.',
                      'thumbnailUrl': SITE + 'assets/school-demo-poster.jpg', 'uploadDate': '2026-10-11', 'duration': 'PT2M10S',
                      'contentUrl': SITE + 'assets/school-demo-ar.mp4', 'inLanguage': 'ar', 'author': person})
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
<body data-page="{pageid}">
<a class="skip" href="#top" data-en="Skip to content" data-ar="تخطَّ إلى المحتوى">Skip to content</a>
<div class="progress" id="progress"></div>
{topbar}
{header}
{body}
{footer}
{analytics}
<a class="wa-float" href="{{{{wa_en}}}}" data-href-en="{{{{wa_en}}}}" data-href-ar="{{{{wa_ar}}}}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" aria-hidden="true" class="wai"><path fill="currentColor" d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.33 4.95L2 22l5.25-1.38a9.9 9.9 0 0 0 4.79 1.22h.01c5.46 0 9.91-4.45 9.91-9.91C22 6.45 17.5 2 12.04 2zm5.8 14.11c-.24.68-1.4 1.32-1.93 1.4-.49.08-1.11.11-1.79-.11-.41-.13-.94-.3-1.62-.6-2.85-1.23-4.71-4.1-4.85-4.29-.14-.19-1.16-1.54-1.16-2.94s.73-2.09.99-2.38c.26-.28.56-.35.75-.35h.54c.17 0 .41-.02.62.48.24.58.81 2 .88 2.15.07.15.11.32.02.51-.08.19-.13.3-.26.46-.13.16-.28.36-.4.48-.13.13-.27.27-.12.53.15.26.67 1.11 1.44 1.8 1 .89 1.83 1.17 2.09 1.3.26.13.41.11.56-.07.15-.17.65-.76.83-1.02.17-.26.34-.21.57-.13.24.09 1.5.71 1.76.84.26.13.43.19.49.3.07.11.07.61-.17 1.29z"/></svg><span class="lbl" data-en="WhatsApp" data-ar="واتساب">WhatsApp</span></a>
<script src="{{{{root}}}}site.js?v={js_v}" defer></script>
</body>
</html>
'''


def build_page(lang, page, css_v, js_v):
    title, desc = PAGES[page]['meta'][lang]
    other = 'ar' if lang == 'en' else 'en'
    partial = lambda n: (SRC / 'partials' / n).read_text(encoding='utf-8')
    body = (SRC / PAGES[page]['src']).read_text(encoding='utf-8')
    product = PAGES[page].get('kind') == 'product'
    alts = ''.join('<link rel="alternate" hreflang="%s" href="%s">\n' % (l, page_url(l, page)) for l in LANGS)
    alts += '<link rel="alternate" hreflang="x-default" href="%s">' % page_url('en', page)
    esc = lambda v: v.replace('&', '&amp;').replace('"', '&quot;')
    html = LAYOUT.format(
        lang=lang, dir='rtl' if lang == 'ar' else 'ltr', title=esc(title), desc=esc(desc), url=page_url(lang, page),
        pageid='%s-%s' % (page, lang), analytics=analytics_html(), alternates=alts, locale=LOCALE[lang], locale_alt=LOCALE[other], css_v=css_v, js_v=js_v,
        og=SITE + 'assets/%s-%s.png' % (PAGES[page]['og'], lang), jsonld='@@JSONLD@@',
        topbar=partial('topbar-product.html' if product else 'topbar.html'),
        header=partial('header-product.html' if product else 'header.html'), body=body, footer=partial('footer.html'))
    tokens = rel_links(lang, page)
    wa = PAGES[page].get('wa', DEFAULT_WA)
    tokens.update({
        '{{wa_en}}': 'https://wa.me/%s?text=%s' % (WA_NUMBER, quote(wa['en'])),
        '{{wa_ar}}': 'https://wa.me/%s?text=%s' % (WA_NUMBER, quote(wa['ar'])),
    })
    if product:
        other_id = 'school' if page == 'clinic' else 'clinic'
        names = {'school': ('School ERP', 'نظام المدارس'), 'clinic': ('Aayadati clinic app', 'تطبيق عيادتي')}[other_id]
        tokens.update({
            '{{other_product}}': tokens['{{school}}'] if other_id == 'school' else tokens['{{clinic}}'],
            '{{other_name_en}}': names[0], '{{other_name_ar}}': names[1],
        })
    tokens['{{analytics_note}}'] = analytics_note()
    for token, value in tokens.items():
        html = html.replace(token, value)
    html = re.sub(r'\{\{price:(\w+)\.(\w+)\}\}', lambda m: price_html(m.group(1), m.group(2), lang), html)
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
            prio = '1.0' if page == 'home' and lang == 'en' else '0.9' if page == 'home' else '0.3' if page == 'legal' else '0.8'
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
