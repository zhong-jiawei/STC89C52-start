import pygame
import random

pygame.init()
W, H = 600, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("自定义墙：大小 + 位置（AABB 碰撞）")
clock = pygame.time.Clock()

# ============ 1) 自定义墙：每面墙是一个字典 ============
#  x, y = 墙左上角在“世界”里的位置（像素）→ 调位置改这里
#  w, h = 墙的宽、高（像素）              → 调大小改这里
#  加一面墙：往列表里加一个字典；删一面墙：删掉对应那行
WORLD_W, WORLD_H = 1200, 900
walls = [
    # —— 外墙：框住整个世界（尺寸由 WORLD_W / WORLD_H 决定）——
    {"x": 0,            "y": 0,             "w": WORLD_W, "h": 20},          # 上边
    {"x": 0,            "y": WORLD_H - 20,  "w": WORLD_W, "h": 20},          # 下边
    {"x": 0,            "y": 0,             "w": 20,      "h": WORLD_H},     # 左边
    {"x": WORLD_W - 20, "y": 0,             "w": 20,      "h": WORLD_H},     # 右边
    # —— 内部墙：下面是“自定义大小和位置”的示例 ——
    {"x": 200, "y": 200, "w": 350, "h": 30},    # 一面横墙：x=200,y=200,宽350高30
    {"x": 700, "y": 150, "w": 30,  "h": 300},   # 一面竖墙：x=700,y=150,宽30高300
    {"x": 300, "y": 550, "w": 200, "h": 30},    # 门：左半
    {"x": 550, "y": 550, "w": 200, "h": 30},    # 门：右半（中间 500~550 留 50px 缺口 = 门）
]

# ============ 2) 玩家 ============
player = {"x": 100, "y": 100, "size": 40, "speed": 3,
          "color": (220, 80, 60), "dir": (0, -1)}

# ============ 2.5) 随机移动的矩形（会与墙碰撞，被挡住；可被子弹消灭）============
ENEMY_SPEED = 2        # 移动时每帧速度（像素/帧，“码”）
ENEMY_MOVE_DIST = 60   # 每次移动要走的总距离（像素）
ENEMY_WAIT = 3000      # 两次移动之间停顿 3000 毫秒（3 秒）
ENEMY_RESPAWN = 2000   # 被消灭后多久重生（毫秒）
enemy = {"x": 600, "y": 400, "size": 36, "color": (90, 200, 120),
         "dx": 0, "dy": 0, "moved": 0, "moving": False, "alive": True}
enemy_wait_until = ENEMY_WAIT        # 开局先停顿 3 秒再动
enemy_respawn_until = 0              # 重生倒计时（alive=False 时计时）

# ============ 3) 攻击模块（子弹打到墙会消失）============
bullets = []
BULLET_SPEED = 12
SHOOT_COOLDOWN = 250
last_shot = 0

held = {
    pygame.K_w: False, pygame.K_a: False, pygame.K_s: False, pygame.K_d: False,
    pygame.K_UP: False, pygame.K_DOWN: False, pygame.K_LEFT: False, pygame.K_RIGHT: False,
    pygame.K_SPACE: False,
}

# ============ 4) 碰撞：玩家矩形 是否 碰到任意一面墙 ============
# 用 pygame.Rect 的 colliderect 做 AABB（轴对齐包围盒）重叠判断
def rect_hits_wall(x, y, size, walls):
    player_rect = pygame.Rect(x, y, size, size)
    for w in walls:
        wall_rect = pygame.Rect(w["x"], w["y"], w["w"], w["h"])
        if player_rect.colliderect(wall_rect):   # 两个矩形有重叠 = 撞墙
            return True
    return False

# 敌人重生：随机挑一个“不在墙里”的位置放下，并重置状态
def respawn_enemy():
    for _ in range(50):                          # 最多试 50 次，避免卡死
        rx = random.randint(40, WORLD_W - 80)
        ry = random.randint(40, WORLD_H - 80)
        if not rect_hits_wall(rx, ry, enemy["size"], walls):
            enemy["x"], enemy["y"] = rx, ry      # 找到安全点，放下敌人
            break
    enemy["alive"] = True
    enemy["moving"] = False
    enemy["moved"] = 0
    enemy["dx"], enemy["dy"] = 0, 0

running = True
while running:
    # 事件：维护按键状态
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in held:
                held[event.key] = True
        elif event.type == pygame.KEYUP:
            if event.key in held:
                held[event.key] = False

    # 移动：分轴处理（撞墙的那根轴不动 → 能贴墙滑动 / 从门穿过）
    dx, dy = 0, 0
    if held[pygame.K_a] or held[pygame.K_LEFT]:  dx -= 1
    if held[pygame.K_d] or held[pygame.K_RIGHT]: dx += 1
    if held[pygame.K_w] or held[pygame.K_UP]:    dy -= 1
    if held[pygame.K_s] or held[pygame.K_DOWN]:  dy += 1

    if dx != 0 or dy != 0:
        new_x = player["x"] + dx * player["speed"]
        if not rect_hits_wall(new_x, player["y"], player["size"], walls):
            player["x"] = new_x
        new_y = player["y"] + dy * player["speed"]
        if not rect_hits_wall(player["x"], new_y, player["size"], walls):
            player["y"] = new_y
        player["dir"] = (dx, dy)     # 记朝向给子弹

    # 摄像机：让玩家永远在屏幕中央（地图动、人不动）
    cam_x = player["x"] - W // 2 + player["size"] // 2
    cam_y = player["y"] - H // 2 + player["size"] // 2

    # 发射 + 更新子弹
    now = pygame.time.get_ticks()

    # 敌人：被消灭 → 等待重生；活着时 停顿3秒→随机方向→每帧2像素走60→再停顿
    if not enemy["alive"]:
        if now >= enemy_respawn_until:        # 时间到，重生
            respawn_enemy()
    elif not enemy["moving"]:
        if now >= enemy_wait_until:                       # 等够了，开始这次移动
            enemy["dx"], enemy["dy"] = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])
            enemy["moved"] = 0
            enemy["moving"] = True
    else:
        new_ex = enemy["x"] + enemy["dx"] * ENEMY_SPEED   # 先算这帧的新位置
        new_ey = enemy["y"] + enemy["dy"] * ENEMY_SPEED
        if not rect_hits_wall(new_ex, new_ey, enemy["size"], walls):
            enemy["x"] = new_ex        # 没撞墙才移动
            enemy["y"] = new_ey
            enemy["moved"] += ENEMY_SPEED
        else:
            enemy["moving"] = False    # 撞墙：本次移动提前结束，进入停顿
            enemy_wait_until = now + ENEMY_WAIT
        if enemy["moved"] >= ENEMY_MOVE_DIST:             # 走满 60 像素 = 移动完成
            enemy["moving"] = False
            enemy_wait_until = now + ENEMY_WAIT           # 再停顿 3 秒

    if held[pygame.K_SPACE] and now - last_shot >= SHOOT_COOLDOWN:
        cx = player["x"] + player["size"] // 2
        cy = player["y"] + player["size"] // 2
        bullets.append({
            "x": cx + player["dir"][0] * player["size"] // 2 - 3,
            "y": cy + player["dir"][1] * player["size"] // 2 - 3,
            "dx": player["dir"][0], "dy": player["dir"][1],
        })
        last_shot = now

    # 更新子弹 + 清理（飞出世界 / 打到墙 / 打中敌人 就消失）
    alive = []
    for b in bullets:
        b["x"] += b["dx"] * BULLET_SPEED
        b["y"] += b["dy"] * BULLET_SPEED
        out_of_world = not (0 <= b["x"] < WORLD_W and 0 <= b["y"] < WORLD_H)
        hit_wall = rect_hits_wall(b["x"], b["y"], 6, walls)   # 复用统一碰撞函数
        # 子弹 6×6 包围盒 是否 与 敌人方块 重叠 → 打中敌人
        hit_enemy = enemy["alive"] and pygame.Rect(b["x"], b["y"], 6, 6).colliderect(
            pygame.Rect(enemy["x"], enemy["y"], enemy["size"], enemy["size"]))
        if hit_enemy:
            enemy["alive"] = False              # 消灭敌人
            enemy_respawn_until = now + ENEMY_RESPAWN   # 隔 2 秒重生
        if not out_of_world and not hit_wall and not hit_enemy:
            alive.append(b)                     # 三不占才保留
    bullets = alive

    # 画：背景
    screen.fill((20, 20, 28))
    # 画墙（世界坐标减 cam → 屏幕坐标）
    for w in walls:
        sx = w["x"] - cam_x
        sy = w["y"] - cam_y
        pygame.draw.rect(screen, (70, 70, 90), (sx, sy, w["w"], w["h"]))
    # 画子弹
    for b in bullets:
        pygame.draw.circle(screen, (255, 230, 80),
                           (b["x"] - cam_x + 3, b["y"] - cam_y + 3), 4)
    # 画敌人（活着才画；世界坐标减 cam，和地图一起滚动；已做碰撞，不会穿墙）
    if enemy["alive"]:
        pygame.draw.rect(screen, enemy["color"],
                         (enemy["x"] - cam_x, enemy["y"] - cam_y,
                          enemy["size"], enemy["size"]))
    # 画玩家（永远中心）
    pygame.draw.rect(screen, player["color"],
                     (W // 2 - player["size"] // 2,
                      H // 2 - player["size"] // 2,
                      player["size"], player["size"]))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
