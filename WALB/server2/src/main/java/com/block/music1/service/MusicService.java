package com.block.music1.service;

import com.block.music1.model.Music;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Service
public class MusicService {
    private final List<Music> musicList;

    public MusicService() {
        musicList = new ArrayList<>();
        // 페이크 데이터 초기화
        musicList.add(new Music(1L, "hello~~Dynamite", "BTS", "BE", 2020, "K-pop", 199, 1000000));
        musicList.add(new Music(2L, "Spring Day", "BTS", "You Never Walk Alone", 2017, "K-pop", 255, 950000));
        musicList.add(new Music(3L, "How You Like That", "BLACKPINK", "THE ALBUM", 2020, "K-pop", 182, 890000));
        musicList.add(new Music(4L, "Maria", "Hwasa", "Maria", 2020, "K-pop", 195, 450000));
        musicList.add(new Music(5L, "Celebrity", "IU", "Celebrity", 2021, "K-pop", 195, 780000));
    }

    public List<Music> getAllMusic() {
        return new ArrayList<>(musicList);
    }

    public Optional<Music> getMusicById(Long id) {
        return musicList.stream()
                .filter(music -> music.getId().equals(id))
                .findFirst();
    }

    public List<Music> searchMusicByGenre(String genre) {
        return musicList.stream()
                .filter(music -> music.getGenre().equalsIgnoreCase(genre))
                .toList();
    }

    public boolean addLike(Long id) {
        Optional<Music> musicOpt = getMusicById(id);
        if (musicOpt.isPresent()) {
            Music music = musicOpt.get();
            music.setLikes(music.getLikes() + 1);
            return true;
        }
        return false;
    }
} 