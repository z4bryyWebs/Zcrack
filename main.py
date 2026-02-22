import pygame
import sys
import random
import time
import math
from collections import deque

# zcrack by zabry0 - Fullscreen sci-fi hacking loader & terminal demo
# Run: python main.py

pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
FPS = 60

# Colors
BLACK = (0, 0, 0)
GREEN = (80, 255, 140)
DARK_GREEN = (8, 28, 8)
CYAN = (80, 220, 255)
WHITE = (230, 230, 230)
GRAY = (60, 60, 60)
ACCENT = (120, 255, 200)

SYSTEM_NAME = "zcrack by zabry0"

# Simulated system lines for the terminal phase
SYSTEM_LINES = [
    "Initializing network stack...",
    "Establishing encrypted tunnel...",
    "Bypassing firewall rules...",
    "Scanning ports 1-65535...",
    "Exploit vector found: CVE-20XX-XXXX",
    "Uploading payload...",
    "Privilege escalation successful.",
    "Mounting virtual file system...",
    "Reading /etc/passwd...",
    "Brute-force keyspace: 43%",
    "Decrypting archive...",
    "Connection stable. Latency: {}ms",
    "Packet capture running...",
    "Access token: {}",
    "Wiping traces...",
    "Process monitor: OK",
    "Kernel hooks: installed",
    "Persistence: scheduled task created",
    "Data exfiltration: queued",
]

# Helper to render text
def draw_text(surf, text, font, color, x, y, center=False):
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surf.blit(img, rect)


class Skull:
    """Cyberpunk cyber-skull: matte ceramic, glowing teal circuitry, hinged jaw, volumetric mouth glow,
    animated circuit traces and tiny moving data particles. Designed to look cinematic in 2D.
    """
    def __init__(self, size=300):
        self.size = int(size)
        self.surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.t = 0.0
        # particle traces traveling through cheekbones
        self.particles = []
        for _ in range(60):
            self._spawn_particle()
        # precompute some cheekbone paths (relative coordinates)
        s = self.size
        self.cheek_paths = [
            [(int(s*0.28), int(s*0.55)), (int(s*0.45), int(s*0.48)), (int(s*0.6), int(s*0.55))],
            [(int(s*0.3), int(s*0.62)), (int(s*0.48), int(s*0.56)), (int(s*0.68), int(s*0.62))]
        ]

    def _spawn_particle(self):
        s = self.size
        # choose a random path and offset along it
        path_idx = random.randrange(len(self.cheek_paths) if hasattr(self, 'cheek_paths') else 2)
        pos = random.random()
        speed = random.uniform(0.2, 1.4)
        life = random.uniform(1.2, 4.0)
        col = (80, 255, 200)
        self.particles.append({'path': path_idx, 'pos': pos, 'speed': speed, 'life': life, 'age': random.random()*life, 'col': col})

    def step(self, dt):
        self.t += dt
        # update particles
        for p in self.particles:
            p['age'] += dt * p['speed']
            if p['age'] > p['life']:
                # respawn
                p['age'] = 0.0
                p['pos'] = 0.0
                p['speed'] = random.uniform(0.4, 1.6)
                p['life'] = random.uniform(1.2, 4.0)
        # occasionally add extra particles
        if random.random() < dt * 6 and len(self.particles) < 120:
            self._spawn_particle()

    def _draw_bloom(self, surf, amount=3, intensity=48):
        # crude bloom by scaling down/up and additive-blitting
        w, h = surf.get_size()
        glow = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(amount):
            factor = 1.0 - (i / (amount + 1)) * 0.4
            sw = max(1, int(w * factor))
            sh = max(1, int(h * factor))
            tmp = pygame.transform.smoothscale(surf, (sw, sh))
            tmp = pygame.transform.smoothscale(tmp, (w, h))
            tmp.set_alpha(int(intensity / (i + 1)))
            glow.blit(tmp, (0, 0), special_flags=pygame.BLEND_ADD)
        return glow

    def draw(self, target_surf, x, y, blink=False, alpha=255):
        s = self.surface
        s.fill((0, 0, 0, 0))
        cx, cy = self.size // 2, self.size // 2

        # base skull silhouette (matte ceramic)
        skull_color = (10, 10, 12, alpha)
        cheek_color = (22, 22, 24, alpha)
        pygame.draw.ellipse(s, skull_color, (cx - 88, cy - 110, 176, 200))  # cranium
        pygame.draw.rect(s, cheek_color, (cx - 70, cy + 6, 140, 78), border_radius=18)  # upper jaw block

        # eye sockets - deep recessed with inner teal rim
        eye_w, eye_h = int(self.size*0.12), int(self.size*0.16)
        eye_x = int(self.size*0.22)
        eye_y = cy - 36
        left_eye = pygame.Rect(cx - eye_x - eye_w//2, eye_y - eye_h//2, eye_w, eye_h)
        right_eye = pygame.Rect(cx + eye_x - eye_w//2, eye_y - eye_h//2, eye_w, eye_h)
        pygame.draw.ellipse(s, (6,6,8,alpha), left_eye)
        pygame.draw.ellipse(s, (6,6,8,alpha), right_eye)
        # inner glowing circuitry rims
        rim_color = (20, 200, 170, int(alpha*0.9))
        pygame.draw.ellipse(s, rim_color, left_eye.inflate(8,8), 2)
        pygame.draw.ellipse(s, rim_color, right_eye.inflate(8,8), 2)

        # nasal cavity
        pygame.draw.polygon(s, (4,4,6,alpha), [(cx-8, cy-8), (cx+8, cy-8), (cx, cy+8)])

        # upper jaw specular highlights
        hl = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.arc(hl, (80,90,100,40), (cx-100, cy-130, 200, 220), math.radians(200), math.radians(340), 6)
        hl = pygame.transform.smoothscale(hl, (self.size, self.size))
        s.blit(hl, (0,0), special_flags=pygame.BLEND_ADD)

        # hinged jaw rotation (simple visual: shift/rotate lower rect)
        jaw_open = 0.18 + 0.18 * (0.5 + 0.5 * math.sin(self.t * 1.6))  # 0..0.36
        jaw_angle = jaw_open * 28  # degrees
        jaw = pygame.Surface((int(self.size*0.62), int(self.size*0.28)), pygame.SRCALPHA)
        jaw.fill((0,0,0,0))
        # jaw shape
        pygame.draw.rect(jaw, cheek_color, (0, 0, jaw.get_width(), jaw.get_height()), border_radius=12)
        # teeth hint lines
        for i in range(5):
            xoff = 10 + i * (jaw.get_width() // 5)
            pygame.draw.line(jaw, (30,30,30,alpha), (xoff, jaw.get_height()//2), (xoff+12, jaw.get_height()//2), 2)
        # rotate jaw around left center
        jaw_rot = pygame.transform.rotozoom(jaw, -jaw_angle, 1.0)
        jr = jaw_rot.get_rect(center=(cx, cy + 60 + int(jaw_open*30)))
        s.blit(jaw_rot, jr)

        # mouth glow (misty neon-green) emitted from jaw gap
        glow_s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        mg_color = (40, 255, 120, 40)
        for i in range(6):
            r = int(self.size*0.12 + i*18 + jaw_open*40)
            alpha_g = max(6, 70 - i*10)
            pygame.draw.ellipse(glow_s, (40, 255, 120, alpha_g), (cx - r, cy + 20 - i*6, r*2, int(r*0.8)))
        # soft vertical mist
        for i in range(40):
            rx = random.randint(cx - 60, cx + 60)
            ry = random.randint(cy + 20, cy + 140)
            rad = random.randint(2, 6)
            pygame.draw.circle(glow_s, (40, 255, 120, 6), (rx, ry), rad)
        # subtle glyph-like streams
        glyphs = "▦▧▩▨◆◈◉♢"
        font = pygame.font.SysFont('consolas', int(self.size*0.05))
        for i in range(6):
            tx = cx + random.randint(-int(self.size*0.18), int(self.size*0.18))
            ty = cy + 10 + i*18 + int((math.sin(self.t*3+i)*8))
            ch = random.choice(glyphs)
            txt = font.render(ch, True, (30,220,160, 40))
            glow_s.blit(txt, (tx, ty))
        s.blit(glow_s, (0,0), special_flags=pygame.BLEND_ADD)

        # circuitry traces (animated fine lines)
        trace_color = (60, 230, 190)
        for path in getattr(self, 'cheek_paths', []):
            # draw smooth cubic-like trace by interpolating points
            pts = path
            for i in range(len(pts)-1):
                (x1,y1) = pts[i]
                (x2,y2) = pts[i+1]
                steps = max(8, int(self.size*0.02))
                for t in range(steps):
                    u = t / float(steps)
                    # small oscillation to look electronic and moving
                    ox = int(6 * math.sin(self.t*3 + u*8 + i))
                    oy = int(4 * math.cos(self.t*2 + u*6 + i))
                    px = int((1-u)*x1 + u*x2) + ox
                    py = int((1-u)*y1 + u*y2) + oy
                    col = (int(trace_color[0] * (0.6+0.4*u)), int(trace_color[1] * (0.6+0.4*u)), int(trace_color[2] * (0.6+0.4*u)))
                    s.set_at((max(0,min(self.size-1, px)), max(0,min(self.size-1, py))), col)

        # small moving particles along cheek paths
        for p in self.particles:
            path = self.cheek_paths[p['path'] % len(self.cheek_paths)]
            # simple linear interpolation along path segments depending on p['age']/p['life']
            u = (p['age'] % p['life']) / p['life']
            # choose segment
            seg = int(u * (len(path)-1))
            su = (u*(len(path)-1)) - seg
            (ax,ay) = path[seg]
            (bx,by) = path[min(seg+1, len(path)-1)]
            px = int((1-su)*ax + su*bx + math.sin(self.t*6 + p['age']*4)*3)
            py = int((1-su)*ay + su*by + math.cos(self.t*5 + p['age']*3)*2)
            age_ratio = p['age'] / p['life']
            col = (int(80 + 175*age_ratio), int(200 + 55*age_ratio), int(160 + 80*age_ratio))
            pygame.draw.circle(s, col + (180,), (px, py), max(1, int(self.size*0.006)))

        # rim lighting and specular highlights (high-contrast)
        rim = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.ellipse(rim, (20,60,60,40), (cx-100, cy-130, 200, 220), 6)
        pygame.draw.ellipse(rim, (10,30,30,20), (cx-60, cy-100, 120, 160), 3)
        s.blit(rim, (0,0), special_flags=pygame.BLEND_ADD)

        # volumetric backlight (soft circle behind skull)
        back = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        for i in range(6):
            c = max(6, 120 - i*18)
            pygame.draw.ellipse(back, (10, 120, 100, c), (cx - int(self.size*0.9) - i*8, cy - int(self.size*0.9) - i*8, int(self.size*1.8) + i*16, int(self.size*1.8) + i*16))
        back = pygame.transform.smoothscale(back, (self.size, self.size))

        # combine glow/bloom
        glow = self._draw_bloom(s, amount=3, intensity=36)
        combined = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        combined.blit(back, (0,0), special_flags=pygame.BLEND_ADD)
        combined.blit(s, (0,0))
        combined.blit(glow, (0,0), special_flags=pygame.BLEND_ADD)

        # final blit scaled/wobble for slight camera depth simulation
        wobble = 1 + 0.005 * math.sin(self.t * 4)
        scaled = pygame.transform.smoothscale(combined, (int(self.size * wobble), int(self.size * wobble)))
        rect = scaled.get_rect(center=(x, y))
        # slight depth-of-field blur: draw faint blurred copy behind
        bg = pygame.transform.smoothscale(combined, (int(self.size * (wobble*0.98)), int(self.size * (wobble*0.98))))
        bg = pygame.transform.smoothscale(bg, (rect.width, rect.height))
        bg.set_alpha(40)
        target_surf.blit(bg, bg.get_rect(center=(x+2, y+4)))
        target_surf.blit(scaled, rect)


def cinematic_loader(screen, clock, big_font, med_font):
    progress = 0.0
    t_start = time.time()
    last_flash = 0
    flash_on = False

    flicker = 0
    skull = Skull(260)
    blink_timer = 0
    blink_state = False

    while progress < 100:
        dt = clock.tick(FPS) / 1000.0
        skull.step(dt)
        blink_timer += dt
        if blink_timer > random.uniform(0.4, 1.6):
            blink_state = True
            blink_timer = 0
        else:
            blink_state = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        elapsed = time.time() - t_start
        base_speed = 18.0
        ease = (1 - (progress / 100.0)) ** 1.5
        jitter = random.uniform(-0.8, 1.6)
        progress += max(0.5, base_speed * ease * dt + jitter * dt)
        progress = min(progress, 100.0)

        flicker = random.randint(-4, 4)
        if time.time() - last_flash > 0.12:
            flash_on = not flash_on
            last_flash = time.time()

        # background grid
        screen.fill((2, 4, 6))
        grid_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        step = 36
        for gx in range(0, WIDTH, step):
            pygame.draw.line(grid_surf, (0, 40, 30, 18), (gx, 0), (gx, HEIGHT))
        for gy in range(0, HEIGHT, step):
            pygame.draw.line(grid_surf, (0, 40, 30, 18), (0, gy), (WIDTH, gy))
        screen.blit(grid_surf, (0, 0))

        # header
        draw_text(screen, SYSTEM_NAME.upper(), med_font, ACCENT, WIDTH // 2, 60, center=True)

        # cinematic progress panel
        panel_w, panel_h = WIDTH * 0.6, 48
        panel_x = (WIDTH - panel_w) // 2
        panel_y = HEIGHT // 2 - 30
        pygame.draw.rect(screen, (6, 12, 10), (panel_x - 6, panel_y - 6, panel_w + 12, panel_h + 12), border_radius=10)
        pygame.draw.rect(screen, (0, 0, 0), (panel_x, panel_y, panel_w, panel_h), border_radius=8)

        # fill
        fill_w = (progress / 100.0) * panel_w
        inner_rect = pygame.Rect(panel_x, panel_y, max(0, fill_w + flicker), panel_h)
        pygame.draw.rect(screen, DARK_GREEN, inner_rect, border_radius=8)

        # sci-fi scan sweep
        sweep_w = int(panel_w * 0.12)
        sweep_x = int((time.time() * 250) % (panel_w + sweep_w)) - sweep_w
        s = pygame.Surface((sweep_w, panel_h), pygame.SRCALPHA)
        s.fill((0, 255, 160, 20))
        screen.blit(s, (panel_x + sweep_x, panel_y))

        # percentage
        pct_text = f"{int(progress)}%"
        draw_text(screen, pct_text, big_font, CYAN if flash_on else GREEN, WIDTH // 2, panel_y + panel_h + 50, center=True)

        # skull to left
        skull.draw(screen, WIDTH // 2 - int(panel_w * 0.55), HEIGHT // 2 - 10, blink_state, alpha=200)

        # small logs
        draw_text(screen, f"Elapsed: {int(elapsed)}s", med_font, GRAY, WIDTH - 220, 24)
        draw_text(screen, "Authenticating modules...", med_font, GRAY, panel_x + 12, panel_y - 56)

        # glitch specks
        for _ in range(8):
            gx = random.randint(int(panel_x), int(panel_x + panel_w))
            gy = random.randint(int(panel_y), int(panel_y + panel_h))
            pygame.draw.rect(screen, (random.randint(50, 120), 255, random.randint(100, 220)), (gx, gy, 2, 1))

        pygame.display.flip()

    # ACCESS GRANTED cinematic
    for alpha in range(0, 256, 5):
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        screen.fill((2, 4, 6))
        draw_text(screen, "ACCESS GRANTED", big_font, (0, 255, 160), WIDTH // 2, HEIGHT // 2 - 60, center=True)
        draw_text(screen, SYSTEM_NAME.upper(), med_font, ACCENT, WIDTH // 2, HEIGHT // 2 + 10, center=True)
        # skull pulse
        s = Skull(300)
        s.t = time.time()
        s.draw(screen, WIDTH // 2 + 260, HEIGHT // 2 - 40, blink=True, alpha=220)
        pygame.display.flip()

    time.sleep(0.3)

    # Welcome typing
    welcome = f"WELCOME, zabry0"
    disp = ""
    for ch in welcome:
        disp += ch
        clock.tick(18)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        screen.fill((0, 0, 0))
        draw_text(screen, "ACCESS GRANTED", big_font, (0, 200, 120), WIDTH // 2, HEIGHT // 2 - 120, center=True)
        draw_text(screen, disp, med_font, CYAN, WIDTH // 2, HEIGHT // 2 + 10, center=True)
        pygame.display.flip()

    time.sleep(0.6)


class MatrixRain:
    def __init__(self, cols, rows, font_height):
        self.drops = [random.randint(-rows, 0) for _ in range(cols)]
        self.cols = cols
        self.rows = rows
        self.font_height = font_height
        self.chars = [chr(i) for i in range(33, 127)]

    def step(self):
        for i in range(self.cols):
            if random.random() > 0.975:
                self.drops[i] = 0
            else:
                self.drops[i] += 1

    def draw(self, surf, font):
        for i, drop in enumerate(self.drops):
            x = i * (self.font_height // 1)
            for j in range(drop):
                if j > self.rows:
                    continue
                y = j * self.font_height
                ch = random.choice(self.chars) if random.random() > 0.9 else ' '
                color = (180, 255, 180) if j == drop - 1 else (20, 120, 40)
                img = font.render(ch, True, color)
                surf.blit(img, (x, y))


def hacking_screen(screen, clock, small_font, mono_font):
    buffer = deque(maxlen=400)
    last_add = 0
    add_interval = 0.14

    font_h = mono_font.get_height()
    cols = max(10, WIDTH // (font_h - 2))
    rows = HEIGHT // font_h + 2
    rain = MatrixRain(cols, rows, font_h)

    skull = Skull(220)
    last_time = time.time()

    cmd_template = "> running exploit --target 192.168.1.{}"
    typing = ""
    typing_target = None
    typing_idx = 0
    typing_speed = 0.02
    typing_last = time.time()

    while True:
        dt = clock.tick(FPS) / 1000.0
        skull.step(dt)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_c:
                    buffer.clear()

        now = time.time()
        if now - last_add > add_interval:
            last_add = now
            line = random.choice(SYSTEM_LINES)
            if "Latency" in line:
                line = line.format(random.randint(5, 250))
            if "Access token" in line:
                tok = ''.join(random.choice('0123456789ABCDEF') for _ in range(16))
                line = line.format(tok)
            if "Brute-force keyspace" in line:
                line = line.replace('43%', f"{random.randint(40, 99)}%")
            timestamp = time.strftime("%H:%M:%S")
            buffer.append(f"[{timestamp}] {line}")

        if typing_target is None and random.random() < 0.012:
            typing_target = cmd_template.format(random.randint(2, 250))
            typing = ""
            typing_idx = 0

        if typing_target is not None and time.time() - typing_last > typing_speed:
            typing_last = time.time()
            if typing_idx < len(typing_target):
                typing += typing_target[typing_idx]
                typing_idx += 1
            else:
                buffer.append(f"> {typing} -- status: OK")
                typing_target = None

        if random.random() > 0.6:
            rain.step()

        # draw background
        screen.fill((2, 6, 8))
        # subtle scanlines
        scan = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(0, HEIGHT, 4):
            scan.fill((0, 0, 0, 8), rect=(0, i, WIDTH, 2))
        screen.blit(scan, (0, 0))

        # left: matrix rain panel
        left_w = WIDTH // 3
        left_rect = pygame.Rect(20, 20, left_w - 40, HEIGHT - 80)
        pygame.draw.rect(screen, (0, 0, 0, 40), left_rect, border_radius=8)
        matrix_surf = pygame.Surface((left_rect.width, left_rect.height), pygame.SRCALPHA)
        matrix_surf.fill((0, 0, 0, 0))
        rain.draw(matrix_surf, mono_font)
        screen.blit(matrix_surf, (left_rect.x + 10, left_rect.y + 10))

        # right: terminal
        right_x = left_w + 40
        draw_text(screen, f"| {SYSTEM_NAME} |", small_font, ACCENT, right_x, 24)
        y = 64
        for line in list(buffer)[-30:]:
            draw_text(screen, line, small_font, GREEN, right_x, y)
            y += small_font.get_height() + 3

        # skull overlay on right
        skull.draw(screen, right_x + 520, HEIGHT // 2 - 30, blink=(int(time.time() * 2) % 2 == 0), alpha=200)

        # typed command display
        bottom_y = HEIGHT - 80
        if typing_target is not None:
            draw_text(screen, typing, med_font if 'med_font' in globals() else small_font, CYAN, right_x, bottom_y)
            if int(time.time() * 2) % 2 == 0:
                cursor_x = right_x + mono_font.size(typing)[0] + 8
                pygame.draw.rect(screen, CYAN, (cursor_x, bottom_y + 6, 10, mono_font.get_height() - 6))
        else:
            draw_text(screen, "> _", small_font, CYAN, right_x, bottom_y)

        # HUD footer
        draw_text(screen, "ESC: Quit  |  C: Clear logs", small_font, GRAY, right_x, HEIGHT - 40)

        pygame.display.flip()


if __name__ == '__main__':
    # fullscreen window
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption(SYSTEM_NAME)
    clock = pygame.time.Clock()

    # fonts
    try:
        big_font = pygame.font.SysFont('consolas', 64)
        med_font = pygame.font.SysFont('consolas', 28)
        small_font = pygame.font.SysFont('consolas', 18)
        mono_font = pygame.font.SysFont('consolas', 16)
    except Exception:
        big_font = pygame.font.Font(None, 72)
        med_font = pygame.font.Font(None, 32)
        small_font = pygame.font.Font(None, 20)
        mono_font = pygame.font.Font(None, 18)

    cinematic_loader(screen, clock, big_font, med_font)
    hacking_screen(screen, clock, small_font, mono_font)