package com.block.music1.model;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class Music {
    private Long id;
    private String title;
    private String artist;
    private String album;
    private int releaseYear;
    private String genre;
    private int duration; // in seconds
    private int likes;
} 