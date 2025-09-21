import pgzrun
import math
import random

WIDTH = 800
HEIGHT = 600
TITLE = "Platform game"

GRAVITY = 0.8
PLAYER_JUMP_STRENGTH = -15
PLAYER_SPEED = 4
ENEMY_SPEED = 1.5
ANIMATION_SPEED = 3
TILE_SIZE = 16
DECOR_SIZE = 32
LEVEL_WIDTH_TILES = 200

game_state = 'main_menu'
is_music_on = False

camera_x = 0
background_mountains = Actor('background_mountains', anchor=('left', 'top'))

class Player:
    def __init__(self, pos):
        self.idle_right_anim = ['hero/idle_right_0']
        self.idle_left_anim = ['hero/idle_left_0']
        self.run_right_anim = [f'hero/run_right_{i}' for i in range(8)]
        self.run_left_anim = [f'hero/run_left_{i}' for i in range(8)]
        self.jump_right_anim = ['hero/jump_right_0']
        self.jump_left_anim = ['hero/jump_left_0']
        
        self.is_facing_right = True
        self.actor = Actor(self.idle_right_anim[0], pos)
        self.vy = 0
        self.is_on_ground = False
        self.frame = 0
        self.timer = 0

    def jump(self):
        if self.is_on_ground:
            self.vy = PLAYER_JUMP_STRENGTH
            sounds.jump.play()

    def update(self, platforms):
        dx = 0
        is_moving_horizontally = False
        if keyboard.left:
            dx = -PLAYER_SPEED
            self.is_facing_right = False
            is_moving_horizontally = True
        if keyboard.right:
            dx = PLAYER_SPEED
            self.is_facing_right = True
            is_moving_horizontally = True
        
        self.actor.x += dx
        
        for platform in platforms:
            if abs(platform.x - self.actor.x) > TILE_SIZE * 2:
                continue
            
            if self.actor.colliderect(platform):
                if dx > 0:
                    self.actor.right = platform.left
                elif dx < 0:
                    self.actor.left = platform.right
        
        self.vy += GRAVITY
        self.actor.y += self.vy
        self.is_on_ground = False
        
        for platform in platforms:
            if abs(platform.x - self.actor.x) > TILE_SIZE * 2:
                continue
                
            if self.actor.colliderect(platform):
                if self.vy > 0:
                    self.actor.bottom = platform.top
                    self.vy = 0
                    self.is_on_ground = True
                elif self.vy < 0:
                    self.actor.top = platform.bottom
                    self.vy = 0

        self._update_animation(is_moving_horizontally)

    def _update_animation(self, is_moving_horizontally):
        animation_type_list = None
        if not self.is_on_ground:
            animation_type_list = (self.jump_right_anim, self.jump_left_anim)
        elif is_moving_horizontally:
            animation_type_list = (self.run_right_anim, self.run_left_anim)
        else:
            animation_type_list = (self.idle_right_anim, self.idle_left_anim)

        if self.is_facing_right:
            current_animation = animation_type_list[0]
        else:
            current_animation = animation_type_list[1]
            
        self.timer += 1
        if self.timer >= ANIMATION_SPEED:
            self.timer = 0
            if self.actor.image not in current_animation:
                self.frame = 0
            
            self.frame = (self.frame + 1) % len(current_animation)
            self.actor.image = current_animation[self.frame]

    def reset(self, pos):
        self.actor.pos = pos
        self.vy = 0

class Enemy:
    def __init__(self, pos, patrol_range):
        self.walk_right_anim = [f'enemy/enemy_walk_right_{i}' for i in range(4)] 
        self.walk_left_anim = [f'enemy/enemy_walk_left_{i}' for i in range(4)] 
        
        self.actor = Actor(self.walk_right_anim[0], pos)
        self.start_x = pos[0]
        self.end_x = pos[0] + patrol_range
        self.direction = 1
        self.frame = 0
        self.timer = 0
        self.is_alive = True

    def update(self):
        if self.is_alive:
            self.actor.x += ENEMY_SPEED * self.direction
            if self.actor.x > self.end_x or self.actor.x < self.start_x:
                self.direction *= -1
            self._update_animation()

    def _update_animation(self):
        self.timer += 1
        if self.timer >= ANIMATION_SPEED * 2: 
            self.timer = 0
            
            current_animation = self.walk_right_anim if self.direction == 1 else self.walk_left_anim
            
            if self.actor.image not in current_animation:
                self.frame = 0

            self.frame = (self.frame + 1) % len(current_animation)
            self.actor.image = current_animation[self.frame]
        
    def die(self):
        self.is_alive = False
    
    def should_be_removed(self):
        return not self.is_alive

def generate_level(width_in_tiles):
    platforms = []
    decorations = []
    enemies = []
    chao_y = HEIGHT - TILE_SIZE

    for i in range(width_in_tiles):
        platforms.append(Actor('tiles/grass_top', pos=(TILE_SIZE * i, chao_y), anchor=('left', 'top')))
        
        if i > 5 and random.randint(0, 10) == 0:
            decor_type = random.choice(['tree', 'rock'])
            decorations.append(Actor(f'tiles/{decor_type}', pos=(TILE_SIZE * i, chao_y), anchor=('left', 'bottom')))

    x_tile = 10
    while x_tile < width_in_tiles - 15:
        if random.randint(0, 12) == 0:
            platform_length = random.randint(3, 8)
            platform_y = chao_y - TILE_SIZE * random.randint(3, 7)
            
            for i in range(platform_length):
                tile_x = TILE_SIZE * (x_tile + i)
                platforms.append(Actor('tiles/grass_top', pos=(tile_x, platform_y), anchor=('left', 'top')))

            if platform_length > 3 and random.randint(0, 3) == 0:
                enemy_start_x = TILE_SIZE * x_tile
                enemy_y = platform_y - TILE_SIZE / 2
                patrol_range = (platform_length - 2) * TILE_SIZE
                enemies.append(Enemy(pos=(enemy_start_x, enemy_y), patrol_range=patrol_range))
            
            x_tile += platform_length
        else:
            x_tile += 1


    return platforms, decorations, enemies

class Button:
    def __init__(self, text, pos, action, fontsize=40, is_checkbox=False, get_state_func=None):
        self.text = text
        self.pos = pos
        self.action = action
        self.fontsize = fontsize
        self.is_checkbox = is_checkbox
        self.get_state_func = get_state_func
        self.color = "white"
        self.hover_color = "yellow"
        self.current_color = self.color
        self.rect = Rect((0, 0), (300, 50))
        self.rect.center = self.pos

    def draw(self):
        display_text = self.text
        if self.is_checkbox and self.get_state_func is not None:
            is_checked = self.get_state_func()
            checkbox_symbol = '[X]' if is_checked else '[ ]'
            display_text = f"{checkbox_symbol} {self.text}"

        screen.draw.filled_rect(self.rect, (50, 50, 150))
        screen.draw.rect(self.rect, self.current_color)
        screen.draw.text(
            display_text,
            center=self.rect.center,
            fontsize=self.fontsize,
            color=self.current_color,
            owidth=0.5,
            ocolor="black"
        )

    def on_mouse_down(self, pos):
        if self.rect.collidepoint(pos):
            self.action()

    def update_hover(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            self.current_color = self.hover_color
        else:
            self.current_color = self.color

player_start_pos = (WIDTH / 4, HEIGHT - 100)
player = Player(player_start_pos)

platforms, decorations, enemies = generate_level(LEVEL_WIDTH_TILES)

def start_game():
    global game_state, camera_x, platforms, decorations, enemies
    game_state = 'playing'
    player.reset(player_start_pos)
    
    platforms, decorations, enemies = generate_level(LEVEL_WIDTH_TILES)
    
    camera_x = 0

def toggle_music():
    global is_music_on
    is_music_on = not is_music_on
    if is_music_on:
        music.play('background_music')
    else:
        music.stop()

def exit_game():
    exit()

start_y = HEIGHT / 2 - 30
spacing = 70

start_button = Button(text="Iniciar Jogo", pos=(WIDTH / 2, start_y), action=start_game)
music_button = Button(text="Som", pos=(WIDTH / 2, start_y + spacing), action=toggle_music, is_checkbox=True, get_state_func=lambda: is_music_on)
exit_button = Button(text="Sair", pos=(WIDTH / 2, start_y + spacing * 2), action=exit_game)
menu_buttons = [start_button, music_button, exit_button]

def resume_game():
    global game_state
    game_state = 'playing'

def go_to_main_menu():
    global game_state
    game_state = 'main_menu'

pause_y = HEIGHT / 2 - 30
resume_button = Button(text="Retornar Jogo", pos=(WIDTH / 2, pause_y), action=resume_game)
pause_music_button = Button(text="Som", pos=(WIDTH / 2, pause_y + spacing), action=toggle_music, is_checkbox=True, get_state_func=lambda: is_music_on)
back_to_menu_button = Button(text="Voltar ao Menu Principal", pos=(WIDTH / 2, pause_y + spacing * 2), action=go_to_main_menu, fontsize=35)
pause_buttons = [resume_button, pause_music_button, back_to_menu_button]

def on_key_down(key):
    global game_state
    if game_state == 'playing' and key == keys.ESCAPE:
        game_state = 'paused'
    elif game_state == 'paused' and key == keys.ESCAPE:
        resume_game()

def update():
    global game_state, camera_x
    if game_state == 'playing':
        if keyboard.up:
            player.jump()
        player.update(platforms)
        for enemy in enemies:
            enemy.update()

        target_camera_x = player.actor.x - WIDTH / 2 + (100 if player.is_facing_right else -100)
        camera_x += (target_camera_x - camera_x) * 0.1

        enemies_to_remove = []
        for enemy in enemies:
            if player.actor.colliderect(enemy.actor):
                if player.vy > 0 and player.actor.bottom < enemy.actor.centery:
                    enemy.die()
                    player.vy = PLAYER_JUMP_STRENGTH * 0.7
                elif enemy.is_alive:
                    player.reset(player_start_pos)
            if enemy.should_be_removed():
                enemies_to_remove.append(enemy)
        
        for enemy_to_remove in enemies_to_remove:
            enemies.remove(enemy_to_remove)
            
        if player.actor.top > HEIGHT:
            player.reset(player_start_pos)

def draw():
    global game_state, camera_x
    
    if game_state == 'playing' or game_state == 'paused':
        sky_parallax_factor = 0.1
        sky_offset = (camera_x * sky_parallax_factor) % WIDTH
        screen.blit('background_sky', (-sky_offset, 0))
        screen.blit('background_sky', (-sky_offset + WIDTH, 0))

        mountains_parallax_factor = 0.3
        mountain_width = background_mountains.width
        y_pos_mountains = HEIGHT - background_mountains.height
        mountain_offset = (camera_x * mountains_parallax_factor)
        start_x = -(mountain_offset % mountain_width)
        current_x = start_x
        while current_x < WIDTH:
            screen.blit(background_mountains.image, (current_x, y_pos_mountains))
            current_x += mountain_width

        for d in decorations:
            screen_x = d.topleft[0] - camera_x
            if -DECOR_SIZE < screen_x < WIDTH:
                screen.blit(d.image, (screen_x, d.topleft[1]))
                
        for p in platforms:
            screen_x = p.topleft[0] - camera_x
            if -TILE_SIZE < screen_x < WIDTH:
                screen.blit(p.image, (screen_x, p.topleft[1]))
            
        for e in enemies:
            screen_x = e.actor.x - camera_x
            if -e.actor.width < screen_x < WIDTH:
                original_pos = e.actor.pos
                e.actor.pos = (screen_x, e.actor.y)
                e.actor.draw()
                e.actor.pos = original_pos

        original_pos = player.actor.pos
        player.actor.pos = (player.actor.x - camera_x, player.actor.y)
        player.actor.draw()
        player.actor.pos = original_pos

    if game_state == 'paused':
        overlay = Rect((0, 0), (WIDTH, HEIGHT))
        screen.draw.filled_rect(overlay, (0, 0, 0, 120))
        screen.draw.text("PAUSADO", center=(WIDTH / 2, HEIGHT / 2 - 150), fontsize=60, color="white", owidth=1, ocolor="black")
        for button in pause_buttons:
            button.draw()

    elif game_state == 'main_menu':
        screen.blit('background_sky', (0, 0))
        screen.draw.text("Aventura na Selva do Código", center=(WIDTH / 2, HEIGHT / 2 - 150), fontsize=60, color="white", owidth=1, ocolor="black")
        for button in menu_buttons:
            button.draw()

def on_mouse_down(pos):
    if game_state == 'main_menu':
        for button in menu_buttons:
            button.on_mouse_down(pos)
    elif game_state == 'paused':
        for button in pause_buttons:
            button.on_mouse_down(pos)

def on_mouse_move(pos):
    if game_state == 'main_menu':
        for button in menu_buttons:
            button.update_hover(pos)
    elif game_state == 'paused':
        for button in pause_buttons:
            button.update_hover(pos)

pgzrun.go()