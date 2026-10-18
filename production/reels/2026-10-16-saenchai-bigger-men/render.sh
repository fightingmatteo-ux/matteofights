# Render one or more hook variants at low load. Usage: bash render.sh B   (one at a time on Matteo's PC)
cd "$(dirname "$0")"
R=../../../media/2026-10-16-saenchai-bigger-men/renders
L=$R/render_bc.log; : > $L
for V in "$@"; do
  python -P make_broll.py $V >/dev/null && python -P build_variant.py $V | tail -1 >> $L
  npx --yes hyperframes@0.8.147 render -q delivery -w 2 -o $R/saenchai-$V.mp4 2>&1 | grep -E "rendered in|Render failed|rror" >> $L
  ffmpeg -loglevel error -y -i $R/saenchai-$V.mp4 -c:v libx264 -crf 22 -preset slow -c:a copy -movflags +faststart $R/saenchai-bigger-men-$V.mp4 && echo "phone $V ok" >> $L
done
echo ALLDONE >> $L
