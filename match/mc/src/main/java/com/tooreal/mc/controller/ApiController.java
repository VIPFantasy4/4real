package com.tooreal.mc.controller;

import com.tooreal.mc.common.ApiCode;
import com.tooreal.mc.common.ApiResponse;
import com.tooreal.mc.dto.ApiDto;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;

@RestController
@RequestMapping("/api")
public class ApiController {

    @PostMapping("/login")
    public ApiResponse login(@RequestBody ApiDto apiDto){
        return ApiResponse.ok();
    }
}
