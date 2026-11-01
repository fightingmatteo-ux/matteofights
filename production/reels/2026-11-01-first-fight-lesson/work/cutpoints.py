"""Find cut points in silence: python3 work/cutpoints.py  (reads assets/voice.wav + work/words.json)."""
import json, subprocess, sys
import numpy as np
pcm = subprocess.run(["ffmpeg","-v","error","-i","assets/voice.wav","-ac","1","-ar","16000","-f","f32le","-"],capture_output=True,check=True).stdout
x = np.frombuffer(pcm, np.float32); H = 160  # 10 ms
rms = np.array([np.sqrt(np.mean(x[i:i+H]**2)) for i in range(0, len(x)-H, H)]); db = 20*np.log10(rms+1e-9)
W = json.load(open("work/words.json"))
def quiet(a, b):
    """lowest-energy 10 ms frame in [a,b] (smoothed over 50 ms)"""
    i0, i1 = int(a*100), int(b*100)
    seg = np.convolve(db[i0:i1], np.ones(5)/5, mode="same")
    k = int(np.argmin(seg)); return (i0+k)/100, float(seg[k])
def onset(t, back=0.4, thr=None):
    """first frame >= thr dB going forward from t-back, where thr = floor+12"""
    i0 = int((t-back)*100); seg = db[i0:int((t+0.3)*100)]
    floor = np.percentile(db[i0:i0+60], 10); thr = thr or floor + 14
    for k, v in enumerate(seg):
        if v > thr: return (i0+k)/100, floor
    return t, floor
def offset(t, fwd=0.4):
    i0 = int((t-0.2)*100); seg = db[i0:int((t+fwd)*100)]
    floor = np.percentile(db[int(t*100):int((t+fwd)*100)], 10); thr = floor + 14
    last = None
    for k, v in enumerate(seg):
        if v > thr: last = (i0+k)/100
    return last, floor
if __name__ == "__main__":
    for t in map(float, sys.argv[1:]):
        print(t, "quiet", quiet(t-0.3, t+0.3), "onset", onset(t), "offset", offset(t))
