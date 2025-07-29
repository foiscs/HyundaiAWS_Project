package com.block.music1.controller;


import com.block.music1.model.Music;
import com.block.music1.service.MusicService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/music")
public class MusicController {
    private final MusicService musicService;

    public MusicController(MusicService musicService) {
        this.musicService = musicService;
    }

    @GetMapping
    public ResponseEntity<List<Music>> getAllMusic() {
        return ResponseEntity.ok(musicService.getAllMusic());
    }

    @GetMapping("/{id}")
    public ResponseEntity<Music> getMusicById(@PathVariable Long id) {
        return musicService.getMusicById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/genre/{genre}")
    public ResponseEntity<List<Music>> searchMusicByGenre(@PathVariable String genre) {
        List<Music> musicList = musicService.searchMusicByGenre(genre);
        return ResponseEntity.ok(musicList);
    }

    @PostMapping("/{id}/like")
    public ResponseEntity<String> addLike(@PathVariable Long id) {
        boolean success = musicService.addLike(id);
        if (success) {
            return ResponseEntity.ok("좋아요가 추가되었습니다.");
        }
        return ResponseEntity.notFound().build();
    }
} 