import numpy as np, sys
from PIL import Image
from scipy import ndimage as ndi
U='/root/.claude/uploads/fe614ef2-2319-5380-86af-14d2f5ef6984/'
O='/home/claude/carousel-assets/'
items=[('50e30738-image.png','lik-01-ledja'),('c4a84e5a-image.png','lik-02-pokazuje'),('5fb48e21-image.png','lik-03-dupli-biceps'),
('9bc1e015-image.jpg','lik-04-odmor'),('382c0f20-image.jpg','lik-05-povrce'),('03019975-image.jpg','lik-06-voda'),
('b705e51c-image.jpg','lik-07-obrok'),('8c0eb573-image.jpg','lik-08-cucanj'),('3b39eab9-image.jpg','lik-09-sklek'),
('edd02b1c-image.jpg','lik-11-trk'),('dd497a4d-image.jpg','lik-12-hod-napred'),('8842e160-image.jpg','lik-13-hod-profil'),('b42d792c-image.jpg','lik-14-okret')]
res={}
for f,name in items:
    im=np.asarray(Image.open(U+f).convert('RGB')).astype(np.float32)
    h,w,_=im.shape
    border=np.concatenate([im[:6].reshape(-1,3),im[-6:].reshape(-1,3),im[:,:6].reshape(-1,3),im[:,-6:].reshape(-1,3)])
    bg=np.median(border,axis=0)
    # smooth local bg estimate not needed; flat
    dist=np.sqrt(((im-bg)**2).sum(-1))
    T=30
    cand=dist<T
    lab,n=ndi.label(cand)
    edge=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))-{0}
    bgreg=np.isin(lab,list(edge))
    # enclosed bg holes: strict
    strict=dist<14
    lab2,n2=ndi.label(strict & ~bgreg)
    if n2:
        sizes=ndi.sum(np.ones_like(lab2),lab2,range(1,n2+1))
        holes=[i+1 for i,s in enumerate(sizes) if s>900]
        if name=='lik-07-obrok':
            cms=ndi.center_of_mass(np.ones_like(lab2),lab2,holes)
            print('holes',[(int(c[0]),int(c[1]),int(sizes[i-1])) for c,i in zip(cms,holes)])
            holes=[i for c,i in zip(cms,holes) if c[0]>700]
        hole=np.isin(lab2,holes)
        # grow hole into candidate
        hole=ndi.binary_dilation(hole,iterations=3)&cand
    else: hole=np.zeros_like(bgreg)
    reg=bgreg|hole
    regd=ndi.binary_dilation(reg,iterations=2)
    a=np.ones((h,w),np.float32)
    soft=np.clip((dist-10)/(46-10),0,1)
    a[regd]=soft[regd]
    a[reg & (dist<10)]=0
    # decontaminate
    aa=np.clip(a,0.05,1)[...,None]
    col=np.where((a[...,None]<1),(im-(1-aa)*bg)/aa,im)
    col=np.clip(col,0,255)
    rgba=np.dstack([col,a*255]).astype(np.uint8)
    ys,xs=np.where(a>0.08)
    y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    out=Image.fromarray(rgba).crop((x0,y0,x1,y1))
    out.save(O+name+'.png',optimize=True)
    res[name]=(out.size,len(holes) if n2 else 0, tuple(int(v) for v in bg))
    print(name,out.size,res[name][1:])
# sleeping: plain
Image.open(U+'9809e93f-image.jpg').convert('RGB').save(O+'lik-10-san.png',optimize=True)
