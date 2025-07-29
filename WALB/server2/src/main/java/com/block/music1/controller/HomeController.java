package com.block.music1.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * 홈 페이지 컨트롤러
 * 루트 경로(/)를 index.html로 리다이렉트
 */
@Controller
public class HomeController {
    
    /**
     * 루트 경로 접속 시 index.html 반환
     * @return index.html 페이지
     */
    @GetMapping("/")
    public String index() {
        return "index.html";
    }
}