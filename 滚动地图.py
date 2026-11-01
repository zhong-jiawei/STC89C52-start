import pygame

pygame.init()
W, H = 800, 600
TILE = 50                     # 每个瓦片(格子)的边长（像素）
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("瓦片地图：房间 + 门 + 自由进出")
clock = pygame.time.Clock()

# ===== 地图：用嵌套列表表示世界，'#'=墙  '.'=地板 =====
# 这是一个 20x15 的网格：左右两个房间，中间一堵墙，第 7 行留了门(缺口)
raw_map = [
    "####################",   # row0  外层墙
    "#.........#........#",   # row1  左房间 | 墙 | 右房间
    "#.........#........#",   # row2
    "#.........#........#",   # row3
    "#.........#........#",   # row4
    "#.........#........#",   # row5
    "#..................#",   # row6
    "#..................#",   # row7  ★门：这一行整条是地板，左右房间连通
    "#.........#........#",   # row8
    "#.........#........#",   # row9
    "#.........#........#",   # row10
    "#.........#........#",   # row11
    "#.........#........#",   # row12
    "#.........#........#",   # row13
    "####################",   # row14 外层墙
]
MAP_H = len(raw_map)          # 15 行
MAP_W = len(raw_map[0])       # 20 列

# 世界坐标 -> 这一格是墙还是地板
def tile_at(px, py):
    col = px // TILE
    row = py // TILE
    if row < 0 or row >= MAP_H or col < 0 or col >= MAP_W:
        return "#"            # 地图外面一律当墙，防止走出世界
    return raw_map[row][col]

# 矩形(x,y,size) 的四角有没有碰到墙（用来做碰撞）
def rect_hits_wall(x, y, size):
    for cx, cy in [(x, y), (x + size, y), (x, y + size), (x + size, y + size)]:
        if tile_at(cx, cy) == "#":
            return True
    return False

# 玩家：初始在左房间中央
player = {"x": 150, "y": 350, "size": 40, "speed": 3,
         "color": (220, 80, 60), "dir": (0, -1)}

# ===== 攻击模块 =====
bullets = []
BULLET_SPEED = 12
SHOOT_COOLDOWN = 250
last_shot = 0

held = {
    pygame.K_w: False, pygame.K_a: False, pygame.K_s: False, pygame.K_d: False,
    pygame.K_UP: False, pygame.K_DOWN: False, pygame.K_LEFT: False, pygame.K_RIGHT: False,
    pygame.K_SPACE: False,
}

running = True
while running:
    # 1) 事件：维护按键状态
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in held:
                held[event.key] = True
        elif event.type == pygame.KEYUP:
            if event.key in held:
                held[event.key] = False

    # 2) 移动 + 撞墙检测（分轴处理：能贴墙滑动、能从门穿过）
    dx, dy = 0, 0
    if held[pygame.K_a] or held[pygame.K_LEFT]:
        dx -= 1
    if held[pygame.K_d] or held[pygame.K_RIGHT]:
        dx += 1
    if held[pygame.K_w] or held[pygame.K_UP]:
        dy -= 1
    if held[pygame.K_s] or held[pygame.K_DOWN]:
        dy += 1

    if dx != 0 or dy != 0:
        # 先试 X 轴：新位置撞墙就不移动 X
        new_x = player["x"] + dx * player["speed"]
        if not rect_hits_wall(new_x, player["y"], player["size"]):
            player["x"] = new_x
        # 再试 Y 轴：同理
        new_y = player["y"] + dy * player["speed"]
        if not rect_hits_wall(player["x"], new_y, player["size"]):
            player["y"] = new_y
        player["dir"] = (dx, dy)     # 记朝向给子弹

    # 3) 摄像机：让玩家永远在屏幕中央
    cam_x = player["x"] - W // 2 + player["size"] // 2
    cam_y = player["y"] - H // 2 + player["size"] // 2

    # 4) 发射 + 更新子弹（子弹打到墙也消失）
    now = pygame.time.get_ticks()
    if held[pygame.K_SPACE] and now - last_shot >= SHOOT_COOLDOWN:
        cx = player["x"] + player["size"] // 2
        cy = player["y"] + player["size"] // 2
        bullets.append({
            "x": cx + player["dir"][0] * player["size"] // 2 - 3,
            "y": cy + player["dir"][1] * player["size"] // 2 - 3,
            "dx": player["dir"][0],
            "dy": player["dir"][1],
        })
        last_shot = now

    for b in bullets:
        b["x"] += b["dx"] * BULLET_SPEED
        b["y"] += b["dy"] * BULLET_SPEED
    # 两个清理条件：打到墙、或飞出视野
    bullets = [b for b in bullets
               if tile_at(b["x"], b["y"]) != "#"
               and -20 < b["x"] - cam_x < W + 20
               and -20 < b["y"] - cam_y < H + 20]

    # 5) 画：先填背景，再只画“看得见的那几排”瓦片
    screen.fill((20, 20, 28))
    start_col = cam_x // TILE
    end_col = (cam_x + W) // TILE + 1
    start_row = cam_y // TILE
    end_row = (cam_y + H) // TILE + 1
    for row in range(start_row, end_row):
        for col in range(start_col, end_col):
            if 0 <= row < MAP_H and 0 <= col < MAP_W:
                tx = col * TILE - cam_x
                ty = row * TILE - cam_y
                if raw_map[row][col] == "#":
                    pygame.draw.rect(screen, (70, 70, 90), (tx, ty, TILE, TILE))
                else:
                    pygame.draw.rect(screen, (45, 45, 60), (tx, ty, TILE, TILE))

    # 子弹（按摄像机偏移画）
    for b in bullets:
        pygame.draw.circle(screen, (255, 230, 80),
                           (b["x"] - cam_x + 3, b["y"] - cam_y + 3), 4)

    # 玩家永远画在屏幕正中央
    pygame.draw.rect(screen, player["color"],
                     (W // 2 - player["size"] // 2,
                      H // 2 - player["size"] // 2,
                      player["size"], player["size"]))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
