import pygame
import random

pygame.init()

WIDTH, HEIGHT = 1280, 720 # モニタに合わせて解像度を調整（大きすぎると起動失敗の原因になります）
GROUND_Y = 450
font = pygame.font.SysFont("arial", 50)

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)

# --- アセットの安全な読み込み ---
def load_sfx(file):
    try:
        return pygame.mixer.Sound(file)
    except:
        print(f"Warning: Sound file {file} not found.")
        return None

def load_img(file, size=None):
    try:
        img = pygame.image.load(file)
        if size:
            img = pygame.transform.scale(img, size)
        return img
    except:
        print(f"Warning: Image file {file} not found.")
        # ファイルがない場合はピンク色のダミー画像を作成して返す
        surf = pygame.Surface(size if size else (100, 100))
        surf.fill((255, 0, 255))
        return surf

def play_sfx(sound):
    if sound: sound.play()

background = load_img("gazo/cyber punk background 1.png", (WIDTH, HEIGHT))

hit_sound = load_sfx("BGM・SE/panti.mp3")
parry_sound = load_sfx("BGM・SE/K.O..mp3")
death_sound = load_sfx("BGM・SE/taore.mp3")

# BGMの読み込みとループ再生
try:
    pygame.mixer.music.load("BGM・SE/BGM.mp3")
    pygame.mixer.music.play(-1)
except:
    print("Warning: BGM.mp3 not found.")
# -------------------------------

clock = pygame.time.Clock()

player_x = 200
player_y = GROUND_Y

velocity_y = 0
gravity = 0.5
jump_power = -20

on_ground = True

scroll_x = 0

running = True
facing_right = True
game_over = False
game_clear = False
is_fullscreen = True
attack_timer = 0
attack_hit_registered = False
attack_cooldown = 0
player_hp = 5
invincible_timer = 0
parry_timer = 0
parry_success_timer = 0
parry_cooldown = 0
knockback_timer = 0
knockback_dir = 0

is_throw_attacking = False
projectile_x = 0
projectile_y = 0
projectile_returning = False
projectile_angle = 0

enemy_world_x = 2000 # 敵の初期位置（画面外の右側）
enemy_hp = 50
enemy_hit_timer = 0

# 敵の画像を0, 2, 3の順で読み込み、左右反転させる
enemy_images = []
for i in [0, 2, 3]:
    img = load_img(f"gazo/hanma-teki({i}).png", (360, 360))
    enemy_images.append(pygame.transform.flip(img, True, False))

enemy_nage_img = pygame.transform.flip(load_img("gazo/hanma-teki-nage.png", (360, 360)), True, False)
projectile_img = load_img("gazo/hanma-.png", (200, 200))

enemy_anim_index = 0
enemy_anim_timer = 0
enemy_speed = 4
enemy_v_y = 0
enemy_y_jump = 0
is_jump_attacking = False
is_dash_attacking = False
dash_attack_timer = 0
dash_attack_flip_timer = 0
dash_flip_state = False
enemy_seen = False
first_throw_done = False

walk_images = [
    load_img("gazo/walk01.png", (180, 180)),
    load_img("gazo/walk02.png", (180, 180)),
]

walk_index = 0
walk_timer = 0

player_image = walk_images[0]

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
                else:
                    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    # --- サイバーパンクな多層背景の描画 ---
    # 1. 遠景：背景画像をパララックス（ゆっくり）で動かす
    bg_speed = 0.5
    rel_bg_x = (scroll_x * bg_speed) % WIDTH
    screen.blit(background, (-rel_bg_x, 0))
    if rel_bg_x > 0:
        screen.blit(background, (WIDTH - rel_bg_x, 0))

    # 2. 中景：遠くのビルのシルエットを追加
    building_interval = 800
    rel_building_x = (scroll_x * 0.7) % building_interval
    for i in range(-1, (WIDTH // building_interval) + 2):
        bx = i * building_interval - rel_building_x
        # 濃い紺色のビルの形
        pygame.draw.rect(screen, (20, 20, 40), (bx, GROUND_Y - 400, 400, 800))
        # ビルの窓（ネオンピンクの明かり）
        for r in range(12):
            for c in range(6):
                if (i + r + c) % 5 == 0:
                    pygame.draw.rect(screen, (255, 0, 255), (bx + 40 + c*60, GROUND_Y - 350 + r*50, 25, 15))

    # 3. 近景：サイバーパンク風の地面（グリッド床）
    floor_y = GROUND_Y + 180 # キャラクターの足元の位置
    pygame.draw.rect(screen, (10, 10, 25), (0, floor_y, WIDTH, HEIGHT - floor_y))
    pygame.draw.line(screen, (0, 255, 255), (0, floor_y), (WIDTH, floor_y), 6) # 地平線のネオンライン
    # グリッドの縦線を描画して遠近感を出す
    for i in range(-20, 40):
        grid_x = i * 200 - (scroll_x % 200)
        pygame.draw.line(screen, (50, 50, 120), (grid_x, floor_y), (grid_x - 500, HEIGHT), 2)
    # ------------------------------------

    keys = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()
    
    moving = False

    if not game_over and not game_clear:
        # ノックバック中かどうかの判定
        if knockback_timer > 0:
            scroll_x += 8 * knockback_dir
            knockback_timer -= 1
        else:
            move_speed = 10 if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else 5
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                scroll_x += move_speed
                moving = True
                facing_right = True

            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                scroll_x -= move_speed
                moving = True
                facing_right = False

        if keys[pygame.K_SPACE] and on_ground:
            velocity_y = jump_power
            on_ground = False

        # 攻撃の入力 (マウス左クリック: 近接攻撃)
        if mouse_buttons[0] and attack_timer == 0 and attack_cooldown == 0:
            attack_timer = 15  # 攻撃判定の持続時間
            attack_cooldown = 25 # 次の攻撃までの待ち時間（クールダウン）
            attack_hit_registered = False # 新しい攻撃なのでヒット判定をリセット

        if attack_timer > 0: attack_timer -= 1
        if attack_cooldown > 0: attack_cooldown -= 1

        if mouse_buttons[2] and parry_timer == 0 and parry_cooldown == 0:
            parry_timer = 12 # 0.2秒間 (60fps x 0.2)

        if parry_timer > 0:
            parry_timer -= 1
            if parry_timer == 0:
                parry_cooldown = 300 # 失敗時：5秒間のペナルティ
        if parry_success_timer > 0:
            parry_success_timer -= 1
        if parry_cooldown > 0:
            parry_cooldown -= 1

        if enemy_hit_timer > 0:
            enemy_hit_timer -= 1

        # 無敵時間のカウントダウン
        if invincible_timer > 0:
            invincible_timer -= 1

        # 敵の移動とジャンプ攻撃のロジック
        player_world_x = scroll_x + player_x
        enemy_screen_x = enemy_world_x - scroll_x

        # 敵を全身視認したかチェック（画面の左右に収まっているか）
        if not enemy_seen:
            if 0 <= enemy_screen_x <= WIDTH - 360:
                enemy_seen = True

        if not is_jump_attacking and not is_dash_attacking and not is_throw_attacking:
            # 通常移動
            if enemy_anim_index == 0:
                if enemy_world_x > player_world_x + 5:
                    enemy_world_x -= enemy_speed
                elif enemy_world_x < player_world_x - 5:
                    enemy_world_x += enemy_speed
            
            # 通常のアニメーション更新
            enemy_anim_timer += 1
            if enemy_anim_timer >= 40:
                enemy_anim_timer = 0
                enemy_anim_index = (enemy_anim_index + 1) % 3
            
            # 特殊攻撃の開始 (歩行中のみ、かつ一度全身が見えてから)
            if enemy_seen and enemy_anim_index == 0:
                if not first_throw_done:
                    # 最初の攻撃は必ずハンマー投げにする
                    is_throw_attacking = True
                    projectile_returning = False
                    warp_dist = 600
                    enemy_world_x = player_world_x + warp_dist
                    projectile_x = enemy_world_x + 180
                    projectile_y = GROUND_Y
                    first_throw_done = True
                elif random.randint(0, 60) == 0:
                    is_jump_attacking = True
                    enemy_v_y = -30
                elif random.randint(0, 80) == 0:
                    is_dash_attacking = True
                    dash_attack_timer = 90 # 約1.5秒間
                    dash_attack_flip_timer = 0
                elif random.randint(0, 100) == 0:
                    is_throw_attacking = True
                    projectile_returning = False
                    # 主人公の右側にワープ
                    warp_dist = 600
                    enemy_world_x = player_world_x + warp_dist
                    projectile_x = enemy_world_x + 180
                    projectile_y = GROUND_Y

        elif is_jump_attacking:
            # ジャンプ攻撃中：物理演算と空中移動
            enemy_v_y += gravity
            enemy_y_jump += enemy_v_y
            enemy_world_x += (enemy_speed * 3) if enemy_world_x < player_world_x else -(enemy_speed * 3)
            
            # 状態に応じた画像：上昇中(2)=index 1, 落下中(3)=index 2
            enemy_anim_index = 1 if enemy_v_y < 0 else 2
                
            # 接地判定
            if enemy_y_jump >= 0:
                enemy_y_jump = 0
                is_jump_attacking = False
                enemy_anim_index = 0
                enemy_anim_timer = 0

        elif is_dash_attacking:
            # ダッシュ攻撃中：高速移動と向きの高速反転
            dash_attack_timer -= 1
            dash_speed = enemy_speed * 6
            if enemy_world_x > player_world_x + 10:
                enemy_world_x -= dash_speed
            elif enemy_world_x < player_world_x - 10:
                enemy_world_x += dash_speed
            
            # 向きを高速でパタパタさせる演出
            dash_attack_flip_timer += 1
            if dash_attack_flip_timer >= 5:
                dash_attack_flip_timer = 0
                dash_flip_state = not dash_flip_state
            
            enemy_anim_index = 2 # hanma-teki(3)
            if dash_attack_timer <= 0:
                is_dash_attacking = False
                enemy_anim_index = 0

        elif is_throw_attacking:
            # 投擲攻撃中：hanma- の移動ロジック
            projectile_angle += 15 # ハンマーを回転させる

            proj_speed = 15
            if not projectile_returning:
                # 主人公に向かって進む
                target_x = scroll_x + player_x + 90
                target_y = player_y + 90
                dx = target_x - projectile_x
                dy = target_y - projectile_y
                dist = (dx**2 + dy**2)**0.5
                if dist < proj_speed:
                    projectile_returning = True
                else:
                    projectile_x += (dx/dist) * proj_speed
                    projectile_y += (dy/dist) * proj_speed
            else:
                # 敵の手元に戻る
                target_x = enemy_world_x + 180
                target_y = enemy_y + 180
                dx = target_x - projectile_x
                dy = target_y - projectile_y
                dist = (dx**2 + dy**2)**0.5
                if dist < proj_speed:
                    is_throw_attacking = False # 戻ったら攻撃終了
                else:
                    projectile_x += (dx/dist) * proj_speed
                    projectile_y += (dy/dist) * proj_speed
            
            # hanma- の攻撃判定
            proj_screen_x = projectile_x - scroll_x
            proj_rect = pygame.Rect(proj_screen_x - 100, projectile_y - 100, 200, 200)
            if proj_rect.colliderect(player_rect):
                if parry_timer > 0:
                    # ハンマーへのパリィ成功！
                    play_sfx(parry_sound)
                    parry_success_timer = 20
                    projectile_returning = True # 敵に跳ね返す
                    parry_timer = 0
                    parry_cooldown = 40
                    invincible_timer = 120 # 成功後の無敵付与
                elif invincible_timer == 0:
                    # パリィしていない、かつ無敵でない場合はダメージ
                    player_hp -= 1
                    if player_hp <= 0:
                        play_sfx(death_sound)
                    else:
                        play_sfx(hit_sound)
                    
                    invincible_timer = 60
                    knockback_timer = 15
                    knockback_dir = -1 if player_x < proj_screen_x else 1
                    velocity_y = -5
                    on_ground = False
                    projectile_returning = True # 当たったら戻り始める
                    if player_hp <= 0:
                        player_hp = 0
                        game_over = True

        # --- 描画の準備 ---
        # 座標が更新された後、描画用のスクリーン座標を再計算（ワープ対策）
        enemy_screen_x = enemy_world_x - scroll_x
        enemy_y = GROUND_Y - 180 + enemy_y_jump
        enemy_rect = pygame.Rect(enemy_screen_x, enemy_y, 360, 360)

        if is_throw_attacking:
            current_enemy_img = enemy_nage_img
        else:
            current_enemy_img = enemy_images[enemy_anim_index]
        
        # ダメージを受けたときは赤っぽく点滅させる演出
        draw_enemy = True
        if enemy_hit_timer > 0 and (enemy_hit_timer // 4) % 2 == 0:
            draw_enemy = False # 簡易的な点滅演出

        if is_dash_attacking:
            # ダッシュ中はフラグに応じて向きを変える
            if dash_flip_state:
                current_enemy_img = pygame.transform.flip(current_enemy_img, True, False)
        elif enemy_world_x < player_world_x:
            current_enemy_img = pygame.transform.flip(current_enemy_img, True, False)
            
        if draw_enemy:
            screen.blit(current_enemy_img, (enemy_screen_x, enemy_y))
        
        # hanma- の回転描画
        if is_throw_attacking:
            proj_screen_x = projectile_x - scroll_x
            
            # --- 鎖（チェーン）のエフェクト描画 ---
            start_p = (enemy_screen_x + 180, enemy_y + 180) # 敵の中心点
            end_p = (proj_screen_x, projectile_y)        # ハンマーの中心点
            dist = ((start_p[0] - end_p[0])**2 + (start_p[1] - end_p[1])**2)**0.5
            num_links = int(dist / 25) # 25ピクセルごとに鎖の輪を描画
            for i in range(num_links):
                t = i / max(1, num_links)
                lx = start_p[0] + (end_p[0] - start_p[0]) * t
                ly = start_p[1] + (end_p[1] - start_p[1]) * t
                # 鎖のリンクを円で表現（メタリックグレーにシアンのネオン縁）
                pygame.draw.circle(screen, (30, 30, 30), (int(lx), int(ly)), 10)
                pygame.draw.circle(screen, (0, 255, 255), (int(lx), int(ly)), 10, 2)
            
            rotated_proj = pygame.transform.rotate(projectile_img, projectile_angle)
            proj_rect = rotated_proj.get_rect(center=(proj_screen_x, projectile_y))
            screen.blit(rotated_proj, proj_rect.topleft)

        # --- 近接攻撃の判定 ---
        if attack_timer > 0:
            # プレイヤーの向きに合わせて前方に攻撃判定（ヒットボックス）を生成
            attack_reach = 140
            if facing_right:
                attack_rect = pygame.Rect(player_x + 130, player_y, attack_reach, 180)
            else:
                attack_rect = pygame.Rect(player_x - attack_reach + 50, player_y, attack_reach, 180)
            
            # 攻撃判定が敵に触れたかチェック（1回の攻撃で1回だけダメージ）
            if attack_rect.colliderect(enemy_rect) and not attack_hit_registered:
                enemy_hp -= 1
                attack_hit_registered = True
                enemy_hit_timer = 20 # 20フレーム点滅
                # 攻撃した方向に少し敵を押し出す（ノックバック）
                enemy_world_x += 50 if facing_right else -50
                
                if enemy_hp <= 0:
                    play_sfx(death_sound)
                    game_clear = True

        # プレイヤー本体の当たり判定用Rect (少し小さくして操作感を向上)
        player_rect = pygame.Rect(player_x + 40, player_y, 100, 180)

        # 衝突判定
        if player_rect.colliderect(enemy_rect):
            if parry_timer > 0 and enemy_anim_index == 2:
                # パリィ成功！敵にダメージ
                enemy_hp -= 1
                play_sfx(parry_sound)
                enemy_hit_timer = 30
                if enemy_hp <= 0:
                    play_sfx(death_sound)
                    game_clear = True
                parry_cooldown = 40 # 成功時：通常の短いクールダウン
                parry_timer = 0
                parry_success_timer = 20 # 成功エフェクトの持続時間
                invincible_timer = 120 # パリィ成功後、一定時間（約2秒）の無敵を付与
            elif enemy_anim_index == 2 and invincible_timer == 0:
                # プレイヤーが攻撃中でなく、敵が攻撃中、かつ無敵時間でない時にダメージ
                player_hp -= 1
                if player_hp <= 0:
                    play_sfx(death_sound)
                else:
                    play_sfx(hit_sound)
                
                invincible_timer = 60  # 約1秒間の無敵時間
                knockback_timer = 15  # ノックバックの時間
                # 敵との位置関係から飛んでいく方向を決める
                knockback_dir = -1 if player_x < enemy_screen_x else 1
                velocity_y = -5 # ダメージを受けたときに少し跳ねる
                on_ground = False
                if player_hp <= 0:
                    player_hp = 0
                    game_over = True
            # それ以外（敵が攻撃中でない時）は当たっても平気

    # 歩きアニメ
    if moving:
        walk_timer += 1
        if walk_timer >= 10:
            walk_timer = 0
            walk_index += 1
            if walk_index >= len(walk_images):
                walk_index = 0
        img = walk_images[walk_index]
    else:
        img = walk_images[0]

    # 向きに合わせて画像を反転
    player_image = img if facing_right else pygame.transform.flip(img, True, False)

    if not game_over:
        velocity_y += gravity
        player_y += velocity_y

        # 接地判定
        if player_y > GROUND_Y:
            player_y = GROUND_Y
            velocity_y = 0
            on_ground = True

    # プレイヤー描画
    # 無敵時間は点滅させる（5フレームおきに表示/非表示を切り替え）
    if invincible_timer == 0 or (invincible_timer // 5) % 2 == 0:
        screen.blit(player_image, (player_x, player_y))

    # --- 敵のHPバー描画 ---
    if not game_over and not game_clear:
        enemy_bar_width = 200
        enemy_bar_x = enemy_screen_x + 80
        enemy_bar_y = enemy_y - 20
        pygame.draw.rect(screen, (50, 0, 0), (enemy_bar_x, enemy_bar_y, enemy_bar_width, 15)) # 背景
        current_hp_width = (enemy_hp / 50) * enemy_bar_width
        pygame.draw.rect(screen, (255, 0, 50), (enemy_bar_x, enemy_bar_y, current_hp_width, 15)) # 残りHP
        pygame.draw.rect(screen, (255, 255, 255), (enemy_bar_x, enemy_bar_y, enemy_bar_width, 15), 2) # 枠線

    # HPゲージ（ドライブゲージ風）の描画
    MAX_HP = 5
    BAR_WIDTH = 120
    BAR_HEIGHT = 30
    for i in range(MAX_HP):
        # HPが残っている分は緑、減った分は暗い灰色
        color = (0, 255, 150) if i < player_hp else (60, 60, 60)
        # 少し斜めにするなどの装飾はせず、シンプルなセグメント表示
        pygame.draw.rect(screen, color, (15 + i * (BAR_WIDTH + 5), 20, BAR_WIDTH, BAR_HEIGHT))
        # 各枠に白い縁取り
        pygame.draw.rect(screen, (200, 200, 200), (15 + i * (BAR_WIDTH + 5), 20, BAR_WIDTH, BAR_HEIGHT), 1)

    # パリィのクールタイム表示
    if parry_cooldown > 0:
        cd_sec = parry_cooldown / 60
        cd_text = font.render(f"PARRY COOLDOWN: {cd_sec:.1f}s", True, (255, 50, 50))
        screen.blit(cd_text, (20, 70))

    # 攻撃中のエフェクト（近接攻撃のスラッシュ）
    if attack_timer > 0:
        slash_color = (0, 255, 255) # サイバーパンク風のシアン
        if facing_right:
            # 右側への斬撃（弧を描く）
            pygame.draw.arc(screen, slash_color, (player_x + 100, player_y - 20, 180, 220), -1.2, 1.2, 10)
        else:
            # 左側への斬撃
            pygame.draw.arc(screen, slash_color, (player_x - 100, player_y - 20, 180, 220), 1.9, 4.3, 10)


    # パリィ中のエフェクト（青い円を表示）
    if parry_timer > 0:
        pygame.draw.circle(screen, (0, 191, 255), (player_x + 90, player_y + 90), 120, 5)

    # パリィ成功時のエフェクト
    if parry_success_timer > 0:
        # 黄金の衝撃波（円）が広がる
        radius = 120 + (20 - parry_success_timer) * 15
        pygame.draw.circle(screen, (255, 215, 0), (player_x + 90, player_y + 90), radius, 10)
        # 「PARRY!!」の文字を表示
        parry_text = font.render("PARRY!!", True, (255, 255, 0))
        screen.blit(parry_text, (player_x + 20, player_y - 120))

    # ゲームオーバー表示
    if game_over:
        text_surf = font.render("GAME OVER", True, (255, 0, 0))
        screen.blit(text_surf, (WIDTH//2 - 120, HEIGHT//2 - 30))

    if game_clear:
        text_surf = font.render("GAME CLEAR!!", True, (0, 255, 255))
        screen.blit(text_surf, (WIDTH//2 - 160, HEIGHT//2 - 30))
    
    pygame.display.update()

    clock.tick(60)

pygame.quit()