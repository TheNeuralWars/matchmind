"""Assemble the < 2:00 1080p demo draft from media/ clips, docs/ stills, VO segments and title cards (ffmpeg, no music)."""
import json, os, subprocess
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); M = os.path.join(R, "media"); T = os.path.join(M, "_build")
FONT_B, FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
V = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0b1020,fps=30,format=yuv420p,setsar=1"
def ff(*a): subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *a], check=True)
def dur(p): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))
def esc(s): return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\u2019")

def card(name, lines, d):
    """lines: [(text, size, y, bold)]"""
    dt = ",".join(f"drawtext=fontfile={FONT_B if b else FONT}:text='{esc(t)}':fontsize={s}:fontcolor=white:x=(w-text_w)/2:y={y}" for t, s, y, b in lines)
    out = os.path.join(T, name + ".mp4")
    ff("-f", "lavfi", "-i", f"color=c=0x0b1020:s=1920x1080:d={d}:r=30", "-vf", dt + ",format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out)
    return out

def clip(name, src, start, d):
    out = os.path.join(T, name + ".mp4"); have = dur(src) - start
    vf = V + (f",tpad=stop_mode=clone:stop_duration={d - have + 0.1:.2f}" if have < d else "")
    ff("-ss", f"{start}", "-i", src, "-t", f"{d}", "-an", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out)
    return out

def still(name, img, d, pan=False):
    out = os.path.join(T, name + ".mp4"); n = int(d * 30)
    if pan:   # tall image: scroll top -> bottom
        vf = f"scale=1920:-2,crop=1920:1080:0:'(ih-1080)*min(1,t/{d})',fps=30,format=yuv420p,setsar=1"
        ff("-loop", "1", "-i", img, "-t", f"{d}", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out)
    else:     # gentle zoom
        vf = f"scale=3840:-2,zoompan=z='1+0.06*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1920x1080:fps=30,{V}"
        ff("-loop", "1", "-i", img, "-frames:v", f"{n}", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out)
    return out

def cat(parts, out):
    lst = os.path.join(T, out + ".txt")
    with open(lst, "w") as f: f.writelines(f"file '{p}'\n" for p in parts)
    o = os.path.join(T, out + ".mp4"); ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", o); return o

def main():
    os.makedirs(T, exist_ok=True)
    vo = {k: os.path.join(M, "vo", k + ".wav") for k in ("s1", "s2", "s3", "s4", "s5", "s6", "s7")}
    L = {k: dur(p) + 0.6 for k, p in vo.items()}
    c = lambda f: os.path.join(M, f)
    segs = [  # (video file, vo key or None, seconds)
        (card("title", [("MatchMind", 120, 380, True), ("Every fan, their own match.", 54, 540, False),
                        ("Synthetic football events → explainable, personalised match intelligence", 34, 650, False)], 3.5), None, 3.5),
        (clip("s1", c("split-analyst-en_casual-it.mp4"), 1.0, L["s1"]), "s1", L["s1"]),
        (clip("s2", c("term-dataset.mp4"), 0.0, L["s2"]), "s2", L["s2"]),
        (clip("s3", c("analyst-es.mp4"), 30.0, L["s3"]), "s3", L["s3"]),
        (cat([clip("s4a", c("casual-it-NOR.mp4"), 39.0, L["s4"] - 4.5), clip("s4b", c("split-analyst-en_casual-it.mp4"), 55.4, 4.5)], "s4"), "s4", L["s4"]),
        (still("s5", os.path.join(R, "docs", "cue-json.png"), L["s5"]), "s5", L["s5"]),
        (cat([still("s6a", os.path.join(R, "docs", "architecture.png"), 6.5, pan=True), clip("s6b", c("term-mcp.mp4"), 0.0, L["s6"] - 6.5)], "s6"), "s6", L["s6"]),
        (card("end", [("Try it: theneuralwars.github.io/matchmind", 56, 360, True), ("Code: github.com/TheNeuralWars/matchmind", 44, 470, False),
                      ("MCP server · Microsoft Agent Framework adapter · Azure AI Foundry-ready narrator", 32, 590, False),
                      ("All players, clubs and data are synthetic. No real footage.", 28, 700, False)], L["s7"] + 1.5), "s7", L["s7"] + 1.5),
    ]
    parts = []
    for i, (v, k, d) in enumerate(segs):
        o = os.path.join(T, f"seg{i}.mp4")
        a = ["-f", "lavfi", "-t", f"{d}", "-i", "anullsrc=r=44100:cl=stereo"] if not k else ["-i", vo[k]]
        ff("-i", v, *a, "-filter_complex", f"[1:a]aresample=44100,aformat=channel_layouts=stereo,adelay=250|250,apad,atrim=0:{d}[a]",
           "-map", "0:v", "-map", "[a]", "-t", f"{d}", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", o)
        parts.append(o)
    lst = os.path.join(T, "all.txt")
    with open(lst, "w") as f: f.writelines(f"file '{p}'\n" for p in parts)
    out = os.path.join(M, "matchmind_demo_v1.mp4")
    ff("-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out)
    print(json.dumps({"out": out, "seconds": round(dur(out), 2)}))

if __name__ == "__main__": main()
