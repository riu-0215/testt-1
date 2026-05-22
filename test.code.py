import pygame
import sys

# Pygameの初期化
pygame.init()

# 画面設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("横スクロールゲームの基本")

# 色の定義
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
SKY_BLUE = (135, 206, 235)
MIDNIGHT_BLUE = (25, 25, 112)
DARK_GREEN = (0, 100, 0)
YELLOW = (255, 255, 0)

# プレイヤーの設定
player_rect = pygame.Rect(100, 500, 50, 50)
player_speed = 5
player_vel_y = 0  # 垂直方向の速度
jump_power = -15  # ジャンプ力
gravity = 0.8    # 重力
is_jumping = False # ジャンプ中かどうかの判定
is_night = False   # 夜かどうか

# スクロール変数
scroll_x = 0

clock = pygame.time.Clock()

while True:
    # 1. イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:  # 1キーで昼夜切り替え
                is_night = not is_night

    # 2. プレイヤーの移動
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_rect.x -= player_speed
    if keys[pygame.K_RIGHT]:
        player_rect.x += player_speed

    # ジャンプ処理
    if keys[pygame.K_SPACE] and not is_jumping:
        player_vel_y = jump_power
        is_jumping = True

    # 重力の適用
    player_vel_y += gravity
    player_rect.y += player_vel_y

    # 地面との当たり判定 (簡易版)
    if player_rect.y >= 500:
        player_rect.y = 500
        player_vel_y = 0
        is_jumping = False

    # 3. カメラの追従 (スクロール計算)
    # プレイヤーが画面の中央に来るようにスクロール値を調整
    scroll_x += (player_rect.x - scroll_x - SCREEN_WIDTH // 2) / 10

    # 4. 描画
    if is_night:
        screen.fill(MIDNIGHT_BLUE)
        # 月の描画 (白い円に背景色を重ねて三日月風にする)
        pygame.draw.circle(screen, WHITE, (700, 80), 40)
        pygame.draw.circle(screen, MIDNIGHT_BLUE, (720, 80), 35)
    else:
        screen.fill(SKY_BLUE)
        # 太陽の描画
        pygame.draw.circle(screen, YELLOW, (700, 80), 40)

    # 雲の描画 (パララックス効果: スクロール速度を遅くして遠くに見せる)
    for i in range(5):
        cloud_x = (i * 400 - scroll_x * 0.3) % (SCREEN_WIDTH + 400) - 200
        pygame.draw.circle(screen, WHITE, (int(cloud_x), 150), 30)
        pygame.draw.circle(screen, WHITE, (int(cloud_x) + 30, 150), 40)
        pygame.draw.circle(screen, WHITE, (int(cloud_x) + 60, 150), 30)

    # 地面の描画 (例としていくつも並べる)
    for i in range(-20, 100):
        ground_color = DARK_GREEN if is_night else GREEN
        # スクロール分だけ座標をずらして描画
        pygame.draw.rect(screen, ground_color, (i * 100 - scroll_x, 550, 101, 50))

    # プレイヤーの描画
    # プレイヤー自身の座標もスクロール分ずらす
    display_pos_x = player_rect.x - scroll_x
    pygame.draw.rect(screen, BLUE, (display_pos_x, player_rect.y, player_rect.width, player_rect.height))

    # 画面更新
    pygame.display.flip()
    
    # フレームレート固定
    clock.tick(60)