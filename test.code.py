import pygame
import sys

# Pygameの初期化
pygame.init()

# 画面設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("アクションゲーム試作 - [Space]:Jump [X]:Attack")

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKIN = (255, 220, 180)  # 肌色
SHIRT = (50, 150, 255)  # 服の色
PANTS = (50, 50, 50)    # ズボンの色
GROUND_COLOR = (100, 100, 100)
SWORD_COLOR = (192, 192, 192)
RED = (255, 0, 0)
ENEMY_SKIN = (200, 100, 100) # 敵の肌色
ENEMY_SHIRT = (150, 0, 0) # 敵の服の色
PURPLE = (150, 0, 150) # 遠距離敵の色
GOLD = (255, 215, 0) # ボスの色

import random
import math

class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = 450
        self.speed = 5
        self.vel_y = 0
        self.jump_power = -15
        self.gravity = 0.8
        self.is_jumping = False
        self.walk_cycle = 0  # 歩行アニメーション用のカウンタ
        self.facing_right = True
        self.attack_timer = 0  # 攻撃モーションの持続時間
        self.health = 3        # プレイヤーの体力
        self.invincible_timer = 0 # 被弾後の無敵時間
        self.rect = pygame.Rect(self.x - 10, self.y - 47, 20, 82)

    def update(self, platforms, enemies, projectiles):
        keys = pygame.key.get_pressed()
        moving = False
        
        if keys[pygame.K_LEFT]:
            self.x -= self.speed
            moving = True
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            self.x += self.speed
            moving = True
            self.facing_right = True

        # ジャンプ処理
        if keys[pygame.K_SPACE] and not self.is_jumping:
            self.vel_y = self.jump_power
            self.is_jumping = True

        # 攻撃処理
        if keys[pygame.K_x] and self.attack_timer <= 0:
            self.attack_timer = 15  # 15フレーム攻撃

        if moving:
            self.walk_cycle += 0.15  # 移動中にアニメーションを進める
        else:
            self.walk_cycle = 0  # 止まったら直立

        # 重力の適用
        self.vel_y += self.gravity
        self.y += self.vel_y

        # 攻撃タイマーの更新
        if self.attack_timer > 0:
            self.attack_timer -= 1

        # 無敵タイマーの更新
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        # 画面外に出ないように制限 (左右の壁)
        if self.x < 10: self.x = 10
        if self.x > SCREEN_WIDTH - 10: self.x = SCREEN_WIDTH - 10

        # 自身のRectを更新
        self.rect.x = self.x - 10
        self.rect.y = self.y - 47

        # 敵からの攻撃判定
        if self.invincible_timer <= 0:
            for enemy in enemies:
                # 接近戦の敵(Enemy/Boss)の攻撃判定 (ボスは猶予を増やすため判定フレームを遅らせる)
                hit_frame = 20 if isinstance(enemy, Enemy) else 10
                if isinstance(enemy, (Enemy, Boss)) and enemy.attack_timer == hit_frame:
                    range_w = 40 if isinstance(enemy, Enemy) else 80
                    range_h = 30 if isinstance(enemy, Enemy) else 60
                    enemy_attack_rect = pygame.Rect(
                        enemy.x + (10 if enemy.facing_right else -(range_w + 10)),
                        enemy.y - 25, range_w, range_h
                    )
                    if self.rect.colliderect(enemy_attack_rect):
                        self.take_damage()
                        break
                
                # ボスの地響き攻撃の判定 (地面に接地している場合のみダメージ)
                if isinstance(enemy, Boss) and enemy.shockwave_timer == 200:
                    if not self.is_jumping and self.y >= 500:
                        self.take_damage()

            # 飛び道具(Projectile)の当たり判定
            for proj in projectiles[:]:
                if self.rect.colliderect(proj.rect):
                    self.take_damage()
                    projectiles.remove(proj)
                    break

            # 攻撃の当たり判定 (攻撃開始の特定のフレームで判定)
            if self.attack_timer == 10:
                attack_rect = pygame.Rect(
                    self.x + (10 if self.facing_right else -50),
                    self.y - 25,
                    40,
                    30
                )
                for enemy in enemies:
                    if attack_rect.colliderect(enemy.rect):
                        enemy.health -= 1

        # 当たり判定 (地面とプラットフォーム)
        self.check_collision(platforms)

    def take_damage(self):
        self.health -= 1
        self.invincible_timer = 60  # 約1秒間の無敵時間
        # 被弾時に少し跳ね返る（ノックバック）
        self.vel_y = -10

    def check_collision(self, platforms):
        # 足元（y座標）の判定用仮想Rect
        foot_rect = pygame.Rect(self.x - 10, self.y + 30, 20, 5)
        
        on_platform = False
        for plat in platforms:
            if self.vel_y >= 0 and foot_rect.colliderect(plat):
                # 足元がプラットフォームの上面にある場合
                if self.y + 30 <= plat.top + self.vel_y + 1:
                    self.y = plat.top - 35
                    self.vel_y = 0
                    self.is_jumping = False
                    on_platform = True
                    break # 衝突したらループを抜ける
        # 地面との衝突はplatformsリスト内の地面Rectで処理されるため、個別のy > 500判定は不要

    def draw(self, surface):
        # 無敵時間中は点滅させる
        if self.invincible_timer > 0 and (self.invincible_timer // 5) % 2 == 0:
            return

        dir_mod = 1 if self.facing_right else -1
        swing = math.sin(self.walk_cycle) * 15
        
        # 1. 脚 (左右交互に振る)
        pygame.draw.line(surface, PANTS, (self.x, self.y + 10), (self.x - 8 + swing, self.y + 35), 8)
        pygame.draw.line(surface, PANTS, (self.x, self.y + 10), (self.x + 8 - swing, self.y + 35), 8)

        # 2. 胴体
        pygame.draw.rect(surface, SHIRT, (self.x - 10, self.y - 20, 20, 30), border_radius=5)

        # 3. 腕 (攻撃中と歩行中でポーズを変える)
        if self.attack_timer > 0:
            # 攻撃モーション: 前方に腕を突き出す
            pygame.draw.line(surface, SKIN, (self.x + (10 * dir_mod), self.y - 15), (self.x + (30 * dir_mod), self.y - 5), 5)
            # 剣の描画
            pygame.draw.line(surface, SWORD_COLOR, (self.x + (25 * dir_mod), self.y - 10), (self.x + (50 * dir_mod), self.y - 20), 4)
        else:
            pygame.draw.line(surface, SKIN, (self.x - 10, self.y - 15), (self.x - 10 - (swing * 0.5), self.y + 10), 5)
            pygame.draw.line(surface, SKIN, (self.x + 10, self.y - 15), (self.x + 10 + (swing * 0.5), self.y + 10), 5)

        # 4. 頭
        pygame.draw.circle(surface, SKIN, (int(self.x), int(self.y - 35)), 12)
        # 目 (向きに合わせて位置調整)
        eye_x = self.x + (4 * dir_mod)
        pygame.draw.circle(surface, BLACK, (int(eye_x), int(self.y - 37)), 2)
        pygame.draw.circle(surface, BLACK, (int(eye_x + (4 * dir_mod)), int(self.y - 37)), 2)

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 1
        self.rect = pygame.Rect(x - 10, y - 35, 20, 70)
        self.move_dir = 1
        self.vel_y = 0
        self.attack_timer = 0 # New: for enemy attack animation
        self.facing_right = True # New: for enemy facing direction
        self.chase_speed = 1.5 # New: Speed for chasing the player
        self.attack_range = 50 # New: Range to trigger attack

    def update(self, platforms, player_x): # platforms引数を追加, player_xを追加
        # 重力
        self.vel_y += 0.8
        self.y += self.vel_y

        # Collision with platforms (similar to player)
        foot_rect = pygame.Rect(self.x - 10, self.y + 30, 20, 5) # Assuming similar foot rect as player
        on_platform = False
        for plat in platforms:
            if self.vel_y >= 0 and foot_rect.colliderect(plat):
                if self.y + 30 <= plat.top + self.vel_y + 1:
                    self.y = plat.top - 35 # Adjust based on enemy height
                    self.vel_y = 0
                    on_platform = True
                    break
        
        # 地面との衝突はplatformsリスト内の地面Rectで処理されるため、個別のy > 500判定は不要
        # ただし、念のため画面下部への落下防止
        if self.y > SCREEN_HEIGHT - 65: # 地面Rectのy座標535を考慮
            self.y = SCREEN_HEIGHT - 65 - 35 # 535 - 35 = 500
            self.y = 500
            self.vel_y = 0
        
        # 攻撃中でない場合のみプレイヤーを追いかける
        if self.attack_timer > 0:
            self.attack_timer -= 1
        else:
            # プレイヤーを追いかけるAI
            if player_x < self.x - self.attack_range / 2: # プレイヤーが左にいて、攻撃範囲外
                self.x -= self.chase_speed
                self.facing_right = False
            elif player_x > self.x + self.attack_range / 2: # プレイヤーが右にいて、攻撃範囲外
                self.x += self.chase_speed
                self.facing_right = True
            else: # プレイヤーが攻撃範囲内
                self.attack_timer = 30 # 攻撃モーションを開始

        # 画面外に出ないように制限 (左右の壁)
        if self.x < 10: self.x = 10
        if self.x > SCREEN_WIDTH - 10: self.x = SCREEN_WIDTH - 10

        # 当たり判定用Rectの更新
        self.rect.x = self.x - 10
        self.rect.y = self.y - 35

    def draw(self, surface):
        dir_mod = 1 if self.facing_right else -1
        
        # 敵の描画 (赤色の人型)
        # 1. 脚
        pygame.draw.line(surface, PANTS, (self.x, self.y + 10), (self.x - 8, self.y + 35), 8)
        pygame.draw.line(surface, PANTS, (self.x, self.y + 10), (self.x + 8, self.y + 35), 8)

        # 2. 胴体
        pygame.draw.rect(surface, ENEMY_SHIRT, (self.x - 10, self.y - 20, 20, 30), border_radius=5)

        # 3. 腕 (攻撃中と通常でポーズを変える)
        if self.attack_timer > 0:
            # 攻撃モーション: 前方に腕を突き出す
            pygame.draw.line(surface, ENEMY_SKIN, (self.x + (10 * dir_mod), self.y - 15), (self.x + (30 * dir_mod), self.y - 5), 5)
        else:
            # 通常の腕の位置
            pygame.draw.line(surface, ENEMY_SKIN, (self.x - 10, self.y - 15), (self.x - 18, self.y + 10), 5)
            pygame.draw.line(surface, ENEMY_SKIN, (self.x + 10, self.y - 15), (self.x + 18, self.y + 10), 5)

        # 4. 頭
        pygame.draw.circle(surface, ENEMY_SKIN, (int(self.x), int(self.y - 35)), 12)
        # 目 (向きに合わせて位置調整)
        eye_x = self.x + (4 * dir_mod)
        pygame.draw.circle(surface, BLACK, (int(eye_x), int(self.y - 37)), 2)
        pygame.draw.circle(surface, BLACK, (int(eye_x + (4 * dir_mod)), int(self.y - 37)), 2)

class Projectile:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.speed = 7
        self.vel_x = self.speed * direction
        self.rect = pygame.Rect(x - 5, y - 5, 10, 10)

    def update(self):
        self.x += self.vel_x
        self.rect.x = self.x - 5

    def draw(self, surface):
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), 5)

class RangedEnemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 1
        self.rect = pygame.Rect(x - 10, y - 35, 20, 70)
        self.shoot_timer = 0
        self.facing_right = False
        self.vel_y = 0
        self.retreat_speed = 1 # New: Speed for moving to maintain distance
        self.optimal_distance = 300 # New: Ideal distance from player

    def update(self, player_x, projectiles, platforms): # platforms引数を追加
        # プレイヤーの方向を向く
        self.facing_right = player_x > self.x
        
        # 重力
        self.vel_y += 0.8
        self.y += self.vel_y

        # Collision with platforms (similar to player)
        foot_rect = pygame.Rect(self.x - 10, self.y + 30, 20, 5) # Assuming similar foot rect as player
        on_platform = False
        for plat in platforms:
            if self.vel_y >= 0 and foot_rect.colliderect(plat):
                if self.y + 30 <= plat.top + self.vel_y + 1:
                    self.y = plat.top - 35 # Adjust based on enemy height
                    self.vel_y = 0
                    on_platform = True
                    break
        # 地面との衝突はplatformsリスト内の地面Rectで処理されるため、個別のy > 500判定は不要
        if self.y > SCREEN_HEIGHT - 65: # 地面Rectのy座標535を考慮
            self.y = 500
            self.vel_y = 0
        
        # プレイヤーとの距離を保つAI
        distance_to_player = self.x - player_x
        if abs(distance_to_player) < self.optimal_distance - 50: # プレイヤーが近すぎる場合、後退
            if distance_to_player > 0: # プレイヤーが左にいる場合、右に移動
                self.x += self.retreat_speed
            else: # プレイヤーが右にいる場合、左に移動
                self.x -= self.retreat_speed
        elif abs(distance_to_player) > self.optimal_distance + 50: # プレイヤーが遠すぎる場合、前進
            if distance_to_player > 0: # プレイヤーが左にいる場合、左に移動
                self.x -= self.retreat_speed
            else: # プレイヤーが右にいる場合、右に移動
                self.x += self.retreat_speed
        # else: 最適な距離にいる場合は移動しない

        # 画面外に出ないように制限 (左右の壁)
        if self.x < 10: self.x = 10
        if self.x > SCREEN_WIDTH - 10: self.x = SCREEN_WIDTH - 10

        # 射撃AI (一定間隔で発射)
        self.shoot_timer += 1
        if self.shoot_timer > 90:
            direction = 1 if self.facing_right else -1
            projectiles.append(Projectile(self.x + (20 * direction), self.y - 15, direction))
            self.shoot_timer = 0

        self.rect.x = self.x - 10
        self.rect.y = self.y - 35

    def draw(self, surface):
        dir_mod = 1 if self.facing_right else -1
        pygame.draw.circle(surface, PURPLE, (int(self.x), int(self.y - 35)), 12)
        pygame.draw.rect(surface, (80, 0, 80), (self.x - 10, self.y - 20, 20, 30), border_radius=5)
        pygame.draw.line(surface, PANTS, (self.x, self.y + 10), (self.x - 8, self.y + 35), 8)
        pygame.draw.line(surface, PANTS, (self.x, self.y + 10), (self.x + 8, self.y + 35), 8)
        pygame.draw.line(surface, SKIN, (self.x + (10 * dir_mod), self.y - 15), (self.x + (25 * dir_mod), self.y - 10), 5)
        eye_x = self.x + (4 * dir_mod)
        pygame.draw.circle(surface, BLACK, (int(eye_x), int(self.y - 37)), 2)

class Boss:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.max_health = 20
        self.health = self.max_health
        self.rect = pygame.Rect(x - 30, y - 80, 60, 130)
        self.vel_y = 0
        self.facing_right = False
        self.shockwave_timer = 0
        self.attack_timer = 0
        self.chase_speed = 1.2
        self.attack_range = 100

    def update(self, player_x, projectiles, platforms):
        # 重力と足場判定
        self.vel_y += 0.8
        self.y += self.vel_y
        foot_rect = pygame.Rect(self.x - 30, self.y + 45, 60, 5)
        for plat in platforms:
            if self.vel_y >= 0 and foot_rect.colliderect(plat):
                self.y = plat.top - 50
                self.vel_y = 0
                break
        if self.y > 500: self.y = 500; self.vel_y = 0

        # AI: プレイヤーを追跡
        if self.attack_timer > 0:
            self.attack_timer -= 1
        else:
            if player_x < self.x - self.attack_range/2:
                self.x -= self.chase_speed
                self.facing_right = False
            elif player_x > self.x + self.attack_range/2:
                self.x += self.chase_speed
                self.facing_right = True
            else:
                self.attack_timer = 70 # 強力な攻撃 (予告時間を含めて猶予を増加)

        # 地響き攻撃 (Shockwave) AI
        self.shockwave_timer += 1
        if self.shockwave_timer > 200: # 約3.3秒周期
            self.shockwave_timer = 0

        if self.x < 50: self.x = 50
        if self.x > SCREEN_WIDTH - 50: self.x = SCREEN_WIDTH - 50
        self.rect.x, self.rect.y = self.x - 30, self.y - 80

    def draw(self, surface):
        dir_mod = 1 if self.facing_right else -1
        # 巨大な体
        pygame.draw.rect(surface, (100, 0, 0), (self.x - 30, self.y - 40, 60, 70), border_radius=10)
        # 金色の鎧/装飾
        pygame.draw.rect(surface, GOLD, (self.x - 35, self.y - 45, 70, 20), border_radius=5)
        # 巨大な頭
        pygame.draw.circle(surface, ENEMY_SKIN, (int(self.x), int(self.y - 65)), 25)
        # 王冠
        pygame.draw.polygon(surface, GOLD, [(self.x-20, self.y-85), (self.x, self.y-110), (self.x+20, self.y-85)])
        # 目
        eye_x = self.x + (10 * dir_mod)
        pygame.draw.circle(surface, BLACK, (int(eye_x), int(self.y - 70)), 4)
        
        # 攻撃の予告とエフェクト
        if self.attack_timer > 10:
            # 予告: 赤い枠線で攻撃範囲を表示
            range_w = 80
            atk_x = self.x + (10 if self.facing_right else -(range_w + 10))
            pygame.draw.rect(surface, RED, (atk_x, self.y - 25, range_w, 60), 2)
        elif self.attack_timer > 0:
            # 攻撃発生時: オレンジ色のエフェクト
            swing_color = (255, 100, 0)
            atk_x = self.x + (40 * dir_mod)
            pygame.draw.ellipse(surface, swing_color, (atk_x - 40, self.y - 30, 80, 60), 5)

        # 地響き攻撃の予告とエフェクト
        if 150 < self.shockwave_timer < 200:
            # 地面に赤い点滅する警告線を表示
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                pygame.draw.rect(surface, RED, (0, 530, SCREEN_WIDTH, 10))
        elif self.shockwave_timer < 10 and self.shockwave_timer > 0:
            # 発生時のエフェクト (白い閃光)
            pygame.draw.rect(surface, WHITE, (0, 530, SCREEN_WIDTH, 15))

def game_clear_screen(screen, font):
    """ゲームクリア画面を表示する"""
    while True:
        screen.fill(WHITE)
        large_font = pygame.font.SysFont("msgothic", 80, bold=True)
        clear_label = large_font.render("GAME CLEAR!", True, GOLD)
        screen.blit(clear_label, (SCREEN_WIDTH // 2 - clear_label.get_width() // 2, 200))
        
        msg = font.render("おめでとう！ ボスを撃破し、全ての試練を突破しました！", True, BLACK)
        screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, 320))
        
        hint = font.render("Escキーで終了します", True, (100, 100, 100))
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 450))
        
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

def setup_stage(stage_number):
    """ステージ番号に基づいて敵と足場を生成する"""
    enemies = []
    platforms = []

    # 常に地面の足場を追加
    platforms.append(pygame.Rect(0, 535, SCREEN_WIDTH, 65))

    if stage_number == 1:
        enemies = [Enemy(200, 450), RangedEnemy(600, 450)]
        platforms.extend([
            pygame.Rect(100, 450, 150, 20),
            pygame.Rect(300, 350, 200, 20),
            pygame.Rect(550, 250, 150, 20)
        ])
    elif stage_number == 2:
        enemies = [Enemy(150, 450), Enemy(400, 450), RangedEnemy(700, 450)]
        platforms.extend([
            pygame.Rect(50, 480, 120, 20),
            pygame.Rect(250, 380, 120, 20),
            pygame.Rect(450, 280, 120, 20),
            pygame.Rect(650, 180, 120, 20)
        ])
    elif stage_number == 4:
        # ステージ4: ボス戦
        enemies = [Boss(600, 450)]
        platforms.extend([
            pygame.Rect(150, 420, 200, 20),
            pygame.Rect(450, 420, 200, 20)
        ])
    else:
        # ステージ3以降はランダムな足場と敵を生成
        num_platforms = random.randint(3, 6 + stage_number // 2) # ステージが進むにつれて足場が増える
        
        # 足場を生成
        for i in range(num_platforms):
            plat_width = random.randint(100, 250)
            plat_x = random.randint(0, SCREEN_WIDTH - plat_width)
            # 足場は地面より上で、画面上部から離れた位置に生成
            plat_y = random.randint(150, 500) 
            platforms.append(pygame.Rect(plat_x, plat_y, plat_width, 20))

        # 足場をY座標でソート（描画順や配置の考慮のため）
        platforms.sort(key=lambda p: p.y, reverse=True)

        # 敵の数をランダムに決定
        num_melee_enemies = random.randint(1 + stage_number // 3, 3 + stage_number // 2)
        num_ranged_enemies = random.randint(0 + stage_number // 4, 2 + stage_number // 3)

        # 敵のスポーン位置（足場の上または地面）を収集
        valid_spawn_y = []
        for p in platforms:
            valid_spawn_y.append(p.top - 35) # 敵の高さに合わせて足場の上に配置
        
        # スポーン位置が画面外にならないようにフィルタリング
        valid_spawn_y = [y for y in valid_spawn_y if y > 50 and y < SCREEN_HEIGHT - 65 - 35] # 地面Rectの上限を考慮

        if not valid_spawn_y: # 有効なスポーン位置がない場合のフォールバック（地面）
            valid_spawn_y.append(500)

        for _ in range(num_melee_enemies):
            enemies.append(Enemy(random.randint(50, SCREEN_WIDTH - 50), random.choice(valid_spawn_y)))
        for _ in range(num_ranged_enemies):
            enemies.append(RangedEnemy(random.randint(50, SCREEN_WIDTH - 50), random.choice(valid_spawn_y)))
    
    return enemies, platforms

def main():
    clock = pygame.time.Clock()
    player = Player()
    current_stage = 1
    enemies, platforms = setup_stage(current_stage)
    projectiles = []
    font = pygame.font.SysFont("msgothic", 24) # 日本語対応フォント（Windows標準）

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        player.update(platforms, enemies, projectiles)
        
        for enemy in enemies:
            if isinstance(enemy, Enemy): # 近接敵
                enemy.update(platforms, player.x) # platformsとplayer.xを渡す
            elif isinstance(enemy, RangedEnemy): # 遠距離敵
                enemy.update(player.x, projectiles, platforms) # platformsを渡す
            elif isinstance(enemy, Boss): # ボス
                enemy.update(player.x, projectiles, platforms)

        for proj in projectiles[:]:
            proj.update()
            # 画面外に出たら削除
            if proj.x < 0 or proj.x > SCREEN_WIDTH:
                projectiles.remove(proj)
        
        # 体力がなくなった敵を削除
        enemies = [e for e in enemies if e.health > 0]

        # ステージクリア判定
        if not enemies:
            if current_stage == 4:
                game_clear_screen(screen, font)
                
            current_stage += 1
            enemies, platforms = setup_stage(current_stage)
            projectiles.clear()
            # プレイヤーの位置と状態をリセット
            player.x = SCREEN_WIDTH // 2
            player.y = 450
            player.vel_y = 0
            player.is_jumping = False

        screen.fill(WHITE)
        
        # 地面の描画
        pygame.draw.rect(screen, GROUND_COLOR, (0, 535, SCREEN_WIDTH, 65))
        
        # 足場の描画
        for plat in platforms:
            pygame.draw.rect(screen, GROUND_COLOR, plat, border_radius=3)

        for enemy in enemies:
            enemy.draw(screen)

        for proj in projectiles:
            proj.draw(screen)

        player.draw(screen)

        # --- UI表示 ---
        # プレイヤーの体力をハートで表示 (左上)
        for i in range(player.health):
            hx, hy = 30 + i * 35, 30
            pygame.draw.circle(screen, RED, (hx - 7, hy), 8)
            pygame.draw.circle(screen, RED, (hx + 7, hy), 8)
            pygame.draw.polygon(screen, RED, [(hx - 15, hy + 3), (hx + 15, hy + 3), (hx, hy + 18)])

        # ボスHPバーの表示 (上部中央)
        for enemy in enemies:
            if isinstance(enemy, Boss):
                bar_w, bar_h = 400, 24
                bx, by = (SCREEN_WIDTH - bar_w) // 2, 30
                # ヘリ（枠）を太くして装飾
                pygame.draw.rect(screen, BLACK, (bx - 6, by - 6, bar_w + 12, bar_h + 12)) # 外枠
                pygame.draw.rect(screen, (60, 60, 60), (bx, by, bar_w, bar_h))      # 背景
                pygame.draw.rect(screen, RED, (bx, by, bar_w * (enemy.health / enemy.max_health), bar_h)) # 残量
                screen.blit(font.render("BOSS", True, WHITE), (bx, by - 20))

        # ステージ情報をタイトルに表示
        pygame.display.set_caption(f"Stage: {current_stage} | アクションゲーム試作")

        pygame.display.flip()
        clock.tick(60)

        # ゲームオーバー判定
        if player.health <= 0:
            print("Game Over!")
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    main()