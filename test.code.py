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

# プレイヤーの設定
player_rect = pygame.Rect(100, 500, 50, 50)
player_speed = 5

# スクロール変数
scroll_x = 0

clock = pygame.time.Clock()

while True:
    # 1. イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # 2. プレイヤーの移動
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_rect.x -= player_speed
    if keys[pygame.K_RIGHT]:
        player_rect.x += player_speed

    # 3. カメラの追従 (スクロール計算)
    # プレイヤーが画面の中央に来るようにスクロール値を調整
    scroll_x += (player_rect.x - scroll_x - SCREEN_WIDTH // 2) / 10

    # 4. 描画
    screen.fill(WHITE)

    # 地面の描画 (例としていくつも並べる)
    for i in range(-10, 20):
        # スクロール分だけ座標をずらして描画
        pygame.draw.rect(screen, GREEN, (i * 100 - scroll_x, 550, 80, 50))

    # プレイヤーの描画
    # プレイヤー自身の座標もスクロール分ずらす
    display_pos_x = player_rect.x - scroll_x
    pygame.draw.rect(screen, BLUE, (display_pos_x, player_rect.y, player_rect.width, player_rect.height))

    # 画面更新
    pygame.display.flip()
    
    # フレームレート固定
    clock.tick(60)