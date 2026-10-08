import re,sys,os,asyncio
from playwright.async_api import async_playwright
P='/tmp/claude-0/-home-claude/fe614ef2-2319-5380-86af-14d2f5ef6984/scratchpad/carousel1/project/'
W=os.getcwd()
ids={'9671f9546c249e48654437debc242c7e':'lik-01-ledja','3611d7780f5130871fb312eec61a1e3a':'lik-02-pokazuje','1018032dc677b84dc8034eb423d6ab12':'lik-03-dupli-biceps','f3e0d073bfccc5df5fff6987a0226a6b':'lik-04-odmor','214ad85032ec344635298ad0a7f782d1':'lik-05-povrce','db735d93583d0b34b8752fd50d4d5356':'lik-06-voda','24de219cd38e787aa493faf2a87baad4':'lik-07-obrok','63570142a3da1a1ebda4b74d6ae42950':'lik-08-cucanj','4bf72a4005283873a58b321d095e4163':'lik-09-sklek','758349ad60d2cbb2d46819eec48e6db7':'lik-10-san','a801d5dbdab6fd0c347dcf41adc8d8c1':'lik-11-trk','e85042ab6e940f826e203f89126c4c3f':'lik-12-hod-napred','97f6d2687ab8edc3edcdb9d6af1c7e1d':'lik-13-hod-profil','ff597d1bf01ca01d18dbee37987e1206':'lik-14-okret'}
ff=''
for fam,pk,ws in (('Barlow','barlow',(500,600,700)),('Barlow Condensed','barlow-condensed',(800,900))):
    for w in ws:
        for sub,rng in (('latin','U+0000-00FF,U+2000-206F'),('latin-ext','U+0100-024F')):
            ff+=f"@font-face{{font-family:'{fam}';font-weight:{w};src:url('file://{W}/node_modules/@fontsource/{pk}/files/{pk}-{sub}-{w}-normal.woff2') format('woff2');unicode-range:{rng}}}\n"
async def main(names):
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':1080,'height':1350})
        for n in names:
            s=open(P+n+'.dc.html').read()
            body=re.search(r'</helmet>(.*)</x-dc>',s,re.S).group(1)
            body=re.sub(r'/_blob/([0-9a-f]{32})',lambda m:'file:///home/claude/carousel-assets/'+ids[m.group(1)]+'.png',body)
            html=f"<!doctype html><meta charset=utf-8><style>{ff}body{{margin:0}}</style>{body}"
            open(f'{n}.html','w').write(html)
            await pg.goto(f'file://{W}/{n}.html'); await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(300)
            await pg.screenshot(path=f'{n}.png')
        await b.close()
names=sys.argv[1:]
asyncio.run(main(names))
from PIL import Image
ims=[Image.open(n+'.png').resize((540,675)) for n in names]
sh=Image.new('RGB',(540*len(ims)+10*(len(ims)-1),675),(60,60,60))
for i,im in enumerate(ims): sh.paste(im,(i*550,0))
sh.save('preview.png')
