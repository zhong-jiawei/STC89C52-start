import pygame

pygame.init()
W, H = 600, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("移动 + 攻击")
clock = pygame.time.Clock()

# 玩家状态：字典存位置/速度/颜色，dir 记录“朝向”（用于子弹方向，默认朝上）
player = {"x": W // 2, "y": H // 2, "size": 40, "speed": 5,
         "color": (220, 80, 60), "dir": (0, -1)}

# ===== 攻击模块 =====
bullets = []              # 每颗子弹是一个字典：位置 x,y + 方向 dx,dy
BULLET_SPEED = 7          # 子弹速度
SHOOT_COOLDOWN = 250      # 发射冷却（毫秒）
last_shot = 0             # 上次发射的时间戳

# 用“事件”维护的按键状态字典（空格也纳入，用于长按连发）
held = {
    pygame.K_w: False, pygame.K_a: False, pygame.K_s: False, pygame.K_d: False,
    pygame.K_UP: False, pygame.K_DOWN: False, pygame.K_LEFT: False, pygame.K_RIGHT: False,
    pygame.K_SPACE: False,
}

running = True
while running:
    # 1) 处理事件：退出 / 按下 / 抬起
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in held:
                held[event.key] = True
        elif event.type == pygame.KEYUP:
            if event.key in held:
                held[event.key] = False

    # 2) 移动 + 记录朝向（WASD 和方向键都支持）
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
        player["x"] += dx * player["speed"]
        player["y"] += dy * player["speed"]
        player["dir"] = (dx, dy)          # 记下这次移动方向，作子弹朝向

    # 边界限制
    player["x"] = max(0, min(W - player["size"], player["x"]))
    player["y"] = max(0, min(H - player["size"], player["y"]))

    # 3) 长按空格 -> 按冷却节奏持续发射（子弹朝 dir 方向）
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

    # 4) 更新子弹：沿方向飞，飞出屏幕就清理
    for b in bullets:
        b["x"] += b["dx"] * BULLET_SPEED
        b["y"] += b["dy"] * BULLET_SPEED
    bullets = [b for b in bullets if -20 < b["x"] < W + 20 and -20 < b["y"] < H + 20]

    # 5) 画画面
    screen.fill((30, 30, 40))
    pygame.draw.rect(screen, player["color"],
                     (player["x"], player["y"], player["size"], player["size"]))
    for b in bullets:
        pygame.draw.circle(screen, (255, 230, 80), (b["x"] + 3, b["y"] + 3), 4)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
