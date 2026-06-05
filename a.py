import pygame

pygame.init()

screen = pygame.display.set_mode((500, 400))
background = pygame.image.load("cyber punk background 1.png")
background = pygame.transform.scale(background, (500, 400))

clock = pygame.time.Clock()

player_x = 200
player_y = 270

velocity_y = 0
gravity = 0.5
jump_power = -10

on_ground = True

scroll_x = 0

running = True


walk_images = [
    pygame.image.load("walk01.png"),
    pygame.image.load("walk02.png"),
]

for i in range(len(walk_images)):
    walk_images[i] = pygame.transform.scale(walk_images[i], (60, 60))

walk_index = 0
walk_timer = 0

player_image = walk_images[0]

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    for i in range(20):
        screen.blit(background, (i * 500 - (scroll_x % 500), 0))

    keys = pygame.key.get_pressed()

    moving = False

    if keys[pygame.K_RIGHT]:
        scroll_x += 5
        moving = True

    if keys[pygame.K_LEFT]:
        scroll_x -= 5
        moving = True

    if keys[pygame.K_SPACE] and on_ground:
    	velocity_y = jump_power
    	on_ground = False

    # 歩きアニメ
    if moving:
        walk_timer += 1

        if walk_timer >= 10:
            walk_timer = 0
            walk_index += 1

            if walk_index >= len(walk_images):
                walk_index = 0

        player_image = walk_images[walk_index]

    else:
        player_image = walk_images[0]

    velocity_y += gravity
    player_y += velocity_y

    if player_y > 245:
    	player_y = 245
    	velocity_y = 0
    	on_ground = True

    # プレイヤー（真ん中固定）

    screen.blit(player_image, (player_x, player_y))
    
    pygame.display.update()

    clock.tick(60)

pygame.quit()
