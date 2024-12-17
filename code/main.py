from settings import * 
from sprites import * 
from groups import AllSprites
from support import * 
from timer import Timer
from random import randint

class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.player_out_time = None  
        self.out_delay = 1
        self.is_falling = False
        pygame.display.set_caption('SUPER UEH')
        self.clock = pygame.time.Clock()
        self.running = True
        self.won = False

        # Volume settings
        self.volume = 0.5  # Default volume

        # groups 
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

        # load game 
        self.load_assets()
        self.setup()

        # timers 
        self.drl_timer = Timer(2000, func = self.create_drl, autostart = True, repeat = True)

    def set_audio_volume(self, volume):
        for sound in self.audio.values():
            sound.set_volume(volume)


    def start_screen(self):
        running = True
        background_image = pygame.image.load('images/ueh-ctd-3i.png')
        background_image = pygame.transform.scale(background_image, (WINDOW_WIDTH, WINDOW_HEIGHT))  # Scale to fit screen size
        # Set the initial volume for the background music and sound effects
        pygame.mixer.music.set_volume(self.volume)
        self.set_audio_volume(self.volume)

        while running:
            dt = self.clock.tick(FRAMERATE) / 1000
            self.display_surface.blit(background_image)
            font = pygame.font.Font(None, 120)
            title_text = font.render("SUPER UEH", True,G_UEH)

            font = pygame.font.Font(None, 60)
            volume_text = font.render(f"Volume: {int(self.volume * 100)}%", True, O_UEH)
            start_text = font.render("ENTER to Start", True, O_UEH)
            exit_text = font.render("ESC to Exit", True, O_UEH)

            self.display_surface.blit(title_text, title_text.get_rect(center=(WINDOW_WIDTH  -350, 230)))
            self.display_surface.blit(volume_text, volume_text.get_rect(center=(WINDOW_WIDTH -350,350)))
            self.display_surface.blit(start_text, start_text.get_rect(center=(WINDOW_WIDTH -350, 450)))
            self.display_surface.blit(exit_text, exit_text.get_rect(center=(WINDOW_WIDTH -350, 550)))

            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        running = False  # Start the game
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        exit()  # Exit the game
                    if event.key == pygame.K_UP:
                        self.volume = min(1.0, self.volume + 0.1)  # Increase volume
                        pygame.mixer.music.set_volume(self.volume)  # Adjust background music volume
                        self.set_audio_volume(self.volume)  # Adjust sound effects volume
                    if event.key == pygame.K_DOWN:
                        self.volume = max(0.0, self.volume - 0.1)  # Decrease volume
                        pygame.mixer.music.set_volume(self.volume)  # Adjust background music volume
                        self.set_audio_volume(self.volume)  # Adjust sound effects volume


    def create_drl(self):
        Drl(
        frames=self.drl_frames,
        pos=((self.level_width+WINDOW_WIDTH/2), randint(0, self.level_height)),   
        groups=(self.all_sprites, self.enemy_sprites),
        speed=randint(200, 400))  

    def create_bullet(self, pos, direction):
        x = pos[0] + direction * 34 if direction == 1 else pos[0] + direction * 34- self.bullet_surf.get_width()
        Bullet(self.bullet_surf, (x, pos[1]), direction, (self.all_sprites, self.bullet_sprites))
        Fire(self.fire_surf, pos, self.all_sprites, self.player)
        self.audio['shoot'].play()

    def check_player_out_of_bounds(self):
        #game overover
        if (self.player.rect.left < 0 or 
            self.player.rect.right > self.level_width or 
            self.player.rect.top < 0 or 
            self.player.rect.bottom > self.level_height):
            if not self.is_falling:  
               self.is_falling = True
               self.player_out_time = pygame.time.get_ticks() / 1000  
        else:
             self.is_falling = False
             self.player_out_time = None            

        # win gamegame
        if self.player.rect.right >= self.level_width:
            self.running = False
            self.won = True

    def load_assets(self):
        # graphics 
        self.player_frames = import_folder('images', 'player')
        self.bullet_surf = import_image('images', 'gun', 'bullet')
        self.fire_surf = import_image('images', 'gun', 'fire')
        self.drl_frames = import_folder('images', 'enemies', 'drl')
        self.deadline_frames = import_folder('images', 'enemies', 'deadline')

        # sounds 
        self.audio = audio_importer('audio')

    def setup(self):
        tmx_map = load_pygame(join('data', 'maps', 'world.tmx'))
        self.level_width = tmx_map.width * TILE_SIZE
        self.level_height = tmx_map.height * TILE_SIZE

        for x, y, image in tmx_map.get_layer_by_name('Main').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE), image, (self.all_sprites, self.collision_sprites))
        
        for x, y, image in tmx_map.get_layer_by_name('Decoration').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE), image, self.all_sprites)
        for obj in tmx_map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites, self.player_frames, self.create_bullet)
            if obj.name == 'Deadline':
                Deadline(self.deadline_frames, pygame.FRect(obj.x, obj.y, obj.width, obj.height), (self.all_sprites, self.enemy_sprites))

        self.audio['music'].play(loops = -1)

    def collision(self):
        # bullets -> enemies 
        for bullet in self.bullet_sprites:
            sprite_collision = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
            if sprite_collision:
                self.audio['impact'].play()
                bullet.kill()
                for sprite in sprite_collision:
                    sprite.destroy()

        # enemies -> player
        # if pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask):
        #    self.running = False
        # if not self.running:
        #    self.game_over_screen()

    def run(self):
        self.start_screen()

        while self.running:
            dt = self.clock.tick(FRAMERATE) / 1000 
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False 
            # update
            self.drl_timer.update()
            self.all_sprites.update(dt)
            self.collision()
            self.check_player_out_of_bounds()
            if self.is_falling:
                self.player.rect.y += 10 
                current_time = pygame.time.get_ticks() / 1000
                if current_time - self.player_out_time > self.out_delay:  
                    self.running = False 
            # draw 
            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.rect.center)
            pygame.display.update()

        if self.won:
            self.win_screen()
        else:
            self.game_over_screen()  # This will call the modified game_over_screen method

        pygame.quit()

    def game_over_screen(self):
        font = pygame.font.Font(None, 100)
        text = font.render("You fail the the computer science!", True, O_UEH)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        
        # Play Again button
        button_font = pygame.font.Font(None, 50)
        play_again_text = button_font.render("ENTER to learn Again", True, G_UEH)
        play_again_rect = play_again_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 180))
        uotgame = button_font.render("ESC to leave school", True, G_UEH)
        uotgame_rect = uotgame.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 250))

        self.display_surface.fill('white')
        self.display_surface.blit(text, text_rect)
        self.display_surface.blit(play_again_text, play_again_rect)
        self.display_surface.blit(uotgame, uotgame_rect)
        pygame.display.update()

        # Wait for player to click "Play Again"
        waiting_for_input = True
        while waiting_for_input:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:  # Check if Enter is pressed
                        self.restart_game()  # Restart the game
                        waiting_for_input = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        exit()

    def restart_game(self):
        # Stop the current background music if it's playing
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        # Quit the current game instance
        pygame.quit()

        # Reinitialize the game by creating a new instance
        self.__init__()  # Reinitialize the game object to start fresh

        # Play the background music again after restarting
        self.audio['music'].play(loops=-1)

        # Start the game loop again
        self.run()



    def win_screen(self):
        font = pygame.font.Font(None, 60)
        text = font.render("Congratulations on passing the computer science!", True, G_UEH)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.display_surface.fill("white")
        self.display_surface.blit(text, text_rect)
        pygame.display.update()
        pygame.time.delay(5000)
if __name__ == '__main__':
    game = Game()
    game.run()




