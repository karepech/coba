import requests
import re

API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
FALLBACK_MP4 = "http://127.0.0.1/dummy.mp4"

def generate_live():
    print("Mengambil data Live & Upcoming dari API...")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(API_URL, headers=headers, timeout=20)
        content = response.text.replace('\r', '').strip()
        
        live_list = ["#EXTM3U\n"]
        upcoming_list = ["#EXTM3U\n"]
        
        c_live = c_upc = 0
        raw_blocks = re.split(r'\n(?=#EXTINF)', content)
        
        for block in raw_blocks:
            if not block.startswith("#EXTINF"): continue
            
            m_group = re.search(r'group-title="([^"]+)"', block, re.IGNORECASE)
            group = m_group.group(1).strip() if m_group else "Uncategorized"
            group_lower = group.lower()
            
            is_upcoming = "upcoming" in group_lower or "mendatang" in group_lower
            is_live = any(x in group_lower for x in ["live", "tv", "nasional", "sport"])
            
            if not is_live and not is_upcoming:
                continue
                
            lines = block.strip().split('\n')
            extinf_line = lines[0]
            other_tags = [l for l in lines[1:] if l.startswith("#")]
            url_line = next((l for l in lines if l.startswith("http")), None)
            
            # --- PENANGANAN FALLBACK UPCOMING ---
            if is_upcoming and not url_line:
                out_block = extinf_line + "\n"
                if other_tags: out_block += "\n".join(other_tags) + "\n"
                out_block += FALLBACK_MP4 + "\n\n"
                upcoming_list.append(out_block)
                c_upc += 1
                continue
                
            if not url_line: continue
            
            # --- MAGIC: MERAKIT DASH & DRM DENGAN STRING REPLACEMENT ---
            dash_url = url_line.replace(".m3u8", ".mpd").replace("type=hls", "type=dash")
            drm_url = url_line.replace("index.m3u8", "index.php").replace("type=hls", "type=drm")
            
            out_block = extinf_line + "\n"
            if other_tags: out_block += "\n".join(other_tags) + "\n"
            out_block += url_line + "\n"
            
            out_block += extinf_line + " (DASH)\n"
            if other_tags: out_block += "\n".join(other_tags) + "\n"
            out_block += "#KODIPROP:inputstream=inputstream.adaptive\n"
            out_block += "#KODIPROP:inputstream.adaptive.manifest_type=mpd\n"
            out_block += "#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n"
            out_block += f"#KODIPROP:inputstream.adaptive.license_key={drm_url}\n"
            out_block += dash_url + "\n\n"
            
            if is_upcoming:
                upcoming_list.append(out_block)
                c_upc += 1
            else:
                live_list.append(out_block)
                c_live += 1
                
        with open("live.m3u", "w", encoding="utf-8") as f: f.writelines(live_list)
        with open("upcoming.m3u", "w", encoding="utf-8") as f: f.writelines(upcoming_list)
        print(f"Sukses! Live: {c_live} | Upcoming: {c_upc}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    generate_live()
