import subprocess, numpy as np, sys
def oku(p,w=480,h=270):
    r=subprocess.run(["ffmpeg","-v","error","-i",p,"-vf",f"scale={w}:{h}","-f","rawvideo","-pix_fmt","gray","-"],capture_output=True)
    return np.frombuffer(r.stdout,np.uint8).reshape(-1,h,w).astype(np.float32)
g,s=sys.argv[1],sys.argv[2]
a=oku(g); b=oku(s); print('kare girdi',len(a),'sonuç',len(b))
n=min(len(a),len(b))
for kay in (-1,0,1):
    c=[]
    for i in range(0,n-2,24):
        j=i+kay
        if 0<=j<len(b):
            ea=np.abs(np.diff(a[i],axis=1)); eb=np.abs(np.diff(b[j],axis=1))
            c.append(np.corrcoef(ea.ravel(),eb.ravel())[0,1])
    print('kayma',kay,'kenar korelasyonu ort %.3f min %.3f'%(np.mean(c),np.min(c)))
# parlaklık sıçraması (kareler arası ortalama fark)
d=np.abs(np.diff(b.mean((1,2)))); print('kareler arası parlaklık farkı en büyük %.2f (kare %d)'%(d.max(),d.argmax()))
